# # models/rag_engine.py - AJOUTER EN HAUT
# from database import get_all_comments  # ← Utilise ta base existante

# # Et modifier get_rag_engine pour utiliser tes données réelles :
# def get_rag_engine(comments=None, force_rebuild=False):
#     """
#     Reconstruit l'index RAG avec les commentaires de MongoDB
#     """
#     global _RAG_ENGINE
    
#     if _RAG_ENGINE is not None and not force_rebuild:
#         return _RAG_ENGINE
    
#     # Récupérer les commentaires si non fournis
#     if comments is None:
#         from database import get_all_comments
#         comments = get_all_comments(limit=50000)
#         print(f"📥 {len(comments)} commentaires chargés depuis MongoDB")
    
#     # Charger depuis cache si disponible
#     if os.path.exists(INDEX_CACHE) and not force_rebuild:
#         try:
#             _RAG_ENGINE = SimpleRAG.load_cache()
#             return _RAG_ENGINE
#         except Exception as e:
#             print(f"⚠️ Cache invalide ({e}), reconstruction...")
    
#     # Construire l'index
#     _RAG_ENGINE = SimpleRAG(comments)
#     _RAG_ENGINE.save_cache()
#     return _RAG_ENGINE
# models/rag_engine.py
"""
Moteur RAG (Retrieval-Augmented Generation) pour les commentaires télécom algériens.
- Embeddings multilingues (sentence-transformers paraphrase-multilingual)
- Reranking par score hybride (sémantique + métadonnées)
- Filtres avancés : source, sentiment, thème, période, frustration
- Cache disque pour éviter de reconstruire l'index à chaque démarrage
"""

import os
import pickle
import hashlib
import numpy as np
import math
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
INDEX_CACHE    = os.path.join(os.path.dirname(__file__), ".rag_cache.pkl")
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"   # 50 langues + darija
BATCH_SIZE     = 64    # pour l'encodage par lots
TOP_K_RETRIEVE = 20    # on récupère 20 avant reranking
TOP_K_RETURN   = 5     # on retourne 5 après reranking

_RAG_ENGINE = None


# ─────────────────────────────────────────────────────────────
# EMBEDDINGS HELPERS
# ─────────────────────────────────────────────────────────────

def _load_embedder():
    """Charge le modèle sentence-transformers (lazy)."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"✅ SentenceTransformer chargé : {EMBEDDING_MODEL}")
        return model
    except ImportError:
        print("⚠️  sentence-transformers non installé — fallback TF-IDF")
        return None
    except Exception as e:
        print(f"⚠️  Erreur chargement embedder : {e}")
        return None


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Similarité cosinus entre deux vecteurs."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ─────────────────────────────────────────────────────────────
# TF-IDF FALLBACK
# ─────────────────────────────────────────────────────────────

class TFIDFIndex:
    """Index TF-IDF minimaliste (aucune dépendance externe)."""

    def __init__(self, texts: list[str]):
        self.texts     = texts
        self.vocab     = {}
        self.idf       = {}
        self.matrix    = []
        self._build(texts)

    def _tokenize(self, text: str) -> list[str]:
        import re
        text = text.lower()
        # Garder arabe + latin + chiffres
        return re.findall(r'[\u0600-\u06ff\w]{2,}', text)

    def _build(self, texts: list[str]) -> None:
        # Construire le vocabulaire
        df = Counter()
        tokenized = []
        for t in texts:
            toks = set(self._tokenize(t))
            tokenized.append(toks)
            df.update(toks)
        N = len(texts)
        self.idf = {w: math.log((N + 1) / (freq + 1)) + 1
                    for w, freq in df.items()}
        all_words = list(self.idf.keys())
        self.vocab = {w: i for i, w in enumerate(all_words)}
        # Vecteurs TF-IDF
        self.matrix = []
        for toks in tokenized:
            vec = np.zeros(len(all_words), dtype=np.float32)
            for w in toks:
                if w in self.vocab:
                    tf  = 1.0  # binary TF
                    idx = self.vocab[w]
                    vec[idx] = tf * self.idf.get(w, 0)
            norm = np.linalg.norm(vec)
            self.matrix.append(vec / norm if norm > 0 else vec)
        self.matrix = np.stack(self.matrix) if self.matrix else np.array([])

    def encode(self, text: str) -> np.ndarray:
        toks = set(self._tokenize(text))
        vec  = np.zeros(len(self.vocab), dtype=np.float32)
        for w in toks:
            if w in self.vocab:
                vec[self.vocab[w]] = self.idf.get(w, 0)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        if self.matrix.size == 0:
            return []
        qv   = self.encode(query)
        sims = self.matrix.dot(qv)
        top  = np.argsort(sims)[::-1][:k]
        return [(int(i), float(sims[i])) for i in top]


# ─────────────────────────────────────────────────────────────
# RERANKER
# ─────────────────────────────────────────────────────────────

def _rerank(candidates: list[dict], query: str, query_filters: dict) -> list[dict]:
    """
    Score hybride = 0.7 * similarité_sémantique
                  + 0.15 * boost_frustration
                  + 0.10 * boost_sentiment_match
                  + 0.05 * boost_récence
    """
    now = datetime.now()
    qlow = query.lower()

    # Détecter si la question porte sur un sentiment particulier
    target_sentiment = None
    if any(k in qlow for k in ["négatif","negatif","mécontent","mécontents","insatisf"]):
        target_sentiment = "NEGATIF"
    elif any(k in qlow for k in ["positif","satisfait","content","heureux"]):
        target_sentiment = "POSITIF"

    for c in candidates:
        base = c.get("similarity_score", 0.0)

        # Boost frustration
        frust_boost = 0.08 if c.get("frustration_detectee") else 0.0

        # Boost sentiment cible
        sent_boost = 0.0
        if target_sentiment and c.get("sentiment_label") == target_sentiment:
            sent_boost = 0.06

        # Boost récence (commentaires des 6 derniers mois)
        recency_boost = 0.0
        try:
            date_str = (c.get("date_originale") or c.get("date_clean") or "")
            if date_str:
                if "/" in date_str:
                    dt = datetime.strptime(date_str.split()[0], "%d/%m/%Y")
                else:
                    dt = datetime.fromisoformat(str(date_str)[:10])
                days_old = (now - dt).days
                if days_old < 180:
                    recency_boost = 0.04 * (1 - days_old / 180)
        except Exception:
            pass

        # Score final
        c["rerank_score"] = (
            0.70 * base
            + frust_boost
            + sent_boost
            + recency_boost
        )

    return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)


# ─────────────────────────────────────────────────────────────
# CLASSE PRINCIPALE
# ─────────────────────────────────────────────────────────────

class SimpleRAG:
    """
    Index vectoriel pour retrouver les commentaires les plus similaires
    à une requête en langage naturel (arabe, darija, français).
    """

    def __init__(self, comments: list[dict]):
        self.comments   = comments
        self.embedder   = None
        self.tfidf      = None
        self.embeddings = None
        self._build()

    # ── Construction ──────────────────────────────────────────
    def _build(self) -> None:
        texts = [self._comment_to_text(c) for c in self.comments]
        print(f"🔨 Construction index RAG sur {len(texts)} commentaires…")

        # Essai sentence-transformers
        self.embedder = _load_embedder()
        if self.embedder is not None:
            self._build_dense(texts)
        else:
            # Fallback TF-IDF
            self.tfidf = TFIDFIndex(texts)
            print("ℹ️  Index TF-IDF construit")

    def _build_dense(self, texts: list[str]) -> None:
        all_vecs = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            vecs  = self.embedder.encode(batch, show_progress_bar=False, normalize_embeddings=True)
            all_vecs.append(vecs)
            if i % (BATCH_SIZE * 10) == 0:
                print(f"  … {i}/{len(texts)} embeddings calculés")
        self.embeddings = np.vstack(all_vecs).astype(np.float32)
        print(f"✅ Index dense construit : {self.embeddings.shape}")

    # ── Texte enrichi pour l'indexation ───────────────────────
    @staticmethod
    def _comment_to_text(c: dict) -> str:
        """Concatène les champs pertinents pour un meilleur embedding."""
        parts = [
            c.get("commentaire_original", ""),
            c.get("commentaire_clean", ""),
            c.get("theme_pred", ""),
            c.get("reason_pred", ""),
        ]
        return " ".join(p for p in parts if p).strip()

    # ── Recherche ─────────────────────────────────────────────
    def search(
        self,
        query: str,
        k: int = TOP_K_RETURN,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Retourne les k commentaires les plus similaires à la requête.

        filters (optionnel) :
            source, sentiment_label, theme_pred, frustration_detectee,
            date_debut (datetime), date_fin (datetime)
        """
        if not self.comments:
            return []

        # 1. Récupérer les index candidats
        candidates_idx = self._raw_search(query, k=TOP_K_RETRIEVE)

        # 2. Enrichir avec les métadonnées et appliquer les filtres
        results = []
        for idx, score in candidates_idx:
            c = dict(self.comments[idx])  # copie
            c["similarity_score"] = score

            # Filtres
            if filters:
                if not self._passes_filters(c, filters):
                    continue

            # Seuil minimal de similarité
            if score < 0.10:
                continue

            results.append(c)

        # 3. Reranking
        results = _rerank(results, query, filters or {})

        return results[:k]

    def _raw_search(self, query: str, k: int) -> list[tuple[int, float]]:
        if self.embedder is not None and self.embeddings is not None:
            qvec = self.embedder.encode([query], normalize_embeddings=True)[0]
            sims = self.embeddings.dot(qvec)
            top  = np.argsort(sims)[::-1][:k]
            return [(int(i), float(sims[i])) for i in top]
        elif self.tfidf is not None:
            return self.tfidf.search(query, k=k)
        return []

    @staticmethod
    def _passes_filters(c: dict, filters: dict) -> bool:
        for key, value in filters.items():
            if value is None or value == "all":
                continue
            if key == "source" and c.get("source", "").lower() != str(value).lower():
                return False
            if key == "sentiment_label" and c.get("sentiment_label") != value:
                return False
            if key == "theme_pred" and c.get("theme_pred") != value:
                return False
            if key == "frustration_detectee" and bool(c.get("frustration_detectee")) != bool(value):
                return False
            if key == "date_debut":
                try:
                    ds = c.get("date_originale") or c.get("date_clean") or ""
                    dt = datetime.fromisoformat(str(ds)[:10]) if ds else None
                    if dt and dt < value:
                        return False
                except Exception:
                    pass
            if key == "date_fin":
                try:
                    ds = c.get("date_originale") or c.get("date_clean") or ""
                    dt = datetime.fromisoformat(str(ds)[:10]) if ds else None
                    if dt and dt > value:
                        return False
                except Exception:
                    pass
        return True

    # ── Analyse agrégée (pour le chatbot tendances) ────────────
    def analyze_topic(
        self,
        query: str,
        k: int = 50,
        filters: Optional[dict] = None,
    ) -> dict:
        """
        Récupère les k commentaires les plus proches et calcule des
        statistiques agrégées utiles pour l'analyste.
        """
        comments = self.search(query, k=k, filters=filters)
        if not comments:
            return {"total": 0, "comments": []}

        sentiments = Counter(c.get("sentiment_label", "NEUTRE") for c in comments)
        themes     = Counter(c.get("theme_pred", "autre") for c in comments)
        sources    = Counter(c.get("source", "?") for c in comments)
        langues    = Counter(c.get("langue_detectee", "?") for c in comments)
        frustrated = [c for c in comments if c.get("frustration_detectee")]

        total = len(comments)
        return {
            "total":        total,
            "sentiments":   dict(sentiments),
            "taux_negatif": round(sentiments.get("NEGATIF", 0) / total * 100, 1),
            "taux_positif": round(sentiments.get("POSITIF", 0) / total * 100, 1),
            "themes":       dict(themes.most_common(5)),
            "sources":      dict(sources.most_common(5)),
            "langues":      dict(langues.most_common(4)),
            "nb_frustres":  len(frustrated),
            "taux_frustration": round(len(frustrated) / total * 100, 1),
            "top_frustra":  frustrated[:3],
            "comments":     comments[:k],
        }

    # ── Détection d'alertes / anomalies ───────────────────────
    def detect_alerts(self, window_days: int = 7) -> list[dict]:
        """
        Détecte les pics de commentaires négatifs récents
        (comparaison semaine courante vs semaine précédente).
        """
        now   = datetime.now()
        week1 = now - timedelta(days=window_days)
        week2 = now - timedelta(days=window_days * 2)

        current, previous = [], []
        for c in self.comments:
            try:
                ds  = c.get("date_originale") or c.get("date_clean") or ""
                dt  = datetime.fromisoformat(str(ds)[:10]) if ds else None
                if dt:
                    if dt >= week1:
                        current.append(c)
                    elif dt >= week2:
                        previous.append(c)
            except Exception:
                pass

        if not current:
            return []

        def neg_rate(lst):
            if not lst:
                return 0.0
            return sum(1 for x in lst if x.get("sentiment_label") == "NEGATIF") / len(lst)

        alerts = []
        cur_neg = neg_rate(current)
        prv_neg = neg_rate(previous)

        if cur_neg > 0.6:
            alerts.append({
                "type":    "high_negative",
                "message": f"🔴 Taux négatif élevé cette semaine : {cur_neg*100:.0f}%",
                "severity": "high",
                "metric":   cur_neg,
            })
        elif prv_neg > 0 and cur_neg > prv_neg * 1.5:
            alerts.append({
                "type":    "spike_negative",
                "message": f"⚠️ Hausse des avis négatifs : +{(cur_neg - prv_neg)*100:.0f}pts vs semaine passée",
                "severity": "medium",
                "metric":   cur_neg - prv_neg,
            })

        # Thèmes en hausse
        cur_themes = Counter(c.get("theme_pred", "autre") for c in current
                             if c.get("sentiment_label") == "NEGATIF")
        prv_themes = Counter(c.get("theme_pred", "autre") for c in previous
                             if c.get("sentiment_label") == "NEGATIF")
        for theme, cnt in cur_themes.most_common(3):
            prv_cnt = prv_themes.get(theme, 0)
            if cnt > 5 and (prv_cnt == 0 or cnt / (prv_cnt + 1) > 1.8):
                alerts.append({
                    "type":    "theme_spike",
                    "message": f"📈 Thème '{theme}' en forte hausse ({cnt} mentions négatives)",
                    "severity": "medium",
                    "theme":   theme,
                    "metric":   cnt,
                })

        return sorted(alerts, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]])

    # ── Cache disque ──────────────────────────────────────────
    def save_cache(self) -> None:
        try:
            with open(INDEX_CACHE, "wb") as f:
                pickle.dump({
                    "comments":   self.comments,
                    "embeddings": self.embeddings,
                    "tfidf":      self.tfidf,
                    "model_name": EMBEDDING_MODEL,
                    "built_at":   datetime.now().isoformat(),
                }, f, protocol=4)
            print(f"💾 Cache RAG sauvegardé : {INDEX_CACHE}")
        except Exception as e:
            print(f"⚠️  Impossible de sauvegarder le cache RAG : {e}")

    @classmethod
    def load_cache(cls) -> "SimpleRAG":
        with open(INDEX_CACHE, "rb") as f:
            data = pickle.load(f)
        if data.get("model_name") != EMBEDDING_MODEL:
            raise ValueError("Modèle d'embedding différent — reconstruction nécessaire")
        obj = object.__new__(cls)
        obj.comments   = data["comments"]
        obj.embeddings = data["embeddings"]
        obj.tfidf      = data["tfidf"]
        obj.embedder   = _load_embedder() if data["embeddings"] is not None else None
        print(f"✅ Cache RAG chargé ({len(obj.comments)} commentaires, "
              f"construit le {data.get('built_at','?')[:10]})")
        return obj


# ─────────────────────────────────────────────────────────────
# FACTORY
# ─────────────────────────────────────────────────────────────

def get_rag_engine(
    comments: Optional[list[dict]] = None,
    force_rebuild: bool = False,
) -> SimpleRAG:
    """
    Retourne l'instance globale du moteur RAG.
    Reconstruit si nécessaire depuis MongoDB ou depuis le cache disque.
    """
    global _RAG_ENGINE

    if _RAG_ENGINE is not None and not force_rebuild:
        return _RAG_ENGINE

    # Charger les commentaires depuis MongoDB si non fournis
    if comments is None:
        try:
            from database import get_all_comments
            comments = get_all_comments(limit=50000)
            print(f"📥 {len(comments)} commentaires chargés depuis MongoDB pour le RAG")
        except Exception as e:
            print(f"⚠️  Impossible de charger les commentaires : {e}")
            comments = []

    if not comments:
        print("⚠️  Aucun commentaire — index RAG vide")
        _RAG_ENGINE = SimpleRAG([])
        return _RAG_ENGINE

    # Essayer le cache disque (si pas force_rebuild)
    if os.path.exists(INDEX_CACHE) and not force_rebuild:
        try:
            cached = SimpleRAG.load_cache()
            # Vérifier que le cache correspond aux données actuelles
            if len(cached.comments) >= len(comments) * 0.9:
                _RAG_ENGINE = cached
                return _RAG_ENGINE
            else:
                print("ℹ️  Cache périmé (nouvelles données) — reconstruction")
        except Exception as e:
            print(f"⚠️  Cache invalide ({e}) — reconstruction")

    # Construire l'index
    _RAG_ENGINE = SimpleRAG(comments)
    _RAG_ENGINE.save_cache()
    return _RAG_ENGINE


def rebuild_rag_engine() -> SimpleRAG:
    """Force la reconstruction complète de l'index."""
    global _RAG_ENGINE
    _RAG_ENGINE = None
    if os.path.exists(INDEX_CACHE):
        os.remove(INDEX_CACHE)
    return get_rag_engine(force_rebuild=True)
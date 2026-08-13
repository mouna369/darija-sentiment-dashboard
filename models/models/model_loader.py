# # # models/model_loader.py - Version API Kaggle
# # import requests
# # import time
# # from functools import lru_cache

# # # Configuration - À METTRE À JOUR APRÈS CHAQUE DÉMARRAGE KAGGLE
# # # Copier l'URL ngrok depuis ton notebook Kaggle
# # KAGGLE_API_URL = "https://imprint-nerd-wok.ngrok-free.dev"  # ← À MODIFIER

# # # Timeout et retry
# # TIMEOUT = 30
# # RETRY_COUNT = 3

# # class KaggleAPIClient:
# #     def __init__(self, api_url=KAGGLE_API_URL):
# #         self.api_url = api_url.rstrip('/')
# #         self.ready = False
# #         self._check_health()
    
# #     def _check_health(self):
# #         """Vérifie que l'API est accessible"""
# #         try:
# #             resp = requests.get(f"{self.api_url}/health", timeout=5)
# #             self.ready = resp.status_code == 200
# #             if self.ready:
# #                 print(f"✅ API Kaggle connectée: {self.api_url}")
# #             return self.ready
# #         except:
# #             self.ready = False
# #             print(f"⚠️ API Kaggle indisponible: {self.api_url}")
# #             return False
    
# #     def analyze(self, text: str) -> dict:
# #         """Appelle l'API Kaggle pour analyser un commentaire"""
# #         if not self.ready:
# #             self._check_health()
# #             if not self.ready:
# #                 return self._fallback_response(text)
        
# #         for attempt in range(RETRY_COUNT):
# #             try:
# #                 resp = requests.post(
# #                     f"{self.api_url}/predict",
# #                     json={"commentaire": text},
# #                     timeout=TIMEOUT
# #                 )
# #                 if resp.status_code == 200:
# #                     return resp.json()
# #             except Exception as e:
# #                 print(f"⚠️ Tentative {attempt+1}/{RETRY_COUNT} échouée: {e}")
# #                 if attempt < RETRY_COUNT - 1:
# #                     time.sleep(2)
        
# #         return self._fallback_response(text)
    
# #     def _fallback_response(self, text: str) -> dict:
# #         """Réponse par défaut si API indisponible"""
# #         return {
# #             "sentiment_label": "NEUTRE",
# #             "sentiment_confidence": 0.5,
# #             "sentiment_probabilities": {"NEGATIF": 0.33, "NEUTRE": 0.34, "POSITIF": 0.33},
# #             "reason_pred": "autre",
# #             "reason_confiance": 0.0
# #         }

# # # Instance globale
# # _client = None

# # def get_client():
# #     global _client
# #     if _client is None:
# #         _client = KaggleAPIClient()
# #     return _client

# # def analyze_comment(text: str) -> dict:
# #     """Pipeline complet via API Kaggle"""
# #     client = get_client()
# #     result = client.analyze(text)
    
# #     # Normaliser les labels (votre code attend "negatif/neutre/positif" en minuscules)
# #     sentiment_map = {"NEGATIF": "negatif", "NEUTRE": "neutre", "POSITIF": "positif"}
    
# #     return {
# #         "sentiment_label": sentiment_map.get(result.get("sentiment_label", "NEUTRE"), "neutre"),
# #         "sentiment_confidence": result.get("sentiment_confiance", 0.5),
# #         "sentiment_probs": {
# #             "negatif": result.get("sentiment_probabilities", {}).get("NEGATIF", 0.33),
# #             "neutre": result.get("sentiment_probabilities", {}).get("NEUTRE", 0.34),
# #             "positif": result.get("sentiment_probabilities", {}).get("POSITIF", 0.33),
# #         },
# #         "reason_pred": result.get("reason_pred", "autre"),
# #         "reason_confidence": result.get("reason_confiance", 0.0),
# #     }
# # models/model_loader.py
# import requests
# import time

# # ⚠️ METS À JOUR CETTE URL APRÈS CHAQUE DÉMARRAGE KAGGLE ⚠️
# KAGGLE_API_URL = "https://imprint-nerd-wok.ngrok-free.dev"

# class KaggleAPIClient:
#     def __init__(self, api_url=KAGGLE_API_URL):
#         self.api_url = api_url.rstrip('/')
#         self.ready = False
#         self._check_health()
    
#     def _check_health(self):
#         try:
#             resp = requests.get(f"{self.api_url}/health", timeout=5)
#             self.ready = resp.status_code == 200
#             if self.ready:
#                 print(f"✅ API Kaggle connectée: {self.api_url}")
#             return self.ready
#         except:
#             self.ready = False
#             print(f"⚠️ API Kaggle indisponible: {self.api_url}")
#             return False
    
#     def analyze(self, text: str) -> dict:
#         if not self.ready:
#             self._check_health()
        
#         try:
#             resp = requests.post(
#                 f"{self.api_url}/predict",
#                 json={"commentaire": text},
#                 timeout=30
#             )
#             if resp.status_code == 200:
#                 return resp.json()
#         except Exception as e:
#             print(f"Erreur API: {e}")
        
#         # Fallback
#         return {
#             "sentiment_label": "NEUTRE",
#             "sentiment_confiance": 0.5,
#             "sentiment_probabilities": {"NEGATIF": 0.33, "NEUTRE": 0.34, "POSITIF": 0.33},
#             "reason_pred": "autre",
#             "reason_confiance": 0.0
#         }

# _client = None

# def get_client():
#     global _client
#     if _client is None:
#         _client = KaggleAPIClient()
#     return _client

# def analyze_comment(text: str) -> dict:
#     """Pipeline complet via API Kaggle - retourne le format attendu par le chatbot"""
#     client = get_client()
#     result = client.analyze(text)
    
#     # Conversion NEGATIF/NEUTRE/POSITIF → negatif/neutre/positif
#     sentiment_map = {"NEGATIF": "negatif", "NEUTRE": "neutre", "POSITIF": "positif"}
    
#     return {
#         "sentiment_label": sentiment_map.get(result.get("sentiment_label", "NEUTRE"), "neutre"),
#         "sentiment_confidence": result.get("sentiment_confiance", 0.5),
#         "sentiment_probs": {
#             "negatif": result.get("sentiment_probabilities", {}).get("NEGATIF", 0.33),
#             "neutre": result.get("sentiment_probabilities", {}).get("NEUTRE", 0.34),
#             "positif": result.get("sentiment_probabilities", {}).get("POSITIF", 0.33),
#         },
#         "reason_pred": result.get("reason_pred", "autre"),
#         "reason_confidence": result.get("reason_confiance", 0.0),
#     }
# models/model_loader.py
"""
Client API Kaggle pour les modèles DziriBERT (sentiment + reason).
L'URL ngrok doit être mise à jour après chaque démarrage Kaggle.
"""

import requests
import time
import os
import json
import hashlib
from datetime import datetime, timedelta
from functools import lru_cache

# ─────────────────────────────────────────────────────────────
# CONFIGURATION — mettre à jour après chaque démarrage Kaggle
# ─────────────────────────────────────────────────────────────
KAGGLE_API_URL = os.environ.get(
    "KAGGLE_API_URL",
    "https://imprint-nerd-wok.ngrok-free.dev"
)

TIMEOUT      = 30
RETRY_COUNT  = 3
RETRY_DELAY  = 2  # secondes entre les tentatives

# Cache en mémoire pour éviter des appels répétés
_PREDICTION_CACHE: dict = {}
_CACHE_TTL_MINUTES = 60  # les prédictions sont valides 1 heure

# ─────────────────────────────────────────────────────────────
# LABELS & MAPPAGE
# ─────────────────────────────────────────────────────────────
SENTIMENT_MAP = {
    "NEGATIF": "negatif",
    "NEUTRE":  "neutre",
    "POSITIF": "positif",
    # lowercase déjà OK
    "negatif": "negatif",
    "neutre":  "neutre",
    "positif": "positif",
}

REASON_LABELS_FR = {
    "reseau":         "Problème réseau",
    "hors_sujet":     "Hors sujet",
    "service_client": "Service client",
    "facturation":    "Facturation",
    "debit":          "Débit / vitesse",
    "fibre":          "Fibre optique",
    "4g":             "Couverture 4G",
    "adsl":           "Connexion ADSL",
    "autre":          "Autre",
    "panne":          "Panne / coupure",
    "installation":   "Installation",
    "prix":           "Prix / tarif",
}

# ─────────────────────────────────────────────────────────────
# CLIENT KAGGLE API
# ─────────────────────────────────────────────────────────────

class KaggleAPIClient:
    def __init__(self, api_url: str = KAGGLE_API_URL):
        self.api_url   = api_url.rstrip('/')
        self.ready     = False
        self.last_check: datetime | None = None
        self._check_health()

    # ── Santé ─────────────────────────────────────────────────
    def _check_health(self) -> bool:
        """Vérifie la disponibilité de l'API (au plus toutes les 30 s)."""
        now = datetime.now()
        if (self.last_check is not None
                and (now - self.last_check).seconds < 30
                and self.ready):
            return True
        try:
            resp = requests.get(
                f"{self.api_url}/health",
                timeout=5,
                headers={"ngrok-skip-browser-warning": "true"}
            )
            self.ready = resp.status_code == 200
        except Exception:
            self.ready = False
        self.last_check = now
        status = "✅" if self.ready else "⚠️"
        print(f"{status} API Kaggle {'connectée' if self.ready else 'indisponible'}: {self.api_url}")
        return self.ready

    def update_url(self, new_url: str) -> None:
        """Met à jour l'URL ngrok sans redémarrer l'appli."""
        self.api_url   = new_url.rstrip('/')
        self.ready     = False
        self.last_check = None
        _PREDICTION_CACHE.clear()
        self._check_health()

    # ── Prédiction ────────────────────────────────────────────
    def analyze(self, text: str) -> dict:
        """Envoie un texte à l'API et retourne la prédiction brute."""
        # 1. Vérifier le cache
        cache_key = _cache_key(text)
        cached    = _get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 2. Vérifier la santé si nécessaire
        if not self.ready:
            self._check_health()

        # 3. Appel avec retry
        if self.ready:
            for attempt in range(RETRY_COUNT):
                try:
                    resp = requests.post(
                        f"{self.api_url}/predict",
                        json={"commentaire": text},
                        timeout=TIMEOUT,
                        headers={"ngrok-skip-browser-warning": "true"}
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        _set_cache(cache_key, result)
                        return result
                    print(f"⚠️ HTTP {resp.status_code} tentative {attempt+1}/{RETRY_COUNT}")
                except requests.exceptions.Timeout:
                    print(f"⏱️  Timeout tentative {attempt+1}/{RETRY_COUNT}")
                except Exception as e:
                    print(f"⚠️  Erreur tentative {attempt+1}/{RETRY_COUNT}: {e}")
                if attempt < RETRY_COUNT - 1:
                    time.sleep(RETRY_DELAY)
            # Après les retries, marquer l'API comme down
            self.ready = False

        # 4. Fallback déterministe si API indisponible
        return _fallback_response(text)

    # ── Batch ─────────────────────────────────────────────────
    def analyze_batch(self, texts: list[str]) -> list[dict]:
        """Analyse une liste de textes (utile pour le RAG)."""
        results = []
        for t in texts:
            results.append(self.analyze(t))
            time.sleep(0.05)  # tiny delay pour ne pas saturer l'API
        return results


# ─────────────────────────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────────────────────────

def _cache_key(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def _get_from_cache(key: str) -> dict | None:
    entry = _PREDICTION_CACHE.get(key)
    if entry is None:
        return None
    if datetime.now() - entry["ts"] > timedelta(minutes=_CACHE_TTL_MINUTES):
        del _PREDICTION_CACHE[key]
        return None
    return entry["data"]

def _set_cache(key: str, data: dict) -> None:
    # Limiter la taille du cache
    if len(_PREDICTION_CACHE) > 5000:
        oldest = min(_PREDICTION_CACHE, key=lambda k: _PREDICTION_CACHE[k]["ts"])
        del _PREDICTION_CACHE[oldest]
    _PREDICTION_CACHE[key] = {"data": data, "ts": datetime.now()}


# ─────────────────────────────────────────────────────────────
# FALLBACK INTELLIGENT
# ─────────────────────────────────────────────────────────────

_NEGATIVE_KEYWORDS = {
    "لا","ما","مش","مو","بطيء","بطيئة","خسارة","مصيبة","نعس","نعاس",
    "lent","lente","nul","nulle","mauvais","problème","panne","coupure",
    "cher","arnaque","honte","catastrophe","horrible","déçu",
    "slow","bad","worst","terrible","awful","outage","down"
}
_POSITIVE_KEYWORDS = {
    "بارك","شكرا","شكراً","مزيان","رائع","ممتاز","زين","برشا",
    "merci","excellent","parfait","super","bravo","rapide","bien",
    "great","thanks","perfect","fast","good","awesome"
}
_REASON_KEYWORDS = {
    "reseau":         ["réseau","شبكة","network","connexion","كونكسيون"],
    "debit":          ["lent","بطيء","débit","vitesse","speed","سرعة"],
    "fibre":          ["fibre","فيبر","fiber"],
    "4g":             ["4g","4G","lte","LTE"],
    "adsl":           ["adsl","ADSL","dsl"],
    "service_client": ["service","client","hotline","support","خدمة"],
    "facturation":    ["facture","paiement","prix","tarif","cher","فاتورة"],
    "panne":          ["panne","coupure","انقطاع","down","outage"],
    "installation":   ["installation","installer","technicien","تقني"],
}

def _fallback_response(text: str) -> dict:
    """Analyse heuristique légère quand l'API Kaggle est indisponible."""
    tl = text.lower()
    words = set(tl.split())

    # Sentiment
    pos = sum(1 for w in _POSITIVE_KEYWORDS if w in tl)
    neg = sum(1 for w in _NEGATIVE_KEYWORDS if w in tl)
    if pos > neg:
        sentiment, conf = "POSITIF", 0.65
        probs = {"NEGATIF": 0.10, "NEUTRE": 0.25, "POSITIF": 0.65}
    elif neg > pos:
        sentiment, conf = "NEGATIF", 0.70
        probs = {"NEGATIF": 0.70, "NEUTRE": 0.20, "POSITIF": 0.10}
    else:
        sentiment, conf = "NEUTRE", 0.55
        probs = {"NEGATIF": 0.20, "NEUTRE": 0.55, "POSITIF": 0.25}

    # Raison
    reason, r_conf = "autre", 0.30
    for label, kws in _REASON_KEYWORDS.items():
        if any(kw in tl for kw in kws):
            reason, r_conf = label, 0.55
            break

    return {
        "sentiment_label":        sentiment,
        "sentiment_confiance":    conf,
        "sentiment_probabilities": probs,
        "reason_pred":            reason,
        "reason_confiance":       r_conf,
        "_fallback":              True,   # flag pour savoir qu'on est en mode dégradé
    }


# ─────────────────────────────────────────────────────────────
# SINGLETON CLIENT
# ─────────────────────────────────────────────────────────────

_client: KaggleAPIClient | None = None

def get_client() -> KaggleAPIClient:
    global _client
    if _client is None:
        _client = KaggleAPIClient()
    return _client

def set_kaggle_url(new_url: str) -> None:
    """Permet de changer l'URL ngrok depuis le dashboard sans redémarrer."""
    global _client
    if _client is None:
        _client = KaggleAPIClient(new_url)
    else:
        _client.update_url(new_url)

def is_api_available() -> bool:
    return get_client().ready


# ─────────────────────────────────────────────────────────────
# INTERFACE PUBLIQUE
# ─────────────────────────────────────────────────────────────

def analyze_comment(text: str) -> dict:
    """
    Analyse un commentaire via l'API Kaggle (DziriBERT).
    Retourne un dict normalisé attendu par chatbot.py et rag_engine.py.
    """
    client = get_client()
    raw    = client.analyze(text)

    sentiment_raw = raw.get("sentiment_label", "NEUTRE")
    reason_raw    = raw.get("reason_pred", "autre")

    return {
        "sentiment_label":    SENTIMENT_MAP.get(sentiment_raw, "neutre"),
        "sentiment_label_raw": sentiment_raw,
        "sentiment_confidence": float(raw.get("sentiment_confiance", 0.5)),
        "sentiment_probs": {
            "negatif": float(raw.get("sentiment_probabilities", {}).get("NEGATIF", 0.33)),
            "neutre":  float(raw.get("sentiment_probabilities", {}).get("NEUTRE",  0.34)),
            "positif": float(raw.get("sentiment_probabilities", {}).get("POSITIF", 0.33)),
        },
        "reason_pred":       reason_raw,
        "reason_label_fr":   REASON_LABELS_FR.get(reason_raw, reason_raw),
        "reason_confidence": float(raw.get("reason_confiance", 0.0)),
        "is_fallback":       raw.get("_fallback", False),
    }


def analyze_comment_batch(texts: list[str]) -> list[dict]:
    """Analyse un lot de textes."""
    client  = get_client()
    results = []
    for text in texts:
        results.append(analyze_comment(text))
    return results


def get_api_status() -> dict:
    """Retourne un dict de statut pour l'affichage dashboard."""
    client     = get_client()
    cache_size = len(_PREDICTION_CACHE)
    return {
        "ready":      client.ready,
        "url":        client.api_url,
        "cache_size": cache_size,
        "last_check": client.last_check.strftime("%H:%M:%S") if client.last_check else "jamais",
    }
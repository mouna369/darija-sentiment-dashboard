
"""
database.py
Module de connexion MongoDB – Algérie Télécom Dashboard
Base : telecom_algerie | Collection : commentaires_predictions_final
Version corrigée : sans limite, dates MongoDB robustes
"""

import os
import random
from datetime import datetime, timedelta
from collections import defaultdict

# ─── CONFIG ────────────────────────────────────────────────────────────────────

MONGO_URI        = os.getenv("MONGO_URI", "mongodb://localhost:27018/?directConnection=true")
DB_NAME          = "telecom_algerie"
COLLECTION_NAME  = "commentaires_predictions_final"

# ─── CONNEXION ─────────────────────────────────────────────────────────────────

_client = None
_col    = None
MONGO_AVAILABLE = False

try:
    from pymongo import MongoClient
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2_000)
    _client.admin.command("ping")
    _col = _client[DB_NAME][COLLECTION_NAME]
    MONGO_AVAILABLE = True
    print(f"✅ MongoDB connecté → {DB_NAME}.{COLLECTION_NAME}")
except Exception as exc:
    print(f"⚠️ MongoDB non disponible ({exc}). Mode démo activé.")

# ─── MAPPING SENTIMENT ─────────────────────────────────────────────────────────

_TO_DASH   = {"POSITIF": "positif", "NEGATIF": "négatif", "NEUTRE": "neutre"}
_FROM_DASH = {v: k for k, v in _TO_DASH.items()}

# ─── HELPER : parse une date MongoDB (dict $date, datetime, string) ──────────

def _parse_mongo_date(val):
    """
    Convertit n'importe quelle représentation de date en datetime Python.
    Gère : dict {"$date": "..."}, datetime natif, string ISO, string dd/mm/yyyy
    """
    if val is None:
        return None

    # Déjà un datetime Python
    if isinstance(val, datetime):
        return val

    # Dict MongoDB {"$date": "2025-12-11T18:29:00.000Z"} ou {"$date": 1234567890}
    if isinstance(val, dict):
        inner = val.get("$date")
        if inner is None:
            return None
        if isinstance(inner, (int, float)):
            # timestamp ms
            try:
                return datetime.utcfromtimestamp(inner / 1000)
            except:
                return None
        if isinstance(inner, str):
            try:
                return datetime.fromisoformat(inner.replace("Z", "+00:00")).replace(tzinfo=None)
            except:
                try:
                    return datetime.strptime(inner[:10], "%Y-%m-%d")
                except:
                    return None

    # String
    if isinstance(val, str):
        # ISO: "2025-12-11T18:29:00"
        if "T" in val:
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
            except:
                pass
        # "2025-12-11"
        if len(val) >= 10 and val[4] == "-":
            try:
                return datetime.strptime(val[:10], "%Y-%m-%d")
            except:
                pass
        # "11/12/2025 18:29" ou "11/12/2025"
        if "/" in val:
            part = val.split()[0]
            try:
                return datetime.strptime(part, "%d/%m/%Y")
            except:
                pass

    return None


def _date_to_ymd(val) -> str:
    """Retourne 'YYYY-MM-DD' ou '' depuis n'importe quelle valeur de date."""
    dt = _parse_mongo_date(val)
    if dt:
        return dt.strftime("%Y-%m-%d")
    return ""


# ─── TRANSFORMATION COMPLÈTE CORRIGÉE ──────────────────────────────────────────

def _transform(doc: dict) -> dict:
    """
    Normalise un document MongoDB vers le format attendu par le dashboard.
    Toutes les dates sont converties en datetime Python standard (naïf).
    """
    # Sentiment
    sentiment_label = doc.get("sentiment_label", doc.get("label_prediction", doc.get("sentiment", "NEUTRE")))
    if sentiment_label in _TO_DASH:
        sentiment = _TO_DASH[sentiment_label]
    elif sentiment_label in ["positif", "négatif", "neutre"]:
        sentiment = sentiment_label
    else:
        sentiment = "neutre"

    # Score
    raw_score = doc.get("sentiment_score",
                doc.get("score_prediction",
                doc.get("score_raw",
                doc.get("score_sentiment", 0))))
    raw_score = raw_score if isinstance(raw_score, (int, float)) else 0.0
    score_sentiment = round((raw_score + 1) / 2, 3) if -1 <= raw_score <= 1 else round(raw_score, 3)

    # Métriques
    frustration       = doc.get("frustration_detectee", doc.get("frustration", False))
    intensite_negative = doc.get("intensite_negative", 0.0)
    has_negatif        = doc.get("has_negatif", False)
    prediction_churn   = doc.get("prediction_churn",
                                  frustration or
                                  (sentiment == "négatif" and intensite_negative > 0.5) or
                                  has_negatif)
    moderateur_repondu = doc.get("a_repondu", doc.get("moderateur_repondu", False))
    demande_reponse    = doc.get("demande_reponse", False)
    incertain          = doc.get("sentiment_incertain", doc.get("incertain", False))
    nb_mots_negatifs   = doc.get("nb_mots_negatifs", 0)

    # Dates – conversion robuste vers datetime Python naïf
    date_clean      = _parse_mongo_date(doc.get("date_clean"))
    date_annotation = _parse_mongo_date(doc.get("date_annotation"))
    date_originale_raw = doc.get("date_originale", "")

    # Date principale pour les calculs
    date_val = date_clean or date_annotation or _parse_mongo_date(date_originale_raw) or datetime.now()

    # "YYYY-MM-DD" précalculé pour les filtres rapides
    date_ymd = date_val.strftime("%Y-%m-%d")

    # mois : préférer le champ stocké sinon le dériver de date_val
    mois_stored = doc.get("mois", "")
    if not mois_stored and date_val:
        mois_stored = date_val.strftime("%Y-%m")

    return {
        # Identifiants
        "_id":         str(doc.get("_id", "")),
        "original_id": doc.get("original_id", ""),
        "batch_id":    doc.get("batch_id", 0),

        # Auteur / géographie
        "client":  doc.get("auteur", doc.get("client", f"Client_{str(doc.get('_id'))[-6:]}")),
        "wilaya":  doc.get("wilaya", doc.get("region", "Non spécifié")),
        "ville":   doc.get("ville", ""),
        "region":  doc.get("region", ""),

        # Contenu
        "service":                doc.get("service", doc.get("source", "Unknown")),
        "commentaire":            doc.get("commentaire_original", doc.get("commentaire", doc.get("texte", ""))),
        "commentaire_original":   doc.get("commentaire_original", doc.get("commentaire", doc.get("texte", ""))),
        "commentaire_normalized": doc.get("commentaire_normalized", ""),

        # Sentiment
        "sentiment":               sentiment,
        "sentiment_label":         sentiment_label,
        "sentiment_label_brut":    doc.get("sentiment_label_brut", doc.get("label_brut", "")),
        "score_sentiment":         score_sentiment,
        "sentiment_score":         raw_score,
        "sentiment_confiance":     round(doc.get("sentiment_confiance", doc.get("confidence", 0.0)), 3),
        "sentiment_incertain":     incertain,
        "sentiment_probabilities": doc.get("sentiment_probabilities", {}),
        "sentiment_num":           -1 if sentiment == "négatif" else (1 if sentiment == "positif" else 0),

        # Prédictions
        "prediction_churn":  prediction_churn,
        "theme_pred":        doc.get("theme_pred", ""),
        "reason_pred":       doc.get("reason_pred", doc.get("raison_pred", "")),
        "reason_confiance":  doc.get("reason_confiance", 0.0),

        # Métriques négatives
        "frustration":            frustration,
        "frustration_detectee":   frustration,
        "has_negatif":            has_negatif,
        "intensite_negative":     intensite_negative,
        "nb_mots_negatifs":       nb_mots_negatifs,
        "categories_negatives":   doc.get("categories_negatives", []),
        "mots_cles_negatifs":     doc.get("mots_cles_negatifs", []),

        # Interaction
        "demande_reponse":    demande_reponse,
        "moderateur_repondu": moderateur_repondu,
        "a_repondu":          moderateur_repondu,
        "a_mention_attente":  doc.get("a_mention_attente", False),
        "a_mention_prv":      doc.get("a_mention_prv", False),

        # Dates – toujours des datetime Python naïfs ou strings
        "date":             date_val,           # datetime Python
        "date_clean":       date_clean,         # datetime Python ou None
        "date_annotation":  date_annotation,    # datetime Python ou None
        "date_originale":   date_originale_raw, # string originale "dd/mm/yyyy HH:MM"
        "date_ymd":         date_ymd,           # "YYYY-MM-DD" pour filtres rapides

        # Temps enrichis
        "annee":           doc.get("annee", date_val.year),
        "mois":            mois_stored,
        "mois_nom":        doc.get("mois_nom", date_val.strftime("%B")),
        "semaine":         doc.get("semaine", 0),
        "heure":           doc.get("heure", date_val.hour),
        "jour_semaine":    doc.get("jour_semaine", date_val.strftime("%A")),
        "jour_semaine_num":doc.get("jour_semaine_num", date_val.weekday()),
        "tranche_horaire": doc.get("tranche_horaire", ""),
        "jour_type":       doc.get("jour_type", "semaine"),
        "est_weekend":     doc.get("est_weekend", False),
        "annee_mois":      doc.get("annee_mois", date_val.strftime("%Y-%m")),
        "annee_semaine":   doc.get("annee_semaine", ""),

        # Stats textuelles
        "longueur_chars":     doc.get("longueur_chars", 0),
        "longueur_mots":      doc.get("longueur_mots", 0),
        "nb_mots_unique":     doc.get("nb_mots_unique", 0),
        "nb_phrases":         doc.get("nb_phrases", 0),
        "longueur_categorie": doc.get("longueur_categorie", "court"),

        # Source / divers
        "source":          doc.get("source", "Unknown"),
        "note":            doc.get("note", round(score_sentiment * 4 + 1, 1)),
        "confidence":      round(doc.get("sentiment_confiance", doc.get("confidence", 0.0)), 3),
        "langue_detectee": doc.get("langue_detectee", ""),
        "langue_confidence":doc.get("langue_confidence", 0.0),
        "langue_scores":   doc.get("langue_scores", {}),
        "version_modele":  doc.get("version_modele", ""),
        "modele_detection":doc.get("modele_detection", ""),
    }


# ─── FONCTIONS DE BASE ─────────────────────────────────────────────────────────

def _fetch(query=None, limit=0):
    """
    Récupère depuis MongoDB sans limite par défaut (limit=0 = tout).
    Passe en mode démo si MongoDB est indisponible.
    """
    if MONGO_AVAILABLE:
        q = query or {}
        cursor = _col.find(q)
        if limit and limit > 0:
            cursor = cursor.limit(limit)
        docs = list(cursor)
        return [_transform(doc) for doc in docs] if docs else []
    return MOCK_DATA

def _fetch_all():
    return _fetch()

# ─── API PRINCIPALE ────────────────────────────────────────────────────────────

def get_all_comments(limit: int = 0,
                     filtre_sentiment=None,
                     filtre_churn=None) -> list:
    """
    Retourne TOUS les commentaires depuis MongoDB (limit=0 → pas de limite).
    """
    if MONGO_AVAILABLE:
        query = {}
        if filtre_sentiment and filtre_sentiment in _FROM_DASH:
            query["sentiment_label"] = _FROM_DASH[filtre_sentiment]

        cursor = _col.find(query).sort("date_annotation", -1)
        if limit and limit > 0:
            cursor = cursor.limit(limit)

        transformed = [_transform(doc) for doc in cursor]

        if filtre_churn is not None:
            transformed = [d for d in transformed if d.get("prediction_churn") == filtre_churn]

        return transformed

    return _make_mock(1000, filtre_sentiment, filtre_churn)


# ─── DONNÉES MOCK ─────────────────────────────────────────────────────────────

_THEMES   = ["reseau_technique","installation_equipement","hors_sujet",
             "facturation_tarifs","service_clientele","application_digitale",
             "suggestions_ameliorations","information_generale","experience_positive"]
_SOURCES  = ["Facebook","IdoomMarket","Instagram","LinkedIn","X","TikTok","YouTube"]
_LANGUES  = ["arabe_darija","latin_francais","mixte","fr","ar","en","ber"]
_WILAYAS  = ["Alger","Oran","Constantine","Annaba","Blida","Sétif",
             "Tizi Ouzou","Béjaïa","Tlemcen","Batna"]
_SENTIMENTS = ["négatif","neutre","positif"]

_COMMENTS = {
    "positif": [
        "Très bon service, connexion rapide et stable.",
        "Excellente qualité, je recommande vivement.",
        "Service client réactif et compétent, bravo !",
        "La fibre est arrivée chez moi, quel bonheur !",
    ],
    "négatif": [
        "La connexion est très lente et instable depuis une semaine.",
        "Problème de déconnexion fréquente, c'est inacceptable.",
        "Service client injoignable, ça fait 3 jours que j'essaie.",
        "Facture anormalement élevée ce mois-ci sans explication.",
    ],
    "neutre": [
        "Service correct, pas d'incident majeur à signaler.",
        "Connexion acceptable pour le prix proposé.",
        "Installation faite dans les délais, rien à redire.",
        "Service standard, comme chez les concurrents.",
    ],
}

def _rand_date(days_back=365):
    return datetime.now() - timedelta(days=random.randint(0, days_back))

def _make_mock(n=1000, filtre_sentiment=None, filtre_churn=None):
    rows = []
    for i in range(n):
        sent = random.choices(_SENTIMENTS, weights=[78, 15, 7])[0]
        if filtre_sentiment and sent != filtre_sentiment:
            continue
        score = {"négatif": random.uniform(-0.95, -0.1),
                 "neutre":  random.uniform(-0.2, 0.2),
                 "positif": random.uniform(0.1, 0.95)}[sent]
        score_sentiment = round((score + 1) / 2, 3)
        dt = _rand_date()
        frus = random.choices([True, False], weights=[30, 70])[0] if sent == "négatif" else False
        intensite = round(random.uniform(0, 1), 2) if sent == "négatif" else 0
        churn = (sent == "négatif" and score_sentiment < 0.35) or frus or (intensite > 0.7)
        if filtre_churn is not None and churn != filtre_churn:
            continue
        commentaire = random.choice(_COMMENTS[sent])
        rows.append({
            "_id": f"mock_{i:06d}",
            "original_id": f"orig_{i:06d}",
            "batch_id": random.randint(0, 10),
            "auteur": f"Client_{i:04d}",
            "commentaire_original": commentaire,
            "commentaire_normalized": commentaire.lower(),
            "sentiment_label": _FROM_DASH.get(sent, "NEUTRE"),
            "sentiment_label_brut": _FROM_DASH.get(sent, "NEUTRE"),
            "sentiment_score": score,
            "sentiment_confiance": round(random.uniform(0.70, 0.99), 3),
            "sentiment_incertain": random.choices([True, False], weights=[2, 98])[0],
            "score_sentiment": score_sentiment,
            "theme_pred": random.choice(_THEMES),
            "reason_pred": random.choice(["autre","probleme_technique","service_client","facturation","reseau"]),
            "reason_confiance": round(random.uniform(0.4, 0.95), 4),
            "source": random.choice(_SOURCES),
            "langue_detectee": random.choice(_LANGUES),
            "langue_confidence": round(random.uniform(0.3, 0.95), 3),
            "wilaya": random.choice(_WILAYAS),
            "frustration_detectee": frus,
            "has_negatif": sent == "négatif",
            "intensite_negative": intensite,
            "nb_mots_negatifs": random.randint(0, 8) if sent == "négatif" else 0,
            "categories_negatives": [],
            "mots_cles_negatifs": [],
            "demande_reponse": random.choices([True, False], weights=[15, 85])[0],
            "a_repondu": random.choices([True, False], weights=[40, 60])[0],
            "a_mention_attente": False,
            "a_mention_prv": False,
            "heure": random.randint(0, 23),
            "tranche_horaire": random.choice(["matin","après-midi","soirée","nuit"]),
            "jour_type": random.choice(["semaine","weekend"]),
            "est_weekend": random.choices([True, False], weights=[30, 70])[0],
            "annee": dt.year,
            "mois": f"{dt.year}-{dt.month:02d}",
            "mois_nom": dt.strftime("%B"),
            "semaine": dt.isocalendar()[1],
            "jour_semaine": dt.strftime("%A"),
            "jour_semaine_num": dt.weekday(),
            "longueur_chars": len(commentaire),
            "longueur_mots": len(commentaire.split()),
            "nb_mots_unique": len(set(commentaire.lower().split())),
            "nb_phrases": max(1, commentaire.count('.') + commentaire.count('!') + commentaire.count('?')),
            "longueur_categorie": "court" if len(commentaire) < 50 else ("moyen" if len(commentaire) < 150 else "long"),
            "date_clean": dt,
            "date_annotation": dt,
            "date_originale": dt.strftime("%d/%m/%Y %H:%M"),
            "prediction_churn": churn,
            "version_modele": "bert_meanpool_v3",
            "modele_detection": "hybrid_v4",
            "annee_mois": f"{dt.year}-{dt.month:02d}",
            "annee_semaine": f"{dt.year}-S{dt.isocalendar()[1]:02d}",
        })
    return rows

MOCK_DATA = _make_mock(1000)

# ─── KPIS GLOBAUX ──────────────────────────────────────────────────────────────

def get_kpis_globaux(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    n = len(data)
    if n == 0:
        return {k: 0 for k in ["total","negatifs","positifs","neutres",
                                "pct_negatif","pct_positif","pct_neutre",
                                "score_sentiment","frustration","pct_frustration",
                                "demande_reponse","pct_demande",
                                "moderateur_repondu","pct_moderateur",
                                "incertains","pct_incertain"]}
    neg  = sum(1 for d in data if d.get("sentiment") == "négatif")
    pos  = sum(1 for d in data if d.get("sentiment") == "positif")
    neu  = sum(1 for d in data if d.get("sentiment") == "neutre")
    frus = sum(1 for d in data if d.get("frustration", False))
    dem  = sum(1 for d in data if d.get("demande_reponse", False))
    mod  = sum(1 for d in data if d.get("moderateur_repondu", False))
    inc  = sum(1 for d in data if d.get("sentiment_incertain", False))
    scores = [d.get("score_sentiment", 0) for d in data]
    avg_score = round(sum(scores) / n, 3)
    return {
        "total": n, "negatifs": neg, "positifs": pos, "neutres": neu,
        "pct_negatif": round(neg/n*100,1), "pct_positif": round(pos/n*100,1),
        "pct_neutre": round(neu/n*100,1), "score_sentiment": avg_score,
        "frustration": frus, "pct_frustration": round(frus/n*100,1),
        "demande_reponse": dem, "pct_demande": round(dem/n*100,1),
        "moderateur_repondu": mod, "pct_moderateur": round(mod/n*100,1),
        "incertains": inc, "pct_incertain": round(inc/n*100,1),
    }

def get_stats():
    k = get_kpis_globaux()
    return {
        "total": k["total"], "positifs": k["positifs"],
        "negatifs": k["negatifs"], "neutres": k["neutres"],
        "churn_risk": k["frustration"], "avg_score": k["score_sentiment"],
        "avg_note": 3.2, "taux_satisfaction": k["pct_positif"],
        "taux_churn": k["pct_frustration"],
    }

def get_collection_info() -> dict:
    if MONGO_AVAILABLE:
        return {
            "connected": True, "count": _col.count_documents({}),
            "db": DB_NAME, "collection": COLLECTION_NAME,
        }
    return {
        "connected": False, "count": len(MOCK_DATA),
        "db": DB_NAME, "collection": COLLECTION_NAME,
    }

def get_recent_comments(n: int = 5) -> list:
    return get_all_comments(limit=n)

def insert_comment(doc: dict) -> bool:
    if not MONGO_AVAILABLE:
        return False
    mongo_doc = {
        "commentaire_original": doc.get("commentaire", ""),
        "sentiment_label": _FROM_DASH.get(doc.get("sentiment", "neutre"), "NEUTRE"),
        "sentiment_score": round(doc.get("score_sentiment", 0.5) * 2 - 1, 3),
        "source": doc.get("service", "Dashboard"),
        "date_annotation": datetime.now(),
        "sentiment_confiance": doc.get("confidence", 0.0),
        "theme_pred": doc.get("theme_pred", None),
        "langue_detectee": doc.get("langue_detectee", None),
    }
    _col.insert_one(mongo_doc)
    return True

# ─── STATISTIQUES PAR DIMENSION ────────────────────────────────────────────────

def get_sentiment_by_wilaya(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    result = {}
    for d in data:
        w = d.get("wilaya", "Non spécifié")
        if w not in result:
            result[w] = {"positif": 0, "négatif": 0, "neutre": 0, "total": 0}
        result[w][d.get("sentiment", "neutre")] += 1
        result[w]["total"] += 1
    return result

def get_churn_by_service(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    result = {}
    for d in data:
        s = d.get("service", d.get("source", "Autre"))
        if s not in result:
            result[s] = {"total": 0, "churn": 0}
        result[s]["total"] += 1
        if d.get("prediction_churn", False):
            result[s]["churn"] += 1
    return result

def get_evolution_mensuelle(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    monthly = defaultdict(lambda: {"total": 0, "neg": 0, "pos": 0, "scores": []})
    for d in data:
        dt = d.get("date")
        if not isinstance(dt, datetime):
            continue
        key = dt.strftime("%Y-%m")
        monthly[key]["total"] += 1
        monthly[key]["neg"]   += 1 if d.get("sentiment") == "négatif" else 0
        monthly[key]["pos"]   += 1 if d.get("sentiment") == "positif" else 0
        monthly[key]["scores"].append(d.get("score_sentiment", 0))
    result = []
    for mois in sorted(monthly.keys()):
        m = monthly[mois]
        n = m["total"]
        result.append({
            "mois": mois, "total": n,
            "pct_negatif": round(m["neg"]/n*100, 2) if n else 0,
            "pct_positif": round(m["pos"]/n*100, 2) if n else 0,
            "score_moyen": round(sum(m["scores"])/len(m["scores"]), 3) if m["scores"] else 0,
        })
    return result

def get_stats_par_theme(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    themes = defaultdict(lambda: {"total": 0, "neg": 0, "scores": [], "frustration": 0, "demande_rep": 0})
    for d in data:
        t = d.get("theme_pred", "autre")
        themes[t]["total"]       += 1
        themes[t]["neg"]         += 1 if d.get("sentiment") == "négatif" else 0
        themes[t]["frustration"] += 1 if d.get("frustration_detectee") else 0
        themes[t]["demande_rep"] += 1 if d.get("demande_reponse") else 0
        themes[t]["scores"].append(d.get("score_sentiment", 0))
    result = []
    for t, v in themes.items():
        n = v["total"]
        result.append({
            "theme": t, "total": n,
            "score_moyen": round(sum(v["scores"])/len(v["scores"]), 3) if v["scores"] else 0,
            "pct_negatif": round(v["neg"]/n*100, 1) if n else 0,
            "frustration": v["frustration"], "demande_rep": v["demande_rep"],
        })
    return sorted(result, key=lambda x: x["pct_negatif"], reverse=True)

def get_stats_par_source(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    sources = defaultdict(lambda: {"total": 0, "neg": 0, "pos": 0, "scores": []})
    for d in data:
        s = d.get("source", "Autre")
        sources[s]["total"] += 1
        sources[s]["neg"]   += 1 if d.get("sentiment") == "négatif" else 0
        sources[s]["pos"]   += 1 if d.get("sentiment") == "positif" else 0
        sources[s]["scores"].append(d.get("score_sentiment", 0))
    result = []
    for s, v in sources.items():
        n = v["total"]
        result.append({
            "source": s, "total": n,
            "pct_negatif": round(v["neg"]/n*100, 1) if n else 0,
            "pct_positif": round(v["pos"]/n*100, 1) if n else 0,
            "score_moyen": round(sum(v["scores"])/len(v["scores"]), 3) if v["scores"] else 0,
            "negatifs": v["neg"],
        })
    return sorted(result, key=lambda x: -x["total"])

def get_stats_par_langue(filtre=None):
    data = _fetch(query=filtre) if filtre else _fetch_all()
    langues = defaultdict(lambda: {"total": 0, "neg": 0, "pos": 0})
    for d in data:
        l = d.get("langue_detectee", "autre")
        langues[l]["total"] += 1
        langues[l]["neg"]   += 1 if d.get("sentiment") == "négatif" else 0
        langues[l]["pos"]   += 1 if d.get("sentiment") == "positif" else 0
    result = []
    for l, v in langues.items():
        n = v["total"]
        result.append({
            "langue": l, "total": n,
            "pct_negatif": round(v["neg"]/n*100, 1) if n else 0,
            "pct_positif": round(v["pos"]/n*100, 1) if n else 0,
        })
    return sorted(result, key=lambda x: -x["total"])


# ─── DEBUG ─────────────────────────────────────────────────────────────────────

def debug_mois_disponibles():
    if not MONGO_AVAILABLE or _col is None:
        print("[DEBUG] MongoDB non disponible")
        return []
    try:
        pipeline = [
            {"$match": {"date_clean": {"$exists": True}}},
            {"$addFields": {"mois": {"$dateToString": {"format": "%Y-%m", "date": "$date_clean"}}}},
            {"$group": {"_id": "$mois", "count": {"$sum": 1}, "avg_score": {"$avg": "$sentiment_score"}}},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        for r in results:
            print(f"  {r['_id']}: {r['count']} avis")
        return results
    except Exception as e:
        print(f"[DEBUG] Erreur: {e}")
        return []


if __name__ == "__main__":
    print("Test _parse_mongo_date:")
    tests = [
        {"$date": "2025-12-11T18:29:00.000Z"},
        {"$date": "2026-04-19T23:10:15.808Z"},
        datetime(2025, 12, 11, 18, 29),
        "11/12/2025 18:29",
        "2025-12-11",
        None,
    ]
    for t in tests:
        print(f"  {str(t)[:40]} → {_parse_mongo_date(t)}")
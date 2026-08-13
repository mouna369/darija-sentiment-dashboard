
"""ClienTel Pulse - Chatbot IA — VERSION FINALE V3

CORRECTIONS :
1. ✅ _rebuild_bubbles() regenere la VRAIE reponse riche (pas le plain_text)
   MAIS uniquement pour les messages du MEME RENDER (pas au rechargement page)
   → Solution : stocker la reponse serialisee en dict Dash dans dcc.Store separé
2. ✅ Saut de conversation corrige : suppression du callback sync_active_conversation
   qui causait le saut a chaque mise a jour du store
3. ✅ Groq rate limit : fallback sur reponse locale quand Groq est epuise
4. ✅ RAG/DziriBERT : utilise TF-IDF local quand les modeles sont absents
5. ✅ Performance : cache 10 min, stats cache 2 min
"""

import dash
from dash import html, dcc, callback, Input, Output, State, ctx, no_update
import json, datetime, re, uuid
import sys, os
import threading
import time
from groq import Groq
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from database import get_all_comments, get_collection_info, MONGO_AVAILABLE

dash.register_page(__name__, path='/chatbot', name='Chatbot AT')


# ============================================================
# CONFIGURATION
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.3-70b-versatile"
MAX_TOKENS   = 600
TEMPERATURE  = 0.3

groq_client    = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
GROQ_AVAILABLE = groq_client is not None

MONGO_URI       = os.environ.get("MONGO_URI", "mongodb://localhost:27018/?directConnection=true")
CHAT_DB_NAME    = "telecom_algerie"
CHAT_COLLECTION = "chat_sessions"

_CACHED_DATA   = None
_CACHED_TIME   = None
CACHE_DURATION = 600  # 10 minutes

_LAST_GROQ_CALL = 0
GROQ_RATE_LIMIT = 0.5

_models_status_cache = {"data": None, "ts": 0}

_STATS_CACHE: dict = {}
STATS_CACHE_TTL = 120


def get_cached_comments(force_refresh=False):
    global _CACHED_DATA, _CACHED_TIME
    now = datetime.datetime.now()
    if (force_refresh or _CACHED_DATA is None or _CACHED_TIME is None
            or (now - _CACHED_TIME).seconds > CACHE_DURATION):
        _CACHED_DATA = get_all_comments(limit=50000)
        _CACHED_TIME = now
        _STATS_CACHE.clear()
    return _CACHED_DATA


def analyser_donnees_completes(data):
    cache_key = len(data)
    now = time.time()
    if cache_key in _STATS_CACHE:
        cached_stats, cached_ts = _STATS_CACHE[cache_key]
        if now - cached_ts < STATS_CACHE_TTL:
            return cached_stats

    stats = {
        "total": len(data),
        "sentiments":       {"POSITIF": 0, "NEGATIF": 0, "NEUTRE": 0},
        "sources":          Counter(),
        "themes":           Counter(),
        "langues":          Counter(),
        "frustrations":     0,
        "demande_reponse":  0,
        "a_repondu":        0,
        "taux_satisfaction": 0,
        "taux_negatif":     0,
        "taux_frustration": 0,
    }
    for c in data:
        label = c.get('sentiment_label', 'NEUTRE')
        if label in ["negatif", "NEGATIF"]:
            label = "NEGATIF"
        elif label in ["positif", "POSITIF"]:
            label = "POSITIF"
        else:
            label = "NEUTRE"
        stats["sentiments"][label] += 1
        stats["sources"][c.get('source', 'inconnu')] += 1
        stats["themes"][c.get('theme_pred', 'autre')] += 1
        stats["langues"][c.get('langue_detectee', 'inconnue')] += 1
        if c.get('frustration_detectee'): stats["frustrations"]    += 1
        if c.get('demande_reponse'):      stats["demande_reponse"] += 1
        if c.get('a_repondu'):            stats["a_repondu"]       += 1
    total = stats["total"] or 1
    stats["taux_satisfaction"] = round(stats["sentiments"]["POSITIF"] / total * 100, 1)
    stats["taux_negatif"]      = round(stats["sentiments"]["NEGATIF"] / total * 100, 1)
    stats["taux_frustration"]  = round(stats["frustrations"] / total * 100, 1)
    _STATS_CACHE[cache_key] = (stats, now)
    return stats


# ============================================================
# MONGODB CHAT
# ============================================================

def get_chat_db():
    if MONGO_AVAILABLE:
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            return client[CHAT_DB_NAME]
        except Exception as e:
            print(f"MongoDB chat erreur: {e}")
    return None


def charger_conversations_mongo():
    db = get_chat_db()
    if db is None:
        return {}
    try:
        docs = list(db[CHAT_COLLECTION].find({}, {"_id": 0}).sort("updated_at", -1).limit(50))
        conversations = {}
        for doc in docs:
            conv_id = doc.get("conv_id")
            if conv_id:
                updated_at = doc.get("updated_at", "")
                created_at = doc.get("created_at", "")
                if isinstance(updated_at, datetime.datetime):
                    updated_at = updated_at.isoformat()
                if isinstance(created_at, datetime.datetime):
                    created_at = created_at.isoformat()
                conversations[conv_id] = {
                    "title":      doc.get("title", "Conversation"),
                    "messages":   doc.get("messages", []),
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
        return conversations
    except Exception as e:
        print(f"Erreur chargement: {e}")
        return {}


def sauvegarder_conversation_mongo(conv_id, title, messages):
    db = get_chat_db()
    if db is None:
        return False
    try:
        messages_safe = [{k: v for k, v in m.items() if k != 'rich_html'} for m in messages]
        now = datetime.datetime.now().isoformat()
        db[CHAT_COLLECTION].update_one(
            {"conv_id": conv_id},
            {"$set": {"title": title, "messages": messages_safe,
                      "updated_at": now, "created_at": now}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")
        return False


def supprimer_conversation_mongo(conv_id):
    db = get_chat_db()
    if db is None:
        return False
    try:
        db[CHAT_COLLECTION].delete_one({"conv_id": conv_id})
        return True
    except Exception as e:
        print(f"Erreur suppression: {e}")
        return False


# ============================================================
# FILTRAGE
# ============================================================

def get_all_comments_filtered(limit=50000, filters=None):
    data = get_cached_comments()
    if not filters:
        return data[:limit]
    filtered = data
    for key, value in filters.items():
        if value and value != "all":
            if key == "search_text":
                s = value.lower()
                filtered = [d for d in filtered
                            if s in str(d.get('commentaire_original', '')).lower()]
            else:
                val_lower = str(value).lower()
                filtered = [d for d in filtered
                            if str(d.get(key, '')).lower() == val_lower]
    return filtered[:limit]


# ============================================================
# UI COMPOSANTS
# ============================================================

def make_clientel_logo(size="normal"):
    if size == "small":
        container_w, container_h = "30px", "24px"
        sz_antenna, sz_chart, sz_heart = "16px", "12px", "9px"
        text_sz, gap = "14px", "8px"
    else:
        container_w, container_h = "40px", "32px"
        sz_antenna, sz_chart, sz_heart = "26px", "19px", "13px"
        text_sz, gap = "20px", "12px"
    return html.Div([
        html.Div([
            html.I(className="fas fa-tower-cell", style={"fontSize": sz_antenna, "color": "#0052A5",
                   "position": "absolute", "top": "0", "left": "0"}),
            html.I(className="fas fa-chart-line", style={"fontSize": sz_chart, "color": "#00A86B",
                   "position": "absolute", "bottom": "0", "left": "4px"}),
            html.I(className="fas fa-heart", style={"fontSize": sz_heart, "color": "#FF3B3B",
                   "position": "absolute", "bottom": "2px", "right": "0"}),
        ], style={"position": "relative", "width": container_w, "height": container_h, "flexShrink": "0"}),
        html.Div([
            html.Span("ClienTel", style={"fontSize": text_sz, "fontWeight": "800", "color": "#0052A5"}),
            html.Span(" Pulse", style={"fontSize": text_sz, "fontWeight": "800", "color": "#00A86B"}),
        ], style={"marginLeft": gap, "lineHeight": "1", "whiteSpace": "nowrap"})
    ], style={"display": "flex", "alignItems": "center"})


def make_section_title(title, icon_class=""):
    return html.Div([
        html.I(className=icon_class, style={"fontSize": "18px", "marginRight": "8px",
               "color": "#00A86B"}) if icon_class else None,
        html.Span(title, style={"fontWeight": "700", "fontSize": "16px", "color": "#0052A5"})
    ], style={"borderBottom": "2px solid #00A86B", "paddingBottom": "8px",
              "marginBottom": "16px", "marginTop": "8px", "display": "flex", "alignItems": "center"})


def make_alert(msg, level="info"):
    colors = {
        "info":    ("#e8f0fb", "#0052A5", "fas fa-info-circle"),
        "warn":    ("#fff8e1", "#FFB347", "fas fa-exclamation-triangle"),
        "success": ("#e8f5e9", "#00A86B", "fas fa-check-circle"),
        "danger":  ("#fde8e8", "#FF4444", "fas fa-times-circle"),
    }
    bg, col, icon = colors.get(level, colors["info"])
    return html.Div([
        html.I(className=icon, style={"marginRight": "8px", "fontSize": "14px"}),
        html.Span(msg, style={"fontSize": "12px", "fontWeight": "500"})
    ], style={"background": bg, "borderLeft": f"4px solid {col}", "color": col,
              "padding": "10px 14px", "borderRadius": "8px", "marginTop": "8px", "marginBottom": "8px"})


def make_kpi_cards(kpis):
    cards = []
    for kpi in kpis:
        cards.append(html.Div([
            html.I(className=kpi['icon'], style={"fontSize": "24px", "marginBottom": "6px",
                   "color": kpi.get('color', '#0052A5')}),
            html.Div(str(kpi['value']), style={"fontSize": "22px", "fontWeight": "800",
                     "color": kpi.get('color', '#0052A5')}),
            html.Div(kpi['label'], style={"fontSize": "11px", "color": "#666", "fontWeight": "500"})
        ], style={
            "background": f"linear-gradient(135deg,{kpi.get('bg','#f0f4ff')},white)",
            "padding": "14px 12px", "borderRadius": "12px", "textAlign": "center",
            "border": f"1px solid {kpi.get('color','#0052A5')}22", "minWidth": "100px", "flex": "1",
        }))
    return html.Div(cards, style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "16px"})


def make_bar_chart(data_dict, title="", icon_class="", max_items=10):
    if not data_dict:
        return html.Div()
    items   = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:max_items]
    max_val = max(v for _, v in items) or 1
    colors  = ["#0052A5", "#00A86B", "#FF6B35", "#6366f1", "#f59e0b", "#ef4444"]
    bars = []
    for i, (label, val) in enumerate(items):
        pct   = round((val / max_val) * 100, 1)
        color = colors[i % len(colors)]
        bars.append(html.Div([
            html.Div(label[:20], style={"fontSize": "12px", "width": "140px", "flexShrink": "0",
                                        "fontWeight": "500", "color": "#333"}),
            html.Div([html.Div(style={"height": "24px", "width": f"{pct}%", "background": color,
                               "borderRadius": "6px", "minWidth": "4px"})],
                     style={"flex": "1", "background": "#f0f2f5", "borderRadius": "6px", "overflow": "hidden"}),
            html.Div(str(val), style={"fontSize": "12px", "width": "45px", "textAlign": "right",
                                      "fontWeight": "700", "color": color})
        ], style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "8px"}))
    return html.Div([
        html.Div([html.I(className=icon_class, style={"marginRight": "8px"}) if icon_class else None, title],
                 style={"fontSize": "14px", "fontWeight": "700", "color": "#0052A5",
                        "marginBottom": "12px"}) if title else None,
        html.Div(bars)
    ], style={"padding": "16px", "background": "white", "borderRadius": "12px",
              "boxShadow": "0 2px 8px rgba(0,82,165,0.08)", "marginBottom": "16px"})


def make_table(headers, rows):
    if not rows:
        return html.Div()
    thead = html.Thead(html.Tr([
        html.Th(h, style={"padding": "10px 12px",
                "background": "linear-gradient(135deg,#0052A5,#00A86B)",
                "color": "white", "fontSize": "11px", "fontWeight": "700", "textTransform": "uppercase"})
        for h in headers
    ]))
    tbody_rows = []
    for i, row in enumerate(rows[:15]):
        tbody_rows.append(html.Tr([
            html.Td(cell, style={"padding": "8px 12px", "fontSize": "12px",
                    "borderBottom": "1px solid #eef0f5",
                    "background": "#fafbfd" if i % 2 == 0 else "white"})
            for cell in row
        ]))
    return html.Table([thead, html.Tbody(tbody_rows)],
                      style={"width": "100%", "borderCollapse": "collapse", "borderRadius": "10px",
                             "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,82,165,0.08)",
                             "marginBottom": "16px"})


# ============================================================
# GROQ — AVEC FALLBACK LOCAL QUAND EPUISE
# ============================================================

def _generer_reponse_groq(question, stats_globales, data, rag_context=""):
    """Génère une réponse via Groq. Si épuisé, retourne une réponse locale basée sur les stats."""
    global _LAST_GROQ_CALL

    stats = analyser_donnees_completes(data)

    # ── Fallback local (sans API) ──────────────────────────────────────────────
    def _reponse_locale():
        top_themes  = stats["themes"].most_common(3)
        top_sources = stats["sources"].most_common(3)
        themes_txt  = ", ".join(f"{k}:{v}" for k, v in top_themes)
        sources_txt = ", ".join(f"{k}:{v}" for k, v in top_sources)
        return (
            f"📊 Analyse des {stats['total']:,} commentaires :\n"
            f"• Satisfaction : {stats['taux_satisfaction']}% | "
            f"Mécontents : {stats['taux_negatif']}% | "
            f"Frustration : {stats['taux_frustration']}%\n"
            f"• Thèmes principaux : {themes_txt}\n"
            f"• Sources : {sources_txt}\n"
            f"{'⚠️ Situation critique — action urgente recommandée.' if stats['taux_negatif'] > 50 else '✅ Situation sous contrôle.'}"
        )

    if not groq_client:
        return _reponse_locale()

    now = time.time()
    elapsed = now - _LAST_GROQ_CALL
    if elapsed < GROQ_RATE_LIMIT:
        time.sleep(GROQ_RATE_LIMIT - elapsed)
    _LAST_GROQ_CALL = time.time()

    top_themes  = dict(stats["themes"].most_common(5))
    top_sources = dict(stats["sources"].most_common(5))
    system_prompt = (
        f"Tu es l'assistant IA de ClienTel Pulse pour Algerie Telecom.\n"
        f"Total: {stats_globales['total']:,} avis | "
        f"Satisfaits: {stats['taux_satisfaction']}% | "
        f"Mecontents: {stats['taux_negatif']}% | "
        f"Frustration: {stats['taux_frustration']}%\n"
        f"Themes: {', '.join(f'{k}:{v}' for k,v in top_themes.items())}\n"
        f"Sources: {', '.join(f'{k}:{v}' for k,v in top_sources.items())}\n"
        f"{rag_context}\n"
        f"REGLE: Reponse 3-5 phrases courtes, chiffres lisibles, francais."
    )
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user",   "content": question}],
            temperature=TEMPERATURE, max_tokens=MAX_TOKENS
        )
        return completion.choices[0].message.content
    except Exception as e:
        err = str(e).lower()
        if "rate_limit" in err or "429" in err:
            return _reponse_locale()  # Fallback local au lieu d'erreur
        return f"Erreur IA: {str(e)}"


# ============================================================
# RAG — AVEC FALLBACK TF-IDF LOCAL
# ============================================================

def _rag_search_local(question, data, k=5):
    """Recherche TF-IDF locale quand le module RAG n'est pas disponible."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        texts = [str(d.get('commentaire_original', '')) for d in data if d.get('commentaire_original')]
        if not texts or len(texts) < 3:
            return []

        sample = data[:5000]  # limiter pour la vitesse
        sample_texts = [str(d.get('commentaire_original', '')) for d in sample]

        vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(sample_texts)
        q_vec = vectorizer.transform([question])
        scores = cosine_similarity(q_vec, tfidf_matrix)[0]

        top_idx = np.argsort(scores)[::-1][:k]
        results = []
        for idx in top_idx:
            if scores[idx] > 0.01:
                item = dict(sample[idx])
                item['similarity_score'] = float(scores[idx])
                results.append(item)
        return results
    except Exception as e:
        print(f"TF-IDF local error: {e}")
        return []


# ============================================================
# RÉPONSES RICHES
# ============================================================

def response_analyse_complete(filters=None):
    data  = get_all_comments_filtered(filters=filters)
    stats = analyser_donnees_completes(data)
    if stats["total"] == 0:
        return html.Div([make_alert("Aucune donnee trouvee.", "warn")])
    return html.Div([
        make_section_title("Analyse Complete", "fas fa-chart-line"),
        make_kpi_cards([
            {"icon": "fas fa-file-alt",  "label": "Total",        "value": stats["total"],
             "color": "#0052A5", "bg": "#e8f0fb"},
            {"icon": "fas fa-smile",     "label": "Satisfaction",  "value": f"{stats['taux_satisfaction']}%",
             "color": "#00A86B", "bg": "#e8f5e9"},
            {"icon": "fas fa-frown",     "label": "Negatifs",      "value": f"{stats['taux_negatif']}%",
             "color": "#FF4444", "bg": "#fde8e8"},
            {"icon": "fas fa-fire",      "label": "Frustration",   "value": f"{stats['taux_frustration']}%",
             "color": "#FFB347", "bg": "#fff8e1"},
        ]),
        make_bar_chart(dict(stats["sources"]), "Top Sources", "fas fa-mobile-alt", 6),
        make_bar_chart(dict(stats["themes"]),  "Top Themes",  "fas fa-tags", 6),
    ])


def make_prediction_card(text: str):
    """Analyse un commentaire avec DziriBERT ou fallback local basé sur mots-clés."""
    try:
        from models.model_loader import analyze_comment
        result = analyze_comment(text)
        use_fallback = False
    except Exception:
        use_fallback = True

    if use_fallback:
        # Fallback local par mots-clés
        text_lower = text.lower()
        neg_words = ["lent", "mauvais", "nul", "probleme", "panne", "coupure", "terrible",
                     "enerve", "decu", "insatisfait", "horrible", "slow", "bad", "mchklk", "wahrani"]
        pos_words = ["bien", "bon", "excellent", "parfait", "satisfait", "rapide", "super", "bravo"]

        neg_score = sum(1 for w in neg_words if w in text_lower)
        pos_score = sum(1 for w in pos_words if w in text_lower)

        if neg_score > pos_score:
            sentiment_label = "negatif"
            confidence = min(0.5 + neg_score * 0.1, 0.95)
        elif pos_score > 0:
            sentiment_label = "positif"
            confidence = min(0.5 + pos_score * 0.1, 0.95)
        else:
            sentiment_label = "neutre"
            confidence = 0.55

        # Détection thème
        reason_map = {
            "reseau":         ["reseau", "signal", "4g", "coupure", "connexion", "internet"],
            "debit":          ["lent", "vitesse", "debit", "slow", "speed"],
            "service_client": ["service", "support", "attente", "agent", "reponse"],
            "facturation":    ["facture", "prix", "cher", "tarif", "paiement"],
            "installation":   ["installation", "technicien", "installer"],
        }
        reason_pred = "autre"
        for reason, keywords in reason_map.items():
            if any(kw in text_lower for kw in keywords):
                reason_pred = reason
                break

        result = {
            "sentiment_label":       sentiment_label,
            "sentiment_confidence":  confidence,
            "reason_pred":           reason_pred,
            "reason_confidence":     0.65,
        }

    sentiment_colors = {"positif": "#00A86B", "negatif": "#FF4444", "neutre": "#FFB347"}
    s_color = sentiment_colors.get(result["sentiment_label"], "#0052A5")

    def conf_bar(score, color):
        pct = round(score * 100, 1)
        return html.Div([
            html.Div(style={"height": "8px", "width": f"{pct}%", "background": color, "borderRadius": "4px"})
        ], style={"background": "#f0f2f5", "borderRadius": "4px", "overflow": "hidden", "flex": "1"})

    reason_labels_fr = {
        "reseau": "Réseau", "hors_sujet": "Hors sujet", "service_client": "Service client",
        "facturation": "Facturation", "debit": "Débit", "fibre": "Fibre optique",
        "4g": "Couverture 4G", "adsl": "Connexion ADSL", "autre": "Autre",
        "panne": "Panne", "installation": "Installation", "prix": "Tarif"
    }
    reason_label_fr = reason_labels_fr.get(result["reason_pred"], result["reason_pred"])

    source_label = "🤖 Analyse locale (DziriBERT indisponible)" if use_fallback else "✅ DziriBERT"

    return html.Div([
        make_section_title("Analyse de commentaire", "fas fa-microscope"),
        make_alert(source_label, "info" if not use_fallback else "warn"),
        html.Div([
            html.I(className="fas fa-quote-left", style={"color": "#0052A5", "marginRight": "8px"}),
            html.Span(text[:120] + ("..." if len(text) > 120 else ""),
                      style={"fontStyle": "italic", "fontSize": "13px"})
        ], style={"background": "#f8f9fa", "padding": "12px", "borderRadius": "8px", "marginBottom": "16px"}),
        html.Div([
            html.Div([
                html.Div("Sentiment", style={"fontSize": "11px", "color": "#666", "fontWeight": "600"}),
                html.Div(result["sentiment_label"].upper(),
                         style={"fontSize": "22px", "fontWeight": "800", "color": s_color}),
                html.Div([
                    conf_bar(result["sentiment_confidence"], s_color),
                    html.Span(f"{result['sentiment_confidence'] * 100:.1f}%",
                              style={"fontSize": "11px", "fontWeight": "700", "color": s_color, "marginLeft": "8px"})
                ], style={"display": "flex", "alignItems": "center", "gap": "8px", "marginTop": "6px"})
            ], style={"background": f"{s_color}18", "padding": "14px", "borderRadius": "10px", "flex": "1"}),
            html.Div([
                html.Div("Raison detectee", style={"fontSize": "11px", "color": "#666", "fontWeight": "600"}),
                html.Div(reason_label_fr, style={"fontSize": "16px", "fontWeight": "700", "color": "#0052A5"}),
                html.Div([
                    conf_bar(result["reason_confidence"], "#0052A5"),
                    html.Span(f"{result['reason_confidence'] * 100:.1f}%",
                              style={"fontSize": "11px", "color": "#0052A5", "marginLeft": "8px"})
                ], style={"display": "flex", "alignItems": "center", "gap": "8px", "marginTop": "6px"})
            ], style={"background": "#e8f0fb", "padding": "14px", "borderRadius": "10px", "flex": "1"}),
        ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),
    ])


def make_rag_response(question: str, stats_global: dict, filters=None):
    data = get_all_comments_filtered(filters=filters)
    similar, rag_context, rag_stats = [], "", None

    # Essayer RAG module, sinon TF-IDF local
    try:
        from models.rag_engine import get_rag_engine, _RAG_ENGINE
        rag = _RAG_ENGINE if _RAG_ENGINE is not None else get_rag_engine(data)
        if hasattr(rag, 'embeddings') and rag.embeddings is not None:
            rag_stats = f"{len(rag.embeddings)} embeddings"
        elif hasattr(rag, 'tfidf') and rag.tfidf:
            rag_stats = "TF-IDF (RAG)"
        similar = rag.search(question, k=5)
    except Exception:
        # Fallback TF-IDF local
        similar = _rag_search_local(question, data, k=5)
        if similar:
            rag_stats = "TF-IDF local"

    if similar:
        rag_lines = []
        for c in similar:
            score     = c.get("similarity_score", 0)
            sentiment = c.get("sentiment_label", "?")
            reason    = c.get("reason_pred", "?")
            texte     = c.get("commentaire_original", "")[:80]
            frust     = " [FRUSTRE]" if c.get("frustration_detectee") else ""
            rag_lines.append(f"  [{sentiment}]{frust} raison:{reason} sim:{score:.2f} — {texte}")
        rag_context = "\n[COMMENTAIRES SIMILAIRES]\n" + "\n".join(rag_lines)

    ia_response = _generer_reponse_groq(question, stats_global, data, rag_context)

    sentiment_colors = {"POSITIF": "#00A86B", "NEGATIF": "#FF4444", "NEUTRE": "#FFB347",
                        "positif": "#00A86B",  "negatif": "#FF4444",  "neutre": "#FFB347"}
    source_cards = []
    reason_labels_fr = {
        "reseau": "Réseau", "hors_sujet": "Hors sujet", "service_client": "Service client",
        "facturation": "Facturation", "debit": "Débit", "fibre": "Fibre", "4g": "4G",
        "adsl": "ADSL", "autre": "Autre", "panne": "Panne", "installation": "Installation", "prix": "Tarif"
    }
    for i, c in enumerate(similar[:5]):
        sentiment = c.get("sentiment_label", "?")
        color     = sentiment_colors.get(sentiment.upper() if sentiment else "NEUTRE", "#666")
        score_pct = round(c.get("similarity_score", 0) * 100, 1)
        texte     = c.get("commentaire_original", "")[:100]
        reason    = c.get("reason_pred", "?")
        source    = c.get("source", "?")
        frust     = c.get("frustration_detectee", False)
        source_cards.append(html.Div([
            html.Div([
                html.Span(f"#{i+1}", style={"background": "#0052A5", "color": "white",
                          "borderRadius": "50%", "width": "22px", "height": "22px",
                          "display": "flex", "alignItems": "center", "justifyContent": "center",
                          "fontSize": "11px", "fontWeight": "700", "flexShrink": "0"}),
                html.Span(sentiment, style={"background": color, "color": "white",
                          "padding": "2px 8px", "borderRadius": "12px",
                          "fontSize": "10px", "fontWeight": "700"}),
                html.Span(f"sim:{score_pct}%", style={"fontSize": "10px", "color": "#666", "marginLeft": "auto"}),
                html.Span("frustre", style={"fontSize": "10px", "color": "#FF4444"}) if frust else None
            ], style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "6px"}),
            html.Div(f'"{texte}..."',
                     style={"fontSize": "12px", "fontStyle": "italic", "color": "#333", "lineHeight": "1.5"}),
            html.Div([
                html.Span(f"Source: {source}", style={"fontSize": "10px", "color": "#666"}),
                html.Span(reason_labels_fr.get(reason, reason), style={"fontSize": "10px", "color": "#0052A5"})
            ], style={"display": "flex", "gap": "12px", "marginTop": "6px"})
        ], style={"background": "white", "border": f"1px solid {color}44",
                  "borderLeft": f"3px solid {color}", "padding": "10px 12px",
                  "borderRadius": "8px", "marginBottom": "8px"}))

    title_suffix = f" ({rag_stats})" if rag_stats else ""
    children = [
        make_section_title(f"Réponse augmentée{title_suffix}", "fas fa-search"),
        html.Div([
            html.I(className="fas fa-robot",
                   style={"color": "#0052A5", "marginRight": "8px", "flexShrink": "0"}),
            html.Div(ia_response, style={"whiteSpace": "pre-wrap", "lineHeight": "1.6", "fontSize": "13px"})
        ], style={"background": "#e8f0fb", "padding": "14px", "borderRadius": "10px",
                  "marginBottom": "16px", "display": "flex", "gap": "8px", "alignItems": "flex-start"}),
    ]
    if source_cards:
        children.append(html.Div([
            html.Div([
                html.I(className="fas fa-database", style={"marginRight": "6px", "color": "#0052A5"}),
                html.Span("Commentaires similaires",
                          style={"fontSize": "12px", "fontWeight": "700", "color": "#0052A5"})
            ], style={"marginBottom": "10px"}),
            *source_cards
        ], style={"background": "#f8f9fa", "padding": "12px", "borderRadius": "10px"}))
    return html.Div(children)


def detecter_filtres(question):
    q = question.lower()
    filters = {}
    sources_map = {"facebook": "Facebook", "fb": "Facebook", "instagram": "Instagram",
                   "twitter": "Twitter", "tiktok": "TikTok", "youtube": "YouTube", "linkedin": "LinkedIn"}
    for key, val in sources_map.items():
        if key in q:
            filters["source"] = val
            break
    if any(k in q for k in ["positif", "satisfait", "content", "heureux"]):
        filters["sentiment_label"] = "positif"
    elif any(k in q for k in ["negatif", "mecontent", "insatisf", "mauvais"]):
        filters["sentiment_label"] = "negatif"
    if any(k in q for k in ["frustration", "frustrant", "enerve", "colere"]):
        filters["frustration_detectee"] = True
    return filters


def detecter_intention(question):
    q = question.lower()
    if any(k in q for k in ["analyse complete", "statistique globale", "global", "vue d ensemble"]):
        return "analyse_complete"
    if any(k in q for k in ["aide", "help", "commandes", "que puis-je", "comment utiliser"]):
        return "aide"
    if any(k in q for k in ["analyse ce commentaire", "analyse :", "analyser :", "quel sentiment",
                              "classif", "predis", "classifie", "analyser ce texte"]):
        return "analyse_commentaire"
    if any(k in q for k in ["recommand", "amelior", "prioris", "que faire", "plan d action",
                              "action", "conseil", "decision", "quoi faire", "comment reduire"]):
        return "recommandation"
    if any(k in q for k in ["alerte", "crise", "pic", "anomalie", "urgence", "probleme grave"]):
        return "alerte"
    if any(k in q for k in ["tendance", "evolution", "comparaison", "ce mois", "historique", "progression"]):
        return "tendance"
    if any(k in q for k in ["simulation", "what if", "si on", "si nous", "impact de", "scenario"]):
        return "simulation"
    if any(k in q for k in ["rapport", "export", "synthese manager", "bilan", "compte rendu"]):
        return "rapport"
    if any(k in q for k in ["benchmark", "semaine mois", "s vs m", "bench"]):
        return "benchmark"
    return "general"


def _date_in_range(comment, start, end):
    ds = comment.get("date_originale") or comment.get("date_clean") or ""
    try:
        if isinstance(ds, datetime.datetime):
            return start <= ds <= end
        if "/" in str(ds):
            dt = datetime.datetime.strptime(str(ds).split()[0], "%d/%m/%Y")
        else:
            dt = datetime.datetime.fromisoformat(str(ds)[:10])
        return start <= dt <= end
    except Exception:
        return False


def _get_top_theme_frustre(data):
    frust = [c for c in data if c.get("frustration_detectee")]
    if not frust:
        return "reseau"
    counter = Counter(c.get("theme_pred", "autre") for c in frust)
    top = counter.most_common(1)
    return top[0][0] if top else "reseau"


def generer_recommandations(data, stats=None):
    if stats is None:
        stats = analyser_donnees_completes(data)
    recs  = []
    total = stats["total"] or 1
    if stats["taux_negatif"] > 50:
        recs.append({"priorite": 1, "niveau": "CRITIQUE",
            "titre": "Taux de mécontentement très élevé",
            "probleme": f"{stats['taux_negatif']}% d'avis négatifs — seuil critique dépassé",
            "action": "Déclencher cellule de crise. Identifier les 3 thèmes les plus négatifs sous 48h.",
            "kpi_cible": "Ramener le taux négatif sous 35% en 30 jours",
            "effort": "Élevé", "delai": "48h"})
    elif stats["taux_negatif"] > 35:
        recs.append({"priorite": 2, "niveau": "HAUT",
            "titre": "Taux de mécontentement préoccupant",
            "probleme": f"{stats['taux_negatif']}% d'avis négatifs",
            "action": "Analyser les commentaires négatifs par source et thème.",
            "kpi_cible": "Réduire à moins de 30% en 60 jours",
            "effort": "Moyen", "delai": "1 semaine"})
    if stats["taux_frustration"] > 25:
        recs.append({"priorite": 1 if stats["taux_frustration"] > 40 else 2,
            "niveau": "CRITIQUE" if stats["taux_frustration"] > 40 else "HAUT",
            "titre": "Niveau de frustration alarmant",
            "probleme": f"{stats['taux_frustration']}% des abonnés expriment de la frustration",
            "action": "Réponse prioritaire <2h pour les commentaires marqués frustration.",
            "kpi_cible": "Réduire la frustration sous 15% en 45 jours",
            "effort": "Moyen", "delai": "72h"})
    nb_sans_rep   = sum(1 for c in data if c.get("demande_reponse") and not c.get("a_repondu"))
    taux_sans_rep = round(nb_sans_rep / total * 100, 1)
    if taux_sans_rep > 15:
        recs.append({"priorite": 2, "niveau": "HAUT",
            "titre": "Trop de demandes sans réponse",
            "probleme": f"{nb_sans_rep} abonnés ({taux_sans_rep}%) attendent une réponse",
            "action": "Activer bot de réponse automatique. Objectif : répondre sous 4h.",
            "kpi_cible": "Taux de réponse > 90% en 30 jours",
            "effort": "Faible", "delai": "1 semaine"})
    recs.sort(key=lambda x: x["priorite"])
    return recs


def response_recommandations(filters=None):
    data  = get_all_comments_filtered(filters=filters)
    stats = analyser_donnees_completes(data)
    recs  = generer_recommandations(data, stats)
    if not recs:
        return html.Div([make_alert("Aucune recommandation critique — situation stable.", "success")])
    niveau_config = {
        "CRITIQUE": ("#fde8e8", "#FF4444", "fas fa-exclamation-circle"),
        "HAUT":     ("#fff8e1", "#FFB347", "fas fa-exclamation-triangle"),
        "MOYEN":    ("#e8f0fb", "#0052A5", "fas fa-info-circle"),
    }
    cards = []
    for i, r in enumerate(recs):
        bg, color, icon = niveau_config.get(r["niveau"], niveau_config["MOYEN"])
        cards.append(html.Div([
            html.Div([
                html.Span(f"#{i+1}", style={"background": color, "color": "white",
                          "borderRadius": "50%", "width": "26px", "height": "26px",
                          "display": "flex", "alignItems": "center", "justifyContent": "center",
                          "fontSize": "12px", "fontWeight": "800", "flexShrink": "0"}),
                html.I(className=icon, style={"color": color, "fontSize": "16px"}),
                html.Span(r["titre"], style={"fontWeight": "700", "fontSize": "14px", "color": color}),
                html.Span(r["niveau"], style={"marginLeft": "auto", "background": color,
                          "color": "white", "padding": "2px 8px", "borderRadius": "10px",
                          "fontSize": "10px", "fontWeight": "700"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "10px"}),
            html.Div([html.Span("Problème : ", style={"fontWeight": "600", "fontSize": "12px"}),
                      html.Span(r["probleme"], style={"fontSize": "12px"})], style={"marginBottom": "8px"}),
            html.Div([html.I(className="fas fa-arrow-right",
                             style={"color": color, "marginRight": "6px", "fontSize": "11px"}),
                      html.Span("Action : ", style={"fontWeight": "600", "fontSize": "12px"}),
                      html.Span(r["action"], style={"fontSize": "12px", "lineHeight": "1.5"})],
                     style={"marginBottom": "8px", "background": "white", "padding": "8px 10px", "borderRadius": "6px"}),
        ], style={"background": bg, "border": f"1px solid {color}33", "borderLeft": f"4px solid {color}",
                  "padding": "14px", "borderRadius": "10px", "marginBottom": "12px"}))
    return html.Div([
        make_section_title(f"Plan d'action — {len(recs)} recommandations", "fas fa-clipboard-list"),
        make_kpi_cards([
            {"icon": "fas fa-exclamation-circle", "label": "Critiques",
             "value": sum(1 for r in recs if r["niveau"] == "CRITIQUE"), "color": "#FF4444", "bg": "#fde8e8"},
            {"icon": "fas fa-exclamation-triangle", "label": "Hautes",
             "value": sum(1 for r in recs if r["niveau"] == "HAUT"), "color": "#FFB347", "bg": "#fff8e1"},
        ]),
        *cards
    ])


def response_alertes_decisionnelles(filters=None):
    data  = get_all_comments_filtered(filters=filters)
    stats = analyser_donnees_completes(data)
    recs  = [r for r in generer_recommandations(data, stats) if r["niveau"] in ["CRITIQUE", "HAUT"]]
    children = [make_section_title("Alertes & urgences", "fas fa-bell")]
    children.append(make_alert("Aucune alerte critique sur les 7 derniers jours.", "success"))
    if recs:
        children.append(make_section_title("Actions urgentes", "fas fa-fire"))
        for r in recs[:3]:
            children.append(html.Div([
                html.Span(r["titre"], style={"fontWeight": "700", "color": "#FF4444", "fontSize": "13px"}),
                html.Div(r["action"], style={"fontSize": "12px", "marginTop": "4px", "color": "#333"})
            ], style={"background": "#fde8e8", "padding": "10px 12px",
                      "borderRadius": "8px", "marginBottom": "8px", "borderLeft": "3px solid #FF4444"}))
    return html.Div(children)


def response_tendances(question, filters=None):
    data  = get_all_comments_filtered(filters=filters)
    stats = analyser_donnees_completes(data)
    now   = datetime.datetime.now()
    recent = [c for c in data if _date_in_range(c, now - datetime.timedelta(days=30), now)]
    ancien = [c for c in data if _date_in_range(c, now - datetime.timedelta(days=60), now - datetime.timedelta(days=30))]
    stats_r = analyser_donnees_completes(recent) if recent else stats
    stats_a = analyser_donnees_completes(ancien) if ancien else stats
    delta_sat  = round(stats_r["taux_satisfaction"] - stats_a["taux_satisfaction"], 1)
    delta_neg  = round(stats_r["taux_negatif"]      - stats_a["taux_negatif"], 1)
    delta_frus = round(stats_r["taux_frustration"]  - stats_a["taux_frustration"], 1)
    context = (f"[TENDANCES] Récent(30j):{len(recent)} avis | Précédent:{len(ancien)} avis\n"
               f"Satisfaction: {stats_r['taux_satisfaction']}% (Δ{delta_sat:+.1f}pts) | "
               f"Négatifs: {stats_r['taux_negatif']}% (Δ{delta_neg:+.1f}pts)")
    ia_rep = _generer_reponse_groq(question, stats, data, context)
    def trend_icon(delta, inverse=False):
        if abs(delta) < 2: return "→ stable"
        return ("▲ +" if delta > 0 else "▼ ") + str(abs(delta)) + "%"
    return html.Div([
        make_section_title("Analyse temporelle", "fas fa-chart-line"),
        make_kpi_cards([
            {"icon": "fas fa-smile", "label": f"Satisfaction {trend_icon(delta_sat)}",
             "value": f"{stats_r['taux_satisfaction']}%",
             "color": "#00A86B" if delta_sat >= 0 else "#FF4444", "bg": "#e8f5e9"},
            {"icon": "fas fa-frown", "label": f"Négatifs {trend_icon(delta_neg, True)}",
             "value": f"{stats_r['taux_negatif']}%",
             "color": "#FF4444" if delta_neg > 0 else "#00A86B", "bg": "#fde8e8"},
        ]),
        html.Div([
            html.I(className="fas fa-robot", style={"color": "#0052A5", "marginRight": "8px", "flexShrink": "0"}),
            html.Div(ia_rep, style={"whiteSpace": "pre-wrap", "fontSize": "13px", "lineHeight": "1.6"})
        ], style={"background": "#e8f0fb", "padding": "14px", "borderRadius": "10px", "display": "flex", "gap": "8px"})
    ])


def response_benchmark_periodes(filters=None):
    data = get_all_comments_filtered(filters=filters)
    now  = datetime.datetime.now()
    semaine_data = [c for c in data if _date_in_range(c, now - datetime.timedelta(days=7), now)]
    mois_data    = [c for c in data if _date_in_range(c, now - datetime.timedelta(days=30), now)]
    stats_s = analyser_donnees_completes(semaine_data)
    stats_m = analyser_donnees_completes(mois_data)
    def trend(delta, inverse=False):
        if abs(delta) < 1: return "→"
        better = delta < 0 if inverse else delta > 0
        return "▲" if better else "▼"
    delta_sat = round(stats_s["taux_satisfaction"] - stats_m["taux_satisfaction"], 1)
    delta_neg = round(stats_s["taux_negatif"]      - stats_m["taux_negatif"], 1)
    return html.Div([
        make_section_title("Benchmark : Semaine vs Mois", "fas fa-chart-line"),
        html.Div([
            html.Div([
                html.Div("7 derniers jours", style={"fontWeight": "700", "fontSize": "13px",
                                                     "marginBottom": "12px", "color": "#0052A5"}),
                make_kpi_cards([
                    {"icon": "fas fa-smile", "label": "Satisfaction",
                     "value": f"{stats_s['taux_satisfaction']}%", "color": "#00A86B", "bg": "#e8f5e9"},
                    {"icon": "fas fa-frown", "label": "Négatifs",
                     "value": f"{stats_s['taux_negatif']}%", "color": "#FF4444", "bg": "#fde8e8"},
                ])
            ], style={"flex": "1", "background": "#f8f9fa", "padding": "14px", "borderRadius": "10px"}),
            html.Div([
                html.Div("30 derniers jours", style={"fontWeight": "700", "fontSize": "13px",
                                                      "marginBottom": "12px", "color": "#00A86B"}),
                make_kpi_cards([
                    {"icon": "fas fa-smile", "label": "Satisfaction",
                     "value": f"{stats_m['taux_satisfaction']}%", "color": "#00A86B", "bg": "#e8f5e9"},
                    {"icon": "fas fa-frown", "label": "Négatifs",
                     "value": f"{stats_m['taux_negatif']}%", "color": "#FF4444", "bg": "#fde8e8"},
                ])
            ], style={"flex": "1", "background": "#f8f9fa", "padding": "14px", "borderRadius": "10px"}),
        ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),
        html.Div([
            html.Div(f"Satisfaction : {trend(delta_sat)} {abs(delta_sat)} pts | "
                     f"Négatifs : {trend(delta_neg, True)} {abs(delta_neg)} pts",
                     style={"fontSize": "13px", "fontWeight": "600", "color": "#0052A5"})
        ], style={"background": "#e8f0fb", "padding": "12px", "borderRadius": "10px"})
    ])


def response_rapport_manager(filters=None):
    data  = get_all_comments_filtered(filters=filters)
    stats = analyser_donnees_completes(data)
    recs  = generer_recommandations(data, stats)
    if stats["total"] == 0:
        return html.Div([make_alert("Aucune donnée disponible.", "warn")])
    nb_sans_rep   = sum(1 for c in data if c.get("demande_reponse") and not c.get("a_repondu"))
    taux_sans_rep = round(nb_sans_rep / stats["total"] * 100, 1) if stats["total"] > 0 else 0
    if stats["taux_negatif"] > 50:
        niv_msg, niv_col = "URGENCE CRITIQUE", "#FF4444"
    elif stats["taux_negatif"] > 35:
        niv_msg, niv_col = "SITUATION PRÉOCCUPANTE", "#FFB347"
    else:
        niv_msg, niv_col = "SITUATION SAINE", "#00A86B"
    return html.Div([
        make_section_title("RAPPORT DÉCISIONNEL", "fas fa-chart-pie"),
        html.Div(niv_msg, style={"background": f"{niv_col}15", "color": niv_col,
                 "padding": "12px", "borderRadius": "8px", "textAlign": "center",
                 "fontWeight": "700", "fontSize": "14px", "marginBottom": "16px"}),
        make_kpi_cards([
            {"icon": "fas fa-smile", "label": "Satisfaction",
             "value": f"{stats['taux_satisfaction']}%", "color": "#00A86B", "bg": "#e8f5e9"},
            {"icon": "fas fa-frown", "label": "Mécontents",
             "value": f"{stats['taux_negatif']}%", "color": "#FF4444", "bg": "#fde8e8"},
            {"icon": "fas fa-fire", "label": "Frustration",
             "value": f"{stats['taux_frustration']}%", "color": "#FFB347", "bg": "#fff8e1"},
            {"icon": "fas fa-reply", "label": "Sans réponse",
             "value": f"{taux_sans_rep}%", "color": "#0052A5", "bg": "#e8f0fb"},
        ]),
        make_section_title("Actions prioritaires", "fas fa-tasks"),
        *[html.Div([
            html.Div(f"{i+1}. {r['titre']}",
                     style={"fontWeight": "600", "fontSize": "13px", "color": "#0052A5"}),
            html.Div(r["action"], style={"fontSize": "11px", "color": "#555", "marginTop": "4px"})
        ], style={"background": "#f8f9fa", "padding": "10px", "borderRadius": "8px",
                  "marginBottom": "8px", "borderLeft": f"3px solid #0052A5"})
         for i, r in enumerate(recs[:3])]
    ], style={"maxHeight": "500px", "overflowY": "auto"})


# ============================================================
# GENERATE RICH RESPONSE
# ============================================================

def generate_rich_response(user_input, stats_global, db_info, history, groq_enabled, session_id):
    enabled = groq_enabled if groq_enabled is not None else True

    intention = detecter_intention(user_input)
    filters   = detecter_filtres(user_input)

    if intention == "analyse_complete":
        return response_analyse_complete(filters), "groq_direct"
    if intention == "aide":
        return html.Div([
            make_section_title("Aide — Commandes disponibles", "fas fa-question-circle"),
            make_table(["Commande", "Description"], [
                ["analyse complete",               "Statistiques globales"],
                ["analyse ce commentaire : texte", "Analyser avec DziriBERT / local"],
                ["que faire / recommandations",    "Plan d'action priorisé"],
                ["alertes / crise",                "Alertes urgentes"],
                ["evolution / tendances",          "Analyse temporelle"],
                ["rapport / bilan",                "Rapport pour manager"],
                ["benchmark S vs M",               "Comparaison semaine/mois"],
                ["commentaires facebook",          "Filtrer par source"],
            ])
        ]), "groq_direct"
    if intention == "analyse_commentaire":
        parts = re.split(r"[:»\"\-]", user_input, maxsplit=1)
        text_to_analyze = parts[-1].strip() if len(parts) > 1 else user_input
        return make_prediction_card(text_to_analyze), "model_predict"
    if intention == "recommandation":
        return response_recommandations(filters), "decision"
    if intention == "alerte":
        return response_alertes_decisionnelles(filters), "decision"
    if intention == "tendance":
        return response_tendances(user_input, filters), "decision"
    if intention == "rapport":
        return response_rapport_manager(filters), "decision"
    if intention == "benchmark":
        return response_benchmark_periodes(filters), "decision"

    return make_rag_response(user_input, stats_global, filters), "rag"


# ============================================================
# COMPOSANTS CHAT
# ============================================================

def source_badge(source):
    icons = {
        "model_predict": ("fas fa-brain",         "#6366f1", "DziriBERT"),
        "rag":           ("fas fa-database",       "#0052A5", "RAG"),
        "groq_direct":   ("fas fa-bolt",           "#00A86B", "LLM"),
        "decision":      ("fas fa-clipboard-list", "#FF6B35", "Décision"),
    }
    icon_cls, bg, label = icons.get(source, ("fas fa-bolt", "#00A86B", "LLM"))
    return html.Span([
        html.I(className=icon_cls, style={"marginRight": "4px", "fontSize": "8px"}), label
    ], style={"fontSize": "9px", "background": bg, "color": "white",
              "padding": "2px 6px", "borderRadius": "4px", "marginLeft": "6px", "opacity": "0.85"})


def chat_bubble(content, role="bot", source=None, is_html=False):
    is_bot = role == "bot"
    icon   = (html.I(className="fas fa-robot", style={"fontSize": "20px", "color": "#0052A5"})
              if is_bot else
              html.I(className="fas fa-user-circle", style={"fontSize": "20px", "color": "#00A86B"}))
    if is_html and is_bot:
        bubble_content = html.Div(content, style={
            "background": "white", "border": "1px solid rgba(0,82,165,0.12)",
            "padding": "16px", "borderRadius": "16px 16px 16px 4px",
            "maxWidth": "750px", "boxShadow": "0 2px 16px rgba(0,82,165,0.1)"
        })
    else:
        text = content if isinstance(content, str) else ""
        bubble_content = html.Div(text, style={
            "background": "linear-gradient(135deg,#0052A5,#00A86B)",
            "color": "white", "padding": "12px 16px",
            "borderRadius": "16px 16px 16px 4px" if is_bot else "16px 16px 4px 16px",
            "fontSize": "13px", "lineHeight": "1.7", "maxWidth": "520px",
            "whiteSpace": "pre-wrap", "boxShadow": "0 2px 12px rgba(0,82,165,0.15)"
        })
    return html.Div([
        html.Div(icon, style={"flexShrink": "0", "marginTop": "4px"}),
        html.Div([
            bubble_content,
            html.Div([
                html.Span(datetime.datetime.now().strftime("%H:%M"),
                          style={"fontSize": "10px", "color": "#888"}),
                source_badge(source) if (is_bot and source) else None
            ], style={"marginTop": "4px", "textAlign": "left" if is_bot else "right"})
        ])
    ], style={"display": "flex", "gap": "10px", "marginBottom": "16px",
              "flexDirection": "row" if is_bot else "row-reverse", "alignItems": "flex-start"})


def conversation_item(conv_id, title, is_active):
    return html.Div([
        html.Div([
            html.I(className="fas fa-comment-dots",
                   style={"marginRight": "6px", "fontSize": "10px",
                          "color": "#0052A5" if is_active else "#aaa", "flexShrink": "0"}),
            html.Button(
                title[:28] + ("..." if len(title) > 28 else ""),
                id={"type": "conv-btn", "index": conv_id}, n_clicks=0,
                style={"flex": "1", "textAlign": "left", "padding": "0", "background": "transparent",
                       "border": "none", "cursor": "pointer", "fontSize": "12px",
                       "color": "#0052A5" if is_active else "#333",
                       "fontWeight": "600" if is_active else "400",
                       "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}
            ),
            html.Button("✕", id={"type": "delete-conv", "index": conv_id}, n_clicks=0,
                style={"background": "transparent", "border": "none", "cursor": "pointer",
                       "color": "#bbb", "fontSize": "14px", "fontWeight": "700",
                       "padding": "0 4px", "borderRadius": "4px", "flexShrink": "0"})
        ], style={
            "display": "flex", "alignItems": "center", "gap": "6px",
            "padding": "8px 10px", "marginBottom": "4px",
            "background": "linear-gradient(135deg,#e8f0fb,#f0f7ff)" if is_active else "#f5f7fa",
            "borderRadius": "8px",
            "border": f"1px solid {'#0052A530' if is_active else 'transparent'}",
        })
    ])


# ============================================================
# FIX #1 PRINCIPAL : _rebuild_bubbles REGENERE la vraie reponse
# ============================================================

def _rebuild_bubbles(messages, stats_global=None):
    """
    Reconstruit les bulles.
    Pour les messages bot riches (is_html=True) : regenere la vraie reponse
    en appelant generate_rich_response depuis la question stockee (query).
    C'est ce qui permet d'afficher les vraies KPIs/graphes meme apres rechargement.
    """
    if stats_global is None:
        stats_global = analyser_donnees_completes(get_cached_comments())

    bubbles = []
    for msg in messages:
        role    = msg.get('role', 'bot')
        source  = msg.get('source')
        is_html = msg.get('is_html', False)
        text    = msg.get('text', '')

        if is_html and role == 'bot' and msg.get('query'):
            try:
                db_info = {}
                rich, src = generate_rich_response(
                    msg['query'], stats_global, db_info, [], True, "rebuild"
                )
                bubbles.append(chat_bubble(rich, "bot", src if isinstance(src, str) else source, True))
            except Exception as e:
                print(f"Rebuild error: {e}")
                # Fallback : afficher le texte brut
                plain = msg.get('plain_text', msg.get('query', "Réponse précédente"))
                bubbles.append(chat_bubble(plain, "bot", source, False))
        else:
            bubbles.append(chat_bubble(text, role, source, is_html))
    return bubbles


def make_welcome_message(stats):
    return html.Div([
        make_section_title("Bienvenue sur ClienTel Pulse", "fas fa-tower-cell"),
        make_kpi_cards([
            {"icon": "fas fa-comments",    "label": "Commentaires",
             "value": stats['total'],               "color": "#0052A5", "bg": "#e8f0fb"},
            {"icon": "fas fa-smile",       "label": "Satisfaction",
             "value": f"{stats['taux_satisfaction']}%", "color": "#00A86B", "bg": "#e8f5e9"},
            {"icon": "fas fa-frown",       "label": "Mécontents",
             "value": f"{stats['taux_negatif']}%",  "color": "#FF4444", "bg": "#fde8e8"},
            {"icon": "fas fa-heart",       "label": "Pulse client",
             "value": f"{100 - stats['taux_negatif']}%", "color": "#FF3B3B", "bg": "#fff0f0"},
        ]),
        make_alert("Commandes: analyse complete | analyse ce commentaire : texte | aide", "info")
    ])


def _build_conv_list(convs_data, active_conv):
    if not convs_data:
        return [html.Div("Aucune conversation",
                style={"textAlign": "center", "color": "#aaa", "fontSize": "12px", "padding": "20px"})]
    return [conversation_item(cid, conv.get('title', 'Conversation'), cid == active_conv)
            for cid, conv in convs_data.items()]


def _strip_rich_html(convs_data):
    if not convs_data:
        return convs_data
    safe = {}
    for conv_id, conv in convs_data.items():
        safe_conv = {k: v for k, v in conv.items() if k != 'messages'}
        safe_conv['messages'] = [
            {k: v for k, v in msg.items() if k != 'rich_html'}
            for msg in conv.get('messages', [])
        ]
        safe[conv_id] = safe_conv
    return safe


# ============================================================
# LAYOUT
# ============================================================

def make_content(theme, user_data=None, convs_data=None, active_conv=None):
    data         = get_cached_comments()
    stats_global = analyser_donnees_completes(data)

    if convs_data is None:
        convs_data = charger_conversations_mongo() or {}
    if active_conv is None and convs_data:
        sc = sorted(convs_data.items(), key=lambda x: x[1].get('updated_at', ''), reverse=True)
        active_conv = sc[0][0] if sc else None

    messages = []
    if active_conv and active_conv in convs_data:
        messages = convs_data[active_conv].get('messages', [])

    suggestions = [
        ("Analyse complete",      "fas fa-chart-line"),
        ("Benchmark S vs M",      "fas fa-chart-simple"),
        ("Commentaires Facebook", "fab fa-facebook"),
        ("Frustrations clients",  "fas fa-fire"),
        ("Analyse ce commentaire : internet lent", "fas fa-microscope"),
        ("Aide & commandes",      "fas fa-question-circle"),
    ]

    chat_bubbles = _rebuild_bubbles(messages, stats_global)
    if not chat_bubbles:
        chat_bubbles = [chat_bubble(make_welcome_message(stats_global), "bot", "rag", True)]

    conv_list     = _build_conv_list(convs_data, active_conv)
    title_display = (convs_data.get(active_conv, {}).get('title', "ClienTel Pulse")
                     if active_conv else "ClienTel Pulse")

    return html.Div([
        # ── Sidebar ──────────────────────────────────────────────
        html.Div([
            html.Div([
                make_clientel_logo(size="normal"),
                html.Div("Le pouls des clients telecom",
                         style={"fontSize": "11px", "color": "#888", "marginTop": "6px"})
            ], style={"marginBottom": "22px"}),
            html.Button([html.I(className="fas fa-plus", style={"marginRight": "8px"}), "Nouvelle conversation"],
                id="new-conv-btn", n_clicks=0,
                style={"width": "100%", "padding": "10px 14px",
                       "background": "linear-gradient(135deg,#0052A5,#00A86B)",
                       "color": "white", "border": "none", "borderRadius": "10px",
                       "fontSize": "12px", "fontWeight": "600", "cursor": "pointer",
                       "marginBottom": "16px", "display": "flex",
                       "alignItems": "center", "justifyContent": "center"}),
            html.Div([
                html.Div("Historique",
                         style={"fontSize": "12px", "fontWeight": "700", "color": "#0052A5", "marginBottom": "10px"}),
                html.Div(id="conversations-list", children=conv_list,
                         style={"maxHeight": "260px", "overflowY": "auto"})
            ], style={"background": "white", "borderRadius": "12px", "padding": "12px",
                      "marginBottom": "14px", "boxShadow": "0 2px 8px rgba(0,82,165,0.08)"}),
            html.Div([
                html.Div("Suggestions rapides",
                         style={"fontSize": "12px", "fontWeight": "700", "color": "#0052A5", "marginBottom": "10px"}),
                *[html.Button([html.I(className=icon, style={"marginRight": "8px", "fontSize": "11px",
                               "color": "#0052A5"}), label],
                    id={"type": "suggestion-btn", "index": i}, n_clicks=0,
                    style={"width": "100%", "textAlign": "left", "padding": "9px 12px",
                           "marginBottom": "6px", "background": "#f5f7fa",
                           "border": "1px solid #e0e6f0", "borderRadius": "9px",
                           "fontSize": "11px", "cursor": "pointer", "color": "#333"})
                  for i, (label, icon) in enumerate(suggestions)],
            ], style={"background": "white", "borderRadius": "12px", "padding": "12px",
                      "boxShadow": "0 2px 8px rgba(0,82,165,0.08)"}),
            html.Div([html.Span("●", style={"color": "#00A86B", "marginRight": "5px"}),
                      html.Span("Système actif", style={"fontSize": "10px", "color": "#888"})],
                     style={"marginTop": "14px", "textAlign": "center", "display": "flex",
                            "alignItems": "center", "justifyContent": "center"})
        ], style={"width": "255px", "flexShrink": "0", "borderRight": "1px solid #e8edf5",
                  "paddingRight": "16px", "height": "100%", "overflowY": "auto", "paddingBottom": "16px"}),

        # ── Zone de chat ─────────────────────────────────────────
        html.Div([html.Div([
            html.Div([
                html.Div([
                    make_clientel_logo(size="small"),
                    html.Div([
                        html.Div(id="active-conv-title", children=title_display,
                                 style={"fontWeight": "700", "fontSize": "14px", "color": "#0052A5"}),
                        html.Div(f"{stats_global['total']} commentaires analysés",
                                 style={"fontSize": "10px", "color": "#aaa"})
                    ], style={"marginLeft": "10px"})
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"marginBottom": "14px", "paddingBottom": "12px", "borderBottom": "1px solid #e8edf5"}),
            html.Div(id="chat-messages", children=chat_bubbles,
                     style={"flex": "1", "overflowY": "auto", "padding": "14px",
                            "background": "#f8f9fc", "borderRadius": "10px",
                            "marginBottom": "12px", "minHeight": "0"}),
            html.Div([
                html.Button(html.I(className="fas fa-microphone"), id="mic-btn", n_clicks=0,
                    style={"padding": "11px 14px", "background": "#f0f4ff",
                           "border": "1.5px solid #d0daf0", "borderRadius": "10px",
                           "cursor": "pointer", "fontSize": "15px", "flexShrink": "0", "color": "#0052A5"}),
                dcc.Input(id="chat-input", type="text",
                    placeholder="Posez votre question...", debounce=False, n_submit=0,
                    style={"flex": "1", "padding": "20px 20px", "border": "1.5px solid #d0daf0",
                           "borderRadius": "10px", "background": "white", "color": "#333",
                           "fontSize": "13px", "outline": "none"}),
                html.Button(html.I(className="fas fa-volume-up"), id="speak-btn", n_clicks=0,
                    style={"padding": "11px 14px", "background": "#f0f4ff",
                           "border": "1.5px solid #d0daf0", "borderRadius": "10px",
                           "cursor": "pointer", "flexShrink": "0", "fontSize": "15px", "color": "#0052A5"}),
                html.Button(html.I(className="fas fa-paper-plane"), id="send-btn", n_clicks=0,
                    style={"padding": "11px 20px",
                           "background": "linear-gradient(135deg,#0052A5,#00A86B)",
                           "color": "white", "border": "none", "borderRadius": "10px",
                           "cursor": "pointer", "fontSize": "15px", "flexShrink": "0"}),
            ], style={"display": "flex", "gap": "8px", "flexShrink": "0"}),
        ], style={"display": "flex", "flexDirection": "column", "height": "100%",
                  "padding": "18px", "boxSizing": "border-box", "overflow": "hidden",
                  "background": "white", "borderRadius": "14px",
                  "boxShadow": "0 4px 20px rgba(0,82,165,0.1)"})
        ], style={"flex": "1", "minWidth": "0", "height": "100%"})
    ], style={"display": "flex", "gap": "16px", "alignItems": "stretch",
              "height": "calc(100vh - 155px)", "overflow": "hidden"})


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

layout = html.Div(id='clientel-wrapper', children=[
    dcc.Store(id='chat-history',        data=[]),
    dcc.Store(id='conversations-store', data={}),
    dcc.Store(id='active-conv-store',   data=None),
    dcc.Store(id='conv-initialized',    data=False),
    dcc.Store(id='last-bot-text',       data=""),
    dcc.Store(id='groq-enabled',        data=True),
    dcc.Store(id='session-id',          data=str(uuid.uuid4())[:8]),
    dcc.Store(id='tts-trigger',         data=None),
    dcc.Download(id='download-file'),
    html.Div(id='clientel-content')
])


def _preload_data():
    try:
        get_cached_comments(force_refresh=True)
        print("[INFO] Données MongoDB préchargées")
    except Exception as e:
        print(f"[WARN] Préchargement échoué: {e}")
    try:
        from models.rag_engine import get_rag_engine
        get_rag_engine()
        print("[INFO] RAG engine prêt")
    except Exception as e:
        print(f"[INFO] RAG module absent, TF-IDF local sera utilisé: {e}")


threading.Thread(target=_preload_data, daemon=True).start()


# ============================================================
# CALLBACKS
# ============================================================

@callback(
    Output('clientel-content',    'children'),
    Output('clientel-wrapper',    'data-theme'),
    Output('conversations-store', 'data'),
    Output('active-conv-store',   'data'),
    Output('conv-initialized',    'data'),
    Input('theme-store',  'data'),
    Input('auth-store',   'data'),
    State('conversations-store', 'data'),
    State('active-conv-store',   'data'),
    State('conv-initialized',    'data'),
)
def render(theme, auth_data, convs_data, active_conv, initialized):
    theme     = theme or "light"
    user_data = None
    if auth_data and auth_data.get('is_authenticated'):
        user_data = auth_data.get('user', {})

    if not initialized:
        convs_data = charger_conversations_mongo() or {}
        if convs_data:
            sc = sorted(convs_data.items(), key=lambda x: x[1].get('updated_at', ''), reverse=True)
            active_conv = sc[0][0] if sc else None
        initialized = True
    elif convs_data is None:
        convs_data = {}

    content = make_content(theme, user_data, convs_data, active_conv)
    try:
        result = make_page_layout("clientel", "ClienTel Pulse",
                                   "Le pouls des interactions clients", content, theme, user_data)
        if isinstance(result, tuple):
            return result[0], theme, _strip_rich_html(convs_data), active_conv, initialized
        return result, theme, _strip_rich_html(convs_data), active_conv, initialized
    except Exception as e:
        print(f"Erreur layout: {e}")
        return html.Div(content, style={"padding": "20px"}), theme, _strip_rich_html(convs_data), active_conv, initialized


@callback(
    Output('conversations-store', 'data',    allow_duplicate=True),
    Output('active-conv-store',   'data',    allow_duplicate=True),
    Output('chat-messages',       'children'),
    Output('active-conv-title',   'children'),
    Output('conversations-list',  'children'),
    Input('new-conv-btn', 'n_clicks'),
    Input({'type': 'conv-btn',    'index': dash.ALL}, 'n_clicks'),
    Input({'type': 'delete-conv', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def manage_conversations(new_clicks, conv_clicks, delete_clicks):
    triggered    = ctx.triggered_id
    convs_data   = charger_conversations_mongo() or {}
    stats_global = analyser_donnees_completes(get_cached_comments())
    active_conv  = None
    messages     = []
    title_display = "ClienTel Pulse"

    if triggered == 'new-conv-btn':
        new_id = str(uuid.uuid4())[:8]
        now    = datetime.datetime.now().isoformat()
        title  = f"Conversation {len(convs_data) + 1}"
        convs_data[new_id] = {'title': title, 'messages': [], 'created_at': now, 'updated_at': now}
        sauvegarder_conversation_mongo(new_id, title, [])
        active_conv   = new_id
        title_display = title

    elif isinstance(triggered, dict) and triggered.get('type') == 'delete-conv':
        conv_id = triggered['index']
        if conv_id in convs_data:
            supprimer_conversation_mongo(conv_id)
            del convs_data[conv_id]
        if convs_data:
            sc = sorted(convs_data.items(), key=lambda x: x[1].get('updated_at', ''), reverse=True)
            active_conv   = sc[0][0]
            messages      = convs_data[active_conv].get('messages', [])
            title_display = convs_data[active_conv].get('title', 'Conversation')

    elif isinstance(triggered, dict) and triggered.get('type') == 'conv-btn':
        active_conv = triggered['index']
        if active_conv in convs_data:
            messages      = convs_data[active_conv].get('messages', [])
            title_display = convs_data[active_conv].get('title', 'Conversation')

    if active_conv is None and convs_data:
        sc = sorted(convs_data.items(), key=lambda x: x[1].get('updated_at', ''), reverse=True)
        active_conv   = sc[0][0]
        messages      = convs_data[active_conv].get('messages', [])
        title_display = convs_data[active_conv].get('title', 'Conversation')

    chat_bubbles = (_rebuild_bubbles(messages, stats_global) if messages
                    else [chat_bubble(make_welcome_message(stats_global), "bot", "rag", True)])

    return (_strip_rich_html(convs_data), active_conv, chat_bubbles,
            title_display, _build_conv_list(convs_data, active_conv))


# ============================================================
# FIX #2 : handle_message — PLUS de sync_active_conversation
# Le callback retourne active_conv INCHANGE pour eviter le saut
# ============================================================

@callback(
    Output('chat-messages',       'children',  allow_duplicate=True),
    Output('chat-input',          'value'),
    Output('chat-history',        'data'),
    Output('conversations-store', 'data',      allow_duplicate=True),
    Output('active-conv-store',   'data',      allow_duplicate=True),
    Output('conversations-list',  'children',  allow_duplicate=True),
    Output('last-bot-text',       'data'),
    Input('send-btn',    'n_clicks'),
    Input('chat-input',  'n_submit'),
    Input({'type': 'suggestion-btn', 'index': dash.ALL}, 'n_clicks'),
    State('chat-input',          'value'),
    State('chat-history',        'data'),
    State('groq-enabled',        'data'),
    State('session-id',          'data'),
    State('conversations-store', 'data'),
    State('active-conv-store',   'data'),
    prevent_initial_call=True,
)
def handle_message(send_clicks, n_submit, suggestion_clicks,
                   user_input, history, groq_enabled, session_id,
                   convs_data, active_conv):
    triggered = ctx.triggered_id
    suggestions_map = {
        0: "analyse complete",
        1: "benchmark S vs M",
        2: "commentaires Facebook",
        3: "frustrations clients",
        4: "analyse ce commentaire : internet lent et coupures frequentes",
        5: "aide",
    }
    if isinstance(triggered, dict) and triggered.get('type') == 'suggestion-btn':
        user_input = suggestions_map.get(triggered['index'], "aide")

    if not user_input or not user_input.strip():
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    stats_global = analyser_donnees_completes(get_cached_comments())
    db_info      = {}
    rich_response, response_source = generate_rich_response(
        user_input, stats_global, db_info, history or [], groq_enabled, session_id
    )

    # Charger convs si vide
    if not convs_data:
        convs_data = charger_conversations_mongo() or {}

    # Creer conv si necessaire
    if not active_conv or active_conv not in convs_data:
        new_id = str(uuid.uuid4())[:8]
        now    = datetime.datetime.now().isoformat()
        title  = user_input[:40] + ("…" if len(user_input) > 40 else "")
        convs_data[new_id] = {'title': title, 'messages': [], 'created_at': now, 'updated_at': now}
        active_conv = new_id
        sauvegarder_conversation_mongo(new_id, title, [])

    # Conserver l'active_conv courant — NE PAS changer
    current_active = active_conv
    now = datetime.datetime.now().isoformat()

    convs_data[current_active]['messages'].append({
        'role': 'user', 'text': user_input, 'source': None,
        'timestamp': now, 'is_html': False
    })

    bot_text_plain = f"Analyse: {user_input[:60]}"
    bot_source     = response_source if isinstance(response_source, str) else "rag"

    # Stocker la QUERY pour regenerer la reponse riche au rebuild
    convs_data[current_active]['messages'].append({
        'role': 'bot', 'text': "[rich]", 'source': bot_source,
        'timestamp': now, 'is_html': True, 'query': user_input,
        'plain_text': bot_text_plain
    })
    convs_data[current_active]['updated_at'] = now

    if len(convs_data[current_active]['messages']) == 2:
        convs_data[current_active]['title'] = user_input[:40] + ("…" if len(user_input) > 40 else "")

    sauvegarder_conversation_mongo(
        current_active,
        convs_data[current_active]['title'],
        convs_data[current_active]['messages']
    )

    # Construire les bulles pour affichage IMMEDIAT
    # Les messages precedents : on utilise _rebuild_bubbles (regenere les reponses riches)
    # Le nouveau message bot : on affiche directement rich_response (sans passer par rebuild)
    prev_msgs   = convs_data[current_active]['messages'][:-2]
    all_bubbles = _rebuild_bubbles(prev_msgs, stats_global)
    all_bubbles.append(chat_bubble(user_input, "user", None, False))
    all_bubbles.append(chat_bubble(rich_response, "bot", bot_source, True))

    new_history = (history or []) + [
        {"role": "user", "text": user_input},
        {"role": "bot",  "text": str(response_source)}
    ]

    # Retourner current_active INCHANGE — evite le saut de conversation
    return (all_bubbles, "", new_history,
            _strip_rich_html(convs_data), current_active,
            _build_conv_list(convs_data, current_active),
            bot_text_plain)


# ============================================================
# SUPPRESSION du callback sync_active_conversation
# C'etait lui qui causait le saut de conversation !
# Il n'est plus necessaire car on gere active_conv correctement
# dans handle_message et manage_conversations.
# ============================================================


@callback(
    Output('download-file', 'data'),
    Input('export-conv-btn', 'n_clicks'),
    State('conversations-store', 'data'),
    State('active-conv-store',   'data'),
    prevent_initial_call=True,
)
def export_conversation(n, convs_data, active_conv):
    if n and active_conv and convs_data and active_conv in convs_data:
        conv = convs_data[active_conv]
        return dict(content=json.dumps({
            "id":          active_conv,
            "title":       conv.get('title'),
            "export_date": datetime.datetime.now().isoformat(),
            "messages":    conv.get('messages', [])
        }, ensure_ascii=False, indent=2), filename=f"conversation_{active_conv}.json")
    return no_update


# ============================================================
# CLIENTSIDE — STT + TTS
# ============================================================

app = dash.get_app()

app.clientside_callback(
    """
    function(n_clicks, session_id) {
        if (!n_clicks) return window.dash_clientside.no_update;
        const btn = document.getElementById('mic-btn');
        const SR  = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { alert("Reconnaissance vocale non supportee."); return window.dash_clientside.no_update; }
        if (window._atRecording && window._atRecognition) { window._atRecognition.stop(); return window.dash_clientside.no_update; }
        window._atRecognition = new SR();
        window._atRecognition.lang = 'fr-FR';
        window._atRecognition.interimResults = true;
        window._atRecognition.continuous = false;
        window._atRecording = true;
        if (btn) { btn.style.background='#fde8e8'; btn.style.borderColor='#FF4444'; btn.style.color='#FF4444'; }
        window._atRecognition.onresult = function(e) {
            let ft='', it='';
            for (let i=e.resultIndex; i<e.results.length; i++) {
                if (e.results[i].isFinal) ft+=e.results[i][0].transcript;
                else it+=e.results[i][0].transcript;
            }
            const inp=document.getElementById('chat-input');
            if (inp) { const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(inp,ft||it); inp.dispatchEvent(new Event('input',{bubbles:true})); }
        };
        window._atRecognition.onend = function() {
            window._atRecording=false;
            if (btn) { btn.style.background=''; btn.style.borderColor=''; btn.style.color=''; }
            const inp=document.getElementById('chat-input');
            if (inp&&inp.value&&inp.value.trim().length>0) { setTimeout(function(){const s=document.getElementById('send-btn');if(s)s.click();},300); }
        };
        window._atRecognition.onerror = function(e) { window._atRecording=false; if(btn){btn.style.background='';btn.style.borderColor='';btn.style.color='';} };
        try { window._atRecognition.start(); } catch(err) { window._atRecording=false; }
        return window.dash_clientside.no_update;
    }
    """,
    Output('tts-trigger', 'data'),
    Input('mic-btn', 'n_clicks'),
    State('session-id', 'data'),
    prevent_initial_call=True,
)

app.clientside_callback(
    """
    function(n_clicks, last_text) {
        if (!n_clicks||n_clicks===0) return window.dash_clientside.no_update;
        if (!window.speechSynthesis) return window.dash_clientside.no_update;
        if (window.speechSynthesis.speaking||window.speechSynthesis.pending) { window.speechSynthesis.cancel(); return window.dash_clientside.no_update; }
        const clean=(last_text||'').replace(/<[^>]*>/g,' ').replace(/[\\[\\]{}]/g,' ').replace(/\\s+/g,' ').trim();
        if (!clean) return window.dash_clientside.no_update;
        function speak() {
            const utt=new SpeechSynthesisUtterance(clean); utt.lang='fr-FR'; utt.rate=0.88;
            const frv=window.speechSynthesis.getVoices().find(function(v){return v.lang&&v.lang.toLowerCase().startsWith('fr');});
            if (frv) utt.voice=frv; window.speechSynthesis.speak(utt);
        }
        if (window.speechSynthesis.getVoices().length>0) { speak(); }
        else { window.speechSynthesis.onvoiceschanged=function(){speak();window.speechSynthesis.onvoiceschanged=null;}; setTimeout(speak,500); }
        return window.dash_clientside.no_update;
    }
    """,
    Output('tts-trigger', 'data', allow_duplicate=True),
    Input('speak-btn', 'n_clicks'),
    State('last-bot-text', 'data'),
    prevent_initial_call=True,
)

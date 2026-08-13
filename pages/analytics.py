
# # """
# # Page d'Analyse Temporelle — ALGÉRIE TÉLÉCOM
# # AVEC FILTRES PÉRIODE (Global / Mois / Jour) — VERSION FINALE CORRIGÉE
# # ✅ Événements détectés automatiquement depuis MongoDB
# # ✅ Heures UTC+1 (Algérie) correctement gérées
# # ✅ Toutes les anomalies du mois affichées
# # ✅ FIX : heure 0 (minuit) correctement détectée (bug falsy 0)
# # """

# # import dash
# # from dash import html, dcc, callback, Input, Output, State
# # import plotly.graph_objects as go
# # import pandas as pd
# # import numpy as np
# # from datetime import datetime, timedelta
# # import statistics
# # import sys, os

# # sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# # from components import make_page_layout
# # from database import MONGO_AVAILABLE, _col

# # dash.register_page(__name__, path='/analytics', name='Analyse Temporelle')

# # # ── PALETTE ALGÉRIE TÉLÉCOM ───────────────────────────────────────────────────
# # BLUE       = "#003087"
# # BLUE_MID   = "#1a4fa0"
# # BLUE_LIGHT = "#4a80d4"
# # BLUE_BG    = "#e8f0fb"
# # GREEN      = "#00a854"
# # GREEN_BG   = "#e6f7ef"
# # RED        = "#e8384f"
# # RED_BG     = "#fde8eb"
# # ORANGE     = "#f59e0b"
# # ORANGE_BG  = "#fef3cd"
# # NEUTRAL    = "#64748b"

# # # ── STYLES BOUTONS PÉRIODE (inline) ──────────────────────────────────────────
# # style_btn_active = {
# #     "padding": "6px 16px",
# #     "borderRadius": "20px",
# #     "border": "none",
# #     "background": BLUE,
# #     "color": "white",
# #     "cursor": "pointer",
# #     "fontSize": "12px",
# #     "fontWeight": "500",
# #     "transition": "all 0.2s ease",
# #     "display": "flex",
# #     "alignItems": "center",
# #     "gap": "6px",
# # }
# # style_btn_inactive = {
# #     "padding": "6px 16px",
# #     "borderRadius": "20px",
# #     "border": f"1px solid {BLUE}",
# #     "background": "transparent",
# #     "color": BLUE,
# #     "cursor": "pointer",
# #     "fontSize": "12px",
# #     "fontWeight": "500",
# #     "transition": "all 0.2s ease",
# #     "display": "flex",
# #     "alignItems": "center",
# #     "gap": "6px",
# # }

# # # ── ICÔNES PAR THÈME D'ANOMALIE ───────────────────────────────────────────────
# # _THEME_ICONS = {
# #     "reseau":      "fas fa-broadcast-tower",
# #     "facturation": "fas fa-file-invoice",
# #     "service":     "fas fa-headset",
# #     "application": "fas fa-mobile-alt",
# #     "offre":       "fas fa-tags",
# #     "hors_sujet":  "fas fa-question-circle",
# #     "default":     "fas fa-circle-exclamation",
# # }


# # def _icon_for_theme(theme: str) -> str:
# #     if not theme:
# #         return _THEME_ICONS["default"]
# #     for key in _THEME_ICONS:
# #         if key in (theme or "").lower():
# #             return _THEME_ICONS[key]
# #     return _THEME_ICONS["default"]


# # # ── COULEURS PAR THÈME ────────────────────────────────────────────────────────
# # def _colors(theme):
# #     if theme == "dark":
# #         return {
# #             "bg": "#141c2e", "paper_bg": "#141c2e", "text": "#dce8f5",
# #             "grid": "#1e2d47", "axis_line": "#1e2d47", "primary": "#4a80d4",
# #             "secondary": "#6c8dcc", "success": "#2ecc71", "warning": "#f39c12",
# #             "danger": "#f06070", "neutral": "#607b99", "card_bg": "#141c2e",
# #             "stat_bg": "#1a2236", "border": "#1e2d47",
# #         }
# #     return {
# #         "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
# #         "grid": "#e8edf5", "axis_line": "#e8edf5", "primary": BLUE,
# #         "secondary": BLUE_MID, "success": GREEN, "warning": ORANGE,
# #         "danger": RED, "neutral": NEUTRAL, "card_bg": "#ffffff",
# #         "stat_bg": "#f8fafd", "border": "rgba(0,48,135,0.10)",
# #     }


# # def _base_layout(c, height, margin=None):
# #     m = margin or dict(l=10, r=10, t=20, b=10)
# #     return dict(
# #         plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
# #         font=dict(color=c["text"], family="'Inter', 'DM Sans', sans-serif", size=10),
# #         height=height, margin=m,
# #     )


# # def now_local():
# #     """Heure locale Algérie (UTC+1)."""
# #     return datetime.utcnow() + timedelta(hours=1)


# # # ── HELPERS ────────────────────────────────────────────────────────────────────

# # def _hour_has_data(hour_dict):
# #     """
# #     Retourne True si le dict contient une heure valide.
# #     ⚠️  L'heure 0 (minuit) est valide — on NE PAS tester `get('hour')` directement
# #         car 0 est falsy en Python. On vérifie explicitement `is not None`.
# #     """
# #     return hour_dict is not None and hour_dict.get("hour") is not None

# # def _score_has_data(hour_dict):
# #     """Retourne True si le dict contient un score valide."""
# #     return hour_dict is not None and hour_dict.get("score") is not None

# # def _fmt_hour(hour_dict):
# #     """Formate une heure en 'HH:00', gère minuit (0) correctement."""
# #     if not _hour_has_data(hour_dict):
# #         return "--:00"
# #     return f"{hour_dict['hour']:02d}:00"


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 1. FONCTIONS DE DONNÉES PAR PÉRIODE
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def get_hourly_data_global():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         pipeline = [
# #             {"$match": {
# #                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #                 "heure": {"$exists": True, "$ne": None},
# #             }},
# #             {"$group": {
# #                 "_id": "$heure",
# #                 "total": {"$sum": 1},
# #                 "sentiment_sum": {"$sum": "$sentiment_score"},
# #                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         data = []
# #         for r in results:
# #             total = r["total"]
# #             if total > 0:
# #                 data.append({
# #                     "hour": r["_id"],
# #                     "avg_score": round(r["sentiment_sum"] / total, 3),
# #                     "neg_pct": round(r["negatifs"] / total * 100, 1),
# #                     "pos_pct": round(r["positifs"] / total * 100, 1),
# #                     "total": total,
# #                 })
# #         return pd.DataFrame(data)
# #     except Exception as e:
# #         print(f"Erreur get_hourly_data_global: {e}")
# #         return pd.DataFrame()


# # def get_weekly_evolution_global():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame(), []
# #     try:
# #         pipeline = [
# #             {"$match": {
# #                 "annee_semaine": {"$exists": True, "$ne": None},
# #                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #             }},
# #             {"$group": {
# #                 "_id": "$annee_semaine",
# #                 "avg_score": {"$avg": "$sentiment_score"},
# #                 "total": {"$sum": 1},
# #                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame(), []
# #         df = pd.DataFrame([{
# #             "week": r["_id"],
# #             "avg_score": round(r["avg_score"], 3),
# #             "total": r["total"],
# #             "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
# #         } for r in results])
# #         if len(df) > 15:
# #             df = df.tail(15)
# #         peaks = []
# #         if len(df) > 3:
# #             mean_score = df["avg_score"].mean()
# #             std_score  = df["avg_score"].std()
# #             for _, row in df.iterrows():
# #                 if row["avg_score"] < mean_score - 1.5 * std_score:
# #                     peaks.append({"week": row["week"], "score": row["avg_score"]})
# #         return df, peaks
# #     except Exception as e:
# #         print(f"Erreur get_weekly_evolution_global: {e}")
# #         return pd.DataFrame(), []


# # def _mois_bornes():
# #     now   = now_local()
# #     debut = datetime(now.year, now.month, 1) - timedelta(hours=1)
# #     fin   = datetime(now.year + 1, 1, 1) - timedelta(hours=1) if now.month == 12 \
# #             else datetime(now.year, now.month + 1, 1) - timedelta(hours=1)
# #     return debut, fin


# # def get_hourly_data_mois():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         debut, fin = _mois_bornes()
# #         mois_str   = now_local().strftime("%Y-%m")
# #         match_filter = {
# #             "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #             "$or": [
# #                 {"mois": mois_str},
# #                 {"date_originale": {"$gte": debut, "$lt": fin}},
# #                 {"date_annotation": {"$gte": debut, "$lt": fin}},
# #             ],
# #         }
# #         pipeline = [
# #             {"$match": match_filter},
# #             {"$addFields": {"_date_src": {"$cond": {
# #                 "if": {"$eq": [{"$type": "$date_originale"}, "date"]},
# #                 "then": "$date_originale",
# #                 "else": {"$cond": {
# #                     "if": {"$eq": [{"$type": "$date_annotation"}, "date"]},
# #                     "then": "$date_annotation", "else": None,
# #                 }},
# #             }}}},
# #             {"$addFields": {"_heure_calc": {"$cond": {
# #                 "if": {"$and": [
# #                     {"$ne": ["$heure", None]},
# #                     {"$ne": [{"$type": "$heure"}, "missing"]},
# #                 ]},
# #                 "then": "$heure",
# #                 "else": {"$cond": {
# #                     "if": {"$ne": ["$_date_src", None]},
# #                     "then": {"$hour": {"$add": ["$_date_src", 3600000]}},
# #                     "else": None,
# #                 }},
# #             }}}},
# #             {"$match": {"_heure_calc": {"$ne": None}}},
# #             {"$group": {
# #                 "_id": "$_heure_calc",
# #                 "total": {"$sum": 1},
# #                 "sentiment_sum": {"$sum": "$sentiment_score"},
# #                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         data = []
# #         for r in results:
# #             total = r["total"]
# #             if total > 0:
# #                 data.append({
# #                     "hour": r["_id"],
# #                     "avg_score": round(r["sentiment_sum"] / total, 3),
# #                     "neg_pct": round(r["negatifs"] / total * 100, 1),
# #                     "pos_pct": round(r["positifs"] / total * 100, 1),
# #                     "total": total,
# #                 })
# #         return pd.DataFrame(data)
# #     except Exception as e:
# #         print(f"Erreur get_hourly_data_mois: {e}")
# #         return pd.DataFrame()

# # def get_weekly_evolution_mois():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame(), []
# #     try:
# #         debut, fin = _mois_bornes()
# #         mois_str   = now_local().strftime("%Y-%m")
# #         match_filter = {
# #             "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #             "$or": [
# #                 {"mois": mois_str},
# #                 {"date_clean": {"$gte": debut, "$lt": fin}},
# #                 {"date_annotation": {"$gte": debut, "$lt": fin}},
# #             ],
# #         }
# #         pipeline = [
# #             {"$match": match_filter},
# #             # ✅ Grouper par jour (date_clean) au lieu de annee_semaine
# #             {"$addFields": {
# #                 "_jour": {
# #                     "$cond": {
# #                         "if": {"$eq": [{"$type": "$date_clean"}, "date"]},
# #                         "then": {
# #                             "$dateToString": {
# #                                 "format": "%Y-%m-%d",
# #                                 "date": "$date_clean",
# #                             }
# #                         },
# #                         "else": None,
# #                     }
# #                 }
# #             }},
# #             {"$match": {"_jour": {"$ne": None}}},
# #             {"$group": {
# #                 "_id": "$_jour",
# #                 "avg_score": {"$avg": "$sentiment_score"},
# #                 "total": {"$sum": 1},
# #                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame(), []
# #         df = pd.DataFrame([{
# #             "week": r["_id"],   # ← contient maintenant "2026-05-01", "2026-05-02", etc.
# #             "avg_score": round(r["avg_score"], 3),
# #             "total": r["total"],
# #             "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
# #         } for r in results])
# #         peaks = []
# #         if len(df) > 2:
# #             mean_score = df["avg_score"].mean()
# #             std_score  = df["avg_score"].std()
# #             for _, row in df.iterrows():
# #                 if row["avg_score"] < mean_score - 1.5 * std_score:
# #                     peaks.append({"week": row["week"], "score": row["avg_score"]})
# #         return df, peaks
# #     except Exception as e:
# #         print(f"Erreur get_weekly_evolution_mois: {e}")
# #         return pd.DataFrame(), []
        
# # def get_hourly_data_jour():
# #     """
# #     Données horaires pour AUJOURD'HUI uniquement.
# #     Filtre sur date_clean (vraie date client) = jour courant en Algérie (UTC+1).
# #     """
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         now = now_local()  # heure locale Algérie (UTC+1)
 
# #         # Début et fin de la journée en cours (heure Algérie → stocker en UTC naïf)
# #         # date_clean est stocké en UTC naïf par le consumer (datetime.now() sans tzinfo)
# #         # Le consumer fait : date_ref = parser_date_client("03/05/2026 22:24")
# #         # → datetime(2026, 5, 3, 22, 24) — naïf, traité comme heure locale Algérie
# #         # Donc pour filtrer "aujourd'hui en Algérie", on compare directement sans décalage
# #         debut_jour = datetime(now.year, now.month, now.day, 0, 0, 0)
# #         fin_jour   = datetime(now.year, now.month, now.day, 23, 59, 59)
 
# #         pipeline = [
# #             {"$match": {
# #                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #                 # ✅ Filtre sur date_clean = vraie date du commentaire client
# #                 # date_clean stocké tel quel depuis le fichier Excel (heure Algérie)
# #                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
# #             }},
# #             {"$group": {
# #                 # ✅ Utiliser le champ "heure" déjà calculé par le consumer (heure réelle client)
# #                 "_id": "$heure",
# #                 "total": {"$sum": 1},
# #                 "sentiment_sum": {"$sum": "$sentiment_score"},
# #                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         data = []
# #         for r in results:
# #             total = r["total"]
# #             if total > 0 and r["_id"] is not None:
# #                 data.append({
# #                     "hour": r["_id"],
# #                     "avg_score": round(r["sentiment_sum"] / total, 3),
# #                     "neg_pct": round(r["negatifs"] / total * 100, 1),
# #                     "pos_pct": round(r["positifs"] / total * 100, 1),
# #                     "total": total,
# #                 })
# #         return pd.DataFrame(data)
# #     except Exception as e:
# #         print(f"Erreur get_hourly_data_jour: {e}")
# #         return pd.DataFrame()
 
 
# # def get_weekly_evolution_jour():
# #     """
# #     Évolution sur les 7 derniers jours (date réelle client).
# #     Filtre sur date_clean uniquement.
# #     """
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame(), []
# #     try:
# #         now = now_local()
# #         # 7 jours en arrière — même logique : date_clean = heure locale Algérie stockée naïve
# #         sept_jours = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=6)
 
# #         pipeline = [
# #             {"$match": {
# #                 "date_clean": {"$gte": sept_jours},
# #                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #             }},
# #             {"$addFields": {
# #                 "jour_str": {
# #                     "$dateToString": {
# #                         "format": "%Y-%m-%d",
# #                         "date": "$date_clean",
# #                     }
# #                 }
# #             }},
# #             {"$group": {
# #                 "_id": "$jour_str",
# #                 "avg_score": {"$avg": "$sentiment_score"},
# #                 "total": {"$sum": 1},
# #                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame(), []
# #         df = pd.DataFrame([{
# #             "week": r["_id"],
# #             "avg_score": round(r["avg_score"], 3),
# #             "total": r["total"],
# #             "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
# #         } for r in results])
# #         peaks = []
# #         if len(df) > 2:
# #             mean_score = df["avg_score"].mean()
# #             std_score  = df["avg_score"].std()
# #             for _, row in df.iterrows():
# #                 if row["avg_score"] < mean_score - 1.5 * std_score:
# #                     peaks.append({"week": row["week"], "score": row["avg_score"]})
# #         return df, peaks
# #     except Exception as e:
# #         print(f"Erreur get_weekly_evolution_jour: {e}")
# #         return pd.DataFrame(), []
 

# # def get_temporal_metrics_periode(df_weekly, df_hourly, periode="global"):
# #     metrics = {"periode": periode, "total_messages": 0}
# #     if not df_hourly.empty:
# #         metrics["total_messages"] = int(df_hourly["total"].sum())
# #         if not df_hourly["avg_score"].isnull().all():
# #             worst_h = df_hourly.loc[df_hourly["avg_score"].idxmin()]
# #             best_h  = df_hourly.loc[df_hourly["avg_score"].idxmax()]
# #             # ✅ FIX : stocker explicitement hour=int(...) — jamais None pour une ligne existante
# #             metrics["worst_hour"] = {
# #                 "hour": int(worst_h["hour"]),
# #                 "score": float(worst_h["avg_score"]),
# #             }
# #             metrics["best_hour"] = {
# #                 "hour": int(best_h["hour"]),
# #                 "score": float(best_h["avg_score"]),
# #             }
# #     if not df_weekly.empty:
# #         worst = df_weekly.loc[df_weekly["avg_score"].idxmin()]
# #         best  = df_weekly.loc[df_weekly["avg_score"].idxmax()]
# #         metrics["worst_week"] = {"week": worst["week"], "score": float(worst["avg_score"])}
# #         metrics["best_week"]  = {"week": best["week"],  "score": float(best["avg_score"])}
# #         if len(df_weekly) > 1:
# #             slope = np.polyfit(np.arange(len(df_weekly)), df_weekly["avg_score"].values, 1)[0]
# #             metrics["trend"]       = "positive" if slope > 0.01 else "negative" if slope < -0.01 else "stable"
# #             metrics["trend_value"] = round(slope, 4)
# #         else:
# #             metrics["trend"]       = "stable"
# #             metrics["trend_value"] = 0.0
# #     elif not df_hourly.empty:
# #         if len(df_hourly) > 1 and not df_hourly["avg_score"].isnull().all():
# #             slope = np.polyfit(np.arange(len(df_hourly)), df_hourly["avg_score"].values, 1)[0]
# #             metrics["trend"]       = "positive" if slope > 0.005 else "negative" if slope < -0.005 else "stable"
# #             metrics["trend_value"] = round(slope, 4)
# #         else:
# #             metrics["trend"]       = "stable"
# #             metrics["trend_value"] = 0.0
# #     return metrics


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 2. DÉTECTION RÉELLE DES ANOMALIES DEPUIS MONGODB
# # # ═══════════════════════════════════════════════════════════════════════════════
# # def get_real_events_from_mongo(periode: str = "global", top_n: int = None):
# #     """
# #     Détecte automatiquement les vraies périodes anormales depuis MongoDB.
# #     ✅ CORRECTION : onglet "jour" filtre sur les 24 dernières heures (date_clean)
# #                     et groupe par heure, pas par jour
# #     """
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         match_base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
# #         add_fields_stage = None
# #         label_prefix     = "Semaine"

# #         if periode == "jour":
# #             # ✅ CORRECTION PRINCIPALE :
# #             #   - Filtre sur date_clean (datetime réel, pas string)
# #             #   - Borne = 24h (pas 7 jours)
# #             #   - UTC-1h car date_clean est stocké en UTC naïf par le consumer
# #             cutoff_utc = now_local() - timedelta(hours=24) - timedelta(hours=1)
# #             match_base["date_clean"] = {"$gte": cutoff_utc}
# #             label_prefix = "Heure"
# #             add_fields_stage = {"$addFields": {"jour_str": {
# #                 "$dateToString": {
# #                     "format": "%Y-%m-%d %H:00",
# #                     # Convertir UTC → UTC+1 pour afficher l'heure Algérie
# #                     "date": {"$add": ["$date_clean", 3600000]},
# #                 }
# #             }}}
# #             group_by = "$jour_str"

# #         elif periode == "mois":
# #             debut, fin = _mois_bornes()
# #             mois_str   = now_local().strftime("%Y-%m")
# #             match_base["$or"] = [
# #                 {"annee_mois": mois_str},
# #                 {"date_clean": {"$gte": debut, "$lt": fin}},
# #                 {"date_annotation": {"$gte": debut, "$lt": fin}},
# #             ]
# #             label_prefix = "Journée"
# #             group_by     = {"$dateToString": {"format": "%Y-%m-%d", "date": "$date_clean"}}

# #         else:
# #             label_prefix = "Semaine"
# #             group_by     = "$annee_semaine"

# #         pipeline = [{"$match": match_base}]
# #         if add_fields_stage:
# #             pipeline.append(add_fields_stage)
# #             pipeline.append({"$match": {"jour_str": {"$ne": None}}})

# #         pipeline += [
# #             {"$group": {
# #                 "_id": group_by,
# #                 "avg_score": {"$avg": "$sentiment_score"},
# #                 "total":     {"$sum": 1},
# #                 "negatifs":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 "positifs":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# #                 "themes":    {"$push": "$theme_pred"},
# #                 "sources":   {"$push": "$source"},
# #             }},
# #             {"$match": {"_id": {"$ne": None}}},
# #             {"$sort": {"_id": 1}},
# #         ]

# #         results = list(_col.aggregate(pipeline))
# #         if not results or len(results) < 2:
# #             return []

# #         scores = [r["avg_score"] for r in results if r.get("avg_score") is not None]
# #         if len(scores) < 2:
# #             return []

# #         mean_score = statistics.mean(scores)
# #         std_score  = statistics.stdev(scores) if len(scores) > 1 else 1.0
# #         if std_score == 0:
# #             std_score = 1.0

# #         anomalies = []
# #         for i, r in enumerate(results):
# #             s       = r.get("avg_score") or 0
# #             total   = r.get("total") or 1
# #             neg_pct = round(r.get("negatifs", 0) / total * 100, 1)
# #             z_score = (s - mean_score) / std_score

# #             if z_score < -0.8 or neg_pct > 65:
# #                 score_before  = round(results[i - 1].get("avg_score") or mean_score, 3) if i > 0 else round(mean_score, 3)
# #                 score_after   = round(s, 3)
# #                 delta         = round(score_after - score_before, 3)

# #                 themes_list     = [t for t in (r.get("themes") or []) if t]
# #                 theme_dominant  = max(set(themes_list), key=themes_list.count) if themes_list else "autre"

# #                 sources_list    = [s2 for s2 in (r.get("sources") or []) if s2]
# #                 source_dominant = max(set(sources_list), key=sources_list.count) if sources_list else "Inconnue"

# #                 period_id = r["_id"]

# #                 # ✅ CORRECTION : format adapté selon la période
# #                 if periode == "jour":
# #                     # period_id = "2026-05-18 14:00"
# #                     period_label = str(period_id)  # Affiche "2026-05-18 14:00"
# #                     try:
# #                         heure_str = str(period_id).split(" ")[-1]  # "14:00"
# #                         period_label = heure_str
# #                     except Exception:
# #                         period_label = str(period_id)
# #                 elif periode == "mois":
# #                     try:
# #                         dt = datetime.strptime(str(period_id), "%Y-%m-%d")
# #                         mois_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
# #                                    "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
# #                         period_label = f"{dt.day} {mois_fr[dt.month - 1]} {dt.year}"
# #                     except Exception:
# #                         period_label = str(period_id)
# #                 else:
# #                     period_label = str(period_id)

# #                 severity = abs(z_score)
# #                 if severity > 2:
# #                     title_prefix = "⚠️ Pic critique"
# #                 elif severity > 1.5:
# #                     title_prefix = "Forte dégradation"
# #                 else:
# #                     title_prefix = "Dégradation détectée"

# #                 anomalies.append({
# #                     "id":           f"auto_{period_id}",
# #                     "date":         str(period_id),
# #                     "title":        f"{title_prefix} — {label_prefix} {period_label}",
# #                     "description":  (
# #                         f"{neg_pct:.0f}% d'avis négatifs · {total:,} messages · "
# #                         f"Score moyen : {score_after:+.3f} · Source : {source_dominant}"
# #                     ),
# #                     "impact":       "negatif",
# #                     "source":       f"Détection automatique ({source_dominant})",
# #                     "icon":         _icon_for_theme(theme_dominant),
# #                     "score_before": score_before,
# #                     "score_after":  score_after,
# #                     "delta":        delta,
# #                     "impact_type":  "negatif" if delta < -0.05 else ("positif" if delta > 0.05 else "neutre"),
# #                     "_z_score":     round(z_score, 2),
# #                     "_neg_pct":     neg_pct,
# #                 })

# #         anomalies.sort(key=lambda x: x["_z_score"])

# #         if periode == "mois":
# #             return anomalies
# #         return anomalies[:top_n] if top_n else anomalies[:5]

# #     except Exception as e:
# #         print(f"Erreur get_real_events_from_mongo: {e}")
# #         return []

# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 3. COMPOSANTS SVG RING
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def make_score_ring(score, color, size=65):
# #     if score is None:
# #         score = 0
# #     pct         = max(0, min(100, int((score + 1) / 2 * 100)))
# #     score_label = f"{score:+.2f}"
# #     fig = go.Figure()
# #     fig.add_trace(go.Pie(
# #         values=[pct, 100 - pct], hole=0.7,
# #         marker_colors=[color, "#e8edf5"],
# #         textinfo='none', hoverinfo='none', showlegend=False,
# #         sort=False, direction="clockwise", rotation=90,
# #     ))
# #     fig.add_annotation(
# #         text=score_label, x=0.5, y=0.5, showarrow=False,
# #         font=dict(size=10, color=color), xanchor="center", yanchor="middle",
# #     )
# #     fig.update_layout(
# #         width=size, height=size, margin=dict(l=0, r=0, t=0, b=0),
# #         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
# #     )
# #     return html.Div(
# #         dcc.Graph(figure=fig, config={'displayModeBar': False}),
# #         style={"flexShrink": "0", "width": f"{size}px", "height": f"{size}px"},
# #     )


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 4. KPI CARDS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def make_kpi_cards(metrics):
# #     if not metrics or metrics.get("total_messages", 0) == 0:
# #         return html.Div(
# #             html.Div([
# #                 html.I(className="fas fa-chart-line", style={"fontSize": "24px", "color": NEUTRAL}),
# #                 html.H4("Aucune donnée", style={"marginTop": "12px", "color": NEUTRAL}),
# #                 html.P("Sélectionnez une période avec des données disponibles",
# #                        style={"fontSize": "12px", "color": NEUTRAL}),
# #             ], style={"textAlign": "center", "padding": "40px"}),
# #             className="at-kpi-grid",
# #         )

# #     worst_week = metrics.get("worst_week", {})
# #     best_week  = metrics.get("best_week", {})
# #     worst_hour = metrics.get("worst_hour", {})
# #     best_hour  = metrics.get("best_hour", {})
# #     trend_dir  = metrics.get("trend", "stable")
# #     trend_val  = metrics.get("trend_value", 0)
# #     periode    = metrics.get("periode", "global")
# #     total_msgs = metrics.get("total_messages", 0)

# #     if trend_dir == "positive":
# #         t_color, t_icon, t_label = GREEN, "fas fa-arrow-trend-up", "Amélioration"
# #         t_delta = f"+{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"
# #     elif trend_dir == "negative":
# #         t_color, t_icon, t_label = RED, "fas fa-arrow-trend-down", "Dégradation"
# #         t_delta = f"{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"
# #     else:
# #         t_color, t_icon, t_label = ORANGE, "fas fa-minus", "Stable"
# #         t_delta = f"{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"

# #     def _card(accent, icon_cls, icon_bg, icon_color, label, value_el, ring_el=None, extra_cls=""):
# #         return html.Div([
# #             html.Div([
# #                 html.Div(
# #                     html.I(className=icon_cls, style={"fontSize": "14px", "color": icon_color}),
# #                     className="at-kpi-icon", style={"background": icon_bg},
# #                 ),
# #                 html.Span(label, className="at-kpi-label"),
# #             ], className="at-kpi-title-row"),
# #             html.Div([value_el, ring_el or html.Span()], className="at-kpi-value-row"),
# #         ], className=f"at-kpi-card {extra_cls}", style={"--kpi-accent": accent})

# #     trend_card = html.Div([
# #         html.Div([
# #             html.Div(
# #                 html.I(className=t_icon, style={"fontSize": "20px", "color": "white"}),
# #                 className="at-kpi-icon", style={"background": "rgba(255,255,255,0.2)"},
# #             ),
# #             html.Span("Tendance générale", className="at-kpi-label",
# #                       style={"color": "rgba(255,255,255,0.7)"}),
# #         ], className="at-kpi-title-row"),
# #         html.Div([html.Div([
# #             html.Div(f"{total_msgs:,} messages",
# #                      style={"color": "white", "fontSize": "14px", "fontWeight": "bold", "marginTop": "5px"}),
# #             html.Div(t_label, style={"color": "white", "fontSize": "13px", "marginTop": "8px"}),
# #             html.Div(t_delta,  style={"color": "rgba(255,255,255,0.7)", "fontSize": "11px", "marginTop": "4px"}),
# #         ], className="at-trend-body")], className="at-kpi-value-row"),
# #     ], className="at-kpi-card trend", style={"background": BLUE, "border": "none"})

# #     # ── MODE JOUR ──────────────────────────────────────────────────────────────
# #     if periode == "jour":
# #         worst_day = worst_week
# #         best_day  = best_week

# #         def _fmt_day(day_str):
# #             if not day_str:
# #                 return "N/A"
# #             try:
# #                 dt = datetime.strptime(str(day_str), "%Y-%m-%d")
# #                 mois_fr = ["Jan","Fév","Mar","Avr","Mai","Juin",
# #                            "Juil","Aoû","Sep","Oct","Nov","Déc"]
# #                 return f"{dt.day} {mois_fr[dt.month - 1]}"
# #             except Exception:
# #                 return str(day_str)

# #         cards = [
# #             _card(
# #                 RED, "fas fa-circle-exclamation", "rgba(232,56,79,0.10)", RED,
# #                 "Heure critique (24h)",
# #                 # ✅ FIX : utiliser _fmt_hour() qui gère l'heure 0 correctement
# #                 html.Div(_fmt_hour(worst_hour), className="at-kpi-value"),
# #                 make_score_ring(worst_hour.get("score", 0), RED) if _score_has_data(worst_hour) else None,
# #             ),
# #             _card(
# #                 GREEN, "fas fa-circle-check", "rgba(0,168,84,0.10)", GREEN,
# #                 "Heure favorable (24h)",
# #                 # ✅ FIX : utiliser _fmt_hour() qui gère l'heure 0 correctement
# #                 html.Div(_fmt_hour(best_hour), className="at-kpi-value"),
# #                 make_score_ring(best_hour.get("score", 0), GREEN) if _score_has_data(best_hour) else None,
# #             ),
# #             _card(
# #                 RED, "fas fa-calendar-xmark", "rgba(232,56,79,0.10)", RED,
# #                 "Jour difficile (7j)",
# #                 html.Div(_fmt_day(worst_day.get("week") if worst_day else None), className="at-kpi-value"),
# #                 make_score_ring(worst_day.get("score", 0), RED) if _score_has_data(worst_day) else None,
# #             ),
# #             _card(
# #                 GREEN, "fas fa-calendar-check", "rgba(0,168,84,0.10)", GREEN,
# #                 "Meilleur jour (7j)",
# #                 html.Div(_fmt_day(best_day.get("week") if best_day else None), className="at-kpi-value"),
# #                 make_score_ring(best_day.get("score", 0), GREEN) if _score_has_data(best_day) else None,
# #             ),
# #             trend_card,
# #         ]
# #         return html.Div(cards, className="at-kpi-grid")

# #     # ── MODE GLOBAL / MOIS ─────────────────────────────────────────────────────
# #     week_labels     = {"global": "Semaine difficile", "mois": "Jour difficile"}
# #     week_labels_pos = {"global": "Semaine positive",  "mois": "Meilleur jour"}
# #     hour_labels     = {"global": "Heure critique",    "mois": "Heure critique (mois)"}
# #     hour_labels_pos = {"global": "Heure favorable",   "mois": "Heure favorable (mois)"}

# #     cards = [
# #         _card(
# #             RED, "fas fa-circle-exclamation", "rgba(232,56,79,0.10)", RED,
# #             week_labels.get(periode, "Semaine difficile"),
# #             html.Div(str(worst_week.get("week", "N/A")) if worst_week else "N/A", className="at-kpi-value"),
# #             make_score_ring(worst_week.get("score", 0), RED) if _score_has_data(worst_week) else None,
# #         ),
# #         _card(
# #             GREEN, "fas fa-circle-check", "rgba(0,168,84,0.10)", GREEN,
# #             week_labels_pos.get(periode, "Semaine positive"),
# #             html.Div(str(best_week.get("week", "N/A")) if best_week else "N/A", className="at-kpi-value"),
# #             make_score_ring(best_week.get("score", 0), GREEN) if _score_has_data(best_week) else None,
# #         ),
# #         _card(
# #             ORANGE, "fas fa-clock", "rgba(245,158,11,0.10)", ORANGE,
# #             hour_labels.get(periode, "Heure critique"),
# #             # ✅ FIX : utiliser _fmt_hour() qui gère l'heure 0 correctement
# #             html.Div(_fmt_hour(worst_hour), className="at-kpi-value"),
# #             make_score_ring(worst_hour.get("score", 0), ORANGE) if _score_has_data(worst_hour) else None,
# #         ),
# #         _card(
# #             GREEN, "fas fa-sun", "rgba(0,168,84,0.10)", GREEN,
# #             hour_labels_pos.get(periode, "Heure favorable"),
# #             # ✅ FIX : utiliser _fmt_hour() qui gère l'heure 0 correctement
# #             html.Div(_fmt_hour(best_hour), className="at-kpi-value"),
# #             make_score_ring(best_hour.get("score", 0), GREEN) if _score_has_data(best_hour) else None,
# #         ),
# #         trend_card,
# #     ]
# #     return html.Div(cards, className="at-kpi-grid")


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 5. GRAPHIQUES PLOTLY
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def make_hourly_stacked(df, theme="light"):
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 260))
# #         return fig
# #     fig = go.Figure()
# #     fig.add_trace(go.Bar(
# #         x=df["hour"], y=df["pos_pct"], name="Satisfaits",
# #         marker=dict(color=c["success"], cornerradius=5),
# #         text=[f"{p:.0f}%" for p in df["pos_pct"]], textposition="inside",
# #         textfont=dict(size=9, color="white"),
# #         hovertemplate="%{x}h — Satisfaits: %{y:.1f}%<extra></extra>",
# #     ))
# #     fig.add_trace(go.Bar(
# #         x=df["hour"], y=df["neg_pct"], name="Insatisfaits",
# #         marker=dict(color=c["danger"], cornerradius=5),
# #         text=[f"{n:.0f}%" for n in df["neg_pct"]], textposition="inside",
# #         textfont=dict(size=9, color="white"),
# #         hovertemplate="%{x}h — Insatisfaits: %{y:.1f}%<extra></extra>",
# #     ))
# #     layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
# #     layout.update(
# #         xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1,range=[0, 23], gridcolor=c["grid"]),
# #         yaxis=dict(title="%", range=[0, 100], ticksuffix="%", gridcolor=c["grid"]),
# #         barmode="stack",
# #         legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"),
# #         hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_volume_bars(df, theme="light"):
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 260))
# #         return fig
# #     max_v      = df["total"].max() if not df.empty else 1
# #     bar_colors = [f"rgba(0,48,135,{0.45 + 0.55 * v / max_v:.2f})" for v in df["total"]]
# #     fig = go.Figure()
# #     fig.add_trace(go.Bar(
# #         x=df["hour"], y=df["total"],
# #         marker=dict(color=bar_colors, cornerradius=6),
# #         text=[f"{v:,}" for v in df["total"]], textposition="outside",
# #         textfont=dict(size=8, color=c["text"]),
# #         hovertemplate="%{x}h — %{y:,} messages<extra></extra>",
# #     ))
# #     layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
# #     layout.update(
# #         xaxis=dict(title="Heure", tickmode="linear", tick0=0,  dtick=1,range=[0, 23],gridcolor=c["grid"]),
# #         yaxis=dict(title="Messages", tickformat=",d", gridcolor=c["grid"]),
# #         showlegend=False, hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_hourly_line(df, theme="light"):
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 260))
# #         return fig
# #     point_colors = [
# #         c["success"] if s >= 0.1 else c["danger"] if s <= -0.1 else c["warning"]
# #         for s in df["avg_score"]
# #     ]
# #     fig = go.Figure()
# #     fig.add_trace(go.Scatter(
# #         x=df["hour"], y=df["avg_score"], mode="lines+markers",
# #         line=dict(color=BLUE, width=2.5, shape="spline"),
# #         marker=dict(size=7, color=point_colors, line=dict(color="white", width=1.5)),
# #         fill="tozeroy", fillcolor="rgba(0,48,135,0.06)",
# #         hovertemplate="%{x}h → %{y:.3f}<extra></extra>",
# #     ))
# #     fig.add_hline(y=0, line_dash="dot", line_color=c["neutral"], opacity=0.35)
# #     layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
# #     layout.update(
# #         xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1,range=[0, 23], gridcolor=c["grid"]),
# #         yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False, gridcolor=c["grid"]),
# #         showlegend=False, hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_weekly_table(df_weekly, theme="light"):
# #     c = _colors(theme)
# #     if df_weekly.empty:
# #         return html.Div("Aucune donnée",
# #                         style={"textAlign": "center", "padding": "40px", "color": c["neutral"]})
# #     rows = []
# #     for _, row in df_weekly.iterrows():
# #         s         = row["avg_score"]
# #         score_cls = "score-pos" if s >= 0.1 else "score-neg" if s <= -0.1 else "score-neu"
# #         rows.append(html.Tr([
# #             html.Td(html.Span(row["week"], className="at-week-badge")),
# #             html.Td(f"{s:+.3f}", className=f"at-score-cell {score_cls}",
# #                     style={"textAlign": "right"}),
# #             html.Td(f"{row['neg_pct']:.1f}%",
# #                     style={"textAlign": "right", "color": RED, "fontSize": "11px"}),
# #             html.Td(f"{row['total']:,}",
# #                     style={"textAlign": "right", "color": c["text"], "fontSize": "11px"}),
# #         ]))
# #     return html.Div(
# #         html.Table([
# #             html.Thead(html.Tr([
# #                 html.Th("Période"),
# #                 html.Th("Score moy.", style={"textAlign": "right"}),
# #                 html.Th("Taux nég.",  style={"textAlign": "right"}),
# #                 html.Th("Volume",     style={"textAlign": "right"}),
# #             ])),
# #             html.Tbody(rows),
# #         ]),
# #         className="at-table-wrap",
# #     )


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 6. COMPOSANTS ÉVÉNEMENTS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def make_impact_native(events_impact):
# #     if not events_impact:
# #         return html.Div(
# #             html.Div([
# #                 html.I(className="fas fa-magnifying-glass-chart",
# #                        style={"fontSize": "28px", "color": NEUTRAL, "marginBottom": "10px"}),
# #                 html.Div("Aucune anomalie détectée sur cette période",
# #                          style={"fontSize": "12px", "color": NEUTRAL}),
# #             ], style={"textAlign": "center", "padding": "30px"}),
# #         )
# #     items = []
# #     for e in events_impact:
# #         delta  = e.get("delta")
# #         impact = e.get("impact_type", "neutre")
# #         color  = GREEN if impact == "positif" else RED if impact == "negatif" else ORANGE
# #         bg     = GREEN_BG if impact == "positif" else RED_BG if impact == "negatif" else ORANGE_BG
# #         sign   = "+" if delta and delta > 0 else ""
# #         delta_label = f"{sign}{delta:.3f}" if delta is not None else "N/A"
# #         before = e.get("score_before", 0) or 0
# #         after  = e.get("score_after",  0) or 0
# #         before_pct = int((before + 1) / 2 * 100)
# #         after_pct  = int((after  + 1) / 2 * 100)

# #         items.append(html.Div([
# #             html.Div([
# #                 html.Div([
# #                     html.I(className=e.get("icon", "fas fa-circle"),
# #                            style={"fontSize": "12px", "color": color, "marginRight": "6px"}),
# #                     html.Strong(e["title"], style={"fontSize": "11px", "color": "#0f1e3c"}),
# #                 ]),
# #                 html.Span(delta_label, style={
# #                     "fontSize": "10px", "fontWeight": "800", "color": color,
# #                     "background": bg, "padding": "2px 8px", "borderRadius": "10px",
# #                 }),
# #             ], style={"display": "flex", "justifyContent": "space-between",
# #                       "alignItems": "center", "marginBottom": "8px"}),
# #             html.Div([
# #                 html.Span("Avant", style={"fontSize": "9px", "color": NEUTRAL,
# #                                           "width": "34px", "display": "inline-block"}),
# #                 html.Div(
# #                     html.Div(style={"width": f"{before_pct}%", "height": "7px",
# #                                     "background": NEUTRAL, "opacity": "0.45", "borderRadius": "4px"}),
# #                     style={"flex": "1", "background": "#eef1f8",
# #                            "borderRadius": "4px", "height": "7px", "margin": "0 8px"},
# #                 ),
# #                 html.Span(f"{before:+.2f}", style={"fontSize": "9px", "color": NEUTRAL,
# #                                                     "width": "36px", "textAlign": "right"}),
# #             ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
# #             html.Div([
# #                 html.Span("Après", style={"fontSize": "9px", "color": color,
# #                                           "width": "34px", "display": "inline-block",
# #                                           "fontWeight": "700"}),
# #                 html.Div(
# #                     html.Div(style={"width": f"{after_pct}%", "height": "7px",
# #                                     "background": color, "borderRadius": "4px"}),
# #                     style={"flex": "1", "background": "#eef1f8",
# #                            "borderRadius": "4px", "height": "7px", "margin": "0 8px"},
# #                 ),
# #                 html.Span(f"{after:+.2f}", style={"fontSize": "9px", "color": color,
# #                                                    "width": "36px", "textAlign": "right",
# #                                                    "fontWeight": "700"}),
# #             ], style={"display": "flex", "alignItems": "center"}),
# #         ], className="at-impact-row"))
# #     return html.Div(items)


# # def make_event_list(events_impact):
# #     if not events_impact:
# #         return html.Div(
# #             html.Div([
# #                 html.I(className="fas fa-inbox",
# #                        style={"fontSize": "28px", "color": NEUTRAL, "marginBottom": "10px"}),
# #                 html.Div("Aucune anomalie détectée",
# #                          style={"fontSize": "12px", "color": NEUTRAL}),
# #             ], style={"textAlign": "center", "padding": "30px"}),
# #         )
# #     cards = []
# #     for e in events_impact:
# #         impact  = e.get("impact_type", "neutre")
# #         color   = GREEN if impact == "positif" else RED if impact == "negatif" else ORANGE
# #         bg      = GREEN_BG if impact == "positif" else RED_BG if impact == "negatif" else ORANGE_BG
# #         arrow   = "↑" if impact == "positif" else "↓" if impact == "negatif" else "→"
# #         delta   = e.get("delta")
# #         sign    = "+" if delta and delta > 0 else ""
# #         d_label = f"{sign}{delta:.3f}" if delta is not None else "N/A"
# #         cards.append(html.Div([
# #             html.Div([
# #                 html.Div(
# #                     html.I(className=e.get("icon", "fas fa-circle"),
# #                            style={"fontSize": "14px", "color": color}),
# #                     className="at-event-icon",
# #                     style={"background": "#fff", "border": f"1px solid {color}30"},
# #                 ),
# #                 html.Div([
# #                     html.Div([
# #                         html.Strong(e["title"], style={"fontSize": "11px", "color": "#0f1e3c"}),
# #                         html.Span(f"{arrow} {d_label}", style={
# #                             "fontSize": "10px", "fontWeight": "800", "color": color,
# #                             "background": bg, "padding": "2px 7px", "borderRadius": "8px",
# #                         }),
# #                     ], style={"display": "flex", "justifyContent": "space-between",
# #                                "alignItems": "center"}),
# #                     html.Div(e["description"],
# #                              style={"fontSize": "10px", "color": NEUTRAL, "marginTop": "4px"}),
# #                     html.Div([
# #                         html.I(className="fas fa-calendar-alt",
# #                                style={"fontSize": "9px", "marginRight": "4px", "color": NEUTRAL}),
# #                         html.Small(e["date"], style={"fontSize": "9px", "color": NEUTRAL}),
# #                     ], style={"marginTop": "6px"}),
# #                 ], style={"flex": "1"}),
# #             ], style={"display": "flex", "gap": "10px"}),
# #         ], className="at-event-card", style={"borderLeft": f"3px solid {color}"}))
# #     return html.Div(cards, className="at-events-list")


# # def _chart_card(icon_cls, icon_color, icon_bg, title, tooltip_body, children):
# #     return html.Div([
# #         html.Div([
# #             html.Div(
# #                 html.I(className=icon_cls, style={"fontSize": "13px", "color": icon_color}),
# #                 className="at-card-icon", style={"background": icon_bg},
# #             ),
# #             html.Span(title, className="at-card-title"),
# #             html.Div([
# #                 html.Div(html.I(className="fas fa-circle-info"), className="at-tooltip-trigger"),
# #                 html.Div([
# #                     html.Div(title, className="at-tooltip-title"),
# #                     html.Div(tooltip_body, className="at-tooltip-body"),
# #                 ], className="at-tooltip-box"),
# #             ], className="at-tooltip-wrap"),
# #         ], className="at-card-header"),
# #         html.Div(children, className="at-card-body"),
# #     ], className="at-chart-card")


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 7. BARRE DE FILTRE PÉRIODE
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def make_periode_filter(active_periode="global"):
# #     def _btn_style(is_active):
# #         return style_btn_active if is_active else style_btn_inactive

# #     return html.Div([
# #         html.Div([
# #             html.I(className="fas fa-calendar-alt",
# #                    style={"fontSize": "11px", "marginRight": "6px"}),
# #             html.Span("Période d'analyse :", style={"fontSize": "12px", "fontWeight": "600"}),
# #         ], style={"display": "flex", "alignItems": "center", "color": NEUTRAL, "marginRight": "12px"}),

# #         html.Button(
# #             [html.I(className="fas fa-globe",
# #                     style={"fontSize": "11px", "marginRight": "6px"}), "Global"],
# #             id="btn-periode-analytics-global",
# #             n_clicks=0,
# #             style=_btn_style(active_periode == "global"),
# #         ),
# #         html.Button(
# #             [html.I(className="fas fa-calendar-day",
# #                     style={"fontSize": "11px", "marginRight": "6px"}), "Ce Mois"],
# #             id="btn-periode-analytics-mois",
# #             n_clicks=0,
# #             style=_btn_style(active_periode == "mois"),
# #         ),
# #         html.Button(
# #             [html.I(className="fas fa-calendar-day",
# #                     style={"fontSize": "11px", "marginRight": "6px"}), "Aujourd'hui"],
# #             id="btn-periode-analytics-jour",
# #             n_clicks=0,
# #             style=_btn_style(active_periode == "jour"),
# #         ),
# #     ], style={
# #         "display": "flex", "alignItems": "center", "gap": "10px",
# #         "padding": "12px 16px", "background": "var(--bg-card)",
# #         "borderRadius": "14px", "marginBottom": "20px",
# #         "border": "1px solid var(--border-color)",
# #         "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
# #         "flexWrap": "wrap",
# #     })


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 8. RENDER PRINCIPAL
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def render_analytics_page(theme="light", user_data=None, periode="global"):
# #     print(f"🔍 Analyse Temporelle — Période : {periode}")

# #     if periode == "jour":
# #         df_hourly    = get_hourly_data_jour()
# #         df_weekly, _ = get_weekly_evolution_jour()
# #     elif periode == "mois":
# #         df_hourly    = get_hourly_data_mois()
# #         df_weekly, _ = get_weekly_evolution_mois()
# #     else:
# #         df_hourly    = get_hourly_data_global()
# #         df_weekly, _ = get_weekly_evolution_global()

# #     events_impact = get_real_events_from_mongo(
# #         periode=periode,
# #         top_n=None if periode == "mois" else 5,
# #     )

# #     metrics    = get_temporal_metrics_periode(df_weekly, df_hourly, periode)
# #     nb_h       = len(df_hourly)
# #     nb_w       = len(df_weekly)
# #     total_msgs = metrics.get("total_messages", 0)
# #     mois_label = now_local().strftime("%B %Y")

# #     subtitles = {
# #         "global": f"{nb_h} tranches horaires · {nb_w} semaines · {total_msgs:,} messages (historique complet)",
# #         "mois":   f"{nb_h} tranches horaires · {nb_w} jours · {total_msgs:,} messages ({mois_label})",
# #         "jour": f"{nb_h} tranche(s) horaire(s) · {total_msgs:,} messages (24h — données réelles uniquement)",
# #     }
# #     sub = subtitles.get(periode, "Analyse des pics d'insatisfaction")

# #     sub_with_live = html.Div([
# #         html.Span(sub, style={"marginRight": "12px"}),
# #         html.Span([
# #             html.I(className="fas fa-circle",
# #                    style={"fontSize": "8px", "color": GREEN, "marginRight": "6px"}),
# #             "Données temps réel" if periode == "jour" else "Données historiques",
# #         ], style={
# #             "fontSize": "10px", "fontWeight": "500", "color": NEUTRAL,
# #             "backgroundColor": GREEN_BG, "padding": "2px 8px",
# #             "borderRadius": "20px", "display": "inline-flex", "alignItems": "center",
# #         }),
# #     ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "8px"})

# #     content = html.Div([

# #         make_periode_filter(periode),

# #         make_kpi_cards(metrics),

# #         html.Div([
# #             _chart_card(
# #                 "fas fa-calendar-xmark", BLUE, BLUE_BG,
# #                 "Impact des anomalies détectées",
# #                 "Variation du score de satisfaction autour de chaque période anormale détectée automatiquement.",
# #                 make_impact_native(events_impact),
# #             ),
# #             html.Div([
# #                 html.Div([
# #                     html.Div(
# #                         html.I(className="fas fa-list-ul",
# #                                style={"fontSize": "13px", "color": BLUE}),
# #                         className="at-card-icon", style={"background": BLUE_BG},
# #                     ),
# #                     html.Span("Détail des anomalies", className="at-card-title"),
# #                 ], className="at-card-header"),
# #                 html.Div(make_event_list(events_impact), className="at-card-body"),
# #             ], className="at-chart-card"),
# #         ], className="at-row-2col"),

# #         html.Div([
# #             _chart_card(
# #                 "fas fa-chart-bar", BLUE, GREEN_BG,
# #                 "Répartition des avis par heure",
# #                 "Proportion satisfaits / insatisfaits par tranche horaire.",
# #                 dcc.Graph(
# #                     figure=make_hourly_stacked(df_hourly, theme),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%", "height": "280px"},
# #                 ),
# #             ),
# #             _chart_card(
# #                 "fas fa-inbox", BLUE, BLUE_BG,
# #                 "Volume de messages reçus par heure",
# #                 "Nombre total de messages clients reçus par tranche horaire.",
# #                 dcc.Graph(
# #                     figure=make_volume_bars(df_hourly, theme),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%", "height": "280px"},
# #                 ),
# #             ),
# #         ], className="at-row-equal"),

# #         html.Div([
# #             _chart_card(
# #                 "fas fa-table-list", BLUE, BLUE_BG,
# #                 f"Évolution {'journalière' if periode != 'global' else 'hebdomadaire'}",
# #                 f"Score moyen, taux négatif et volume "
# #                 f"{'jour par jour' if periode != 'global' else 'semaine par semaine'}.",
# #                 make_weekly_table(df_weekly, theme),
# #             ),
# #             _chart_card(
# #                 "fas fa-clock-rotate-left", BLUE, BLUE_BG,
# #                 "Score de satisfaction par heure",
# #                 "Courbe du score moyen de satisfaction heure par heure.",
# #                 dcc.Graph(
# #                     figure=make_hourly_line(df_hourly, theme),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%", "height": "280px"},
# #                 ),
# #             ),
# #         ], className="at-row-equal"),

# #     ], className="at-analytics-page", **{"data-theme": theme})

# #     return make_page_layout(
# #         "analytics", "Analyse Temporelle", sub_with_live, content, theme, user_data
# #     )


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 9. DASH LAYOUT + CALLBACKS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # layout = html.Div(
# #     id="analytics-wrapper",
# #     **{"data-theme": "light"},
# #     children=[
# #         dcc.Store(id="periode-analytics-store", data="global", storage_type="session"),
# #         dcc.Interval(id="refresh-interval-analytics", interval=300_000, n_intervals=0),
# #         html.Div(id="full-analytics-layout"),
# #     ],
# # )


# # @callback(
# #     Output("periode-analytics-store",      "data"),
# #     Output("btn-periode-analytics-global", "style"),
# #     Output("btn-periode-analytics-mois",   "style"),
# #     Output("btn-periode-analytics-jour",   "style"),
# #     Input("btn-periode-analytics-global",  "n_clicks"),
# #     Input("btn-periode-analytics-mois",    "n_clicks"),
# #     Input("btn-periode-analytics-jour",    "n_clicks"),
# #     State("periode-analytics-store",       "data"),
# #     prevent_initial_call=True,
# # )
# # def set_analytics_periode(n_global, n_mois, n_jour, current_periode):
# #     A = style_btn_active
# #     I = style_btn_inactive

# #     ctx = dash.callback_context
# #     if not ctx.triggered:
# #         styles = {
# #             "global": [A, I, I],
# #             "mois":   [I, A, I],
# #             "jour":   [I, I, A],
# #         }
# #         s = styles.get(current_periode or "global", [A, I, I])
# #         return current_periode or "global", s[0], s[1], s[2]

# #     btn = ctx.triggered[0]["prop_id"].split(".")[0]

# #     if btn == "btn-periode-analytics-mois":
# #         return "mois", I, A, I
# #     elif btn == "btn-periode-analytics-jour":
# #         return "jour", I, I, A

# #     return "global", A, I, I


# # @callback(
# #     Output("full-analytics-layout", "children"),
# #     Output("analytics-wrapper",     "data-theme"),
# #     Input("theme-store",             "data"),
# #     Input("auth-store",              "data"),
# #     Input("periode-analytics-store", "data"),
# #     Input("refresh-interval-analytics", "n_intervals"),
# # )
# # def update_analytics_page(theme, auth_data, periode, n_intervals):
# #     theme   = theme   or "light"
# #     periode = periode or "global"
# #     user_data = None
# #     if auth_data and auth_data.get("is_authenticated"):
# #         user_data = auth_data.get("user", {})
# #     return render_analytics_page(theme, user_data, periode), theme

# """
# Page d'Analyse Temporelle — ALGÉRIE TÉLÉCOM
# AVEC FILTRES PÉRIODE (Global / Mois / Jour) — VERSION FINALE CORRIGÉE
# ✅ Événements détectés automatiquement depuis MongoDB
# ✅ Heures UTC+1 (Algérie) correctement gérées
# ✅ Toutes les anomalies du mois affichées
# ✅ FIX : heure 0 (minuit) correctement détectée (bug falsy 0)
# ✅ Barre de filtre : fond blanc, badge date, bouton Actualiser
# """

# import dash
# from dash import html, dcc, callback, Input, Output, State
# import plotly.graph_objects as go
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import statistics
# import sys, os

# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# from components import make_page_layout
# from database import MONGO_AVAILABLE, _col

# dash.register_page(__name__, path='/analytics', name='Analyse Temporelle')

# # ── PALETTE ALGÉRIE TÉLÉCOM ───────────────────────────────────────────────────
# BLUE       = "#003087"
# BLUE_MID   = "#1a4fa0"
# BLUE_LIGHT = "#4a80d4"
# BLUE_BG    = "#e8f0fb"
# GREEN      = "#00a854"
# GREEN_BG   = "#e6f7ef"
# RED        = "#e8384f"
# RED_BG     = "#fde8eb"
# ORANGE     = "#f59e0b"
# ORANGE_BG  = "#fef3cd"
# NEUTRAL    = "#64748b"

# # ── STYLES BOUTONS PÉRIODE (inline) ──────────────────────────────────────────
# style_btn_active = {
#     "padding": "6px 16px",
#     "borderRadius": "20px",
#     "border": "none",
#     "background": BLUE,
#     "color": "white",
#     "cursor": "pointer",
#     "fontSize": "12px",
#     "fontWeight": "500",
#     "transition": "all 0.2s ease",
#     "display": "flex",
#     "alignItems": "center",
#     "gap": "6px",
# }
# style_btn_inactive = {
#     "padding": "6px 16px",
#     "borderRadius": "20px",
#     "border": f"1px solid {BLUE}",
#     "background": "transparent",
#     "color": BLUE,
#     "cursor": "pointer",
#     "fontSize": "12px",
#     "fontWeight": "500",
#     "transition": "all 0.2s ease",
#     "display": "flex",
#     "alignItems": "center",
#     "gap": "6px",
# }

# # ── ICÔNES PAR THÈME D'ANOMALIE ───────────────────────────────────────────────
# _THEME_ICONS = {
#     "reseau":      "fas fa-broadcast-tower",
#     "facturation": "fas fa-file-invoice",
#     "service":     "fas fa-headset",
#     "application": "fas fa-mobile-alt",
#     "offre":       "fas fa-tags",
#     "hors_sujet":  "fas fa-question-circle",
#     "default":     "fas fa-circle-exclamation",
# }


# def _icon_for_theme(theme: str) -> str:
#     if not theme:
#         return _THEME_ICONS["default"]
#     for key in _THEME_ICONS:
#         if key in (theme or "").lower():
#             return _THEME_ICONS[key]
#     return _THEME_ICONS["default"]


# # ── COULEURS PAR THÈME ────────────────────────────────────────────────────────
# def _colors(theme):
#     if theme == "dark":
#         return {
#             "bg": "#141c2e", "paper_bg": "#141c2e", "text": "#dce8f5",
#             "grid": "#1e2d47", "axis_line": "#1e2d47", "primary": "#4a80d4",
#             "secondary": "#6c8dcc", "success": "#2ecc71", "warning": "#f39c12",
#             "danger": "#f06070", "neutral": "#607b99", "card_bg": "#141c2e",
#             "stat_bg": "#1a2236", "border": "#1e2d47",
#         }
#     return {
#         "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
#         "grid": "#e8edf5", "axis_line": "#e8edf5", "primary": BLUE,
#         "secondary": BLUE_MID, "success": GREEN, "warning": ORANGE,
#         "danger": RED, "neutral": NEUTRAL, "card_bg": "#ffffff",
#         "stat_bg": "#f8fafd", "border": "rgba(0,48,135,0.10)",
#     }


# def _base_layout(c, height, margin=None):
#     m = margin or dict(l=10, r=10, t=20, b=10)
#     return dict(
#         plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
#         font=dict(color=c["text"], family="'Inter', 'DM Sans', sans-serif", size=10),
#         height=height, margin=m,
#     )


# def now_local():
#     """Heure locale Algérie (UTC+1)."""
#     return datetime.utcnow() + timedelta(hours=1)


# # ── HELPERS ────────────────────────────────────────────────────────────────────

# def _hour_has_data(hour_dict):
#     return hour_dict is not None and hour_dict.get("hour") is not None

# def _score_has_data(hour_dict):
#     return hour_dict is not None and hour_dict.get("score") is not None

# def _fmt_hour(hour_dict):
#     if not _hour_has_data(hour_dict):
#         return "--:00"
#     return f"{hour_dict['hour']:02d}:00"


# # ═══════════════════════════════════════════════════════════════════════════════
# # 1. FONCTIONS DE DONNÉES PAR PÉRIODE
# # ═══════════════════════════════════════════════════════════════════════════════

# def get_hourly_data_global():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         pipeline = [
#             {"$match": {
#                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
#                 "heure": {"$exists": True, "$ne": None},
#             }},
#             {"$group": {
#                 "_id": "$heure",
#                 "total": {"$sum": 1},
#                 "sentiment_sum": {"$sum": "$sentiment_score"},
#                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#                 "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         data = []
#         for r in results:
#             total = r["total"]
#             if total > 0:
#                 data.append({
#                     "hour": r["_id"],
#                     "avg_score": round(r["sentiment_sum"] / total, 3),
#                     "neg_pct": round(r["negatifs"] / total * 100, 1),
#                     "pos_pct": round(r["positifs"] / total * 100, 1),
#                     "total": total,
#                 })
#         return pd.DataFrame(data)
#     except Exception as e:
#         print(f"Erreur get_hourly_data_global: {e}")
#         return pd.DataFrame()


# def get_weekly_evolution_global():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame(), []
#     try:
#         pipeline = [
#             {"$match": {
#                 "annee_semaine": {"$exists": True, "$ne": None},
#                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
#             }},
#             {"$group": {
#                 "_id": "$annee_semaine",
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total": {"$sum": 1},
#                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame(), []
#         df = pd.DataFrame([{
#             "week": r["_id"],
#             "avg_score": round(r["avg_score"], 3),
#             "total": r["total"],
#             "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
#         } for r in results])
#         if len(df) > 15:
#             df = df.tail(15)
#         peaks = []
#         if len(df) > 3:
#             mean_score = df["avg_score"].mean()
#             std_score  = df["avg_score"].std()
#             for _, row in df.iterrows():
#                 if row["avg_score"] < mean_score - 1.5 * std_score:
#                     peaks.append({"week": row["week"], "score": row["avg_score"]})
#         return df, peaks
#     except Exception as e:
#         print(f"Erreur get_weekly_evolution_global: {e}")
#         return pd.DataFrame(), []


# def _mois_bornes():
#     now   = now_local()
#     debut = datetime(now.year, now.month, 1) - timedelta(hours=1)
#     fin   = datetime(now.year + 1, 1, 1) - timedelta(hours=1) if now.month == 12 \
#             else datetime(now.year, now.month + 1, 1) - timedelta(hours=1)
#     return debut, fin


# def get_hourly_data_mois():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         debut, fin = _mois_bornes()
#         mois_str   = now_local().strftime("%Y-%m")
#         match_filter = {
#             "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
#             "$or": [
#                 {"mois": mois_str},
#                 {"date_originale": {"$gte": debut, "$lt": fin}},
#                 {"date_annotation": {"$gte": debut, "$lt": fin}},
#             ],
#         }
#         pipeline = [
#             {"$match": match_filter},
#             {"$addFields": {"_date_src": {"$cond": {
#                 "if": {"$eq": [{"$type": "$date_originale"}, "date"]},
#                 "then": "$date_originale",
#                 "else": {"$cond": {
#                     "if": {"$eq": [{"$type": "$date_annotation"}, "date"]},
#                     "then": "$date_annotation", "else": None,
#                 }},
#             }}}},
#             {"$addFields": {"_heure_calc": {"$cond": {
#                 "if": {"$and": [
#                     {"$ne": ["$heure", None]},
#                     {"$ne": [{"$type": "$heure"}, "missing"]},
#                 ]},
#                 "then": "$heure",
#                 "else": {"$cond": {
#                     "if": {"$ne": ["$_date_src", None]},
#                     "then": {"$hour": {"$add": ["$_date_src", 3600000]}},
#                     "else": None,
#                 }},
#             }}}},
#             {"$match": {"_heure_calc": {"$ne": None}}},
#             {"$group": {
#                 "_id": "$_heure_calc",
#                 "total": {"$sum": 1},
#                 "sentiment_sum": {"$sum": "$sentiment_score"},
#                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#                 "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         data = []
#         for r in results:
#             total = r["total"]
#             if total > 0:
#                 data.append({
#                     "hour": r["_id"],
#                     "avg_score": round(r["sentiment_sum"] / total, 3),
#                     "neg_pct": round(r["negatifs"] / total * 100, 1),
#                     "pos_pct": round(r["positifs"] / total * 100, 1),
#                     "total": total,
#                 })
#         return pd.DataFrame(data)
#     except Exception as e:
#         print(f"Erreur get_hourly_data_mois: {e}")
#         return pd.DataFrame()


# def get_weekly_evolution_mois():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame(), []
#     try:
#         debut, fin = _mois_bornes()
#         mois_str   = now_local().strftime("%Y-%m")
#         match_filter = {
#             "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
#             "$or": [
#                 {"mois": mois_str},
#                 {"date_clean": {"$gte": debut, "$lt": fin}},
#                 {"date_annotation": {"$gte": debut, "$lt": fin}},
#             ],
#         }
#         pipeline = [
#             {"$match": match_filter},
#             {"$addFields": {
#                 "_jour": {
#                     "$cond": {
#                         "if": {"$eq": [{"$type": "$date_clean"}, "date"]},
#                         "then": {
#                             "$dateToString": {
#                                 "format": "%Y-%m-%d",
#                                 "date": "$date_clean",
#                             }
#                         },
#                         "else": None,
#                     }
#                 }
#             }},
#             {"$match": {"_jour": {"$ne": None}}},
#             {"$group": {
#                 "_id": "$_jour",
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total": {"$sum": 1},
#                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame(), []
#         df = pd.DataFrame([{
#             "week": r["_id"],
#             "avg_score": round(r["avg_score"], 3),
#             "total": r["total"],
#             "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
#         } for r in results])
#         peaks = []
#         if len(df) > 2:
#             mean_score = df["avg_score"].mean()
#             std_score  = df["avg_score"].std()
#             for _, row in df.iterrows():
#                 if row["avg_score"] < mean_score - 1.5 * std_score:
#                     peaks.append({"week": row["week"], "score": row["avg_score"]})
#         return df, peaks
#     except Exception as e:
#         print(f"Erreur get_weekly_evolution_mois: {e}")
#         return pd.DataFrame(), []


# def get_hourly_data_jour():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         now = now_local()
#         debut_jour = datetime(now.year, now.month, now.day, 0, 0, 0)
#         fin_jour   = datetime(now.year, now.month, now.day, 23, 59, 59)
#         pipeline = [
#             {"$match": {
#                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
#                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
#             }},
#             {"$group": {
#                 "_id": "$heure",
#                 "total": {"$sum": 1},
#                 "sentiment_sum": {"$sum": "$sentiment_score"},
#                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#                 "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         data = []
#         for r in results:
#             total = r["total"]
#             if total > 0 and r["_id"] is not None:
#                 data.append({
#                     "hour": r["_id"],
#                     "avg_score": round(r["sentiment_sum"] / total, 3),
#                     "neg_pct": round(r["negatifs"] / total * 100, 1),
#                     "pos_pct": round(r["positifs"] / total * 100, 1),
#                     "total": total,
#                 })
#         return pd.DataFrame(data)
#     except Exception as e:
#         print(f"Erreur get_hourly_data_jour: {e}")
#         return pd.DataFrame()


# def get_weekly_evolution_jour():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame(), []
#     try:
#         now = now_local()
#         sept_jours = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=6)
#         pipeline = [
#             {"$match": {
#                 "date_clean": {"$gte": sept_jours},
#                 "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
#             }},
#             {"$addFields": {
#                 "jour_str": {
#                     "$dateToString": {
#                         "format": "%Y-%m-%d",
#                         "date": "$date_clean",
#                     }
#                 }
#             }},
#             {"$group": {
#                 "_id": "$jour_str",
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total": {"$sum": 1},
#                 "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame(), []
#         df = pd.DataFrame([{
#             "week": r["_id"],
#             "avg_score": round(r["avg_score"], 3),
#             "total": r["total"],
#             "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
#         } for r in results])
#         peaks = []
#         if len(df) > 2:
#             mean_score = df["avg_score"].mean()
#             std_score  = df["avg_score"].std()
#             for _, row in df.iterrows():
#                 if row["avg_score"] < mean_score - 1.5 * std_score:
#                     peaks.append({"week": row["week"], "score": row["avg_score"]})
#         return df, peaks
#     except Exception as e:
#         print(f"Erreur get_weekly_evolution_jour: {e}")
#         return pd.DataFrame(), []


# def get_temporal_metrics_periode(df_weekly, df_hourly, periode="global"):
#     metrics = {"periode": periode, "total_messages": 0}
#     if not df_hourly.empty:
#         metrics["total_messages"] = int(df_hourly["total"].sum())
#         if not df_hourly["avg_score"].isnull().all():
#             worst_h = df_hourly.loc[df_hourly["avg_score"].idxmin()]
#             best_h  = df_hourly.loc[df_hourly["avg_score"].idxmax()]
#             metrics["worst_hour"] = {
#                 "hour": int(worst_h["hour"]),
#                 "score": float(worst_h["avg_score"]),
#             }
#             metrics["best_hour"] = {
#                 "hour": int(best_h["hour"]),
#                 "score": float(best_h["avg_score"]),
#             }
#     if not df_weekly.empty:
#         worst = df_weekly.loc[df_weekly["avg_score"].idxmin()]
#         best  = df_weekly.loc[df_weekly["avg_score"].idxmax()]
#         metrics["worst_week"] = {"week": worst["week"], "score": float(worst["avg_score"])}
#         metrics["best_week"]  = {"week": best["week"],  "score": float(best["avg_score"])}
#         if len(df_weekly) > 1:
#             slope = np.polyfit(np.arange(len(df_weekly)), df_weekly["avg_score"].values, 1)[0]
#             metrics["trend"]       = "positive" if slope > 0.01 else "negative" if slope < -0.01 else "stable"
#             metrics["trend_value"] = round(slope, 4)
#         else:
#             metrics["trend"]       = "stable"
#             metrics["trend_value"] = 0.0
#     elif not df_hourly.empty:
#         if len(df_hourly) > 1 and not df_hourly["avg_score"].isnull().all():
#             slope = np.polyfit(np.arange(len(df_hourly)), df_hourly["avg_score"].values, 1)[0]
#             metrics["trend"]       = "positive" if slope > 0.005 else "negative" if slope < -0.005 else "stable"
#             metrics["trend_value"] = round(slope, 4)
#         else:
#             metrics["trend"]       = "stable"
#             metrics["trend_value"] = 0.0
#     return metrics


# # ═══════════════════════════════════════════════════════════════════════════════
# # 2. DÉTECTION RÉELLE DES ANOMALIES DEPUIS MONGODB
# # ═══════════════════════════════════════════════════════════════════════════════

# def get_real_events_from_mongo(periode: str = "global", top_n: int = None):
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         match_base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
#         add_fields_stage = None
#         label_prefix     = "Semaine"

#         if periode == "jour":
#             cutoff_utc = now_local() - timedelta(hours=24) - timedelta(hours=1)
#             match_base["date_clean"] = {"$gte": cutoff_utc}
#             label_prefix = "Heure"
#             add_fields_stage = {"$addFields": {"jour_str": {
#                 "$dateToString": {
#                     "format": "%Y-%m-%d %H:00",
#                     "date": {"$add": ["$date_clean", 3600000]},
#                 }
#             }}}
#             group_by = "$jour_str"

#         elif periode == "mois":
#             debut, fin = _mois_bornes()
#             mois_str   = now_local().strftime("%Y-%m")
#             match_base["$or"] = [
#                 {"annee_mois": mois_str},
#                 {"date_clean": {"$gte": debut, "$lt": fin}},
#                 {"date_annotation": {"$gte": debut, "$lt": fin}},
#             ]
#             label_prefix = "Journée"
#             group_by     = {"$dateToString": {"format": "%Y-%m-%d", "date": "$date_clean"}}

#         else:
#             label_prefix = "Semaine"
#             group_by     = "$annee_semaine"

#         pipeline = [{"$match": match_base}]
#         if add_fields_stage:
#             pipeline.append(add_fields_stage)
#             pipeline.append({"$match": {"jour_str": {"$ne": None}}})

#         pipeline += [
#             {"$group": {
#                 "_id": group_by,
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total":     {"$sum": 1},
#                 "negatifs":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#                 "positifs":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
#                 "themes":    {"$push": "$theme_pred"},
#                 "sources":   {"$push": "$source"},
#             }},
#             {"$match": {"_id": {"$ne": None}}},
#             {"$sort": {"_id": 1}},
#         ]

#         results = list(_col.aggregate(pipeline))
#         if not results or len(results) < 2:
#             return []

#         scores = [r["avg_score"] for r in results if r.get("avg_score") is not None]
#         if len(scores) < 2:
#             return []

#         mean_score = statistics.mean(scores)
#         std_score  = statistics.stdev(scores) if len(scores) > 1 else 1.0
#         if std_score == 0:
#             std_score = 1.0

#         anomalies = []
#         for i, r in enumerate(results):
#             s       = r.get("avg_score") or 0
#             total   = r.get("total") or 1
#             neg_pct = round(r.get("negatifs", 0) / total * 100, 1)
#             z_score = (s - mean_score) / std_score

#             if z_score < -0.8 or neg_pct > 65:
#                 score_before  = round(results[i - 1].get("avg_score") or mean_score, 3) if i > 0 else round(mean_score, 3)
#                 score_after   = round(s, 3)
#                 delta         = round(score_after - score_before, 3)

#                 themes_list     = [t for t in (r.get("themes") or []) if t]
#                 theme_dominant  = max(set(themes_list), key=themes_list.count) if themes_list else "autre"
#                 sources_list    = [s2 for s2 in (r.get("sources") or []) if s2]
#                 source_dominant = max(set(sources_list), key=sources_list.count) if sources_list else "Inconnue"
#                 period_id = r["_id"]

#                 if periode == "jour":
#                     try:
#                         heure_str = str(period_id).split(" ")[-1]
#                         period_label = heure_str
#                     except Exception:
#                         period_label = str(period_id)
#                 elif periode == "mois":
#                     try:
#                         dt = datetime.strptime(str(period_id), "%Y-%m-%d")
#                         mois_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
#                                    "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
#                         period_label = f"{dt.day} {mois_fr[dt.month - 1]} {dt.year}"
#                     except Exception:
#                         period_label = str(period_id)
#                 else:
#                     period_label = str(period_id)

#                 severity = abs(z_score)
#                 if severity > 2:
#                     title_prefix = "⚠️ Pic critique"
#                 elif severity > 1.5:
#                     title_prefix = "Forte dégradation"
#                 else:
#                     title_prefix = "Dégradation détectée"

#                 anomalies.append({
#                     "id":           f"auto_{period_id}",
#                     "date":         str(period_id),
#                     "title":        f"{title_prefix} — {label_prefix} {period_label}",
#                     "description":  (
#                         f"{neg_pct:.0f}% d'avis négatifs · {total:,} messages · "
#                         f"Score moyen : {score_after:+.3f} · Source : {source_dominant}"
#                     ),
#                     "impact":       "negatif",
#                     "source":       f"Détection automatique ({source_dominant})",
#                     "icon":         _icon_for_theme(theme_dominant),
#                     "score_before": score_before,
#                     "score_after":  score_after,
#                     "delta":        delta,
#                     "impact_type":  "negatif" if delta < -0.05 else ("positif" if delta > 0.05 else "neutre"),
#                     "_z_score":     round(z_score, 2),
#                     "_neg_pct":     neg_pct,
#                 })

#         anomalies.sort(key=lambda x: x["_z_score"])
#         if periode == "mois":
#             return anomalies
#         return anomalies[:top_n] if top_n else anomalies[:5]

#     except Exception as e:
#         print(f"Erreur get_real_events_from_mongo: {e}")
#         return []


# # ═══════════════════════════════════════════════════════════════════════════════
# # 3. COMPOSANTS SVG RING
# # ═══════════════════════════════════════════════════════════════════════════════

# def make_score_ring(score, color, size=65):
#     if score is None:
#         score = 0
#     pct         = max(0, min(100, int((score + 1) / 2 * 100)))
#     score_label = f"{score:+.2f}"
#     fig = go.Figure()
#     fig.add_trace(go.Pie(
#         values=[pct, 100 - pct], hole=0.7,
#         marker_colors=[color, "#e8edf5"],
#         textinfo='none', hoverinfo='none', showlegend=False,
#         sort=False, direction="clockwise", rotation=90,
#     ))
#     fig.add_annotation(
#         text=score_label, x=0.5, y=0.5, showarrow=False,
#         font=dict(size=10, color=color), xanchor="center", yanchor="middle",
#     )
#     fig.update_layout(
#         width=size, height=size, margin=dict(l=0, r=0, t=0, b=0),
#         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
#     )
#     return html.Div(
#         dcc.Graph(figure=fig, config={'displayModeBar': False}),
#         style={"flexShrink": "0", "width": f"{size}px", "height": f"{size}px"},
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# # 4. KPI CARDS
# # ═══════════════════════════════════════════════════════════════════════════════

# def make_kpi_cards(metrics):
#     if not metrics or metrics.get("total_messages", 0) == 0:
#         return html.Div(
#             html.Div([
#                 html.I(className="fas fa-chart-line", style={"fontSize": "24px", "color": NEUTRAL}),
#                 html.H4("Aucune donnée", style={"marginTop": "12px", "color": NEUTRAL}),
#                 html.P("Sélectionnez une période avec des données disponibles",
#                        style={"fontSize": "12px", "color": NEUTRAL}),
#             ], style={"textAlign": "center", "padding": "40px"}),
#             className="at-kpi-grid",
#         )

#     worst_week = metrics.get("worst_week", {})
#     best_week  = metrics.get("best_week", {})
#     worst_hour = metrics.get("worst_hour", {})
#     best_hour  = metrics.get("best_hour", {})
#     trend_dir  = metrics.get("trend", "stable")
#     trend_val  = metrics.get("trend_value", 0)
#     periode    = metrics.get("periode", "global")
#     total_msgs = metrics.get("total_messages", 0)

#     if trend_dir == "positive":
#         t_color, t_icon, t_label = GREEN, "fas fa-arrow-trend-up", "Amélioration"
#         t_delta = f"+{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"
#     elif trend_dir == "negative":
#         t_color, t_icon, t_label = RED, "fas fa-arrow-trend-down", "Dégradation"
#         t_delta = f"{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"
#     else:
#         t_color, t_icon, t_label = ORANGE, "fas fa-minus", "Stable"
#         t_delta = f"{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"

#     def _card(accent, icon_cls, icon_bg, icon_color, label, value_el, ring_el=None, extra_cls=""):
#         return html.Div([
#             html.Div([
#                 html.Div(
#                     html.I(className=icon_cls, style={"fontSize": "14px", "color": icon_color}),
#                     className="at-kpi-icon", style={"background": icon_bg},
#                 ),
#                 html.Span(label, className="at-kpi-label"),
#             ], className="at-kpi-title-row"),
#             html.Div([value_el, ring_el or html.Span()], className="at-kpi-value-row"),
#         ], className=f"at-kpi-card {extra_cls}", style={"--kpi-accent": accent})

#     trend_card = html.Div([
#         html.Div([
#             html.Div(
#                 html.I(className=t_icon, style={"fontSize": "20px", "color": "white"}),
#                 className="at-kpi-icon", style={"background": "rgba(255,255,255,0.2)"},
#             ),
#             html.Span("Tendance générale", className="at-kpi-label",
#                       style={"color": "rgba(255,255,255,0.7)"}),
#         ], className="at-kpi-title-row"),
#         html.Div([html.Div([
#             html.Div(f"{total_msgs:,} messages",
#                      style={"color": "white", "fontSize": "14px", "fontWeight": "bold", "marginTop": "5px"}),
#             html.Div(t_label, style={"color": "white", "fontSize": "13px", "marginTop": "8px"}),
#             html.Div(t_delta,  style={"color": "rgba(255,255,255,0.7)", "fontSize": "11px", "marginTop": "4px"}),
#         ], className="at-trend-body")], className="at-kpi-value-row"),
#     ], className="at-kpi-card trend", style={"background": BLUE, "border": "none"})

#     if periode == "jour":
#         worst_day = worst_week
#         best_day  = best_week

#         def _fmt_day(day_str):
#             if not day_str:
#                 return "N/A"
#             try:
#                 dt = datetime.strptime(str(day_str), "%Y-%m-%d")
#                 mois_fr = ["Jan","Fév","Mar","Avr","Mai","Juin",
#                            "Juil","Aoû","Sep","Oct","Nov","Déc"]
#                 return f"{dt.day} {mois_fr[dt.month - 1]}"
#             except Exception:
#                 return str(day_str)

#         cards = [
#             _card(RED, "fas fa-circle-exclamation", "rgba(232,56,79,0.10)", RED,
#                   "Heure critique (24h)",
#                   html.Div(_fmt_hour(worst_hour), className="at-kpi-value"),
#                   make_score_ring(worst_hour.get("score", 0), RED) if _score_has_data(worst_hour) else None),
#             _card(GREEN, "fas fa-circle-check", "rgba(0,168,84,0.10)", GREEN,
#                   "Heure favorable (24h)",
#                   html.Div(_fmt_hour(best_hour), className="at-kpi-value"),
#                   make_score_ring(best_hour.get("score", 0), GREEN) if _score_has_data(best_hour) else None),
#             _card(RED, "fas fa-calendar-xmark", "rgba(232,56,79,0.10)", RED,
#                   "Jour difficile (7j)",
#                   html.Div(_fmt_day(worst_day.get("week") if worst_day else None), className="at-kpi-value"),
#                   make_score_ring(worst_day.get("score", 0), RED) if _score_has_data(worst_day) else None),
#             _card(GREEN, "fas fa-calendar-check", "rgba(0,168,84,0.10)", GREEN,
#                   "Meilleur jour (7j)",
#                   html.Div(_fmt_day(best_day.get("week") if best_day else None), className="at-kpi-value"),
#                   make_score_ring(best_day.get("score", 0), GREEN) if _score_has_data(best_day) else None),
#             trend_card,
#         ]
#         return html.Div(cards, className="at-kpi-grid")

#     week_labels     = {"global": "Semaine difficile", "mois": "Jour difficile"}
#     week_labels_pos = {"global": "Semaine positive",  "mois": "Meilleur jour"}
#     hour_labels     = {"global": "Heure critique",    "mois": "Heure critique (mois)"}
#     hour_labels_pos = {"global": "Heure favorable",   "mois": "Heure favorable (mois)"}

#     cards = [
#         _card(RED, "fas fa-circle-exclamation", "rgba(232,56,79,0.10)", RED,
#               week_labels.get(periode, "Semaine difficile"),
#               html.Div(str(worst_week.get("week", "N/A")) if worst_week else "N/A", className="at-kpi-value"),
#               make_score_ring(worst_week.get("score", 0), RED) if _score_has_data(worst_week) else None),
#         _card(GREEN, "fas fa-circle-check", "rgba(0,168,84,0.10)", GREEN,
#               week_labels_pos.get(periode, "Semaine positive"),
#               html.Div(str(best_week.get("week", "N/A")) if best_week else "N/A", className="at-kpi-value"),
#               make_score_ring(best_week.get("score", 0), GREEN) if _score_has_data(best_week) else None),
#         _card(ORANGE, "fas fa-clock", "rgba(245,158,11,0.10)", ORANGE,
#               hour_labels.get(periode, "Heure critique"),
#               html.Div(_fmt_hour(worst_hour), className="at-kpi-value"),
#               make_score_ring(worst_hour.get("score", 0), ORANGE) if _score_has_data(worst_hour) else None),
#         _card(GREEN, "fas fa-sun", "rgba(0,168,84,0.10)", GREEN,
#               hour_labels_pos.get(periode, "Heure favorable"),
#               html.Div(_fmt_hour(best_hour), className="at-kpi-value"),
#               make_score_ring(best_hour.get("score", 0), GREEN) if _score_has_data(best_hour) else None),
#         trend_card,
#     ]
#     return html.Div(cards, className="at-kpi-grid")


# # ═══════════════════════════════════════════════════════════════════════════════
# # 5. GRAPHIQUES PLOTLY
# # ═══════════════════════════════════════════════════════════════════════════════

# def make_hourly_stacked(df, theme="light"):
#     c = _colors(theme)
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
#                            font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 260))
#         return fig
#     fig = go.Figure()
#     fig.add_trace(go.Bar(
#         x=df["hour"], y=df["pos_pct"], name="Satisfaits",
#         marker=dict(color=c["success"], cornerradius=5),
#         text=[f"{p:.0f}%" for p in df["pos_pct"]], textposition="inside",
#         textfont=dict(size=9, color="white"),
#         hovertemplate="%{x}h — Satisfaits: %{y:.1f}%<extra></extra>",
#     ))
#     fig.add_trace(go.Bar(
#         x=df["hour"], y=df["neg_pct"], name="Insatisfaits",
#         marker=dict(color=c["danger"], cornerradius=5),
#         text=[f"{n:.0f}%" for n in df["neg_pct"]], textposition="inside",
#         textfont=dict(size=9, color="white"),
#         hovertemplate="%{x}h — Insatisfaits: %{y:.1f}%<extra></extra>",
#     ))
#     layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
#     layout.update(
#         xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1, range=[0, 23], gridcolor=c["grid"]),
#         yaxis=dict(title="%", range=[0, 100], ticksuffix="%", gridcolor=c["grid"]),
#         barmode="stack",
#         legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"),
#         hovermode="x unified",
#     )
#     fig.update_layout(**layout)
#     return fig


# def make_volume_bars(df, theme="light"):
#     c = _colors(theme)
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
#                            font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 260))
#         return fig
#     max_v      = df["total"].max() if not df.empty else 1
#     bar_colors = [f"rgba(0,48,135,{0.45 + 0.55 * v / max_v:.2f})" for v in df["total"]]
#     fig = go.Figure()
#     fig.add_trace(go.Bar(
#         x=df["hour"], y=df["total"],
#         marker=dict(color=bar_colors, cornerradius=6),
#         text=[f"{v:,}" for v in df["total"]], textposition="outside",
#         textfont=dict(size=8, color=c["text"]),
#         hovertemplate="%{x}h — %{y:,} messages<extra></extra>",
#     ))
#     layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
#     layout.update(
#         xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1, range=[0, 23], gridcolor=c["grid"]),
#         yaxis=dict(title="Messages", tickformat=",d", gridcolor=c["grid"]),
#         showlegend=False, hovermode="x unified",
#     )
#     fig.update_layout(**layout)
#     return fig


# def make_hourly_line(df, theme="light"):
#     c = _colors(theme)
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
#                            font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 260))
#         return fig
#     point_colors = [
#         c["success"] if s >= 0.1 else c["danger"] if s <= -0.1 else c["warning"]
#         for s in df["avg_score"]
#     ]
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=df["hour"], y=df["avg_score"], mode="lines+markers",
#         line=dict(color=BLUE, width=2.5, shape="spline"),
#         marker=dict(size=7, color=point_colors, line=dict(color="white", width=1.5)),
#         fill="tozeroy", fillcolor="rgba(0,48,135,0.06)",
#         hovertemplate="%{x}h → %{y:.3f}<extra></extra>",
#     ))
#     fig.add_hline(y=0, line_dash="dot", line_color=c["neutral"], opacity=0.35)
#     layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
#     layout.update(
#         xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1, range=[0, 23], gridcolor=c["grid"]),
#         yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False, gridcolor=c["grid"]),
#         showlegend=False, hovermode="x unified",
#     )
#     fig.update_layout(**layout)
#     return fig


# def make_weekly_table(df_weekly, theme="light"):
#     c = _colors(theme)
#     if df_weekly.empty:
#         return html.Div("Aucune donnée",
#                         style={"textAlign": "center", "padding": "40px", "color": c["neutral"]})
#     rows = []
#     for _, row in df_weekly.iterrows():
#         s         = row["avg_score"]
#         score_cls = "score-pos" if s >= 0.1 else "score-neg" if s <= -0.1 else "score-neu"
#         rows.append(html.Tr([
#             html.Td(html.Span(row["week"], className="at-week-badge")),
#             html.Td(f"{s:+.3f}", className=f"at-score-cell {score_cls}",
#                     style={"textAlign": "right"}),
#             html.Td(f"{row['neg_pct']:.1f}%",
#                     style={"textAlign": "right", "color": RED, "fontSize": "11px"}),
#             html.Td(f"{row['total']:,}",
#                     style={"textAlign": "right", "color": c["text"], "fontSize": "11px"}),
#         ]))
#     return html.Div(
#         html.Table([
#             html.Thead(html.Tr([
#                 html.Th("Période"),
#                 html.Th("Score moy.", style={"textAlign": "right"}),
#                 html.Th("Taux nég.",  style={"textAlign": "right"}),
#                 html.Th("Volume",     style={"textAlign": "right"}),
#             ])),
#             html.Tbody(rows),
#         ]),
#         className="at-table-wrap",
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# # 6. COMPOSANTS ÉVÉNEMENTS
# # ═══════════════════════════════════════════════════════════════════════════════

# def make_impact_native(events_impact):
#     if not events_impact:
#         return html.Div(
#             html.Div([
#                 html.I(className="fas fa-magnifying-glass-chart",
#                        style={"fontSize": "28px", "color": NEUTRAL, "marginBottom": "10px"}),
#                 html.Div("Aucune anomalie détectée sur cette période",
#                          style={"fontSize": "12px", "color": NEUTRAL}),
#             ], style={"textAlign": "center", "padding": "30px"}),
#         )
#     items = []
#     for e in events_impact:
#         delta  = e.get("delta")
#         impact = e.get("impact_type", "neutre")
#         color  = GREEN if impact == "positif" else RED if impact == "negatif" else ORANGE
#         bg     = GREEN_BG if impact == "positif" else RED_BG if impact == "negatif" else ORANGE_BG
#         sign   = "+" if delta and delta > 0 else ""
#         delta_label = f"{sign}{delta:.3f}" if delta is not None else "N/A"
#         before = e.get("score_before", 0) or 0
#         after  = e.get("score_after",  0) or 0
#         before_pct = int((before + 1) / 2 * 100)
#         after_pct  = int((after  + 1) / 2 * 100)

#         items.append(html.Div([
#             html.Div([
#                 html.Div([
#                     html.I(className=e.get("icon", "fas fa-circle"),
#                            style={"fontSize": "12px", "color": color, "marginRight": "6px"}),
#                     html.Strong(e["title"], style={"fontSize": "11px", "color": "#0f1e3c"}),
#                 ]),
#                 html.Span(delta_label, style={
#                     "fontSize": "10px", "fontWeight": "800", "color": color,
#                     "background": bg, "padding": "2px 8px", "borderRadius": "10px",
#                 }),
#             ], style={"display": "flex", "justifyContent": "space-between",
#                       "alignItems": "center", "marginBottom": "8px"}),
#             html.Div([
#                 html.Span("Avant", style={"fontSize": "9px", "color": NEUTRAL,
#                                           "width": "34px", "display": "inline-block"}),
#                 html.Div(
#                     html.Div(style={"width": f"{before_pct}%", "height": "7px",
#                                     "background": NEUTRAL, "opacity": "0.45", "borderRadius": "4px"}),
#                     style={"flex": "1", "background": "#eef1f8",
#                            "borderRadius": "4px", "height": "7px", "margin": "0 8px"},
#                 ),
#                 html.Span(f"{before:+.2f}", style={"fontSize": "9px", "color": NEUTRAL,
#                                                     "width": "36px", "textAlign": "right"}),
#             ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
#             html.Div([
#                 html.Span("Après", style={"fontSize": "9px", "color": color,
#                                           "width": "34px", "display": "inline-block",
#                                           "fontWeight": "700"}),
#                 html.Div(
#                     html.Div(style={"width": f"{after_pct}%", "height": "7px",
#                                     "background": color, "borderRadius": "4px"}),
#                     style={"flex": "1", "background": "#eef1f8",
#                            "borderRadius": "4px", "height": "7px", "margin": "0 8px"},
#                 ),
#                 html.Span(f"{after:+.2f}", style={"fontSize": "9px", "color": color,
#                                                    "width": "36px", "textAlign": "right",
#                                                    "fontWeight": "700"}),
#             ], style={"display": "flex", "alignItems": "center"}),
#         ], className="at-impact-row"))
#     return html.Div(items)


# def make_event_list(events_impact):
#     if not events_impact:
#         return html.Div(
#             html.Div([
#                 html.I(className="fas fa-inbox",
#                        style={"fontSize": "28px", "color": NEUTRAL, "marginBottom": "10px"}),
#                 html.Div("Aucune anomalie détectée",
#                          style={"fontSize": "12px", "color": NEUTRAL}),
#             ], style={"textAlign": "center", "padding": "30px"}),
#         )
#     cards = []
#     for e in events_impact:
#         impact  = e.get("impact_type", "neutre")
#         color   = GREEN if impact == "positif" else RED if impact == "negatif" else ORANGE
#         bg      = GREEN_BG if impact == "positif" else RED_BG if impact == "negatif" else ORANGE_BG
#         arrow   = "↑" if impact == "positif" else "↓" if impact == "negatif" else "→"
#         delta   = e.get("delta")
#         sign    = "+" if delta and delta > 0 else ""
#         d_label = f"{sign}{delta:.3f}" if delta is not None else "N/A"
#         cards.append(html.Div([
#             html.Div([
#                 html.Div(
#                     html.I(className=e.get("icon", "fas fa-circle"),
#                            style={"fontSize": "14px", "color": color}),
#                     className="at-event-icon",
#                     style={"background": "#fff", "border": f"1px solid {color}30"},
#                 ),
#                 html.Div([
#                     html.Div([
#                         html.Strong(e["title"], style={"fontSize": "11px", "color": "#0f1e3c"}),
#                         html.Span(f"{arrow} {d_label}", style={
#                             "fontSize": "10px", "fontWeight": "800", "color": color,
#                             "background": bg, "padding": "2px 7px", "borderRadius": "8px",
#                         }),
#                     ], style={"display": "flex", "justifyContent": "space-between",
#                                "alignItems": "center"}),
#                     html.Div(e["description"],
#                              style={"fontSize": "10px", "color": NEUTRAL, "marginTop": "4px"}),
#                     html.Div([
#                         html.I(className="fas fa-calendar-alt",
#                                style={"fontSize": "9px", "marginRight": "4px", "color": NEUTRAL}),
#                         html.Small(e["date"], style={"fontSize": "9px", "color": NEUTRAL}),
#                     ], style={"marginTop": "6px"}),
#                 ], style={"flex": "1"}),
#             ], style={"display": "flex", "gap": "10px"}),
#         ], className="at-event-card", style={"borderLeft": f"3px solid {color}"}))
#     return html.Div(cards, className="at-events-list")


# def _chart_card(icon_cls, icon_color, icon_bg, title, tooltip_body, children):
#     return html.Div([
#         html.Div([
#             html.Div(
#                 html.I(className=icon_cls, style={"fontSize": "13px", "color": icon_color}),
#                 className="at-card-icon", style={"background": icon_bg},
#             ),
#             html.Span(title, className="at-card-title"),
#             html.Div([
#                 html.Div(html.I(className="fas fa-circle-info"), className="at-tooltip-trigger"),
#                 html.Div([
#                     html.Div(title, className="at-tooltip-title"),
#                     html.Div(tooltip_body, className="at-tooltip-body"),
#                 ], className="at-tooltip-box"),
#             ], className="at-tooltip-wrap"),
#         ], className="at-card-header"),
#         html.Div(children, className="at-card-body"),
#     ], className="at-chart-card")


# # ═══════════════════════════════════════════════════════════════════════════════
# # 7. BARRE DE FILTRE PÉRIODE  ← MODIFIÉE
# #    ✅ Fond blanc avec bordure et ombre (même style que themes_temporal)
# #    ✅ Label "Période d'analyse :" à gauche avec les 3 boutons
# #    ✅ Badge date + bouton Actualiser à droite
# # ═══════════════════════════════════════════════════════════════════════════════

# def make_periode_filter(active_periode="global"):
#     def _btn_style(is_active):
#         return style_btn_active if is_active else style_btn_inactive

#     today = now_local().strftime("%d/%m/%Y")

#     return html.Div(
#         [
#             # ── Gauche : label + boutons ────────────────────────────────────
#             html.Div([
#                 html.I(className="fas fa-calendar-alt",
#                        style={"fontSize": "13px", "color": NEUTRAL, "marginRight": "6px"}),
#                 html.Span("Période d'analyse :",
#                           style={"fontSize": "13px", "color": NEUTRAL,
#                                  "fontWeight": "500", "marginRight": "12px",
#                                  "whiteSpace": "nowrap"}),
#                 html.Button(
#                     [html.I(className="fas fa-globe",
#                             style={"fontSize": "11px"}), "Global"],
#                     id="btn-periode-analytics-global",
#                     n_clicks=0,
#                     style=_btn_style(active_periode == "global"),
#                 ),
#                 html.Button(
#                     [html.I(className="fas fa-calendar-day",
#                             style={"fontSize": "11px"}), "Ce Mois"],
#                     id="btn-periode-analytics-mois",
#                     n_clicks=0,
#                     style=_btn_style(active_periode == "mois"),
#                 ),
#                 html.Button(
#                     [html.I(className="fas fa-clock",
#                             style={"fontSize": "11px"}), "Aujourd'hui"],
#                     id="btn-periode-analytics-jour",
#                     n_clicks=0,
#                     style=_btn_style(active_periode == "jour"),
#                 ),
#             ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),

#             # ── Droite : badge date + bouton Actualiser ─────────────────────
#             html.Div([
#                 html.Div(
#                     [
#                         html.I(className="far fa-calendar-alt",
#                                style={"marginRight": "5px", "fontSize": "13px"}),
#                         html.Span(f"Mise à jour : {today}", style={"fontSize": "13px","color":NEUTRAL}),
#                     ],
#                     style={
#                         "display": "flex", "alignItems": "center",
#                         "background": "white", "padding": "0 15px",
#                         "borderRadius": "8px", "height": "36px",
#                         "border": "1px solid #e0e0e0","color":BLUE,
#                     }
#                 ),
#                 html.Button(
#                     [
#                         html.I(className="fas fa-sync-alt",
#                                style={"marginRight": "5px", "fontSize": "12px"}),
#                         html.Span("Actualiser", style={"fontSize": "12px"}),
#                     ],
#                     id="btn-analytics-refresh",
#                     n_clicks=0,
#                     style={
#                         "background": BLUE, "color": "white", "border": "none",
#                         "borderRadius": "8px", "padding": "0 18px", "cursor": "pointer",
#                         "fontSize": "12px", "display": "flex", "alignItems": "center",
#                         "height": "36px", "gap": "6px",
#                     },
#                 ),
#             ], style={"display": "flex", "gap": "10px", "alignItems": "center"}),
#         ],
#         style={
#             "display": "flex",
#             "justifyContent": "space-between",
#             "alignItems": "center",
#             "gap": "12px",
#             "padding": "12px 20px",
#             "background": "white",
#             "borderRadius": "12px",
#             "marginBottom": "20px",
#             "border": "1px solid #e8edf5",
#             "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
#             "flexWrap": "wrap",
#         }
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# # 8. RENDER PRINCIPAL
# # ═══════════════════════════════════════════════════════════════════════════════
# def render_analytics_page(theme="light", user_data=None, periode="global"):
#     print(f"Analyse Temporelle — Période : {periode}")

#     if periode == "jour":
#         df_hourly    = get_hourly_data_jour()
#         df_weekly, _ = get_weekly_evolution_jour()
#     elif periode == "mois":
#         df_hourly    = get_hourly_data_mois()
#         df_weekly, _ = get_weekly_evolution_mois()
#     else:
#         df_hourly    = get_hourly_data_global()
#         df_weekly, _ = get_weekly_evolution_global()

#     events_impact = get_real_events_from_mongo(
#         periode=periode,
#         top_n=None if periode == "mois" else 5,
#     )

#     metrics    = get_temporal_metrics_periode(df_weekly, df_hourly, periode)
#     nb_h       = len(df_hourly)
#     nb_w       = len(df_weekly)
#     total_msgs = metrics.get("total_messages", 0)
#     mois_label = now_local().strftime("%B %Y")

#     subtitles = {
#         "global": f"{nb_h} tranches horaires · {nb_w} semaines · {total_msgs:,} messages (historique complet)",
#         "mois":   f"{nb_h} tranches horaires · {nb_w} jours · {total_msgs:,} messages ({mois_label})",
#         "jour":   f"{nb_h} tranche(s) horaire(s) · {total_msgs:,} messages (24h — données réelles uniquement)",
#     }
#     sub = subtitles.get(periode, "Analyse des pics d'insatisfaction")

#     sub_with_live = html.Div([
#         html.Span(sub, style={"marginRight": "12px"}),
#         html.Span([
#             html.I(className="fas fa-circle",
#                    style={"fontSize": "8px", "color": GREEN, "marginRight": "6px"}),
#             "Données temps réel" if periode == "jour" else "Données historiques",
#         ], style={
#             "fontSize": "10px", "fontWeight": "500", "color": NEUTRAL,
#             "backgroundColor": GREEN_BG, "padding": "2px 8px",
#             "borderRadius": "20px", "display": "inline-flex", "alignItems": "center",
#         }),
#     ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "8px"})

#     content = html.Div([

#         make_periode_filter(periode),   # ← Ça DOIT être présent !

#         make_kpi_cards(metrics),

#         html.Div([
#             _chart_card(
#                 "fas fa-calendar-xmark", BLUE, BLUE_BG,
#                 "Impact des anomalies détectées",
#                 "Variation du score de satisfaction autour de chaque période anormale détectée automatiquement.",
#                 make_impact_native(events_impact),
#             ),
#             html.Div([
#                 html.Div([
#                     html.Div(
#                         html.I(className="fas fa-list-ul",
#                                style={"fontSize": "13px", "color": BLUE}),
#                         className="at-card-icon", style={"background": BLUE_BG},
#                     ),
#                     html.Span("Détail des anomalies", className="at-card-title"),
#                 ], className="at-card-header"),
#                 html.Div(make_event_list(events_impact), className="at-card-body"),
#             ], className="at-chart-card"),
#         ], className="at-row-2col"),

#         html.Div([
#             _chart_card(
#                 "fas fa-chart-bar", BLUE, GREEN_BG,
#                 "Répartition des avis par heure",
#                 "Proportion satisfaits / insatisfaits par tranche horaire.",
#                 dcc.Graph(
#                     figure=make_hourly_stacked(df_hourly, theme),
#                     config={"displayModeBar": False},
#                     style={"width": "100%", "height": "280px"},
#                 ),
#             ),
#             _chart_card(
#                 "fas fa-inbox", BLUE, BLUE_BG,
#                 "Volume de messages reçus par heure",
#                 "Nombre total de messages clients reçus par tranche horaire.",
#                 dcc.Graph(
#                     figure=make_volume_bars(df_hourly, theme),
#                     config={"displayModeBar": False},
#                     style={"width": "100%", "height": "280px"},
#                 ),
#             ),
#         ], className="at-row-equal"),

#         html.Div([
#             _chart_card(
#                 "fas fa-table-list", BLUE, BLUE_BG,
#                 f"Évolution {'7 derniers jours' if periode == 'jour' else 'journalière' if periode == 'mois' else 'hebdomadaire'}",
#                 f"Score moyen, taux négatif et volume "
#                 f"{'jour par jour sur les 7 derniers jours' if periode == 'jour' else 'jour par jour' if periode == 'mois' else 'semaine par semaine'}.",
#                 make_weekly_table(df_weekly, theme),
#             ),
#             _chart_card(
#                 "fas fa-clock-rotate-left", BLUE, BLUE_BG,
#                 "Score de satisfaction par heure",
#                 "Courbe du score moyen de satisfaction heure par heure.",
#                 dcc.Graph(
#                     figure=make_hourly_line(df_hourly, theme),
#                     config={"displayModeBar": False},
#                     style={"width": "100%", "height": "280px"},
#                 ),
#             ),
#         ], className="at-row-equal"),

#     ], className="at-analytics-page", **{"data-theme": theme})

#     return make_page_layout(
#         "analytics", "Analyse Temporelle", sub_with_live, content, theme, user_data
#     )
# # ═══════════════════════════════════════════════════════════════════════════════
# # 9. DASH LAYOUT + CALLBACKS
# # ═══════════════════════════════════════════════════════════════════════════════

# layout = html.Div(
#     id="analytics-wrapper",
#     **{"data-theme": "light"},
#     children=[
#         dcc.Store(id="periode-analytics-store", data="global", storage_type="session"),
#         dcc.Interval(id="refresh-interval-analytics", interval=300_000, n_intervals=0),
#         html.Div(id="full-analytics-layout"),
#     ],
# )


# @callback(
#     Output("periode-analytics-store", "data"),
#     Output("btn-periode-analytics-global", "style"),
#     Output("btn-periode-analytics-mois", "style"),
#     Output("btn-periode-analytics-jour", "style"),
#     Input("btn-periode-analytics-global", "n_clicks"),
#     Input("btn-periode-analytics-mois", "n_clicks"),
#     Input("btn-periode-analytics-jour", "n_clicks"),
#     State("periode-analytics-store", "data"),
#     prevent_initial_call=True,
# )
# def set_analytics_periode(n_global, n_mois, n_jour, current_periode):
#     A = style_btn_active
#     I = style_btn_inactive

#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return dash.no_update, dash.no_update, dash.no_update, dash.no_update

#     btn = ctx.triggered[0]["prop_id"].split(".")[0]

#     if btn == "btn-periode-analytics-mois":
#         return "mois", I, A, I
#     elif btn == "btn-periode-analytics-jour":
#         return "jour", I, I, A
#     else:
#         return "global", A, I, I


# @callback(
#     Output("full-analytics-layout", "children"),
#     Output("analytics-wrapper", "data-theme"),
#     Input("theme-store", "data"),
#     Input("auth-store", "data"),
#     Input("periode-analytics-store", "data"),
#     Input("refresh-interval-analytics", "n_intervals"),
#     prevent_initial_call=False,
# )
# def update_analytics_page(theme, auth_data, periode, n_intervals):
#     theme = theme or "light"
#     periode = periode or "global"
#     user_data = None
#     if auth_data and auth_data.get("is_authenticated"):
#         user_data = auth_data.get("user", {})
#     return render_analytics_page(theme, user_data, periode), theme

"""
Page d'Analyse Temporelle — ALGÉRIE TÉLÉCOM
✅ Période : Global / Mois / Jour
✅ Événements détectés automatiquement depuis MongoDB
✅ Heures UTC+1 (Algérie) correctement gérées
✅ FIX : heure 0 (minuit) correctement détectée
✅ FIX : btn-analytics-refresh retiré des callbacks (élément dynamique)
✅ FIX : un seul callback principal (prevent_initial_call=False)
✅ FIX : plus de conflit d'Output / allow_duplicate
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import statistics
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from database import MONGO_AVAILABLE, _col

dash.register_page(__name__, path='/analytics', name='Analyse Temporelle')

# ── PALETTE ALGÉRIE TÉLÉCOM ───────────────────────────────────────────────────
BLUE       = "#003087"
BLUE_MID   = "#1a4fa0"
BLUE_LIGHT = "#4a80d4"
BLUE_BG    = "#e8f0fb"
GREEN      = "#00a854"
GREEN_BG   = "#e6f7ef"
RED        = "#e8384f"
RED_BG     = "#fde8eb"
ORANGE     = "#f59e0b"
ORANGE_BG  = "#fef3cd"
NEUTRAL    = "#64748b"

# ── STYLES BOUTONS PÉRIODE ────────────────────────────────────────────────────
style_btn_active = {
    "padding": "6px 16px",
    "borderRadius": "20px",
    "border": "none",
    "background": BLUE,
    "color": "white",
    "cursor": "pointer",
    "fontSize": "12px",
    "fontWeight": "500",
    "transition": "all 0.2s ease",
    "display": "flex",
    "alignItems": "center",
    "gap": "6px",
}
style_btn_inactive = {
    "padding": "6px 16px",
    "borderRadius": "20px",
    "border": f"1px solid {BLUE}",
    "background": "transparent",
    "color": BLUE,
    "cursor": "pointer",
    "fontSize": "12px",
    "fontWeight": "500",
    "transition": "all 0.2s ease",
    "display": "flex",
    "alignItems": "center",
    "gap": "6px",
}

# ── ICÔNES PAR THÈME D'ANOMALIE ───────────────────────────────────────────────
_THEME_ICONS = {
    "reseau":      "fas fa-broadcast-tower",
    "facturation": "fas fa-file-invoice",
    "service":     "fas fa-headset",
    "application": "fas fa-mobile-alt",
    "offre":       "fas fa-tags",
    "hors_sujet":  "fas fa-question-circle",
    "default":     "fas fa-circle-exclamation",
}


def _icon_for_theme(theme: str) -> str:
    if not theme:
        return _THEME_ICONS["default"]
    for key in _THEME_ICONS:
        if key in (theme or "").lower():
            return _THEME_ICONS[key]
    return _THEME_ICONS["default"]


# ── COULEURS PAR THÈME UI ─────────────────────────────────────────────────────
def _colors(theme):
    if theme == "dark":
        return {
            "bg": "#141c2e", "paper_bg": "#141c2e", "text": "#dce8f5",
            "grid": "#1e2d47", "axis_line": "#1e2d47", "primary": "#4a80d4",
            "secondary": "#6c8dcc", "success": "#2ecc71", "warning": "#f39c12",
            "danger": "#f06070", "neutral": "#607b99", "card_bg": "#141c2e",
            "stat_bg": "#1a2236", "border": "#1e2d47",
        }
    return {
        "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
        "grid": "#e8edf5", "axis_line": "#e8edf5", "primary": BLUE,
        "secondary": BLUE_MID, "success": GREEN, "warning": ORANGE,
        "danger": RED, "neutral": NEUTRAL, "card_bg": "#ffffff",
        "stat_bg": "#f8fafd", "border": "rgba(0,48,135,0.10)",
    }


def _base_layout(c, height, margin=None):
    m = margin or dict(l=10, r=10, t=20, b=10)
    return dict(
        plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
        font=dict(color=c["text"], family="'Inter', 'DM Sans', sans-serif", size=10),
        height=height, margin=m,
    )


def now_local():
    """Heure locale Algérie (UTC+1)."""
    return datetime.utcnow() + timedelta(hours=1)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _hour_has_data(hour_dict):
    """
    Vérifie si le dict contient une heure valide.
    ⚠️ L'heure 0 (minuit) est valide — on vérifie explicitement `is not None`.
    """
    return hour_dict is not None and hour_dict.get("hour") is not None


def _score_has_data(hour_dict):
    return hour_dict is not None and hour_dict.get("score") is not None


def _fmt_hour(hour_dict):
    """Formate une heure en 'HH:00', gère minuit (0) correctement."""
    if not _hour_has_data(hour_dict):
        return "--:00"
    return f"{hour_dict['hour']:02d}:00"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FONCTIONS DE DONNÉES PAR PÉRIODE
# ═══════════════════════════════════════════════════════════════════════════════

def get_hourly_data_global():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        pipeline = [
            {"$match": {
                "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
                "heure": {"$exists": True, "$ne": None},
            }},
            {"$group": {
                "_id": "$heure",
                "total": {"$sum": 1},
                "sentiment_sum": {"$sum": "$sentiment_score"},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        data = []
        for r in results:
            total = r["total"]
            if total > 0:
                data.append({
                    "hour": r["_id"],
                    "avg_score": round(r["sentiment_sum"] / total, 3),
                    "neg_pct": round(r["negatifs"] / total * 100, 1),
                    "pos_pct": round(r["positifs"] / total * 100, 1),
                    "total": total,
                })
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erreur get_hourly_data_global: {e}")
        return pd.DataFrame()


def get_weekly_evolution_global():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame(), []
    try:
        pipeline = [
            {"$match": {
                "annee_semaine": {"$exists": True, "$ne": None},
                "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
            }},
            {"$group": {
                "_id": "$annee_semaine",
                "avg_score": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame(), []
        df = pd.DataFrame([{
            "week": r["_id"],
            "avg_score": round(r["avg_score"], 3),
            "total": r["total"],
            "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
        } for r in results])
        if len(df) > 15:
            df = df.tail(15)
        peaks = []
        if len(df) > 3:
            mean_score = df["avg_score"].mean()
            std_score  = df["avg_score"].std()
            for _, row in df.iterrows():
                if row["avg_score"] < mean_score - 1.5 * std_score:
                    peaks.append({"week": row["week"], "score": row["avg_score"]})
        return df, peaks
    except Exception as e:
        print(f"Erreur get_weekly_evolution_global: {e}")
        return pd.DataFrame(), []


def _mois_bornes():
    now   = now_local()
    debut = datetime(now.year, now.month, 1) - timedelta(hours=1)
    fin   = datetime(now.year + 1, 1, 1) - timedelta(hours=1) if now.month == 12 \
            else datetime(now.year, now.month + 1, 1) - timedelta(hours=1)
    return debut, fin


def get_hourly_data_mois():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        debut, fin = _mois_bornes()
        mois_str   = now_local().strftime("%Y-%m")
        match_filter = {
            "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
            "$or": [
                {"mois": mois_str},
                {"date_originale": {"$gte": debut, "$lt": fin}},
                {"date_annotation": {"$gte": debut, "$lt": fin}},
            ],
        }
        pipeline = [
            {"$match": match_filter},
            {"$addFields": {"_date_src": {"$cond": {
                "if": {"$eq": [{"$type": "$date_originale"}, "date"]},
                "then": "$date_originale",
                "else": {"$cond": {
                    "if": {"$eq": [{"$type": "$date_annotation"}, "date"]},
                    "then": "$date_annotation", "else": None,
                }},
            }}}},
            {"$addFields": {"_heure_calc": {"$cond": {
                "if": {"$and": [
                    {"$ne": ["$heure", None]},
                    {"$ne": [{"$type": "$heure"}, "missing"]},
                ]},
                "then": "$heure",
                "else": {"$cond": {
                    "if": {"$ne": ["$_date_src", None]},
                    "then": {"$hour": {"$add": ["$_date_src", 3600000]}},
                    "else": None,
                }},
            }}}},
            {"$match": {"_heure_calc": {"$ne": None}}},
            {"$group": {
                "_id": "$_heure_calc",
                "total": {"$sum": 1},
                "sentiment_sum": {"$sum": "$sentiment_score"},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        data = []
        for r in results:
            total = r["total"]
            if total > 0:
                data.append({
                    "hour": r["_id"],
                    "avg_score": round(r["sentiment_sum"] / total, 3),
                    "neg_pct": round(r["negatifs"] / total * 100, 1),
                    "pos_pct": round(r["positifs"] / total * 100, 1),
                    "total": total,
                })
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erreur get_hourly_data_mois: {e}")
        return pd.DataFrame()


def get_weekly_evolution_mois():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame(), []
    try:
        debut, fin = _mois_bornes()
        mois_str   = now_local().strftime("%Y-%m")
        match_filter = {
            "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
            "$or": [
                {"mois": mois_str},
                {"date_clean": {"$gte": debut, "$lt": fin}},
                {"date_annotation": {"$gte": debut, "$lt": fin}},
            ],
        }
        pipeline = [
            {"$match": match_filter},
            {"$addFields": {
                "_jour": {
                    "$cond": {
                        "if": {"$eq": [{"$type": "$date_clean"}, "date"]},
                        "then": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$date_clean",
                            }
                        },
                        "else": None,
                    }
                }
            }},
            {"$match": {"_jour": {"$ne": None}}},
            {"$group": {
                "_id": "$_jour",
                "avg_score": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame(), []
        df = pd.DataFrame([{
            "week": r["_id"],
            "avg_score": round(r["avg_score"], 3),
            "total": r["total"],
            "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
        } for r in results])
        peaks = []
        if len(df) > 2:
            mean_score = df["avg_score"].mean()
            std_score  = df["avg_score"].std()
            for _, row in df.iterrows():
                if row["avg_score"] < mean_score - 1.5 * std_score:
                    peaks.append({"week": row["week"], "score": row["avg_score"]})
        return df, peaks
    except Exception as e:
        print(f"Erreur get_weekly_evolution_mois: {e}")
        return pd.DataFrame(), []


def get_hourly_data_jour():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        now = now_local()
        debut_jour = datetime(now.year, now.month, now.day, 0, 0, 0)
        fin_jour   = datetime(now.year, now.month, now.day, 23, 59, 59)
        pipeline = [
            {"$match": {
                "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
                "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
            }},
            {"$group": {
                "_id": "$heure",
                "total": {"$sum": 1},
                "sentiment_sum": {"$sum": "$sentiment_score"},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        data = []
        for r in results:
            total = r["total"]
            if total > 0 and r["_id"] is not None:
                data.append({
                    "hour": r["_id"],
                    "avg_score": round(r["sentiment_sum"] / total, 3),
                    "neg_pct": round(r["negatifs"] / total * 100, 1),
                    "pos_pct": round(r["positifs"] / total * 100, 1),
                    "total": total,
                })
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erreur get_hourly_data_jour: {e}")
        return pd.DataFrame()


def get_weekly_evolution_jour():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame(), []
    try:
        now = now_local()
        sept_jours = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=6)
        pipeline = [
            {"$match": {
                "date_clean": {"$gte": sept_jours},
                "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
            }},
            {"$addFields": {
                "jour_str": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$date_clean",
                    }
                }
            }},
            {"$group": {
                "_id": "$jour_str",
                "avg_score": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame(), []
        df = pd.DataFrame([{
            "week": r["_id"],
            "avg_score": round(r["avg_score"], 3),
            "total": r["total"],
            "neg_pct": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
        } for r in results])
        peaks = []
        if len(df) > 2:
            mean_score = df["avg_score"].mean()
            std_score  = df["avg_score"].std()
            for _, row in df.iterrows():
                if row["avg_score"] < mean_score - 1.5 * std_score:
                    peaks.append({"week": row["week"], "score": row["avg_score"]})
        return df, peaks
    except Exception as e:
        print(f"Erreur get_weekly_evolution_jour: {e}")
        return pd.DataFrame(), []


def get_temporal_metrics_periode(df_weekly, df_hourly, periode="global"):
    metrics = {"periode": periode, "total_messages": 0}
    if not df_hourly.empty:
        metrics["total_messages"] = int(df_hourly["total"].sum())
        if not df_hourly["avg_score"].isnull().all():
            worst_h = df_hourly.loc[df_hourly["avg_score"].idxmin()]
            best_h  = df_hourly.loc[df_hourly["avg_score"].idxmax()]
            metrics["worst_hour"] = {
                "hour": int(worst_h["hour"]),
                "score": float(worst_h["avg_score"]),
            }
            metrics["best_hour"] = {
                "hour": int(best_h["hour"]),
                "score": float(best_h["avg_score"]),
            }
    if not df_weekly.empty:
        worst = df_weekly.loc[df_weekly["avg_score"].idxmin()]
        best  = df_weekly.loc[df_weekly["avg_score"].idxmax()]
        metrics["worst_week"] = {"week": worst["week"], "score": float(worst["avg_score"])}
        metrics["best_week"]  = {"week": best["week"],  "score": float(best["avg_score"])}
        if len(df_weekly) > 1:
            slope = np.polyfit(np.arange(len(df_weekly)), df_weekly["avg_score"].values, 1)[0]
            metrics["trend"]       = "positive" if slope > 0.01 else "negative" if slope < -0.01 else "stable"
            metrics["trend_value"] = round(slope, 4)
        else:
            metrics["trend"]       = "stable"
            metrics["trend_value"] = 0.0
    elif not df_hourly.empty:
        if len(df_hourly) > 1 and not df_hourly["avg_score"].isnull().all():
            slope = np.polyfit(np.arange(len(df_hourly)), df_hourly["avg_score"].values, 1)[0]
            metrics["trend"]       = "positive" if slope > 0.005 else "negative" if slope < -0.005 else "stable"
            metrics["trend_value"] = round(slope, 4)
        else:
            metrics["trend"]       = "stable"
            metrics["trend_value"] = 0.0
    return metrics


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DÉTECTION RÉELLE DES ANOMALIES DEPUIS MONGODB
# ═══════════════════════════════════════════════════════════════════════════════

def get_real_events_from_mongo(periode: str = "global", top_n: int = None):
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        match_base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
        add_fields_stage = None
        label_prefix     = "Semaine"

        if periode == "jour":
            now = now_local()
            debut_jour = datetime(now.year, now.month, now.day, 0, 0, 0)
            fin_jour   = datetime(now.year, now.month, now.day, 23, 59, 59)
            match_base["date_clean"] = {"$gte": debut_jour, "$lte": fin_jour}
            label_prefix = "Heure"
            add_fields_stage = None
            group_by = "$heure"

        elif periode == "mois":
            debut, fin = _mois_bornes()
            mois_str   = now_local().strftime("%Y-%m")
            match_base["$or"] = [
                {"annee_mois": mois_str},
                {"date_clean": {"$gte": debut, "$lt": fin}},
                {"date_annotation": {"$gte": debut, "$lt": fin}},
            ]
            label_prefix = "Journée"
            group_by     = {"$dateToString": {"format": "%Y-%m-%d", "date": "$date_clean"}}

        else:
            label_prefix = "Semaine"
            group_by     = "$annee_semaine"

        pipeline = [{"$match": match_base}]
        if add_fields_stage:
            pipeline.append(add_fields_stage)
            pipeline.append({"$match": {"jour_str": {"$ne": None}}})

        pipeline += [
            {"$group": {
                "_id": group_by,
                "avg_score": {"$avg": "$sentiment_score"},
                "total":     {"$sum": 1},
                "negatifs":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                "themes":    {"$push": "$theme_pred"},
                "sources":   {"$push": "$source"},
            }},
            {"$match": {"_id": {"$ne": None}}},
            {"$sort": {"_id": 1}},
        ]

        results = list(_col.aggregate(pipeline))
        if not results or len(results) < 2:
            return []

        scores = [r["avg_score"] for r in results if r.get("avg_score") is not None]
        if len(scores) < 2:
            return []

        mean_score = statistics.mean(scores)
        std_score  = statistics.stdev(scores) if len(scores) > 1 else 1.0
        if std_score == 0:
            std_score = 1.0

        anomalies = []
        for i, r in enumerate(results):
            s       = r.get("avg_score") or 0
            total   = r.get("total") or 1
            neg_pct = round(r.get("negatifs", 0) / total * 100, 1)
            z_score = (s - mean_score) / std_score

            if z_score < -0.8 or neg_pct > 65:
                score_before  = round(results[i - 1].get("avg_score") or mean_score, 3) if i > 0 else round(mean_score, 3)
                score_after   = round(s, 3)
                delta         = round(score_after - score_before, 3)

                themes_list     = [t for t in (r.get("themes") or []) if t]
                theme_dominant  = max(set(themes_list), key=themes_list.count) if themes_list else "autre"
                sources_list    = [s2 for s2 in (r.get("sources") or []) if s2]
                source_dominant = max(set(sources_list), key=sources_list.count) if sources_list else "Inconnue"
                period_id = r["_id"]

                if periode == "jour":
                    try:
                        heure_str = str(period_id).split(" ")[-1]
                        period_label = heure_str
                    except Exception:
                        period_label = str(period_id)
                elif periode == "mois":
                    try:
                        dt = datetime.strptime(str(period_id), "%Y-%m-%d")
                        mois_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                                   "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
                        period_label = f"{dt.day} {mois_fr[dt.month - 1]} {dt.year}"
                    except Exception:
                        period_label = str(period_id)
                else:
                    period_label = str(period_id)

                severity = abs(z_score)
                # Déterminer impact_type si pas déjà fait
                delta = round(score_after - score_before, 3)
                if delta < -0.05:
                    impact_type = "negatif"
                elif delta > 0.05:
                    impact_type = "positif"
                else:
                    impact_type = "neutre"

                # Choisir le préfixe du titre en fonction de l'impact et de la sévérité
                if impact_type == "positif":
                    title_prefix = "✅ Amélioration notable"
                elif impact_type == "negatif":
                    if severity > 2:
                        title_prefix = "⚠️ Pic critique"
                    elif severity > 1.5:
                        title_prefix = "Forte dégradation"
                    else:
                        title_prefix = "Dégradation détectée"
                else:  # neutre
                    title_prefix = "🔵 Variation neutre"

                anomalies.append({
                    "id":           f"auto_{period_id}",
                    "date":         str(period_id),
                    "title":        f"{title_prefix} — {label_prefix} {period_label}",
                    "description":  (
                        f"{neg_pct:.0f}% d'avis négatifs · {total:,} messages · "
                        f"Score moyen : {score_after:+.3f} · Source : {source_dominant}"
                    ),
                    "impact":       "negatif",
                    "source":       f"Détection automatique ({source_dominant})",
                    "icon":         _icon_for_theme(theme_dominant),
                    "score_before": score_before,
                    "score_after":  score_after,
                    "delta":        delta,
                    "impact_type":  impact_type,
                    "_z_score":     round(z_score, 2),
                    "_neg_pct":     neg_pct,
                })

                

        anomalies.sort(key=lambda x: x["_z_score"])

        if periode == "mois":
            return anomalies
        if top_n is not None:
            return anomalies[:top_n]
        return anomalies 

    except Exception as e:
        print(f"Erreur get_real_events_from_mongo: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 3. COMPOSANTS SVG RING
# ═══════════════════════════════════════════════════════════════════════════════

def make_score_ring(score, color, size=65):
    if score is None:
        score = 0
    pct         = max(0, min(100, int((score + 1) / 2 * 100)))
    score_label = f"{score:+.2f}"
    fig = go.Figure()
    fig.add_trace(go.Pie(
        values=[pct, 100 - pct], hole=0.7,
        marker_colors=[color, "#e8edf5"],
        textinfo='none', hoverinfo='none', showlegend=False,
        sort=False, direction="clockwise", rotation=90,
    ))
    fig.add_annotation(
        text=score_label, x=0.5, y=0.5, showarrow=False,
        font=dict(size=10, color=color), xanchor="center", yanchor="middle",
    )
    fig.update_layout(
        width=size, height=size, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return html.Div(
        dcc.Graph(figure=fig, config={'displayModeBar': False}),
        style={"flexShrink": "0", "width": f"{size}px", "height": f"{size}px"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. KPI CARDS
# ═══════════════════════════════════════════════════════════════════════════════

def make_kpi_cards(metrics):
    if not metrics or metrics.get("total_messages", 0) == 0:
        return html.Div(
            html.Div([
                html.I(className="fas fa-chart-line", style={"fontSize": "24px", "color": NEUTRAL}),
                html.H4("Aucune donnée", style={"marginTop": "12px", "color": NEUTRAL}),
                html.P("Sélectionnez une période avec des données disponibles",
                       style={"fontSize": "12px", "color": NEUTRAL}),
            ], style={"textAlign": "center", "padding": "40px"}),
            className="at-kpi-grid",
        )

    worst_week = metrics.get("worst_week", {})
    best_week  = metrics.get("best_week", {})
    worst_hour = metrics.get("worst_hour", {})
    best_hour  = metrics.get("best_hour", {})
    trend_dir  = metrics.get("trend", "stable")
    trend_val  = metrics.get("trend_value", 0)
    periode    = metrics.get("periode", "global")
    total_msgs = metrics.get("total_messages", 0)

    if trend_dir == "positive":
        t_color, t_icon, t_label = GREEN, "fas fa-arrow-trend-up", "Amélioration"
        t_delta = f"+{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"
    elif trend_dir == "negative":
        t_color, t_icon, t_label = RED, "fas fa-arrow-trend-down", "Dégradation"
        t_delta = f"{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"
    else:
        t_color, t_icon, t_label = ORANGE, "fas fa-minus", "Stable"
        t_delta = f"{trend_val:.4f} / {'sem' if periode != 'jour' else 'jour'}"

    def _card(accent, icon_cls, icon_bg, icon_color, label, value_el, ring_el=None, extra_cls=""):
        return html.Div([
            html.Div([
                html.Div(
                    html.I(className=icon_cls, style={"fontSize": "14px", "color": icon_color}),
                    className="at-kpi-icon", style={"background": icon_bg},
                ),
                html.Span(label, className="at-kpi-label"),
            ], className="at-kpi-title-row"),
            html.Div([value_el, ring_el or html.Span()], className="at-kpi-value-row"),
        ], className=f"at-kpi-card {extra_cls}", style={"--kpi-accent": accent})

    trend_card = html.Div([
        html.Div([
            html.Div(
                html.I(className=t_icon, style={"fontSize": "20px", "color": "white"}),
                className="at-kpi-icon", style={"background": "rgba(255,255,255,0.2)"},
            ),
            html.Span("Tendance générale", className="at-kpi-label",
                      style={"color": "rgba(255,255,255,0.7)"}),
        ], className="at-kpi-title-row"),
        html.Div([html.Div([
            html.Div(f"{total_msgs:,} messages",
                     style={"color": "white", "fontSize": "14px", "fontWeight": "bold", "marginTop": "5px"}),
            html.Div(t_label, style={"color": "white", "fontSize": "13px", "marginTop": "8px"}),
            html.Div(t_delta,  style={"color": "rgba(255,255,255,0.7)", "fontSize": "11px", "marginTop": "4px"}),
        ], className="at-trend-body")], className="at-kpi-value-row"),
    ], className="at-kpi-card trend", style={"background": BLUE, "border": "none"})

    # ── MODE JOUR ──────────────────────────────────────────────────────────────
    if periode == "jour":
        worst_day = worst_week
        best_day  = best_week

        def _fmt_day(day_str):
            if not day_str:
                return "N/A"
            try:
                dt = datetime.strptime(str(day_str), "%Y-%m-%d")
                mois_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                           "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
                return f"{dt.day} {mois_fr[dt.month - 1]}"
            except Exception:
                return str(day_str)

        cards = [
            _card(RED, "fas fa-circle-exclamation", "rgba(232,56,79,0.10)", RED,
                  "Heure critique (24h)",
                  html.Div(_fmt_hour(worst_hour), className="at-kpi-value"),
                  make_score_ring(worst_hour.get("score", 0), RED) if _score_has_data(worst_hour) else None),
            _card(GREEN, "fas fa-circle-check", "rgba(0,168,84,0.10)", GREEN,
                  "Heure favorable (24h)",
                  html.Div(_fmt_hour(best_hour), className="at-kpi-value"),
                  make_score_ring(best_hour.get("score", 0), GREEN) if _score_has_data(best_hour) else None),
            _card(RED, "fas fa-calendar-xmark", "rgba(232,56,79,0.10)", RED,
                  "Jour difficile (7j)",
                  html.Div(_fmt_day(worst_day.get("week") if worst_day else None), className="at-kpi-value"),
                  make_score_ring(worst_day.get("score", 0), RED) if _score_has_data(worst_day) else None),
            _card(GREEN, "fas fa-calendar-check", "rgba(0,168,84,0.10)", GREEN,
                  "Meilleur jour (7j)",
                  html.Div(_fmt_day(best_day.get("week") if best_day else None), className="at-kpi-value"),
                  make_score_ring(best_day.get("score", 0), GREEN) if _score_has_data(best_day) else None),
            trend_card,
        ]
        return html.Div(cards, className="at-kpi-grid")

    # ── MODE GLOBAL / MOIS ─────────────────────────────────────────────────────
    week_labels     = {"global": "Semaine difficile", "mois": "Jour difficile"}
    week_labels_pos = {"global": "Semaine positive",  "mois": "Meilleur jour"}
    hour_labels     = {"global": "Heure critique",    "mois": "Heure critique (mois)"}
    hour_labels_pos = {"global": "Heure favorable",   "mois": "Heure favorable (mois)"}

    cards = [
        _card(RED, "fas fa-circle-exclamation", "rgba(232,56,79,0.10)", RED,
              week_labels.get(periode, "Semaine difficile"),
              html.Div(str(worst_week.get("week", "N/A")) if worst_week else "N/A", className="at-kpi-value"),
              make_score_ring(worst_week.get("score", 0), RED) if _score_has_data(worst_week) else None),
        _card(GREEN, "fas fa-circle-check", "rgba(0,168,84,0.10)", GREEN,
              week_labels_pos.get(periode, "Semaine positive"),
              html.Div(str(best_week.get("week", "N/A")) if best_week else "N/A", className="at-kpi-value"),
              make_score_ring(best_week.get("score", 0), GREEN) if _score_has_data(best_week) else None),
        _card(ORANGE, "fas fa-clock", "rgba(245,158,11,0.10)", ORANGE,
              hour_labels.get(periode, "Heure critique"),
              html.Div(_fmt_hour(worst_hour), className="at-kpi-value"),
              make_score_ring(worst_hour.get("score", 0), ORANGE) if _score_has_data(worst_hour) else None),
        _card(GREEN, "fas fa-sun", "rgba(0,168,84,0.10)", GREEN,
              hour_labels_pos.get(periode, "Heure favorable"),
              html.Div(_fmt_hour(best_hour), className="at-kpi-value"),
              make_score_ring(best_hour.get("score", 0), GREEN) if _score_has_data(best_hour) else None),
        trend_card,
    ]
    return html.Div(cards, className="at-kpi-grid")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GRAPHIQUES PLOTLY
# ═══════════════════════════════════════════════════════════════════════════════

def make_hourly_stacked(df, theme="light"):
    c = _colors(theme)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 260))
        return fig
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["hour"], y=df["pos_pct"], name="Satisfaits",
        marker=dict(color=c["success"], cornerradius=5),
        text=[f"{p:.0f}%" for p in df["pos_pct"]], textposition="inside",
        textfont=dict(size=9, color="white"),
        hovertemplate="%{x}h — Satisfaits: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df["hour"], y=df["neg_pct"], name="Insatisfaits",
        marker=dict(color=c["danger"], cornerradius=5),
        text=[f"{n:.0f}%" for n in df["neg_pct"]], textposition="inside",
        textfont=dict(size=9, color="white"),
        hovertemplate="%{x}h — Insatisfaits: %{y:.1f}%<extra></extra>",
    ))
    layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
    layout.update(
        xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1, range=[0, 23], gridcolor=c["grid"]),
        yaxis=dict(title="%", range=[0, 100], ticksuffix="%", gridcolor=c["grid"]),
        barmode="stack",
        legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"),
        hovermode="x unified",
    )
    fig.update_layout(**layout)
    return fig


def make_volume_bars(df, theme="light"):
    c = _colors(theme)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 260))
        return fig
    max_v      = df["total"].max() if not df.empty else 1
    bar_colors = [f"rgba(0,48,135,{0.45 + 0.55 * v / max_v:.2f})" for v in df["total"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["hour"], y=df["total"],
        marker=dict(color=bar_colors, cornerradius=6),
        text=[f"{v:,}" for v in df["total"]], textposition="outside",
        textfont=dict(size=8, color=c["text"]),
        hovertemplate="%{x}h — %{y:,} messages<extra></extra>",
    ))
    layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
    layout.update(
        xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1, range=[0, 23], gridcolor=c["grid"]),
        yaxis=dict(title="Messages", tickformat=",d", gridcolor=c["grid"]),
        showlegend=False, hovermode="x unified",
    )
    fig.update_layout(**layout)
    return fig


def make_hourly_line(df, theme="light"):
    c = _colors(theme)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 260))
        return fig
    point_colors = [
        c["success"] if s >= 0.1 else c["danger"] if s <= -0.1 else c["warning"]
        for s in df["avg_score"]
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["hour"], y=df["avg_score"], mode="lines+markers",
        line=dict(color=BLUE, width=2.5, shape="spline"),
        marker=dict(size=7, color=point_colors, line=dict(color="white", width=1.5)),
        fill="tozeroy", fillcolor="rgba(0,48,135,0.06)",
        hovertemplate="%{x}h → %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=c["neutral"], opacity=0.35)
    layout = _base_layout(c, 260, margin=dict(l=36, r=16, t=14, b=36))
    layout.update(
        xaxis=dict(title="Heure", tickmode="linear", tick0=0, dtick=1, range=[0, 23], gridcolor=c["grid"]),
        yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False, gridcolor=c["grid"]),
        showlegend=False, hovermode="x unified",
    )
    fig.update_layout(**layout)
    return fig


def make_weekly_table(df_weekly, theme="light"):
    c = _colors(theme)
    if df_weekly.empty:
        return html.Div("Aucune donnée",
                        style={"textAlign": "center", "padding": "40px", "color": c["neutral"]})
    rows = []
    for _, row in df_weekly.iterrows():
        s         = row["avg_score"]
        score_cls = "score-pos" if s >= 0.1 else "score-neg" if s <= -0.1 else "score-neu"
        rows.append(html.Tr([
            html.Td(html.Span(row["week"], className="at-week-badge")),
            html.Td(f"{s:+.3f}", className=f"at-score-cell {score_cls}",
                    style={"textAlign": "right"}),
            html.Td(f"{row['neg_pct']:.1f}%",
                    style={"textAlign": "right", "color": RED, "fontSize": "11px"}),
            html.Td(f"{row['total']:,}",
                    style={"textAlign": "right", "color": c["text"], "fontSize": "11px"}),
        ]))
    return html.Div(
        html.Table([
            html.Thead(html.Tr([
                html.Th("Période"),
                html.Th("Score moy.", style={"textAlign": "right"}),
                html.Th("Taux nég.",  style={"textAlign": "right"}),
                html.Th("Volume",     style={"textAlign": "right"}),
            ])),
            html.Tbody(rows),
        ]),
        className="at-table-wrap",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. COMPOSANTS ÉVÉNEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def make_impact_native(events_impact):
    if not events_impact:
        return html.Div(
            html.Div([
                html.I(className="fas fa-magnifying-glass-chart",
                       style={"fontSize": "28px", "color": NEUTRAL, "marginBottom": "10px"}),
                html.Div("Aucune anomalie détectée sur cette période",
                         style={"fontSize": "12px", "color": NEUTRAL}),
            ], style={"textAlign": "center", "padding": "30px"}),
        )
    items = []
    for e in events_impact:
        delta  = e.get("delta")
        impact = e.get("impact_type", "neutre")
        color  = GREEN if impact == "positif" else RED if impact == "negatif" else ORANGE
        bg     = GREEN_BG if impact == "positif" else RED_BG if impact == "negatif" else ORANGE_BG
        sign   = "+" if delta and delta > 0 else ""
        delta_label = f"{sign}{delta:.3f}" if delta is not None else "N/A"
        before = e.get("score_before", 0) or 0
        after  = e.get("score_after",  0) or 0
        before_pct = int((before + 1) / 2 * 100)
        after_pct  = int((after  + 1) / 2 * 100)

        items.append(html.Div([
            html.Div([
                html.Div([
                    html.I(className=e.get("icon", "fas fa-circle"),
                           style={"fontSize": "12px", "color": color, "marginRight": "6px"}),
                    html.Strong(e["title"], style={"fontSize": "11px", "color": "#0f1e3c"}),
                ]),
                html.Span(delta_label, style={
                    "fontSize": "10px", "fontWeight": "800", "color": color,
                    "background": bg, "padding": "2px 8px", "borderRadius": "10px",
                }),
            ], style={"display": "flex", "justifyContent": "space-between",
                      "alignItems": "center", "marginBottom": "8px"}),
            html.Div([
                html.Span("Avant", style={"fontSize": "9px", "color": NEUTRAL,
                                          "width": "34px", "display": "inline-block"}),
                html.Div(
                    html.Div(style={"width": f"{before_pct}%", "height": "7px",
                                    "background": NEUTRAL, "opacity": "0.45", "borderRadius": "4px"}),
                    style={"flex": "1", "background": "#eef1f8",
                           "borderRadius": "4px", "height": "7px", "margin": "0 8px"},
                ),
                html.Span(f"{before:+.2f}", style={"fontSize": "9px", "color": NEUTRAL,
                                                    "width": "36px", "textAlign": "right"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
            html.Div([
                html.Span("Après", style={"fontSize": "9px", "color": color,
                                          "width": "34px", "display": "inline-block",
                                          "fontWeight": "700"}),
                html.Div(
                    html.Div(style={"width": f"{after_pct}%", "height": "7px",
                                    "background": color, "borderRadius": "4px"}),
                    style={"flex": "1", "background": "#eef1f8",
                           "borderRadius": "4px", "height": "7px", "margin": "0 8px"},
                ),
                html.Span(f"{after:+.2f}", style={"fontSize": "9px", "color": color,
                                                   "width": "36px", "textAlign": "right",
                                                   "fontWeight": "700"}),
            ], style={"display": "flex", "alignItems": "center"}),
        ], className="at-impact-row"))
    return html.Div(items)


def make_event_list(events_impact):
    if not events_impact:
        return html.Div(
            html.Div([
                html.I(className="fas fa-inbox",
                       style={"fontSize": "28px", "color": NEUTRAL, "marginBottom": "10px"}),
                html.Div("Aucune anomalie détectée",
                         style={"fontSize": "12px", "color": NEUTRAL}),
            ], style={"textAlign": "center", "padding": "30px"}),
        )
    cards = []
    for e in events_impact:
        impact  = e.get("impact_type", "neutre")
        color   = GREEN if impact == "positif" else RED if impact == "negatif" else ORANGE
        bg      = GREEN_BG if impact == "positif" else RED_BG if impact == "negatif" else ORANGE_BG
        arrow   = "↑" if impact == "positif" else "↓" if impact == "negatif" else "→"
        delta   = e.get("delta")
        sign    = "+" if delta and delta > 0 else ""
        d_label = f"{sign}{delta:.3f}" if delta is not None else "N/A"
        cards.append(html.Div([
            html.Div([
                html.Div(
                    html.I(className=e.get("icon", "fas fa-circle"),
                           style={"fontSize": "14px", "color": color}),
                    className="at-event-icon",
                    style={"background": "#fff", "border": f"1px solid {color}30"},
                ),
                html.Div([
                    html.Div([
                        html.Strong(e["title"], style={"fontSize": "11px", "color": "#0f1e3c"}),
                        html.Span(f"{arrow} {d_label}", style={
                            "fontSize": "10px", "fontWeight": "800", "color": color,
                            "background": bg, "padding": "2px 7px", "borderRadius": "8px",
                        }),
                    ], style={"display": "flex", "justifyContent": "space-between",
                               "alignItems": "center"}),
                    html.Div(e["description"],
                             style={"fontSize": "10px", "color": NEUTRAL, "marginTop": "4px"}),
                    html.Div([
                        html.I(className="fas fa-calendar-alt",
                               style={"fontSize": "9px", "marginRight": "4px", "color": NEUTRAL}),
                        html.Small(e["date"], style={"fontSize": "9px", "color": NEUTRAL}),
                    ], style={"marginTop": "6px"}),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "10px"}),
        ], className="at-event-card", style={"borderLeft": f"3px solid {color}"}))
    return html.Div(cards, className="at-events-list")


def _chart_card(icon_cls, icon_color, icon_bg, title, tooltip_body, children):
    return html.Div([
        html.Div([
            html.Div(
                html.I(className=icon_cls, style={"fontSize": "13px", "color": icon_color}),
                className="at-card-icon", style={"background": icon_bg},
            ),
            html.Span(title, className="at-card-title"),
            html.Div([
                html.Div(html.I(className="fas fa-circle-info"), className="at-tooltip-trigger"),
                html.Div([
                    html.Div(title, className="at-tooltip-title"),
                    html.Div(tooltip_body, className="at-tooltip-body"),
                ], className="at-tooltip-box"),
            ], className="at-tooltip-wrap"),
        ], className="at-card-header"),
        html.Div(children, className="at-card-body"),
    ], className="at-chart-card")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. BARRE DE FILTRE PÉRIODE
#    ✅ Pas de btn-analytics-refresh (évite l'erreur d'ID inexistant dans callback)
#    ✅ Badge date + rafraîchissement automatique via dcc.Interval
# ═══════════════════════════════════════════════════════════════════════════════

def make_periode_filter(active_periode="global"):
    def _btn_style(is_active):
        return style_btn_active if is_active else style_btn_inactive

    today = now_local().strftime("%d/%m/%Y")

    return html.Div(
        [
            # ── Gauche : label + boutons ────────────────────────────────────
            html.Div([
                html.I(className="fas fa-calendar-alt",
                       style={"fontSize": "13px", "color": NEUTRAL, "marginRight": "6px"}),
                html.Span("Période d'analyse :",
                          style={"fontSize": "13px", "color": NEUTRAL,
                                 "fontWeight": "500", "marginRight": "12px",
                                 "whiteSpace": "nowrap"}),
                html.Button(
                    [html.I(className="fas fa-globe",
                            style={"fontSize": "11px"}), "Global"],
                    id="btn-periode-analytics-global",
                    n_clicks=0,
                    style=_btn_style(active_periode == "global"),
                ),
                html.Button(
                    [html.I(className="fas fa-calendar-day",
                            style={"fontSize": "11px"}), "Ce Mois"],
                    id="btn-periode-analytics-mois",
                    n_clicks=0,
                    style=_btn_style(active_periode == "mois"),
                ),
                html.Button(
                    [html.I(className="fas fa-clock",
                            style={"fontSize": "11px"}), "Aujourd'hui"],
                    id="btn-periode-analytics-jour",
                    n_clicks=0,
                    style=_btn_style(active_periode == "jour"),
                ),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),

            # ── Droite : badge date uniquement (pas de btn-analytics-refresh) ──
            html.Div(
                [
                    html.I(className="far fa-calendar-alt",
                           style={"marginRight": "5px", "fontSize": "13px", "color": BLUE}),
                    html.Span(f"Mise à jour : {today}",
                              style={"fontSize": "13px", "color": NEUTRAL}),
                ],
                style={
                    "display": "flex", "alignItems": "center",
                    "background": "white", "padding": "0 15px",
                    "borderRadius": "8px", "height": "36px",
                    "border": "1px solid #e0e0e0",
                }
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "gap": "12px",
            "padding": "12px 20px",
            "background": "white",
            "borderRadius": "12px",
            "marginBottom": "20px",
            "border": "1px solid #e8edf5",
            "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
            "flexWrap": "wrap",
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 8. RENDER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def render_analytics_page(theme="light", user_data=None, periode="global"):
    print(f"Analyse Temporelle — Période : {periode}")

    if periode == "jour":
        df_hourly    = get_hourly_data_jour()
        df_weekly, _ = get_weekly_evolution_jour()
    elif periode == "mois":
        df_hourly    = get_hourly_data_mois()
        df_weekly, _ = get_weekly_evolution_mois()
    else:
        df_hourly    = get_hourly_data_global()
        df_weekly, _ = get_weekly_evolution_global()

    events_impact = get_real_events_from_mongo(
        periode=periode,
        top_n=None,
    )

    metrics    = get_temporal_metrics_periode(df_weekly, df_hourly, periode)
    nb_h       = len(df_hourly)
    nb_w       = len(df_weekly)
    total_msgs = metrics.get("total_messages", 0)
    mois_label = now_local().strftime("%B %Y")

    subtitles = {
        "global": f"{nb_h} tranches horaires · {nb_w} semaines · {total_msgs:,} messages (historique complet)",
        "mois":   f"{nb_h} tranches horaires · {nb_w} jours · {total_msgs:,} messages ({mois_label})",
        "jour":   f"{nb_h} tranche(s) horaire(s) · {total_msgs:,} messages (aujourd'hui — données réelles)",
    }
    sub = subtitles.get(periode, "Analyse des pics d'insatisfaction")

    sub_with_live = html.Div([
        html.Span(sub, style={"marginRight": "12px"}),
        html.Span([
            html.I(className="fas fa-circle",
                   style={"fontSize": "8px", "color": GREEN, "marginRight": "6px"}),
            "Données temps réel" if periode == "jour" else "Données historiques",
        ], style={
            "fontSize": "10px", "fontWeight": "500", "color": NEUTRAL,
            "backgroundColor": GREEN_BG, "padding": "2px 8px",
            "borderRadius": "20px", "display": "inline-flex", "alignItems": "center",
        }),
    ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "8px"})

    # Libellé évolution adapté à la période
    if periode == "jour":
        evol_title   = "Évolution — 7 derniers jours"
        evol_tooltip = "Score moyen, taux négatif et volume jour par jour sur les 7 derniers jours."
    elif periode == "mois":
        evol_title   = "Évolution journalière"
        evol_tooltip = "Score moyen, taux négatif et volume jour par jour."
    else:
        evol_title   = "Évolution hebdomadaire"
        evol_tooltip = "Score moyen, taux négatif et volume semaine par semaine."

    content = html.Div([

        make_periode_filter(periode),

        make_kpi_cards(metrics),

        html.Div([
            _chart_card(
                "fas fa-calendar-xmark", BLUE, BLUE_BG,
                "Impact des anomalies détectées",
                "Variation du score de satisfaction autour de chaque période anormale détectée automatiquement.",
                make_impact_native(events_impact),
            ),
            html.Div([
                html.Div([
                    html.Div(
                        html.I(className="fas fa-list-ul",
                               style={"fontSize": "13px", "color": BLUE}),
                        className="at-card-icon", style={"background": BLUE_BG},
                    ),
                    html.Span("Détail des anomalies", className="at-card-title"),
                ], className="at-card-header"),
                html.Div(make_event_list(events_impact), className="at-card-body"),
            ], className="at-chart-card"),
        ], className="at-row-2col"),

        html.Div([
            _chart_card(
                "fas fa-chart-bar", BLUE, GREEN_BG,
                "Répartition des avis par heure",
                "Proportion satisfaits / insatisfaits par tranche horaire.",
                dcc.Graph(
                    figure=make_hourly_stacked(df_hourly, theme),
                    config={"displayModeBar": False},
                    style={"width": "100%", "height": "280px"},
                ),
            ),
            _chart_card(
                "fas fa-inbox", BLUE, BLUE_BG,
                "Volume de messages reçus par heure",
                "Nombre total de messages clients reçus par tranche horaire.",
                dcc.Graph(
                    figure=make_volume_bars(df_hourly, theme),
                    config={"displayModeBar": False},
                    style={"width": "100%", "height": "280px"},
                ),
            ),
        ], className="at-row-equal"),

        html.Div([
            _chart_card(
                "fas fa-table-list", BLUE, BLUE_BG,
                evol_title,
                evol_tooltip,
                make_weekly_table(df_weekly, theme),
            ),
            _chart_card(
                "fas fa-clock-rotate-left", BLUE, BLUE_BG,
                "Score de satisfaction par heure",
                "Courbe du score moyen de satisfaction heure par heure.",
                dcc.Graph(
                    figure=make_hourly_line(df_hourly, theme),
                    config={"displayModeBar": False},
                    style={"width": "100%", "height": "280px"},
                ),
            ),
        ], className="at-row-equal"),

    ], className="at-analytics-page", **{"data-theme": theme})

    return make_page_layout(
        "analytics", "Analyse Temporelle", sub_with_live, content, theme, user_data
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 9. DASH LAYOUT + CALLBACKS
#
# RÈGLE CLÉ : Tout ID utilisé dans Input/Output doit exister dans le layout
# statique. Les boutons de période sont dans full-analytics-layout (dynamique),
# donc ils ne peuvent PAS être dans Output (styles) — on gère leur style via
# le store et la fonction render_analytics_page.
#
# ✅ Un seul callback principal avec prevent_initial_call=False
# ✅ Un callback pour le store de période (boutons → store)
# ✅ Aucun btn-analytics-refresh dans les callbacks
# ═══════════════════════════════════════════════════════════════════════════════

layout = html.Div(
    id="analytics-wrapper",
    **{"data-theme": "light"},
    children=[
        dcc.Store(id="periode-analytics-store", data="global", storage_type="session"),
        dcc.Interval(id="refresh-interval-analytics", interval=300_000, n_intervals=0),
        html.Div(id="full-analytics-layout"),
    ],
)


# ── Callback 1 : boutons → mise à jour du store ───────────────────────────────
# Les boutons (btn-periode-analytics-*) sont générés dynamiquement dans
# render_analytics_page → make_periode_filter. Dash les accepte en Input car
# ils sont présents dans le DOM au moment des clics (page déjà chargée).
# En revanche ils ne peuvent PAS être en Output car ils n'existent pas encore
# lors de l'enregistrement des callbacks.
@callback(
    Output("periode-analytics-store", "data"),
    Input("btn-periode-analytics-global", "n_clicks"),
    Input("btn-periode-analytics-mois",   "n_clicks"),
    Input("btn-periode-analytics-jour",   "n_clicks"),
    State("periode-analytics-store",      "data"),
    prevent_initial_call=True,
)
def set_analytics_periode(n_global, n_mois, n_jour, current_periode):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    btn = ctx.triggered[0]["prop_id"].split(".")[0]

    if btn == "btn-periode-analytics-mois":
        return "mois"
    elif btn == "btn-periode-analytics-jour":
        return "jour"
    else:
        return "global"


# ── Callback 2 : rendu principal ──────────────────────────────────────────────
# prevent_initial_call=False → charge la page au premier rendu (remplace
# l'ancien init_analytics_page qui causait le conflit).
# Les styles des boutons sont gérés directement dans make_periode_filter via
# active_periode — pas besoin de les mettre en Output ici.
@callback(
    Output("full-analytics-layout", "children"),
    Output("analytics-wrapper",     "data-theme"),
    Input("theme-store",             "data"),
    Input("auth-store",              "data"),
    Input("periode-analytics-store", "data"),
    Input("refresh-interval-analytics", "n_intervals"),
    prevent_initial_call=False,
)
def update_analytics_page(theme, auth_data, periode, n_intervals):
    theme   = theme   or "light"
    periode = periode or "global"
    user_data = None
    if auth_data and auth_data.get("is_authenticated"):
        user_data = auth_data.get("user", {})
    return render_analytics_page(theme, user_data, periode), theme
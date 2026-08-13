# # # """ themes_temporal.py — REFONTE UI/UX PROFESSIONNELLE
# # # ✅ Grille 3×2 (3 lignes, 2 colonnes)
# # # ✅ Style Power BI / Desktop
# # # ✅ Date placée à droite
# # # ✅ Pas d'emoji, uniquement icônes FontAwesome
# # # ✅ Couleurs Algérie Télécom (#003087, #00a854, #e8384f, #f59e0b)
# # # """

# # # import dash
# # # from dash import html, dcc, callback, Input, Output, State
# # # import plotly.graph_objects as go
# # # import pandas as pd
# # # import numpy as np
# # # import sys, os, re, json
# # # from collections import Counter
# # # from datetime import datetime

# # # sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# # # from components import make_page_layout
# # # from database import MONGO_AVAILABLE, _col

# # # dash.register_page(__name__, path='/themes-temporal', name='Thèmes & Temporel')

# # # # ============================================================
# # # # MAPPINGS
# # # # ============================================================

# # # THEME_MAPPING = {
# # #     "reseau":       "Réseau Technique",
# # #     "technique":    "Problèmes Techniques",
# # #     "service":      "Service Client",
# # #     "client":       "Service Client",
# # #     "attente":      "Délais d'attente",
# # #     "prix":         "Tarifs",
# # #     "facture":      "Facturation",
# # #     "produit":      "Qualité Produit",
# # #     "offre":        "Offres Promo",
# # #     "hors_sujet":   "Hors Sujet",
# # #     "information":  "Information Générale",
# # #     "installation": "Installation",
# # #     "equipement":   "Équipement",
# # #     "saturation":   "Saturation Réseau",
# # #     "couverture":   "Couverture",
# # #     "debit":        "Débit Internet",
# # #     "autre":        "Autre",
# # # }

# # # REASON_MAPPING = {
# # #     "reseau":       "Réseau",
# # #     "service":      "Service Client",
# # #     "prix":         "Tarifs",
# # #     "attente":      "Attente",
# # #     "hors_sujet":   "Hors Sujet",
# # #     "installation": "Installation",
# # #     "facture":      "Facturation",
# # #     "saturation":   "Saturation",
# # #     "couverture":   "Couverture",
# # #     "autre":        "Autre",
# # #     "technique":    "Technique",
# # #     "produit":      "Produit",
# # # }

# # # STOPWORDS = {
# # #     "le","la","les","un","une","des","du","de","et","ou","mais","donc","or","ni","car",
# # #     "je","tu","il","elle","on","nous","vous","ils","elles","me","te","se","ce","cet",
# # #     "cette","ces","mon","ton","son","notre","votre","leur","que","qui","quoi","dont",
# # #     "est","sont","être","avoir","faire","dire","aller","voir","pouvoir","vouloir",
# # #     "a","dans","pour","par","avec","sans","sur","sous","entre","très","trop",
# # #     "peu","fort","bien","mal","oui","non","ainsi","plus","pas","tout","ça","si","ya",
# # #     "ال","و","في","من","على","إلى","ب","عن","مع","ما","هذا","هذه","ذلك","تلك",
# # #     "كان","كانت","يكون","أن","إن","أنه","لأن","حتى","إذا","فقد","قد","هل","أين",
# # #     "لم","لن","له","لها","لهم","لهن","هو","هي","هم","هن",
# # # }

# # # # ============================================================
# # # # COULEURS
# # # # ============================================================

# # # def _colors(theme):
# # #     if theme == "dark":
# # #         return {
# # #             "bg": "#141c2e", "paper_bg": "#1a2540", "text": "#dce8f5",
# # #             "grid": "#1e2d47", "primary": "#4a80d4", "success": "#2ecc71",
# # #             "danger": "#f06070", "warning": "#f39c12", "neutral": "#607b99",
# # #             "secondary": "#6c8dcc", "blue_light": "#8ab8e4", "blue_dark": "#2c5f8a",
# # #         }
# # #     return {
# # #         "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
# # #         "grid": "#e8edf5", "primary": "#003087", "success": "#00a854",
# # #         "danger": "#e8384f", "warning": "#f59e0b", "neutral": "#64748b",
# # #         "secondary": "#1a4fa0", "blue_light": "#4a80d4", "blue_dark": "#1a4a8a",
# # #     }


# # # def _base_layout(c, height, margin=None):
# # #     m = margin or dict(l=10, r=10, t=20, b=10)
# # #     return dict(
# # #         plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
# # #         font=dict(color=c["text"], family="'Segoe UI', 'DM Sans', sans-serif", size=10),
# # #         height=height, margin=m,
# # #     )


# # # BLUE_PALETTE_LIGHT = ["#003087","#1a4fa0","#2d66bb","#4a80d4","#6c8dcc","#8ab8e4"]
# # # BLUE_PALETTE_DARK  = ["#4a80d4","#6a9ae0","#8ab8e4","#5a8ed8","#7aaae0","#3a6fc4"]


# # # # ============================================================
# # # # EXTRACTION MONGODB
# # # # ============================================================

# # # def get_anomaly_data():
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return pd.DataFrame()
# # #     try:
# # #         pipeline = [
# # #             {"$match": {"sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]}, "mois": {"$exists": True}}},
# # #             {"$group": {
# # #                 "_id": "$mois",
# # #                 "avg_score": {"$avg": "$sentiment_score"},
# # #                 "total": {"$sum": 1},
# # #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# # #                 "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
# # #             }},
# # #             {"$sort": {"_id": 1}},
# # #         ]
# # #         results = list(_col.aggregate(pipeline))
# # #         if not results:
# # #             return pd.DataFrame()
# # #         df = pd.DataFrame([{
# # #             "mois": r["_id"],
# # #             "avg_score": round(r["avg_score"],3),
# # #             "total": r["total"],
# # #             "neg_pct": round(r["neg_pct"]*100,1),
# # #             "frustration_pct": round(r["frustration_pct"]*100,1),
# # #         } for r in results])
# # #         if len(df) > 2:
# # #             mean_s = df["avg_score"].mean()
# # #             std_s  = df["avg_score"].std()
# # #             if std_s > 0:
# # #                 df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
# # #                 df["anomaly_severity"] = np.where(
# # #                     df["avg_score"] < (mean_s - 2*std_s), "critical",
# # #                     np.where(df["is_anomaly"], "high", "normal")
# # #                 )
# # #             else:
# # #                 df["is_anomaly"] = False
# # #                 df["anomaly_severity"] = "normal"
# # #         return df
# # #     except Exception as e:
# # #         print(f"Erreur get_anomaly_data: {e}")
# # #         return pd.DataFrame()


# # # def get_lda_topics():
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return []
# # #     try:
# # #         pipeline = [
# # #             {"$match": {"theme_pred": {"$exists": True, "$ne": None}}},
# # #             {"$group": {
# # #                 "_id": "$theme_pred",
# # #                 "count": {"$sum": 1},
# # #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# # #                 "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
# # #             }},
# # #             {"$sort": {"count": -1}},
# # #             {"$limit": 8},
# # #         ]
# # #         results = list(_col.aggregate(pipeline))
# # #         keywords_map = {
# # #             "reseau":       ["reseau","connexion","4g","internet","signal"],
# # #             "service":      ["service","client","accueil","conseiller","support"],
# # #             "prix":         ["prix","tarif","forfait","cher","abonnement"],
# # #             "hors_sujet":   ["general","information","actualite","annonce"],
# # #             "installation": ["installation","technicien","rdv","delai","pose"],
# # #             "facture":      ["facture","paiement","montant","recu","payer"],
# # #             "saturation":   ["saturation","debit","lent","connexion"],
# # #             "couverture":   ["couverture","zone","antenne","signal"],
# # #             "autre":        ["divers","autre","general"],
# # #             "technique":    ["technique","probleme","bug","erreur","panne"],
# # #             "produit":      ["produit","qualite","equipement","modem","box"],
# # #             "attente":      ["attente","delai","long","patienter","lent"],
# # #         }
# # #         topics = []
# # #         for r in results:
# # #             theme = r["_id"]
# # #             if not theme:
# # #                 continue
# # #             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
# # #             kw = keywords_map.get(theme.lower(), [theme_fr])
# # #             topics.append({
# # #                 "name": theme_fr,
# # #                 "keywords": kw[:4],
# # #                 "count": r["count"],
# # #                 "neg_pct": round(r["neg_pct"]*100,1),
# # #                 "pos_pct": round(r["pos_pct"]*100,1),
# # #             })
# # #         return topics
# # #     except Exception as e:
# # #         print(f"Erreur get_lda_topics: {e}")
# # #         return []


# # # def get_wordcloud_data():
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return []
# # #     try:
# # #         pipeline = [
# # #             {"$match": {"commentaire_normalized": {"$exists": True, "$ne": ""}}},
# # #             {"$limit": 8000},
# # #             {"$project": {"commentaire_normalized": 1}},
# # #         ]
# # #         results = list(_col.aggregate(pipeline))
# # #         if not results:
# # #             return []
# # #         words = []
# # #         for r in results:
# # #             text = r.get("commentaire_normalized","")
# # #             if not text:
# # #                 continue
# # #             text = text.lower()
# # #             text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
# # #             text = re.sub(r'\d+','',text)
# # #             for word in text.split():
# # #                 word = word.strip()
# # #                 if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
# # #                     words.append(word)
# # #         if not words:
# # #             return []
# # #         wc = Counter(words)
# # #         top = wc.most_common(60)
# # #         return [{"word": w, "count": c} for w,c in top]
# # #     except Exception as e:
# # #         print(f"Erreur get_wordcloud_data: {e}")
# # #         return []


# # # def get_monthly_frequency():
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return pd.DataFrame()
# # #     try:
# # #         pipeline = [
# # #             {"$match": {"theme_pred": {"$exists": True,"$ne": None}, "mois": {"$exists": True}}},
# # #             {"$group": {"_id": {"mois":"$mois","theme":"$theme_pred"}, "count": {"$sum": 1}}},
# # #             {"$sort": {"_id.mois": 1}},
# # #         ]
# # #         results = list(_col.aggregate(pipeline))
# # #         if not results:
# # #             return pd.DataFrame()
# # #         data = []
# # #         for r in results:
# # #             theme = r["_id"]["theme"]
# # #             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
# # #             data.append({"mois": r["_id"]["mois"], "theme": theme_fr, "count": r["count"]})
# # #         df = pd.DataFrame(data)
# # #         top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
# # #         return df[df["theme"].isin(top6)]
# # #     except Exception as e:
# # #         print(f"Erreur get_monthly_frequency: {e}")
# # #         return pd.DataFrame()


# # # def get_reason_distribution():
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return pd.DataFrame()
# # #     try:
# # #         pipeline = [
# # #             {"$match": {"reason_pred": {"$exists": True, "$ne": None}}},
# # #             {"$group": {
# # #                 "_id": "$reason_pred",
# # #                 "count": {"$sum": 1},
# # #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# # #                "confiance": {"$avg": "$sentiment_confiance"}, 
# # #             }},
# # #             {"$sort": {"count": -1}},
# # #             {"$limit": 10},
# # #         ]
# # #         results = list(_col.aggregate(pipeline))
# # #         if not results:
# # #             return pd.DataFrame()
# # #         total = sum(r["count"] for r in results)
# # #         data = [{
# # #             "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
# # #             "count": r["count"],
# # #             "pct": round(r["count"]/total*100,1),
# # #             "neg_pct": round(r["neg_pct"]*100,1),
# # #             "confiance": round((r["confiance"] or 0)*100,1),
# # #         } for r in results]
# # #         return pd.DataFrame(data)
# # #     except Exception as e:
# # #         print(f"Erreur get_reason_distribution: {e}")
# # #         return pd.DataFrame()


# # # # ============================================================
# # # # GRAPHIQUES
# # # # ============================================================

# # # def make_reasons_donut(df, theme="light"):
# # #     c = _colors(theme)
# # #     if df.empty:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
# # #                            font=dict(color=c["neutral"]))
# # #         fig.update_layout(**_base_layout(c, 280))
# # #         return fig

# # #     palette = (BLUE_PALETTE_DARK if theme=="dark" else BLUE_PALETTE_LIGHT)[:len(df)]

# # #     fig = go.Figure(go.Pie(
# # #         labels=df["reason"],
# # #         values=df["count"],
# # #         hole=0.55,
# # #         marker=dict(colors=palette, line=dict(color=c["bg"], width=2)),
# # #         textinfo="label+percent",
# # #         textposition="outside",
# # #         textfont=dict(size=9, color=c["text"]),
# # #         hovertemplate="<b>%{label}</b><br>Volume: %{value:,}<br>Part: %{percent}<br>Insatisfaction: %{customdata}%<extra></extra>",
# # #         customdata=df["neg_pct"],
# # #         pull=[0.03 if i == 0 else 0 for i in range(len(df))],
# # #         sort=False,
# # #         direction="clockwise",
# # #     ))

# # #     layout = _base_layout(c, 280, margin=dict(l=10, r=80, t=30, b=30))
# # #     layout.update(
# # #         showlegend=True,
# # #         legend=dict(
# # #             orientation="v",
# # #             x=1.02,
# # #             y=0.5,
# # #             xanchor="left",
# # #             yanchor="middle",
# # #             font=dict(size=9, color=c["text"]),
# # #             bgcolor="rgba(0,0,0,0)",
# # #             borderwidth=0,
# # #         ),
# # #         annotations=[dict(
# # #             text=f"<b>{df['count'].sum():,}</b><br><span style='font-size:8px'>messages</span>",
# # #             x=0.5, y=0.5,
# # #             font=dict(size=12, color=c["primary"]),
# # #             showarrow=False,
# # #         )],
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # def make_reasons_bar(df, theme="light"):
# # #     c = _colors(theme)
# # #     if df.empty:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
# # #                            font=dict(color=c["neutral"]))
# # #         fig.update_layout(**_base_layout(c, 280))
# # #         return fig

# # #     df_sorted = df.sort_values("neg_pct", ascending=True).copy()

# # #     bar_colors = []
# # #     for p in df_sorted["neg_pct"]:
# # #         if p >= 60:
# # #             bar_colors.append(c["danger"])
# # #         elif p >= 40:
# # #             bar_colors.append(c["warning"])
# # #         else:
# # #             bar_colors.append(c["success"])

# # #     fig = go.Figure()
# # #     fig.add_trace(go.Bar(
# # #         y=df_sorted["reason"],
# # #         x=df_sorted["neg_pct"],
# # #         orientation="h",
# # #         width=0.65,
# # #         marker=dict(
# # #             color=bar_colors,
# # #             line=dict(width=0),
# # #             cornerradius=4,
# # #         ),
# # #         text=[f"{p:.0f}%" for p in df_sorted["neg_pct"]],
# # #         textposition="outside",
# # #         textfont=dict(size=9, weight="bold"),
# # #         hovertemplate="<b>%{y}</b><br>Insatisfaction: %{x:.1f}%<br>Volume: %{customdata:,}<extra></extra>",
# # #         customdata=df_sorted["count"],
# # #     ))

# # #     fig.add_vline(x=60, line_dash="dash", line_color=c["danger"], line_width=1.5, opacity=0.7)
# # #     fig.add_vline(x=40, line_dash="dot",  line_color=c["warning"], line_width=1, opacity=0.6)

# # #     layout = _base_layout(c, 280, margin=dict(l=100, r=50, t=20, b=20))
# # #     layout.update(
# # #         xaxis=dict(
# # #             ticksuffix="%", range=[0, 110],
# # #             showgrid=True, gridcolor=c["grid"],
# # #             zeroline=False,
# # #         ),
# # #         yaxis=dict(showgrid=False),
# # #         showlegend=False,
# # #         bargap=0.3,
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # def make_anomaly_chart(df, theme="light"):
# # #     c = _colors(theme)
# # #     if df.empty:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnee mensuelle", x=0.5, y=0.5,
# # #                            showarrow=False, font=dict(color=c["neutral"]))
# # #         fig.update_layout(**_base_layout(c, 240))
# # #         return fig

# # #     fig = go.Figure()
# # #     r,g,b_ = int(c["primary"][1:3],16), int(c["primary"][3:5],16), int(c["primary"][5:7],16)
# # #     fig.add_trace(go.Scatter(
# # #         x=df["mois"], y=df["avg_score"],
# # #         mode="lines+markers",
# # #         name="Score satisfaction",
# # #         line=dict(color=c["primary"], width=2.5),
# # #         fill="tozeroy",
# # #         fillcolor=f"rgba({r},{g},{b_},0.08)",
# # #         marker=dict(size=8, color=c["primary"], line=dict(color=c["bg"], width=2)),
# # #         hovertemplate="Mois: %{x}<br>Score: %{y:.3f}<br>Insatisfaits: %{customdata:.1f}%<extra></extra>",
# # #         customdata=df["neg_pct"],
# # #     ))

# # #     if "is_anomaly" in df.columns:
# # #         anom = df[df["is_anomaly"]]
# # #         if not anom.empty:
# # #             fig.add_trace(go.Scatter(
# # #                 x=anom["mois"], y=anom["avg_score"],
# # #                 mode="markers",
# # #                 marker=dict(symbol="x", size=12, color=c["danger"],
# # #                             line=dict(width=2, color="white")),
# # #                 name="Mois degradé",
# # #                 hovertemplate="ALERTE — %{x}<br>Score: %{y:.3f}<extra></extra>",
# # #             ))

# # #     mean_s = df["avg_score"].mean()
# # #     fig.add_hline(y=mean_s, line_dash="dash", line_color=c["neutral"], opacity=0.5)

# # #     layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
# # #     layout.update(
# # #         xaxis=dict(title="Mois", tickangle=-30, tickfont=dict(size=8), nticks=6),
# # #         yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False),
# # #         legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=8)),
# # #         hovermode="x unified",
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # def make_monthly_frequency_chart(df, theme="light"):
# # #     c = _colors(theme)
# # #     multi_palette = [c["primary"], c["danger"], c["warning"], c["success"], "#6c5ce7", "#00cec9"]
# # #     if df.empty:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5,
# # #                            showarrow=False, font=dict(color=c["neutral"]))
# # #         fig.update_layout(**_base_layout(c, 240))
# # #         return fig

# # #     fig = go.Figure()
# # #     for i, th in enumerate(df["theme"].unique()):
# # #         sub = df[df["theme"] == th].sort_values("mois")
# # #         fig.add_trace(go.Scatter(
# # #             x=sub["mois"], y=sub["count"],
# # #             mode="lines+markers",
# # #             name=th,
# # #             line=dict(width=1.5, color=multi_palette[i % len(multi_palette)]),
# # #             marker=dict(size=5),
# # #             hovertemplate="<b>%{fullData.name}</b><br>Mois: %{x}<br>Messages: %{y:,}<extra></extra>",
# # #         ))

# # #     layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
# # #     layout.update(
# # #         xaxis=dict(title="Mois", tickangle=-30, tickfont=dict(size=8), nticks=6),
# # #         yaxis=dict(title="Messages", tickformat=","),
# # #         legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=7)),
# # #         hovermode="x unified",
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # # ============================================================
# # # # WORDCLOUD
# # # # ============================================================

# # # def make_wordcloud_iframe(word_data, theme="light"):
# # #     if not word_data:
# # #         return html.Div([
# # #             html.I(className="fas fa-cloud",
# # #                    style={"fontSize":"28px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
# # #             html.P("Aucune donnee textuelle",
# # #                    style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
# # #         ], style={"textAlign":"center","padding":"30px","display":"flex",
# # #                   "flexDirection":"column","alignItems":"center"})

# # #     bg_color = "#1a2540" if theme == "dark" else "#ffffff"
# # #     max_c = max(w["count"] for w in word_data)
# # #     min_c = min(w["count"] for w in word_data)
# # #     rng   = max_c - min_c if max_c != min_c else 1

# # #     words_js = json.dumps([
# # #         [w["word"], round(10 + (w["count"] - min_c) / rng * 58)]
# # #         for w in word_data
# # #     ])

# # #     colors_light = ["#003087","#1a4fa0","#4a80d4","#e8384f","#f59e0b","#00a854","#6c8dcc"]
# # #     colors_dark  = ["#4a80d4","#6a9ae0","#8ab8e4","#2ecc71","#f06070","#f39c12","#a78bfa"]
# # #     colors_js = json.dumps(colors_dark if theme == "dark" else colors_light)

# # #     html_content = f"""<!DOCTYPE html>
# # # <html><head><meta charset="utf-8">
# # # <style>
# # #   *{{margin:0;padding:0;box-sizing:border-box}}
# # #   body{{background:{bg_color};width:100%;height:100%;overflow:hidden;
# # #         display:flex;align-items:center;justify-content:center}}
# # #   #wc{{width:100%;height:100%;display:block}}
# # # </style>
# # # <script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js"></script>
# # # </head><body>
# # # <canvas id="wc"></canvas>
# # # <script>
# # #   var words={words_js};
# # #   var colors={colors_js};
# # #   var ci=0;
# # #   function init(){{
# # #     var c=document.getElementById('wc');
# # #     var W=window.innerWidth||600,H=window.innerHeight||320;
# # #     c.width=W;c.height=H;
# # #     WordCloud(c,{{
# # #       list:words,
# # #       gridSize:Math.round(6*W/700),
# # #       weightFactor:function(s){{return s*(W/600)}},
# # #       fontFamily:"'Segoe UI','DM Sans',sans-serif",
# # #       color:function(){{return colors[(ci++)%colors.length]}},
# # #       rotateRatio:0.3,rotationSteps:3,
# # #       backgroundColor:'{bg_color}',
# # #       shuffle:true,drawOutOfBound:false,shrinkToFit:true,minSize:8,
# # #     }});
# # #   }}
# # #   if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
# # #   else init();
# # #   window.addEventListener('resize',function(){{setTimeout(init,100)}});
# # # </script>
# # # </body></html>"""

# # #     return html.Iframe(
# # #         srcDoc=html_content,
# # #         style={
# # #             "width": "100%",
# # #             "height": "340px",
# # #             "border": "none",
# # #             "borderRadius": "8px",
# # #             "background": bg_color,
# # #             "display": "block",
# # #         },
# # #     )


# # # # ============================================================
# # # # COMPOSANTS HTML
# # # # ============================================================

# # # def make_anomaly_banner(anomaly_df):
# # #     no_anomaly = (
# # #         anomaly_df.empty
# # #         or "is_anomaly" not in anomaly_df.columns
# # #         or int(anomaly_df["is_anomaly"].sum()) == 0
# # #     )

# # #     if no_anomaly:
# # #         return html.Div(
# # #             id="tt-anomaly-banner",
# # #             children=[
# # #                 html.Div([
# # #                     html.I(className="fas fa-check-circle",
# # #                            style={"fontSize":"12px","color":"var(--tt-green, #04723b)",
# # #                                   "marginRight":"8px","flexShrink":"0"}),
# # #                     html.Strong("Aucune anomalie détectée", style={"fontSize":"10px"}),
# # #                 ], style={"display":"flex","alignItems":"center","flex":"1"}),
# # #                 html.Button(
# # #                     html.I(className="fas fa-times", style={"fontSize":"9px"}),
# # #                     id="close-anomaly-banner-btn", n_clicks=0,
# # #                     style={"background":"transparent","border":"none",
# # #                            "color":"var(--tt-green, #00a854)",
# # #                            "cursor":"pointer","padding":"2px 5px",
# # #                            "borderRadius":"4px","flexShrink":"0"},
# # #                 ),
# # #             ],
# # #             style={
# # #                 "display":"flex","alignItems":"center","justifyContent":"space-between",
# # #                 "padding":"6px 12px","borderRadius":"8px",
# # #                 "background":"rgba(0,168,84,0.07)","border":"1px solid rgba(0,168,84,0.18)",
# # #                 "marginBottom":"8px",
# # #             },
# # #         )

# # #     n_anom = int(anomaly_df["is_anomaly"].sum())
# # #     n_crit = int((anomaly_df.get("anomaly_severity", pd.Series([])) == "critical").sum()) \
# # #              if "anomaly_severity" in anomaly_df.columns else 0
# # #     txt = f"{n_anom} mois anormalement dégradé(s)" + (f" (dont {n_crit} critique)" if n_crit else "")

# # #     return html.Div(
# # #         id="tt-anomaly-banner",
# # #         children=[
# # #             html.Div([
# # #                 html.I(className="fas fa-exclamation-triangle",
# # #                        style={"fontSize":"12px","color":"var(--tt-red, #e8384f)",
# # #                               "marginRight":"8px","flexShrink":"0"}),
# # #                 html.Strong(txt, style={"fontSize":"10px"}),
# # #             ], style={"display":"flex","alignItems":"center","flex":"1"}),
# # #             html.Button(
# # #                 html.I(className="fas fa-times", style={"fontSize":"9px"}),
# # #                 id="close-anomaly-banner-btn", n_clicks=0,
# # #                 style={"background":"transparent","border":"none",
# # #                        "color":"var(--tt-red, #e8384f)",
# # #                        "cursor":"pointer","padding":"2px 5px",
# # #                        "borderRadius":"4px","flexShrink":"0"},
# # #             ),
# # #         ],
# # #         style={
# # #             "display":"flex","alignItems":"center","justifyContent":"space-between",
# # #             "padding":"6px 12px","borderRadius":"8px",
# # #             "background":"rgba(232,56,79,0.07)","border":"1px solid rgba(232,56,79,0.18)",
# # #             "marginBottom":"8px",
# # #         },
# # #     )


# # # def make_topics_list(topics, theme="light"):
# # #     if not topics:
# # #         return html.Div([
# # #             html.I(className="fas fa-tags",
# # #                    style={"fontSize":"24px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
# # #             html.P("Aucun thème détecté",
# # #                    style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
# # #         ], style={"textAlign":"center","padding":"30px","display":"flex",
# # #                   "flexDirection":"column","alignItems":"center"})

# # #     c = _colors(theme)
# # #     items = []
# # #     for t in topics:
# # #         if t["neg_pct"] > 60:
# # #             neg_col   = c["danger"]
# # #             badge_cls = "tt-badge-crit"
# # #             badge_txt = "Critique"
# # #         elif t["neg_pct"] > 40:
# # #             neg_col   = c["warning"]
# # #             badge_cls = "tt-badge-warn"
# # #             badge_txt = "Alerte"
# # #         else:
# # #             neg_col   = c["success"]
# # #             badge_cls = "tt-badge-ok"
# # #             badge_txt = "Normal"

# # #         items.append(html.Div([
# # #             html.Div([
# # #                 html.Div(style={
# # #                     "width":"5px","height":"5px","borderRadius":"50%",
# # #                     "background":neg_col,"flexShrink":"0",
# # #                 }),
# # #                 html.Span(t["name"], style={
# # #                     "fontSize":"10px","fontWeight":"600",
# # #                     "color":"var(--tt-text, #1a2a4a)","flex":"1",
# # #                 }),
# # #                 html.Span(badge_txt, className=f"tt-badge {badge_cls}"),
# # #             ], style={"display":"flex","alignItems":"center","gap":"6px","marginBottom":"4px"}),

# # #             html.Div([
# # #                 html.I(className="fas fa-comment-dots",
# # #                        style={"fontSize":"8px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
# # #                 html.Span(f"{t['count']:,} messages",
# # #                           style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
# # #                 html.Span(" · ", style={"color":"var(--tt-border, #ccc)","margin":"0 3px"}),
# # #                 html.Span(f"{t['neg_pct']}% insatisfaits",
# # #                           style={"fontSize":"8px","color":neg_col,"fontWeight":"600"}),
# # #             ], style={"display":"flex","alignItems":"center","flexWrap":"wrap","marginBottom":"4px"}),

# # #             html.Div([
# # #                 html.I(className="fas fa-key",
# # #                        style={"fontSize":"7px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
# # #                 html.Span("Mots-clés : ",
# # #                           style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
# # #                 html.Span(", ".join(t["keywords"][:3]),
# # #                           style={"fontSize":"8px","fontWeight":"500",
# # #                                  "color":"var(--tt-text, #1a2a4a)"}),
# # #             ], style={"display":"flex","alignItems":"center","marginBottom":"5px","flexWrap":"wrap"}),

# # #             html.Div(
# # #                 html.Div(style={
# # #                     "height":"100%","width":f"{min(t['neg_pct'],100)}%",
# # #                     "background":neg_col,"borderRadius":"2px",
# # #                     "transition":"width 0.4s ease",
# # #                 }),
# # #                 className="tt-topic-bar-track",
# # #             ),
# # #         ], className="tt-topic-item"))

# # #     return html.Div(items, className="tt-topics-list")


# # # # ============================================================
# # # # HELPER : carte générique pour grille 3x2
# # # # ============================================================

# # # def _chart_card(icon, title, tooltip_title, tooltip_body, children, icon_variant=""):
# # #     icon_cls = "card-icon"
# # #     if icon_variant:
# # #         icon_cls += f" card-icon--{icon_variant}"

# # #     return html.Div([
# # #         html.Div([
# # #             html.Div([html.I(className=icon, style={"fontSize":"13px"})],
# # #                      className=icon_cls),
# # #             html.Span(title, className="card-title"),
# # #             html.Div([
# # #                 html.Div(
# # #                     html.I(className="fas fa-info-circle", style={"fontSize":"10px"}),
# # #                     className="tooltip-icon",
# # #                 ),
# # #                 html.Div([
# # #                     html.Div(tooltip_title, className="tooltip-title"),
# # #                     html.Div(tooltip_body,  className="tooltip-body"),
# # #                 ], className="card-tooltip"),
# # #             ], className="tooltip-wrapper"),
# # #         ], className="card-header"),
# # #         html.Div(children, className="card-content"),
# # #     ], className="chart-card", style={"padding":"14px 16px","borderRadius":"14px","height":"100%"})


# # # # ============================================================
# # # # CACHE
# # # # ============================================================

# # # _cache = {}

# # # def _get_data():
# # #     global _cache
# # #     if not _cache:
# # #         print("🔄 Chargement des données depuis MongoDB...")
        
# # #         # Récupération des données avec gestion d'erreur
# # #         anomaly_df = get_anomaly_data()
# # #         topics = get_lda_topics()
# # #         word_data = get_wordcloud_data()
# # #         monthly_df = get_monthly_frequency()
# # #         reason_df = get_reason_distribution()
        
# # #         # Vérification que monthly_df est bien un DataFrame
# # #         if monthly_df is None or monthly_df.empty:
# # #             print("⚠️ Aucune donnée mensuelle trouvée, création d'un DataFrame vide")
# # #             monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
        
# # #         if reason_df is None or reason_df.empty:
# # #             print("⚠️ Aucune donnée de raison trouvée, création d'un DataFrame vide")
# # #             reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
        
# # #         if anomaly_df is None or anomaly_df.empty:
# # #             print("⚠️ Aucune donnée d'anomalie trouvée, création d'un DataFrame vide")
# # #             anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])
        
# # #         _cache["anomaly_df"] = anomaly_df
# # #         _cache["topics"] = topics if topics else []
# # #         _cache["word_data"] = word_data if word_data else []
# # #         _cache["monthly_df"] = monthly_df
# # #         _cache["reason_df"] = reason_df
        
# # #         print(f"✅ Données chargées: monthly_df={len(monthly_df)} lignes, reason_df={len(reason_df)} lignes, topics={len(topics)}")
    
# # #     return _cache
# # # # ============================================================
# # # # LAYOUT (Grille 3×2 : 3 lignes, 2 colonnes)
# # # # ============================================================
# # # # ============================================================
# # # # LAYOUT (Grille 3×2 : 3 lignes, 2 colonnes)
# # # # ============================================================

# # # def render_page(theme="light", user_data=None):
# # #     print("Chargement Thèmes & Temporel — grille 3×2...")
# # #     d = _get_data()
# # #     t = theme
# # #     today = datetime.now().strftime("%d/%m/%Y")

# # #     content = html.Div(
# # #         className="dashboard-container themes-temporal-page",
# # #         **{"data-theme": theme, "data-page": "themes-temporal"},
# # #         children=[
# # #             # Header avec bannière et actions
# # #             html.Div(
# # #                 [
# # #                     # Bannière verte "Aucune anomalie détectée" (à gauche)
# # #                     html.Div(
# # #                         [
# # #                             html.I(
# # #                                 className="fas fa-check-circle",
# # #                                 style={
# # #                                     "fontSize": "14px",
# # #                                     "color": "#ffffff",
# # #                                     "marginRight": "10px",
# # #                                     "flexShrink": "0"
# # #                                 }
# # #                             ),
# # #                             html.Strong(
# # #                                 "Aucune anomalie détectée",
# # #                                 style={
# # #                                     "fontSize": "14px",
# # #                                     "fontWeight": "600",
# # #                                     "color": "#ffffff"
# # #                                 }
# # #                             ),
# # #                         ],
# # #                         style={
# # #                             "display": "flex",
# # #                             "alignItems": "center",
# # #                             "padding": "0 20px",
# # #                             "borderRadius": "8px",
# # #                             "background": "#04723b",
# # #                             "border": "1px solid #046635",
# # #                             "height": "40px",
# # #                             "width": "250px",
# # #                             "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
# # #                         }
# # #                     ),
# # #                     # Groupe droite : Date + Actualiser + Vider historique
# # #                     html.Div(
# # #                         [
# # #                             # Date badge
# # #                             html.Div(
# # #                                 [
# # #                                     html.I(
# # #                                         className="far fa-calendar-alt",
# # #                                         style={"marginRight": "5px", "fontSize": "13px"}
# # #                                     ),
# # #                                     html.Span(f"Mise à jour : {today}", style={"fontSize": "13px"}),
# # #                                 ],
# # #                                 className="date-badge",
# # #                                 style={
# # #                                     "display": "flex",
# # #                                     "alignItems": "center",
# # #                                     "background": "white",
# # #                                     "padding": "0 15px",
# # #                                     "borderRadius": "8px",
# # #                                     "height": "40px",
# # #                                     "border": "1px solid #e0e0e0",
# # #                                 }
# # #                             ),
# # #                             # Bouton Actualiser
# # #                             html.Button(
# # #                                 [
# # #                                     html.I(
# # #                                         className="fas fa-sync-alt",
# # #                                         style={"marginRight": "5px", "fontSize": "13px"}
# # #                                     ),
# # #                                     html.Span("Actualiser", style={"fontSize": "13px"}),
# # #                                 ],
# # #                                 id="tt-refresh-btn",
# # #                                 n_clicks=0,
# # #                                 style={
# # #                                     "background": "#003087",
# # #                                     "color": "white",
# # #                                     "border": "none",
# # #                                     "borderRadius": "8px",
# # #                                     "padding": "0 20px",
# # #                                     "cursor": "pointer",
# # #                                     "fontSize": "13px",
# # #                                     "display": "flex",
# # #                                     "alignItems": "center",
# # #                                     "height": "40px",
# # #                                     "gap": "8px",
# # #                                 },
# # #                             ),
# # #                             # Bouton Vider historique
                           
# # #                         ],
# # #                         style={"display": "flex", "gap": "12px", "alignItems": "center"}
# # #                     ),
# # #                 ],
# # #                 style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"}
# # #             ),

# # #             # ── Grille 3×2 (3 lignes, 2 colonnes) ───────────────────
# # #             html.Div(className="grid-3x2", children=[

# # #                 # LIGNE 1 : ÉVOLUTION MENSUELLE PAR THÈME | DÉTECTION DES ANOMALIES
# # #                 html.Div(className="grid-row", children=[
# # #                     _chart_card(
# # #                         "fas fa-chart-line", "ÉVOLUTION MENSUELLE PAR THÈME",
# # #                         "Fréquence mensuelle par sujet",
# # #                         "Evolution du nombre de messages par thème et par mois.",
# # #                         dcc.Graph(
# # #                             id="tt-monthly-chart",
# # #                             figure=make_monthly_frequency_chart(d["monthly_df"], theme),
# # #                             config={"displayModeBar": False},
# # #                             style={"height": "280px"},
# # #                         ),
# # #                         icon_variant="#ffffff",
# # #                     ),
# # #                     _chart_card(
# # #                         "fas fa-exclamation-triangle", "DÉTECTION DES ANOMALIES",
# # #                         "Anomalies de satisfaction",
# # #                         "Score de satisfaction mensuel. Les croix signalent des mois anormaux.",
# # #                         html.Div([
# # #                             html.Div(
# # #                                 id="tt-anomaly-banner-container",
# # #                                 children=make_anomaly_banner(d["anomaly_df"]),
# # #                             ),
# # #                             dcc.Graph(
# # #                                 id="tt-anomaly-chart",
# # #                                 figure=make_anomaly_chart(d["anomaly_df"], theme),
# # #                                 config={"displayModeBar": False},
# # #                                 style={"height": "250px"},
# # #                             ),
# # #                         ]),
# # #                         icon_variant="#ffffff",
# # #                     ),
# # #                 ]),
              
       


# # #                 # LIGNE 2 : TAUX D'INSATISFACTION | SUJETS LES PLUS ABORDÉS
# # #                 html.Div(className="grid-row", children=[
# # #                     _chart_card(
# # #                         "fas fa-chart-bar", "TAUX D'INSATISFACTION",
# # #                         "Raisons classées par criticité",
# # #                         "Les raisons sont triées du plus critique au moins critique.",
# # #                         dcc.Graph(
# # #                             id="tt-reasons-bar",
# # #                             figure=make_reasons_bar(d["reason_df"], theme),
# # #                             config={"displayModeBar": False},
# # #                             style={"height":"280px"},
# # #                         ),
# # #                         icon_variant="#ffffff",
# # #                     ),
# # #                     _chart_card(
# # #                         "fas fa-tags", "SUJETS LES PLUS ABORDÉS",
# # #                         "Thèmes principaux identifiés",
# # #                         "Catégories détectées automatiquement depuis les commentaires.",
# # #                         html.Div(
# # #                             id="tt-topics-list",
# # #                             children=make_topics_list(d["topics"], theme),
# # #                             style={"height":"280px","overflowY":"auto"},
# # #                         ),
# # #                         icon_variant="#ffffff",
# # #                     ),
# # #                 ]),

# # #                 # LIGNE 3 : RÉPARTITION DES RAISONS | VOCABULAIRE CLIENTS
# # #                 html.Div(className="grid-row", children=[
# # #                     _chart_card(
# # #                         "fas fa-chart-pie", "RÉPARTITION DES RAISONS",
# # #                         "Distribution des raisons détectées",
# # #                         "Répartition par volume des principales raisons détectées automatiquement.",
# # #                         dcc.Graph(
# # #                             id="tt-reasons-donut",
# # #                             figure=make_reasons_donut(d["reason_df"], theme),
# # #                             config={"displayModeBar": False},
# # #                             style={"height":"280px"},
# # #                         ),
# # #                         icon_variant="#ffffff",
# # #                     ),
# # #                     _chart_card(
# # #                         "fas fa-comment-dots", "VOCABULAIRE CLIENTS",
# # #                         "Nuage de mots",
# # #                         "Mots les plus utilisés dans les commentaires (français, arabe, darija).",
# # #                         html.Div(
# # #                             id="tt-wordcloud",
# # #                             children=make_wordcloud_iframe(d["word_data"], theme),
# # #                             style={"height":"280px"},
# # #                         ),
# # #                         icon_variant="#ffffff",
# # #                     ),
# # #                 ]),
# # #             ]),
# # #         ],
# # #     )

# # #     return make_page_layout(
# # #         "themes-temporal",
# # #         "Thèmes & Analyse Temporelle",
# # #         "Quels sujets génèrent le plus d'insatisfaction ? Quels mois ont été les plus difficiles ?",
# # #         content,
# # #         theme,
# # #         user_data,
# # #     )


# # # # ============================================================
# # # # CALLBACKS
# # # # ============================================================

# # # @callback(
# # #     Output("tt-anomaly-chart", "figure"),
# # #     Output("tt-monthly-chart", "figure"),
# # #     Output("tt-reasons-donut", "figure"),
# # #     Output("tt-reasons-bar",   "figure"),
# # #     Input("theme-store",  "data"),
# # #     Input("auth-store",   "data"),
# # # )
# # # def update_charts(theme, auth_data):
# # #     theme = theme or "light"
# # #     d = _get_data()
# # #     return (
# # #         make_anomaly_chart(d["anomaly_df"], theme),
# # #         make_monthly_frequency_chart(d["monthly_df"], theme),
# # #         make_reasons_donut(d["reason_df"], theme),
# # #         make_reasons_bar(d["reason_df"], theme),
# # #     )


# # # @callback(
# # #     Output("tt-wordcloud",   "children"),
# # #     Output("tt-topics-list", "children"),
# # #     Input("theme-store", "data"),
# # #     Input("auth-store",  "data"),
# # # )
# # # def update_wordcloud_and_topics(theme, auth_data):
# # #     theme = theme or "light"
# # #     d = _get_data()
# # #     return (
# # #         make_wordcloud_iframe(d["word_data"], theme),
# # #         make_topics_list(d["topics"], theme),
# # #     )


# # # @callback(
# # #     Output("tt-anomaly-banner-container", "children"),
# # #     Input("close-anomaly-banner-btn", "n_clicks"),
# # #     prevent_initial_call=True,
# # # )
# # # def close_anomaly_banner(n_clicks):
# # #     if n_clicks:
# # #         return None
# # #     return dash.no_update


# # # @callback(
# # #     Output("tt-page-content", "children"),
# # #     Input("theme-store", "data"),
# # #     Input("auth-store",  "data"),
# # # )
# # # def themes_page_with_auth(theme, auth_data):
# # #     theme = theme or "light"
# # #     user_data = None
# # #     if auth_data and auth_data.get("is_authenticated"):
# # #         user_data = auth_data.get("user", {})
# # #     return render_page(theme, user_data)


# # # @callback(
# # #     Output("tt-page-content", "children", allow_duplicate=True),
# # #     Input("tt-refresh-btn", "n_clicks"),
# # #     State("theme-store", "data"),
# # #     State("auth-store",  "data"),
# # #     prevent_initial_call=True,
# # # )
# # # def refresh_data(n_clicks, theme, auth_data):
# # #     """Vide le cache et recharge toutes les données."""
# # #     global _cache
# # #     if n_clicks and n_clicks > 0:
# # #         _cache = {}
# # #         theme = theme or "light"
# # #         user_data = None
# # #         if auth_data and auth_data.get("is_authenticated"):
# # #             user_data = auth_data.get("user", {})
# # #         return render_page(theme, user_data)
# # #     return dash.no_update


# # # # ============================================================
# # # # LAYOUT ENTRY POINT
# # # # ============================================================

# # # layout = html.Div(id="tt-page-content")


# # # @callback(
# # #     Output("tt-page-content", "children", allow_duplicate=True),
# # #     Input("_pages_location", "pathname"),
# # #     prevent_initial_call=True,
# # # )
# # # def init_themes_page(pathname):
# # #     if pathname == "/themes-temporal":
# # #         return render_page("light")
# # #     return dash.no_update
# # """ themes_temporal.py — REFONTE UI/UX PROFESSIONNELLE
# # ✅ Grille 3×2 (3 lignes, 2 colonnes)
# # ✅ Style Power BI / Desktop
# # ✅ Date placée à droite
# # ✅ Pas d'emoji, uniquement icônes FontAwesome
# # ✅ Couleurs Algérie Télécom (#003087, #00a854, #e8384f, #f59e0b)
# # ✅ Logique Global / Ce Mois (même logique que dashboard.py)
# # """

# # import dash
# # from dash import html, dcc, callback, Input, Output, State
# # import plotly.graph_objects as go
# # import pandas as pd
# # import numpy as np
# # import sys, os, re, json
# # from collections import Counter
# # from datetime import datetime, timedelta

# # sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# # from components import make_page_layout
# # from database import MONGO_AVAILABLE, _col

# # dash.register_page(__name__, path='/themes-temporal', name='Thèmes & Temporel')

# # # ============================================================
# # # CONSTANTES COULEURS
# # # ============================================================

# # BLUE       = "#003087"
# # BLUE_MID   = "#1a4fa0"
# # BLUE_LIGHT = "#e8f0fb"
# # GREEN      = "#00a854"
# # RED        = "#e8384f"
# # ORANGE     = "#f59e0b"
# # NEUTRAL    = "#64748b"

# # TZ_OFFSET = timedelta(hours=1)

# # def now_local():
# #     return datetime.utcnow() + TZ_OFFSET

# # # ============================================================
# # # MAPPINGS
# # # ============================================================

# # THEME_MAPPING = {
# #     "reseau":       "Réseau Technique",
# #     "technique":    "Problèmes Techniques",
# #     "service":      "Service Client",
# #     "client":       "Service Client",
# #     "attente":      "Délais d'attente",
# #     "prix":         "Tarifs",
# #     "facture":      "Facturation",
# #     "produit":      "Qualité Produit",
# #     "offre":        "Offres Promo",
# #     "hors_sujet":   "Hors Sujet",
# #     "information":  "Information Générale",
# #     "installation": "Installation",
# #     "equipement":   "Équipement",
# #     "saturation":   "Saturation Réseau",
# #     "couverture":   "Couverture",
# #     "debit":        "Débit Internet",
# #     "autre":        "Autre",
# # }

# # REASON_MAPPING = {
# #     "reseau":       "Réseau",
# #     "service":      "Service Client",
# #     "prix":         "Tarifs",
# #     "attente":      "Attente",
# #     "hors_sujet":   "Hors Sujet",
# #     "installation": "Installation",
# #     "facture":      "Facturation",
# #     "saturation":   "Saturation",
# #     "couverture":   "Couverture",
# #     "autre":        "Autre",
# #     "technique":    "Technique",
# #     "produit":      "Produit",
# # }

# # STOPWORDS = {
# #     "le","la","les","un","une","des","du","de","et","ou","mais","donc","or","ni","car",
# #     "je","tu","il","elle","on","nous","vous","ils","elles","me","te","se","ce","cet",
# #     "cette","ces","mon","ton","son","notre","votre","leur","que","qui","quoi","dont",
# #     "est","sont","être","avoir","faire","dire","aller","voir","pouvoir","vouloir",
# #     "a","dans","pour","par","avec","sans","sur","sous","entre","très","trop",
# #     "peu","fort","bien","mal","oui","non","ainsi","plus","pas","tout","ça","si","ya",
# #     "ال","و","في","من","على","إلى","ب","عن","مع","ما","هذا","هذه","ذلك","تلك",
# #     "كان","كانت","يكون","أن","إن","أنه","لأن","حتى","إذا","فقد","قد","هل","أين",
# #     "لم","لن","له","لها","لهم","لهن","هو","هي","هم","هن",
# # }

# # # ============================================================
# # # COULEURS THÈME
# # # ============================================================

# # def _colors(theme):
# #     if theme == "dark":
# #         return {
# #             "bg": "#141c2e", "paper_bg": "#1a2540", "text": "#dce8f5",
# #             "grid": "#1e2d47", "primary": "#4a80d4", "success": "#2ecc71",
# #             "danger": "#f06070", "warning": "#f39c12", "neutral": "#607b99",
# #             "secondary": "#6c8dcc", "blue_light": "#8ab8e4", "blue_dark": "#2c5f8a",
# #         }
# #     return {
# #         "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
# #         "grid": "#e8edf5", "primary": "#003087", "success": "#00a854",
# #         "danger": "#e8384f", "warning": "#f59e0b", "neutral": "#64748b",
# #         "secondary": "#1a4fa0", "blue_light": "#4a80d4", "blue_dark": "#1a4a8a",
# #     }


# # def _base_layout(c, height, margin=None):
# #     m = margin or dict(l=10, r=10, t=20, b=10)
# #     return dict(
# #         plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
# #         font=dict(color=c["text"], family="'Segoe UI', 'DM Sans', sans-serif", size=10),
# #         height=height, margin=m,
# #     )


# # BLUE_PALETTE_LIGHT = ["#003087","#1a4fa0","#2d66bb","#4a80d4","#6c8dcc","#8ab8e4"]
# # BLUE_PALETTE_DARK  = ["#4a80d4","#6a9ae0","#8ab8e4","#5a8ed8","#7aaae0","#3a6fc4"]


# # # ============================================================
# # # EXTRACTION MONGODB — GLOBAL
# # # ============================================================

# # def get_anomaly_data():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         pipeline = [
# #             {"$match": {"sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]}, "mois": {"$exists": True}}},
# #             {"$group": {
# #                 "_id": "$mois",
# #                 "avg_score": {"$avg": "$sentiment_score"},
# #                 "total": {"$sum": 1},
# #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# #                 "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         df = pd.DataFrame([{
# #             "mois": r["_id"],
# #             "avg_score": round(r["avg_score"],3),
# #             "total": r["total"],
# #             "neg_pct": round(r["neg_pct"]*100,1),
# #             "frustration_pct": round(r["frustration_pct"]*100,1),
# #         } for r in results])
# #         if len(df) > 2:
# #             mean_s = df["avg_score"].mean()
# #             std_s  = df["avg_score"].std()
# #             if std_s > 0:
# #                 df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
# #                 df["anomaly_severity"] = np.where(
# #                     df["avg_score"] < (mean_s - 2*std_s), "critical",
# #                     np.where(df["is_anomaly"], "high", "normal")
# #                 )
# #             else:
# #                 df["is_anomaly"] = False
# #                 df["anomaly_severity"] = "normal"
# #         return df
# #     except Exception as e:
# #         print(f"Erreur get_anomaly_data: {e}")
# #         return pd.DataFrame()


# # def get_lda_topics():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         pipeline = [
# #             {"$match": {"theme_pred": {"$exists": True, "$ne": None}}},
# #             {"$group": {
# #                 "_id": "$theme_pred",
# #                 "count": {"$sum": 1},
# #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# #                 "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
# #             }},
# #             {"$sort": {"count": -1}},
# #             {"$limit": 8},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         keywords_map = {
# #             "reseau":       ["reseau","connexion","4g","internet","signal"],
# #             "service":      ["service","client","accueil","conseiller","support"],
# #             "prix":         ["prix","tarif","forfait","cher","abonnement"],
# #             "hors_sujet":   ["general","information","actualite","annonce"],
# #             "installation": ["installation","technicien","rdv","delai","pose"],
# #             "facture":      ["facture","paiement","montant","recu","payer"],
# #             "saturation":   ["saturation","debit","lent","connexion"],
# #             "couverture":   ["couverture","zone","antenne","signal"],
# #             "autre":        ["divers","autre","general"],
# #             "technique":    ["technique","probleme","bug","erreur","panne"],
# #             "produit":      ["produit","qualite","equipement","modem","box"],
# #             "attente":      ["attente","delai","long","patienter","lent"],
# #         }
# #         topics = []
# #         for r in results:
# #             theme = r["_id"]
# #             if not theme:
# #                 continue
# #             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
# #             kw = keywords_map.get(theme.lower(), [theme_fr])
# #             topics.append({
# #                 "name": theme_fr,
# #                 "keywords": kw[:4],
# #                 "count": r["count"],
# #                 "neg_pct": round(r["neg_pct"]*100,1),
# #                 "pos_pct": round(r["pos_pct"]*100,1),
# #             })
# #         return topics
# #     except Exception as e:
# #         print(f"Erreur get_lda_topics: {e}")
# #         return []


# # def get_wordcloud_data():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         pipeline = [
# #             {"$match": {"commentaire_normalized": {"$exists": True, "$ne": ""}}},
# #             {"$limit": 8000},
# #             {"$project": {"commentaire_normalized": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return []
# #         words = []
# #         for r in results:
# #             text = r.get("commentaire_normalized","")
# #             if not text:
# #                 continue
# #             text = text.lower()
# #             text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
# #             text = re.sub(r'\d+','',text)
# #             for word in text.split():
# #                 word = word.strip()
# #                 if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
# #                     words.append(word)
# #         if not words:
# #             return []
# #         wc = Counter(words)
# #         top = wc.most_common(60)
# #         return [{"word": w, "count": c} for w,c in top]
# #     except Exception as e:
# #         print(f"Erreur get_wordcloud_data: {e}")
# #         return []


# # def get_monthly_frequency():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         pipeline = [
# #             {"$match": {"theme_pred": {"$exists": True,"$ne": None}, "mois": {"$exists": True}}},
# #             {"$group": {"_id": {"mois":"$mois","theme":"$theme_pred"}, "count": {"$sum": 1}}},
# #             {"$sort": {"_id.mois": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         data = []
# #         for r in results:
# #             theme = r["_id"]["theme"]
# #             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
# #             data.append({"mois": r["_id"]["mois"], "theme": theme_fr, "count": r["count"]})
# #         df = pd.DataFrame(data)
# #         top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
# #         return df[df["theme"].isin(top6)]
# #     except Exception as e:
# #         print(f"Erreur get_monthly_frequency: {e}")
# #         return pd.DataFrame()


# # def get_reason_distribution():
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         pipeline = [
# #             {"$match": {"reason_pred": {"$exists": True, "$ne": None}}},
# #             {"$group": {
# #                 "_id": "$reason_pred",
# #                 "count": {"$sum": 1},
# #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# #                 "confiance": {"$avg": "$sentiment_confiance"},
# #             }},
# #             {"$sort": {"count": -1}},
# #             {"$limit": 10},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         total = sum(r["count"] for r in results)
# #         data = [{
# #             "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
# #             "count": r["count"],
# #             "pct": round(r["count"]/total*100,1),
# #             "neg_pct": round(r["neg_pct"]*100,1),
# #             "confiance": round((r["confiance"] or 0)*100,1),
# #         } for r in results]
# #         return pd.DataFrame(data)
# #     except Exception as e:
# #         print(f"Erreur get_reason_distribution: {e}")
# #         return pd.DataFrame()


# # # ============================================================
# # # EXTRACTION MONGODB — CE MOIS (CORRIGÉ)
# # # ============================================================

# # def get_anomaly_data_mois():
# #     """Anomalies uniquement pour le mois courant (comparaison jour par jour)."""
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         mois_str = now_local().strftime("%Y-%m")
# #         pipeline = [
# #             {"$match": {
# #                 "mois": mois_str,
# #                 "sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]},
# #                 "date_clean": {"$exists": True, "$ne": None},  # ← CORRIGÉ : date_clean au lieu de date_originale
# #             }},
# #             {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_clean"}}}},  # ← CORRIGÉ
# #             {"$group": {
# #                 "_id": "$day_str",
# #                 "avg_score": {"$avg": "$sentiment_score"},
# #                 "total": {"$sum": 1},
# #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# #                 "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
# #             }},
# #             {"$sort": {"_id": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         df = pd.DataFrame([{
# #             "mois": f"{mois_str}-{r['_id']}",
# #             "avg_score": round(r["avg_score"],3),
# #             "total": r["total"],
# #             "neg_pct": round(r["neg_pct"]*100,1),
# #             "frustration_pct": round(r["frustration_pct"]*100,1),
# #         } for r in results])
# #         if len(df) > 2:
# #             mean_s = df["avg_score"].mean()
# #             std_s  = df["avg_score"].std()
# #             if std_s > 0:
# #                 df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
# #                 df["anomaly_severity"] = np.where(
# #                     df["avg_score"] < (mean_s - 2*std_s), "critical",
# #                     np.where(df["is_anomaly"], "high", "normal")
# #                 )
# #             else:
# #                 df["is_anomaly"] = False
# #                 df["anomaly_severity"] = "normal"
# #         return df
# #     except Exception as e:
# #         print(f"Erreur get_anomaly_data_mois: {e}")
# #         return pd.DataFrame()


# # def get_lda_topics_mois():
# #     """Thèmes filtrés sur le mois courant."""
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         mois_str = now_local().strftime("%Y-%m")
# #         pipeline = [
# #             {"$match": {"mois": mois_str, "theme_pred": {"$exists": True, "$ne": None}}},
# #             {"$group": {
# #                 "_id": "$theme_pred",
# #                 "count": {"$sum": 1},
# #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# #                 "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
# #             }},
# #             {"$sort": {"count": -1}},
# #             {"$limit": 8},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         keywords_map = {
# #             "reseau":       ["reseau","connexion","4g","internet","signal"],
# #             "service":      ["service","client","accueil","conseiller","support"],
# #             "prix":         ["prix","tarif","forfait","cher","abonnement"],
# #             "hors_sujet":   ["general","information","actualite","annonce"],
# #             "installation": ["installation","technicien","rdv","delai","pose"],
# #             "facture":      ["facture","paiement","montant","recu","payer"],
# #             "saturation":   ["saturation","debit","lent","connexion"],
# #             "couverture":   ["couverture","zone","antenne","signal"],
# #             "autre":        ["divers","autre","general"],
# #             "technique":    ["technique","probleme","bug","erreur","panne"],
# #             "produit":      ["produit","qualite","equipement","modem","box"],
# #             "attente":      ["attente","delai","long","patienter","lent"],
# #         }
# #         topics = []
# #         for r in results:
# #             theme = r["_id"]
# #             if not theme:
# #                 continue
# #             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
# #             kw = keywords_map.get(theme.lower(), [theme_fr])
# #             topics.append({
# #                 "name": theme_fr,
# #                 "keywords": kw[:4],
# #                 "count": r["count"],
# #                 "neg_pct": round(r["neg_pct"]*100,1),
# #                 "pos_pct": round(r["pos_pct"]*100,1),
# #             })
# #         return topics
# #     except Exception as e:
# #         print(f"Erreur get_lda_topics_mois: {e}")
# #         return []


# # def get_wordcloud_data_mois():
# #     """Wordcloud filtré sur le mois courant."""
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         mois_str = now_local().strftime("%Y-%m")
# #         pipeline = [
# #             {"$match": {
# #                 "mois": mois_str,
# #                 "commentaire_normalized": {"$exists": True, "$ne": ""},
# #             }},
# #             {"$limit": 3000},
# #             {"$project": {"commentaire_normalized": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return []
# #         words = []
# #         for r in results:
# #             text = r.get("commentaire_normalized","")
# #             if not text:
# #                 continue
# #             text = text.lower()
# #             text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
# #             text = re.sub(r'\d+','',text)
# #             for word in text.split():
# #                 word = word.strip()
# #                 if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
# #                     words.append(word)
# #         if not words:
# #             return []
# #         wc = Counter(words)
# #         top = wc.most_common(60)
# #         return [{"word": w, "count": c} for w,c in top]
# #     except Exception as e:
# #         print(f"Erreur get_wordcloud_data_mois: {e}")
# #         return []


# # def get_monthly_frequency_mois():
# #     """Fréquence par thème filtrée sur le mois courant (par jour)."""
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         mois_str = now_local().strftime("%Y-%m")
# #         pipeline = [
# #             {"$match": {
# #                 "mois": mois_str,
# #                 "theme_pred": {"$exists": True,"$ne": None},
# #                 "date_clean": {"$exists": True,"$ne": None},  # ← CORRIGÉ : date_clean au lieu de date_originale
# #             }},
# #             {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_clean"}}}},  # ← CORRIGÉ
# #             {"$group": {"_id": {"jour":"$day_str","theme":"$theme_pred"}, "count": {"$sum": 1}}},
# #             {"$sort": {"_id.jour": 1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         data = []
# #         for r in results:
# #             theme = r["_id"]["theme"]
# #             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
# #             data.append({"mois": r["_id"]["jour"], "theme": theme_fr, "count": r["count"]})
# #         df = pd.DataFrame(data)
# #         top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
# #         return df[df["theme"].isin(top6)]
# #     except Exception as e:
# #         print(f"Erreur get_monthly_frequency_mois: {e}")
# #         return pd.DataFrame()


# # def get_reason_distribution_mois():
# #     """Répartition des raisons pour le mois courant."""
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         mois_str = now_local().strftime("%Y-%m")
# #         pipeline = [
# #             {"$match": {"mois": mois_str, "reason_pred": {"$exists": True, "$ne": None}}},
# #             {"$group": {
# #                 "_id": "$reason_pred",
# #                 "count": {"$sum": 1},
# #                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
# #                 "confiance": {"$avg": "$sentiment_confiance"},
# #             }},
# #             {"$sort": {"count": -1}},
# #             {"$limit": 10},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         total = sum(r["count"] for r in results)
# #         data = [{
# #             "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
# #             "count": r["count"],
# #             "pct": round(r["count"]/total*100,1),
# #             "neg_pct": round(r["neg_pct"]*100,1),
# #             "confiance": round((r["confiance"] or 0)*100,1),
# #         } for r in results]
# #         return pd.DataFrame(data)
# #     except Exception as e:
# #         print(f"Erreur get_reason_distribution_mois: {e}")
# #         return pd.DataFrame()


# # # ============================================================
# # # GRAPHIQUES
# # # ============================================================

# # def make_reasons_donut(df, theme="light"):
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 280))
# #         return fig

# #     palette = (BLUE_PALETTE_DARK if theme=="dark" else BLUE_PALETTE_LIGHT)[:len(df)]

# #     fig = go.Figure(go.Pie(
# #         labels=df["reason"],
# #         values=df["count"],
# #         hole=0.55,
# #         marker=dict(colors=palette, line=dict(color=c["bg"], width=2)),
# #         textinfo="label+percent",
# #         textposition="outside",
# #         textfont=dict(size=9, color=c["text"]),
# #         hovertemplate="<b>%{label}</b><br>Volume: %{value:,}<br>Part: %{percent}<br>Insatisfaction: %{customdata}%<extra></extra>",
# #         customdata=df["neg_pct"],
# #         pull=[0.03 if i == 0 else 0 for i in range(len(df))],
# #         sort=False,
# #         direction="clockwise",
# #     ))

# #     layout = _base_layout(c, 280, margin=dict(l=10, r=80, t=30, b=30))
# #     layout.update(
# #         showlegend=True,
# #         legend=dict(
# #             orientation="v", x=1.02, y=0.5, xanchor="left", yanchor="middle",
# #             font=dict(size=9, color=c["text"]), bgcolor="rgba(0,0,0,0)", borderwidth=0,
# #         ),
# #         annotations=[dict(
# #             text=f"<b>{df['count'].sum():,}</b><br><span style='font-size:8px'>messages</span>",
# #             x=0.5, y=0.5,
# #             font=dict(size=12, color=c["primary"]),
# #             showarrow=False,
# #         )],
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_reasons_bar(df, theme="light"):
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 280))
# #         return fig

# #     df_sorted = df.sort_values("neg_pct", ascending=True).copy()

# #     bar_colors = []
# #     for p in df_sorted["neg_pct"]:
# #         if p >= 60:
# #             bar_colors.append(c["danger"])
# #         elif p >= 40:
# #             bar_colors.append(c["warning"])
# #         else:
# #             bar_colors.append(c["success"])

# #     fig = go.Figure()
# #     fig.add_trace(go.Bar(
# #         y=df_sorted["reason"],
# #         x=df_sorted["neg_pct"],
# #         orientation="h",
# #         width=0.65,
# #         marker=dict(color=bar_colors, line=dict(width=0), cornerradius=4),
# #         text=[f"{p:.0f}%" for p in df_sorted["neg_pct"]],
# #         textposition="outside",
# #         textfont=dict(size=9, weight="bold"),
# #         hovertemplate="<b>%{y}</b><br>Insatisfaction: %{x:.1f}%<br>Volume: %{customdata:,}<extra></extra>",
# #         customdata=df_sorted["count"],
# #     ))

# #     fig.add_vline(x=60, line_dash="dash", line_color=c["danger"], line_width=1.5, opacity=0.7)
# #     fig.add_vline(x=40, line_dash="dot",  line_color=c["warning"], line_width=1, opacity=0.6)

# #     layout = _base_layout(c, 280, margin=dict(l=100, r=50, t=20, b=20))
# #     layout.update(
# #         xaxis=dict(ticksuffix="%", range=[0, 110], showgrid=True, gridcolor=c["grid"], zeroline=False),
# #         yaxis=dict(showgrid=False),
# #         showlegend=False,
# #         bargap=0.3,
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_anomaly_chart(df, theme="light"):
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnee mensuelle", x=0.5, y=0.5,
# #                            showarrow=False, font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 240))
# #         return fig

# #     fig = go.Figure()
# #     r,g,b_ = int(c["primary"][1:3],16), int(c["primary"][3:5],16), int(c["primary"][5:7],16)
# #     fig.add_trace(go.Scatter(
# #         x=df["mois"], y=df["avg_score"],
# #         mode="lines+markers",
# #         name="Score satisfaction",
# #         line=dict(color=c["primary"], width=2.5),
# #         fill="tozeroy",
# #         fillcolor=f"rgba({r},{g},{b_},0.08)",
# #         marker=dict(size=8, color=c["primary"], line=dict(color=c["bg"], width=2)),
# #         hovertemplate="Mois: %{x}<br>Score: %{y:.3f}<br>Insatisfaits: %{customdata:.1f}%<extra></extra>",
# #         customdata=df["neg_pct"],
# #     ))

# #     if "is_anomaly" in df.columns:
# #         anom = df[df["is_anomaly"]]
# #         if not anom.empty:
# #             fig.add_trace(go.Scatter(
# #                 x=anom["mois"], y=anom["avg_score"],
# #                 mode="markers",
# #                 marker=dict(symbol="x", size=12, color=c["danger"],
# #                             line=dict(width=2, color="white")),
# #                 name="Mois dégradé",
# #                 hovertemplate="ALERTE — %{x}<br>Score: %{y:.3f}<extra></extra>",
# #             ))

# #     mean_s = df["avg_score"].mean()
# #     fig.add_hline(y=mean_s, line_dash="dash", line_color=c["neutral"], opacity=0.5)

# #     layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
# #     layout.update(
# #         xaxis=dict(title="Période", tickangle=-30, tickfont=dict(size=8), nticks=6,tickformat="%d/%m"),
# #         yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False),
# #         legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=8)),
# #         hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_monthly_frequency_chart(df, theme="light"):
# #     c = _colors(theme)
# #     multi_palette = [c["primary"], c["danger"], c["warning"], c["success"], "#6c5ce7", "#00cec9"]
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5,
# #                            showarrow=False, font=dict(color=c["neutral"]))
# #         fig.update_layout(**_base_layout(c, 240))
# #         return fig

# #     fig = go.Figure()
# #     for i, th in enumerate(df["theme"].unique()):
# #         sub = df[df["theme"] == th].sort_values("mois")
# #         fig.add_trace(go.Scatter(
# #             x=sub["mois"], y=sub["count"],
# #             mode="lines+markers",
# #             name=th,
# #             line=dict(width=1.5, color=multi_palette[i % len(multi_palette)]),
# #             marker=dict(size=5),
# #             hovertemplate="<b>%{fullData.name}</b><br>Période: %{x}<br>Messages: %{y:,}<extra></extra>",
# #         ))

# #     layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
# #     layout.update(
# #         xaxis=dict(title="Période", tickangle=-30, tickfont=dict(size=8), nticks=6),
# #         yaxis=dict(title="Messages", tickformat=","),
# #         legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=7)),
# #         hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # # ============================================================
# # # WORDCLOUD
# # # ============================================================

# # def make_wordcloud_iframe(word_data, theme="light"):
# #     if not word_data:
# #         return html.Div([
# #             html.I(className="fas fa-cloud",
# #                    style={"fontSize":"28px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
# #             html.P("Aucune donnee textuelle",
# #                    style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
# #         ], style={"textAlign":"center","padding":"30px","display":"flex",
# #                   "flexDirection":"column","alignItems":"center"})

# #     bg_color = "#1a2540" if theme == "dark" else "#ffffff"
# #     max_c = max(w["count"] for w in word_data)
# #     min_c = min(w["count"] for w in word_data)
# #     rng   = max_c - min_c if max_c != min_c else 1

# #     words_js = json.dumps([
# #         [w["word"], round(10 + (w["count"] - min_c) / rng * 58)]
# #         for w in word_data
# #     ])

# #     colors_light = ["#003087","#1a4fa0","#4a80d4","#e8384f","#f59e0b","#00a854","#6c8dcc"]
# #     colors_dark  = ["#4a80d4","#6a9ae0","#8ab8e4","#2ecc71","#f06070","#f39c12","#a78bfa"]
# #     colors_js = json.dumps(colors_dark if theme == "dark" else colors_light)

# #     html_content = f"""<!DOCTYPE html>
# # <html><head><meta charset="utf-8">
# # <style>
# #   *{{margin:0;padding:0;box-sizing:border-box}}
# #   body{{background:{bg_color};width:100%;height:100%;overflow:hidden;
# #         display:flex;align-items:center;justify-content:center}}
# #   #wc{{width:100%;height:100%;display:block}}
# # </style>
# # <script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js"></script>
# # </head><body>
# # <canvas id="wc"></canvas>
# # <script>
# #   var words={words_js};
# #   var colors={colors_js};
# #   var ci=0;
# #   function init(){{
# #     var c=document.getElementById('wc');
# #     var W=window.innerWidth||600,H=window.innerHeight||320;
# #     c.width=W;c.height=H;
# #     WordCloud(c,{{
# #       list:words,
# #       gridSize:Math.round(6*W/700),
# #       weightFactor:function(s){{return s*(W/600)}},
# #       fontFamily:"'Segoe UI','DM Sans',sans-serif",
# #       color:function(){{return colors[(ci++)%colors.length]}},
# #       rotateRatio:0.3,rotationSteps:3,
# #       backgroundColor:'{bg_color}',
# #       shuffle:true,drawOutOfBound:false,shrinkToFit:true,minSize:8,
# #     }});
# #   }}
# #   if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
# #   else init();
# #   window.addEventListener('resize',function(){{setTimeout(init,100)}});
# # </script>
# # </body></html>"""

# #     return html.Iframe(
# #         srcDoc=html_content,
# #         style={
# #             "width": "100%", "height": "340px", "border": "none",
# #             "borderRadius": "8px", "background": bg_color, "display": "block",
# #         },
# #     )


# # # ============================================================
# # # COMPOSANTS HTML
# # # ============================================================

# # def make_anomaly_banner(anomaly_df):
# #     no_anomaly = (
# #         anomaly_df.empty
# #         or "is_anomaly" not in anomaly_df.columns
# #         or int(anomaly_df["is_anomaly"].sum()) == 0
# #     )

# #     if no_anomaly:
# #         return html.Div(
# #             id="tt-anomaly-banner",
# #             children=[
# #                 html.Div([
# #                     html.I(className="fas fa-check-circle",
# #                            style={"fontSize":"12px","color":"var(--tt-green, #04723b)",
# #                                   "marginRight":"8px","flexShrink":"0"}),
# #                     html.Strong("Aucune anomalie détectée", style={"fontSize":"10px"}),
# #                 ], style={"display":"flex","alignItems":"center","flex":"1"}),
# #                 html.Button(
# #                     html.I(className="fas fa-times", style={"fontSize":"9px"}),
# #                     id="close-anomaly-banner-btn", n_clicks=0,
# #                     style={"background":"transparent","border":"none",
# #                            "color":"var(--tt-green, #00a854)",
# #                            "cursor":"pointer","padding":"2px 5px",
# #                            "borderRadius":"4px","flexShrink":"0"},
# #                 ),
# #             ],
# #             style={
# #                 "display":"flex","alignItems":"center","justifyContent":"space-between",
# #                 "padding":"6px 12px","borderRadius":"8px",
# #                 "background":"rgba(0,168,84,0.07)","border":"1px solid rgba(0,168,84,0.18)",
# #                 "marginBottom":"8px",
# #             },
# #         )

# #     n_anom = int(anomaly_df["is_anomaly"].sum())
# #     n_crit = int((anomaly_df.get("anomaly_severity", pd.Series([])) == "critical").sum()) \
# #              if "anomaly_severity" in anomaly_df.columns else 0
# #     txt = f"{n_anom} période(s) anormalement dégradée(s)" + (f" (dont {n_crit} critique)" if n_crit else "")

# #     return html.Div(
# #         id="tt-anomaly-banner",
# #         children=[
# #             html.Div([
# #                 html.I(className="fas fa-exclamation-triangle",
# #                        style={"fontSize":"12px","color":"var(--tt-red, #e8384f)",
# #                               "marginRight":"8px","flexShrink":"0"}),
# #                 html.Strong(txt, style={"fontSize":"10px"}),
# #             ], style={"display":"flex","alignItems":"center","flex":"1"}),
# #             html.Button(
# #                 html.I(className="fas fa-times", style={"fontSize":"9px"}),
# #                 id="close-anomaly-banner-btn", n_clicks=0,
# #                 style={"background":"transparent","border":"none",
# #                        "color":"var(--tt-red, #e8384f)",
# #                        "cursor":"pointer","padding":"2px 5px",
# #                        "borderRadius":"4px","flexShrink":"0"},
# #             ),
# #         ],
# #         style={
# #             "display":"flex","alignItems":"center","justifyContent":"space-between",
# #             "padding":"6px 12px","borderRadius":"8px",
# #             "background":"rgba(232,56,79,0.07)","border":"1px solid rgba(232,56,79,0.18)",
# #             "marginBottom":"8px",
# #         },
# #     )


# # def make_topics_list(topics, theme="light"):
# #     if not topics:
# #         return html.Div([
# #             html.I(className="fas fa-tags",
# #                    style={"fontSize":"24px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
# #             html.P("Aucun thème détecté",
# #                    style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
# #         ], style={"textAlign":"center","padding":"30px","display":"flex",
# #                   "flexDirection":"column","alignItems":"center"})

# #     c = _colors(theme)
# #     items = []
# #     for t in topics:
# #         if t["neg_pct"] > 60:
# #             neg_col   = c["danger"]
# #             badge_txt = "Critique"
# #         elif t["neg_pct"] > 40:
# #             neg_col   = c["warning"]
# #             badge_txt = "Alerte"
# #         else:
# #             neg_col   = c["success"]
# #             badge_txt = "Normal"

# #         items.append(html.Div([
# #             html.Div([
# #                 html.Div(style={
# #                     "width":"5px","height":"5px","borderRadius":"50%",
# #                     "background":neg_col,"flexShrink":"0",
# #                 }),
# #                 html.Span(t["name"], style={
# #                     "fontSize":"10px","fontWeight":"600",
# #                     "color":"var(--tt-text, #1a2a4a)","flex":"1",
# #                 }),
# #                 html.Span(badge_txt, style={
# #                     "fontSize":"9px","fontWeight":"600",
# #                     "color": neg_col,
# #                     "padding":"2px 6px","borderRadius":"8px",
# #                     "background": f"rgba({','.join(str(int(neg_col.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.1)",
# #                 }),
# #             ], style={"display":"flex","alignItems":"center","gap":"6px","marginBottom":"4px"}),

# #             html.Div([
# #                 html.I(className="fas fa-comment-dots",
# #                        style={"fontSize":"8px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
# #                 html.Span(f"{t['count']:,} messages",
# #                           style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
# #                 html.Span(" · ", style={"color":"var(--tt-border, #ccc)","margin":"0 3px"}),
# #                 html.Span(f"{t['neg_pct']}% insatisfaits",
# #                           style={"fontSize":"8px","color":neg_col,"fontWeight":"600"}),
# #             ], style={"display":"flex","alignItems":"center","flexWrap":"wrap","marginBottom":"4px"}),

# #             html.Div([
# #                 html.I(className="fas fa-key",
# #                        style={"fontSize":"7px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
# #                 html.Span("Mots-clés : ",
# #                           style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
# #                 html.Span(", ".join(t["keywords"][:3]),
# #                           style={"fontSize":"8px","fontWeight":"500",
# #                                  "color":"var(--tt-text, #1a2a4a)"}),
# #             ], style={"display":"flex","alignItems":"center","marginBottom":"5px","flexWrap":"wrap"}),

# #             html.Div(
# #                 html.Div(style={
# #                     "height":"100%","width":f"{min(t['neg_pct'],100)}%",
# #                     "background":neg_col,"borderRadius":"2px",
# #                     "transition":"width 0.4s ease",
# #                 }),
# #                 className="tt-topic-bar-track",
# #             ),
# #         ], className="tt-topic-item"))

# #     return html.Div(items, className="tt-topics-list")


# # # ============================================================
# # # HELPER : carte générique pour grille 3x2
# # # ============================================================

# # def _chart_card(icon, title, tooltip_title, tooltip_body, children, icon_variant=""):
# #     return html.Div([
# #         html.Div([
# #             html.Div([html.I(className=icon, style={"fontSize":"13px"})],
# #                      className="card-icon"),
# #             html.Span(title, className="card-title"),
# #             html.Div([
# #                 html.Div(
# #                     html.I(className="fas fa-info-circle", style={"fontSize":"10px"}),
# #                     className="tooltip-icon",
# #                 ),
# #                 html.Div([
# #                     html.Div(tooltip_title, className="tooltip-title"),
# #                     html.Div(tooltip_body,  className="tooltip-body"),
# #                 ], className="card-tooltip"),
# #             ], className="tooltip-wrapper"),
# #         ], className="card-header"),
# #         html.Div(children, className="card-content"),
# #     ], className="chart-card", style={"padding":"14px 16px","borderRadius":"14px","height":"100%"})


# # # ============================================================
# # # CACHE
# # # ============================================================

# # _cache = {}

# # def _get_data():
# #     global _cache
# #     if not _cache:
# #         print("Chargement des données depuis MongoDB...")

# #         anomaly_df = get_anomaly_data()
# #         topics = get_lda_topics()
# #         word_data = get_wordcloud_data()
# #         monthly_df = get_monthly_frequency()
# #         reason_df = get_reason_distribution()

# #         if monthly_df is None or monthly_df.empty:
# #             monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
# #         if reason_df is None or reason_df.empty:
# #             reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
# #         if anomaly_df is None or anomaly_df.empty:
# #             anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

# #         _cache["anomaly_df"] = anomaly_df
# #         _cache["topics"] = topics if topics else []
# #         _cache["word_data"] = word_data if word_data else []
# #         _cache["monthly_df"] = monthly_df
# #         _cache["reason_df"] = reason_df

# #     return _cache


# # def _get_data_mois():
# #     """Données filtrées sur le mois courant (pas mises en cache longtemps)."""
# #     anomaly_df = get_anomaly_data_mois()
# #     topics = get_lda_topics_mois()
# #     word_data = get_wordcloud_data_mois()
# #     monthly_df = get_monthly_frequency_mois()
# #     reason_df = get_reason_distribution_mois()

# #     if monthly_df is None or monthly_df.empty:
# #         monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
# #     if reason_df is None or reason_df.empty:
# #         reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
# #     if anomaly_df is None or anomaly_df.empty:
# #         anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

# #     return {
# #         "anomaly_df": anomaly_df,
# #         "topics": topics if topics else [],
# #         "word_data": word_data if word_data else [],
# #         "monthly_df": monthly_df,
# #         "reason_df": reason_df,
# #     }


# # # ============================================================
# # # LAYOUT : grille 3×2
# # # ============================================================

# # def _make_grid(d, theme, periode_label=""):
# #     """Construit la grille 3×2 avec les données fournies."""
# #     return html.Div(className="grid-3x2", children=[

# #         # LIGNE 1 : ÉVOLUTION | ANOMALIES
# #         html.Div(className="grid-row", children=[
# #             _chart_card(
# #                 "fas fa-chart-line", "ÉVOLUTION PAR THÈME",
# #                 "Fréquence par sujet",
# #                 f"Evolution du nombre de messages par thème{' pour le mois en cours' if periode_label else ' par mois'}.",
# #                 dcc.Graph(
# #                     id="tt-monthly-chart",
# #                     figure=make_monthly_frequency_chart(d["monthly_df"], theme),
# #                     config={"displayModeBar": False},
# #                     style={"height": "280px"},
# #                 ),
# #             ),
# #             _chart_card(
# #                 "fas fa-exclamation-triangle", "DÉTECTION DES ANOMALIES",
# #                 "Anomalies de satisfaction",
# #                 f"Score de satisfaction{'  journalier' if periode_label else ' mensuel'}. Les croix signalent des périodes anormales.",
# #                 html.Div([
# #                     html.Div(
# #                         id="tt-anomaly-banner-container",
# #                         children=make_anomaly_banner(d["anomaly_df"]),
# #                     ),
# #                     dcc.Graph(
# #                         id="tt-anomaly-chart",
# #                         figure=make_anomaly_chart(d["anomaly_df"], theme),
# #                         config={"displayModeBar": False},
# #                         style={"height": "250px"},
# #                     ),
# #                 ]),
# #             ),
# #         ]),

# #         # LIGNE 2 : INSATISFACTION | SUJETS
# #         html.Div(className="grid-row", children=[
# #             _chart_card(
# #                 "fas fa-chart-bar", "TAUX D'INSATISFACTION",
# #                 "Raisons classées par criticité",
# #                 "Les raisons sont triées du plus critique au moins critique.",
# #                 dcc.Graph(
# #                     id="tt-reasons-bar",
# #                     figure=make_reasons_bar(d["reason_df"], theme),
# #                     config={"displayModeBar": False},
# #                     style={"height":"280px"},
# #                 ),
# #             ),
# #             _chart_card(
# #                 "fas fa-tags", "SUJETS LES PLUS ABORDÉS",
# #                 "Thèmes principaux identifiés",
# #                 "Catégories détectées automatiquement depuis les commentaires.",
# #                 html.Div(
# #                     id="tt-topics-list",
# #                     children=make_topics_list(d["topics"], theme),
# #                     style={"height":"280px","overflowY":"auto"},
# #                 ),
# #             ),
# #         ]),

# #         # LIGNE 3 : RÉPARTITION | VOCABULAIRE
# #         html.Div(className="grid-row", children=[
# #             _chart_card(
# #                 "fas fa-chart-pie", "RÉPARTITION DES RAISONS",
# #                 "Distribution des raisons détectées",
# #                 "Répartition par volume des principales raisons détectées automatiquement.",
# #                 dcc.Graph(
# #                     id="tt-reasons-donut",
# #                     figure=make_reasons_donut(d["reason_df"], theme),
# #                     config={"displayModeBar": False},
# #                     style={"height":"280px"},
# #                 ),
# #             ),
# #             _chart_card(
# #                 "fas fa-comment-dots", "VOCABULAIRE CLIENTS",
# #                 "Nuage de mots",
# #                 "Mots les plus utilisés dans les commentaires (français, arabe, darija).",
# #                 html.Div(
# #                     id="tt-wordcloud",
# #                     children=make_wordcloud_iframe(d["word_data"], theme),
# #                     style={"height":"280px"},
# #                 ),
# #             ),
# #         ]),
# #     ])


# # def render_page(theme="light", user_data=None):
# #     print("Chargement Thèmes & Temporel...")
# #     d = _get_data()
# #     t = theme
# #     today = now_local().strftime("%d/%m/%Y")

# #     style_active = {
# #         "padding": "6px 16px", "borderRadius": "20px", "border": "none",
# #         "background": BLUE, "color": "white", "cursor": "pointer",
# #         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# #         "display": "flex", "alignItems": "center", "gap": "6px",
# #     }
# #     style_inactive = {
# #         "padding": "6px 16px", "borderRadius": "20px", "border": f"1px solid {BLUE}",
# #         "background": "transparent", "color": BLUE, "cursor": "pointer",
# #         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# #         "display": "flex", "alignItems": "center", "gap": "6px",
# #     }

# #     content = html.Div(
# #         className="dashboard-container themes-temporal-page",
# #         **{"data-theme": theme, "data-page": "themes-temporal"},
# #         children=[
# #             # ── Header ──────────────────────────────────────────────────────
# #             html.Div(
# #                 [
# #                     # Bannière statut anomalie
# #                     html.Div(
# #                         [
# #                             html.I(className="fas fa-check-circle",
# #                                    style={"fontSize":"14px","color":"#ffffff","marginRight":"10px","flexShrink":"0"}),
# #                             html.Strong("Aucune anomalie détectée",
# #                                         style={"fontSize":"14px","fontWeight":"600","color":"#ffffff"}),
# #                         ],
# #                         style={
# #                             "display":"flex","alignItems":"center","padding":"0 20px",
# #                             "borderRadius":"8px","background":"#04723b",
# #                             "border":"1px solid #046635","height":"40px","width":"250px",
# #                             "boxShadow":"0 2px 4px rgba(0,0,0,0.1)",
# #                         }
# #                     ),

# #                     # Groupe droite
# #                     html.Div(
# #                         [
# #                             # Boutons Global / Ce Mois
# #                             html.Div([
# #                                 html.Button(
# #                                     [html.I(className="fas fa-globe", style={"fontSize":"11px"}), "Global"],
# #                                     id="tt-btn-global",
# #                                     n_clicks=0,
# #                                     style=style_active,
# #                                 ),
# #                                 html.Button(
# #                                     [html.I(className="fas fa-calendar-day", style={"fontSize":"11px"}), "Ce Mois"],
# #                                     id="tt-btn-mois",
# #                                     n_clicks=0,
# #                                     style=style_inactive,
# #                                 ),
# #                             ], style={"display":"flex","alignItems":"center","gap":"8px"}),

# #                             # Badge date
# #                             html.Div(
# #                                 [
# #                                     html.I(className="far fa-calendar-alt",
# #                                            style={"marginRight":"5px","fontSize":"13px"}),
# #                                     html.Span(f"Mise à jour : {today}", style={"fontSize":"13px"}),
# #                                 ],
# #                                 style={
# #                                     "display":"flex","alignItems":"center","background":"white",
# #                                     "padding":"0 15px","borderRadius":"8px","height":"40px",
# #                                     "border":"1px solid #e0e0e0",
# #                                 }
# #                             ),

# #                             # Bouton Actualiser
# #                             html.Button(
# #                                 [html.I(className="fas fa-sync-alt",
# #                                         style={"marginRight":"5px","fontSize":"13px"}),
# #                                  html.Span("Actualiser", style={"fontSize":"13px"})],
# #                                 id="tt-refresh-btn",
# #                                 n_clicks=0,
# #                                 style={
# #                                     "background": BLUE, "color":"white","border":"none",
# #                                     "borderRadius":"8px","padding":"0 20px","cursor":"pointer",
# #                                     "fontSize":"13px","display":"flex","alignItems":"center",
# #                                     "height":"40px","gap":"8px",
# #                                 },
# #                             ),
# #                         ],
# #                         style={"display":"flex","gap":"12px","alignItems":"center"}
# #                     ),
# #                 ],
# #                 style={"display":"flex","justifyContent":"space-between",
# #                        "alignItems":"center","marginBottom":"20px"}
# #             ),

# #             # Store période
# #             dcc.Store(id="tt-periode-store", data="global"),

# #             # ── Zone grille : Global (visible par défaut) ──────────────────
# #             html.Div(
# #                 id="tt-global-content",
# #                 style={"display": "block"},
# #                 children=[_make_grid(d, theme)],
# #             ),

# #             # ── Zone grille : Ce Mois (cachée par défaut) ──────────────────
# #             html.Div(
# #                 id="tt-mois-content",
# #                 style={"display": "none"},
# #                 children=[],  # Chargé dynamiquement via callback
# #             ),
# #         ],
# #     )

# #     return make_page_layout(
# #         "themes-temporal",
# #         "Thèmes & Analyse Temporelle",
# #         "Quels sujets génèrent le plus d'insatisfaction ? Quels mois ont été les plus difficiles ?",
# #         content,
# #         theme,
# #         user_data,
# #     )


# # # ============================================================
# # # CALLBACKS
# # # ============================================================

# # # ── Basculer Global / Ce Mois ────────────────────────────────────────────────
# # @callback(
# #     Output("tt-periode-store", "data"),
# #     Output("tt-btn-global", "style"),
# #     Output("tt-btn-mois", "style"),
# #     Input("tt-btn-global", "n_clicks"),
# #     Input("tt-btn-mois", "n_clicks"),
# #     prevent_initial_call=True,
# # )
# # def tt_set_periode(n_global, n_mois):
# #     style_active = {
# #         "padding": "6px 16px", "borderRadius": "20px", "border": "none",
# #         "background": BLUE, "color": "white", "cursor": "pointer",
# #         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# #         "display": "flex", "alignItems": "center", "gap": "6px",
# #     }
# #     style_inactive = {
# #         "padding": "6px 16px", "borderRadius": "20px", "border": f"1px solid {BLUE}",
# #         "background": "transparent", "color": BLUE, "cursor": "pointer",
# #         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# #         "display": "flex", "alignItems": "center", "gap": "6px",
# #     }
# #     ctx = dash.callback_context
# #     if not ctx.triggered:
# #         return "global", style_active, style_inactive
# #     btn = ctx.triggered[0]["prop_id"].split(".")[0]
# #     if btn == "tt-btn-mois":
# #         return "mois", style_inactive, style_active
# #     return "global", style_active, style_inactive


# # # ── Afficher/cacher les zones Global / Ce Mois ──────────────────────────────
# # @callback(
# #     Output("tt-global-content", "style"),
# #     Output("tt-mois-content", "style"),
# #     Output("tt-mois-content", "children"),
# #     Input("tt-periode-store", "data"),
# #     State("theme-store", "data"),
# #     prevent_initial_call=False,
# # )
# # def tt_toggle_content(periode, theme):
# #     theme = theme or "light"

# #     if periode == "mois":
# #         mois_lbl = now_local().strftime("%B %Y")
# #         d_mois = _get_data_mois()

# #         # Bandeau titre
# #         bandeau = html.Div([
# #             html.Div(style={
# #                 "width":"4px","height":"28px","borderRadius":"4px",
# #                 "background": BLUE, "marginRight":"12px",
# #             }),
# #             html.I(className="fas fa-calendar-day",
# #                    style={"fontSize":"16px","color": BLUE,"marginRight":"10px"}),
# #             html.Span(f"Statistiques de {mois_lbl}", style={
# #                 "fontSize":"14px","fontWeight":"700","color": BLUE,"letterSpacing":"0.3px",
# #             }),
# #             html.Span("Données filtrées sur le mois en cours", style={
# #                 "fontSize":"11px","color": NEUTRAL,"marginLeft":"12px",
# #             }),
# #         ], style={
# #             "display":"flex","alignItems":"center","padding":"10px 16px",
# #             "background":"var(--bg-card)","borderRadius":"12px","marginBottom":"20px",
# #             "border":f"1px solid {BLUE_LIGHT}","boxShadow":"0 1px 3px rgba(0,0,0,0.05)",
# #         })

# #         grid_mois = _make_grid(d_mois, theme, periode_label=mois_lbl)

# #         return (
# #             {"display": "none"},
# #             {"display": "block"},
# #             [bandeau, grid_mois],
# #         )

# #     return (
# #         {"display": "block"},
# #         {"display": "none"},
# #         [],
# #     )


# # # ── Mise à jour des graphiques selon thème ───────────────────────────────────
# # @callback(
# #     Output("tt-anomaly-chart", "figure"),
# #     Output("tt-monthly-chart", "figure"),
# #     Output("tt-reasons-donut", "figure"),
# #     Output("tt-reasons-bar",   "figure"),
# #     Input("theme-store",  "data"),
# #     Input("tt-periode-store", "data"),
# #     State("auth-store",   "data"),
# # )
# # def update_charts(theme, periode, auth_data):
# #     theme = theme or "light"
# #     d = _get_data_mois() if periode == "mois" else _get_data()
# #     return (
# #         make_anomaly_chart(d["anomaly_df"], theme),
# #         make_monthly_frequency_chart(d["monthly_df"], theme),
# #         make_reasons_donut(d["reason_df"], theme),
# #         make_reasons_bar(d["reason_df"], theme),
# #     )


# # @callback(
# #     Output("tt-wordcloud",   "children"),
# #     Output("tt-topics-list", "children"),
# #     Input("theme-store", "data"),
# #     Input("tt-periode-store", "data"),
# #     State("auth-store",  "data"),
# # )
# # def update_wordcloud_and_topics(theme, periode, auth_data):
# #     theme = theme or "light"
# #     d = _get_data_mois() if periode == "mois" else _get_data()
# #     return (
# #         make_wordcloud_iframe(d["word_data"], theme),
# #         make_topics_list(d["topics"], theme),
# #     )


# # @callback(
# #     Output("tt-anomaly-banner-container", "children"),
# #     Input("close-anomaly-banner-btn", "n_clicks"),
# #     prevent_initial_call=True,
# # )
# # def close_anomaly_banner(n_clicks):
# #     if n_clicks:
# #         return None
# #     return dash.no_update


# # @callback(
# #     Output("tt-page-content", "children"),
# #     Input("theme-store", "data"),
# #     Input("auth-store",  "data"),
# # )
# # def themes_page_with_auth(theme, auth_data):
# #     theme = theme or "light"
# #     user_data = None
# #     if auth_data and auth_data.get("is_authenticated"):
# #         user_data = auth_data.get("user", {})
# #     return render_page(theme, user_data)


# # @callback(
# #     Output("tt-page-content", "children", allow_duplicate=True),
# #     Input("tt-refresh-btn", "n_clicks"),
# #     State("theme-store", "data"),
# #     State("auth-store",  "data"),
# #     prevent_initial_call=True,
# # )
# # def refresh_data(n_clicks, theme, auth_data):
# #     """Vide le cache et recharge toutes les données."""
# #     global _cache
# #     if n_clicks and n_clicks > 0:
# #         _cache = {}
# #         theme = theme or "light"
# #         user_data = None
# #         if auth_data and auth_data.get("is_authenticated"):
# #             user_data = auth_data.get("user", {})
# #         return render_page(theme, user_data)
# #     return dash.no_update


# # # ============================================================
# # # LAYOUT ENTRY POINT
# # # ============================================================

# # layout = html.Div(id="tt-page-content")


# # @callback(
# #     Output("tt-page-content", "children", allow_duplicate=True),
# #     Input("_pages_location", "pathname"),
# #     prevent_initial_call=True,
# # )
# # def init_themes_page(pathname):
# #     if pathname == "/themes-temporal":
# #         return render_page("light")
# #     return dash.no_update

# """ themes_temporal.py — REFONTE UI/UX PROFESSIONNELLE
# ✅ Grille 3×2 (3 lignes, 2 colonnes)
# ✅ Style Power BI / Desktop
# ✅ Date placée à droite
# ✅ Pas d'emoji, uniquement icônes FontAwesome
# ✅ Couleurs Algérie Télécom (#003087, #00a854, #e8384f, #f59e0b)
# ✅ Logique Global / Ce Mois / Aujourd'hui (même logique que dashboard.py)
# """

# import dash
# from dash import html, dcc, callback, Input, Output, State
# import plotly.graph_objects as go
# import pandas as pd
# import numpy as np
# import sys, os, re, json
# from collections import Counter
# from datetime import datetime, timedelta

# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# from components import make_page_layout
# from database import MONGO_AVAILABLE, _col

# dash.register_page(__name__, path='/themes-temporal', name='Thèmes & Temporel')

# # ============================================================
# # CONSTANTES COULEURS
# # ============================================================

# BLUE       = "#003087"
# BLUE_MID   = "#1a4fa0"
# BLUE_LIGHT = "#e8f0fb"
# GREEN      = "#00a854"
# RED        = "#e8384f"
# ORANGE     = "#f59e0b"
# NEUTRAL    = "#64748b"

# TZ_OFFSET = timedelta(hours=1)

# def now_local():
#     return datetime.utcnow() + TZ_OFFSET

# # ============================================================
# # MAPPINGS
# # ============================================================

# THEME_MAPPING = {
#     "reseau":       "Réseau Technique",
#     "technique":    "Problèmes Techniques",
#     "service":      "Service Client",
#     "client":       "Service Client",
#     "attente":      "Délais d'attente",
#     "prix":         "Tarifs",
#     "facture":      "Facturation",
#     "produit":      "Qualité Produit",
#     "offre":        "Offres Promo",
#     "hors_sujet":   "Hors Sujet",
#     "information":  "Information Générale",
#     "installation": "Installation",
#     "equipement":   "Équipement",
#     "saturation":   "Saturation Réseau",
#     "couverture":   "Couverture",
#     "debit":        "Débit Internet",
#     "autre":        "Autre",
# }

# REASON_MAPPING = {
#     "reseau":       "Réseau",
#     "service":      "Service Client",
#     "prix":         "Tarifs",
#     "attente":      "Attente",
#     "hors_sujet":   "Hors Sujet",
#     "installation": "Installation",
#     "facture":      "Facturation",
#     "saturation":   "Saturation",
#     "couverture":   "Couverture",
#     "autre":        "Autre",
#     "technique":    "Technique",
#     "produit":      "Produit",
# }

# STOPWORDS = {
#     "le","la","les","un","une","des","du","de","et","ou","mais","donc","or","ni","car",
#     "je","tu","il","elle","on","nous","vous","ils","elles","me","te","se","ce","cet",
#     "cette","ces","mon","ton","son","notre","votre","leur","que","qui","quoi","dont",
#     "est","sont","être","avoir","faire","dire","aller","voir","pouvoir","vouloir",
#     "a","dans","pour","par","avec","sans","sur","sous","entre","très","trop",
#     "peu","fort","bien","mal","oui","non","ainsi","plus","pas","tout","ça","si","ya",
#     "ال","و","في","من","على","إلى","ب","عن","مع","ما","هذا","هذه","ذلك","تلك",
#     "كان","كانت","يكون","أن","إن","أنه","لأن","حتى","إذا","فقد","قد","هل","أين",
#     "لم","لن","له","لها","لهم","لهن","هو","هي","هم","هن",
# }

# # ============================================================
# # COULEURS THÈME
# # ============================================================

# def _colors(theme):
#     if theme == "dark":
#         return {
#             "bg": "#141c2e", "paper_bg": "#1a2540", "text": "#dce8f5",
#             "grid": "#1e2d47", "primary": "#4a80d4", "success": "#2ecc71",
#             "danger": "#f06070", "warning": "#f39c12", "neutral": "#607b99",
#             "secondary": "#6c8dcc", "blue_light": "#8ab8e4", "blue_dark": "#2c5f8a",
#         }
#     return {
#         "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
#         "grid": "#e8edf5", "primary": "#003087", "success": "#00a854",
#         "danger": "#e8384f", "warning": "#f59e0b", "neutral": "#64748b",
#         "secondary": "#1a4fa0", "blue_light": "#4a80d4", "blue_dark": "#1a4a8a",
#     }


# def _base_layout(c, height, margin=None):
#     m = margin or dict(l=10, r=10, t=20, b=10)
#     return dict(
#         plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
#         font=dict(color=c["text"], family="'Segoe UI', 'DM Sans', sans-serif", size=10),
#         height=height, margin=m,
#     )


# BLUE_PALETTE_LIGHT = ["#003087","#1a4fa0","#2d66bb","#4a80d4","#6c8dcc","#8ab8e4"]
# BLUE_PALETTE_DARK  = ["#4a80d4","#6a9ae0","#8ab8e4","#5a8ed8","#7aaae0","#3a6fc4"]


# # ============================================================
# # EXTRACTION MONGODB — GLOBAL
# # ============================================================

# def get_anomaly_data():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         pipeline = [
#             {"$match": {"sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]}, "mois": {"$exists": True}}},
#             {"$group": {
#                 "_id": "$mois",
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         df = pd.DataFrame([{
#             "mois": r["_id"],
#             "avg_score": round(r["avg_score"],3),
#             "total": r["total"],
#             "neg_pct": round(r["neg_pct"]*100,1),
#             "frustration_pct": round(r["frustration_pct"]*100,1),
#         } for r in results])
#         if len(df) > 2:
#             mean_s = df["avg_score"].mean()
#             std_s  = df["avg_score"].std()
#             if std_s > 0:
#                 df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
#                 df["anomaly_severity"] = np.where(
#                     df["avg_score"] < (mean_s - 2*std_s), "critical",
#                     np.where(df["is_anomaly"], "high", "normal")
#                 )
#             else:
#                 df["is_anomaly"] = False
#                 df["anomaly_severity"] = "normal"
#         return df
#     except Exception as e:
#         print(f"Erreur get_anomaly_data: {e}")
#         return pd.DataFrame()


# def get_lda_topics():
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         pipeline = [
#             {"$match": {"theme_pred": {"$exists": True, "$ne": None}}},
#             {"$group": {
#                 "_id": "$theme_pred",
#                 "count": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
#             }},
#             {"$sort": {"count": -1}},
#             {"$limit": 8},
#         ]
#         results = list(_col.aggregate(pipeline))
#         keywords_map = {
#             "reseau":       ["reseau","connexion","4g","internet","signal"],
#             "service":      ["service","client","accueil","conseiller","support"],
#             "prix":         ["prix","tarif","forfait","cher","abonnement"],
#             "hors_sujet":   ["general","information","actualite","annonce"],
#             "installation": ["installation","technicien","rdv","delai","pose"],
#             "facture":      ["facture","paiement","montant","recu","payer"],
#             "saturation":   ["saturation","debit","lent","connexion"],
#             "couverture":   ["couverture","zone","antenne","signal"],
#             "autre":        ["divers","autre","general"],
#             "technique":    ["technique","probleme","bug","erreur","panne"],
#             "produit":      ["produit","qualite","equipement","modem","box"],
#             "attente":      ["attente","delai","long","patienter","lent"],
#         }
#         topics = []
#         for r in results:
#             theme = r["_id"]
#             if not theme:
#                 continue
#             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
#             kw = keywords_map.get(theme.lower(), [theme_fr])
#             topics.append({
#                 "name": theme_fr,
#                 "keywords": kw[:4],
#                 "count": r["count"],
#                 "neg_pct": round(r["neg_pct"]*100,1),
#                 "pos_pct": round(r["pos_pct"]*100,1),
#             })
#         return topics
#     except Exception as e:
#         print(f"Erreur get_lda_topics: {e}")
#         return []


# def get_wordcloud_data():
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         pipeline = [
#             {"$match": {"commentaire_normalized": {"$exists": True, "$ne": ""}}},
#             {"$limit": 8000},
#             {"$project": {"commentaire_normalized": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return []
#         words = []
#         for r in results:
#             text = r.get("commentaire_normalized","")
#             if not text:
#                 continue
#             text = text.lower()
#             text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
#             text = re.sub(r'\d+','',text)
#             for word in text.split():
#                 word = word.strip()
#                 if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
#                     words.append(word)
#         if not words:
#             return []
#         wc = Counter(words)
#         top = wc.most_common(60)
#         return [{"word": w, "count": c} for w,c in top]
#     except Exception as e:
#         print(f"Erreur get_wordcloud_data: {e}")
#         return []


# def get_monthly_frequency():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         pipeline = [
#             {"$match": {"theme_pred": {"$exists": True,"$ne": None}, "mois": {"$exists": True}}},
#             {"$group": {"_id": {"mois":"$mois","theme":"$theme_pred"}, "count": {"$sum": 1}}},
#             {"$sort": {"_id.mois": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         data = []
#         for r in results:
#             theme = r["_id"]["theme"]
#             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
#             data.append({"mois": r["_id"]["mois"], "theme": theme_fr, "count": r["count"]})
#         df = pd.DataFrame(data)
#         top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
#         return df[df["theme"].isin(top6)]
#     except Exception as e:
#         print(f"Erreur get_monthly_frequency: {e}")
#         return pd.DataFrame()


# def get_reason_distribution():
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         pipeline = [
#             {"$match": {"reason_pred": {"$exists": True, "$ne": None}}},
#             {"$group": {
#                 "_id": "$reason_pred",
#                 "count": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "confiance": {"$avg": "$sentiment_confiance"},
#             }},
#             {"$sort": {"count": -1}},
#             {"$limit": 10},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         total = sum(r["count"] for r in results)
#         data = [{
#             "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
#             "count": r["count"],
#             "pct": round(r["count"]/total*100,1),
#             "neg_pct": round(r["neg_pct"]*100,1),
#             "confiance": round((r["confiance"] or 0)*100,1),
#         } for r in results]
#         return pd.DataFrame(data)
#     except Exception as e:
#         print(f"Erreur get_reason_distribution: {e}")
#         return pd.DataFrame()


# # ============================================================
# # EXTRACTION MONGODB — CE MOIS
# # ============================================================

# def get_anomaly_data_mois():
#     """Anomalies pour le mois courant (comparaison jour par jour)."""
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         mois_str = now_local().strftime("%Y-%m")
#         pipeline = [
#             {"$match": {
#                 "mois": mois_str,
#                 "sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]},
#                 "date_clean": {"$exists": True, "$ne": None},
#             }},
#             {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_clean"}}}},
#             {"$group": {
#                 "_id": "$day_str",
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         df = pd.DataFrame([{
#             "mois": f"{mois_str}-{r['_id']}",
#             "avg_score": round(r["avg_score"],3),
#             "total": r["total"],
#             "neg_pct": round(r["neg_pct"]*100,1),
#             "frustration_pct": round(r["frustration_pct"]*100,1),
#         } for r in results])
#         if len(df) > 2:
#             mean_s = df["avg_score"].mean()
#             std_s  = df["avg_score"].std()
#             if std_s > 0:
#                 df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
#                 df["anomaly_severity"] = np.where(
#                     df["avg_score"] < (mean_s - 2*std_s), "critical",
#                     np.where(df["is_anomaly"], "high", "normal")
#                 )
#             else:
#                 df["is_anomaly"] = False
#                 df["anomaly_severity"] = "normal"
#         return df
#     except Exception as e:
#         print(f"Erreur get_anomaly_data_mois: {e}")
#         return pd.DataFrame()


# def get_lda_topics_mois():
#     """Thèmes filtrés sur le mois courant."""
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         mois_str = now_local().strftime("%Y-%m")
#         pipeline = [
#             {"$match": {"mois": mois_str, "theme_pred": {"$exists": True, "$ne": None}}},
#             {"$group": {
#                 "_id": "$theme_pred",
#                 "count": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
#             }},
#             {"$sort": {"count": -1}},
#             {"$limit": 8},
#         ]
#         results = list(_col.aggregate(pipeline))
#         keywords_map = {
#             "reseau":       ["reseau","connexion","4g","internet","signal"],
#             "service":      ["service","client","accueil","conseiller","support"],
#             "prix":         ["prix","tarif","forfait","cher","abonnement"],
#             "hors_sujet":   ["general","information","actualite","annonce"],
#             "installation": ["installation","technicien","rdv","delai","pose"],
#             "facture":      ["facture","paiement","montant","recu","payer"],
#             "saturation":   ["saturation","debit","lent","connexion"],
#             "couverture":   ["couverture","zone","antenne","signal"],
#             "autre":        ["divers","autre","general"],
#             "technique":    ["technique","probleme","bug","erreur","panne"],
#             "produit":      ["produit","qualite","equipement","modem","box"],
#             "attente":      ["attente","delai","long","patienter","lent"],
#         }
#         topics = []
#         for r in results:
#             theme = r["_id"]
#             if not theme:
#                 continue
#             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
#             kw = keywords_map.get(theme.lower(), [theme_fr])
#             topics.append({
#                 "name": theme_fr,
#                 "keywords": kw[:4],
#                 "count": r["count"],
#                 "neg_pct": round(r["neg_pct"]*100,1),
#                 "pos_pct": round(r["pos_pct"]*100,1),
#             })
#         return topics
#     except Exception as e:
#         print(f"Erreur get_lda_topics_mois: {e}")
#         return []


# def get_wordcloud_data_mois():
#     """Wordcloud filtré sur le mois courant."""
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         mois_str = now_local().strftime("%Y-%m")
#         pipeline = [
#             {"$match": {
#                 "mois": mois_str,
#                 "commentaire_normalized": {"$exists": True, "$ne": ""},
#             }},
#             {"$limit": 3000},
#             {"$project": {"commentaire_normalized": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return []
#         words = []
#         for r in results:
#             text = r.get("commentaire_normalized","")
#             if not text:
#                 continue
#             text = text.lower()
#             text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
#             text = re.sub(r'\d+','',text)
#             for word in text.split():
#                 word = word.strip()
#                 if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
#                     words.append(word)
#         if not words:
#             return []
#         wc = Counter(words)
#         top = wc.most_common(60)
#         return [{"word": w, "count": c} for w,c in top]
#     except Exception as e:
#         print(f"Erreur get_wordcloud_data_mois: {e}")
#         return []


# def get_monthly_frequency_mois():
#     """Fréquence par thème filtrée sur le mois courant (par jour)."""
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         mois_str = now_local().strftime("%Y-%m")
#         pipeline = [
#             {"$match": {
#                 "mois": mois_str,
#                 "theme_pred": {"$exists": True,"$ne": None},
#                 "date_clean": {"$exists": True,"$ne": None},
#             }},
#             {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_clean"}}}},
#             {"$group": {"_id": {"jour":"$day_str","theme":"$theme_pred"}, "count": {"$sum": 1}}},
#             {"$sort": {"_id.jour": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         data = []
#         for r in results:
#             theme = r["_id"]["theme"]
#             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
#             data.append({"mois": r["_id"]["jour"], "theme": theme_fr, "count": r["count"]})
#         df = pd.DataFrame(data)
#         top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
#         return df[df["theme"].isin(top6)]
#     except Exception as e:
#         print(f"Erreur get_monthly_frequency_mois: {e}")
#         return pd.DataFrame()


# def get_reason_distribution_mois():
#     """Répartition des raisons pour le mois courant."""
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         mois_str = now_local().strftime("%Y-%m")
#         pipeline = [
#             {"$match": {"mois": mois_str, "reason_pred": {"$exists": True, "$ne": None}}},
#             {"$group": {
#                 "_id": "$reason_pred",
#                 "count": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "confiance": {"$avg": "$sentiment_confiance"},
#             }},
#             {"$sort": {"count": -1}},
#             {"$limit": 10},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         total = sum(r["count"] for r in results)
#         data = [{
#             "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
#             "count": r["count"],
#             "pct": round(r["count"]/total*100,1),
#             "neg_pct": round(r["neg_pct"]*100,1),
#             "confiance": round((r["confiance"] or 0)*100,1),
#         } for r in results]
#         return pd.DataFrame(data)
#     except Exception as e:
#         print(f"Erreur get_reason_distribution_mois: {e}")
#         return pd.DataFrame()


# # ============================================================
# # EXTRACTION MONGODB — AUJOURD'HUI
# # ============================================================

# def get_anomaly_data_jour():
#     """
#     Anomalies pour aujourd'hui : groupe par heure (heure du commentaire client via date_clean).
#     Filtre sur le jour courant en UTC (date_clean est stocké en UTC par le consumer,
#     représentant l'heure locale Algérie directement).
#     """
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         local_now = now_local()
#         # Bornes du jour courant en UTC (date_clean = heure locale stockée naïve)
#         debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
#         fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

#         pipeline = [
#             {"$match": {
#                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
#                 "sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]},
#             }},
#             {"$group": {
#                 "_id": "$heure",  # champ heure déjà calculé par le consumer
#                 "avg_score": {"$avg": "$sentiment_score"},
#                 "total": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
#             }},
#             {"$sort": {"_id": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()

#         df = pd.DataFrame([{
#             "mois": f"{r['_id']:02d}:00",   # label "HH:00"
#             "avg_score": round(r["avg_score"],3),
#             "total": r["total"],
#             "neg_pct": round(r["neg_pct"]*100,1),
#             "frustration_pct": round(r["frustration_pct"]*100,1),
#         } for r in results])

#         if len(df) > 2:
#             mean_s = df["avg_score"].mean()
#             std_s  = df["avg_score"].std()
#             if std_s > 0:
#                 df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
#                 df["anomaly_severity"] = np.where(
#                     df["avg_score"] < (mean_s - 2*std_s), "critical",
#                     np.where(df["is_anomaly"], "high", "normal")
#                 )
#             else:
#                 df["is_anomaly"] = False
#                 df["anomaly_severity"] = "normal"
#         return df
#     except Exception as e:
#         print(f"Erreur get_anomaly_data_jour: {e}")
#         return pd.DataFrame()


# def get_lda_topics_jour():
#     """Thèmes filtrés sur aujourd'hui."""
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         local_now = now_local()
#         debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
#         fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

#         pipeline = [
#             {"$match": {
#                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
#                 "theme_pred": {"$exists": True, "$ne": None},
#             }},
#             {"$group": {
#                 "_id": "$theme_pred",
#                 "count": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
#             }},
#             {"$sort": {"count": -1}},
#             {"$limit": 8},
#         ]
#         results = list(_col.aggregate(pipeline))
#         keywords_map = {
#             "reseau":       ["reseau","connexion","4g","internet","signal"],
#             "service":      ["service","client","accueil","conseiller","support"],
#             "prix":         ["prix","tarif","forfait","cher","abonnement"],
#             "hors_sujet":   ["general","information","actualite","annonce"],
#             "installation": ["installation","technicien","rdv","delai","pose"],
#             "facture":      ["facture","paiement","montant","recu","payer"],
#             "saturation":   ["saturation","debit","lent","connexion"],
#             "couverture":   ["couverture","zone","antenne","signal"],
#             "autre":        ["divers","autre","general"],
#             "technique":    ["technique","probleme","bug","erreur","panne"],
#             "produit":      ["produit","qualite","equipement","modem","box"],
#             "attente":      ["attente","delai","long","patienter","lent"],
#         }
#         topics = []
#         for r in results:
#             theme = r["_id"]
#             if not theme:
#                 continue
#             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
#             kw = keywords_map.get(theme.lower(), [theme_fr])
#             topics.append({
#                 "name": theme_fr,
#                 "keywords": kw[:4],
#                 "count": r["count"],
#                 "neg_pct": round(r["neg_pct"]*100,1),
#                 "pos_pct": round(r["pos_pct"]*100,1),
#             })
#         return topics
#     except Exception as e:
#         print(f"Erreur get_lda_topics_jour: {e}")
#         return []


# def get_wordcloud_data_jour():
#     """Wordcloud filtré sur aujourd'hui."""
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         local_now = now_local()
#         debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
#         fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

#         pipeline = [
#             {"$match": {
#                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
#                 "commentaire_normalized": {"$exists": True, "$ne": ""},
#             }},
#             {"$limit": 1000},
#             {"$project": {"commentaire_normalized": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return []
#         words = []
#         for r in results:
#             text = r.get("commentaire_normalized","")
#             if not text:
#                 continue
#             text = text.lower()
#             text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
#             text = re.sub(r'\d+','',text)
#             for word in text.split():
#                 word = word.strip()
#                 if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
#                     words.append(word)
#         if not words:
#             return []
#         wc = Counter(words)
#         top = wc.most_common(60)
#         return [{"word": w, "count": c} for w,c in top]
#     except Exception as e:
#         print(f"Erreur get_wordcloud_data_jour: {e}")
#         return []


# def get_monthly_frequency_jour():
#     """
#     Fréquence par thème pour aujourd'hui, groupée par heure.
#     Utilise le champ 'heure' déjà calculé par le consumer.
#     """
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         local_now = now_local()
#         debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
#         fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

#         pipeline = [
#             {"$match": {
#                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
#                 "theme_pred": {"$exists": True,"$ne": None},
#             }},
#             {"$group": {
#                 "_id": {"heure": "$heure", "theme": "$theme_pred"},
#                 "count": {"$sum": 1},
#             }},
#             {"$sort": {"_id.heure": 1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         data = []
#         for r in results:
#             theme = r["_id"]["theme"]
#             theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
#             heure = r["_id"]["heure"]
#             data.append({"mois": f"{heure:02d}:00", "theme": theme_fr, "count": r["count"]})
#         df = pd.DataFrame(data)
#         top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
#         return df[df["theme"].isin(top6)]
#     except Exception as e:
#         print(f"Erreur get_monthly_frequency_jour: {e}")
#         return pd.DataFrame()


# def get_reason_distribution_jour():
#     """Répartition des raisons pour aujourd'hui."""
#     if not MONGO_AVAILABLE or _col is None:
#         return pd.DataFrame()
#     try:
#         local_now = now_local()
#         debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
#         fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

#         pipeline = [
#             {"$match": {
#                 "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
#                 "reason_pred": {"$exists": True, "$ne": None},
#             }},
#             {"$group": {
#                 "_id": "$reason_pred",
#                 "count": {"$sum": 1},
#                 "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
#                 "confiance": {"$avg": "$sentiment_confiance"},
#             }},
#             {"$sort": {"count": -1}},
#             {"$limit": 10},
#         ]
#         results = list(_col.aggregate(pipeline))
#         if not results:
#             return pd.DataFrame()
#         total = sum(r["count"] for r in results)
#         data = [{
#             "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
#             "count": r["count"],
#             "pct": round(r["count"]/total*100,1),
#             "neg_pct": round(r["neg_pct"]*100,1),
#             "confiance": round((r["confiance"] or 0)*100,1),
#         } for r in results]
#         return pd.DataFrame(data)
#     except Exception as e:
#         print(f"Erreur get_reason_distribution_jour: {e}")
#         return pd.DataFrame()


# def _get_data_jour():
#     """Données filtrées sur aujourd'hui (jamais mises en cache)."""
#     anomaly_df = get_anomaly_data_jour()
#     topics     = get_lda_topics_jour()
#     word_data  = get_wordcloud_data_jour()
#     monthly_df = get_monthly_frequency_jour()
#     reason_df  = get_reason_distribution_jour()

#     if monthly_df is None or monthly_df.empty:
#         monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
#     if reason_df is None or reason_df.empty:
#         reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
#     if anomaly_df is None or anomaly_df.empty:
#         anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

#     return {
#         "anomaly_df": anomaly_df,
#         "topics":     topics if topics else [],
#         "word_data":  word_data if word_data else [],
#         "monthly_df": monthly_df,
#         "reason_df":  reason_df,
#     }


# # ============================================================
# # GRAPHIQUES
# # ============================================================

# def make_reasons_donut(df, theme="light"):
#     c = _colors(theme)
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
#                            font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 280))
#         return fig

#     palette = (BLUE_PALETTE_DARK if theme=="dark" else BLUE_PALETTE_LIGHT)[:len(df)]

#     fig = go.Figure(go.Pie(
#         labels=df["reason"],
#         values=df["count"],
#         hole=0.55,
#         marker=dict(colors=palette, line=dict(color=c["bg"], width=2)),
#         textinfo="label+percent",
#         textposition="outside",
#         textfont=dict(size=9, color=c["text"]),
#         hovertemplate="<b>%{label}</b><br>Volume: %{value:,}<br>Part: %{percent}<br>Insatisfaction: %{customdata}%<extra></extra>",
#         customdata=df["neg_pct"],
#         pull=[0.03 if i == 0 else 0 for i in range(len(df))],
#         sort=False,
#         direction="clockwise",
#     ))

#     layout = _base_layout(c, 280, margin=dict(l=10, r=80, t=30, b=30))
#     layout.update(
#         showlegend=True,
#         legend=dict(
#             orientation="v", x=1.02, y=0.5, xanchor="left", yanchor="middle",
#             font=dict(size=9, color=c["text"]), bgcolor="rgba(0,0,0,0)", borderwidth=0,
#         ),
#         annotations=[dict(
#             text=f"<b>{df['count'].sum():,}</b><br><span style='font-size:8px'>messages</span>",
#             x=0.5, y=0.5,
#             font=dict(size=12, color=c["primary"]),
#             showarrow=False,
#         )],
#     )
#     fig.update_layout(**layout)
#     return fig


# def make_reasons_bar(df, theme="light"):
#     c = _colors(theme)
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
#                            font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 280))
#         return fig

#     df_sorted = df.sort_values("neg_pct", ascending=True).copy()

#     bar_colors = []
#     for p in df_sorted["neg_pct"]:
#         if p >= 60:
#             bar_colors.append(c["danger"])
#         elif p >= 40:
#             bar_colors.append(c["warning"])
#         else:
#             bar_colors.append(c["success"])

#     fig = go.Figure()
#     fig.add_trace(go.Bar(
#         y=df_sorted["reason"],
#         x=df_sorted["neg_pct"],
#         orientation="h",
#         width=0.65,
#         marker=dict(color=bar_colors, line=dict(width=0), cornerradius=4),
#         text=[f"{p:.0f}%" for p in df_sorted["neg_pct"]],
#         textposition="outside",
#         textfont=dict(size=9, weight="bold"),
#         hovertemplate="<b>%{y}</b><br>Insatisfaction: %{x:.1f}%<br>Volume: %{customdata:,}<extra></extra>",
#         customdata=df_sorted["count"],
#     ))

#     fig.add_vline(x=60, line_dash="dash", line_color=c["danger"], line_width=1.5, opacity=0.7)
#     fig.add_vline(x=40, line_dash="dot",  line_color=c["warning"], line_width=1, opacity=0.6)

#     layout = _base_layout(c, 280, margin=dict(l=100, r=50, t=20, b=20))
#     layout.update(
#         xaxis=dict(ticksuffix="%", range=[0, 110], showgrid=True, gridcolor=c["grid"], zeroline=False),
#         yaxis=dict(showgrid=False),
#         showlegend=False,
#         bargap=0.3,
#     )
#     fig.update_layout(**layout)
#     return fig


# def make_anomaly_chart(df, theme="light", x_title="Période"):
#     c = _colors(theme)
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnee pour cette période", x=0.5, y=0.5,
#                            showarrow=False, font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 240))
#         return fig

#     fig = go.Figure()
#     r,g,b_ = int(c["primary"][1:3],16), int(c["primary"][3:5],16), int(c["primary"][5:7],16)
#     fig.add_trace(go.Scatter(
#         x=df["mois"], y=df["avg_score"],
#         mode="lines+markers",
#         name="Score satisfaction",
#         line=dict(color=c["primary"], width=2.5),
#         fill="tozeroy",
#         fillcolor=f"rgba({r},{g},{b_},0.08)",
#         marker=dict(size=8, color=c["primary"], line=dict(color=c["bg"], width=2)),
#         hovertemplate=f"{x_title}: %{{x}}<br>Score: %{{y:.3f}}<br>Insatisfaits: %{{customdata:.1f}}%<extra></extra>",
#         customdata=df["neg_pct"],
#     ))

#     if "is_anomaly" in df.columns:
#         anom = df[df["is_anomaly"]]
#         if not anom.empty:
#             fig.add_trace(go.Scatter(
#                 x=anom["mois"], y=anom["avg_score"],
#                 mode="markers",
#                 marker=dict(symbol="x", size=12, color=c["danger"],
#                             line=dict(width=2, color="white")),
#                 name="Période dégradée",
#                 hovertemplate="ALERTE — %{x}<br>Score: %{y:.3f}<extra></extra>",
#             ))

#     mean_s = df["avg_score"].mean()
#     fig.add_hline(y=mean_s, line_dash="dash", line_color=c["neutral"], opacity=0.5)

#     layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
#     layout.update(
#         xaxis=dict(title=x_title, tickangle=-30, tickfont=dict(size=8), nticks=6),
#         yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False),
#         legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=8)),
#         hovermode="x unified",
#     )
#     fig.update_layout(**layout)
#     return fig


# def make_monthly_frequency_chart(df, theme="light", x_title="Période"):
#     c = _colors(theme)
#     multi_palette = [c["primary"], c["danger"], c["warning"], c["success"], "#6c5ce7", "#00cec9"]
#     if df.empty:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5,
#                            showarrow=False, font=dict(color=c["neutral"]))
#         fig.update_layout(**_base_layout(c, 240))
#         return fig

#     fig = go.Figure()
#     for i, th in enumerate(df["theme"].unique()):
#         sub = df[df["theme"] == th].sort_values("mois")
#         fig.add_trace(go.Scatter(
#             x=sub["mois"], y=sub["count"],
#             mode="lines+markers",
#             name=th,
#             line=dict(width=1.5, color=multi_palette[i % len(multi_palette)]),
#             marker=dict(size=5),
#             hovertemplate=f"<b>%{{fullData.name}}</b><br>{x_title}: %{{x}}<br>Messages: %{{y:,}}<extra></extra>",
#         ))

#     layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
#     layout.update(
#         xaxis=dict(title=x_title, tickangle=-30, tickfont=dict(size=8), nticks=6),
#         yaxis=dict(title="Messages", tickformat=","),
#         legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=7)),
#         hovermode="x unified",
#     )
#     fig.update_layout(**layout)
#     return fig


# # ============================================================
# # WORDCLOUD
# # ============================================================

# def make_wordcloud_iframe(word_data, theme="light"):
#     if not word_data:
#         return html.Div([
#             html.I(className="fas fa-cloud",
#                    style={"fontSize":"28px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
#             html.P("Aucune donnee textuelle",
#                    style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
#         ], style={"textAlign":"center","padding":"30px","display":"flex",
#                   "flexDirection":"column","alignItems":"center"})

#     bg_color = "#1a2540" if theme == "dark" else "#ffffff"
#     max_c = max(w["count"] for w in word_data)
#     min_c = min(w["count"] for w in word_data)
#     rng   = max_c - min_c if max_c != min_c else 1

#     words_js = json.dumps([
#         [w["word"], round(10 + (w["count"] - min_c) / rng * 58)]
#         for w in word_data
#     ])

#     colors_light = ["#003087","#1a4fa0","#4a80d4","#e8384f","#f59e0b","#00a854","#6c8dcc"]
#     colors_dark  = ["#4a80d4","#6a9ae0","#8ab8e4","#2ecc71","#f06070","#f39c12","#a78bfa"]
#     colors_js = json.dumps(colors_dark if theme == "dark" else colors_light)

#     html_content = f"""<!DOCTYPE html>
# <html><head><meta charset="utf-8">
# <style>
#   *{{margin:0;padding:0;box-sizing:border-box}}
#   body{{background:{bg_color};width:100%;height:100%;overflow:hidden;
#         display:flex;align-items:center;justify-content:center}}
#   #wc{{width:100%;height:100%;display:block}}
# </style>
# <script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js"></script>
# </head><body>
# <canvas id="wc"></canvas>
# <script>
#   var words={words_js};
#   var colors={colors_js};
#   var ci=0;
#   function init(){{
#     var c=document.getElementById('wc');
#     var W=window.innerWidth||600,H=window.innerHeight||320;
#     c.width=W;c.height=H;
#     WordCloud(c,{{
#       list:words,
#       gridSize:Math.round(6*W/700),
#       weightFactor:function(s){{return s*(W/600)}},
#       fontFamily:"'Segoe UI','DM Sans',sans-serif",
#       color:function(){{return colors[(ci++)%colors.length]}},
#       rotateRatio:0.3,rotationSteps:3,
#       backgroundColor:'{bg_color}',
#       shuffle:true,drawOutOfBound:false,shrinkToFit:true,minSize:8,
#     }});
#   }}
#   if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
#   else init();
#   window.addEventListener('resize',function(){{setTimeout(init,100)}});
# </script>
# </body></html>"""

#     return html.Iframe(
#         srcDoc=html_content,
#         style={
#             "width": "100%", "height": "340px", "border": "none",
#             "borderRadius": "8px", "background": bg_color, "display": "block",
#         },
#     )


# # ============================================================
# # COMPOSANTS HTML
# # ============================================================

# def make_anomaly_banner(anomaly_df):
#     no_anomaly = (
#         anomaly_df.empty
#         or "is_anomaly" not in anomaly_df.columns
#         or int(anomaly_df["is_anomaly"].sum()) == 0
#     )

#     if no_anomaly:
#         return html.Div(
#             id="tt-anomaly-banner",
#             children=[
#                 html.Div([
#                     html.I(className="fas fa-check-circle",
#                            style={"fontSize":"12px","color":"var(--tt-green, #04723b)",
#                                   "marginRight":"8px","flexShrink":"0"}),
#                     html.Strong("Aucune anomalie détectée", style={"fontSize":"10px"}),
#                 ], style={"display":"flex","alignItems":"center","flex":"1"}),
#                 html.Button(
#                     html.I(className="fas fa-times", style={"fontSize":"9px"}),
#                     id="close-anomaly-banner-btn", n_clicks=0,
#                     style={"background":"transparent","border":"none",
#                            "color":"var(--tt-green, #00a854)",
#                            "cursor":"pointer","padding":"2px 5px",
#                            "borderRadius":"4px","flexShrink":"0"},
#                 ),
#             ],
#             style={
#                 "display":"flex","alignItems":"center","justifyContent":"space-between",
#                 "padding":"6px 12px","borderRadius":"8px",
#                 "background":"rgba(0,168,84,0.07)","border":"1px solid rgba(0,168,84,0.18)",
#                 "marginBottom":"8px",
#             },
#         )

#     n_anom = int(anomaly_df["is_anomaly"].sum())
#     n_crit = int((anomaly_df.get("anomaly_severity", pd.Series([])) == "critical").sum()) \
#              if "anomaly_severity" in anomaly_df.columns else 0
#     txt = f"{n_anom} période(s) anormalement dégradée(s)" + (f" (dont {n_crit} critique)" if n_crit else "")

#     return html.Div(
#         id="tt-anomaly-banner",
#         children=[
#             html.Div([
#                 html.I(className="fas fa-exclamation-triangle",
#                        style={"fontSize":"12px","color":"var(--tt-red, #e8384f)",
#                               "marginRight":"8px","flexShrink":"0"}),
#                 html.Strong(txt, style={"fontSize":"10px"}),
#             ], style={"display":"flex","alignItems":"center","flex":"1"}),
#             html.Button(
#                 html.I(className="fas fa-times", style={"fontSize":"9px"}),
#                 id="close-anomaly-banner-btn", n_clicks=0,
#                 style={"background":"transparent","border":"none",
#                        "color":"var(--tt-red, #e8384f)",
#                        "cursor":"pointer","padding":"2px 5px",
#                        "borderRadius":"4px","flexShrink":"0"},
#             ),
#         ],
#         style={
#             "display":"flex","alignItems":"center","justifyContent":"space-between",
#             "padding":"6px 12px","borderRadius":"8px",
#             "background":"rgba(232,56,79,0.07)","border":"1px solid rgba(232,56,79,0.18)",
#             "marginBottom":"8px",
#         },
#     )


# def make_topics_list(topics, theme="light"):
#     if not topics:
#         return html.Div([
#             html.I(className="fas fa-tags",
#                    style={"fontSize":"24px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
#             html.P("Aucun thème détecté",
#                    style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
#         ], style={"textAlign":"center","padding":"30px","display":"flex",
#                   "flexDirection":"column","alignItems":"center"})

#     c = _colors(theme)
#     items = []
#     for t in topics:
#         if t["neg_pct"] > 60:
#             neg_col   = c["danger"]
#             badge_txt = "Critique"
#         elif t["neg_pct"] > 40:
#             neg_col   = c["warning"]
#             badge_txt = "Alerte"
#         else:
#             neg_col   = c["success"]
#             badge_txt = "Normal"

#         items.append(html.Div([
#             html.Div([
#                 html.Div(style={
#                     "width":"5px","height":"5px","borderRadius":"50%",
#                     "background":neg_col,"flexShrink":"0",
#                 }),
#                 html.Span(t["name"], style={
#                     "fontSize":"10px","fontWeight":"600",
#                     "color":"var(--tt-text, #1a2a4a)","flex":"1",
#                 }),
#                 html.Span(badge_txt, style={
#                     "fontSize":"9px","fontWeight":"600",
#                     "color": neg_col,
#                     "padding":"2px 6px","borderRadius":"8px",
#                     "background": f"rgba({','.join(str(int(neg_col.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.1)",
#                 }),
#             ], style={"display":"flex","alignItems":"center","gap":"6px","marginBottom":"4px"}),

#             html.Div([
#                 html.I(className="fas fa-comment-dots",
#                        style={"fontSize":"8px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
#                 html.Span(f"{t['count']:,} messages",
#                           style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
#                 html.Span(" · ", style={"color":"var(--tt-border, #ccc)","margin":"0 3px"}),
#                 html.Span(f"{t['neg_pct']}% insatisfaits",
#                           style={"fontSize":"8px","color":neg_col,"fontWeight":"600"}),
#             ], style={"display":"flex","alignItems":"center","flexWrap":"wrap","marginBottom":"4px"}),

#             html.Div([
#                 html.I(className="fas fa-key",
#                        style={"fontSize":"7px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
#                 html.Span("Mots-clés : ",
#                           style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
#                 html.Span(", ".join(t["keywords"][:3]),
#                           style={"fontSize":"8px","fontWeight":"500",
#                                  "color":"var(--tt-text, #1a2a4a)"}),
#             ], style={"display":"flex","alignItems":"center","marginBottom":"5px","flexWrap":"wrap"}),

#             html.Div(
#                 html.Div(style={
#                     "height":"100%","width":f"{min(t['neg_pct'],100)}%",
#                     "background":neg_col,"borderRadius":"2px",
#                     "transition":"width 0.4s ease",
#                 }),
#                 className="tt-topic-bar-track",
#             ),
#         ], className="tt-topic-item"))

#     return html.Div(items, className="tt-topics-list")


# # ============================================================
# # HELPER : carte générique pour grille 3x2
# # ============================================================

# def _chart_card(icon, title, tooltip_title, tooltip_body, children):
#     return html.Div([
#         html.Div([
#             html.Div([html.I(className=icon, style={"fontSize":"13px"})],
#                      className="card-icon"),
#             html.Span(title, className="card-title"),
#             html.Div([
#                 html.Div(
#                     html.I(className="fas fa-info-circle", style={"fontSize":"10px"}),
#                     className="tooltip-icon",
#                 ),
#                 html.Div([
#                     html.Div(tooltip_title, className="tooltip-title"),
#                     html.Div(tooltip_body,  className="tooltip-body"),
#                 ], className="card-tooltip"),
#             ], className="tooltip-wrapper"),
#         ], className="card-header"),
#         html.Div(children, className="card-content"),
#     ], className="chart-card", style={"padding":"14px 16px","borderRadius":"14px","height":"100%"})


# # ============================================================
# # CACHE
# # ============================================================

# _cache = {}

# def _get_data():
#     global _cache
#     if not _cache:
#         print("Chargement des données depuis MongoDB...")
#         anomaly_df = get_anomaly_data()
#         topics     = get_lda_topics()
#         word_data  = get_wordcloud_data()
#         monthly_df = get_monthly_frequency()
#         reason_df  = get_reason_distribution()

#         if monthly_df is None or monthly_df.empty:
#             monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
#         if reason_df is None or reason_df.empty:
#             reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
#         if anomaly_df is None or anomaly_df.empty:
#             anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

#         _cache["anomaly_df"] = anomaly_df
#         _cache["topics"]     = topics if topics else []
#         _cache["word_data"]  = word_data if word_data else []
#         _cache["monthly_df"] = monthly_df
#         _cache["reason_df"]  = reason_df

#     return _cache


# def _get_data_mois():
#     """Données filtrées sur le mois courant (pas mises en cache longtemps)."""
#     anomaly_df = get_anomaly_data_mois()
#     topics     = get_lda_topics_mois()
#     word_data  = get_wordcloud_data_mois()
#     monthly_df = get_monthly_frequency_mois()
#     reason_df  = get_reason_distribution_mois()

#     if monthly_df is None or monthly_df.empty:
#         monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
#     if reason_df is None or reason_df.empty:
#         reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
#     if anomaly_df is None or anomaly_df.empty:
#         anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

#     return {
#         "anomaly_df": anomaly_df,
#         "topics":     topics if topics else [],
#         "word_data":  word_data if word_data else [],
#         "monthly_df": monthly_df,
#         "reason_df":  reason_df,
#     }


# # ============================================================
# # HELPER GRILLE — construit la grille 3×2 avec les données
# # ============================================================

# def _make_grid(d, theme, periode="global"):
#     """
#     Construit la grille 3×2 avec les données fournies.
#     periode = "global" | "mois" | "jour"
#     """
#     if periode == "jour":
#         x_title_chart = "Heure"
#         anom_tooltip  = "Score de satisfaction horaire pour aujourd'hui. Les croix signalent les heures anormales."
#         evol_tooltip  = "Evolution du nombre de messages par thème sur les heures de la journée."
#     elif periode == "mois":
#         x_title_chart = "Jour"
#         anom_tooltip  = "Score de satisfaction journalier pour le mois en cours. Les croix signalent les jours anormaux."
#         evol_tooltip  = "Evolution du nombre de messages par thème et par jour pour le mois en cours."
#     else:
#         x_title_chart = "Mois"
#         anom_tooltip  = "Score de satisfaction mensuel. Les croix signalent des mois anormaux."
#         evol_tooltip  = "Evolution du nombre de messages par thème et par mois."

#     return html.Div(className="grid-3x2", children=[

#         # LIGNE 1 : ÉVOLUTION | ANOMALIES
#         html.Div(className="grid-row", children=[
#             _chart_card(
#                 "fas fa-chart-line", "ÉVOLUTION PAR THÈME",
#                 "Fréquence par sujet",
#                 evol_tooltip,
#                 dcc.Graph(
#                     id="tt-monthly-chart",
#                     figure=make_monthly_frequency_chart(d["monthly_df"], theme, x_title=x_title_chart),
#                     config={"displayModeBar": False},
#                     style={"height": "280px"},
#                 ),
#             ),
#             _chart_card(
#                 "fas fa-exclamation-triangle", "DÉTECTION DES ANOMALIES",
#                 "Anomalies de satisfaction",
#                 anom_tooltip,
#                 html.Div([
#                     html.Div(
#                         id="tt-anomaly-banner-container",
#                         children=make_anomaly_banner(d["anomaly_df"]),
#                     ),
#                     dcc.Graph(
#                         id="tt-anomaly-chart",
#                         figure=make_anomaly_chart(d["anomaly_df"], theme, x_title=x_title_chart),
#                         config={"displayModeBar": False},
#                         style={"height": "250px"},
#                     ),
#                 ]),
#             ),
#         ]),

#         # LIGNE 2 : INSATISFACTION | SUJETS
#         html.Div(className="grid-row", children=[
#             _chart_card(
#                 "fas fa-chart-bar", "TAUX D'INSATISFACTION",
#                 "Raisons classées par criticité",
#                 "Les raisons sont triées du plus critique au moins critique.",
#                 dcc.Graph(
#                     id="tt-reasons-bar",
#                     figure=make_reasons_bar(d["reason_df"], theme),
#                     config={"displayModeBar": False},
#                     style={"height":"280px"},
#                 ),
#             ),
#             _chart_card(
#                 "fas fa-tags", "SUJETS LES PLUS ABORDÉS",
#                 "Thèmes principaux identifiés",
#                 "Catégories détectées automatiquement depuis les commentaires.",
#                 html.Div(
#                     id="tt-topics-list",
#                     children=make_topics_list(d["topics"], theme),
#                     style={"height":"280px","overflowY":"auto"},
#                 ),
#             ),
#         ]),

#         # LIGNE 3 : RÉPARTITION | VOCABULAIRE
#         html.Div(className="grid-row", children=[
#             _chart_card(
#                 "fas fa-chart-pie", "RÉPARTITION DES RAISONS",
#                 "Distribution des raisons détectées",
#                 "Répartition par volume des principales raisons détectées automatiquement.",
#                 dcc.Graph(
#                     id="tt-reasons-donut",
#                     figure=make_reasons_donut(d["reason_df"], theme),
#                     config={"displayModeBar": False},
#                     style={"height":"280px"},
#                 ),
#             ),
#             _chart_card(
#                 "fas fa-comment-dots", "VOCABULAIRE CLIENTS",
#                 "Nuage de mots",
#                 "Mots les plus utilisés dans les commentaires (français, arabe, darija).",
#                 html.Div(
#                     id="tt-wordcloud",
#                     children=make_wordcloud_iframe(d["word_data"], theme),
#                     style={"height":"280px"},
#                 ),
#             ),
#         ]),
#     ])


# # ============================================================
# # LAYOUT PRINCIPAL
# # ============================================================

# def render_page(theme="light", user_data=None):
#     print("Chargement Thèmes & Temporel...")
#     d = _get_data()
#     today = now_local().strftime("%d/%m/%Y")

#     style_active = {
#         "padding": "6px 16px", "borderRadius": "20px", "border": "none",
#         "background": BLUE, "color": "white", "cursor": "pointer",
#         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
#         "display": "flex", "alignItems": "center", "gap": "6px",
#     }
#     style_inactive = {
#         "padding": "6px 16px", "borderRadius": "20px", "border": f"1px solid {BLUE}",
#         "background": "transparent", "color": BLUE, "cursor": "pointer",
#         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
#         "display": "flex", "alignItems": "center", "gap": "6px",
#     }

#     content = html.Div(
#         className="dashboard-container themes-temporal-page",
#         **{"data-theme": theme, "data-page": "themes-temporal"},
#         children=[
#             # ── Header ──────────────────────────────────────────────────────
#             html.Div(
#                 [
#                     # Bannière statut anomalie
#                     html.Div(
#                         # [
#                         #     html.I(className="fas fa-check-circle",
#                         #            style={"fontSize":"14px","color":"#ffffff","marginRight":"10px","flexShrink":"0"}),
#                         #     html.Strong("Aucune anomalie détectée",
#                         #                 style={"fontSize":"14px","fontWeight":"600","color":"#ffffff"}),
#                         # ],
#                         # style={
#                         #     "display":"flex","alignItems":"center","padding":"0 20px",
#                         #     "borderRadius":"8px","background":"#04723b",
#                         #     "border":"1px solid #046635","height":"40px","width":"250px",
#                         #     "boxShadow":"0 2px 4px rgba(0,0,0,0.1)",
#                         # }
#                     ),

#                     # Groupe droite
#                     html.Div(
#                         [
#                             # Boutons Global / Ce Mois / Aujourd'hui
#                             html.Div([
#                                 html.Button(
#                                     [html.I(className="fas fa-globe", style={"fontSize":"11px"}), "Global"],
#                                     id="tt-btn-global",
#                                     n_clicks=0,
#                                     style=style_active,
#                                 ),
#                                 html.Button(
#                                     [html.I(className="fas fa-calendar-day", style={"fontSize":"11px"}), "Ce Mois"],
#                                     id="tt-btn-mois",
#                                     n_clicks=0,
#                                     style=style_inactive,
#                                 ),
#                                 html.Button(
#                                     [html.I(className="fas fa-clock", style={"fontSize":"11px"}), "Aujourd'hui"],
#                                     id="tt-btn-jour",
#                                     n_clicks=0,
#                                     style=style_inactive,
#                                 ),
#                             ], style={"display":"flex","alignItems":"center","gap":"8px"}),

#                             # Badge date
#                             html.Div(
#                                 [
#                                     html.I(className="far fa-calendar-alt",
#                                            style={"marginRight":"5px","fontSize":"13px"}),
#                                     html.Span(f"Mise à jour : {today}", style={"fontSize":"13px"}),
#                                 ],
#                                 style={
#                                     "display":"flex","alignItems":"center","background":"white",
#                                     "padding":"0 15px","borderRadius":"8px","height":"40px",
#                                     "border":"1px solid #e0e0e0",
#                                 }
#                             ),

#                             # Bouton Actualiser
#                             html.Button(
#                                 [html.I(className="fas fa-sync-alt",
#                                         style={"marginRight":"5px","fontSize":"13px"}),
#                                  html.Span("Actualiser", style={"fontSize":"13px"})],
#                                 id="tt-refresh-btn",
#                                 n_clicks=0,
#                                 style={
#                                     "background": BLUE, "color":"white","border":"none",
#                                     "borderRadius":"8px","padding":"0 20px","cursor":"pointer",
#                                     "fontSize":"13px","display":"flex","alignItems":"center",
#                                     "height":"40px","gap":"8px",
#                                 },
#                             ),
#                         ],
#                         style={"display":"flex","gap":"12px","alignItems":"center"}
#                     ),
#                 ],
#                 style={"display":"flex","justifyContent":"space-between",
#                        "alignItems":"center","marginBottom":"20px"}
#             ),

#             # Store période
#             dcc.Store(id="tt-periode-store", data="global"),

#             # ── Zone grille : Global (visible par défaut) ──────────────────
#             html.Div(
#                 id="tt-global-content",
#                 style={"display": "block"},
#                 children=[_make_grid(d, theme, periode="global")],
#             ),

#             # ── Zone grille : Ce Mois (cachée par défaut) ──────────────────
#             html.Div(
#                 id="tt-mois-content",
#                 style={"display": "none"},
#                 children=[],
#             ),

#             # ── Zone grille : Aujourd'hui (cachée par défaut) ──────────────
#             html.Div(
#                 id="tt-jour-content",
#                 style={"display": "none"},
#                 children=[],
#             ),
#         ],
#     )

#     return make_page_layout(
#         "themes-temporal",
#         "Thèmes & Analyse Temporelle",
#         "Quels sujets génèrent le plus d'insatisfaction ? Quels mois ont été les plus difficiles ?",
#         content,
#         theme,
#         user_data,
#     )


# # ============================================================
# # CALLBACKS
# # ============================================================

# # ── Basculer Global / Ce Mois / Aujourd'hui ──────────────────────────────────
# @callback(
#     Output("tt-periode-store", "data"),
#     Output("tt-btn-global", "style"),
#     Output("tt-btn-mois",   "style"),
#     Output("tt-btn-jour",   "style"),
#     Input("tt-btn-global", "n_clicks"),
#     Input("tt-btn-mois",   "n_clicks"),
#     Input("tt-btn-jour",   "n_clicks"),
#     prevent_initial_call=True,
# )
# def tt_set_periode(n_global, n_mois, n_jour):
#     style_active = {
#         "padding": "6px 16px", "borderRadius": "20px", "border": "none",
#         "background": BLUE, "color": "white", "cursor": "pointer",
#         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
#         "display": "flex", "alignItems": "center", "gap": "6px",
#     }
#     style_inactive = {
#         "padding": "6px 16px", "borderRadius": "20px", "border": f"1px solid {BLUE}",
#         "background": "transparent", "color": BLUE, "cursor": "pointer",
#         "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
#         "display": "flex", "alignItems": "center", "gap": "6px",
#     }
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return "global", style_active, style_inactive, style_inactive
#     btn = ctx.triggered[0]["prop_id"].split(".")[0]
#     if btn == "tt-btn-mois":
#         return "mois", style_inactive, style_active, style_inactive
#     if btn == "tt-btn-jour":
#         return "jour", style_inactive, style_inactive, style_active
#     return "global", style_active, style_inactive, style_inactive


# # ── Afficher/cacher les zones Global / Ce Mois / Aujourd'hui ─────────────────
# @callback(
#     Output("tt-global-content", "style"),
#     Output("tt-mois-content",   "style"),
#     Output("tt-mois-content",   "children"),
#     Output("tt-jour-content",   "style"),
#     Output("tt-jour-content",   "children"),
#     Input("tt-periode-store", "data"),
#     State("theme-store", "data"),
#     prevent_initial_call=False,
# )
# def tt_toggle_content(periode, theme):
#     theme = theme or "light"
#     local_now = now_local()

#     # ── Bandeau Ce Mois ──────────────────────────────────────────────
#     if periode == "mois":
#         mois_lbl = local_now.strftime("%B %Y")
#         d_mois   = _get_data_mois()
#         bandeau  = _make_bandeau(
#             icon="fas fa-calendar-day",
#             label=f"Statistiques de {mois_lbl}",
#             sublabel="Données filtrées sur le mois en cours",
#         )
#         grid_mois = _make_grid(d_mois, theme, periode="mois")
#         return (
#             {"display": "none"},
#             {"display": "block"},
#             [bandeau, grid_mois],
#             {"display": "none"},
#             [],
#         )

#     # ── Bandeau Aujourd'hui ──────────────────────────────────────────
#     if periode == "jour":
#         jour_lbl = local_now.strftime("%A %d %B %Y")
#         d_jour   = _get_data_jour()
#         total_msgs = int(d_jour["anomaly_df"]["total"].sum()) if not d_jour["anomaly_df"].empty else 0
#         bandeau  = _make_bandeau(
#             icon="fas fa-clock",
#             label=f"Aujourd'hui — {jour_lbl}",
#             sublabel=f"{total_msgs:,} message(s) reçu(s) aujourd'hui · données en temps réel",
#         )
#         grid_jour = _make_grid(d_jour, theme, periode="jour")
#         return (
#             {"display": "none"},
#             {"display": "none"},
#             [],
#             {"display": "block"},
#             [bandeau, grid_jour],
#         )

#     # ── Global ───────────────────────────────────────────────────────
#     return (
#         {"display": "block"},
#         {"display": "none"},
#         [],
#         {"display": "none"},
#         [],
#     )


# def _make_bandeau(icon, label, sublabel):
#     """Bandeau titre commun pour Ce Mois et Aujourd'hui."""
#     return html.Div([
#         html.Div(style={
#             "width":"4px","height":"28px","borderRadius":"4px",
#             "background": BLUE, "marginRight":"12px",
#         }),
#         html.I(className=icon,
#                style={"fontSize":"16px","color": BLUE,"marginRight":"10px"}),
#         html.Span(label, style={
#             "fontSize":"14px","fontWeight":"700","color": BLUE,"letterSpacing":"0.3px",
#         }),
#         html.Span(sublabel, style={
#             "fontSize":"11px","color": NEUTRAL,"marginLeft":"12px",
#         }),
#     ], style={
#         "display":"flex","alignItems":"center","padding":"10px 16px",
#         "background":"var(--bg-card)","borderRadius":"12px","marginBottom":"20px",
#         "border":f"1px solid {BLUE_LIGHT}","boxShadow":"0 1px 3px rgba(0,0,0,0.05)",
#     })


# # ── Mise à jour des graphiques selon thème ───────────────────────────────────
# @callback(
#     Output("tt-anomaly-chart", "figure"),
#     Output("tt-monthly-chart", "figure"),
#     Output("tt-reasons-donut", "figure"),
#     Output("tt-reasons-bar",   "figure"),
#     Input("theme-store",       "data"),
#     Input("tt-periode-store",  "data"),
#     State("auth-store",        "data"),
# )
# def update_charts(theme, periode, auth_data):
#     theme = theme or "light"
#     if periode == "mois":
#         d = _get_data_mois()
#         x_title = "Jour"
#     elif periode == "jour":
#         d = _get_data_jour()
#         x_title = "Heure"
#     else:
#         d = _get_data()
#         x_title = "Mois"
#     return (
#         make_anomaly_chart(d["anomaly_df"], theme, x_title=x_title),
#         make_monthly_frequency_chart(d["monthly_df"], theme, x_title=x_title),
#         make_reasons_donut(d["reason_df"], theme),
#         make_reasons_bar(d["reason_df"], theme),
#     )


# @callback(
#     Output("tt-wordcloud",   "children"),
#     Output("tt-topics-list", "children"),
#     Input("theme-store",     "data"),
#     Input("tt-periode-store","data"),
#     State("auth-store",      "data"),
# )
# def update_wordcloud_and_topics(theme, periode, auth_data):
#     theme = theme or "light"
#     if periode == "mois":
#         d = _get_data_mois()
#     elif periode == "jour":
#         d = _get_data_jour()
#     else:
#         d = _get_data()
#     return (
#         make_wordcloud_iframe(d["word_data"], theme),
#         make_topics_list(d["topics"], theme),
#     )


# @callback(
#     Output("tt-anomaly-banner-container", "children"),
#     Input("close-anomaly-banner-btn", "n_clicks"),
#     prevent_initial_call=True,
# )
# def close_anomaly_banner(n_clicks):
#     if n_clicks:
#         return None
#     return dash.no_update


# @callback(
#     Output("tt-page-content", "children"),
#     Input("theme-store", "data"),
#     Input("auth-store",  "data"),
# )
# def themes_page_with_auth(theme, auth_data):
#     theme = theme or "light"
#     user_data = None
#     if auth_data and auth_data.get("is_authenticated"):
#         user_data = auth_data.get("user", {})
#     return render_page(theme, user_data)


# @callback(
#     Output("tt-page-content", "children", allow_duplicate=True),
#     Input("tt-refresh-btn", "n_clicks"),
#     State("theme-store", "data"),
#     State("auth-store",  "data"),
#     prevent_initial_call=True,
# )
# def refresh_data(n_clicks, theme, auth_data):
#     """Vide le cache et recharge toutes les données."""
#     global _cache
#     if n_clicks and n_clicks > 0:
#         _cache = {}
#         theme = theme or "light"
#         user_data = None
#         if auth_data and auth_data.get("is_authenticated"):
#             user_data = auth_data.get("user", {})
#         return render_page(theme, user_data)
#     return dash.no_update


# # ============================================================
# # LAYOUT ENTRY POINT
# # ============================================================

# layout = html.Div(id="tt-page-content")


# @callback(
#     Output("tt-page-content", "children", allow_duplicate=True),
#     Input("_pages_location", "pathname"),
#     prevent_initial_call=True,
# )
# def init_themes_page(pathname):
#     if pathname == "/themes-temporal":
#         return render_page("light")
#     return dash.no_update

""" themes_temporal.py — REFONTE UI/UX PROFESSIONNELLE
✅ Grille 3×2 (3 lignes, 2 colonnes)
✅ Style Power BI / Desktop
✅ Date placée à droite
✅ Pas d'emoji, uniquement icônes FontAwesome
✅ Couleurs Algérie Télécom (#003087, #00a854, #e8384f, #f59e0b)
✅ Logique Global / Ce Mois / Aujourd'hui (même logique que dashboard.py)
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os, re, json
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from database import MONGO_AVAILABLE, _col

dash.register_page(__name__, path='/themes-temporal', name='Thèmes & Temporel')

# ============================================================
# CONSTANTES COULEURS
# ============================================================

BLUE       = "#003087"
BLUE_MID   = "#1a4fa0"
BLUE_LIGHT = "#e8f0fb"
GREEN      = "#00a854"
RED        = "#e8384f"
ORANGE     = "#f59e0b"
NEUTRAL    = "#64748b"

TZ_OFFSET = timedelta(hours=1)

def now_local():
    return datetime.utcnow() + TZ_OFFSET

# ============================================================
# MAPPINGS
# ============================================================

THEME_MAPPING = {
    "reseau":       "Réseau Technique",
    "technique":    "Problèmes Techniques",
    "service":      "Service Client",
    "client":       "Service Client",
    "attente":      "Délais d'attente",
    "prix":         "Tarifs",
    "facture":      "Facturation",
    "produit":      "Qualité Produit",
    "offre":        "Offres Promo",
    "hors_sujet":   "Hors Sujet",
    "information":  "Information Générale",
    "installation": "Installation",
    "equipement":   "Équipement",
    "saturation":   "Saturation Réseau",
    "couverture":   "Couverture",
    "debit":        "Débit Internet",
    "autre":        "Autre",
}

REASON_MAPPING = {
    "reseau":       "Réseau",
    "service":      "Service Client",
    "prix":         "Tarifs",
    "attente":      "Attente",
    "hors_sujet":   "Hors Sujet",
    "installation": "Installation",
    "facture":      "Facturation",
    "saturation":   "Saturation",
    "couverture":   "Couverture",
    "autre":        "Autre",
    "technique":    "Technique",
    "produit":      "Produit",
}

STOPWORDS = {
    "le","la","les","un","une","des","du","de","et","ou","mais","donc","or","ni","car",
    "je","tu","il","elle","on","nous","vous","ils","elles","me","te","se","ce","cet",
    "cette","ces","mon","ton","son","notre","votre","leur","que","qui","quoi","dont",
    "est","sont","être","avoir","faire","dire","aller","voir","pouvoir","vouloir",
    "a","dans","pour","par","avec","sans","sur","sous","entre","très","trop",
    "peu","fort","bien","mal","oui","non","ainsi","plus","pas","tout","ça","si","ya",
    "ال","و","في","من","على","إلى","ب","عن","مع","ما","هذا","هذه","ذلك","تلك",
    "كان","كانت","يكون","أن","إن","أنه","لأن","حتى","إذا","فقد","قد","هل","أين",
    "لم","لن","له","لها","لهم","لهن","هو","هي","هم","هن",
}

# ============================================================
# COULEURS THÈME
# ============================================================

def _colors(theme):
    if theme == "dark":
        return {
            "bg": "#141c2e", "paper_bg": "#1a2540", "text": "#dce8f5",
            "grid": "#1e2d47", "primary": "#4a80d4", "success": "#2ecc71",
            "danger": "#f06070", "warning": "#f39c12", "neutral": "#607b99",
            "secondary": "#6c8dcc", "blue_light": "#8ab8e4", "blue_dark": "#2c5f8a",
        }
    return {
        "bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
        "grid": "#e8edf5", "primary": "#003087", "success": "#00a854",
        "danger": "#e8384f", "warning": "#f59e0b", "neutral": "#64748b",
        "secondary": "#1a4fa0", "blue_light": "#4a80d4", "blue_dark": "#1a4a8a",
    }


def _base_layout(c, height, margin=None):
    m = margin or dict(l=10, r=10, t=20, b=10)
    return dict(
        plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
        font=dict(color=c["text"], family="'Segoe UI', 'DM Sans', sans-serif", size=10),
        height=height, margin=m,
    )


BLUE_PALETTE_LIGHT = ["#003087","#1a4fa0","#2d66bb","#4a80d4","#6c8dcc","#8ab8e4"]
BLUE_PALETTE_DARK  = ["#4a80d4","#6a9ae0","#8ab8e4","#5a8ed8","#7aaae0","#3a6fc4"]


# ============================================================
# EXTRACTION MONGODB — GLOBAL
# ============================================================

def get_anomaly_data():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        pipeline = [
            {"$match": {"sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]}, "mois": {"$exists": True}}},
            {"$group": {
                "_id": "$mois",
                "avg_score": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        df = pd.DataFrame([{
            "mois": r["_id"],
            "avg_score": round(r["avg_score"],3),
            "total": r["total"],
            "neg_pct": round(r["neg_pct"]*100,1),
            "frustration_pct": round(r["frustration_pct"]*100,1),
        } for r in results])
        if len(df) > 2:
            mean_s = df["avg_score"].mean()
            std_s  = df["avg_score"].std()
            if std_s > 0:
                df["is_anomaly"] = df["avg_score"] < (mean_s - 1.5*std_s)
                df["anomaly_severity"] = np.where(
                    df["avg_score"] < (mean_s - 2*std_s), "critical",
                    np.where(df["is_anomaly"], "high", "normal")
                )
            else:
                df["is_anomaly"] = False
                df["anomaly_severity"] = "normal"
        return df
    except Exception as e:
        print(f"Erreur get_anomaly_data: {e}")
        return pd.DataFrame()


def get_lda_topics():
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        pipeline = [
            {"$match": {"theme_pred": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$theme_pred",
                "count": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 8},
        ]
        results = list(_col.aggregate(pipeline))
        keywords_map = {
            "reseau":       ["reseau","connexion","4g","internet","signal"],
            "service":      ["service","client","accueil","conseiller","support"],
            "prix":         ["prix","tarif","forfait","cher","abonnement"],
            "hors_sujet":   ["general","information","actualite","annonce"],
            "installation": ["installation","technicien","rdv","delai","pose"],
            "facture":      ["facture","paiement","montant","recu","payer"],
            "saturation":   ["saturation","debit","lent","connexion"],
            "couverture":   ["couverture","zone","antenne","signal"],
            "autre":        ["divers","autre","general"],
            "technique":    ["technique","probleme","bug","erreur","panne"],
            "produit":      ["produit","qualite","equipement","modem","box"],
            "attente":      ["attente","delai","long","patienter","lent"],
        }
        topics = []
        for r in results:
            theme = r["_id"]
            if not theme:
                continue
            theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
            kw = keywords_map.get(theme.lower(), [theme_fr])
            topics.append({
                "name": theme_fr,
                "keywords": kw[:4],
                "count": r["count"],
                "neg_pct": round(r["neg_pct"]*100,1),
                "pos_pct": round(r["pos_pct"]*100,1),
            })
        return topics
    except Exception as e:
        print(f"Erreur get_lda_topics: {e}")
        return []


def get_wordcloud_data():
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        pipeline = [
            {"$match": {"commentaire_normalized": {"$exists": True, "$ne": ""}}},
            {"$limit": 8000},
            {"$project": {"commentaire_normalized": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return []
        words = []
        for r in results:
            text = r.get("commentaire_normalized","")
            if not text:
                continue
            text = text.lower()
            text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
            text = re.sub(r'\d+','',text)
            for word in text.split():
                word = word.strip()
                if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
                    words.append(word)
        if not words:
            return []
        wc = Counter(words)
        top = wc.most_common(60)
        return [{"word": w, "count": c} for w,c in top]
    except Exception as e:
        print(f"Erreur get_wordcloud_data: {e}")
        return []


def get_monthly_frequency():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        pipeline = [
            {"$match": {"theme_pred": {"$exists": True,"$ne": None}, "mois": {"$exists": True}}},
            {"$group": {"_id": {"mois":"$mois","theme":"$theme_pred"}, "count": {"$sum": 1}}},
            {"$sort": {"_id.mois": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        data = []
        for r in results:
            theme = r["_id"]["theme"]
            theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
            data.append({"mois": r["_id"]["mois"], "theme": theme_fr, "count": r["count"]})
        df = pd.DataFrame(data)
        top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
        return df[df["theme"].isin(top6)]
    except Exception as e:
        print(f"Erreur get_monthly_frequency: {e}")
        return pd.DataFrame()


def get_reason_distribution():
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        pipeline = [
            {"$match": {"reason_pred": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$reason_pred",
                "count": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "confiance": {"$avg": "$sentiment_confiance"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        total = sum(r["count"] for r in results)
        data = [{
            "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
            "count": r["count"],
            "pct": round(r["count"]/total*100,1),
            "neg_pct": round(r["neg_pct"]*100,1),
            "confiance": round((r["confiance"] or 0)*100,1),
        } for r in results]
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erreur get_reason_distribution: {e}")
        return pd.DataFrame()


# ============================================================
# EXTRACTION MONGODB — CE MOIS
# ============================================================

def get_anomaly_data_mois():
    """Anomalies pour le mois courant (comparaison jour par jour)."""
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        mois_str = now_local().strftime("%Y-%m")
        pipeline = [
            {"$match": {
                "mois": mois_str,
                "sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]},
                "date_clean": {"$exists": True, "$ne": None},
            }},
            {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_clean"}}}},
            {"$group": {
                "_id": "$day_str",
                "avg_score": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        df = pd.DataFrame([{
            "mois": f"{mois_str}-{r['_id']}",
            "avg_score": round(r["avg_score"],3),
            "total": r["total"],
            "neg_pct": round(r["neg_pct"]*100,1),
            "frustration_pct": round(r["frustration_pct"]*100,1),
        } for r in results])
        if len(df) > 2:
            mean_s = df["avg_score"].mean()
            std_s  = df["avg_score"].std()
            if std_s > 0:
                df["is_anomaly"] = (df["avg_score"] < (mean_s - 0.8*std_s)) | (df["neg_pct"] > 65)
                df["anomaly_severity"] = np.where(
                    df["avg_score"] < (mean_s - 2*std_s), "critical",
                    np.where(df["is_anomaly"], "high", "normal")
                )
            else:
                df["is_anomaly"] = False
                df["anomaly_severity"] = "normal"
        return df
    except Exception as e:
        print(f"Erreur get_anomaly_data_mois: {e}")
        return pd.DataFrame()


def get_lda_topics_mois():
    """Thèmes filtrés sur le mois courant."""
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        mois_str = now_local().strftime("%Y-%m")
        pipeline = [
            {"$match": {"mois": mois_str, "theme_pred": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$theme_pred",
                "count": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 8},
        ]
        results = list(_col.aggregate(pipeline))
        keywords_map = {
            "reseau":       ["reseau","connexion","4g","internet","signal"],
            "service":      ["service","client","accueil","conseiller","support"],
            "prix":         ["prix","tarif","forfait","cher","abonnement"],
            "hors_sujet":   ["general","information","actualite","annonce"],
            "installation": ["installation","technicien","rdv","delai","pose"],
            "facture":      ["facture","paiement","montant","recu","payer"],
            "saturation":   ["saturation","debit","lent","connexion"],
            "couverture":   ["couverture","zone","antenne","signal"],
            "autre":        ["divers","autre","general"],
            "technique":    ["technique","probleme","bug","erreur","panne"],
            "produit":      ["produit","qualite","equipement","modem","box"],
            "attente":      ["attente","delai","long","patienter","lent"],
        }
        topics = []
        for r in results:
            theme = r["_id"]
            if not theme:
                continue
            theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
            kw = keywords_map.get(theme.lower(), [theme_fr])
            topics.append({
                "name": theme_fr,
                "keywords": kw[:4],
                "count": r["count"],
                "neg_pct": round(r["neg_pct"]*100,1),
                "pos_pct": round(r["pos_pct"]*100,1),
            })
        return topics
    except Exception as e:
        print(f"Erreur get_lda_topics_mois: {e}")
        return []


def get_wordcloud_data_mois():
    """Wordcloud filtré sur le mois courant."""
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        mois_str = now_local().strftime("%Y-%m")
        pipeline = [
            {"$match": {
                "mois": mois_str,
                "commentaire_normalized": {"$exists": True, "$ne": ""},
            }},
            {"$limit": 3000},
            {"$project": {"commentaire_normalized": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return []
        words = []
        for r in results:
            text = r.get("commentaire_normalized","")
            if not text:
                continue
            text = text.lower()
            text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
            text = re.sub(r'\d+','',text)
            for word in text.split():
                word = word.strip()
                if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
                    words.append(word)
        if not words:
            return []
        wc = Counter(words)
        top = wc.most_common(60)
        return [{"word": w, "count": c} for w,c in top]
    except Exception as e:
        print(f"Erreur get_wordcloud_data_mois: {e}")
        return []


def get_monthly_frequency_mois():
    """Fréquence par thème filtrée sur le mois courant (par jour)."""
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        mois_str = now_local().strftime("%Y-%m")
        pipeline = [
            {"$match": {
                "mois": mois_str,
                "theme_pred": {"$exists": True,"$ne": None},
                "date_clean": {"$exists": True,"$ne": None},
            }},
            {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_clean"}}}},
            {"$group": {"_id": {"jour":"$day_str","theme":"$theme_pred"}, "count": {"$sum": 1}}},
            {"$sort": {"_id.jour": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        data = []
        for r in results:
            theme = r["_id"]["theme"]
            theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
            data.append({"mois": r["_id"]["jour"], "theme": theme_fr, "count": r["count"]})
        df = pd.DataFrame(data)
        top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
        return df[df["theme"].isin(top6)]
    except Exception as e:
        print(f"Erreur get_monthly_frequency_mois: {e}")
        return pd.DataFrame()


def get_reason_distribution_mois():
    """Répartition des raisons pour le mois courant."""
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        mois_str = now_local().strftime("%Y-%m")
        pipeline = [
            {"$match": {"mois": mois_str, "reason_pred": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$reason_pred",
                "count": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "confiance": {"$avg": "$sentiment_confiance"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        total = sum(r["count"] for r in results)
        data = [{
            "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
            "count": r["count"],
            "pct": round(r["count"]/total*100,1),
            "neg_pct": round(r["neg_pct"]*100,1),
            "confiance": round((r["confiance"] or 0)*100,1),
        } for r in results]
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erreur get_reason_distribution_mois: {e}")
        return pd.DataFrame()


# ============================================================
# EXTRACTION MONGODB — AUJOURD'HUI
# ============================================================
def get_anomaly_data_jour():
    """
    Anomalies pour aujourd'hui : utilise les MÊMES SEUILS que l'Analyse Temporelle.
    """
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        local_now = now_local()
        debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
        fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

        pipeline = [
            {"$match": {
                "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
                "sentiment_label": {"$in": ["POSITIF","NEGATIF","NEUTRE"]},
            }},
            {"$group": {
                "_id": "$heure",
                "avg_score": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "frustration_pct": {"$avg": {"$cond": ["$frustration_detectee",1,0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame([{
            "mois": f"{r['_id']:02d}:00",
            "avg_score": round(r["avg_score"],3),
            "total": r["total"],
            "neg_pct": round(r["neg_pct"]*100,1),
            "frustration_pct": round(r["frustration_pct"]*100,1),
        } for r in results])

        if len(df) > 2:
            mean_s = df["avg_score"].mean()
            std_s  = df["avg_score"].std()
            if std_s > 0:
                df["is_anomaly"] = (df["avg_score"] < (mean_s - 0.8*std_s)) | (df["neg_pct"] > 65)
                df["anomaly_severity"] = np.where(
                    df["avg_score"] < (mean_s - 2*std_s), "critical",
                    np.where(df["is_anomaly"], "high", "normal")
                )
            else:
                df["is_anomaly"] = False
                df["anomaly_severity"] = "normal"
        return df
    except Exception as e:
        print(f"Erreur get_anomaly_data_jour: {e}")
        return pd.DataFrame()

def get_lda_topics_jour():
    """Thèmes filtrés sur aujourd'hui."""
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        local_now = now_local()
        debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
        fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

        pipeline = [
            {"$match": {
                "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
                "theme_pred": {"$exists": True, "$ne": None},
            }},
            {"$group": {
                "_id": "$theme_pred",
                "count": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "pos_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","POSITIF"]},1,0]}},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 8},
        ]
        results = list(_col.aggregate(pipeline))
        keywords_map = {
            "reseau":       ["reseau","connexion","4g","internet","signal"],
            "service":      ["service","client","accueil","conseiller","support"],
            "prix":         ["prix","tarif","forfait","cher","abonnement"],
            "hors_sujet":   ["general","information","actualite","annonce"],
            "installation": ["installation","technicien","rdv","delai","pose"],
            "facture":      ["facture","paiement","montant","recu","payer"],
            "saturation":   ["saturation","debit","lent","connexion"],
            "couverture":   ["couverture","zone","antenne","signal"],
            "autre":        ["divers","autre","general"],
            "technique":    ["technique","probleme","bug","erreur","panne"],
            "produit":      ["produit","qualite","equipement","modem","box"],
            "attente":      ["attente","delai","long","patienter","lent"],
        }
        topics = []
        for r in results:
            theme = r["_id"]
            if not theme:
                continue
            theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
            kw = keywords_map.get(theme.lower(), [theme_fr])
            topics.append({
                "name": theme_fr,
                "keywords": kw[:4],
                "count": r["count"],
                "neg_pct": round(r["neg_pct"]*100,1),
                "pos_pct": round(r["pos_pct"]*100,1),
            })
        return topics
    except Exception as e:
        print(f"Erreur get_lda_topics_jour: {e}")
        return []


def get_wordcloud_data_jour():
    """Wordcloud filtré sur aujourd'hui."""
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        local_now = now_local()
        debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
        fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

        pipeline = [
            {"$match": {
                "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
                "commentaire_normalized": {"$exists": True, "$ne": ""},
            }},
            {"$limit": 1000},
            {"$project": {"commentaire_normalized": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return []
        words = []
        for r in results:
            text = r.get("commentaire_normalized","")
            if not text:
                continue
            text = text.lower()
            text = re.sub(r'[^\w\s\u0600-\u06FF]',' ',text)
            text = re.sub(r'\d+','',text)
            for word in text.split():
                word = word.strip()
                if len(word) > 2 and word not in STOPWORDS and not word.isdigit():
                    words.append(word)
        if not words:
            return []
        wc = Counter(words)
        top = wc.most_common(60)
        return [{"word": w, "count": c} for w,c in top]
    except Exception as e:
        print(f"Erreur get_wordcloud_data_jour: {e}")
        return []


def get_monthly_frequency_jour():
    """
    Fréquence par thème pour aujourd'hui, groupée par heure.
    Utilise le champ 'heure' déjà calculé par le consumer.
    """
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        local_now = now_local()
        debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
        fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

        pipeline = [
            {"$match": {
                "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
                "theme_pred": {"$exists": True,"$ne": None},
            }},
            {"$group": {
                "_id": {"heure": "$heure", "theme": "$theme_pred"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id.heure": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        data = []
        for r in results:
            theme = r["_id"]["theme"]
            theme_fr = THEME_MAPPING.get(theme.lower(), theme.replace("_"," ").title())
            heure = r["_id"]["heure"]
            data.append({"mois": f"{heure:02d}:00", "theme": theme_fr, "count": r["count"]})
        df = pd.DataFrame(data)
        top6 = df.groupby("theme")["count"].sum().nlargest(6).index.tolist()
        return df[df["theme"].isin(top6)]
    except Exception as e:
        print(f"Erreur get_monthly_frequency_jour: {e}")
        return pd.DataFrame()


def get_reason_distribution_jour():
    """Répartition des raisons pour aujourd'hui."""
    if not MONGO_AVAILABLE or _col is None:
        return pd.DataFrame()
    try:
        local_now = now_local()
        debut_jour = datetime(local_now.year, local_now.month, local_now.day, 0, 0, 0)
        fin_jour   = datetime(local_now.year, local_now.month, local_now.day, 23, 59, 59)

        pipeline = [
            {"$match": {
                "date_clean": {"$gte": debut_jour, "$lte": fin_jour},
                "reason_pred": {"$exists": True, "$ne": None},
            }},
            {"$group": {
                "_id": "$reason_pred",
                "count": {"$sum": 1},
                "neg_pct": {"$avg": {"$cond": [{"$eq": ["$sentiment_label","NEGATIF"]},1,0]}},
                "confiance": {"$avg": "$sentiment_confiance"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        results = list(_col.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
        total = sum(r["count"] for r in results)
        data = [{
            "reason": REASON_MAPPING.get(r["_id"], r["_id"].replace("_"," ").title()),
            "count": r["count"],
            "pct": round(r["count"]/total*100,1),
            "neg_pct": round(r["neg_pct"]*100,1),
            "confiance": round((r["confiance"] or 0)*100,1),
        } for r in results]
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Erreur get_reason_distribution_jour: {e}")
        return pd.DataFrame()


def _get_data_jour():
    """Données filtrées sur aujourd'hui (jamais mises en cache)."""
    anomaly_df = get_anomaly_data_jour()
    topics     = get_lda_topics_jour()
    word_data  = get_wordcloud_data_jour()
    monthly_df = get_monthly_frequency_jour()
    reason_df  = get_reason_distribution_jour()

    if monthly_df is None or monthly_df.empty:
        monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
    if reason_df is None or reason_df.empty:
        reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
    if anomaly_df is None or anomaly_df.empty:
        anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

    return {
        "anomaly_df": anomaly_df,
        "topics":     topics if topics else [],
        "word_data":  word_data if word_data else [],
        "monthly_df": monthly_df,
        "reason_df":  reason_df,
    }


# ============================================================
# GRAPHIQUES
# ============================================================

def make_reasons_donut(df, theme="light"):
    c = _colors(theme)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 280))
        return fig

    palette = (BLUE_PALETTE_DARK if theme=="dark" else BLUE_PALETTE_LIGHT)[:len(df)]

    fig = go.Figure(go.Pie(
        labels=df["reason"],
        values=df["count"],
        hole=0.55,
        marker=dict(colors=palette, line=dict(color=c["bg"], width=2)),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=9, color=c["text"]),
        hovertemplate="<b>%{label}</b><br>Volume: %{value:,}<br>Part: %{percent}<br>Insatisfaction: %{customdata}%<extra></extra>",
        customdata=df["neg_pct"],
        pull=[0.03 if i == 0 else 0 for i in range(len(df))],
        sort=False,
        direction="clockwise",
    ))

    layout = _base_layout(c, 280, margin=dict(l=10, r=80, t=30, b=30))
    layout.update(
        showlegend=True,
        legend=dict(
            orientation="v", x=1.02, y=0.5, xanchor="left", yanchor="middle",
            font=dict(size=9, color=c["text"]), bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        annotations=[dict(
            text=f"<b>{df['count'].sum():,}</b><br><span style='font-size:8px'>messages</span>",
            x=0.5, y=0.5,
            font=dict(size=12, color=c["primary"]),
            showarrow=False,
        )],
    )
    fig.update_layout(**layout)
    return fig


def make_reasons_bar(df, theme="light"):
    c = _colors(theme)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 280))
        return fig

    df_sorted = df.sort_values("neg_pct", ascending=True).copy()

    bar_colors = []
    for p in df_sorted["neg_pct"]:
        if p >= 60:
            bar_colors.append(c["danger"])
        elif p >= 40:
            bar_colors.append(c["warning"])
        else:
            bar_colors.append(c["success"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted["reason"],
        x=df_sorted["neg_pct"],
        orientation="h",
        width=0.65,
        marker=dict(color=bar_colors, line=dict(width=0), cornerradius=4),
        text=[f"{p:.0f}%" for p in df_sorted["neg_pct"]],
        textposition="outside",
        textfont=dict(size=9, weight="bold"),
        hovertemplate="<b>%{y}</b><br>Insatisfaction: %{x:.1f}%<br>Volume: %{customdata:,}<extra></extra>",
        customdata=df_sorted["count"],
    ))

    fig.add_vline(x=60, line_dash="dash", line_color=c["danger"], line_width=1.5, opacity=0.7)
    fig.add_vline(x=40, line_dash="dot",  line_color=c["warning"], line_width=1, opacity=0.6)

    layout = _base_layout(c, 280, margin=dict(l=100, r=50, t=20, b=20))
    layout.update(
        xaxis=dict(ticksuffix="%", range=[0, 110], showgrid=True, gridcolor=c["grid"], zeroline=False),
        yaxis=dict(showgrid=False),
        showlegend=False,
        bargap=0.3,
    )
    fig.update_layout(**layout)
    return fig


def make_anomaly_chart(df, theme="light", x_title="Période"):
    c = _colors(theme)
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee pour cette période", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 240))
        return fig

    fig = go.Figure()
    r,g,b_ = int(c["primary"][1:3],16), int(c["primary"][3:5],16), int(c["primary"][5:7],16)
    fig.add_trace(go.Scatter(
        x=df["mois"], y=df["avg_score"],
        mode="lines+markers",
        name="Score satisfaction",
        line=dict(color=c["primary"], width=2.5),
        fill="tozeroy",
        fillcolor=f"rgba({r},{g},{b_},0.08)",
        marker=dict(size=8, color=c["primary"], line=dict(color=c["bg"], width=2)),
        hovertemplate=f"{x_title}: %{{x}}<br>Score: %{{y:.3f}}<br>Insatisfaits: %{{customdata:.1f}}%<extra></extra>",
        customdata=df["neg_pct"],
    ))

    if "is_anomaly" in df.columns:
        anom = df[df["is_anomaly"]]
        if not anom.empty:
            fig.add_trace(go.Scatter(
                x=anom["mois"], y=anom["avg_score"],
                mode="markers",
                marker=dict(symbol="x", size=12, color=c["danger"],
                            line=dict(width=2, color="white")),
                name="Période dégradée",
                hovertemplate="ALERTE — %{x}<br>Score: %{y:.3f}<extra></extra>",
            ))

    mean_s = df["avg_score"].mean()
    fig.add_hline(y=mean_s, line_dash="dash", line_color=c["neutral"], opacity=0.5)

    layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
    layout.update(
        xaxis=dict(title=x_title, tickangle=-30, tickfont=dict(size=8), nticks=6),
        yaxis=dict(title="Score", range=[-1.1, 1.1], zeroline=False),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=8)),
        hovermode="x unified",
    )
    fig.update_layout(**layout)
    return fig


def make_monthly_frequency_chart(df, theme="light", x_title="Période"):
    c = _colors(theme)
    multi_palette = [c["primary"], c["danger"], c["warning"], c["success"], "#6c5ce7", "#00cec9"]
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 240))
        return fig

    fig = go.Figure()
    for i, th in enumerate(df["theme"].unique()):
        sub = df[df["theme"] == th].sort_values("mois")
        fig.add_trace(go.Scatter(
            x=sub["mois"], y=sub["count"],
            mode="lines+markers",
            name=th,
            line=dict(width=1.5, color=multi_palette[i % len(multi_palette)]),
            marker=dict(size=5),
            hovertemplate=f"<b>%{{fullData.name}}</b><br>{x_title}: %{{x}}<br>Messages: %{{y:,}}<extra></extra>",
        ))

    layout = _base_layout(c, 240, margin=dict(l=45, r=20, t=15, b=45))
    layout.update(
        xaxis=dict(title=x_title, tickangle=-30, tickfont=dict(size=8), nticks=6),
        yaxis=dict(title="Messages", tickformat=","),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=7)),
        hovermode="x unified",
    )
    fig.update_layout(**layout)
    return fig


# ============================================================
# WORDCLOUD
# ============================================================

def make_wordcloud_iframe(word_data, theme="light"):
    if not word_data:
        return html.Div([
            html.I(className="fas fa-cloud",
                   style={"fontSize":"28px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
            html.P("Aucune donnee textuelle",
                   style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
        ], style={"textAlign":"center","padding":"30px","display":"flex",
                  "flexDirection":"column","alignItems":"center"})

    bg_color = "#1a2540" if theme == "dark" else "#ffffff"
    max_c = max(w["count"] for w in word_data)
    min_c = min(w["count"] for w in word_data)
    rng   = max_c - min_c if max_c != min_c else 1

    words_js = json.dumps([
        [w["word"], round(10 + (w["count"] - min_c) / rng * 58)]
        for w in word_data
    ])

    colors_light = ["#003087","#1a4fa0","#4a80d4","#e8384f","#f59e0b","#00a854","#6c8dcc"]
    colors_dark  = ["#4a80d4","#6a9ae0","#8ab8e4","#2ecc71","#f06070","#f39c12","#a78bfa"]
    colors_js = json.dumps(colors_dark if theme == "dark" else colors_light)

    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:{bg_color};width:100%;height:100%;overflow:hidden;
        display:flex;align-items:center;justify-content:center}}
  #wc{{width:100%;height:100%;display:block}}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js"></script>
</head><body>
<canvas id="wc"></canvas>
<script>
  var words={words_js};
  var colors={colors_js};
  var ci=0;
  function init(){{
    var c=document.getElementById('wc');
    var W=window.innerWidth||600,H=window.innerHeight||320;
    c.width=W;c.height=H;
    WordCloud(c,{{
      list:words,
      gridSize:Math.round(6*W/700),
      weightFactor:function(s){{return s*(W/600)}},
      fontFamily:"'Segoe UI','DM Sans',sans-serif",
      color:function(){{return colors[(ci++)%colors.length]}},
      rotateRatio:0.3,rotationSteps:3,
      backgroundColor:'{bg_color}',
      shuffle:true,drawOutOfBound:false,shrinkToFit:true,minSize:8,
    }});
  }}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
  window.addEventListener('resize',function(){{setTimeout(init,100)}});
</script>
</body></html>"""

    return html.Iframe(
        srcDoc=html_content,
        style={
            "width": "100%", "height": "340px", "border": "none",
            "borderRadius": "8px", "background": bg_color, "display": "block",
        },
    )


# ============================================================
# COMPOSANTS HTML
# ============================================================
def make_anomaly_banner(anomaly_df):
    no_anomaly = (
        anomaly_df.empty
        or "is_anomaly" not in anomaly_df.columns
        or int(anomaly_df["is_anomaly"].sum()) == 0
    )

    if no_anomaly:
        return html.Div(
            id="tt-anomaly-banner",
            children=[
                html.Div([
                    html.I(className="fas fa-check-circle",
                           style={"fontSize":"12px","color":"var(--tt-green, #04723b)",
                                  "marginRight":"8px","flexShrink":"0"}),
                    html.Strong("Aucune anomalie détectée", style={"fontSize":"10px"}),
                ], style={"display":"flex","alignItems":"center","flex":"1"}),
                html.Button(
                    html.I(className="fas fa-times", style={"fontSize":"9px"}),
                    id="close-anomaly-banner-btn", n_clicks=0,
                    style={"background":"transparent","border":"none",
                           "color":"var(--tt-green, #00a854)",
                           "cursor":"pointer","padding":"2px 5px",
                           "borderRadius":"4px","flexShrink":"0"},
                ),
            ],
            style={
                "display":"flex","alignItems":"center","justifyContent":"space-between",
                "padding":"6px 12px","borderRadius":"8px",
                "background":"rgba(0,168,84,0.07)","border":"1px solid rgba(0,168,84,0.18)",
                "marginBottom":"8px",
            },
        )

    n_anom = int(anomaly_df["is_anomaly"].sum())
    n_crit = int((anomaly_df.get("anomaly_severity", pd.Series([])) == "critical").sum()) \
             if "anomaly_severity" in anomaly_df.columns else 0
    
    # Limite à 5 pour correspondre à Analytics (top_n=5)
    top_n = 5
    n_anom_display = min(n_anom, top_n)
    
    # Construction du texte selon le nombre d'anomalies
    if n_anom > top_n:
        txt = f"{n_anom_display} période(s) anormalement dégradée(s) (parmi {n_anom})"
    else:
        txt = f"{n_anom} période(s) anormalement dégradée(s)"
    
    if n_crit:
        txt += f" · {n_crit} critique"

    return html.Div(
        id="tt-anomaly-banner",
        children=[
            html.Div([
                html.I(className="fas fa-exclamation-triangle",
                       style={"fontSize":"12px","color":"var(--tt-red, #e8384f)",
                              "marginRight":"8px","flexShrink":"0"}),
                html.Strong(txt, style={"fontSize":"10px"}),
            ], style={"display":"flex","alignItems":"center","flex":"1"}),
            html.Button(
                html.I(className="fas fa-times", style={"fontSize":"9px"}),
                id="close-anomaly-banner-btn", n_clicks=0,
                style={"background":"transparent","border":"none",
                       "color":"var(--tt-red, #e8384f)",
                       "cursor":"pointer","padding":"2px 5px",
                       "borderRadius":"4px","flexShrink":"0"},
            ),
        ],
        style={
            "display":"flex","alignItems":"center","justifyContent":"space-between",
            "padding":"6px 12px","borderRadius":"8px",
            "background":"rgba(232,56,79,0.07)","border":"1px solid rgba(232,56,79,0.18)",
            "marginBottom":"8px",
        },
    )

def make_topics_list(topics, theme="light"):
    if not topics:
        return html.Div([
            html.I(className="fas fa-tags",
                   style={"fontSize":"24px","color":"var(--tt-border, #ccc)","marginBottom":"8px"}),
            html.P("Aucun thème détecté",
                   style={"color":"var(--tt-muted, #64748b)","fontSize":"11px"}),
        ], style={"textAlign":"center","padding":"30px","display":"flex",
                  "flexDirection":"column","alignItems":"center"})

    c = _colors(theme)
    items = []
    for t in topics:
        if t["neg_pct"] > 60:
            neg_col   = c["danger"]
            badge_txt = "Critique"
        elif t["neg_pct"] > 40:
            neg_col   = c["warning"]
            badge_txt = "Alerte"
        else:
            neg_col   = c["success"]
            badge_txt = "Normal"

        items.append(html.Div([
            html.Div([
                html.Div(style={
                    "width":"5px","height":"5px","borderRadius":"50%",
                    "background":neg_col,"flexShrink":"0",
                }),
                html.Span(t["name"], style={
                    "fontSize":"10px","fontWeight":"600",
                    "color":"var(--tt-text, #1a2a4a)","flex":"1",
                }),
                html.Span(badge_txt, style={
                    "fontSize":"9px","fontWeight":"600",
                    "color": neg_col,
                    "padding":"2px 6px","borderRadius":"8px",
                    "background": f"rgba({','.join(str(int(neg_col.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.1)",
                }),
            ], style={"display":"flex","alignItems":"center","gap":"6px","marginBottom":"4px"}),

            html.Div([
                html.I(className="fas fa-comment-dots",
                       style={"fontSize":"8px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
                html.Span(f"{t['count']:,} messages",
                          style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
                html.Span(" · ", style={"color":"var(--tt-border, #ccc)","margin":"0 3px"}),
                html.Span(f"{t['neg_pct']}% insatisfaits",
                          style={"fontSize":"8px","color":neg_col,"fontWeight":"600"}),
            ], style={"display":"flex","alignItems":"center","flexWrap":"wrap","marginBottom":"4px"}),

            html.Div([
                html.I(className="fas fa-key",
                       style={"fontSize":"7px","color":"var(--tt-muted, #64748b)","marginRight":"3px"}),
                html.Span("Mots-clés : ",
                          style={"fontSize":"8px","color":"var(--tt-muted, #64748b)"}),
                html.Span(", ".join(t["keywords"][:3]),
                          style={"fontSize":"8px","fontWeight":"500",
                                 "color":"var(--tt-text, #1a2a4a)"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"5px","flexWrap":"wrap"}),

            html.Div(
                html.Div(style={
                    "height":"100%","width":f"{min(t['neg_pct'],100)}%",
                    "background":neg_col,"borderRadius":"2px",
                    "transition":"width 0.4s ease",
                }),
                className="tt-topic-bar-track",
            ),
        ], className="tt-topic-item"))

    return html.Div(items, className="tt-topics-list")


# ============================================================
# HELPER : carte générique pour grille 3x2
# ============================================================

def _chart_card(icon, title, tooltip_title, tooltip_body, children):
    return html.Div([
        html.Div([
            html.Div([html.I(className=icon, style={"fontSize":"13px"})],
                     className="card-icon"),
            html.Span(title, className="card-title"),
            html.Div([
                html.Div(
                    html.I(className="fas fa-info-circle", style={"fontSize":"10px"}),
                    className="tooltip-icon",
                ),
                html.Div([
                    html.Div(tooltip_title, className="tooltip-title"),
                    html.Div(tooltip_body,  className="tooltip-body"),
                ], className="card-tooltip"),
            ], className="tooltip-wrapper"),
        ], className="card-header"),
        html.Div(children, className="card-content"),
    ], className="chart-card", style={"padding":"14px 16px","borderRadius":"14px","height":"100%"})


# ============================================================
# CACHE
# ============================================================

_cache = {}

def _get_data():
    global _cache
    if not _cache:
        print("Chargement des données depuis MongoDB...")
        anomaly_df = get_anomaly_data()
        topics     = get_lda_topics()
        word_data  = get_wordcloud_data()
        monthly_df = get_monthly_frequency()
        reason_df  = get_reason_distribution()

        if monthly_df is None or monthly_df.empty:
            monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
        if reason_df is None or reason_df.empty:
            reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
        if anomaly_df is None or anomaly_df.empty:
            anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

        _cache["anomaly_df"] = anomaly_df
        _cache["topics"]     = topics if topics else []
        _cache["word_data"]  = word_data if word_data else []
        _cache["monthly_df"] = monthly_df
        _cache["reason_df"]  = reason_df

    return _cache


def _get_data_mois():
    """Données filtrées sur le mois courant (pas mises en cache longtemps)."""
    anomaly_df = get_anomaly_data_mois()
    topics     = get_lda_topics_mois()
    word_data  = get_wordcloud_data_mois()
    monthly_df = get_monthly_frequency_mois()
    reason_df  = get_reason_distribution_mois()

    if monthly_df is None or monthly_df.empty:
        monthly_df = pd.DataFrame(columns=["mois", "theme", "count"])
    if reason_df is None or reason_df.empty:
        reason_df = pd.DataFrame(columns=["reason", "count", "pct", "neg_pct", "confiance"])
    if anomaly_df is None or anomaly_df.empty:
        anomaly_df = pd.DataFrame(columns=["mois", "avg_score", "total", "neg_pct", "frustration_pct"])

    return {
        "anomaly_df": anomaly_df,
        "topics":     topics if topics else [],
        "word_data":  word_data if word_data else [],
        "monthly_df": monthly_df,
        "reason_df":  reason_df,
    }


# ============================================================
# HELPER GRILLE — construit la grille 3×2 avec les données
# ============================================================

def _make_grid(d, theme, periode="global"):
    """
    Construit la grille 3×2 avec les données fournies.
    periode = "global" | "mois" | "jour"
    """
    if periode == "jour":
        x_title_chart = "Heure"
        anom_tooltip  = "Score de satisfaction horaire pour aujourd'hui. Les croix signalent les heures anormales."
        evol_tooltip  = "Evolution du nombre de messages par thème sur les heures de la journée."
    elif periode == "mois":
        x_title_chart = "Jour"
        anom_tooltip  = "Score de satisfaction journalier pour le mois en cours. Les croix signalent les jours anormaux."
        evol_tooltip  = "Evolution du nombre de messages par thème et par jour pour le mois en cours."
    else:
        x_title_chart = "Mois"
        anom_tooltip  = "Score de satisfaction mensuel. Les croix signalent des mois anormaux."
        evol_tooltip  = "Evolution du nombre de messages par thème et par mois."

    return html.Div(className="grid-3x2", children=[

        # LIGNE 1 : ÉVOLUTION | ANOMALIES
        html.Div(className="grid-row", children=[
            _chart_card(
                "fas fa-chart-line", "ÉVOLUTION PAR THÈME",
                "Fréquence par sujet",
                evol_tooltip,
                dcc.Graph(
                    id="tt-monthly-chart",
                    figure=make_monthly_frequency_chart(d["monthly_df"], theme, x_title=x_title_chart),
                    config={"displayModeBar": False},
                    style={"height": "280px"},
                ),
            ),
            _chart_card(
                "fas fa-exclamation-triangle", "DÉTECTION DES ANOMALIES",
                "Anomalies de satisfaction",
                anom_tooltip,
                html.Div([
                    html.Div(
                        id="tt-anomaly-banner-container",
                        children=make_anomaly_banner(d["anomaly_df"]),
                    ),
                    dcc.Graph(
                        id="tt-anomaly-chart",
                        figure=make_anomaly_chart(d["anomaly_df"], theme, x_title=x_title_chart),
                        config={"displayModeBar": False},
                        style={"height": "250px"},
                    ),
                ]),
            ),
        ]),

        # LIGNE 2 : INSATISFACTION | SUJETS
        html.Div(className="grid-row", children=[
            _chart_card(
                "fas fa-chart-bar", "TAUX D'INSATISFACTION",
                "Raisons classées par criticité",
                "Les raisons sont triées du plus critique au moins critique.",
                dcc.Graph(
                    id="tt-reasons-bar",
                    figure=make_reasons_bar(d["reason_df"], theme),
                    config={"displayModeBar": False},
                    style={"height":"280px"},
                ),
            ),
            _chart_card(
                "fas fa-tags", "SUJETS LES PLUS ABORDÉS",
                "Thèmes principaux identifiés",
                "Catégories détectées automatiquement depuis les commentaires.",
                html.Div(
                    id="tt-topics-list",
                    children=make_topics_list(d["topics"], theme),
                    style={"height":"280px","overflowY":"auto"},
                ),
            ),
        ]),

        # LIGNE 3 : RÉPARTITION | VOCABULAIRE
        html.Div(className="grid-row", children=[
            _chart_card(
                "fas fa-chart-pie", "RÉPARTITION DES RAISONS",
                "Distribution des raisons détectées",
                "Répartition par volume des principales raisons détectées automatiquement.",
                dcc.Graph(
                    id="tt-reasons-donut",
                    figure=make_reasons_donut(d["reason_df"], theme),
                    config={"displayModeBar": False},
                    style={"height":"280px"},
                ),
            ),
            _chart_card(
                "fas fa-comment-dots", "VOCABULAIRE CLIENTS",
                "Nuage de mots",
                "Mots les plus utilisés dans les commentaires (français, arabe, darija).",
                html.Div(
                    id="tt-wordcloud",
                    children=make_wordcloud_iframe(d["word_data"], theme),
                    style={"height":"280px"},
                ),
            ),
        ]),
    ])


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

def render_page(theme="light", user_data=None):
    print("Chargement Thèmes & Temporel...")
    d = _get_data()
    today = now_local().strftime("%d/%m/%Y")

    style_active = {
        "padding": "6px 16px", "borderRadius": "20px", "border": "none",
        "background": BLUE, "color": "white", "cursor": "pointer",
        "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px",
    }
    style_inactive = {
        "padding": "6px 16px", "borderRadius": "20px", "border": f"1px solid {BLUE}",
        "background": "transparent", "color": BLUE, "cursor": "pointer",
        "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px",
    }

    content = html.Div(
        className="dashboard-container themes-temporal-page",
        **{"data-theme": theme, "data-page": "themes-temporal"},
        children=[
            # ── Header ──────────────────────────────────────────────────────
            html.Div(
                [
                    # Gauche : label + boutons de période
                    html.Div(
                        [
                            html.I(className="far fa-calendar-alt",
                                   style={"fontSize":"13px","color": NEUTRAL,"marginRight":"6px"}),
                            html.Span("Période d'analyse :",
                                      style={"fontSize":"13px","color": NEUTRAL,
                                             "fontWeight":"500","marginRight":"12px"}),
                            html.Button(
                                [html.I(className="fas fa-globe", style={"fontSize":"11px"}), "Global"],
                                id="tt-btn-global",
                                n_clicks=0,
                                style=style_active,
                            ),
                            html.Button(
                                [html.I(className="fas fa-calendar-day", style={"fontSize":"11px"}), "Ce Mois"],
                                id="tt-btn-mois",
                                n_clicks=0,
                                style=style_inactive,
                            ),
                            html.Button(
                                [html.I(className="fas fa-clock", style={"fontSize":"11px"}), "Aujourd'hui"],
                                id="tt-btn-jour",
                                n_clicks=0,
                                style=style_inactive,
                            ),
                        ],
                        style={"display":"flex","alignItems":"center","gap":"8px"},
                    ),

                    # Droite : badge date + bouton Actualiser
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(className="far fa-calendar-alt",
                                           style={"marginRight":"5px","fontSize":"13px"}),
                                    html.Span(f"Mise à jour : {today}", style={"fontSize":"13px","color":NEUTRAL}),
                                ],
                                style={
                                    "display":"flex","alignItems":"center","background":"white",
                                    "padding":"0 15px","borderRadius":"8px","height":"40px",
                                    "border":"1px solid #e0e0e0","color":BLUE,
                                }
                            ),
                            html.Button(
                                [html.I(className="fas fa-sync-alt",
                                        style={"marginRight":"5px","fontSize":"13px"}),
                                 html.Span("Actualiser", style={"fontSize":"13px"})],
                                id="tt-refresh-btn",
                                n_clicks=0,
                                style={
                                    "background": BLUE, "color":"white","border":"none",
                                    "borderRadius":"8px","padding":"0 20px","cursor":"pointer",
                                    "fontSize":"13px","display":"flex","alignItems":"center",
                                    "height":"40px","gap":"8px",
                                },
                            ),
                        ],
                        style={"display":"flex","gap":"12px","alignItems":"center"}
                    ),
                ],
                style={
                    "display":"flex","justifyContent":"space-between","alignItems":"center",
                    "marginBottom":"20px","background":"white","borderRadius":"12px",
                    "padding":"12px 20px","border":"1px solid #e8edf5",
                    "boxShadow":"0 1px 4px rgba(0,0,0,0.06)",
                }
            ),

            # Store période
            dcc.Store(id="tt-periode-store", data="global"),

            # ── Zone grille : Global (visible par défaut) ──────────────────
            html.Div(
                id="tt-global-content",
                style={"display": "block"},
                children=[_make_grid(d, theme, periode="global")],
            ),

            # ── Zone grille : Ce Mois (cachée par défaut) ──────────────────
            html.Div(
                id="tt-mois-content",
                style={"display": "none"},
                children=[],
            ),

            # ── Zone grille : Aujourd'hui (cachée par défaut) ──────────────
            html.Div(
                id="tt-jour-content",
                style={"display": "none"},
                children=[],
            ),
        ],
    )

    return make_page_layout(
        "themes-temporal",
        "Thèmes & Analyse Temporelle",
        "Quels sujets génèrent le plus d'insatisfaction ? Quels mois ont été les plus difficiles ?",
        content,
        theme,
        user_data,
    )


# ============================================================
# CALLBACKS
# ============================================================

# ── Basculer Global / Ce Mois / Aujourd'hui ──────────────────────────────────
@callback(
    Output("tt-periode-store", "data"),
    Output("tt-btn-global", "style"),
    Output("tt-btn-mois",   "style"),
    Output("tt-btn-jour",   "style"),
    Input("tt-btn-global", "n_clicks"),
    Input("tt-btn-mois",   "n_clicks"),
    Input("tt-btn-jour",   "n_clicks"),
    prevent_initial_call=True,
)
def tt_set_periode(n_global, n_mois, n_jour):
    style_active = {
        "padding": "6px 16px", "borderRadius": "20px", "border": "none",
        "background": BLUE, "color": "white", "cursor": "pointer",
        "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px",
    }
    style_inactive = {
        "padding": "6px 16px", "borderRadius": "20px", "border": f"1px solid {BLUE}",
        "background": "transparent", "color": BLUE, "cursor": "pointer",
        "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px",
    }
    ctx = dash.callback_context
    if not ctx.triggered:
        return "global", style_active, style_inactive, style_inactive
    btn = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn == "tt-btn-mois":
        return "mois", style_inactive, style_active, style_inactive
    if btn == "tt-btn-jour":
        return "jour", style_inactive, style_inactive, style_active
    return "global", style_active, style_inactive, style_inactive


# ── Afficher/cacher les zones Global / Ce Mois / Aujourd'hui ─────────────────
@callback(
    Output("tt-global-content", "style"),
    Output("tt-mois-content",   "style"),
    Output("tt-mois-content",   "children"),
    Output("tt-jour-content",   "style"),
    Output("tt-jour-content",   "children"),
    Input("tt-periode-store", "data"),
    State("theme-store", "data"),
    prevent_initial_call=False,
)
def tt_toggle_content(periode, theme):
    theme = theme or "light"
    local_now = now_local()

    # ── Bandeau Ce Mois ──────────────────────────────────────────────
    if periode == "mois":
        mois_lbl = local_now.strftime("%B %Y")
        d_mois   = _get_data_mois()
        bandeau  = _make_bandeau(
            icon="fas fa-calendar-day",
            label=f"Statistiques de {mois_lbl}",
            sublabel="Données filtrées sur le mois en cours",
        )
        grid_mois = _make_grid(d_mois, theme, periode="mois")
        return (
            {"display": "none"},
            {"display": "block"},
            [bandeau, grid_mois],
            {"display": "none"},
            [],
        )

    # ── Bandeau Aujourd'hui ──────────────────────────────────────────
    if periode == "jour":
        jour_lbl = local_now.strftime("%A %d %B %Y")
        d_jour   = _get_data_jour()
        total_msgs = int(d_jour["anomaly_df"]["total"].sum()) if not d_jour["anomaly_df"].empty else 0
        bandeau  = _make_bandeau(
            icon="fas fa-clock",
            label=f"Aujourd'hui — {jour_lbl}",
            sublabel=f"{total_msgs:,} message(s) reçu(s) aujourd'hui · données en temps réel",
        )
        grid_jour = _make_grid(d_jour, theme, periode="jour")
        return (
            {"display": "none"},
            {"display": "none"},
            [],
            {"display": "block"},
            [bandeau, grid_jour],
        )

    # ── Global ───────────────────────────────────────────────────────
    return (
        {"display": "block"},
        {"display": "none"},
        [],
        {"display": "none"},
        [],
    )


def _make_bandeau(icon, label, sublabel):
    """Bandeau titre commun pour Ce Mois et Aujourd'hui."""
    return html.Div([
        html.Div(style={
            "width":"4px","height":"28px","borderRadius":"4px",
            "background": BLUE, "marginRight":"12px",
        }),
        html.I(className=icon,
               style={"fontSize":"16px","color": BLUE,"marginRight":"10px"}),
        html.Span(label, style={
            "fontSize":"14px","fontWeight":"700","color": BLUE,"letterSpacing":"0.3px",
        }),
        html.Span(sublabel, style={
            "fontSize":"11px","color": NEUTRAL,"marginLeft":"12px",
        }),
    ], style={
        "display":"flex","alignItems":"center","padding":"10px 16px",
        "background":"var(--bg-card)","borderRadius":"12px","marginBottom":"20px",
        "border":f"1px solid {BLUE_LIGHT}","boxShadow":"0 1px 3px rgba(0,0,0,0.05)",
    })


# ── Mise à jour des graphiques selon thème ───────────────────────────────────
@callback(
    Output("tt-anomaly-chart", "figure"),
    Output("tt-monthly-chart", "figure"),
    Output("tt-reasons-donut", "figure"),
    Output("tt-reasons-bar",   "figure"),
    Input("theme-store",       "data"),
    Input("tt-periode-store",  "data"),
    State("auth-store",        "data"),
)
def update_charts(theme, periode, auth_data):
    theme = theme or "light"
    if periode == "mois":
        d = _get_data_mois()
        x_title = "Jour"
    elif periode == "jour":
        d = _get_data_jour()
        x_title = "Heure"
    else:
        d = _get_data()
        x_title = "Mois"
    return (
        make_anomaly_chart(d["anomaly_df"], theme, x_title=x_title),
        make_monthly_frequency_chart(d["monthly_df"], theme, x_title=x_title),
        make_reasons_donut(d["reason_df"], theme),
        make_reasons_bar(d["reason_df"], theme),
    )


@callback(
    Output("tt-wordcloud",   "children"),
    Output("tt-topics-list", "children"),
    Input("theme-store",     "data"),
    Input("tt-periode-store","data"),
    State("auth-store",      "data"),
)
def update_wordcloud_and_topics(theme, periode, auth_data):
    theme = theme or "light"
    if periode == "mois":
        d = _get_data_mois()
    elif periode == "jour":
        d = _get_data_jour()
    else:
        d = _get_data()
    return (
        make_wordcloud_iframe(d["word_data"], theme),
        make_topics_list(d["topics"], theme),
    )


@callback(
    Output("tt-anomaly-banner-container", "children"),
    Input("close-anomaly-banner-btn", "n_clicks"),
    prevent_initial_call=True,
)
def close_anomaly_banner(n_clicks):
    if n_clicks:
        return None
    return dash.no_update


@callback(
    Output("tt-page-content", "children"),
    Input("theme-store", "data"),
    Input("auth-store",  "data"),
)
def themes_page_with_auth(theme, auth_data):
    theme = theme or "light"
    user_data = None
    if auth_data and auth_data.get("is_authenticated"):
        user_data = auth_data.get("user", {})
    return render_page(theme, user_data)


@callback(
    Output("tt-page-content", "children", allow_duplicate=True),
    Input("tt-refresh-btn", "n_clicks"),
    State("theme-store", "data"),
    State("auth-store",  "data"),
    prevent_initial_call=True,
)
def refresh_data(n_clicks, theme, auth_data):
    """Vide le cache et recharge toutes les données."""
    global _cache
    if n_clicks and n_clicks > 0:
        _cache = {}
        theme = theme or "light"
        user_data = None
        if auth_data and auth_data.get("is_authenticated"):
            user_data = auth_data.get("user", {})
        return render_page(theme, user_data)
    return dash.no_update


# ============================================================
# LAYOUT ENTRY POINT
# ============================================================

layout = html.Div(id="tt-page-content")


@callback(
    Output("tt-page-content", "children", allow_duplicate=True),
    Input("_pages_location", "pathname"),
    prevent_initial_call=True,
)
def init_themes_page(pathname):
    if pathname == "/themes-temporal":
        return render_page("light")
    return dash.no_update
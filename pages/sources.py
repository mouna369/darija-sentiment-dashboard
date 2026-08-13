# # """
# # Page Analyse par Source — ALGÉRIE TÉLÉCOM
# # ✅ Design system identique au dashboard
# # ✅ Logos Font Awesome Brands partout (KPI, tableau, légende donut, filtre période)
# # """

# # import dash
# # from dash import html, dcc, callback, Input, Output, State
# # import plotly.graph_objects as go
# # import pandas as pd
# # from datetime import datetime, timedelta
# # import sys, os

# # sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# # from components import make_page_layout
# # from database import MONGO_AVAILABLE, _col

# # dash.register_page(__name__, path='/sources', name='Analyse par Source')

# # # ── PALETTE AT ────────────────────────────────────────────────────────────────
# # BLUE      = "#003087"
# # BLUE_MID  = "#1a4fa0"
# # BLUE_BG   = "#e8f0fb"
# # GREEN     = "#00a854"
# # GREEN_BG  = "#e6f7ef"
# # RED       = "#e8384f"
# # RED_BG    = "#fde8eb"
# # ORANGE    = "#f59e0b"
# # ORANGE_BG = "#fef3cd"
# # NEUTRAL   = "#64748b"

# # # ── MAP source → (couleur, classe FA) ────────────────────────────────────────
# # SOURCE_META = {
# #     "facebook":    {"color": "#1a4fa0", "icon": "fab fa-facebook",      "label": "Facebook"},
# #     "youtube":     {"color": "#FF0000", "icon": "fab fa-youtube",        "label": "YouTube"},
# #     "instagram":   {"color": "#E1306C", "icon": "fab fa-instagram",      "label": "Instagram"},
# #     "x":           {"color": "#000000", "icon": "fab fa-x-twitter",      "label": "X"},
# #     "twitter":     {"color": "#000000", "icon": "fab fa-x-twitter",      "label": "X / Twitter"},
# #     "linkedin":    {"color": "#0077B5", "icon": "fab fa-linkedin",       "label": "LinkedIn"},
# #     "tiktok":      {"color": "#010101", "icon": "fab fa-tiktok",         "label": "TikTok"},
# #     "whatsapp":    {"color": "#25D366", "icon": "fab fa-whatsapp",       "label": "WhatsApp"},
# #     "idoommarket": {"color": "#00a854", "icon": "fas fa-store",          "label": "IdoomMarket"},
# # }

# # def _source_meta(name: str) -> dict:
# #     key = (name or "").lower().strip()
# #     for k, meta in SOURCE_META.items():
# #         if k in key:
# #             return meta
# #     return {"color": BLUE_MID, "icon": "fas fa-globe", "label": name or "Autre"}

# # def _source_color(name: str) -> str:
# #     return _source_meta(name)["color"]

# # def _source_icon(name: str) -> str:
# #     return _source_meta(name)["icon"]


# # # ── Styles boutons (identiques dashboard) ─────────────────────────────────────
# # style_btn_active = {
# #     "padding": "6px 16px", "borderRadius": "20px", "border": "none",
# #     "background": BLUE, "color": "white", "cursor": "pointer",
# #     "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# #     "display": "flex", "alignItems": "center", "gap": "6px",
# # }
# # style_btn_inactive = {
# #     "padding": "6px 16px", "borderRadius": "20px",
# #     "border": f"1px solid {BLUE}", "background": "transparent",
# #     "color": BLUE, "cursor": "pointer", "fontSize": "12px", "fontWeight": "500",
# #     "transition": "all 0.2s ease",
# #     "display": "flex", "alignItems": "center", "gap": "6px",
# # }


# # def now_local():
# #     return datetime.utcnow() + timedelta(hours=1)


# # def _mois_bornes():
# #     now = now_local()
# #     debut = datetime(now.year, now.month, 1)
# #     fin = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
# #     return debut, fin


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 1. DONNÉES
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def _build_match(periode: str) -> dict:
# #     base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
# #     if periode == "mois":
# #         debut, fin = _mois_bornes()
# #         mois_str = now_local().strftime("%Y-%m")
# #         base["$or"] = [
# #             {"mois": mois_str},
# #             {"date_clean": {"$gte": debut, "$lt": fin}},
# #         ]
# #     elif periode == "jour":
# #         base["date_clean"] = {"$gte": now_local() - timedelta(hours=24)}
# #     return base


# # def get_sources_data(periode: str = "global") -> list:
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         match = _build_match(periode)
# #         pipeline = [
# #             {"$match": match},
# #             {"$group": {
# #                 "_id":          {"$ifNull": ["$source", "Autre"]},
# #                 "total":        {"$sum": 1},
# #                 "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# #                 "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
# #                 "avg_score":    {"$avg": "$sentiment_score"},
# #                 "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
# #             }},
# #             {"$sort": {"total": -1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         total_global = sum(r["total"] for r in results) or 1
# #         data = []
# #         for r in results:
# #             total = r["total"] or 1
# #             meta  = _source_meta(r["_id"])
# #             data.append({
# #                 "name":         r["_id"],
# #                 "total":        r["total"],
# #                 "negatifs":     r["negatifs"],
# #                 "positifs":     r["positifs"],
# #                 "neutres":      r["neutres"],
# #                 "avg_score":    round(float(r["avg_score"] or 0), 3),
# #                 "pct_neg":      round(r["negatifs"] / total * 100, 1),
# #                 "pct_pos":      round(r["positifs"] / total * 100, 1),
# #                 "pct_total":    round(r["total"] / total_global * 100, 1),
# #                 "frustrations": r["frustrations"],
# #                 "health":       round(100 - r["negatifs"] / total * 100),
# #                 "color":        meta["color"],
# #                 "icon":         meta["icon"],
# #             })
# #         return data
# #     except Exception as e:
# #         print(f"Erreur get_sources_data: {e}")
# #         return []


# # def get_evolution_par_source(periode: str = "global") -> pd.DataFrame:
# #     if not MONGO_AVAILABLE or _col is None:
# #         return pd.DataFrame()
# #     try:
# #         if periode == "jour":
# #             hier_24h = now_local() - timedelta(hours=24)
# #             pipeline = [
# #                 {"$match": {
# #                     "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# #                     "date_clean": {"$gte": hier_24h},
# #                 }},
# #                 {"$addFields": {"_heure": {"$hour": "$date_clean"}}},
# #                 {"$group": {
# #                     "_id": {"periode": "$_heure", "source": {"$ifNull": ["$source", "Autre"]}},
# #                     "total": {"$sum": 1},
# #                     "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 }},
# #                 {"$sort": {"_id.periode": 1}},
# #             ]
# #         else:
# #             match = _build_match(periode)
# #             pipeline = [
# #                 {"$match": match},
# #                 {"$group": {
# #                     "_id": {"periode": "$mois", "source": {"$ifNull": ["$source", "Autre"]}},
# #                     "total": {"$sum": 1},
# #                     "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 }},
# #                 {"$sort": {"_id.periode": 1}},
# #             ]
# #         results = list(_col.aggregate(pipeline))
# #         if not results:
# #             return pd.DataFrame()
# #         rows = []
# #         for r in results:
# #             total = r["total"] or 1
# #             rows.append({
# #                 "periode": str(r["_id"]["periode"]),
# #                 "source":  r["_id"]["source"],
# #                 "pct_neg": round(r["negatifs"] / total * 100, 1),
# #                 "total":   r["total"],
# #             })
# #         return pd.DataFrame(rows)
# #     except Exception as e:
# #         print(f"Erreur get_evolution_par_source: {e}")
# #         return pd.DataFrame()


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 2. GRAPHIQUES
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def _colors(theme):
# #     if theme == "dark":
# #         return {"bg": "#141c2e", "paper": "#141c2e", "text": "#dce8f5",
# #                 "grid": "#1e2d47", "neutral": "#607b99"}
# #     return {"bg": "#ffffff", "paper": "#ffffff", "text": "#1a2a4a",
# #             "grid": "#e8edf5", "neutral": "#64748b"}


# # def _base_layout(c, height, margin=None):
# #     m = margin or dict(l=10, r=10, t=20, b=10)
# #     return dict(
# #         plot_bgcolor=c["bg"], paper_bgcolor=c["paper"],
# #         font=dict(color=c["text"], family="'DM Sans', sans-serif", size=10),
# #         height=height, margin=m,
# #     )


# # def make_donut_repartition(sources: list, theme="light") -> go.Figure:
# #     c = _colors(theme)
# #     if not sources:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["text"]))
# #         fig.update_layout(**_base_layout(c, 300))
# #         return fig

# #     labels = [s["name"]  for s in sources]
# #     values = [s["total"] for s in sources]
# #     colors = [s["color"] for s in sources]
# #     total  = sum(values)

# #     fig = go.Figure(go.Pie(
# #         labels=labels, values=values, hole=0.62,
# #         marker=dict(colors=colors, line=dict(color=c["bg"], width=3)),
# #         textinfo="percent", textfont=dict(size=10, color="white"),
# #         hovertemplate="<b>%{label}</b><br>%{value:,} messages<br>%{percent}<extra></extra>",
# #         sort=False, pull=[0.04] + [0] * (len(sources) - 1),
# #     ))
# #     fig.add_annotation(text=f"<b>{total:,}</b>", x=0.5, y=0.58,
# #                        font=dict(size=18, color=c["text"]), showarrow=False)
# #     fig.add_annotation(text="messages", x=0.5, y=0.43,
# #                        font=dict(size=10, color=c["neutral"]), showarrow=False)
# #     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=10))
# #     layout.update(showlegend=False)
# #     fig.update_layout(**layout)
# #     return fig


# # def make_volume_bars(sources: list, theme="light") -> go.Figure:
# #     c = _colors(theme)
# #     if not sources:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
# #         fig.update_layout(**_base_layout(c, 300))
# #         return fig
# #     names    = [s["name"]     for s in sources]
# #     negatifs = [s["negatifs"] for s in sources]
# #     neutres  = [s["neutres"]  for s in sources]
# #     positifs = [s["positifs"] for s in sources]
# #     fig = go.Figure()
# #     fig.add_trace(go.Bar(name="Négatifs", x=names, y=negatifs,
# #                          marker=dict(color=RED, cornerradius=4),
# #                          hovertemplate="<b>%{x}</b><br>Négatifs : <b>%{y:,}</b><extra></extra>"))
# #     fig.add_trace(go.Bar(name="Neutres", x=names, y=neutres,
# #                          marker=dict(color="rgba(100,116,139,0.5)", cornerradius=4),
# #                          hovertemplate="<b>%{x}</b><br>Neutres : <b>%{y:,}</b><extra></extra>"))
# #     fig.add_trace(go.Bar(name="Positifs", x=names, y=positifs,
# #                          marker=dict(color=GREEN, cornerradius=4),
# #                          hovertemplate="<b>%{x}</b><br>Positifs : <b>%{y:,}</b><extra></extra>"))
# #     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=60))
# #     layout.update(
# #         barmode="stack",
# #         xaxis=dict(tickfont=dict(size=10, color=c["text"]), showgrid=False),
# #         yaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=",d",
# #                    tickfont=dict(size=9, color=c["text"])),
# #         legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18,
# #                     font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
# #         hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_taux_negatif_bars(sources: list, theme="light") -> go.Figure:
# #     c = _colors(theme)
# #     if not sources:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
# #         fig.update_layout(**_base_layout(c, 300))
# #         return fig
# #     sorted_s = sorted(sources, key=lambda s: s["pct_neg"])
# #     names    = [s["name"]    for s in sorted_s]
# #     pct_neg  = [s["pct_neg"] for s in sorted_s]
# #     bar_colors = [RED if p > 58 else ORANGE if p > 45 else GREEN for p in pct_neg]
# #     fig = go.Figure()
# #     fig.add_trace(go.Bar(
# #         x=pct_neg, y=names, orientation="h",
# #         marker=dict(color=bar_colors, cornerradius=5),
# #         text=[f"{p}%" for p in pct_neg],
# #         textposition="outside",
# #         textfont=dict(size=10, color=c["text"], weight="bold"),
# #         hovertemplate="<b>%{y}</b><br>Taux négatif : <b>%{x}%</b><extra></extra>",
# #         width=0.6,
# #     ))
# #     fig.add_vline(x=50, line_dash="dot", line_color=RED, opacity=0.4,
# #                   annotation_text="Seuil 50%",
# #                   annotation_font=dict(size=9, color=RED),
# #                   annotation_position="top right")
# #     layout = _base_layout(c, 300, margin=dict(l=10, r=60, t=20, b=10))
# #     layout.update(
# #         xaxis=dict(range=[0, max(pct_neg) * 1.15 if pct_neg else 100],
# #                    ticksuffix="%", showgrid=True, gridcolor=c["grid"],
# #                    tickfont=dict(size=9, color=c["text"])),
# #         yaxis=dict(showgrid=False, tickfont=dict(size=11, color=c["text"])),
# #         showlegend=False,
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # def make_evolution_chart(df: pd.DataFrame, theme="light", periode="global") -> go.Figure:
# #     c = _colors(theme)
# #     if df.empty:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée d'évolution", x=0.5, y=0.5, showarrow=False)
# #         fig.update_layout(**_base_layout(c, 300))
# #         return fig
# #     fig = go.Figure()
# #     for src in df["source"].unique():
# #         df_src = df[df["source"] == src].sort_values("periode")
# #         if df_src.empty:
# #             continue
# #         color = _source_color(src)
# #         fig.add_trace(go.Scatter(
# #             x=df_src["periode"], y=df_src["pct_neg"], name=src,
# #             mode="lines+markers",
# #             line=dict(color=color, width=2.5),
# #             marker=dict(size=7, color=color, line=dict(color="white", width=1.5)),
# #             hovertemplate=f"<b>{src}</b><br>%{{x}}<br>Taux négatif : <b>%{{y:.1f}}%</b><extra></extra>",
# #         ))
# #     fig.add_hline(y=50, line_dash="dot", line_color=RED, opacity=0.35,
# #                   annotation_text="Seuil 50%",
# #                   annotation_font=dict(size=9, color=RED))
# #     x_title = "Heure" if periode == "jour" else "Mois"
# #     layout = _base_layout(c, 300, margin=dict(l=40, r=20, t=20, b=40))
# #     layout.update(
# #         xaxis=dict(showgrid=False, tickfont=dict(size=9, color=c["text"]),
# #                    title=x_title, type="category"),
# #         yaxis=dict(showgrid=True, gridcolor=c["grid"], ticksuffix="%",
# #                    tickfont=dict(size=9, color=c["text"]), title="Taux négatif"),
# #         legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22,
# #                     font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
# #         hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 3. COMPOSANTS UI
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def _source_badge(name: str, show_label: bool = True) -> html.Div:
# #     """Badge source avec icône FA + point coloré + nom."""
# #     meta  = _source_meta(name)
# #     color = meta["color"]
# #     icon  = meta["icon"]
# #     children = [
# #         html.Div(
# #             html.I(className=icon, style={"fontSize": "13px", "color": "white"}),
# #             style={
# #                 "width": "26px", "height": "26px", "borderRadius": "8px",
# #                 "background": color, "display": "flex",
# #                 "alignItems": "center", "justifyContent": "center",
# #                 "flexShrink": "0",
# #                 "boxShadow": f"0 2px 6px {color}55",
# #             },
# #         ),
# #     ]
# #     if show_label:
# #         children.append(
# #             html.Span(name, style={"fontWeight": "600", "fontSize": "12px",
# #                                    "color": "var(--text-primary)"})
# #         )
# #     return html.Div(children, style={"display": "flex", "alignItems": "center", "gap": "8px"})


# # def _source_icon_small(name: str) -> html.Span:
# #     """Icône FA inline (pour KPI pill, etc.)."""
# #     meta = _source_meta(name)
# #     return html.Span([
# #         html.I(className=meta["icon"],
# #                style={"fontSize": "11px", "color": meta["color"], "marginRight": "4px"}),
# #     ])


# # def _chart_card_wrap(icon_cls, title, tt_title, tt_body, children):
# #     return html.Div([
# #         html.Div([
# #             html.Div(html.I(className=icon_cls, style={"fontSize": "14px"}),
# #                      className="card-icon"),
# #             html.Span(title, className="card-title"),
# #             html.Div([
# #                 html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
# #                 html.Div([
# #                     html.Div(tt_title, className="tooltip-title"),
# #                     html.Div(tt_body,  className="tooltip-body"),
# #                 ], className="card-tooltip"),
# #             ], className="tooltip-wrapper"),
# #         ], className="card-header"),
# #         html.Div(children, className="card-content"),
# #     ], className="chart-card")

# # def make_kpi_sources(sources: list, periode: str) -> html.Div:
# #     if not sources:
# #         return html.Div("Aucune donnée", style={"color": NEUTRAL, "padding": "20px"})

# #     periode_labels = {"global": "Période complète", "mois": "Ce mois", "jour": "Dernières 24h"}
# #     periode_label  = periode_labels.get(periode, "")

# #     def _kpi(source: dict) -> html.Div:
# #         """Génère une carte KPI pour une source : logo + nom sur même ligne, puis volume"""
# #         return html.Div([
# #             # Ligne 1 : Logo + Nom côte à côte
# #             html.Div([
# #                 # Logo
# #                 html.Div(
# #                     html.I(className=source["icon"], style={"fontSize": "14px", "color": "white"}),
# #                     style={
# #                         "width": "32px", "height": "32px", "borderRadius": "8px",
# #                         "background": source["color"], "display": "flex",
# #                         "alignItems": "center", "justifyContent": "center",
# #                         "boxShadow": f"0 2px 6px {source['color']}55",
# #                     },
# #                 ),
# #                 # Nom
# #                 html.Span(
# #                     source["name"].upper(),
# #                     style={
# #                         "fontSize": "12px", "fontWeight": "700", 
# #                         "letterSpacing": "0.3px", "color": "var(--text-primary)",
# #                     },
# #                 ),
# #             ], style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "12px"}),
            
# #             # Ligne 2 : Nombre de commentaires
# #             html.Div(
# #                 f"{source['total']:,}".replace(",", "\u202f"),
# #                 style={
# #                     "fontSize": "22px", "fontWeight": "800", 
# #                     "color": source["color"], "lineHeight": "1.2",
# #                 },
# #             ),
            
# #             # Ligne 3 : Label commentaires + pourcentage
# #             html.Div([
# #                 html.Span("commentaires", style={"fontSize": "9px", "color": NEUTRAL}),
# #                 html.Span(f" · {source['pct_total']}%", 
# #                           style={"fontSize": "9px", "color": source["color"], "fontWeight": "500"}),
# #             ], style={"marginTop": "4px"}),
            
# #         ], className="kpi-card", style={
# #             "padding": "14px 12px",
# #             "minWidth": "140px",
# #         })

# #     # TOUTES les sources
# #     kpi_cards = [_kpi(src) for src in sources]

# #     # Grille responsive : s'adapte automatiquement au nombre de sources
# #     return html.Div(
# #         html.Div(kpi_cards, className="kpi-grid-6",
# #                  style={
# #                      "display": "grid", 
# #                      "gridTemplateColumns": "repeat(auto-fit, minmax(160px, 1fr))",
# #                      "gap": "12px",
# #                  }),
# #     )
# # def make_donut_legend(sources: list) -> html.Div:
# #     """Légende custom du donut avec icônes FA + couleurs."""
# #     if not sources:
# #         return html.Div()
# #     items = []
# #     for s in sources[:8]:
# #         items.append(html.Div([
# #             html.Div(
# #                 html.I(className=s["icon"],
# #                        style={"fontSize": "11px", "color": "white"}),
# #                 style={
# #                     "width": "22px", "height": "22px", "borderRadius": "6px",
# #                     "background": s["color"], "display": "flex",
# #                     "alignItems": "center", "justifyContent": "center",
# #                     "flexShrink": "0",
# #                 },
# #             ),
# #             html.Span(s["name"],
# #                       style={"fontSize": "11px", "fontWeight": "600",
# #                              "color": "var(--text-primary)", "flex": "1",
# #                              "whiteSpace": "nowrap"}),
# #             html.Span(f"{s['pct_total']}%",
# #                       style={"fontSize": "10px", "fontWeight": "700",
# #                              "color": s["color"]}),
# #         ], style={
# #             "display": "flex", "alignItems": "center", "gap": "7px",
# #             "padding": "5px 8px", "borderRadius": "8px",
# #             "border": "1px solid var(--border-color)",
# #             "background": "var(--stat-bg)",
# #             "transition": "all 0.15s ease",
# #             "cursor": "default",
# #         }))
# #     return html.Div(items, style={
# #         "display": "flex", "flexDirection": "column", "gap": "5px",
# #         "padding": "8px 4px",
# #         "maxHeight": "260px", "overflowY": "auto",
# #     })


# # def make_periode_filter(active: str = "global") -> html.Div:
# #     def _btn(label, icon, val):
# #         is_active = active == val
# #         return html.Button(
# #             [html.I(className=icon, style={"fontSize": "11px"}), label],
# #             id=f"btn-sources-{val}",
# #             n_clicks=0,
# #             style=style_btn_active if is_active else style_btn_inactive,
# #         )
# #     return html.Div([
# #         html.Div([
# #             html.I(className="fas fa-share-nodes",
# #                    style={"fontSize": "11px", "marginRight": "6px", "color": BLUE}),
# #             html.Span("Vue :", style={"fontSize": "12px", "fontWeight": "600",
# #                                       "color": NEUTRAL}),
# #         ], style={"display": "flex", "alignItems": "center"}),
# #         _btn("Global",      "fas fa-globe ",        "global"),
# #         _btn("Ce Mois",     "fas fa-calendar-day ", "mois"),
# #         _btn("Aujourd'hui", "fas fa-clock ",        "jour"),
# #     ], style={
# #         "display": "flex", "alignItems": "center", "gap": "8px",
# #         "padding": "10px 14px", "background": "var(--bg-card)",
# #         "borderRadius": "14px", "marginBottom": "20px",
# #         "border": "1px solid var(--border-color)",
# #         "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
# #         "flexWrap": "wrap",
# #     })


# # def make_table_sources(sources: list) -> html.Div:
# #     if not sources:
# #         return html.Div("Aucune donnée",
# #                         style={"color": NEUTRAL, "padding": "20px", "textAlign": "center"})

# #     th_style = {
# #         "textAlign": "right", "padding": "10px 14px",
# #         "fontSize": "10px", "color": NEUTRAL, "fontWeight": "700",
# #         "textTransform": "uppercase", "letterSpacing": "0.4px",
# #         "borderBottom": "2px solid var(--border-color)",
# #         "background": "var(--stat-bg)", "whiteSpace": "nowrap",
# #     }
# #     th_left = {**th_style, "textAlign": "left"}

# #     header = html.Thead(html.Tr([
# #         html.Th("Source",       style=th_left),
# #         html.Th("Total",        style=th_style),
# #         html.Th("Négatifs",     style=th_style),
# #         html.Th("Positifs",     style=th_style),
# #         html.Th("Neutres",      style=th_style),
# #         html.Th("Taux négatif", style=th_style),
# #         html.Th("Score moy.",   style=th_style),
# #         html.Th("Frustrations", style=th_style),
# #         html.Th("Santé",        style=th_style),
# #     ]))

# #     rows = []
# #     for i, s in enumerate(sources):
# #         health_color = GREEN if s["health"] > 55 else ORANGE if s["health"] > 45 else RED
# #         taux_color   = RED   if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN
# #         taux_bg      = RED_BG if s["pct_neg"] > 58 else ORANGE_BG if s["pct_neg"] > 45 else GREEN_BG
# #         score_color  = GREEN if s["avg_score"] >= -0.2 else ORANGE if s["avg_score"] >= -0.5 else RED

# #         td = {"padding": "10px 14px", "fontSize": "12px",
# #               "borderBottom": "1px solid var(--border-color)"}

# #         # Cellule source : icône FA dans carré coloré + nom
# #         source_cell = html.Td(
# #             html.Div([
# #                 html.Div(
# #                     html.I(className=s["icon"],
# #                            style={"fontSize": "13px", "color": "white"}),
# #                     style={
# #                         "width": "28px", "height": "28px", "borderRadius": "8px",
# #                         "background": s["color"], "display": "flex",
# #                         "alignItems": "center", "justifyContent": "center",
# #                         "flexShrink": "0",
# #                         "boxShadow": f"0 2px 6px {s['color']}55",
# #                     },
# #                 ),
# #                 html.Span(s["name"],
# #                           style={"fontWeight": "600", "fontSize": "12px",
# #                                  "color": "var(--text-primary)"}),
# #             ], style={"display": "flex", "alignItems": "center", "gap": "9px"}),
# #             style=td,
# #         )

# #         rows.append(html.Tr([
# #             source_cell,
# #             html.Td(f"{s['total']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "fontWeight": "600",
# #                            "color": "var(--text-primary)"}),
# #             html.Td(f"{s['negatifs']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "color": RED}),
# #             html.Td(f"{s['positifs']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "color": GREEN}),
# #             html.Td(f"{s['neutres']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "color": NEUTRAL}),
# #             html.Td(html.Span(f"{s['pct_neg']}%", style={
# #                 "fontSize": "11px", "fontWeight": "700",
# #                 "color": taux_color, "background": taux_bg,
# #                 "padding": "3px 8px", "borderRadius": "8px",
# #             }), style={**td, "textAlign": "right"}),
# #             html.Td(f"{s['avg_score']:+.3f}",
# #                     style={**td, "textAlign": "right", "fontWeight": "600",
# #                            "color": score_color}),
# #             html.Td(str(s["frustrations"]),
# #                     style={**td, "textAlign": "right", "color": NEUTRAL}),
# #             html.Td(html.Div([
# #                 html.Div([
# #                     html.Div(style={
# #                         "width": f"{s['health']}%", "height": "100%",
# #                         "borderRadius": "3px", "background": health_color,
# #                         "transition": "width 0.6s ease",
# #                     }),
# #                 ], style={"width": "52px", "height": "6px",
# #                           "background": "var(--border-color)",
# #                           "borderRadius": "3px", "overflow": "hidden"}),
# #                 html.Span(str(s["health"]),
# #                           style={"fontSize": "11px", "color": NEUTRAL,
# #                                  "fontWeight": "600", "minWidth": "22px"}),
# #             ], style={"display": "flex", "alignItems": "center", "gap": "6px",
# #                       "justifyContent": "flex-end"}),
# #                 style={**td}),
# #         ], style={"background": "var(--bg-card)" if i % 2 == 0 else "var(--stat-bg)"}))

# #     return html.Div(html.Table(
# #         [header, html.Tbody(rows)],
# #         style={"width": "100%", "borderCollapse": "collapse"},
# #     ), style={"overflowX": "auto"})


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 4. RENDER
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def render_sources_page(theme="light", user_data=None, periode="global"):
# #     sources = get_sources_data(periode)
# #     df_evol = get_evolution_par_source(periode)
# #     total   = sum(s["total"] for s in sources) if sources else 0
# #     nb_src  = len(sources)

# #     periode_labels = {
# #         "global": "historique complet",
# #         "mois":   now_local().strftime("%B %Y"),
# #         "jour":   "dernières 24h",
# #     }
# #     sub = (f"{nb_src} sources · {total:,} messages · {periode_labels.get(periode, '')}"
# #            .replace(",", "\u202f"))

# #     content = html.Div([

# #         make_periode_filter(periode),
# #         make_kpi_sources(sources, periode),

# #         # ── Ligne 1 : Donut (+ légende custom) + Barres empilées ─────────────
# #         html.Div([
# #             _chart_card_wrap(
# #                 "fas fa-chart-pie",
# #                 "RÉPARTITION DES SOURCES",
# #                 "Répartition par Source",
# #                 "Part de volume de chaque réseau social dans le total des commentaires.",
# #                 html.Div([
# #                     dcc.Graph(
# #                         figure=make_donut_repartition(sources, theme),
# #                         config={"displayModeBar": False},
# #                         style={"width": "100%", "flex": "1"},
# #                     ),
# #                     # Légende custom avec icônes FA
# #                     make_donut_legend(sources),
# #                 ], style={"display": "flex", "flexDirection": "column"}),
# #             ),
# #             _chart_card_wrap(
# #                 "fas fa-chart-bar",
# #                 "VOLUME & SENTIMENT PAR SOURCE",
# #                 "Volume et Sentiment",
# #                 "Décomposition Négatifs / Neutres / Positifs pour chaque source.",
# #                 dcc.Graph(
# #                     figure=make_volume_bars(sources, theme),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%"},
# #                 ),
# #             ),
# #         ], className="row-2cols", style={"marginTop": "20px"}),

# #         # ── Ligne 2 : Taux négatif + Évolution ───────────────────────────────
# #         html.Div([
# #             _chart_card_wrap(
# #                 "fas fa-face-frown",
# #                 "TAUX NÉGATIF PAR SOURCE",
# #                 "Classement par Taux Négatif",
# #                 "Sources classées par % de commentaires négatifs. Seuil critique : 50%.",
# #                 dcc.Graph(
# #                     figure=make_taux_negatif_bars(sources, theme),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%"},
# #                 ),
# #             ),
# #             _chart_card_wrap(
# #                 "fas fa-chart-line",
# #                 "ÉVOLUTION DU TAUX NÉGATIF",
# #                 "Évolution par Source",
# #                 "Courbe d'évolution du taux négatif de chaque source dans le temps.",
# #                 dcc.Graph(
# #                     figure=make_evolution_chart(df_evol, theme, periode),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%"},
# #                 ),
# #             ),
# #         ], className="row-2cols", style={"marginTop": "14px"}),

# #         # ── Tableau détaillé ─────────────────────────────────────────────────
# #         html.Div([
# #             _chart_card_wrap(
# #                 "fas fa-table-list",
# #                 "TABLEAU DÉTAILLÉ PAR SOURCE",
# #                 "Tableau Détaillé",
# #                 "Toutes les métriques par source : volume, sentiments, score moyen, "
# #                 "frustrations et score santé.",
# #                 make_table_sources(sources),
# #             ),
# #         ], style={"marginTop": "14px"}),

# #     ], style={"padding": "0"}, className="dashboard-container")

# #     return make_page_layout(
# #         "sources", "Analyse par Source", sub, content, theme, user_data,
# #     )


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 5. LAYOUT + CALLBACKS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # layout = html.Div(
# #     id="sources-wrapper",
# #     **{"data-theme": "light"},
# #     children=[
# #         dcc.Store(id="periode-sources-store", data="global", storage_type="session"),
# #         dcc.Interval(id="refresh-interval-sources", interval=300_000, n_intervals=0),
# #         html.Div(id="full-sources-layout"),
# #     ],
# # )


# # @callback(
# #     Output("periode-sources-store", "data"),
# #     Output("btn-sources-global",    "style"),
# #     Output("btn-sources-mois",      "style"),
# #     Output("btn-sources-jour",      "style"),
# #     Input("btn-sources-global",     "n_clicks"),
# #     Input("btn-sources-mois",       "n_clicks"),
# #     Input("btn-sources-jour",       "n_clicks"),
# #     State("periode-sources-store",  "data"),
# #     prevent_initial_call=True,
# # )
# # def set_sources_periode(n_g, n_m, n_j, current):
# #     A, I = style_btn_active, style_btn_inactive
# #     ctx  = dash.callback_context
# #     if not ctx.triggered:
# #         s = {"global": [A,I,I], "mois": [I,A,I], "jour": [I,I,A]}.get(current or "global", [A,I,I])
# #         return current or "global", s[0], s[1], s[2]
# #     btn = ctx.triggered[0]["prop_id"].split(".")[0]
# #     if btn == "btn-sources-mois":
# #         return "mois", I, A, I
# #     elif btn == "btn-sources-jour":
# #         return "jour", I, I, A
# #     return "global", A, I, I


# # @callback(
# #     Output("full-sources-layout", "children"),
# #     Output("sources-wrapper",     "data-theme"),
# #     Input("theme-store",           "data"),
# #     Input("auth-store",            "data"),
# #     Input("periode-sources-store", "data"),
# #     Input("refresh-interval-sources", "n_intervals"),
# # )
# # def update_sources_page(theme, auth_data, periode, _):
# #     theme   = theme   or "light"
# #     periode = periode or "global"
# #     user_data = None
# #     if auth_data and auth_data.get("is_authenticated"):
# #         user_data = auth_data.get("user", {})
# #     return render_sources_page(theme, user_data, periode), theme

# # # """
# # # Page Analyse par Source — ALGÉRIE TÉLÉCOM
# # # ✅ Design system identique au dashboard
# # # ✅ Logos Font Awesome Brands partout (KPI, tableau, légende donut, filtre période)
# # # """

# # # import dash
# # # from dash import html, dcc, callback, Input, Output, State
# # # import plotly.graph_objects as go
# # # import pandas as pd
# # # from datetime import datetime, timedelta
# # # import sys, os

# # # sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# # # from components import make_page_layout
# # # from database import MONGO_AVAILABLE, _col

# # # dash.register_page(__name__, path='/sources', name='Analyse par Source')

# # # # ── PALETTE AT ────────────────────────────────────────────────────────────────
# # # BLUE      = "#003087"
# # # BLUE_MID  = "#1a4fa0"
# # # BLUE_BG   = "#e8f0fb"
# # # GREEN     = "#00a854"
# # # GREEN_BG  = "#e6f7ef"
# # # RED       = "#e8384f"
# # # RED_BG    = "#fde8eb"
# # # ORANGE    = "#f59e0b"
# # # ORANGE_BG = "#fef3cd"
# # # NEUTRAL   = "#64748b"

# # # # ── MAP source → (couleur, classe FA) ────────────────────────────────────────
# # # SOURCE_META = {
# # #     "facebook":    {"color": "#1a4fa0", "icon": "fab fa-facebook",      "label": "Facebook"},
# # #     "youtube":     {"color": "#FF0000", "icon": "fab fa-youtube",        "label": "YouTube"},
# # #     "instagram":   {"color": "#E1306C", "icon": "fab fa-instagram",      "label": "Instagram"},
# # #     "x":           {"color": "#000000", "icon": "fab fa-x-twitter",      "label": "X"},
# # #     "twitter":     {"color": "#000000", "icon": "fab fa-x-twitter",      "label": "X / Twitter"},
# # #     "linkedin":    {"color": "#0077B5", "icon": "fab fa-linkedin",       "label": "LinkedIn"},
# # #     "tiktok":      {"color": "#010101", "icon": "fab fa-tiktok",         "label": "TikTok"},
# # #     "whatsapp":    {"color": "#25D366", "icon": "fab fa-whatsapp",       "label": "WhatsApp"},
# # #     "idoommarket": {"color": "#00a854", "icon": "fas fa-store",          "label": "IdoomMarket"},
# # # }

# # # def _source_meta(name: str) -> dict:
# # #     key = (name or "").lower().strip()
# # #     for k, meta in SOURCE_META.items():
# # #         if k in key:
# # #             return meta
# # #     return {"color": BLUE_MID, "icon": "fas fa-globe", "label": name or "Autre"}

# # # def _source_color(name: str) -> str:
# # #     return _source_meta(name)["color"]

# # # def _source_icon(name: str) -> str:
# # #     return _source_meta(name)["icon"]


# # # # ── Styles boutons (identiques dashboard) ─────────────────────────────────────
# # # style_btn_active = {
# # #     "padding": "6px 16px", "borderRadius": "20px", "border": "none",
# # #     "background": BLUE, "color": "white", "cursor": "pointer",
# # #     "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# # #     "display": "flex", "alignItems": "center", "gap": "6px",
# # # }
# # # style_btn_inactive = {
# # #     "padding": "6px 16px", "borderRadius": "20px",
# # #     "border": f"1px solid {BLUE}", "background": "transparent",
# # #     "color": BLUE, "cursor": "pointer", "fontSize": "12px", "fontWeight": "500",
# # #     "transition": "all 0.2s ease",
# # #     "display": "flex", "alignItems": "center", "gap": "6px",
# # # }


# # # def now_local():
# # #     return datetime.utcnow() + timedelta(hours=1)


# # # def _mois_bornes():
# # #     now = now_local()
# # #     debut = datetime(now.year, now.month, 1)
# # #     fin = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
# # #     return debut, fin


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # 1. DONNÉES
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # def _build_match(periode: str) -> dict:
# # #     base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
# # #     if periode == "mois":
# # #         debut, fin = _mois_bornes()
# # #         mois_str = now_local().strftime("%Y-%m")
# # #         base["$or"] = [
# # #             {"mois": mois_str},
# # #             {"date_clean": {"$gte": debut, "$lt": fin}},
# # #         ]
# # #     elif periode == "jour":
# # #         base["date_clean"] = {"$gte": now_local() - timedelta(hours=24)}
# # #     return base


# # # def get_sources_data(periode: str = "global") -> list:
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return []
# # #     try:
# # #         match = _build_match(periode)
# # #         pipeline = [
# # #             {"$match": match},
# # #             {"$group": {
# # #                 "_id":          {"$ifNull": ["$source", "Autre"]},
# # #                 "total":        {"$sum": 1},
# # #                 "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# # #                 "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# # #                 "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
# # #                 "avg_score":    {"$avg": "$sentiment_score"},
# # #                 "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
# # #             }},
# # #             {"$sort": {"total": -1}},
# # #         ]
# # #         results = list(_col.aggregate(pipeline))
# # #         total_global = sum(r["total"] for r in results) or 1
# # #         data = []
# # #         for r in results:
# # #             total = r["total"] or 1
# # #             meta  = _source_meta(r["_id"])
# # #             data.append({
# # #                 "name":         r["_id"],
# # #                 "total":        r["total"],
# # #                 "negatifs":     r["negatifs"],
# # #                 "positifs":     r["positifs"],
# # #                 "neutres":      r["neutres"],
# # #                 "avg_score":    round(float(r["avg_score"] or 0), 3),
# # #                 "pct_neg":      round(r["negatifs"] / total * 100, 1),
# # #                 "pct_pos":      round(r["positifs"] / total * 100, 1),
# # #                 "pct_total":    round(r["total"] / total_global * 100, 1),
# # #                 "frustrations": r["frustrations"],
# # #                 "health":       round(100 - r["negatifs"] / total * 100),
# # #                 "color":        meta["color"],
# # #                 "icon":         meta["icon"],
# # #             })
# # #         return data
# # #     except Exception as e:
# # #         print(f"Erreur get_sources_data: {e}")
# # #         return []


# # # def get_evolution_par_source(periode: str = "global") -> pd.DataFrame:
# # #     if not MONGO_AVAILABLE or _col is None:
# # #         return pd.DataFrame()
# # #     try:
# # #         if periode == "jour":
# # #             hier_24h = now_local() - timedelta(hours=24)
# # #             pipeline = [
# # #                 {"$match": {
# # #                     "sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]},
# # #                     "date_clean": {"$gte": hier_24h},
# # #                 }},
# # #                 {"$addFields": {"_heure": {"$hour": "$date_clean"}}},
# # #                 {"$group": {
# # #                     "_id": {"periode": "$_heure", "source": {"$ifNull": ["$source", "Autre"]}},
# # #                     "total": {"$sum": 1},
# # #                     "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# # #                 }},
# # #                 {"$sort": {"_id.periode": 1}},
# # #             ]
# # #         else:
# # #             match = _build_match(periode)
# # #             pipeline = [
# # #                 {"$match": match},
# # #                 {"$group": {
# # #                     "_id": {"periode": "$mois", "source": {"$ifNull": ["$source", "Autre"]}},
# # #                     "total": {"$sum": 1},
# # #                     "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# # #                 }},
# # #                 {"$sort": {"_id.periode": 1}},
# # #             ]
# # #         results = list(_col.aggregate(pipeline))
# # #         if not results:
# # #             return pd.DataFrame()
# # #         rows = []
# # #         for r in results:
# # #             total = r["total"] or 1
# # #             rows.append({
# # #                 "periode": str(r["_id"]["periode"]),
# # #                 "source":  r["_id"]["source"],
# # #                 "pct_neg": round(r["negatifs"] / total * 100, 1),
# # #                 "total":   r["total"],
# # #             })
# # #         return pd.DataFrame(rows)
# # #     except Exception as e:
# # #         print(f"Erreur get_evolution_par_source: {e}")
# # #         return pd.DataFrame()


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # 2. GRAPHIQUES
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # def _colors(theme):
# # #     if theme == "dark":
# # #         return {"bg": "#141c2e", "paper": "#141c2e", "text": "#dce8f5",
# # #                 "grid": "#1e2d47", "neutral": "#607b99"}
# # #     return {"bg": "#ffffff", "paper": "#ffffff", "text": "#1a2a4a",
# # #             "grid": "#e8edf5", "neutral": "#64748b"}


# # # def _base_layout(c, height, margin=None):
# # #     m = margin or dict(l=10, r=10, t=20, b=10)
# # #     return dict(
# # #         plot_bgcolor=c["bg"], paper_bgcolor=c["paper"],
# # #         font=dict(color=c["text"], family="'DM Sans', sans-serif", size=10),
# # #         height=height, margin=m,
# # #     )


# # # def make_donut_repartition(sources: list, theme="light") -> go.Figure:
# # #     c = _colors(theme)
# # #     if not sources:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
# # #                            font=dict(color=c["text"]))
# # #         fig.update_layout(**_base_layout(c, 300))
# # #         return fig

# # #     labels = [s["name"]  for s in sources]
# # #     values = [s["total"] for s in sources]
# # #     colors = [s["color"] for s in sources]
# # #     total  = sum(values)

# # #     fig = go.Figure(go.Pie(
# # #         labels=labels, values=values, hole=0.62,
# # #         marker=dict(colors=colors, line=dict(color=c["bg"], width=3)),
# # #         textinfo="percent", textfont=dict(size=10, color="white"),
# # #         hovertemplate="<b>%{label}</b><br>%{value:,} messages<br>%{percent}<extra></extra>",
# # #         sort=False, pull=[0.04] + [0] * (len(sources) - 1),
# # #     ))
# # #     fig.add_annotation(text=f"<b>{total:,}</b>", x=0.5, y=0.58,
# # #                        font=dict(size=18, color=c["text"]), showarrow=False)
# # #     fig.add_annotation(text="messages", x=0.5, y=0.43,
# # #                        font=dict(size=10, color=c["neutral"]), showarrow=False)
# # #     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=10))
# # #     layout.update(showlegend=False)
# # #     fig.update_layout(**layout)
# # #     return fig


# # # def make_volume_bars(sources: list, theme="light") -> go.Figure:
# # #     c = _colors(theme)
# # #     if not sources:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
# # #         fig.update_layout(**_base_layout(c, 300))
# # #         return fig
# # #     names    = [s["name"]     for s in sources]
# # #     negatifs = [s["negatifs"] for s in sources]
# # #     neutres  = [s["neutres"]  for s in sources]
# # #     positifs = [s["positifs"] for s in sources]
# # #     fig = go.Figure()
# # #     fig.add_trace(go.Bar(name="Négatifs", x=names, y=negatifs,
# # #                          marker=dict(color=RED, cornerradius=4),
# # #                          hovertemplate="<b>%{x}</b><br>Négatifs : <b>%{y:,}</b><extra></extra>"))
# # #     fig.add_trace(go.Bar(name="Neutres", x=names, y=neutres,
# # #                          marker=dict(color="rgba(100,116,139,0.5)", cornerradius=4),
# # #                          hovertemplate="<b>%{x}</b><br>Neutres : <b>%{y:,}</b><extra></extra>"))
# # #     fig.add_trace(go.Bar(name="Positifs", x=names, y=positifs,
# # #                          marker=dict(color=GREEN, cornerradius=4),
# # #                          hovertemplate="<b>%{x}</b><br>Positifs : <b>%{y:,}</b><extra></extra>"))
# # #     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=60))
# # #     layout.update(
# # #         barmode="stack",
# # #         xaxis=dict(tickfont=dict(size=10, color=c["text"]), showgrid=False),
# # #         yaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=",d",
# # #                    tickfont=dict(size=9, color=c["text"])),
# # #         legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18,
# # #                     font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
# # #         hovermode="x unified",
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # def make_taux_negatif_bars(sources: list, theme="light") -> go.Figure:
# # #     c = _colors(theme)
# # #     if not sources:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
# # #         fig.update_layout(**_base_layout(c, 300))
# # #         return fig
# # #     sorted_s = sorted(sources, key=lambda s: s["pct_neg"])
# # #     names    = [s["name"]    for s in sorted_s]
# # #     pct_neg  = [s["pct_neg"] for s in sorted_s]
# # #     bar_colors = [RED if p > 58 else ORANGE if p > 45 else GREEN for p in pct_neg]
# # #     fig = go.Figure()
# # #     fig.add_trace(go.Bar(
# # #         x=pct_neg, y=names, orientation="h",
# # #         marker=dict(color=bar_colors, cornerradius=5),
# # #         text=[f"{p}%" for p in pct_neg],
# # #         textposition="outside",
# # #         textfont=dict(size=10, color=c["text"], weight="bold"),
# # #         hovertemplate="<b>%{y}</b><br>Taux négatif : <b>%{x}%</b><extra></extra>",
# # #         width=0.6,
# # #     ))
# # #     fig.add_vline(x=50, line_dash="dot", line_color=RED, opacity=0.4,
# # #                   annotation_text="Seuil 50%",
# # #                   annotation_font=dict(size=9, color=RED),
# # #                   annotation_position="top right")
# # #     layout = _base_layout(c, 300, margin=dict(l=10, r=60, t=20, b=10))
# # #     layout.update(
# # #         xaxis=dict(range=[0, max(pct_neg) * 1.15 if pct_neg else 100],
# # #                    ticksuffix="%", showgrid=True, gridcolor=c["grid"],
# # #                    tickfont=dict(size=9, color=c["text"])),
# # #         yaxis=dict(showgrid=False, tickfont=dict(size=11, color=c["text"])),
# # #         showlegend=False,
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # def make_evolution_chart(df: pd.DataFrame, theme="light", periode="global") -> go.Figure:
# # #     c = _colors(theme)
# # #     if df.empty:
# # #         fig = go.Figure()
# # #         fig.add_annotation(text="Aucune donnée d'évolution", x=0.5, y=0.5, showarrow=False)
# # #         fig.update_layout(**_base_layout(c, 300))
# # #         return fig
# # #     fig = go.Figure()
# # #     for src in df["source"].unique():
# # #         df_src = df[df["source"] == src].sort_values("periode")
# # #         if df_src.empty:
# # #             continue
# # #         color = _source_color(src)
# # #         fig.add_trace(go.Scatter(
# # #             x=df_src["periode"], y=df_src["pct_neg"], name=src,
# # #             mode="lines+markers",
# # #             line=dict(color=color, width=2.5),
# # #             marker=dict(size=7, color=color, line=dict(color="white", width=1.5)),
# # #             hovertemplate=f"<b>{src}</b><br>%{{x}}<br>Taux négatif : <b>%{{y:.1f}}%</b><extra></extra>",
# # #         ))
# # #     fig.add_hline(y=50, line_dash="dot", line_color=RED, opacity=0.35,
# # #                   annotation_text="Seuil 50%",
# # #                   annotation_font=dict(size=9, color=RED))
# # #     x_title = "Heure" if periode == "jour" else "Mois"
# # #     layout = _base_layout(c, 300, margin=dict(l=40, r=20, t=20, b=40))
# # #     layout.update(
# # #         xaxis=dict(showgrid=False, tickfont=dict(size=9, color=c["text"]),
# # #                    title=x_title, type="category"),
# # #         yaxis=dict(showgrid=True, gridcolor=c["grid"], ticksuffix="%",
# # #                    tickfont=dict(size=9, color=c["text"]), title="Taux négatif"),
# # #         legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22,
# # #                     font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
# # #         hovermode="x unified",
# # #     )
# # #     fig.update_layout(**layout)
# # #     return fig


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # 3. COMPOSANTS UI
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # def _source_badge(name: str, show_label: bool = True) -> html.Div:
# # #     """Badge source avec icône FA + point coloré + nom."""
# # #     meta  = _source_meta(name)
# # #     color = meta["color"]
# # #     icon  = meta["icon"]
# # #     children = [
# # #         html.Div(
# # #             html.I(className=icon, style={"fontSize": "13px", "color": "white"}),
# # #             style={
# # #                 "width": "26px", "height": "26px", "borderRadius": "8px",
# # #                 "background": color, "display": "flex",
# # #                 "alignItems": "center", "justifyContent": "center",
# # #                 "flexShrink": "0",
# # #                 "boxShadow": f"0 2px 6px {color}55",
# # #             },
# # #         ),
# # #     ]
# # #     if show_label:
# # #         children.append(
# # #             html.Span(name, style={"fontWeight": "600", "fontSize": "12px",
# # #                                    "color": "var(--text-primary)"})
# # #         )
# # #     return html.Div(children, style={"display": "flex", "alignItems": "center", "gap": "8px"})


# # # def _source_icon_small(name: str) -> html.Span:
# # #     """Icône FA inline (pour KPI pill, etc.)."""
# # #     meta = _source_meta(name)
# # #     return html.Span([
# # #         html.I(className=meta["icon"],
# # #                style={"fontSize": "11px", "color": meta["color"], "marginRight": "4px"}),
# # #     ])


# # # def _chart_card_wrap(icon_cls, title, tt_title, tt_body, children):
# # #     return html.Div([
# # #         html.Div([
# # #             html.Div(html.I(className=icon_cls, style={"fontSize": "14px"}),
# # #                      className="card-icon"),
# # #             html.Span(title, className="card-title"),
# # #             html.Div([
# # #                 html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
# # #                 html.Div([
# # #                     html.Div(tt_title, className="tooltip-title"),
# # #                     html.Div(tt_body,  className="tooltip-body"),
# # #                 ], className="card-tooltip"),
# # #             ], className="tooltip-wrapper"),
# # #         ], className="card-header"),
# # #         html.Div(children, className="card-content"),
# # #     ], className="chart-card")


# # # def make_kpi_sources(sources: list, periode: str) -> html.Div:
# # #     if not sources:
# # #         return html.Div("Aucune donnée", style={"color": NEUTRAL, "padding": "20px"})

# # #     total_all  = sum(s["total"] for s in sources)
# # #     top_src    = max(sources, key=lambda s: s["total"])
# # #     worst_src  = max(sources, key=lambda s: s["pct_neg"])
# # #     best_src   = min(sources, key=lambda s: s["pct_neg"])
# # #     nb_sources = len(sources)

# # #     periode_labels = {"global": "Période complète", "mois": "Ce mois", "jour": "Dernières 24h"}
# # #     periode_label  = periode_labels.get(periode, "")

# # #     def _kpi(variant, fa_icon, label, value_node, sub, pill_content=None, pill_class="neutral"):
# # #         return html.Div([
# # #             html.Div([
# # #                 html.Div(html.I(className=fa_icon, style={"fontSize": "20px"}),
# # #                          className="kpi-icon-wrap"),
# # #                 html.Span(label, className="kpi-label"),
# # #             ], className="kpi-top-row"),
# # #             html.Div(value_node, className="kpi-value",
# # #                      style={"fontSize": "20px", "display": "flex",
# # #                             "alignItems": "center", "gap": "10px"}),
# # #             html.Div(className="kpi-underline"),
# # #             html.Div([
# # #                 html.Span(pill_content or [], className=f"kpi-pill {pill_class}",
# # #                           style={"display": "inline-flex", "alignItems": "center", "gap": "4px"}),
# # #                 html.Span(sub, className="kpi-period"),
# # #             ], className="kpi-footer"),
# # #         ], className=f"kpi-card {variant}")

# # #     # KPI 1 — Total
# # #     kpi1 = _kpi(
# # #         "kpi-blue", "fas fa-share-nodes",
# # #         "TOTAL COMMENTAIRES",
# # #         html.Span(f"{total_all:,}".replace(",", "\u202f"),
# # #                   style={"fontSize": "26px", "fontWeight": "800"}),
# # #         f"{nb_sources} sources · {periode_label}",
# # #         pill_content=[
# # #             html.I(className="fas fa-database", style={"fontSize": "9px"}),
# # #             html.Span(f" {nb_sources} sources"),
# # #         ],
# # #     )

# # #     # KPI 2 — Source la plus active (avec icône de la source)
# # #     kpi2 = _kpi(
# # #         "kpi-blue", "fas fa-fire",
# # #         "SOURCE LA PLUS ACTIVE",
# # #         html.Div([
# # #             html.Div(
# # #                 html.I(className=top_src["icon"],
# # #                        style={"fontSize": "14px", "color": "white"}),
# # #                 style={
# # #                     "width": "32px", "height": "32px", "borderRadius": "10px",
# # #                     "background": top_src["color"], "display": "flex",
# # #                     "alignItems": "center", "justifyContent": "center",
# # #                     "flexShrink": "0",
# # #                     "boxShadow": f"0 3px 8px {top_src['color']}66",
# # #                 },
# # #             ),
# # #             html.Span(top_src["name"], style={"fontSize": "18px", "fontWeight": "700"}),
# # #         ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
# # #         f"{top_src['total']:,} msgs · {top_src['pct_total']}% du total",
# # #         pill_content=[
# # #             html.I(className=top_src["icon"],
# # #                    style={"fontSize": "9px", "color": top_src["color"]}),
# # #             html.Span(f" {top_src['pct_total']}% du volume"),
# # #         ],
# # #     )

# # #     # KPI 3 — Source la plus négative
# # #     kpi3 = _kpi(
# # #         "kpi-red", "fas fa-circle-exclamation",
# # #         "SOURCE LA PLUS NÉGATIVE",
# # #         html.Div([
# # #             html.Div(
# # #                 html.I(className=worst_src["icon"],
# # #                        style={"fontSize": "14px", "color": "white"}),
# # #                 style={
# # #                     "width": "32px", "height": "32px", "borderRadius": "10px",
# # #                     "background": worst_src["color"], "display": "flex",
# # #                     "alignItems": "center", "justifyContent": "center",
# # #                     "flexShrink": "0",
# # #                     "boxShadow": f"0 3px 8px {worst_src['color']}66",
# # #                 },
# # #             ),
# # #             html.Span(worst_src["name"], style={"fontSize": "18px", "fontWeight": "700"}),
# # #         ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
# # #         f"{worst_src['pct_neg']}% de commentaires négatifs",
# # #         pill_content=[
# # #             html.I(className=worst_src["icon"],
# # #                    style={"fontSize": "9px", "color": worst_src["color"]}),
# # #             html.Span(f" {worst_src['pct_neg']}% négatifs"),
# # #         ],
# # #         pill_class="down",
# # #     )

# # #     # KPI 4 — Source la plus positive
# # #     kpi4 = _kpi(
# # #         "kpi-green", "fas fa-circle-check",
# # #         "SOURCE LA PLUS POSITIVE",
# # #         html.Div([
# # #             html.Div(
# # #                 html.I(className=best_src["icon"],
# # #                        style={"fontSize": "14px", "color": "white"}),
# # #                 style={
# # #                     "width": "32px", "height": "32px", "borderRadius": "10px",
# # #                     "background": best_src["color"], "display": "flex",
# # #                     "alignItems": "center", "justifyContent": "center",
# # #                     "flexShrink": "0",
# # #                     "boxShadow": f"0 3px 8px {best_src['color']}66",
# # #                 },
# # #             ),
# # #             html.Span(best_src["name"], style={"fontSize": "18px", "fontWeight": "700"}),
# # #         ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
# # #         f"Seulement {best_src['pct_neg']}% de négatifs",
# # #         pill_content=[
# # #             html.I(className=best_src["icon"],
# # #                    style={"fontSize": "9px", "color": best_src["color"]}),
# # #             html.Span(f" {best_src['pct_neg']}% négatifs"),
# # #         ],
# # #         pill_class="up",
# # #     )

# # #     return html.Div(
# # #         html.Div([kpi1, kpi2, kpi3, kpi4],
# # #                  className="kpi-grid-6",
# # #                  style={"gridTemplateColumns": "repeat(4, 1fr)"}),
# # #     )


# # # def make_donut_legend(sources: list) -> html.Div:
# # #     """Légende custom du donut avec icônes FA + couleurs."""
# # #     if not sources:
# # #         return html.Div()
# # #     items = []
# # #     for s in sources[:8]:
# # #         items.append(html.Div([
# # #             html.Div(
# # #                 html.I(className=s["icon"],
# # #                        style={"fontSize": "11px", "color": "white"}),
# # #                 style={
# # #                     "width": "22px", "height": "22px", "borderRadius": "6px",
# # #                     "background": s["color"], "display": "flex",
# # #                     "alignItems": "center", "justifyContent": "center",
# # #                     "flexShrink": "0",
# # #                 },
# # #             ),
# # #             html.Span(s["name"],
# # #                       style={"fontSize": "11px", "fontWeight": "600",
# # #                              "color": "var(--text-primary)", "flex": "1",
# # #                              "whiteSpace": "nowrap"}),
# # #             html.Span(f"{s['pct_total']}%",
# # #                       style={"fontSize": "10px", "fontWeight": "700",
# # #                              "color": s["color"]}),
# # #         ], style={
# # #             "display": "flex", "alignItems": "center", "gap": "7px",
# # #             "padding": "5px 8px", "borderRadius": "8px",
# # #             "border": "1px solid var(--border-color)",
# # #             "background": "var(--stat-bg)",
# # #             "transition": "all 0.15s ease",
# # #             "cursor": "default",
# # #         }))
# # #     return html.Div(items, style={
# # #         "display": "flex", "flexDirection": "column", "gap": "5px",
# # #         "padding": "8px 4px",
# # #         "maxHeight": "260px", "overflowY": "auto",
# # #     })


# # # def make_periode_filter(active: str = "global") -> html.Div:
# # #     def _btn(label, icon, val):
# # #         is_active = active == val
# # #         return html.Button(
# # #             [html.I(className=icon, style={"fontSize": "11px"}), label],
# # #             id=f"btn-sources-{val}",
# # #             n_clicks=0,
# # #             style=style_btn_active if is_active else style_btn_inactive,
# # #         )
# # #     return html.Div([
# # #         html.Div([
# # #             html.I(className="fas fa-share-nodes",
# # #                    style={"fontSize": "11px", "marginRight": "6px", "color": BLUE}),
# # #             html.Span("Vue :", style={"fontSize": "12px", "fontWeight": "600",
# # #                                       "color": NEUTRAL}),
# # #         ], style={"display": "flex", "alignItems": "center"}),
# # #         _btn("Global",      "fas fa-globe ",        "global"),
# # #         _btn("Ce Mois",     "fas fa-calendar-day ", "mois"),
# # #         _btn("Aujourd'hui", "fas fa-clock ",        "jour"),
# # #     ], style={
# # #         "display": "flex", "alignItems": "center", "gap": "8px",
# # #         "padding": "10px 14px", "background": "var(--bg-card)",
# # #         "borderRadius": "14px", "marginBottom": "20px",
# # #         "border": "1px solid var(--border-color)",
# # #         "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
# # #         "flexWrap": "wrap",
# # #     })


# # # def make_table_sources(sources: list) -> html.Div:
# # #     if not sources:
# # #         return html.Div("Aucune donnée",
# # #                         style={"color": NEUTRAL, "padding": "20px", "textAlign": "center"})

# # #     th_style = {
# # #         "textAlign": "right", "padding": "10px 14px",
# # #         "fontSize": "10px", "color": NEUTRAL, "fontWeight": "700",
# # #         "textTransform": "uppercase", "letterSpacing": "0.4px",
# # #         "borderBottom": "2px solid var(--border-color)",
# # #         "background": "var(--stat-bg)", "whiteSpace": "nowrap",
# # #     }
# # #     th_left = {**th_style, "textAlign": "left"}

# # #     header = html.Thead(html.Tr([
# # #         html.Th("Source",       style=th_left),
# # #         html.Th("Total",        style=th_style),
# # #         html.Th("Négatifs",     style=th_style),
# # #         html.Th("Positifs",     style=th_style),
# # #         html.Th("Neutres",      style=th_style),
# # #         html.Th("Taux négatif", style=th_style),
# # #         html.Th("Score moy.",   style=th_style),
# # #         html.Th("Frustrations", style=th_style),
# # #         html.Th("Santé",        style=th_style),
# # #     ]))

# # #     rows = []
# # #     for i, s in enumerate(sources):
# # #         health_color = GREEN if s["health"] > 55 else ORANGE if s["health"] > 45 else RED
# # #         taux_color   = RED   if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN
# # #         taux_bg      = RED_BG if s["pct_neg"] > 58 else ORANGE_BG if s["pct_neg"] > 45 else GREEN_BG
# # #         score_color  = GREEN if s["avg_score"] >= -0.2 else ORANGE if s["avg_score"] >= -0.5 else RED

# # #         td = {"padding": "10px 14px", "fontSize": "12px",
# # #               "borderBottom": "1px solid var(--border-color)"}

# # #         # Cellule source : icône FA dans carré coloré + nom
# # #         source_cell = html.Td(
# # #             html.Div([
# # #                 html.Div(
# # #                     html.I(className=s["icon"],
# # #                            style={"fontSize": "13px", "color": "white"}),
# # #                     style={
# # #                         "width": "28px", "height": "28px", "borderRadius": "8px",
# # #                         "background": s["color"], "display": "flex",
# # #                         "alignItems": "center", "justifyContent": "center",
# # #                         "flexShrink": "0",
# # #                         "boxShadow": f"0 2px 6px {s['color']}55",
# # #                     },
# # #                 ),
# # #                 html.Span(s["name"],
# # #                           style={"fontWeight": "600", "fontSize": "12px",
# # #                                  "color": "var(--text-primary)"}),
# # #             ], style={"display": "flex", "alignItems": "center", "gap": "9px"}),
# # #             style=td,
# # #         )

# # #         rows.append(html.Tr([
# # #             source_cell,
# # #             html.Td(f"{s['total']:,}".replace(",", "\u202f"),
# # #                     style={**td, "textAlign": "right", "fontWeight": "600",
# # #                            "color": "var(--text-primary)"}),
# # #             html.Td(f"{s['negatifs']:,}".replace(",", "\u202f"),
# # #                     style={**td, "textAlign": "right", "color": RED}),
# # #             html.Td(f"{s['positifs']:,}".replace(",", "\u202f"),
# # #                     style={**td, "textAlign": "right", "color": GREEN}),
# # #             html.Td(f"{s['neutres']:,}".replace(",", "\u202f"),
# # #                     style={**td, "textAlign": "right", "color": NEUTRAL}),
# # #             html.Td(html.Span(f"{s['pct_neg']}%", style={
# # #                 "fontSize": "11px", "fontWeight": "700",
# # #                 "color": taux_color, "background": taux_bg,
# # #                 "padding": "3px 8px", "borderRadius": "8px",
# # #             }), style={**td, "textAlign": "right"}),
# # #             html.Td(f"{s['avg_score']:+.3f}",
# # #                     style={**td, "textAlign": "right", "fontWeight": "600",
# # #                            "color": score_color}),
# # #             html.Td(str(s["frustrations"]),
# # #                     style={**td, "textAlign": "right", "color": NEUTRAL}),
# # #             html.Td(html.Div([
# # #                 html.Div([
# # #                     html.Div(style={
# # #                         "width": f"{s['health']}%", "height": "100%",
# # #                         "borderRadius": "3px", "background": health_color,
# # #                         "transition": "width 0.6s ease",
# # #                     }),
# # #                 ], style={"width": "52px", "height": "6px",
# # #                           "background": "var(--border-color)",
# # #                           "borderRadius": "3px", "overflow": "hidden"}),
# # #                 html.Span(str(s["health"]),
# # #                           style={"fontSize": "11px", "color": NEUTRAL,
# # #                                  "fontWeight": "600", "minWidth": "22px"}),
# # #             ], style={"display": "flex", "alignItems": "center", "gap": "6px",
# # #                       "justifyContent": "flex-end"}),
# # #                 style={**td}),
# # #         ], style={"background": "var(--bg-card)" if i % 2 == 0 else "var(--stat-bg)"}))

# # #     return html.Div(html.Table(
# # #         [header, html.Tbody(rows)],
# # #         style={"width": "100%", "borderCollapse": "collapse"},
# # #     ), style={"overflowX": "auto"})


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # 4. RENDER
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # def render_sources_page(theme="light", user_data=None, periode="global"):
# # #     sources = get_sources_data(periode)
# # #     df_evol = get_evolution_par_source(periode)
# # #     total   = sum(s["total"] for s in sources) if sources else 0
# # #     nb_src  = len(sources)

# # #     periode_labels = {
# # #         "global": "historique complet",
# # #         "mois":   now_local().strftime("%B %Y"),
# # #         "jour":   "dernières 24h",
# # #     }
# # #     sub = (f"{nb_src} sources · {total:,} messages · {periode_labels.get(periode, '')}"
# # #            .replace(",", "\u202f"))

# # #     content = html.Div([

# # #         make_periode_filter(periode),
# # #         make_kpi_sources(sources, periode),

# # #         # ── Ligne 1 : Donut (+ légende custom) + Barres empilées ─────────────
# # #         html.Div([
# # #             _chart_card_wrap(
# # #                 "fas fa-chart-pie",
# # #                 "RÉPARTITION DES SOURCES",
# # #                 "Répartition par Source",
# # #                 "Part de volume de chaque réseau social dans le total des commentaires.",
# # #                 html.Div([
# # #                     dcc.Graph(
# # #                         figure=make_donut_repartition(sources, theme),
# # #                         config={"displayModeBar": False},
# # #                         style={"width": "100%", "flex": "1"},
# # #                     ),
# # #                     # Légende custom avec icônes FA
# # #                     make_donut_legend(sources),
# # #                 ], style={"display": "flex", "flexDirection": "column"}),
# # #             ),
# # #             _chart_card_wrap(
# # #                 "fas fa-chart-bar",
# # #                 "VOLUME & SENTIMENT PAR SOURCE",
# # #                 "Volume et Sentiment",
# # #                 "Décomposition Négatifs / Neutres / Positifs pour chaque source.",
# # #                 dcc.Graph(
# # #                     figure=make_volume_bars(sources, theme),
# # #                     config={"displayModeBar": False},
# # #                     style={"width": "100%"},
# # #                 ),
# # #             ),
# # #         ], className="row-2cols", style={"marginTop": "20px"}),

# # #         # ── Ligne 2 : Taux négatif + Évolution ───────────────────────────────
# # #         html.Div([
# # #             _chart_card_wrap(
# # #                 "fas fa-face-frown",
# # #                 "TAUX NÉGATIF PAR SOURCE",
# # #                 "Classement par Taux Négatif",
# # #                 "Sources classées par % de commentaires négatifs. Seuil critique : 50%.",
# # #                 dcc.Graph(
# # #                     figure=make_taux_negatif_bars(sources, theme),
# # #                     config={"displayModeBar": False},
# # #                     style={"width": "100%"},
# # #                 ),
# # #             ),
# # #             _chart_card_wrap(
# # #                 "fas fa-chart-line",
# # #                 "ÉVOLUTION DU TAUX NÉGATIF",
# # #                 "Évolution par Source",
# # #                 "Courbe d'évolution du taux négatif de chaque source dans le temps.",
# # #                 dcc.Graph(
# # #                     figure=make_evolution_chart(df_evol, theme, periode),
# # #                     config={"displayModeBar": False},
# # #                     style={"width": "100%"},
# # #                 ),
# # #             ),
# # #         ], className="row-2cols", style={"marginTop": "14px"}),

# # #         # ── Tableau détaillé ─────────────────────────────────────────────────
# # #         html.Div([
# # #             _chart_card_wrap(
# # #                 "fas fa-table-list",
# # #                 "TABLEAU DÉTAILLÉ PAR SOURCE",
# # #                 "Tableau Détaillé",
# # #                 "Toutes les métriques par source : volume, sentiments, score moyen, "
# # #                 "frustrations et score santé.",
# # #                 make_table_sources(sources),
# # #             ),
# # #         ], style={"marginTop": "14px"}),

# # #     ], style={"padding": "0"}, className="dashboard-container")

# # #     return make_page_layout(
# # #         "sources", "Analyse par Source", sub, content, theme, user_data,
# # #     )


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # 5. LAYOUT + CALLBACKS
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # layout = html.Div(
# # #     id="sources-wrapper",
# # #     **{"data-theme": "light"},
# # #     children=[
# # #         dcc.Store(id="periode-sources-store", data="global", storage_type="session"),
# # #         dcc.Interval(id="refresh-interval-sources", interval=300_000, n_intervals=0),
# # #         html.Div(id="full-sources-layout"),
# # #     ],
# # # )


# # # @callback(
# # #     Output("periode-sources-store", "data"),
# # #     Output("btn-sources-global",    "style"),
# # #     Output("btn-sources-mois",      "style"),
# # #     Output("btn-sources-jour",      "style"),
# # #     Input("btn-sources-global",     "n_clicks"),
# # #     Input("btn-sources-mois",       "n_clicks"),
# # #     Input("btn-sources-jour",       "n_clicks"),
# # #     State("periode-sources-store",  "data"),
# # #     prevent_initial_call=True,
# # # )
# # # def set_sources_periode(n_g, n_m, n_j, current):
# # #     A, I = style_btn_active, style_btn_inactive
# # #     ctx  = dash.callback_context
# # #     if not ctx.triggered:
# # #         s = {"global": [A,I,I], "mois": [I,A,I], "jour": [I,I,A]}.get(current or "global", [A,I,I])
# # #         return current or "global", s[0], s[1], s[2]
# # #     btn = ctx.triggered[0]["prop_id"].split(".")[0]
# # #     if btn == "btn-sources-mois":
# # #         return "mois", I, A, I
# # #     elif btn == "btn-sources-jour":
# # #         return "jour", I, I, A
# # #     return "global", A, I, I


# # # @callback(
# # #     Output("full-sources-layout", "children"),
# # #     Output("sources-wrapper",     "data-theme"),
# # #     Input("theme-store",           "data"),
# # #     Input("auth-store",            "data"),
# # #     Input("periode-sources-store", "data"),
# # #     Input("refresh-interval-sources", "n_intervals"),
# # # )
# # # def update_sources_page(theme, auth_data, periode, _):
# # #     theme   = theme   or "light"
# # #     periode = periode or "global"
# # #     user_data = None
# # #     if auth_data and auth_data.get("is_authenticated"):
# # #         user_data = auth_data.get("user", {})
# # #     return render_sources_page(theme, user_data, periode), theme
# # """
# # Page Analyse par Source — ALGÉRIE TÉLÉCOM
# # ✅ Design system identique au dashboard
# # ✅ Social Media Cards horizontales style photo 2
# # ✅ Logos Font Awesome Brands partout
# # ✅ Ligne 2 (taux négatif + évolution) supprimée
# # """

# # import dash
# # from dash import html, dcc, callback, Input, Output, State
# # import plotly.graph_objects as go
# # import pandas as pd
# # from datetime import datetime, timedelta
# # import sys, os

# # sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# # from components import make_page_layout
# # from database import MONGO_AVAILABLE, _col

# # dash.register_page(__name__, path='/sources', name='Analyse par Source')

# # # ── PALETTE AT ────────────────────────────────────────────────────────────────
# # BLUE      = "#003087"
# # BLUE_MID  = "#1a4fa0"
# # BLUE_BG   = "#e8f0fb"
# # GREEN     = "#00a854"
# # GREEN_BG  = "#e6f7ef"
# # RED       = "#e8384f"
# # RED_BG    = "#fde8eb"
# # ORANGE    = "#f59e0b"
# # ORANGE_BG = "#fef3cd"
# # NEUTRAL   = "#64748b"

# # # ── MAP source → (couleur, gradient, classe FA) ───────────────────────────────
# # SOURCE_META = {
# #     "facebook":    {
# #         "color": "#1877F2",
# #         "gradient": "linear-gradient(135deg, #1877F2 0%, #0d5fd4 100%)",
# #         "icon": "fab fa-facebook",
# #         "label": "Facebook",
# #     },
# #     "youtube":     {
# #         "color": "#FF0000",
# #         "gradient": "linear-gradient(135deg, #FF0000 0%, #cc0000 100%)",
# #         "icon": "fab fa-youtube",
# #         "label": "YouTube",
# #     },
# #     "instagram":   {
# #         "color": "#E1306C",
# #         "gradient": "linear-gradient(135deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)",
# #         "icon": "fab fa-instagram",
# #         "label": "Instagram",
# #     },
# #     "x":           {
# #         "color": "#14171A",
# #         "gradient": "linear-gradient(135deg, #14171A 0%, #333 100%)",
# #         "icon": "fab fa-x-twitter",
# #         "label": "X",
# #     },
# #     "twitter":     {
# #         "color": "#14171A",
# #         "gradient": "linear-gradient(135deg, #14171A 0%, #333 100%)",
# #         "icon": "fab fa-x-twitter",
# #         "label": "X / Twitter",
# #     },
# #     "linkedin":    {
# #         "color": "#0077B5",
# #         "gradient": "linear-gradient(135deg, #0077B5 0%, #005885 100%)",
# #         "icon": "fab fa-linkedin",
# #         "label": "LinkedIn",
# #     },
# #     "tiktok":      {
# #         "color": "#010101",
# #         "gradient": "linear-gradient(135deg, #010101 0%, #69C9D0 50%, #EE1D52 100%)",
# #         "icon": "fab fa-tiktok",
# #         "label": "TikTok",
# #     },
# #     "whatsapp":    {
# #         "color": "#25D366",
# #         "gradient": "linear-gradient(135deg, #25D366 0%, #128C7E 100%)",
# #         "icon": "fab fa-whatsapp",
# #         "label": "WhatsApp",
# #     },
# #     "idoommarket": {
# #         "color": "#00a854",
# #         "gradient": "linear-gradient(135deg, #00a854 0%, #007a3d 100%)",
# #         "icon": "fas fa-store",
# #         "label": "IdoomMarket",
# #     },
# # }


# # def _source_meta(name: str) -> dict:
# #     key = (name or "").lower().strip()
# #     for k, meta in SOURCE_META.items():
# #         if k in key:
# #             return meta
# #     return {
# #         "color": BLUE_MID,
# #         "gradient": f"linear-gradient(135deg, {BLUE_MID} 0%, {BLUE} 100%)",
# #         "icon": "fas fa-globe",
# #         "label": name or "Autre",
# #     }


# # def _source_color(name: str) -> str:
# #     return _source_meta(name)["color"]


# # def _source_icon(name: str) -> str:
# #     return _source_meta(name)["icon"]


# # # ── Styles boutons ─────────────────────────────────────────────────────────────
# # style_btn_active = {
# #     "padding": "6px 16px", "borderRadius": "20px", "border": "none",
# #     "background": BLUE, "color": "white", "cursor": "pointer",
# #     "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
# #     "display": "flex", "alignItems": "center", "gap": "6px",
# # }
# # style_btn_inactive = {
# #     "padding": "6px 16px", "borderRadius": "20px",
# #     "border": f"1px solid {BLUE}", "background": "transparent",
# #     "color": BLUE, "cursor": "pointer", "fontSize": "12px", "fontWeight": "500",
# #     "transition": "all 0.2s ease",
# #     "display": "flex", "alignItems": "center", "gap": "6px",
# # }


# # def now_local():
# #     return datetime.utcnow() + timedelta(hours=1)


# # def _mois_bornes():
# #     now = now_local()
# #     debut = datetime(now.year, now.month, 1)
# #     fin = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
# #     return debut, fin


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 1. DONNÉES
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def _build_match(periode: str) -> dict:
# #     base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
# #     if periode == "mois":
# #         debut, fin = _mois_bornes()
# #         mois_str = now_local().strftime("%Y-%m")
# #         base["$or"] = [
# #             {"mois": mois_str},
# #             {"date_clean": {"$gte": debut, "$lt": fin}},
# #         ]
# #     elif periode == "jour":
# #         base["date_clean"] = {"$gte": now_local() - timedelta(hours=24)}
# #     return base


# # def get_sources_data(periode: str = "global") -> list:
# #     if not MONGO_AVAILABLE or _col is None:
# #         return []
# #     try:
# #         match = _build_match(periode)
# #         pipeline = [
# #             {"$match": match},
# #             {"$group": {
# #                 "_id":          {"$ifNull": ["$source", "Autre"]},
# #                 "total":        {"$sum": 1},
# #                 "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
# #                 "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
# #                 "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
# #                 "avg_score":    {"$avg": "$sentiment_score"},
# #                 "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
# #             }},
# #             {"$sort": {"total": -1}},
# #         ]
# #         results = list(_col.aggregate(pipeline))
# #         total_global = sum(r["total"] for r in results) or 1
# #         data = []
# #         for r in results:
# #             total = r["total"] or 1
# #             meta  = _source_meta(r["_id"])
# #             data.append({
# #                 "name":         r["_id"],
# #                 "total":        r["total"],
# #                 "negatifs":     r["negatifs"],
# #                 "positifs":     r["positifs"],
# #                 "neutres":      r["neutres"],
# #                 "avg_score":    round(float(r["avg_score"] or 0), 3),
# #                 "pct_neg":      round(r["negatifs"] / total * 100, 1),
# #                 "pct_pos":      round(r["positifs"] / total * 100, 1),
# #                 "pct_total":    round(r["total"] / total_global * 100, 1),
# #                 "frustrations": r["frustrations"],
# #                 "health":       round(100 - r["negatifs"] / total * 100),
# #                 "color":        meta["color"],
# #                 "gradient":     meta["gradient"],
# #                 "icon":         meta["icon"],
# #             })
# #         return data
# #     except Exception as e:
# #         print(f"Erreur get_sources_data: {e}")
# #         return []


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 2. GRAPHIQUES
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def _colors(theme):
# #     if theme == "dark":
# #         return {"bg": "#141c2e", "paper": "#141c2e", "text": "#dce8f5",
# #                 "grid": "#1e2d47", "neutral": "#607b99"}
# #     return {"bg": "#ffffff", "paper": "#ffffff", "text": "#1a2a4a",
# #             "grid": "#e8edf5", "neutral": "#64748b"}


# # def _base_layout(c, height, margin=None):
# #     m = margin or dict(l=10, r=10, t=20, b=10)
# #     return dict(
# #         plot_bgcolor=c["bg"], paper_bgcolor=c["paper"],
# #         font=dict(color=c["text"], family="'DM Sans', sans-serif", size=10),
# #         height=height, margin=m,
# #     )


# # def make_donut_repartition(sources: list, theme="light") -> go.Figure:
# #     c = _colors(theme)
# #     if not sources:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
# #                            font=dict(color=c["text"]))
# #         fig.update_layout(**_base_layout(c, 300))
# #         return fig

# #     labels = [s["name"]  for s in sources]
# #     values = [s["total"] for s in sources]
# #     colors = [s["color"] for s in sources]
# #     total  = sum(values)

# #     fig = go.Figure(go.Pie(
# #         labels=labels, values=values, hole=0.62,
# #         marker=dict(colors=colors, line=dict(color=c["bg"], width=3)),
# #         textinfo="percent", textfont=dict(size=10, color="white"),
# #         hovertemplate="<b>%{label}</b><br>%{value:,} messages<br>%{percent}<extra></extra>",
# #         sort=False, pull=[0.04] + [0] * (len(sources) - 1),
# #     ))
# #     fig.add_annotation(text=f"<b>{total:,}</b>", x=0.5, y=0.58,
# #                        font=dict(size=18, color=c["text"]), showarrow=False)
# #     fig.add_annotation(text="messages", x=0.5, y=0.43,
# #                        font=dict(size=10, color=c["neutral"]), showarrow=False)
# #     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=10))
# #     layout.update(showlegend=False)
# #     fig.update_layout(**layout)
# #     return fig


# # def make_volume_bars(sources: list, theme="light") -> go.Figure:
# #     c = _colors(theme)
# #     if not sources:
# #         fig = go.Figure()
# #         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
# #         fig.update_layout(**_base_layout(c, 300))
# #         return fig
# #     names    = [s["name"]     for s in sources]
# #     negatifs = [s["negatifs"] for s in sources]
# #     neutres  = [s["neutres"]  for s in sources]
# #     positifs = [s["positifs"] for s in sources]
# #     fig = go.Figure()
# #     fig.add_trace(go.Bar(name="Négatifs", x=names, y=negatifs,
# #                          marker=dict(color=RED, cornerradius=4),
# #                          hovertemplate="<b>%{x}</b><br>Négatifs : <b>%{y:,}</b><extra></extra>"))
# #     fig.add_trace(go.Bar(name="Neutres", x=names, y=neutres,
# #                          marker=dict(color="rgba(100,116,139,0.5)", cornerradius=4),
# #                          hovertemplate="<b>%{x}</b><br>Neutres : <b>%{y:,}</b><extra></extra>"))
# #     fig.add_trace(go.Bar(name="Positifs", x=names, y=positifs,
# #                          marker=dict(color=GREEN, cornerradius=4),
# #                          hovertemplate="<b>%{x}</b><br>Positifs : <b>%{y:,}</b><extra></extra>"))
# #     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=60))
# #     layout.update(
# #         barmode="stack",
# #         xaxis=dict(tickfont=dict(size=10, color=c["text"]), showgrid=False),
# #         yaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=",d",
# #                    tickfont=dict(size=9, color=c["text"])),
# #         legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18,
# #                     font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
# #         hovermode="x unified",
# #     )
# #     fig.update_layout(**layout)
# #     return fig


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 3. COMPOSANTS UI
# # # ═══════════════════════════════════════════════════════════════════════════════

# # def make_source_cards(sources: list) -> html.Div:
# #     """
# #     Cartes sources HORIZONTALES style photo 2.
# #     Icône grande à gauche (48×48) + nom / volume / stats ↑↓ / barre à droite.
# #     """
# #     if not sources:
# #         return html.Div()

# #     cards = []
# #     for s in sources:
# #         gradient  = s.get("gradient", s["color"])
# #         neg_color = RED if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN

# #         # ── Icône (gauche) ────────────────────────────────────────────────────
# #         icon_box = html.Div(
# #             html.I(className=s["icon"],
# #                    style={"fontSize": "22px", "color": "white"}),
# #             style={
# #                 "width": "48px", "height": "48px", "borderRadius": "12px",
# #                 "background": gradient,
# #                 "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                 "flexShrink": "0",
# #                 "boxShadow": f"0 4px 14px {s['color']}45",
# #             },
# #         )

# #         # ── Infos (droite) ────────────────────────────────────────────────────
# #         info_block = html.Div([

# #             # Nom de la source
# #             html.Div(s["name"], style={
# #                 "fontSize": "11px", "fontWeight": "600",
# #                 "color": "var(--text-secondary)",
# #                 "textTransform": "uppercase", "letterSpacing": "0.4px",
# #                 "marginBottom": "2px",
# #                 "whiteSpace": "nowrap", "overflow": "hidden",
# #                 "textOverflow": "ellipsis",
# #             }),

# #             # Volume total coloré
# #             html.Div(
# #                 f"{s['total']:,}".replace(",", "\u202f"),
# #                 style={
# #                     "fontSize": "20px", "fontWeight": "700",
# #                     "color": s["color"],
# #                     "lineHeight": "1.1",
# #                     "marginBottom": "5px",
# #                 },
# #             ),

# #             # Mini stats ↑pos% ↓neg%
# #             html.Div([
# #                 html.Span([
# #                     html.I(className="fas fa-arrow-up",
# #                            style={"fontSize": "9px", "marginRight": "2px"}),
# #                     f"{s['pct_pos']}%",
# #                 ], style={
# #                     "fontSize": "11px", "fontWeight": "700", "color": GREEN,
# #                     "display": "inline-flex", "alignItems": "center", "gap": "2px",
# #                 }),
# #                 html.Span([
# #                     html.I(className="fas fa-arrow-down",
# #                            style={"fontSize": "9px", "marginRight": "2px"}),
# #                     f"{s['pct_neg']}%",
# #                 ], style={
# #                     "fontSize": "11px", "fontWeight": "700", "color": neg_color,
# #                     "display": "inline-flex", "alignItems": "center", "gap": "2px",
# #                 }),
# #             ], style={"display": "flex", "gap": "10px", "marginBottom": "6px"}),

# #             # Barre progression (taux négatif)
# #             html.Div([
# #                 html.Div(style={
# #                     "width": f"{s['pct_neg']}%", "height": "100%",
# #                     "borderRadius": "2px", "background": neg_color,
# #                     "transition": "width 0.6s ease",
# #                 }),
# #             ], style={
# #                 "width": "100%", "height": "3px",
# #                 "background": "var(--border-color)",
# #                 "borderRadius": "2px", "overflow": "hidden",
# #             }),

# #         ], style={"flex": "1", "minWidth": "0"})

# #         # ── Carte complète horizontale ─────────────────────────────────────────
# #         cards.append(html.Div([
# #             icon_box,
# #             info_block,
# #         ], style={
# #             "display": "flex",
# #             "alignItems": "center",
# #             "gap": "14px",
# #             "background": "var(--bg-card)",
# #             "border": "0.5px solid var(--border-color)",
# #             "borderLeft": f"3px solid {s['color']}",
# #             "borderRadius": "12px",
# #             "padding": "14px 16px",
# #             "cursor": "default",
# #             "transition": "box-shadow 0.15s ease",
# #             "boxShadow": "0 1px 6px rgba(0,48,135,.05)",
# #         }))

# #     return html.Div([
# #         # En-tête section
# #         html.Div([
# #             html.I(className="fas fa-share-nodes",
# #                    style={"fontSize": "12px", "color": BLUE, "marginRight": "7px"}),
# #             html.Span("VUE D'ENSEMBLE DES SOURCES", style={
# #                 "fontSize": "11px", "fontWeight": "700",
# #                 "color": NEUTRAL, "letterSpacing": "0.5px",
# #                 "textTransform": "uppercase",
# #             }),
# #         ], style={"display": "flex", "alignItems": "center", "marginBottom": "12px"}),

# #         # Grille responsive horizontale
# #         html.Div(cards, style={
# #             "display": "grid",
# #             "gridTemplateColumns": "repeat(auto-fill, minmax(210px, 1fr))",
# #             "gap": "12px",
# #         }),
# #     ], style={"marginBottom": "22px"})


# # def _chart_card_wrap(icon_cls, title, tt_title, tt_body, children):
# #     return html.Div([
# #         html.Div([
# #             html.Div(html.I(className=icon_cls, style={"fontSize": "14px"}),
# #                      className="card-icon"),
# #             html.Span(title, className="card-title"),
# #             html.Div([
# #                 html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
# #                 html.Div([
# #                     html.Div(tt_title, className="tooltip-title"),
# #                     html.Div(tt_body,  className="tooltip-body"),
# #                 ], className="card-tooltip"),
# #             ], className="tooltip-wrapper"),
# #         ], className="card-header"),
# #         html.Div(children, className="card-content"),
# #     ], className="chart-card")


# # def make_kpi_sources(sources: list, periode: str) -> html.Div:
# #     if not sources:
# #         return html.Div("Aucune donnée", style={"color": NEUTRAL, "padding": "20px"})

# #     total_all  = sum(s["total"] for s in sources)
# #     top_src    = max(sources, key=lambda s: s["total"])
# #     worst_src  = max(sources, key=lambda s: s["pct_neg"])
# #     best_src   = min(sources, key=lambda s: s["pct_neg"])
# #     nb_sources = len(sources)

# #     periode_labels = {"global": "Période complète", "mois": "Ce mois", "jour": "Dernières 24h"}
# #     periode_label  = periode_labels.get(periode, "")

# #     def _kpi(variant, fa_icon, label, value_node, sub, pill_content=None, pill_class="neutral"):
# #         return html.Div([
# #             html.Div([
# #                 html.Div(html.I(className=fa_icon, style={"fontSize": "20px"}),
# #                          className="kpi-icon-wrap"),
# #                 html.Span(label, className="kpi-label"),
# #             ], className="kpi-top-row"),
# #             html.Div(value_node, className="kpi-value",
# #                      style={"fontSize": "20px", "display": "flex",
# #                             "alignItems": "center", "gap": "10px"}),
# #             html.Div(className="kpi-underline"),
# #             html.Div([
# #                 html.Span(pill_content or [], className=f"kpi-pill {pill_class}",
# #                           style={"display": "inline-flex", "alignItems": "center", "gap": "4px"}),
# #                 html.Span(sub, className="kpi-period"),
# #             ], className="kpi-footer"),
# #         ], className=f"kpi-card {variant}")

# #     # KPI 1 — Total
# #     kpi1 = _kpi(
# #         "kpi-blue", "fas fa-share-nodes",
# #         "TOTAL COMMENTAIRES",
# #         html.Span(f"{total_all:,}".replace(",", "\u202f"),
# #                   style={"fontSize": "26px", "fontWeight": "800"}),
# #         f"{nb_sources} sources · {periode_label}",
# #         pill_content=[
# #             html.I(className="fas fa-database", style={"fontSize": "9px"}),
# #             html.Span(f" {nb_sources} sources"),
# #         ],
# #     )

# #     # KPI 2 — Source la plus active
# #     kpi2 = _kpi(
# #         "kpi-blue", "fas fa-fire",
# #         "SOURCE LA PLUS ACTIVE",
# #         html.Div([
# #             html.Div(
# #                 html.I(className=top_src["icon"],
# #                        style={"fontSize": "14px", "color": "white"}),
# #                 style={
# #                     "width": "32px", "height": "32px", "borderRadius": "10px",
# #                     "background": top_src.get("gradient", top_src["color"]),
# #                     "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                     "flexShrink": "0",
# #                     "boxShadow": f"0 3px 8px {top_src['color']}66",
# #                 },
# #             ),
# #             html.Span(top_src["name"], style={"fontSize": "18px", "fontWeight": "700"}),
# #         ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
# #         f"{top_src['total']:,} msgs · {top_src['pct_total']}% du total",
# #         pill_content=[
# #             html.I(className=top_src["icon"],
# #                    style={"fontSize": "9px", "color": top_src["color"]}),
# #             html.Span(f" {top_src['pct_total']}% du volume"),
# #         ],
# #     )

# #     # KPI 3 — Source la plus négative
# #     kpi3 = _kpi(
# #         "kpi-red", "fas fa-circle-exclamation",
# #         "SOURCE LA PLUS NÉGATIVE",
# #         html.Div([
# #             html.Div(
# #                 html.I(className=worst_src["icon"],
# #                        style={"fontSize": "14px", "color": "white"}),
# #                 style={
# #                     "width": "32px", "height": "32px", "borderRadius": "10px",
# #                     "background": worst_src.get("gradient", worst_src["color"]),
# #                     "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                     "flexShrink": "0",
# #                     "boxShadow": f"0 3px 8px {worst_src['color']}66",
# #                 },
# #             ),
# #             html.Span(worst_src["name"], style={"fontSize": "18px", "fontWeight": "700"}),
# #         ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
# #         f"{worst_src['pct_neg']}% de commentaires négatifs",
# #         pill_content=[
# #             html.I(className=worst_src["icon"],
# #                    style={"fontSize": "9px", "color": worst_src["color"]}),
# #             html.Span(f" {worst_src['pct_neg']}% négatifs"),
# #         ],
# #         pill_class="down",
# #     )

# #     # KPI 4 — Source la plus positive
# #     kpi4 = _kpi(
# #         "kpi-green", "fas fa-circle-check",
# #         "SOURCE LA PLUS POSITIVE",
# #         html.Div([
# #             html.Div(
# #                 html.I(className=best_src["icon"],
# #                        style={"fontSize": "14px", "color": "white"}),
# #                 style={
# #                     "width": "32px", "height": "32px", "borderRadius": "10px",
# #                     "background": best_src.get("gradient", best_src["color"]),
# #                     "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                     "flexShrink": "0",
# #                     "boxShadow": f"0 3px 8px {best_src['color']}66",
# #                 },
# #             ),
# #             html.Span(best_src["name"], style={"fontSize": "18px", "fontWeight": "700"}),
# #         ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
# #         f"Seulement {best_src['pct_neg']}% de négatifs",
# #         pill_content=[
# #             html.I(className=best_src["icon"],
# #                    style={"fontSize": "9px", "color": best_src["color"]}),
# #             html.Span(f" {best_src['pct_neg']}% négatifs"),
# #         ],
# #         pill_class="up",
# #     )

# #     return html.Div(
# #         html.Div([kpi1, kpi2, kpi3, kpi4],
# #                  className="kpi-grid-6",
# #                  style={"gridTemplateColumns": "repeat(4, 1fr)"}),
# #     )


# # def make_donut_legend(sources: list) -> html.Div:
# #     if not sources:
# #         return html.Div()
# #     items = []
# #     for s in sources[:8]:
# #         items.append(html.Div([
# #             html.Div(
# #                 html.I(className=s["icon"],
# #                        style={"fontSize": "11px", "color": "white"}),
# #                 style={
# #                     "width": "22px", "height": "22px", "borderRadius": "6px",
# #                     "background": s.get("gradient", s["color"]),
# #                     "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                     "flexShrink": "0",
# #                 },
# #             ),
# #             html.Span(s["name"],
# #                       style={"fontSize": "11px", "fontWeight": "600",
# #                              "color": "var(--text-primary)", "flex": "1",
# #                              "whiteSpace": "nowrap"}),
# #             html.Span(f"{s['pct_total']}%",
# #                       style={"fontSize": "10px", "fontWeight": "700",
# #                              "color": s["color"]}),
# #         ], style={
# #             "display": "flex", "alignItems": "center", "gap": "7px",
# #             "padding": "5px 8px", "borderRadius": "8px",
# #             "border": "1px solid var(--border-color)",
# #             "background": "var(--stat-bg)",
# #             "transition": "all 0.15s ease",
# #             "cursor": "default",
# #         }))
# #     return html.Div(items, style={
# #         "display": "flex", "flexDirection": "column", "gap": "5px",
# #         "padding": "8px 4px",
# #         "maxHeight": "260px", "overflowY": "auto",
# #     })


# # def make_periode_filter(active: str = "global") -> html.Div:
# #     def _btn(label, icon, val):
# #         is_active = active == val
# #         return html.Button(
# #             [html.I(className=icon, style={"fontSize": "11px"}), label],
# #             id=f"btn-sources-{val}",
# #             n_clicks=0,
# #             style=style_btn_active if is_active else style_btn_inactive,
# #         )
# #     return html.Div([
# #         html.Div([
# #             html.I(className="fas fa-share-nodes",
# #                    style={"fontSize": "11px", "marginRight": "6px", "color": BLUE}),
# #             html.Span("Vue :", style={"fontSize": "12px", "fontWeight": "600",
# #                                       "color": NEUTRAL}),
# #         ], style={"display": "flex", "alignItems": "center"}),
# #         _btn("Global",      "fas fa-globe ",        "global"),
# #         _btn("Ce Mois",     "fas fa-calendar-day ", "mois"),
# #         _btn("Aujourd'hui", "fas fa-clock ",        "jour"),
# #     ], style={
# #         "display": "flex", "alignItems": "center", "gap": "8px",
# #         "padding": "10px 14px", "background": "var(--bg-card)",
# #         "borderRadius": "14px", "marginBottom": "20px",
# #         "border": "1px solid var(--border-color)",
# #         "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
# #         "flexWrap": "wrap",
# #     })


# # def make_table_sources(sources: list) -> html.Div:
# #     if not sources:
# #         return html.Div("Aucune donnée",
# #                         style={"color": NEUTRAL, "padding": "20px", "textAlign": "center"})

# #     th_style = {
# #         "textAlign": "right", "padding": "10px 14px",
# #         "fontSize": "10px", "color": NEUTRAL, "fontWeight": "700",
# #         "textTransform": "uppercase", "letterSpacing": "0.4px",
# #         "borderBottom": "2px solid var(--border-color)",
# #         "background": "var(--stat-bg)", "whiteSpace": "nowrap",
# #     }
# #     th_left = {**th_style, "textAlign": "left"}

# #     header = html.Thead(html.Tr([
# #         html.Th("Source",       style=th_left),
# #         html.Th("Total",        style=th_style),
# #         html.Th("Négatifs",     style=th_style),
# #         html.Th("Positifs",     style=th_style),
# #         html.Th("Neutres",      style=th_style),
# #         html.Th("Taux négatif", style=th_style),
# #         html.Th("Score moy.",   style=th_style),
# #         html.Th("Frustrations", style=th_style),
# #         html.Th("Santé",        style=th_style),
# #     ]))

# #     rows = []
# #     for i, s in enumerate(sources):
# #         health_color = GREEN if s["health"] > 55 else ORANGE if s["health"] > 45 else RED
# #         taux_color   = RED   if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN
# #         taux_bg      = RED_BG if s["pct_neg"] > 58 else ORANGE_BG if s["pct_neg"] > 45 else GREEN_BG
# #         score_color  = GREEN if s["avg_score"] >= -0.2 else ORANGE if s["avg_score"] >= -0.5 else RED

# #         td = {"padding": "10px 14px", "fontSize": "12px",
# #               "borderBottom": "1px solid var(--border-color)"}

# #         source_cell = html.Td(
# #             html.Div([
# #                 html.Div(
# #                     html.I(className=s["icon"],
# #                            style={"fontSize": "13px", "color": "white"}),
# #                     style={
# #                         "width": "28px", "height": "28px", "borderRadius": "8px",
# #                         "background": s.get("gradient", s["color"]),
# #                         "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                         "flexShrink": "0",
# #                         "boxShadow": f"0 2px 6px {s['color']}55",
# #                     },
# #                 ),
# #                 html.Span(s["name"],
# #                           style={"fontWeight": "600", "fontSize": "12px",
# #                                  "color": "var(--text-primary)"}),
# #             ], style={"display": "flex", "alignItems": "center", "gap": "9px"}),
# #             style=td,
# #         )

# #         rows.append(html.Tr([
# #             source_cell,
# #             html.Td(f"{s['total']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "fontWeight": "600",
# #                            "color": "var(--text-primary)"}),
# #             html.Td(f"{s['negatifs']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "color": RED}),
# #             html.Td(f"{s['positifs']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "color": GREEN}),
# #             html.Td(f"{s['neutres']:,}".replace(",", "\u202f"),
# #                     style={**td, "textAlign": "right", "color": NEUTRAL}),
# #             html.Td(html.Span(f"{s['pct_neg']}%", style={
# #                 "fontSize": "11px", "fontWeight": "700",
# #                 "color": taux_color, "background": taux_bg,
# #                 "padding": "3px 8px", "borderRadius": "8px",
# #             }), style={**td, "textAlign": "right"}),
# #             html.Td(f"{s['avg_score']:+.3f}",
# #                     style={**td, "textAlign": "right", "fontWeight": "600",
# #                            "color": score_color}),
# #             html.Td(str(s["frustrations"]),
# #                     style={**td, "textAlign": "right", "color": NEUTRAL}),
# #             html.Td(html.Div([
# #                 html.Div([
# #                     html.Div(style={
# #                         "width": f"{s['health']}%", "height": "100%",
# #                         "borderRadius": "3px", "background": health_color,
# #                         "transition": "width 0.6s ease",
# #                     }),
# #                 ], style={"width": "52px", "height": "6px",
# #                           "background": "var(--border-color)",
# #                           "borderRadius": "3px", "overflow": "hidden"}),
# #                 html.Span(str(s["health"]),
# #                           style={"fontSize": "11px", "color": NEUTRAL,
# #                                  "fontWeight": "600", "minWidth": "22px"}),
# #             ], style={"display": "flex", "alignItems": "center", "gap": "6px",
# #                       "justifyContent": "flex-end"}),
# #                 style={**td}),
# #         ], style={"background": "var(--bg-card)" if i % 2 == 0 else "var(--stat-bg)"}))

# #     return html.Div(html.Table(
# #         [header, html.Tbody(rows)],
# #         style={"width": "100%", "borderCollapse": "collapse"},
# #     ), style={"overflowX": "auto"})


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 4. RENDER
# # # ═══════════════════════════════════════════════════════════════════════════════
# # def render_sources_page(theme="light", user_data=None, periode="global"):
# #     sources = get_sources_data(periode)
# #     total   = sum(s["total"] for s in sources) if sources else 0
# #     nb_src  = len(sources)

# #     periode_labels = {
# #         "global": "historique complet",
# #         "mois":   now_local().strftime("%B %Y"),
# #         "jour":   "dernières 24h",
# #     }
# #     sub = (f"{nb_src} sources · {total:,} messages · {periode_labels.get(periode, '')}"
# #            .replace(",", "\u202f"))

# #     content = html.Div([

# #         # ── Filtre période ────────────────────────────────────────────────────
# #         make_periode_filter(periode),

# #         # ── Social Media Cards horizontales ───────────────────────────────────
# #         make_source_cards(sources),

# #         # ── Ligne 1 : Donut + Barres empilées ────────────────────────────────
# #         html.Div([
# #             _chart_card_wrap(
# #                 "fas fa-chart-pie",
# #                 "RÉPARTITION DES SOURCES",
# #                 "Répartition par Source",
# #                 "Part de volume de chaque réseau social dans le total des commentaires.",
# #                 html.Div([
# #                     dcc.Graph(
# #                         figure=make_donut_repartition(sources, theme),
# #                         config={"displayModeBar": False},
# #                         style={"width": "100%", "flex": "1"},
# #                     ),
# #                     make_donut_legend(sources),
# #                 ], style={"display": "flex", "flexDirection": "column"}),
# #             ),
# #             _chart_card_wrap(
# #                 "fas fa-chart-bar",
# #                 "VOLUME & SENTIMENT PAR SOURCE",
# #                 "Volume et Sentiment",
# #                 "Décomposition Négatifs / Neutres / Positifs pour chaque source.",
# #                 dcc.Graph(
# #                     figure=make_volume_bars(sources, theme),
# #                     config={"displayModeBar": False},
# #                     style={"width": "100%"},
# #                 ),
# #             ),
# #         ], className="row-2cols", style={"marginTop": "20px"}),

# #         # ── Tableau détaillé ──────────────────────────────────────────────────
# #         html.Div([
# #             _chart_card_wrap(
# #                 "fas fa-table-list",
# #                 "TABLEAU DÉTAILLÉ PAR SOURCE",
# #                 "Tableau Détaillé",
# #                 "Toutes les métriques par source : volume, sentiments, score moyen, "
# #                 "frustrations et score santé.",
# #                 make_table_sources(sources),
# #             ),
# #         ], style={"marginTop": "14px"}),

# #     ], style={"padding": "0"}, className="dashboard-container")

# #     return make_page_layout(
# #         "sources", "Analyse par Source", sub, content, theme, user_data,
# #     )
# # # ═══════════════════════════════════════════════════════════════════════════════
# # # 5. LAYOUT + CALLBACKS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # layout = html.Div(
# #     id="sources-wrapper",
# #     **{"data-theme": "light"},
# #     children=[
# #         dcc.Store(id="periode-sources-store", data="global", storage_type="session"),
# #         dcc.Interval(id="refresh-interval-sources", interval=300_000, n_intervals=0),
# #         html.Div(id="full-sources-layout"),
# #     ],
# # )


# # @callback(
# #     Output("periode-sources-store", "data"),
# #     Output("btn-sources-global",    "style"),
# #     Output("btn-sources-mois",      "style"),
# #     Output("btn-sources-jour",      "style"),
# #     Input("btn-sources-global",     "n_clicks"),
# #     Input("btn-sources-mois",       "n_clicks"),
# #     Input("btn-sources-jour",       "n_clicks"),
# #     State("periode-sources-store",  "data"),
# #     prevent_initial_call=True,
# # )
# # def set_sources_periode(n_g, n_m, n_j, current):
# #     A, I = style_btn_active, style_btn_inactive
# #     ctx  = dash.callback_context
# #     if not ctx.triggered:
# #         s = {"global": [A,I,I], "mois": [I,A,I], "jour": [I,I,A]}.get(current or "global", [A,I,I])
# #         return current or "global", s[0], s[1], s[2]
# #     btn = ctx.triggered[0]["prop_id"].split(".")[0]
# #     if btn == "btn-sources-mois":
# #         return "mois", I, A, I
# #     elif btn == "btn-sources-jour":
# #         return "jour", I, I, A
# #     return "global", A, I, I


# # @callback(
# #     Output("full-sources-layout", "children"),
# #     Output("sources-wrapper",     "data-theme"),
# #     Input("theme-store",              "data"),
# #     Input("auth-store",               "data"),
# #     Input("periode-sources-store",    "data"),
# #     Input("refresh-interval-sources", "n_intervals"),
# # )
# # def update_sources_page(theme, auth_data, periode, _):
# #     theme   = theme   or "light"
# #     periode = periode or "global"
# #     user_data = None
# #     if auth_data and auth_data.get("is_authenticated"):
# #         user_data = auth_data.get("user", {})
# #     return render_sources_page(theme, user_data, periode), theme
# """
# Page Analyse par Source — ALGÉRIE TÉLÉCOM
# ✅ Vrais SVG officiels via html.Img + data URI base64 (100% compatible Dash 4.0)
# ✅ Légende donut style "photo 2" : points colorés + nom à DROITE du graphe
# ✅ Design system identique au dashboard
# ✅ KPI cards supprimées
# ✅ Cartes ligne 1 même hauteur (via CSS)
# """

# import dash
# from dash import html, dcc, callback, Input, Output, State
# import plotly.graph_objects as go
# import pandas as pd
# from datetime import datetime, timedelta
# import sys, os
# import base64

# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# from components import make_page_layout
# from database import MONGO_AVAILABLE, _col

# dash.register_page(__name__, path='/sources', name='Analyse par Source')

# # ── PALETTE AT ────────────────────────────────────────────────────────────────
# BLUE      = "#003087"
# BLUE_MID  = "#1a4fa0"
# GREEN     = "#00a854"
# RED       = "#e8384f"
# RED_BG    = "#fde8eb"
# ORANGE    = "#f59e0b"
# ORANGE_BG = "#fef3cd"
# GREEN_BG  = "#e6f7ef"
# NEUTRAL   = "#64748b"

# # ══════════════════════════════════════════════════════════════════════════════
# # SVG OFFICIELS — encodés en base64, compatibles html.Img Dash 4.0
# # ══════════════════════════════════════════════════════════════════════════════

# _SVGS = {
#     "facebook": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="white"/></svg>',
#     "instagram": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" fill="white"/></svg>',
#     "youtube": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" fill="white"/></svg>',
#     "x": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="white"/></svg>',
#     "twitter": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="white"/></svg>',
#     "linkedin": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" fill="white"/></svg>',
#     "tiktok": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" fill="white"/></svg>',
#     "whatsapp": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" fill="white"/></svg>',
#     "idoommarket": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 6h-2V5c0-1.654-1.346-3-3-3h-4C8.346 2 7 3.346 7 5v1H5C3.897 6 3 6.897 3 8v11c0 1.103.897 2 2 2h14c1.103 0 2-.897 2-2V8c0-1.103-.897-2-2-2zm-8-1h2v1h-2V5zm2 9h-2v2H9v-2H7v-2h2v-2h2v2h2v2z" fill="white"/></svg>',
#     "globe": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93V18c0-.55-.45-1-1-1H8v-2c0-.55-.45-1-1-1H5.07C4.4 13.07 4 12.58 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8c-.34 0-.67-.02-1-.07zM17 12h-2v-1h-3V9h3V7.07C17.16 7.56 18 9.67 18 12h-1z" fill="white"/></svg>',
# }


# def _svg_uri(name: str) -> str:
#     key = (name or "").lower().strip()
#     svg_str = None
#     for k in _SVGS:
#         if k in key:
#             svg_str = _SVGS[k]
#             break
#     if svg_str is None:
#         svg_str = _SVGS["globe"]
#     encoded = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
#     return f"data:image/svg+xml;base64,{encoded}"


# def _logo_img(name: str, size: int = 18) -> html.Img:
#     return html.Img(
#         src=_svg_uri(name),
#         style={
#             "width": f"{size}px",
#             "height": f"{size}px",
#             "objectFit": "contain",
#             "display": "block",
#         },
#     )


# # ── MAP source → (couleur, gradient, label) ───────────────────────────────────
# SOURCE_META = {
#     "facebook":    {"color": "#1877F2", "gradient": "linear-gradient(135deg,#1877F2,#0d5fd4)", "label": "Facebook"},
#     "youtube":     {"color": "#FF0000", "gradient": "linear-gradient(135deg,#FF0000,#cc0000)", "label": "YouTube"},
#     "instagram":   {"color": "#E1306C", "gradient": "linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)", "label": "Instagram"},
#     "x":           {"color": "#333333", "gradient": "linear-gradient(135deg,#14171A,#444)", "label": "X"},
#     "twitter":     {"color": "#333333", "gradient": "linear-gradient(135deg,#14171A,#444)", "label": "X / Twitter"},
#     "linkedin":    {"color": "#0077B5", "gradient": "linear-gradient(135deg,#0077B5,#005885)", "label": "LinkedIn"},
#     "tiktok":      {"color": "#fe2c55", "gradient": "linear-gradient(135deg,#010101,#69C9D0,#EE1D52)", "label": "TikTok"},
#     "whatsapp":    {"color": "#25D366", "gradient": "linear-gradient(135deg,#25D366,#128C7E)", "label": "WhatsApp"},
#     "idoommarket": {"color": "#00a854", "gradient": "linear-gradient(135deg,#00a854,#007a3d)", "label": "IdoomMarket"},
# }

# _DEFAULT_META = {"color": BLUE_MID, "gradient": f"linear-gradient(135deg,{BLUE_MID},{BLUE})", "label": "Autre"}


# def _source_meta(name: str) -> dict:
#     key = (name or "").lower().strip()
#     for k, meta in SOURCE_META.items():
#         if k in key:
#             return meta
#     return {**_DEFAULT_META, "label": name or "Autre"}


# def _source_color(name: str) -> str:
#     return _source_meta(name)["color"]


# # ── Styles boutons ─────────────────────────────────────────────────────────────
# style_btn_active = {
#     "padding": "6px 16px", "borderRadius": "20px", "border": "none",
#     "background": BLUE, "color": "white", "cursor": "pointer",
#     "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
#     "display": "flex", "alignItems": "center", "gap": "6px",
# }
# style_btn_inactive = {
#     "padding": "6px 16px", "borderRadius": "20px",
#     "border": f"1px solid {BLUE}", "background": "transparent",
#     "color": BLUE, "cursor": "pointer", "fontSize": "12px", "fontWeight": "500",
#     "transition": "all 0.2s ease",
#     "display": "flex", "alignItems": "center", "gap": "6px",
# }


# def now_local():
#     return datetime.utcnow() + timedelta(hours=1)


# def _mois_bornes():
#     now = now_local()
#     debut = datetime(now.year, now.month, 1)
#     fin = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
#     return debut, fin


# # ═══════════════════════════════════════════════════════════════════════════════
# # 1. DONNÉES
# # ═══════════════════════════════════════════════════════════════════════════════

# def _build_match(periode: str) -> dict:
#     base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
#     if periode == "mois":
#         debut, fin = _mois_bornes()
#         mois_str = now_local().strftime("%Y-%m")
#         base["$or"] = [{"mois": mois_str}, {"date_clean": {"$gte": debut, "$lt": fin}}]
#     elif periode == "jour":
#         base["date_clean"] = {"$gte": now_local() - timedelta(hours=24)}
#     return base


# def get_sources_data(periode: str = "global") -> list:
#     if not MONGO_AVAILABLE or _col is None:
#         return []
#     try:
#         match = _build_match(periode)
#         pipeline = [
#             {"$match": match},
#             {"$group": {
#                 "_id":          {"$ifNull": ["$source", "Autre"]},
#                 "total":        {"$sum": 1},
#                 "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
#                 "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
#                 "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
#                 "avg_score":    {"$avg": "$sentiment_score"},
#                 "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
#             }},
#             {"$sort": {"total": -1}},
#         ]
#         results = list(_col.aggregate(pipeline))
#         total_global = sum(r["total"] for r in results) or 1
#         data = []
#         for r in results:
#             total = r["total"] or 1
#             meta  = _source_meta(r["_id"])
#             data.append({
#                 "name":         r["_id"],
#                 "total":        r["total"],
#                 "negatifs":     r["negatifs"],
#                 "positifs":     r["positifs"],
#                 "neutres":      r["neutres"],
#                 "avg_score":    round(float(r["avg_score"] or 0), 3),
#                 "pct_neg":      round(r["negatifs"] / total * 100, 1),
#                 "pct_pos":      round(r["positifs"] / total * 100, 1),
#                 "pct_total":    round(r["total"] / total_global * 100, 1),
#                 "frustrations": r["frustrations"],
#                 "health":       round(100 - r["negatifs"] / total * 100),
#                 "color":        meta["color"],
#                 "gradient":     meta["gradient"],
#             })
#         return data
#     except Exception as e:
#         print(f"Erreur get_sources_data: {e}")
#         return []


# # ═══════════════════════════════════════════════════════════════════════════════
# # 2. GRAPHIQUES
# # ═══════════════════════════════════════════════════════════════════════════════

# def _colors(theme):
#     if theme == "dark":
#         return {"bg": "#141c2e", "paper": "#141c2e", "text": "#dce8f5",
#                 "grid": "#1e2d47", "neutral": "#607b99"}
#     return {"bg": "#ffffff", "paper": "#ffffff", "text": "#1a2a4a",
#             "grid": "#e8edf5", "neutral": "#64748b"}


# def _base_layout(c, height, margin=None):
#     m = margin or dict(l=10, r=10, t=20, b=10)
#     return dict(
#         plot_bgcolor=c["bg"], paper_bgcolor=c["paper"],
#         font=dict(color=c["text"], family="'DM Sans', sans-serif", size=10),
#         height=height, margin=m,
#     )


# def make_donut_repartition(sources: list, theme="light") -> go.Figure:
#     """Donut SANS légende interne — la légende est placée à droite en HTML."""
#     c = _colors(theme)
#     if not sources:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
#                            font=dict(color=c["text"]))
#         fig.update_layout(**_base_layout(c, 280))
#         return fig
#     labels = [s["name"]  for s in sources]
#     values = [s["total"] for s in sources]
#     colors = [s["color"] for s in sources]
#     total  = sum(values)
#     fig = go.Figure(go.Pie(
#         labels=labels, values=values, hole=0.65,
#         marker=dict(colors=colors, line=dict(color=c["bg"], width=2)),
#         textinfo="none",
#         hovertemplate="<b>%{label}</b><br>%{value:,} messages<br>%{percent}<extra></extra>",
#         sort=False,
#         pull=[0.03] + [0] * (len(sources) - 1),
#     ))
#     fig.add_annotation(
#         text=f"<b>{total:,}</b>", x=0.5, y=0.58,
#         font=dict(size=20, color=c["text"], family="'DM Sans', sans-serif"),
#         showarrow=False,
#     )
#     fig.add_annotation(
#         text="messages", x=0.5, y=0.42,
#         font=dict(size=11, color=c["neutral"], family="'DM Sans', sans-serif"),
#         showarrow=False,
#     )
#     layout = _base_layout(c, 280, margin=dict(l=10, r=10, t=10, b=10))
#     layout.update(showlegend=False)
#     fig.update_layout(**layout)
#     return fig


# def make_volume_bars(sources: list, theme="light") -> go.Figure:
#     c = _colors(theme)
#     if not sources:
#         fig = go.Figure()
#         fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
#         fig.update_layout(**_base_layout(c, 300))
#         return fig
#     names    = [s["name"]     for s in sources]
#     negatifs = [s["negatifs"] for s in sources]
#     neutres  = [s["neutres"]  for s in sources]
#     positifs = [s["positifs"] for s in sources]
#     fig = go.Figure()
#     fig.add_trace(go.Bar(name="Négatifs", x=names, y=negatifs,
#                          marker=dict(color=RED, cornerradius=4),
#                          hovertemplate="<b>%{x}</b><br>Négatifs : <b>%{y:,}</b><extra></extra>"))
#     fig.add_trace(go.Bar(name="Neutres", x=names, y=neutres,
#                          marker=dict(color="rgba(100,116,139,0.5)", cornerradius=4),
#                          hovertemplate="<b>%{x}</b><br>Neutres : <b>%{y:,}</b><extra></extra>"))
#     fig.add_trace(go.Bar(name="Positifs", x=names, y=positifs,
#                          marker=dict(color=GREEN, cornerradius=4),
#                          hovertemplate="<b>%{x}</b><br>Positifs : <b>%{y:,}</b><extra></extra>"))
#     layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=60))
#     layout.update(
#         barmode="stack",
#         xaxis=dict(tickfont=dict(size=10, color=c["text"]), showgrid=False),
#         yaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=",d",
#                    tickfont=dict(size=9, color=c["text"])),
#         legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18,
#                     font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
#         hovermode="x unified",
#     )
#     fig.update_layout(**layout)
#     return fig


# # ═══════════════════════════════════════════════════════════════════════════════
# # 3. COMPOSANTS UI
# # ═══════════════════════════════════════════════════════════════════════════════

# def make_donut_legend_side(sources: list) -> html.Div:
#     """
#     Légende STYLE PHOTO 2 : bullet coloré + nom + % — placée à DROITE du donut.
#     """
#     if not sources:
#         return html.Div()

#     items = []
#     for s in sources[:8]:
#         items.append(html.Div([
#             html.Div(style={
#                 "width": "10px", "height": "10px",
#                 "borderRadius": "50%",
#                 "background": s["color"],
#                 "flexShrink": "0",
#                 "marginTop": "2px",
#             }),
#             html.Div([
#                 html.Span(s["name"], style={
#                     "fontSize": "12px", "fontWeight": "500",
#                     "color": "var(--text-primary)",
#                     "display": "block", "lineHeight": "1.2",
#                 }),
#                 html.Span(f"{s['pct_total']}%", style={
#                     "fontSize": "11px", "fontWeight": "700",
#                     "color": s["color"],
#                 }),
#             ]),
#         ], style={
#             "display": "flex", "alignItems": "flex-start", "gap": "8px",
#             "padding": "5px 0",
#         }))

#     return html.Div(items, style={
#         "display": "flex", "flexDirection": "column",
#         "justifyContent": "center",
#         "gap": "2px",
#         "padding": "10px 16px 10px 8px",
#         "minWidth": "130px",
#     })


# def make_donut_section(sources: list, theme: str) -> html.Div:
#     """
#     Section complète : Donut (gauche) + Légende style photo 2 (droite).
#     """
#     return html.Div([
#         html.Div(
#             dcc.Graph(
#                 figure=make_donut_repartition(sources, theme),
#                 config={"displayModeBar": False},
#                 style={"width": "100%", "height": "280px"},
#             ),
#             style={"flex": "1", "minWidth": "0"},
#         ),
#         make_donut_legend_side(sources),
#     ], style={
#         "display": "flex",
#         "alignItems": "center",
#         "gap": "0px",
#     })


# def make_source_cards(sources: list) -> html.Div:
#     """Cartes horizontales avec vrais SVG officiels (html.Img + data URI)."""
#     if not sources:
#         return html.Div()

#     cards = []
#     for s in sources:
#         neg_color = RED if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN

#         icon_box = html.Div(
#             _logo_img(s["name"], size=26),
#             style={
#                 "width": "52px", "height": "52px", "borderRadius": "14px",
#                 "background": s["gradient"],
#                 "display": "flex", "alignItems": "center", "justifyContent": "center",
#                 "flexShrink": "0",
#                 "boxShadow": f"0 4px 14px {s['color']}45",
#             },
#         )

#         info_block = html.Div([
#             html.Div(s["name"], style={
#                 "fontSize": "10px", "fontWeight": "700", "color": "var(--text-secondary)",
#                 "textTransform": "uppercase", "letterSpacing": "0.5px", "marginBottom": "2px",
#                 "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis",
#             }),
#             html.Div(
#                 f"{s['total']:,}".replace(",", "\u202f"),
#                 style={"fontSize": "20px", "fontWeight": "800", "color": s["color"],
#                        "lineHeight": "1.1", "marginBottom": "5px"},
#             ),
#             html.Div([
#                 html.Span(f"↑ {s['pct_pos']}%",
#                           style={"fontSize": "11px", "fontWeight": "700", "color": GREEN}),
#                 html.Span(f"↓ {s['pct_neg']}%",
#                           style={"fontSize": "11px", "fontWeight": "700", "color": neg_color}),
#             ], style={"display": "flex", "gap": "10px", "marginBottom": "7px"}),
#             html.Div([
#                 html.Div(style={
#                     "width": f"{s['pct_neg']}%", "height": "100%",
#                     "borderRadius": "2px", "background": neg_color,
#                     "transition": "width 0.6s ease",
#                 }),
#             ], style={"width": "100%", "height": "3px",
#                       "background": "var(--border-color)", "borderRadius": "2px",
#                       "overflow": "hidden"}),
#         ], style={"flex": "1", "minWidth": "0"})

#         cards.append(html.Div([icon_box, info_block], style={
#             "display": "flex", "alignItems": "center", "gap": "14px",
#             "background": "var(--bg-card)",
#             "border": "0.5px solid var(--border-color)",
#             "borderLeft": f"3px solid {s['color']}",
#             "borderRadius": "12px", "padding": "14px 16px",
#             "cursor": "default",
#             "boxShadow": "0 1px 6px rgba(0,48,135,.05)",
#         }))

#     return html.Div([
#         html.Div("VUE D'ENSEMBLE DES SOURCES", style={
#             "fontSize": "10px", "fontWeight": "700", "color": NEUTRAL,
#             "letterSpacing": "0.6px", "textTransform": "uppercase", "marginBottom": "12px",
#         }),
#         html.Div(cards, style={
#             "display": "grid",
#             "gridTemplateColumns": "repeat(auto-fill, minmax(210px, 1fr))",
#             "gap": "12px",
#         }),
#     ], style={"marginBottom": "22px"})


# def _chart_card_wrap(icon_cls, title, tt_title, tt_body, children):
#     return html.Div([
#         html.Div([
#             html.Div(html.I(className=icon_cls, style={"fontSize": "14px"}), className="card-icon"),
#             html.Span(title, className="card-title"),
#             html.Div([
#                 html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
#                 html.Div([
#                     html.Div(tt_title, className="tooltip-title"),
#                     html.Div(tt_body,  className="tooltip-body"),
#                 ], className="card-tooltip"),
#             ], className="tooltip-wrapper"),
#         ], className="card-header"),
#         html.Div(children, className="card-content"),
#     ], className="chart-card")

# def make_periode_filter(active_periode="global"):
#     def _btn_style(is_active):
#         return style_btn_active if is_active else style_btn_inactive

#     today = now_local().strftime("%d/%m/%Y")

#     return html.Div(
#         [
#             # ── Gauche : label + boutons ────────────────────────────────────
#             html.Div([
#                 html.I(className="fas fa-calendar-alt",
#                        style={"fontSize": "13px", "color": BLUE, "marginRight": "6px"}),
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

#             # ── Droite : badge date uniquement (pas de btn-analytics-refresh) ──
#             html.Div(
#                 [
#                     html.I(className="far fa-calendar-alt",
#                            style={"marginRight": "5px", "fontSize": "13px", "color": BLUE}),
#                     html.Span(f"Mise à jour : {today}",
#                               style={"fontSize": "13px", "color": NEUTRAL}),
#                 ],
#                 style={
#                     "display": "flex", "alignItems": "center",
#                     "background": "white", "padding": "0 15px",
#                     "borderRadius": "8px", "height": "36px",
#                     "border": "1px solid #e0e0e0",
#                 }
#             ),
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
# def make_table_sources(sources: list) -> html.Div:
#     if not sources:
#         return html.Div("Aucune donnée",
#                         style={"color": NEUTRAL, "padding": "20px", "textAlign": "center"})

#     th_style = {
#         "textAlign": "right", "padding": "10px 14px",
#         "fontSize": "10px", "color": NEUTRAL, "fontWeight": "700",
#         "textTransform": "uppercase", "letterSpacing": "0.4px",
#         "borderBottom": "2px solid var(--border-color)",
#         "background": "var(--stat-bg)", "whiteSpace": "nowrap",
#     }
#     th_left = {**th_style, "textAlign": "left"}

#     header = html.Thead(html.Tr([
#         html.Th("Source",       style=th_left),
#         html.Th("Total",        style=th_style),
#         html.Th("Négatifs",     style=th_style),
#         html.Th("Positifs",     style=th_style),
#         html.Th("Neutres",      style=th_style),
#         html.Th("Taux négatif", style=th_style),
#         html.Th("Score moy.",   style=th_style),
#         html.Th("Frustrations", style=th_style),
#         html.Th("Santé",        style=th_style),
#     ]))

#     rows = []
#     for i, s in enumerate(sources):
#         health_color = GREEN if s["health"] > 55 else ORANGE if s["health"] > 45 else RED
#         taux_color   = RED   if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN
#         taux_bg      = RED_BG if s["pct_neg"] > 58 else ORANGE_BG if s["pct_neg"] > 45 else GREEN_BG
#         score_color  = GREEN if s["avg_score"] >= -0.2 else ORANGE if s["avg_score"] >= -0.5 else RED

#         td = {"padding": "10px 14px", "fontSize": "12px",
#               "borderBottom": "1px solid var(--border-color)"}

#         source_cell = html.Td(
#             html.Div([
#                 html.Div(
#                     _logo_img(s["name"], size=14),
#                     style={
#                         "width": "28px", "height": "28px", "borderRadius": "8px",
#                         "background": s["gradient"],
#                         "display": "flex", "alignItems": "center", "justifyContent": "center",
#                         "flexShrink": "0", "boxShadow": f"0 2px 6px {s['color']}55",
#                     },
#                 ),
#                 html.Span(s["name"], style={"fontWeight": "600", "fontSize": "12px",
#                                              "color": "var(--text-primary)"}),
#             ], style={"display": "flex", "alignItems": "center", "gap": "9px"}),
#             style=td,
#         )

#         rows.append(html.Tr([
#             source_cell,
#             html.Td(f"{s['total']:,}".replace(",", "\u202f"),
#                     style={**td, "textAlign": "right", "fontWeight": "600",
#                            "color": "var(--text-primary)"}),
#             html.Td(f"{s['negatifs']:,}".replace(",", "\u202f"),
#                     style={**td, "textAlign": "right", "color": RED}),
#             html.Td(f"{s['positifs']:,}".replace(",", "\u202f"),
#                     style={**td, "textAlign": "right", "color": GREEN}),
#             html.Td(f"{s['neutres']:,}".replace(",", "\u202f"),
#                     style={**td, "textAlign": "right", "color": NEUTRAL}),
#             html.Td(html.Span(f"{s['pct_neg']}%", style={
#                 "fontSize": "11px", "fontWeight": "700",
#                 "color": taux_color, "background": taux_bg,
#                 "padding": "3px 8px", "borderRadius": "8px",
#             }), style={**td, "textAlign": "right"}),
#             html.Td(f"{s['avg_score']:+.3f}",
#                     style={**td, "textAlign": "right", "fontWeight": "600",
#                            "color": score_color}),
#             html.Td(str(s["frustrations"]),
#                     style={**td, "textAlign": "right", "color": NEUTRAL}),
#             html.Td(html.Div([
#                 html.Div([
#                     html.Div(style={
#                         "width": f"{s['health']}%", "height": "100%",
#                         "borderRadius": "3px", "background": health_color,
#                         "transition": "width 0.6s ease",
#                     }),
#                 ], style={"width": "52px", "height": "6px",
#                           "background": "var(--border-color)",
#                           "borderRadius": "3px", "overflow": "hidden"}),
#                 html.Span(str(s["health"]),
#                           style={"fontSize": "11px", "color": NEUTRAL,
#                                  "fontWeight": "600", "minWidth": "22px"}),
#             ], style={"display": "flex", "alignItems": "center", "gap": "6px",
#                       "justifyContent": "flex-end"}),
#                 style={**td}),
#         ], style={"background": "var(--bg-card)" if i % 2 == 0 else "var(--stat-bg)"}))

#     return html.Div(html.Table(
#         [header, html.Tbody(rows)],
#         style={"width": "100%", "borderCollapse": "collapse"},
#     ), style={"overflowX": "auto"})


# # ═══════════════════════════════════════════════════════════════════════════════
# # 4. RENDER
# # ═══════════════════════════════════════════════════════════════════════════════

# def render_sources_page(theme="light", user_data=None, periode="global"):
#     sources = get_sources_data(periode)
#     total   = sum(s["total"] for s in sources) if sources else 0
#     nb_src  = len(sources)

#     periode_labels = {
#         "global": "historique complet",
#         "mois":   now_local().strftime("%B %Y"),
#         "jour":   "dernières 24h",
#     }
#     sub = (f"{nb_src} sources · {total:,} messages · {periode_labels.get(periode, '')}"
#            .replace(",", "\u202f"))

#     content = html.Div([

#         # ── Filtre période ────────────────────────────────────────────────────
#         make_periode_filter(periode),

#         # ── Social Media Cards horizontales ───────────────────────────────────
#         make_source_cards(sources),

#         # ── Ligne 1 : Donut (avec légende à droite) + Barres empilées ────────
#         # ✅ Les deux cartes ont la même hauteur grâce au CSS (align-items: stretch)
#         # html.Div([
#         #     _chart_card_wrap(
#         #         "fas fa-chart-pie", "RÉPARTITION DES SOURCES",
#         #         "Répartition par Source",
#         #         "Part de volume de chaque réseau social dans le total des commentaires.",
#         #         make_donut_section(sources, theme),
#         #     ),
#         #     _chart_card_wrap(
#         #         "fas fa-chart-bar", "VOLUME & SENTIMENT PAR SOURCE",
#         #         "Volume et Sentiment",
#         #         "Décomposition Négatifs / Neutres / Positifs pour chaque source.",
#         #         dcc.Graph(
#         #             figure=make_volume_bars(sources, theme),
#         #             config={"displayModeBar": False},
#         #             style={"width": "100%"},
#         #         ),
#         #     ),
#         # ], className="row-2cols", style={"marginTop": "20px"}),

#         # ── Tableau détaillé ──────────────────────────────────────────────────
#         html.Div([
#             _chart_card_wrap(
#                 "fas fa-table-list", "TABLEAU DÉTAILLÉ PAR SOURCE",
#                 "Tableau Détaillé",
#                 "Toutes les métriques par source : volume, sentiments, score moyen, "
#                 "frustrations et score santé.",
#                 make_table_sources(sources),
#             ),
#         ], style={"marginTop": "14px"}),

#     ], style={"padding": "0"}, className="dashboard-container")

#     return make_page_layout("sources", "Analyse par Source", sub, content, theme, user_data)


# # ═══════════════════════════════════════════════════════════════════════════════
# # 5. LAYOUT + CALLBACKS
# # ═══════════════════════════════════════════════════════════════════════════════

# layout = html.Div(
#     id="sources-wrapper",
#     **{"data-theme": "light"},
#     children=[
#         dcc.Store(id="periode-sources-store", data="global", storage_type="session"),
#         dcc.Interval(id="refresh-interval-sources", interval=300_000, n_intervals=0),
#         html.Div(id="full-sources-layout"),
#     ],
# )


# @callback(
#     Output("periode-sources-store", "data"),
#     Output("btn-sources-global",    "style"),
#     Output("btn-sources-mois",      "style"),
#     Output("btn-sources-jour",      "style"),
#     Input("btn-sources-global",     "n_clicks"),
#     Input("btn-sources-mois",       "n_clicks"),
#     Input("btn-sources-jour",       "n_clicks"),
#     State("periode-sources-store",  "data"),
#     prevent_initial_call=True,
# )
# def set_sources_periode(n_g, n_m, n_j, current):
#     A, I = style_btn_active, style_btn_inactive
#     ctx  = dash.callback_context
#     if not ctx.triggered:
#         s = {"global": [A,I,I], "mois": [I,A,I], "jour": [I,I,A]}.get(current or "global", [A,I,I])
#         return current or "global", s[0], s[1], s[2]
#     btn = ctx.triggered[0]["prop_id"].split(".")[0]
#     if btn == "btn-sources-mois":
#         return "mois", I, A, I
#     elif btn == "btn-sources-jour":
#         return "jour", I, I, A
#     return "global", A, I, I


# @callback(
#     Output("full-sources-layout", "children"),
#     Output("sources-wrapper",     "data-theme"),
#     Input("theme-store",              "data"),
#     Input("auth-store",               "data"),
#     Input("periode-sources-store",    "data"),
#     Input("refresh-interval-sources", "n_intervals"),
# )
# def update_sources_page(theme, auth_data, periode, _):
#     theme   = theme   or "light"
#     periode = periode or "global"
#     user_data = None
#     if auth_data and auth_data.get("is_authenticated"):
#         user_data = auth_data.get("user", {})
#     return render_sources_page(theme, user_data, periode), theme

"""
Page Analyse par Source — ALGÉRIE TÉLÉCOM
✅ Graphique Radar (santé & score multi-dimensionnel) remplace le donut
✅ 4 graphiques : Radar, Barres empilées, Taux négatif H-bar, Score sentiment
✅ Cartes sources horizontales avec SVG officiels base64
✅ Tableau détaillé complet
✅ Design system identique au dashboard
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys, os, base64

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from database import MONGO_AVAILABLE, _col

dash.register_page(__name__, path='/sources', name='Analyse par Source')

# ── PALETTE ───────────────────────────────────────────────────────────────────
BLUE      = "#003087"
BLUE_MID  = "#1a4fa0"
GREEN     = "#00a854"
RED       = "#e8384f"
RED_BG    = "#fde8eb"
ORANGE    = "#f59e0b"
ORANGE_BG = "#fef3cd"
GREEN_BG  = "#e6f7ef"
NEUTRAL   = "#64748b"

# ── SVG LOGOS BASE64 ──────────────────────────────────────────────────────────
_SVGS = {
    "facebook": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="white"/></svg>',
    "instagram": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" fill="white"/></svg>',
    "youtube":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" fill="white"/></svg>',
    "x":         '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="white"/></svg>',
    "twitter":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="white"/></svg>',
    "linkedin":  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" fill="white"/></svg>',
    "tiktok": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 15.64a6.34 6.34 0 0 0 10.86 4.37 6.34 6.34 0 0 0 1.55-4.12V11.1a8.16 8.16 0 0 0 4.66 1.36V8.84a4.82 4.82 0 0 1-2.48-2.15z" fill="white"/></svg>',
    "whatsapp":  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" fill="white"/></svg>',
    "idoommarket": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 6h-2V5c0-1.654-1.346-3-3-3h-4C8.346 2 7 3.346 7 5v1H5C3.897 6 3 6.897 3 8v11c0 1.103.897 2 2 2h14c1.103 0 2-.897 2-2V8c0-1.103-.897-2-2-2zm-8-1h2v1h-2V5zm2 9h-2v2H9v-2H7v-2h2v-2h2v2h2v2z" fill="white"/></svg>',
    "globe":     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93V18c0-.55-.45-1-1-1H8v-2c0-.55-.45-1-1-1H5.07C4.4 13.07 4 12.58 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8c-.34 0-.67-.02-1-.07z" fill="white"/></svg>',
}

SOURCE_META = {
    "facebook":    {"color": "#1877F2", "gradient": "linear-gradient(135deg,#1877F2,#0d5fd4)", "label": "Facebook"},
    "youtube":     {"color": "#FF0000", "gradient": "linear-gradient(135deg,#FF0000,#cc0000)", "label": "YouTube"},
    "instagram":   {"color": "#E1306C", "gradient": "linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)", "label": "Instagram"},
    "x":           {"color": "#444444", "gradient": "linear-gradient(135deg,#14171A,#444)", "label": "X"},
    "twitter":     {"color": "#444444", "gradient": "linear-gradient(135deg,#14171A,#444)", "label": "X / Twitter"},
    "linkedin":    {"color": "#0077B5", "gradient": "linear-gradient(135deg,#0077B5,#005885)", "label": "LinkedIn"},
    "tiktok":      {"color": "#010101", "gradient": "linear-gradient(135deg, #010101 0%, #010101 100%)", "label": "TikTok"},
    "whatsapp":    {"color": "#25D366", "gradient": "linear-gradient(135deg,#25D366,#128C7E)", "label": "WhatsApp"},
    "idoommarket": {"color": "#00a854", "gradient": "linear-gradient(135deg,#00a854,#007a3d)", "label": "IdoomMarket"},
}
_DEFAULT_META = {"color": BLUE_MID, "gradient": f"linear-gradient(135deg,{BLUE_MID},{BLUE})", "label": "Autre"}


def _source_meta(name: str) -> dict:
    key = (name or "").lower().strip()
    for k, meta in SOURCE_META.items():
        if k in key:
            return meta
    return {**_DEFAULT_META, "label": name or "Autre"}


def _svg_uri(name: str) -> str:
    key = (name or "").lower().strip()
    svg_str = None
    for k in _SVGS:
        if k in key:
            svg_str = _SVGS[k]
            break
    if svg_str is None:
        svg_str = _SVGS["globe"]
    encoded = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _logo_img(name: str, size: int = 18) -> html.Img:
    return html.Img(src=_svg_uri(name), style={"width": f"{size}px", "height": f"{size}px", "objectFit": "contain", "display": "block"})


# ── Styles boutons ─────────────────────────────────────────────────────────────
style_btn_active = {
    "padding": "6px 16px", "borderRadius": "20px", "border": "none",
    "background": BLUE, "color": "white", "cursor": "pointer",
    "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
    "display": "flex", "alignItems": "center", "gap": "6px",
}
style_btn_inactive = {
    "padding": "6px 16px", "borderRadius": "20px",
    "border": f"1px solid {BLUE}", "background": "transparent",
    "color": BLUE, "cursor": "pointer", "fontSize": "12px", "fontWeight": "500",
    "transition": "all 0.2s ease",
    "display": "flex", "alignItems": "center", "gap": "6px",
}


def now_local():
    return datetime.utcnow() + timedelta(hours=1)


def _mois_bornes():
    now = now_local()
    debut = datetime(now.year, now.month, 1)
    fin = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
    return debut, fin


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def _build_match(periode: str) -> dict:
    base = {"sentiment_label": {"$in": ["POSITIF", "NEGATIF", "NEUTRE"]}}
    if periode == "mois":
        debut, fin = _mois_bornes()
        mois_str = now_local().strftime("%Y-%m")
        base["$or"] = [{"mois": mois_str}, {"date_clean": {"$gte": debut, "$lt": fin}}]
    elif periode == "jour":
        base["date_clean"] = {"$gte": now_local() - timedelta(hours=24)}
    return base


def get_sources_data(periode: str = "global") -> list:
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        match = _build_match(periode)
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id":          {"$ifNull": ["$source", "Autre"]},
                "total":        {"$sum": 1},
                "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]}, 1, 0]}},
                "avg_score":    {"$avg": "$sentiment_score"},
                "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
            }},
            {"$sort": {"total": -1}},
        ]
        results = list(_col.aggregate(pipeline))
        total_global = sum(r["total"] for r in results) or 1
        max_frust = max((r["frustrations"] for r in results), default=1) or 1
        data = []
        for r in results:
            total = r["total"] or 1
            meta = _source_meta(r["_id"])
            pct_neg = round(r["negatifs"] / total * 100, 1)
            health = round(100 - pct_neg)
            avg_score = round(float(r["avg_score"] or 0), 3)
            data.append({
                "name":         r["_id"],
                "total":        r["total"],
                "negatifs":     r["negatifs"],
                "positifs":     r["positifs"],
                "neutres":      r["neutres"],
                "avg_score":    avg_score,
                "pct_neg":      pct_neg,
                "pct_pos":      round(r["positifs"] / total * 100, 1),
                "pct_total":    round(r["total"] / total_global * 100, 1),
                "frustrations": r["frustrations"],
                "health":       health,
                "color":        meta["color"],
                "gradient":     meta["gradient"],
                # Scores normalisés [0–100] pour le radar
                "radar_health":   health,
                "radar_pos_pct":  round(r["positifs"] / total * 100),
                "radar_frust_inv": round(100 - (r["frustrations"] / max_frust * 100)),
                "radar_score":    round((avg_score + 0.7) / 0.77 * 100),
                "radar_volume":   round(r["total"] / total_global * 100),
            })
        return data
    except Exception as e:
        print(f"Erreur get_sources_data: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GRAPHIQUES PLOTLY
# ═══════════════════════════════════════════════════════════════════════════════

def _colors(theme):
    if theme == "dark":
        return {"bg": "#141c2e", "paper": "#141c2e", "text": "#dce8f5",
                "grid": "#1e2d47", "neutral": "#607b99"}
    return {"bg": "#ffffff", "paper": "#ffffff", "text": "#1a2a4a",
            "grid": "#e8edf5", "neutral": "#64748b"}


def _base_layout(c, height, margin=None):
    m = margin or dict(l=10, r=10, t=20, b=10)
    return dict(
        plot_bgcolor=c["bg"], paper_bgcolor=c["paper"],
        font=dict(color=c["text"], family="'DM Sans', sans-serif", size=10),
        height=height, margin=m,
    )

def make_radar_chart(sources: list, theme="light") -> go.Figure:
    """
    Graphique Radar (Spider) multi-dimensionnel par source.
    Axes : Santé, % Positifs, Frustrations (inversé), Score (normalisé), Volume (normalisé).
    """
    c = _colors(theme)
    if not sources:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False, font=dict(color=c["text"]))
        fig.update_layout(**_base_layout(c, 320))
        return fig

    categories = ["Santé", "% Positifs", "Frustrations<br>(inversé)", "Score<br>(normalisé)", "Volume<br>(normalisé)"]

    fig = go.Figure()
    for s in sources:
        vals = [
            s["radar_health"],
            s["radar_pos_pct"],
            s["radar_frust_inv"],
            max(0, min(100, s["radar_score"])),
            s["radar_volume"],
        ]
        
        # Convertir la couleur hex en rgba (opacité 0.1)
        hex_color = s["color"].lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        fill_color = f"rgba({r}, {g}, {b}, 0.1)"
        
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            name=s["name"],
            line=dict(color=s["color"], width=2),
            fill="toself",
            fillcolor=fill_color,  # ← format rgba au lieu de #XXXXXX18
            marker=dict(size=5, color=s["color"]),
            hovertemplate=(
                f"<b>{s['name']}</b><br>"
                "%{theta} : <b>%{r:.0f}</b><extra></extra>"
            ),
        ))

    layout = _base_layout(c, 320, margin=dict(l=50, r=50, t=30, b=30))
    layout.update(
        polar=dict(
            bgcolor=c["bg"],
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(size=9, color=c["neutral"]),
                gridcolor=c["grid"],
                linecolor=c["grid"],
                tickvals=[0, 25, 50, 75, 100],
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color=c["text"]),
                gridcolor=c["grid"],
                linecolor=c["grid"],
            ),
        ),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", y=-0.12,
            font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    fig.update_layout(**layout)
    return fig

def make_volume_bars(sources: list, theme="light") -> go.Figure:
    """Barres empilées Négatifs / Neutres / Positifs par source."""
    c = _colors(theme)
    if not sources:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**_base_layout(c, 300))
        return fig

    names    = [s["name"]     for s in sources]
    negatifs = [s["negatifs"] for s in sources]
    neutres  = [s["neutres"]  for s in sources]
    positifs = [s["positifs"] for s in sources]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Négatifs", x=names, y=negatifs,
        marker=dict(color=RED, cornerradius=4),
        hovertemplate="<b>%{x}</b><br>Négatifs : <b>%{y:,}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Neutres", x=names, y=neutres,
        marker=dict(color="rgba(100,116,139,0.5)", cornerradius=4),
        hovertemplate="<b>%{x}</b><br>Neutres : <b>%{y:,}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Positifs", x=names, y=positifs,
        marker=dict(color=GREEN, cornerradius=4),
        hovertemplate="<b>%{x}</b><br>Positifs : <b>%{y:,}</b><extra></extra>",
    ))
    layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=10, b=60))
    layout.update(
        barmode="stack",
        xaxis=dict(tickfont=dict(size=10, color=c["text"]), showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=",d",
                   tickfont=dict(size=9, color=c["text"])),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18,
                    font=dict(size=10, color=c["text"]), bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    fig.update_layout(**layout)
    return fig


def make_taux_negatif_bars(sources: list, theme="light") -> go.Figure:
    """Barres horizontales — taux négatif par source, classées croissant."""
    c = _colors(theme)
    if not sources:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**_base_layout(c, 300))
        return fig

    sorted_s   = sorted(sources, key=lambda s: s["pct_neg"])
    names      = [s["name"]    for s in sorted_s]
    pct_neg    = [s["pct_neg"] for s in sorted_s]
    bar_colors = [RED if p > 58 else ORANGE if p > 45 else GREEN for p in pct_neg]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pct_neg, y=names, orientation="h",
        marker=dict(color=bar_colors, cornerradius=5),
        text=[f"{p}%" for p in pct_neg],
        textposition="outside",
        textfont=dict(size=10, color=c["text"], weight="bold"),
        hovertemplate="<b>%{y}</b><br>Taux négatif : <b>%{x}%</b><extra></extra>",
        width=0.6,
    ))
    fig.add_vline(
        x=50, line_dash="dot", line_color=RED, opacity=0.4,
        annotation_text="Seuil 50%",
        annotation_font=dict(size=9, color=RED),
        annotation_position="top right",
    )
    layout = _base_layout(c, 300, margin=dict(l=10, r=60, t=20, b=10))
    layout.update(
        xaxis=dict(
            range=[0, max(pct_neg) * 1.15 if pct_neg else 100],
            ticksuffix="%", showgrid=True, gridcolor=c["grid"],
            tickfont=dict(size=9, color=c["text"]),
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color=c["text"])),
        showlegend=False,
    )
    fig.update_layout(**layout)
    return fig


def make_score_bars(sources: list, theme="light") -> go.Figure:
    """Barres verticales — score moyen de sentiment par source."""
    c = _colors(theme)
    if not sources:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**_base_layout(c, 300))
        return fig

    names  = [s["name"]      for s in sources]
    scores = [s["avg_score"] for s in sources]
    colors = [GREEN if sc >= 0 else RED for sc in scores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=scores,
        marker=dict(color=colors, cornerradius=5),
        text=[f"{sc:+.3f}" for sc in scores],
        textposition="outside",
        textfont=dict(size=10, color=c["text"]),
        hovertemplate="<b>%{x}</b><br>Score : <b>%{y:+.3f}</b><extra></extra>",
        width=0.55,
    ))
    fig.add_hline(y=0, line_color=c["neutral"], line_width=1)
    layout = _base_layout(c, 300, margin=dict(l=10, r=10, t=30, b=60))
    layout.update(
        xaxis=dict(tickfont=dict(size=10, color=c["text"]), showgrid=False),
        yaxis=dict(
            showgrid=True, gridcolor=c["grid"],
            tickfont=dict(size=9, color=c["text"]),
            range=[min(scores) * 1.25 - 0.05, max(scores) * 1.3 + 0.05] if scores else [-1, 0.5],
        ),
        showlegend=False,
    )
    fig.update_layout(**layout)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 3. COMPOSANTS UI
# ═══════════════════════════════════════════════════════════════════════════════

def _chart_card_wrap(icon_cls, title, tt_title, tt_body, children):
    return html.Div([
        html.Div([
            html.Div(html.I(className=icon_cls, style={"fontSize": "14px"}), className="card-icon"),
            html.Span(title, className="card-title"),
            html.Div([
                html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
                html.Div([
                    html.Div(tt_title, className="tooltip-title"),
                    html.Div(tt_body, className="tooltip-body"),
                ], className="card-tooltip"),
            ], className="tooltip-wrapper"),
        ], className="card-header"),
        html.Div(children, className="card-content"),
    ], className="chart-card")


def make_source_cards(sources: list) -> html.Div:
    """Cartes horizontales avec logos SVG officiels + barre de progression."""
    if not sources:
        return html.Div()

    cards = []
    for s in sources:
        neg_color = RED if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN

        icon_box = html.Div(
            _logo_img(s["name"], size=26),
            style={
                "width": "52px", "height": "52px", "borderRadius": "14px",
                "background": s["gradient"],
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "flexShrink": "0",
            },
        )

        info_block = html.Div([
            html.Div(s["name"], style={
                "fontSize": "10px", "fontWeight": "700", "color": "var(--text-secondary)",
                "textTransform": "uppercase", "letterSpacing": "0.5px", "marginBottom": "2px",
                "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis",
            }),
            html.Div(
                f"{s['total']:,}".replace(",", "\u202f"),
                style={"fontSize": "20px", "fontWeight": "800", "color": s["color"],
                       "lineHeight": "1.1", "marginBottom": "4px"},
            ),
            html.Div([
                html.Span(f"↑ {s['pct_pos']}%",
                          style={"fontSize": "11px", "fontWeight": "700", "color": GREEN}),
                html.Span(f"↓ {s['pct_neg']}%",
                          style={"fontSize": "11px", "fontWeight": "700", "color": neg_color}),
            ], style={"display": "flex", "gap": "10px", "marginBottom": "7px"}),
            html.Div([
                html.Div(style={
                    "width": f"{s['pct_neg']}%", "height": "100%",
                    "borderRadius": "2px", "background": neg_color,
                }),
            ], style={"width": "100%", "height": "3px",
                      "background": "var(--border-color)", "borderRadius": "2px", "overflow": "hidden"}),
        ], style={"flex": "1", "minWidth": "0"})

        cards.append(html.Div([icon_box, info_block], style={
            "display": "flex", "alignItems": "center", "gap": "14px",
            "background": "var(--bg-card)",
            "border": "0.5px solid var(--border-color)",
            "borderLeft": f"3px solid {s['color']}",
            "borderRadius": "12px", "padding": "14px 16px",
            "cursor": "default",
            "boxShadow": "0 1px 6px rgba(0,48,135,.05)",
        }))

    return html.Div([
        html.Div("VUE D'ENSEMBLE DES SOURCES", style={
            "fontSize": "10px", "fontWeight": "700", "color": NEUTRAL,
            "letterSpacing": "0.6px", "textTransform": "uppercase", "marginBottom": "12px",
        }),
        html.Div(cards, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(210px, 1fr))",
            "gap": "12px",
        }),
    ], style={"marginBottom": "22px"})

def make_periode_filter(active: str = "global") -> html.Div:
    def _btn(label, icon, val):
        is_active = active == val
        return html.Button(
            [html.I(className=icon, style={"fontSize": "11px"}), label],
            id=f"btn-sources-{val}", n_clicks=0,
            style=style_btn_active if is_active else style_btn_inactive,
        )
    
    today = now_local().strftime("%d/%m/%Y")
    
    return html.Div([
        # ── Gauche : label + boutons de période ────────────────────────────────
        html.Div([
            html.I(className="fas fa-calendar-alt",
                   style={"fontSize": "13px", "color": BLUE, "marginRight": "6px"}),
            html.Span("Période d'analyse :",
                      style={"fontSize": "13px", "color": NEUTRAL,
                             "fontWeight": "500", "marginRight": "12px",
                             "whiteSpace": "nowrap"}),
            _btn("Global",      "fas fa-globe",         "global"),
            _btn("Ce Mois",     "fas fa-calendar-day",  "mois"),
            _btn("Aujourd'hui", "fas fa-clock",         "jour"),
        ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),

        # ── Droite : badge date + bouton Actualiser ───────────────────────────
        html.Div([
            # Badge date
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
            # Bouton Actualiser
            html.Button(
                [html.I(className="fas fa-sync-alt", style={"marginRight": "5px", "fontSize": "12px"}),
                 html.Span("Actualiser", style={"fontSize": "12px"})],
                id="btn-sources-refresh",
                n_clicks=0,
                style={
                    "background": BLUE, "color": "white", "border": "none",
                    "borderRadius": "8px", "padding": "0 18px", "cursor": "pointer",
                    "fontSize": "12px", "display": "flex", "alignItems": "center",
                    "height": "36px", "gap": "6px",
                },
            ),
        ], style={"display": "flex", "gap": "10px", "alignItems": "center"}),
        
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "gap": "12px",
        "padding": "12px 20px",
        "background": "var(--bg-card)",
        "borderRadius": "14px",
        "marginBottom": "20px",
        "border": "1px solid var(--border-color)",
        "boxShadow": "0 1px 4px rgba(0,48,135,.06)",
        "flexWrap": "wrap",
    })

def make_table_sources(sources: list) -> html.Div:
    if not sources:
        return html.Div("Aucune donnée",
                        style={"color": NEUTRAL, "padding": "20px", "textAlign": "center"})

    th_style = {
        "textAlign": "right", "padding": "10px 14px",
        "fontSize": "10px", "color": NEUTRAL, "fontWeight": "700",
        "textTransform": "uppercase", "letterSpacing": "0.4px",
        "borderBottom": "2px solid var(--border-color)",
        "background": "var(--stat-bg)", "whiteSpace": "nowrap",
    }
    th_left = {**th_style, "textAlign": "left"}

    header = html.Thead(html.Tr([
        html.Th("Source",       style=th_left),
        html.Th("Total",        style=th_style),
        html.Th("Négatifs",     style=th_style),
        html.Th("Positifs",     style=th_style),
        html.Th("Neutres",      style=th_style),
        html.Th("Taux négatif", style=th_style),
        html.Th("Score moy.",   style=th_style),
        html.Th("Frustrations", style=th_style),
        html.Th("Santé",        style=th_style),
    ]))

    rows = []
    for i, s in enumerate(sources):
        health_color = GREEN if s["health"] > 55 else ORANGE if s["health"] > 45 else RED
        taux_color   = RED   if s["pct_neg"] > 58 else ORANGE if s["pct_neg"] > 45 else GREEN
        taux_bg      = RED_BG if s["pct_neg"] > 58 else ORANGE_BG if s["pct_neg"] > 45 else GREEN_BG
        score_color  = GREEN if s["avg_score"] >= 0 else ORANGE if s["avg_score"] >= -0.2 else RED

        td = {"padding": "10px 14px", "fontSize": "12px",
              "borderBottom": "1px solid var(--border-color)"}

        source_cell = html.Td(
            html.Div([
                html.Div(
                    _logo_img(s["name"], size=14),
                    style={
                        "width": "28px", "height": "28px", "borderRadius": "8px",
                        "background": s["gradient"],
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "flexShrink": "0", "boxShadow": f"0 2px 6px {s['color']}55",
                    },
                ),
                html.Span(s["name"], style={"fontWeight": "600", "fontSize": "12px",
                                            "color": "var(--text-primary)"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "9px"}),
            style=td,
        )

        rows.append(html.Tr([
            source_cell,
            html.Td(f"{s['total']:,}".replace(",", "\u202f"),
                    style={**td, "textAlign": "right", "fontWeight": "600", "color": "var(--text-primary)"}),
            html.Td(f"{s['negatifs']:,}".replace(",", "\u202f"),
                    style={**td, "textAlign": "right", "color": RED}),
            html.Td(f"{s['positifs']:,}".replace(",", "\u202f"),
                    style={**td, "textAlign": "right", "color": GREEN}),
            html.Td(f"{s['neutres']:,}".replace(",", "\u202f"),
                    style={**td, "textAlign": "right", "color": NEUTRAL}),
            html.Td(html.Span(f"{s['pct_neg']}%", style={
                "fontSize": "11px", "fontWeight": "700",
                "color": taux_color, "background": taux_bg,
                "padding": "3px 8px", "borderRadius": "8px",
            }), style={**td, "textAlign": "right"}),
            html.Td(f"{s['avg_score']:+.3f}",
                    style={**td, "textAlign": "right", "fontWeight": "600", "color": score_color}),
            html.Td(str(s["frustrations"]),
                    style={**td, "textAlign": "right", "color": NEUTRAL}),
            html.Td(html.Div([
                html.Div([
                    html.Div(style={
                        "width": f"{s['health']}%", "height": "100%",
                        "borderRadius": "3px", "background": health_color,
                        "transition": "width 0.6s ease",
                    }),
                ], style={"width": "52px", "height": "6px",
                          "background": "var(--border-color)", "borderRadius": "3px", "overflow": "hidden"}),
                html.Span(str(s["health"]),
                          style={"fontSize": "11px", "color": NEUTRAL, "fontWeight": "600", "minWidth": "22px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "6px", "justifyContent": "flex-end"}),
                style={**td}),
        ], style={"background": "var(--bg-card)" if i % 2 == 0 else "var(--stat-bg)"}))

    return html.Div(html.Table(
        [header, html.Tbody(rows)],
        style={"width": "100%", "borderCollapse": "collapse"},
    ), style={"overflowX": "auto"})


# ═══════════════════════════════════════════════════════════════════════════════
# 4. RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render_sources_page(theme="light", user_data=None, periode="global"):
    sources = get_sources_data(periode)
    total   = sum(s["total"] for s in sources) if sources else 0
    nb_src  = len(sources)

    periode_labels = {
        "global": "historique complet",
        "mois":   now_local().strftime("%B %Y"),
        "jour":   "dernières 24h",
    }
    sub = (f"{nb_src} sources · {total:,} messages · {periode_labels.get(periode, '')}"
           .replace(",", "\u202f"))

    graph_cfg = {"displayModeBar": False}

    content = html.Div([

        # ── Filtre période ────────────────────────────────────────────────────
        make_periode_filter(periode),

        # ── Cartes sources horizontales ───────────────────────────────────────
        make_source_cards(sources),

        # ── Ligne 1 : Radar + Barres empilées ────────────────────────────────
        html.Div([
            _chart_card_wrap(
                "fas fa-share-nodes",
                "SANTÉ & SCORE PAR SOURCE",
                "Radar multi-dimensionnel",
                "Comparaison des sources sur 5 axes : santé, % positifs, frustrations (inversé), score normalisé et volume relatif.",
                dcc.Graph(
                    figure=make_radar_chart(sources, theme),
                    config=graph_cfg,
                    style={"width": "100%"},
                ),
            ),
            _chart_card_wrap(
                "fas fa-chart-bar",
                "VOLUME & SENTIMENT PAR SOURCE",
                "Volume et Sentiment",
                "Décomposition Négatifs / Neutres / Positifs pour chaque source.",
                dcc.Graph(
                    figure=make_volume_bars(sources, theme),
                    config=graph_cfg,
                    style={"width": "100%"},
                ),
            ),
        ], className="row-2cols", style={"marginTop": "20px"}),

        # ── Ligne 2 : Taux négatif + Score moyen ─────────────────────────────
        html.Div([
            _chart_card_wrap(
                "fas fa-face-frown",
                "TAUX NÉGATIF PAR SOURCE",
                "Classement par Taux Négatif",
                "Sources classées par % de commentaires négatifs. Seuil critique : 50%.",
                dcc.Graph(
                    figure=make_taux_negatif_bars(sources, theme),
                    config=graph_cfg,
                    style={"width": "100%"},
                ),
            ),
            _chart_card_wrap(
                "fas fa-chart-line",
                "SCORE MOYEN DE SENTIMENT",
                "Score Sentiment par Source",
                "Score moyen de sentiment : vert = positif, rouge = négatif. TikTok est la seule source positive.",
                dcc.Graph(
                    figure=make_score_bars(sources, theme),
                    config=graph_cfg,
                    style={"width": "100%"},
                ),
            ),
        ], className="row-2cols", style={"marginTop": "14px"}),

        # ── Tableau détaillé ──────────────────────────────────────────────────
        html.Div([
            _chart_card_wrap(
                "fas fa-table-list",
                "TABLEAU DÉTAILLÉ PAR SOURCE",
                "Tableau Détaillé",
                "Toutes les métriques par source : volume, sentiments, score moyen, frustrations et score santé.",
                make_table_sources(sources),
            ),
        ], style={"marginTop": "14px"}),

    ], style={"padding": "0"}, className="dashboard-container")

    return make_page_layout("sources", "Analyse par Source", sub, content, theme, user_data)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. LAYOUT + CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

layout = html.Div(
    id="sources-wrapper",
    **{"data-theme": "light"},
    children=[
        dcc.Store(id="periode-sources-store", data="global", storage_type="session"),
        dcc.Interval(id="refresh-interval-sources", interval=300_000, n_intervals=0),
        html.Div(id="full-sources-layout"),
    ],
)


@callback(
    Output("periode-sources-store", "data"),
    Output("btn-sources-global",    "style"),
    Output("btn-sources-mois",      "style"),
    Output("btn-sources-jour",      "style"),
    Input("btn-sources-global",     "n_clicks"),
    Input("btn-sources-mois",       "n_clicks"),
    Input("btn-sources-jour",       "n_clicks"),
    State("periode-sources-store",  "data"),
    prevent_initial_call=True,
)
def set_sources_periode(n_g, n_m, n_j, current):
    A, I = style_btn_active, style_btn_inactive
    ctx  = dash.callback_context
    if not ctx.triggered:
        s = {"global": [A, I, I], "mois": [I, A, I], "jour": [I, I, A]}.get(current or "global", [A, I, I])
        return current or "global", s[0], s[1], s[2]
    btn = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn == "btn-sources-mois":
        return "mois", I, A, I
    elif btn == "btn-sources-jour":
        return "jour", I, I, A
    return "global", A, I, I


@callback(
    Output("full-sources-layout",     "children"),
    Output("sources-wrapper",         "data-theme"),
    Input("theme-store",              "data"),
    Input("auth-store",               "data"),
    Input("periode-sources-store",    "data"),
    Input("refresh-interval-sources", "n_intervals"),
)
def update_sources_page(theme, auth_data, periode, _):
    theme   = theme   or "light"
    periode = periode or "global"
    user_data = None
    if auth_data and auth_data.get("is_authenticated"):
        user_data = auth_data.get("user", {})
    return render_sources_page(theme, user_data, periode), theme
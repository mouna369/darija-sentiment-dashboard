

"""Page Commentaires — Version Finale Corrigée avec Export CSV et Cache"""

import dash
from dash import html, dcc, callback, Input, Output, State, callback_context as ctx, no_update
import sys, os
import pandas as pd
import hashlib
from datetime import datetime, date
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_sidebar, make_topbar
from database import get_all_comments, get_kpis_globaux, get_collection_info

dash.register_page(__name__, path='/comments', name='Commentaires')

AT_BLUE       = "#003087"
AT_GREEN      = "#009A44"
AT_RED        = "#dc3545"
AT_ORANGE     = "#ff8c00"
AT_LIGHT_BLUE = "#e8f0fb"

SENTIMENT_MAP = {
    "POSITIF": "positif",
    "NEGATIF": "négatif",
    "NEUTRE":  "neutre"
}
SENTIMENT_MAP_REVERSE = {
    "positif": "POSITIF",
    "négatif": "NEGATIF",
    "neutre":  "NEUTRE"
}
# Cache global pour les données
_DATA_CACHE = None
_CACHE_TIMESTAMP = None
_CACHE_TTL = 300  # 5 minutes
def get_cached_data():
    """Récupère les données avec cache pour éviter les rechargements"""
    global _DATA_CACHE, _CACHE_TIMESTAMP
    
    now = datetime.now()
    if _DATA_CACHE is None or _CACHE_TIMESTAMP is None or (now - _CACHE_TIMESTAMP).seconds > _CACHE_TTL:
        print("🔄 Chargement des commentaires depuis MongoDB...")
        _DATA_CACHE = get_all_comments(limit=0)  # limit=0 = pas de limite
        _CACHE_TIMESTAMP = now
        print(f"✅ {len(_DATA_CACHE)} commentaires chargés et mis en cache")
    
    return _DATA_CACHE

def _parse_date_for_filter(date_val):
    """Convertit n'importe quel format de date en string YYYY-MM-DD"""
    from datetime import datetime
    import re
    
    if date_val is None:
        return None
    
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    
    if isinstance(date_val, dict) and "$date" in date_val:
        try:
            date_str = date_val["$date"]
            if "T" in date_str:
                return date_str.split("T")[0]
        except:
            pass
    
    if isinstance(date_val, str):
        # Format "11/12/2025"
        if "/" in date_val:
            parts = date_val.split()[0].split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        # Format ISO
        if re.match(r"\d{4}-\d{2}-\d{2}", date_val):
            return date_val[:10]
    
    return None
def get_cached_data():
    """Récupère les données avec cache"""
    global _DATA_CACHE, _CACHE_TIMESTAMP
    
    now = datetime.now()
    if _DATA_CACHE is None or _CACHE_TIMESTAMP is None or (now - _CACHE_TIMESTAMP).seconds > _CACHE_TTL:
        print("🔄 Chargement des commentaires depuis MongoDB...")
        _DATA_CACHE = get_all_comments(limit=50000)
        _CACHE_TIMESTAMP = now
        print(f"✅ {len(_DATA_CACHE)} commentaires chargés et mis en cache")
    
    return _DATA_CACHE

def invalidate_cache():
    """Invalide le cache pour forcer un rechargement"""
    global _DATA_CACHE, _CACHE_TIMESTAMP
    _DATA_CACHE = None
    _CACHE_TIMESTAMP = None
    print("🔄 Cache invalidé")


# ============================================================
# FONCTION get_comment_date() - CORRIGÉE
# ============================================================
def get_comment_date(c):
    """Extrait la date d'un commentaire au format YYYY-MM-DD"""
    
    # Liste des champs de date à vérifier (du plus fiable au moins fiable)
    date_fields = ["date_clean", "date_annotation", "date_originale", "date", "mois"]
    
    for field in date_fields:
        val = c.get(field)
        if val:
            # Pour le champ mois, format "2025-01"
            if field == "mois" and isinstance(val, str) and len(val) >= 7:
                return f"{val}-01"
            
            parsed = _parse_date_for_filter(val)
            if parsed:
                return parsed
    
    return ""



# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt_date(d):
    if isinstance(d, datetime):
        return d.strftime("%d/%m/%Y"), d.strftime("%H:%M")
    if d is None:
        return "", ""
    
    # Si c'est un dict MongoDB
    if isinstance(d, dict) and "$date" in d:
        try:
            date_str = d["$date"]
            if "T" in date_str:
                return date_str.split("T")[0], date_str.split("T")[1].split(".")[0][:5]
        except:
            pass
    
    s = str(d)[:16]
    if "T" in s:
        parts = s.split("T")
        return parts[0], parts[1]
    if " " in s:
        parts = s.split(" ")
        return parts[0], parts[1] if len(parts) > 1 else ""
    return s[:10], s[11:16] if len(s) > 10 else ""

SENT_CFG = {
    "positif": {"bg":"#e8f8ef","color":"#009A44","dot":"#009A44","label":"Positif","emoji":"😊","border":"#b8e8cc"},
    "négatif": {"bg":"#fdf0f0","color":"#dc3545","dot":"#dc3545","label":"Négatif","emoji":"😡","border":"#f5c0c5"},
    "neutre":  {"bg":"#f5f6f7","color":"#6c757d","dot":"#adb5bd","label":"Neutre","emoji":"😐","border":"#dee2e6"},
}
CHURN_CFG = {
    True:  {"bg":"#fdf0f0","color":"#dc3545","label":"⚠ Élevé","border":"#f5c0c5"},
    False: {"bg":"#e8f8ef","color":"#009A44","label":"✓ Faible","border":"#b8e8cc"},
}
THEME_COLORS = {
    "reseau_technique":         "#003087",
    "installation_equipement":  "#0050b3",
    "facturation_tarifs":       "#ff8c00",
    "service_clientele":        "#009A44",
    "hors_sujet":               "#6c757d",
    "application_digitale":     "#7c3aed",
    "suggestions_ameliorations":"#0891b2",
    "information_generale":     "#059669",
    "experience_positive":      "#16a34a",
}

def badge(text, bg, color, border=None, extra_style=None):
    style = {
        "display":    "inline-flex","alignItems":"center",
        "padding":    "3px 10px","borderRadius":"20px",
        "fontSize":   "11px","fontWeight":"600",
        "background": bg,"color":color,"whiteSpace":"nowrap",
        "border":     f"1px solid {border}" if border else f"1px solid {color}30",
        "lineHeight": "1.4",
        **(extra_style or {})
    }
    return html.Span(text, style=style)

def score_bar(score):
    pct = max(0, min(100, int(abs(score) * 100)))
    col = "#009A44" if score >= 0 else "#dc3545"
    return html.Div([
        html.Div(style={"width":f"{pct}%","height":"100%","background":col,
                        "borderRadius":"3px","transition":"width .4s"})
    ], style={"width":"56px","height":"5px","background":"#e9ecef","borderRadius":"3px",
              "overflow":"hidden","display":"inline-block","verticalAlign":"middle"})

SOURCE_ICONS = {
    "Facebook":    ("fa-brands fa-facebook",  "#1877f2"),
    "Instagram":   ("fa-brands fa-instagram", "#e1306c"),
    "TikTok":      ("fa-brands fa-tiktok",    "#000"),
    "YouTube":     ("fa-brands fa-youtube",   "#ff0000"),
    "LinkedIn":    ("fa-brands fa-linkedin",  "#0a66c2"),
    "X":           ("fa-brands fa-x-twitter", "#14171a"),
    "IdoomMarket": ("fa-solid fa-store",      "#ff8c00"),
}

def source_icon(src):
    icon, color = SOURCE_ICONS.get(src, ("fa-solid fa-comment", "#8899bb"))
    return html.Div([
        html.Div(html.I(className=icon), style={
            "width":"26px","height":"26px","borderRadius":"6px",
            "background":f"{color}18","border":f"1px solid {color}30",
            "display":"flex","alignItems":"center","justifyContent":"center",
            "color":color,"fontSize":"12px","flexShrink":"0",
        }),
        html.Span(src, style={"fontSize":"11px","fontWeight":"600","color":"var(--text-primary)"}),
    ], style={"display":"flex","alignItems":"center","gap":"6px"})

def get_text(c):
    return c.get("commentaire_original") or c.get("commentaire") or c.get("texte") or ""


# ── APPLIQUER LES FILTRES ─────────────────────────────────────────────────
def apply_filters(data, f_sent, f_churn, f_src, f_theme,
                  search, date_debut, date_fin, f_score):
    """Applique tous les filtres sur les données"""
    if not data:
        return []
    
    filtered = data.copy()
    
    # Sentiment
    if f_sent and f_sent != "all":
        db_sent = SENTIMENT_MAP_REVERSE.get(f_sent, f_sent.upper())
        filtered = [d for d in filtered if d.get("sentiment_label") == db_sent]

    # Frustration
    if f_churn and f_churn != "all":
        if f_churn == "high":
            filtered = [d for d in filtered if bool(d.get("frustration_detectee", False)) is True]
        elif f_churn == "low":
            filtered = [d for d in filtered if bool(d.get("frustration_detectee", False)) is False]

    # Source
    if f_src and f_src != "all":
        filtered = [d for d in filtered if d.get("source") == f_src]

    # Thème
    if f_theme and f_theme != "all":
        filtered = [d for d in filtered if d.get("theme_pred") == f_theme]

    # Dates - CORRIGÉ
   # Plage de dates - CORRIGÉ
    if date_debut and date_debut != "":
           try:
             debut_str = str(date_debut)[:10]
             filtered = [d for d in filtered if get_comment_date(d) and get_comment_date(d) >= debut_str]
           except:
                 pass

    if date_fin and date_fin != "":
            try:
              fin_str = str(date_fin)[:10]
              filtered = [d for d in filtered if get_comment_date(d) and get_comment_date(d) <= fin_str]
            except:
                 pass

    # Score
    if f_score and f_score != "all":
        def get_score(c):
            try:
                return float(c.get("sentiment_score") or 0)
            except:
                return 0.0
        if f_score == "very_neg":
            filtered = [d for d in filtered if get_score(d) < -0.6]
        elif f_score == "neg":
            filtered = [d for d in filtered if -0.6 <= get_score(d) < 0]
        elif f_score == "pos":
            filtered = [d for d in filtered if 0 <= get_score(d) <= 0.6]
        elif f_score == "very_pos":
            filtered = [d for d in filtered if get_score(d) > 0.6]

    # Recherche texte
    if search and search.strip():
        s = search.lower()
        filtered = [d for d in filtered if s in get_text(d).lower()]

    return filtered


# ── TABLE ROW ─────────────────────────────────────────────────────────────────
def make_row(c, idx):
    sent_label = c.get("sentiment_label", "NEUTRE")
    sent = SENTIMENT_MAP.get(sent_label, "neutre")
    sc   = SENT_CFG.get(sent, SENT_CFG["neutre"])
    frus = bool(c.get("frustration_detectee", False))
    cc   = CHURN_CFG.get(frus, CHURN_CFG[False])
    score = c.get("sentiment_score") or 0
    theme = c.get("theme_pred") or ""
    tcol  = THEME_COLORS.get(theme, AT_BLUE)
    txt_full = get_text(c)
    txt      = txt_full[:110]
    mod = bool(c.get("a_repondu", False))
    src = c.get("source") or "?"
    langue_val = c.get("langue_detectee") or ""
    lng = langue_val.replace("_", " ").title()[:15] if langue_val else "—"
    date_str, time_str = fmt_date(
        c.get("date_originale") or c.get("date_clean") or
        c.get("date_annotation") or c.get("date") or ""
    )
    row_bg = "#fafbfd" if idx % 2 == 0 else "var(--bg-card)"

    return html.Tr([
        html.Td(html.Div(style={"width":"15px","height":"15px","border":"1.5px solid #ced4da",
                                "borderRadius":"4px","cursor":"pointer","background":"white"}),
                style={"padding":"0 8px 0 16px","width":"40px","verticalAlign":"middle"}),

        html.Td(html.Div([
            html.Div(date_str, style={"fontSize":"12px","fontWeight":"600","color":"var(--text-primary)"}),
            html.Div(time_str, style={"fontSize":"10px","color":"#8fa3c0","marginTop":"1px"}),
        ]), style={"padding":"10px 10px","whiteSpace":"nowrap","width":"88px","verticalAlign":"middle"}),

        html.Td(html.Div([
            html.Div(txt + ("…" if len(txt_full) > 110 else ""), style={
                "fontSize":"12.5px","color":"var(--text-primary)","lineHeight":"1.45",
                "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap","maxWidth":"300px",
            }),
            html.Div([
                html.I(className="fas fa-exclamation-triangle", style={"fontSize":"9px","marginRight":"3px"}),
                "Frustration détectée",
            ], style={"fontSize":"10px","color":AT_ORANGE,"fontWeight":"600","marginTop":"3px",
                      "display":"flex","alignItems":"center"}) if frus else html.Div(),
        ]), style={"padding":"10px 10px","maxWidth":"320px","verticalAlign":"middle"}),

        html.Td(badge(f"{sc['emoji']} {sc['label']}", sc["bg"], sc["color"], sc["border"]),
                style={"padding":"10px","whiteSpace":"nowrap","verticalAlign":"middle"}),

        html.Td(html.Div([
            score_bar(score),
            html.Span(f"{score:+.2f}", style={"fontSize":"11px","fontWeight":"700",
                      "color":AT_GREEN if score>=0 else AT_RED,"marginLeft":"6px",
                      "fontFamily":"'Courier New',monospace"}),
        ], style={"display":"flex","alignItems":"center"}),
        style={"padding":"10px","verticalAlign":"middle","whiteSpace":"nowrap"}),

        html.Td(badge(theme.replace("_"," ").title()[:22] if theme else "N/A",
                      f"{tcol}12", tcol, f"{tcol}35"),
                style={"padding":"10px","whiteSpace":"nowrap","verticalAlign":"middle"}),

        html.Td(source_icon(src),
                style={"padding":"10px","whiteSpace":"nowrap","verticalAlign":"middle"}),

        html.Td(html.Span(lng, style={"fontSize":"11px","color":"var(--text-secondary)","fontWeight":"500"}),
                style={"padding":"10px","verticalAlign":"middle"}),

        html.Td(badge(cc["label"], cc["bg"], cc["color"], cc["border"]),
                style={"padding":"10px","whiteSpace":"nowrap","verticalAlign":"middle"}),

        html.Td(html.Div([
            html.I(className="fas fa-check-circle" if mod else "fas fa-times-circle",
                   style={"marginRight":"4px","fontSize":"11px"}),
            "Oui" if mod else "Non",
        ], style={"display":"flex","alignItems":"center","fontSize":"11px","fontWeight":"600",
                  "color":AT_GREEN if mod else AT_RED}),
        style={"padding":"10px","whiteSpace":"nowrap","verticalAlign":"middle"}),

        html.Td(html.Button([
            html.I(className="fas fa-eye", style={"marginRight":"5px","fontSize":"10px"}), "Voir",
        ], id={"type":"view-btn","index":str(c.get("_id", idx))}, n_clicks=0, style={
            "padding":"5px 12px","background":AT_LIGHT_BLUE,"color":AT_BLUE,
            "border":f"1.5px solid {AT_BLUE}30","borderRadius":"7px","fontSize":"11px",
            "cursor":"pointer","fontFamily":"'Poppins',sans-serif","fontWeight":"600",
            "display":"inline-flex","alignItems":"center","transition":"all .15s",
        }), style={"padding":"10px","whiteSpace":"nowrap","verticalAlign":"middle"}),

    ], style={"borderBottom":"1px solid #eef0f5","background":row_bg,"transition":"background .12s"},
    className="comment-row")


# ── PAGINATION ────────────────────────────────────────────────────────────────
def make_pagination(page, total_pages, total, per_page):
    start = (page - 1) * per_page + 1
    end   = min(page * per_page, total)

    def page_btn(p):
        active = p == page
        return html.Button(str(p), id={"type":"page-btn","index":p}, n_clicks=0, style={
            "width":"32px","height":"32px",
            "border":f"1.5px solid {AT_BLUE if active else '#dee2e6'}",
            "borderRadius":"7px","background":AT_BLUE if active else "white",
            "color":"white" if active else "#495057","fontSize":"12px",
            "fontWeight":"700" if active else "500","cursor":"pointer",
            "fontFamily":"'Poppins',sans-serif","transition":"all .15s",
        })

    def nav_btn(label, disabled, btn_id):
        return html.Button(label, id=btn_id, n_clicks=0, style={
            "width":"32px","height":"32px","border":"1.5px solid #dee2e6","borderRadius":"7px",
            "background":"#f8f9fa" if disabled else "white",
            "color":"#adb5bd" if disabled else AT_BLUE,
            "fontSize":"14px","cursor":"not-allowed" if disabled else "pointer",
            "fontWeight":"700","transition":"all .15s",
        })

    pages_to_show = []
    for p in range(1, total_pages + 1):
        if p == 1 or p == total_pages or abs(p - page) <= 1:
            pages_to_show.append(p)
        elif pages_to_show and pages_to_show[-1] != "...":
            pages_to_show.append("...")

    return html.Div([
        html.Span(f"Affichage {start:,}–{end:,} sur {total:,} résultats",
                  style={"fontSize":"12px","color":"#6c757d","marginRight":"auto","fontWeight":"500"}),
        nav_btn("‹", page == 1, "prev-page"),
        *[page_btn(p) if p != "..."
          else html.Span("…", style={"padding":"0 4px","color":"#adb5bd","fontSize":"13px","lineHeight":"32px"})
          for p in pages_to_show],
        nav_btn("›", page == total_pages, "next-page"),
        html.Div([
            html.Span("Par page:", style={"fontSize":"11px","color":"#6c757d",
                                          "marginLeft":"16px","marginRight":"6px","fontWeight":"500"}),
            dcc.Dropdown(id="per-page-select",
                options=[{"label":str(n),"value":n} for n in [25,50,100,200]],
                value=per_page, clearable=False,
                style={"width":"70px","fontSize":"12px","display":"inline-block"}),
        ], style={"display":"flex","alignItems":"center"}),
    ], style={"display":"flex","alignItems":"center","gap":"5px","padding":"12px 20px",
              "borderTop":"1px solid #eef0f5","background":"#fafbfd","borderRadius":"0 0 12px 12px"})


# ── STATS BAR ───────────────────────────────────────────────────────────────
def stats_bar(kpis, active_filter="all"):
    items = [
        ("Tous",        kpis.get("total",      0), AT_BLUE,   "total",       "fa-comments",   "all"),
        ("Négatifs",    kpis.get("negatifs",   0), AT_RED,    "negatifs",    "fa-face-angry", "négatif"),
        ("Positifs",    kpis.get("positifs",   0), AT_GREEN,  "positifs",    "fa-face-smile", "positif"),
        ("Neutres",     kpis.get("neutres",    0), "#6c757d", "neutres",     "fa-face-meh",   "neutre"),
        ("Frustration", kpis.get("frustration",0), AT_ORANGE, "frustration", "fa-triangle-exclamation","frustration"),
    ]

    tabs = []
    for label, count, color, key, icon, fval in items:
        is_active = (active_filter == fval)

        if is_active:
            tab_style = {
                "padding":         "10px 18px",
                "cursor":          "pointer",
                "borderRadius":    "10px 10px 0 0",
                "background":      f"{color}14",
                "borderTop":       f"2px solid {color}",
                "borderLeft":      f"1px solid {color}30",
                "borderRight":     f"1px solid {color}30",
                "borderBottom":    f"2px solid {f'{color}14'}",
                "transition":      "all .2s",
                "position":        "relative",
                "marginBottom":    "-1px",
                "zIndex":          2,
            }
            label_color  = color
            count_bg     = f"{color}22"
            count_color  = color
        else:
            tab_style = {
                "padding":       "10px 18px",
                "cursor":        "pointer",
                "borderRadius":  "10px 10px 0 0",
                "background":    "#f5f6f8",
                "border":        "1px solid #e5e8ef",
                "borderBottom":  "1px solid #eef0f5",
                "transition":    "all .2s",
                "position":      "relative",
                "marginBottom":  "-1px",
                "zIndex":        1,
            }
            label_color  = "#8a9ab5"
            count_bg     = "#e8eaf0"
            count_color  = "#8a9ab5"

        tabs.append(html.Div([
            html.Div([
                html.I(className=f"fas {icon}",
                       style={"marginRight":"6px","fontSize":"12px","color":label_color}),
                html.Span(label, style={"fontWeight":"600","fontSize":"13px","color":label_color}),
                html.Span(f"{count:,}", style={
                    "background":   count_bg,
                    "color":        count_color,
                    "padding":      "1px 8px",
                    "borderRadius": "12px",
                    "fontSize":     "11px",
                    "fontWeight":   "700",
                    "marginLeft":   "6px",
                    "border":       f"1px solid {color}25" if is_active else "1px solid #dde0e8",
                }),
            ], style={"display":"flex","alignItems":"center"}),
        ], id=f"stat-{key}", style=tab_style, n_clicks=0))

    return html.Div(tabs, style={
        "display":      "flex",
        "gap":          "4px",
        "borderBottom": "1px solid #eef0f5",
        "marginBottom": "0",
        "paddingBottom": "0",
        "overflowX":    "auto",
        "padding":      "12px 16px 0 16px",
    })


# ── TABLE BLOCK ───────────────────────────────────────────────────────────────
def make_table_block(comments, page=1, per_page=50, active_filter="all"):
    if not comments:
        return html.Div([
            html.I(className="fas fa-inbox", style={"fontSize":"40px","color":"#ced4da"}),
            html.Div("Aucun commentaire trouvé",
                     style={"fontSize":"14px","color":"#6c757d","marginTop":"12px","fontWeight":"500"}),
            html.Div("Essayez de modifier vos filtres",
                     style={"fontSize":"12px","color":"#adb5bd","marginTop":"4px"}),
        ], style={"textAlign":"center","padding":"60px 20px",
                  "display":"flex","flexDirection":"column","alignItems":"center"})

    start      = (page - 1) * per_page
    end        = start + per_page
    page_data  = comments[start:end]
    total_pages = max(1, (len(comments) + per_page - 1) // per_page)

    def th(label, width=None):
        return html.Th(label, style={
            "padding":       "11px 10px" if label else "11px 16px",
            "fontSize":      "11px","fontWeight":"700","color":"#6c757d",
            "textAlign":     "left","background":"#f8f9fa","letterSpacing":"0.5px",
            "textTransform": "uppercase","whiteSpace":"nowrap",
            "borderBottom": "2px solid #eef0f5",
            "position": "sticky","top": 0,"zIndex": 10,
            **({"width":width} if width else {})
        })

    return html.Div([
        html.Div(style={
            "overflowX":"auto",
            "overflowY":"auto",
            "maxHeight":"calc(100vh - 350px)",
            "borderRadius":"8px",
        }, children=[
            html.Table([
                html.Thead(html.Tr([
                    html.Th(html.Div(style={"width":"15px","height":"15px","border":"1.5px solid #ced4da",
                                            "borderRadius":"4px","cursor":"pointer","background":"white"}),
                            style={"padding":"11px 8px 11px 16px","background":"#f8f9fa",
                                   "width":"40px","borderBottom":"2px solid #eef0f5",
                                   "position":"sticky","top":0,"zIndex":10}),
                    th("Date","88px"), th("Commentaire"), th("Sentiment","110px"),
                    th("Score","100px"), th("Thème","160px"), th("Source","120px"),
                    th("Langue","90px"), th("Frustration","100px"),
                    th("Modéré","80px"), th("Actions","90px"),
                ])),
                html.Tbody([make_row(c, i) for i, c in enumerate(page_data)]),
            ], style={"width":"100%","borderCollapse":"collapse","minWidth":"1100px"}),
        ]),
        make_pagination(page, total_pages, len(comments), per_page),
    ])


# ── FILTER BAR ────────────────────────────────────────────────────────────────
DD_STYLE = {
    "fontSize":"12px","borderRadius":"8px",
    "border":"1px solid #e2e8f0","background":"white","minWidth":"130px",
    "boxShadow":"none",
}

def filter_bar(comments):
    sources = sorted({c.get("source","") for c in comments if c.get("source")})
    themes = sorted({c.get("theme_pred","") for c in comments if c.get("theme_pred")})

    def opts(items, all_lbl="Tous"):
        return [{"label":all_lbl,"value":"all"}] + [
            {"label":i.replace("_"," ").title(),"value":i} for i in items if i
        ]

    return html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-search",
                       style={"color":"#94a3b8","fontSize":"13px","flexShrink":"0"}),
                dcc.Input(id="search-comment", placeholder="Rechercher un commentaire...",
                          type="text", debounce=True,
                          style={"border":"none","background":"transparent","color":"#1e293b",
                                 "outline":"none","fontFamily":"'Poppins',sans-serif",
                                 "fontSize":"12.5px","width":"650px"}),
            ], style={"display":"flex","alignItems":"center","gap":"10px","padding":"8px 14px",
                      "border":"1px solid #e2e8f0","borderRadius":"10px","background":"#f8fafc",
                      "transition":"all 0.2s"}),

            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line",
                           style={"color":"#64748b","fontSize":"11px","marginRight":"5px"}),
                    html.Span("Score", style={"fontSize":"10px","fontWeight":"600","color":"#475569",
                                              "letterSpacing":"0.3px","textTransform":"uppercase"}),
                ], style={"display":"flex","alignItems":"center","marginBottom":"4px"}),
                dcc.Dropdown(id="filter-score", options=[
                    {"label":"Tous",               "value":"all"},
                    {"label":"🔴 Très négatif",    "value":"very_neg"},
                    {"label":"🟠 Négatif",         "value":"neg"},
                    {"label":"🟢 Positif",         "value":"pos"},
                    {"label":"💚 Très positif",    "value":"very_pos"},
                ], value="all", clearable=False, style={**DD_STYLE,"minWidth":"125px"}),
            ]),

            html.Div([
                html.Div([
                    html.I(className="fas fa-share-alt",
                           style={"color":"#64748b","fontSize":"11px","marginRight":"5px"}),
                    html.Span("Source", style={"fontSize":"10px","fontWeight":"600","color":"#475569",
                                               "letterSpacing":"0.3px","textTransform":"uppercase"}),
                ], style={"display":"flex","alignItems":"center","marginBottom":"4px"}),
                dcc.Dropdown(id="filter-source", options=opts(sources,"Toutes"), value="all",
                             clearable=False, style=DD_STYLE),
            ]),

            html.Div([
                html.Div([
                    html.I(className="fas fa-tag",
                           style={"color":"#64748b","fontSize":"11px","marginRight":"5px"}),
                    html.Span("Thème", style={"fontSize":"10px","fontWeight":"600","color":"#475569",
                                              "letterSpacing":"0.3px","textTransform":"uppercase"}),
                ], style={"display":"flex","alignItems":"center","marginBottom":"4px"}),
                dcc.Dropdown(id="filter-theme", options=opts(themes,"Tous"), value="all",
                             clearable=False, style=DD_STYLE),
            ]),

            html.Div([
                html.Div([
                    html.I(className="fas fa-calendar-alt",
                           style={"color":"#64748b","fontSize":"11px","marginRight":"5px"}),
                    html.Span("Dates", style={"fontSize":"10px","fontWeight":"600","color":"#475569",
                                              "letterSpacing":"0.3px","textTransform":"uppercase"}),
                ], style={"display":"flex","alignItems":"center","marginBottom":"4px"}),
                dcc.DatePickerRange(
                    id="date-range",
                    start_date="",
                    end_date="",
                    display_format="DD/MM/YYYY",
                    start_date_placeholder_text="Début",
                    end_date_placeholder_text="Fin",
                    style={"border":"1px solid #e2e8f0","borderRadius":"8px","padding":"4px 8px",
                           "background":"#f8fafc"}
                ),
            ]),

        ], style={"display":"flex","alignItems":"flex-end","gap":"16px","flexWrap":"wrap"}),

    ], style={"background":"white","borderRadius":"16px","padding":"16px 20px",
              "border":"1px solid #eef2f8","marginBottom":"16px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)"})


# ── MODALE ────────────────────────────────────────────────────────────────────
def create_modal():
    return html.Div(id="comment-modal", style={
        "display":"none","position":"fixed","top":0,"left":0,
        "width":"100%","height":"100%","backgroundColor":"rgba(0,10,30,0.55)",
        "zIndex":99999,"justifyContent":"center","alignItems":"center",
        "backdropFilter":"blur(3px)",
    }, children=[html.Div(style={
        "backgroundColor":"white","borderRadius":"16px","width":"640px",
        "maxWidth":"92vw","maxHeight":"85vh","overflow":"hidden",
        "boxShadow":"0 24px 64px rgba(0,48,135,0.18), 0 4px 16px rgba(0,0,0,0.1)",
        "display":"flex","flexDirection":"column",
    }, children=[
        html.Div(style={
            "display":"flex","justifyContent":"space-between","alignItems":"center",
            "padding":"16px 22px","background":f"linear-gradient(135deg,{AT_BLUE} 0%,#0050b3 100%)",
            "borderRadius":"16px 16px 0 0","flexShrink":0,
        }, children=[
            html.Div([
                html.Div(style={"width":"32px","height":"32px","background":"rgba(255,255,255,0.15)",
                                "borderRadius":"8px","display":"flex","alignItems":"center",
                                "justifyContent":"center","marginRight":"10px"},
                         children=html.I(className="fas fa-comment-dots",
                                         style={"color":"white","fontSize":"14px"})),
                html.Div([
                    html.Div("Détail du commentaire",
                             style={"color":"white","fontSize":"15px","fontWeight":"700",
                                    "fontFamily":"'Poppins',sans-serif"}),
                    html.Div("Informations complètes",
                             style={"color":"rgba(255,255,255,0.65)","fontSize":"11px","marginTop":"1px"}),
                ]),
            ], style={"display":"flex","alignItems":"center"}),
            html.Button("✕", id="close-modal", n_clicks=0, style={
                "background":"rgba(255,255,255,0.15)","border":"1.5px solid rgba(255,255,255,0.3)",
                "color":"white","fontSize":"15px","cursor":"pointer","fontWeight":"bold",
                "width":"32px","height":"32px","borderRadius":"8px","lineHeight":"1",
                "display":"flex","alignItems":"center","justifyContent":"center",
            }),
        ]),
        html.Div(id="modal-content", style={"padding":"22px 24px","overflowY":"auto",
                                            "flex":1,"background":"white"}),
    ])])


def detail_card(icon, label, value):
    return html.Div([
        html.Div([
            html.I(className=f"fas {icon}",
                   style={"color":AT_BLUE,"fontSize":"12px","marginRight":"6px"}),
            html.Span(label, style={"fontSize":"10px","fontWeight":"700","color":"#6c757d",
                                    "textTransform":"uppercase","letterSpacing":"0.5px"}),
        ], style={"display":"flex","alignItems":"center","marginBottom":"6px"}),
        html.Div(value, style={"fontSize":"13px","fontWeight":"600","color":"#212529"}),
    ], style={"background":"#f8f9fa","borderRadius":"10px","padding":"12px 14px",
              "border":"1px solid #eef0f5","flex":"1","minWidth":"140px"})


# ── DOWNLOAD COMPONENT ────────────────────────────────────────────────────────
def create_download_component():
    return html.Div([
        dcc.Download(id="download-csv"),
    ], style={"display": "none"})


# ── BUILD PAGE ────────────────────────────────────────────────────────────────
def build_layout(theme="light", user_data=None):
    all_data = get_cached_data()
    db_info  = get_collection_info()
    if not isinstance(db_info, dict):
        db_info = {"count":len(all_data),"connected":True,
                   "db":"telecom_algerie","collection":"commentaires_predictions_final"}

    n    = len(all_data)
    neg  = sum(1 for d in all_data if d.get("sentiment_label") == "NEGATIF")
    pos  = sum(1 for d in all_data if d.get("sentiment_label") == "POSITIF")
    neu  = sum(1 for d in all_data if d.get("sentiment_label") == "NEUTRE")
    frus = sum(1 for d in all_data if bool(d.get("frustration_detectee", False)) is True)
    initial_kpis = {"total":n,"negatifs":neg,"positifs":pos,"neutres":neu,"frustration":frus}

    return html.Div([
        make_sidebar("comments", user_data),
        html.Div([
            make_topbar("Commentaires Clients",
                        f"Base MongoDB · {db_info.get('count',0):,} documents analysés", theme, user_data),
            html.Div([

                html.Div([
                    html.Div(style={"flex":"1"}),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-file-export",
                                   style={"marginRight":"7px","fontSize":"12px"}),
                            "Exporter CSV",
                        ], id="export-btn", n_clicks=0, style={
                            "padding":"9px 18px","background":"white","color":AT_BLUE,
                            "border":f"1.5px solid {AT_BLUE}35","borderRadius":"9px",
                            "fontSize":"13px","fontWeight":"600","cursor":"pointer",
                            "display":"inline-flex","alignItems":"center",
                            "fontFamily":"'Poppins',sans-serif","marginRight":"10px",
                        }),
                        html.Button([
                            html.I(className="fas fa-rotate-left",
                                   style={"marginRight":"7px","fontSize":"12px"}),
                            "Réinitialiser",
                        ], id="reset-filters", n_clicks=0, style={
                            "padding":"9px 18px","background":AT_BLUE,"color":"white",
                            "border":"none","borderRadius":"9px","fontSize":"13px",
                            "fontWeight":"600","cursor":"pointer","display":"inline-flex",
                            "alignItems":"center","fontFamily":"'Poppins',sans-serif",
                        }),
                    ], style={"display":"flex","gap":"10px"}),
                ], style={"display":"flex","justifyContent":"flex-end",
                          "alignItems":"center","marginBottom":"18px"}),

                create_modal(),
                create_download_component(),
                filter_bar(all_data),

                html.Div(id="stats-bar-container", children=stats_bar(initial_kpis, "all"), style={
                    "background":"white","borderRadius":"12px 12px 0 0",
                    "border":"1px solid #eef0f5","borderBottom":"none",
                    "overflow":"hidden"
                }),

                html.Div([
                    html.Div(id="comments-table-container",
                             children=make_table_block(all_data, page=1, per_page=50,
                                                       active_filter="all")),
                ], style={"background":"white","borderRadius":"0 0 12px 12px",
                          "border":"1px solid #eef0f5","borderTop":"none",
                          "overflow":"hidden","boxShadow":"0 1px 6px rgba(0,48,135,0.07)"}),

                html.Div([
                    html.Span(id="comments-count",
                              style={"fontSize":"11.5px","color":"#6c757d","fontWeight":"500"}),
                ], style={"marginTop":"8px","paddingLeft":"4px"}),

                dcc.Store(id="current-page", data=1),
                dcc.Store(id="per-page-val", data=50),
                dcc.Store(id="active-stat-filter", data="all"),
                dcc.Store(id="page-theme", data=theme),
                dcc.Store(id="filter-sentiment-store", data="all"),
                dcc.Store(id="filter-churn-store", data="all"),
                dcc.Store(id="filtered-data-store", data=all_data),

            ], className="page-content"),
        ], className="main-content"),
    ], id="app-wrapper", **{"data-theme": theme})


layout = html.Div([html.Div(id="comments-root")])


# ── CALLBACK PRINCIPAL ────────────────────────────────────────────────────────
@callback(
    Output('comments-root', 'children'),
    Input('theme-store', 'data'),
    Input('auth-store', 'data')
)
def render_page(theme, auth_data):
    theme = theme or "light"
    
    user_data = None
    if auth_data and auth_data.get('is_authenticated'):
        user_data = auth_data.get('user', {})
    
    return build_layout(theme, user_data)


# ── RESET ─────────────────────────────────────────────────────────────────────
@callback(
    Output("filter-sentiment-store", "data"),
    Output("filter-churn-store",     "data"),
    Output("filter-source",          "value"),
    Output("filter-theme",           "value"),
    Output("search-comment",         "value"),
    Output("date-range",             "start_date"),
    Output("date-range",             "end_date"),
    Output("filter-score",           "value"),
    Output("current-page",           "data"),
    Output("active-stat-filter",     "data"),
    Input("reset-filters", "n_clicks"),
    prevent_initial_call=True,
)
def reset_all(_):
    return "all", "all", "all", "all", "", None, None, "all", 1, "all"


# ── STATS CLICK ──────────────────────────────────────────────────────────────
@callback(
    Output("filter-sentiment-store", "data", allow_duplicate=True),
    Output("filter-churn-store",     "data", allow_duplicate=True),
    Output("current-page",           "data", allow_duplicate=True),
    Output("active-stat-filter",     "data", allow_duplicate=True),
    Input("stat-total",       "n_clicks"),
    Input("stat-negatifs",    "n_clicks"),
    Input("stat-positifs",    "n_clicks"),
    Input("stat-neutres",     "n_clicks"),
    Input("stat-frustration", "n_clicks"),
    prevent_initial_call=True,
)
def on_stat_click(total, neg, pos, neu, frust):
    mapping = {
        "stat-total":       ("all",     "all",     "all"),
        "stat-negatifs":    ("négatif", "all",     "négatif"),
        "stat-positifs":    ("positif", "all",     "positif"),
        "stat-neutres":     ("neutre",  "all",     "neutre"),
        "stat-frustration": ("all",     "high",    "frustration"),
    }
    sent_val, churn_val, filt_val = mapping.get(ctx.triggered_id, ("all","all","all"))
    return sent_val, churn_val, 1, filt_val


# ── PAGINATION ────────────────────────────────────────────────────────────────
@callback(
    Output("current-page","data",allow_duplicate=True),
    Input("prev-page","n_clicks"),
    Input("next-page","n_clicks"),
    Input({"type":"page-btn","index":dash.ALL},"n_clicks"),
    State("current-page","data"),
    prevent_initial_call=True,
)
def paginate(prev, nxt, page_btns, cur):
    t = ctx.triggered_id
    if t == "prev-page":   return max(1, cur-1)
    if t == "next-page":   return cur+1
    if isinstance(t, dict) and t.get("type") == "page-btn":
        return int(t["index"])
    return cur


@callback(
    Output("per-page-val","data"),
    Output("current-page","data",allow_duplicate=True),
    Input("per-page-select","value"),
    prevent_initial_call=True,
)
def change_per_page(val):
    return val, 1


# ── UPDATE TABLE ──────────────────────────────────────────────────────────────
@callback(
    Output("comments-table-container","children"),
    Output("comments-count","children"),
    Output("stats-bar-container","children"),
    Output("filtered-data-store","data"),
    Input("filter-sentiment-store","data"),
    Input("filter-churn-store","data"),
    Input("filter-source",     "value"),
    Input("filter-theme",      "value"),
    Input("search-comment",    "value"),
    Input("date-range",        "start_date"),
    Input("date-range",        "end_date"),
    Input("filter-score",      "value"),
    Input("current-page",      "data"),
    Input("per-page-val",      "data"),
    Input("active-stat-filter","data"),
)
def update_table(f_sent, f_churn, f_src, f_theme, search,
                 date_debut, date_fin, f_score,
                 page, per_page, active_filter):
    
    all_data = get_cached_data()
    total_all = len(all_data)
    
    data_for_stats = apply_filters(all_data, "all", "all", f_src, f_theme,
                                   search, date_debut, date_fin, f_score)
    n_s   = len(data_for_stats)
    neg_s = sum(1 for d in data_for_stats if d.get("sentiment_label") == "NEGATIF")
    pos_s = sum(1 for d in data_for_stats if d.get("sentiment_label") == "POSITIF")
    neu_s = sum(1 for d in data_for_stats if d.get("sentiment_label") == "NEUTRE")
    fru_s = sum(1 for d in data_for_stats if bool(d.get("frustration_detectee",False)) is True)
    kpis  = {"total":n_s,"negatifs":neg_s,"positifs":pos_s,"neutres":neu_s,"frustration":fru_s}
    new_stats_bar = stats_bar(kpis, active_filter or "all")

    filtered_data = apply_filters(all_data, f_sent, f_churn, f_src, f_theme,
                                  search, date_debut, date_fin, f_score)
    
    pp = per_page or 50
    n  = len(filtered_data)
    count_text = (
        f"{n:,} commentaire{'s' if n!=1 else ''} affiché{'s' if n!=1 else ''}"
        f" sur {total_all:,} au total"
    )
    table = make_table_block(filtered_data, page=page or 1, per_page=pp,
                             active_filter=active_filter or "all")
    
    serializable_data = []
    for d in filtered_data:
        serializable_data.append({
            "_id": str(d.get("_id", "")),
            "commentaire_original": d.get("commentaire_original", ""),
            "sentiment_label": d.get("sentiment_label", ""),
            "sentiment_score": d.get("sentiment_score", 0),
            "theme_pred": d.get("theme_pred", ""),
            "source": d.get("source", ""),
            "langue_detectee": d.get("langue_detectee", ""),
            "frustration_detectee": d.get("frustration_detectee", False),
            "a_repondu": d.get("a_repondu", False),
            "sentiment_confiance": d.get("sentiment_confiance", 0),
            "wilaya": d.get("wilaya", ""),
            "service": d.get("service", ""),
            "date_originale": d.get("date_originale", ""),
            "date_clean": d.get("date_clean", ""),
            "date_annotation": d.get("date_annotation", ""),
            "mois": d.get("mois", ""),
        })
    
    return table, count_text, new_stats_bar, serializable_data


# ── EXPORT CSV ────────────────────────────────────────────────────────────────
@callback(
    Output("download-csv", "data"),
    Input("export-btn", "n_clicks"),
    State("filtered-data-store", "data"),
    prevent_initial_call=True,
)
def export_to_csv_callback(n_clicks, filtered_data):
    if n_clicks is None or n_clicks == 0 or not filtered_data:
        return no_update
    
    export_data = []
    for d in filtered_data:
        date_str, time_str = fmt_date(
            d.get("date_originale") or d.get("date_clean") or
            d.get("date_annotation") or ""
        )
        
        export_data.append({
            "ID": d.get("_id", ""),
            "Date": date_str,
            "Heure": time_str,
            "Commentaire": d.get("commentaire_original", ""),
            "Sentiment": SENTIMENT_MAP.get(d.get("sentiment_label", "NEUTRE"), "neutre"),
            "Score": d.get("sentiment_score", 0),
            "Thème": d.get("theme_pred", ""),
            "Source": d.get("source", ""),
            "Langue": d.get("langue_detectee", ""),
            "Frustration": "Oui" if d.get("frustration_detectee", False) else "Non",
            "Modérateur répondu": "Oui" if d.get("a_repondu", False) else "Non",
            "Confiance": d.get("sentiment_confiance", 0),
            "Wilaya": d.get("wilaya", ""),
            "Service": d.get("service", ""),
        })
    
    df = pd.DataFrame(export_data)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"commentaires_export_{now}.csv"
    
    return dcc.send_data_frame(
        df.to_csv,
        filename=filename,
        index=False,
        encoding='utf-8-sig'
    )


# ── MODALE : OUVRIR (CORRIGÉ - ne s'ouvre plus automatiquement) ──────────────
@callback(
    Output("comment-modal","style", allow_duplicate=True),
    Output("modal-content","children", allow_duplicate=True),
    Input({"type":"view-btn","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def show_comment_details(view_clicks):
    triggered = ctx.triggered_id
    
    # Vérifier qu'un bouton a vraiment été cliqué et que ce n'est pas un clic vide
    if not triggered or triggered == "":
        return no_update, no_update
    
    # Vérifier le format du triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    
    if triggered.get("type") != "view-btn":
        return no_update, no_update
    
    # Vérifier qu'il y a bien un index
    comment_id = triggered.get("index")
    if not comment_id:
        return no_update, no_update
    
    # Vérifier que view_clicks est une liste et qu'au moins un bouton a été cliqué
    if not view_clicks or not isinstance(view_clicks, list):
        return no_update, no_update
    
    # Trouver quel bouton a été cliqué
    button_clicked = None
    for i, clicks in enumerate(view_clicks):
        if clicks and clicks > 0:
            button_clicked = i
            break
    
    if button_clicked is None:
        return no_update, no_update
    
    # Récupérer le commentaire
    all_comments = get_cached_data()
    comment = None
    for c in all_comments:
        if str(c.get("_id")) == str(comment_id):
            comment = c
            break
    
    if not comment:
        modal_style = {
            "display":"flex","position":"fixed","top":0,"left":0,
            "width":"100%","height":"100%","backgroundColor":"rgba(0,10,30,0.55)",
            "zIndex":99999,"justifyContent":"center","alignItems":"center",
            "backdropFilter":"blur(3px)",
        }
        return modal_style, html.Div("Commentaire non trouvé", style={"color":AT_RED})

    # Construire le contenu de la modale (identique à avant)
    sent_label = comment.get("sentiment_label","NEUTRE")
    sent = SENTIMENT_MAP.get(sent_label,"neutre")
    sc = SENT_CFG.get(sent, SENT_CFG["neutre"])
    score = comment.get("sentiment_score") or 0
    theme = comment.get("theme_pred") or ""
    frus = bool(comment.get("frustration_detectee",False))
    mod = bool(comment.get("a_repondu",False))
    langue_val = comment.get("langue_detectee") or ""
    lng = langue_val.replace("_"," ").title() if langue_val else "Non détectée"
    src = comment.get("source") or "?"
    date_s, time_s = fmt_date(
        comment.get("date_originale") or comment.get("date_clean") or
        comment.get("date_annotation") or comment.get("date") or ""
    )

    content = html.Div([
        html.Div([
            detail_card("fa-calendar",    "Date",   f"{date_s} {time_s}".strip() or "—"),
            detail_card("fa-share-nodes", "Source", src),
            detail_card("fa-language",    "Langue", lng),
            detail_card("fa-tag",         "Thème",  theme.replace("_"," ").title() if theme else "N/A"),
        ], style={"display":"flex","gap":"10px","flexWrap":"wrap","marginBottom":"16px"}),

        html.Div([
            html.Div([
                html.Div([html.I(className="fas fa-face-smile",
                                 style={"color":"#6c757d","marginRight":"6px","fontSize":"11px"}),
                          html.Span("Sentiment", style={"fontSize":"10px","fontWeight":"700",
                                                        "color":"#6c757d","textTransform":"uppercase",
                                                        "letterSpacing":"0.5px"})],
                         style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
                badge(f"{sc['emoji']} {sc['label']}", sc["bg"], sc["color"], sc["border"],
                      {"fontSize":"13px","padding":"5px 14px"}),
            ], style={"background":"#f8f9fa","borderRadius":"10px","padding":"14px",
                      "border":"1px solid #eef0f5","flex":"1"}),

            html.Div([
                html.Div([html.I(className="fas fa-chart-bar",
                                 style={"color":"#6c757d","marginRight":"6px","fontSize":"11px"}),
                          html.Span("Score", style={"fontSize":"10px","fontWeight":"700",
                                                    "color":"#6c757d","textTransform":"uppercase",
                                                    "letterSpacing":"0.5px"})],
                         style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
                html.Div([
                    score_bar(score),
                    html.Span(f"{score:+.3f}", style={"marginLeft":"10px","fontWeight":"700",
                                                      "fontSize":"14px",
                                                      "color":AT_GREEN if score>=0 else AT_RED,
                                                      "fontFamily":"'Courier New',monospace"}),
                ], style={"display":"flex","alignItems":"center"}),
            ], style={"background":"#f8f9fa","borderRadius":"10px","padding":"14px",
                      "border":"1px solid #eef0f5","flex":"1"}),

            html.Div([
                html.Div([html.I(className="fas fa-triangle-exclamation",
                                 style={"color":"#6c757d","marginRight":"6px","fontSize":"11px"}),
                          html.Span("Frustration", style={"fontSize":"10px","fontWeight":"700",
                                                          "color":"#6c757d","textTransform":"uppercase",
                                                          "letterSpacing":"0.5px"})],
                         style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
                badge("⚠️ Détectée" if frus else "✓ Non détectée",
                      "#fdf0f0" if frus else "#e8f8ef",
                      AT_ORANGE if frus else AT_GREEN,
                      "#f5c0c5" if frus else "#b8e8cc",
                      {"fontSize":"12px","padding":"4px 12px"}),
            ], style={"background":"#f8f9fa","borderRadius":"10px","padding":"14px",
                      "border":"1px solid #eef0f5","flex":"1"}),

            html.Div([
                html.Div([html.I(className="fas fa-shield-halved",
                                 style={"color":"#6c757d","marginRight":"6px","fontSize":"11px"}),
                          html.Span("Modération", style={"fontSize":"10px","fontWeight":"700",
                                                         "color":"#6c757d","textTransform":"uppercase",
                                                         "letterSpacing":"0.5px"})],
                         style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
                badge("✓ Répondu" if mod else "✗ Non répondu",
                      "#e8f8ef" if mod else "#fdf0f0",
                      AT_GREEN if mod else AT_RED,
                      "#b8e8cc" if mod else "#f5c0c5",
                      {"fontSize":"12px","padding":"4px 12px"}),
            ], style={"background":"#f8f9fa","borderRadius":"10px","padding":"14px",
                      "border":"1px solid #eef0f5","flex":"1"}),
        ], style={"display":"flex","gap":"10px","flexWrap":"wrap","marginBottom":"16px"}),

        html.Div([
            html.Div([
                html.I(className="fas fa-quote-left",
                       style={"color":AT_BLUE,"marginRight":"8px","fontSize":"13px"}),
                html.Span("Commentaire original", style={"fontSize":"11px","fontWeight":"700",
                                                         "color":"#495057","textTransform":"uppercase",
                                                         "letterSpacing":"0.5px"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"10px"}),
            html.Div(comment.get("commentaire_original",
                                  comment.get("commentaire","Non disponible")),
                     style={"background":"#f8f9fa","padding":"14px 16px","borderRadius":"10px",
                            "fontSize":"13.5px","lineHeight":"1.65","color":"#212529",
                            "border":f"1px solid {AT_BLUE}20","borderLeft":f"4px solid {AT_BLUE}",
                            "wordBreak":"break-word"}),
        ], style={"marginBottom":"14px"}),

        html.Div(f"ID: {comment.get('_id','N/A')}",
                 style={"fontSize":"10px","color":"#adb5bd","textAlign":"right",
                        "fontFamily":"monospace","marginTop":"4px"}),
    ])

    modal_style = {
        "display":"flex","position":"fixed","top":0,"left":0,"width":"100%","height":"100%",
        "backgroundColor":"rgba(0,10,30,0.55)","zIndex":99999,
        "justifyContent":"center","alignItems":"center","backdropFilter":"blur(3px)",
    }
    return modal_style, content


# ── FERMER MODALE ─────────────────────────────────────────────────────────────
@callback(
    Output("comment-modal","style",allow_duplicate=True),
    Input("close-modal","n_clicks"),
    prevent_initial_call=True,
)
def close_modal(_):
    return {"display":"none"}


# ── THEME ─────────────────────────────────────────────────────────────────────
@callback(
    Output("app-wrapper","data-theme"),
    Input("theme-store","data"),
    prevent_initial_call=False,
)
def update_theme(theme):
    return theme or "light"
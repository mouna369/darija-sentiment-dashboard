
"""dashboard.py — Tableau de bord principal avec vue Global / Ce Mois"""

import dash
from dash import html, dcc, callback, Input, Output, State, clientside_callback, no_update
import plotly.graph_objects as go
import sys, os, time
from functools import lru_cache
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from database import MONGO_AVAILABLE, _col

# Décalage horaire Algérie (UTC+1)
TZ_OFFSET = timedelta(hours=1)

def now_local():
    """Retourne l'heure locale algérienne (UTC+1)."""
    return datetime.utcnow() + TZ_OFFSET

dash.register_page(__name__, path='/', name='Tableau de Bord')

# ── COULEURS ALGÉRIE TÉLÉCOM ──────────────────────────────────────────────────
BLUE       = "#003087"
BLUE_MID   = "#1a4fa0"
BLUE_LIGHT = "#e8f0fb"
GREEN      = "#00a854"
RED        = "#e8384f"
ORANGE     = "#f59e0b"
NEUTRAL    = "#64748b"

import config.configuration_seuil as cfg
cfg.load_seuils_from_db()

SEUIL_NEGATIF      = cfg.SEUIL_NEGATIF
SEUIL_TAUX_JOUR    = cfg.SEUIL_TAUX_JOUR
SEUIL_VOLUME_JOUR  = cfg.SEUIL_VOLUME_JOUR
SEUIL_PIC_CRITIQUE = cfg.SEUIL_PIC_CRITIQUE

def get_ttl_hash(seconds=300):
    return round(time.time() / seconds)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DÉTECTION JOURNALIÈRE
# ═══════════════════════════════════════════════════════════════════════════════
def get_alarme_journaliere():
    """
    Détecte une crise journalière selon 2 conditions :
    Condition 1 — Taux négatif >= SEUIL_TAUX_JOUR
    Condition 2 — Volume pondéré >= SEUIL_VOLUME_JOUR
    """
    cfg.load_seuils_from_db()
    SEUIL_TAUX_JOUR   = cfg.SEUIL_TAUX_JOUR
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR

    vide = {
        "alarme_active":     False,
        "raison":            "",
        "taux_auj":          0.0,
        "volume_negatif":    0,
        "volume_pondere":    0,
        "volume_total":      0,
        "volume_positif":    0,
        "volume_neutre":     0,
        "taux_vs_hier":      0.0,
        "volume_vs_hier":    0,
        "heure_pic":         "—",
        "themes_crise":      [],
        "date_analyse":      now_local().strftime("%d/%m/%Y à %H:%M"),
        "seuil_taux":        SEUIL_TAUX_JOUR,
        "seuil_volume":      SEUIL_VOLUME_JOUR,
        "condition_taux":    False,
        "condition_volume":  False,
        "source_principale": "—",
        "sources_detail":    {},
    }

    if not MONGO_AVAILABLE or _col is None:
        print("⚠️ MongoDB non disponible pour get_alarme_journaliere")
        return vide

    try:
        maintenant = now_local()
        hier_24h   = maintenant - timedelta(hours=24)
        avant_hier = maintenant - timedelta(hours=48)

        # ── 1. Agrégation aujourd'hui ─────────────────────────────────────────
        pipeline_auj = [
            {"$match": {"date_clean": {"$gte": hier_24h}}},
            {"$group": {
                "_id": None,
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                "neutres":  {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
                "volume_pondere": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$sentiment_label", "NEGATIF"]},
                            {"$ifNull": ["$frequence", 1]},
                            0
                        ]
                    }
                },
            }}
        ]

        res_auj = list(_col.aggregate(pipeline_auj))
        if not res_auj or res_auj[0]["total"] == 0:
            return vide

        r              = res_auj[0]
        total          = r["total"]
        negatifs       = r["negatifs"]
        positifs       = r["positifs"]
        neutres        = r["neutres"]
        volume_pondere = r.get("volume_pondere", negatifs)
        taux_auj       = round(negatifs / total * 100, 1) if total > 0 else 0.0

        # ── 2. Agrégation hier (variation) ────────────────────────────────────
        pipeline_hier = [
            {"$match": {"date_clean": {"$gte": avant_hier, "$lt": hier_24h}}},
            {"$group": {
                "_id": None,
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "volume_pondere": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$sentiment_label", "NEGATIF"]},
                            {"$ifNull": ["$frequence", 1]},
                            0
                        ]
                    }
                },
            }}
        ]
        res_hier         = list(_col.aggregate(pipeline_hier))
        hier_total       = res_hier[0]["total"]                        if res_hier else 0
        hier_neg         = res_hier[0]["negatifs"]                     if res_hier else 0
        hier_vol_pondere = res_hier[0].get("volume_pondere", hier_neg) if res_hier else 0
        taux_hier        = round(hier_neg / hier_total * 100, 1) if hier_total > 0 else 0.0
        taux_vs_hier     = round(taux_auj - taux_hier, 1)
        volume_vs_hier   = volume_pondere - hier_vol_pondere

        # ── 3. Heure de pic ──────────────────────────────────────────────────
        pipeline_heure = [
            {"$match": {"sentiment_label": "NEGATIF", "date_clean": {"$gte": hier_24h}}},
            {"$addFields": {
                "_date_src": {
                    "$cond": {
                        "if": {"$eq": [{"$type": "$date_originale"}, "date"]},
                        "then": "$date_originale",
                        "else": "$date_annotation",
                    }
                }
            }},
            # {"$addFields": {"_date_utcplus1": {"$add": ["$_date_src", 3600000]}}},
            # {"$addFields": {"heure": {"$hour": "$_date_utcplus1"}}},
            {"$addFields": {"heure": {"$hour": "$_date_src"}}},
            {"$group": {"_id": "$heure", "signal": {"$sum": {"$ifNull": ["$frequence", 1]}}}},
            {"$sort": {"signal": -1}},
            {"$limit": 1},
        ]

        res_heure = list(_col.aggregate(pipeline_heure))
        if res_heure and res_heure[0]["_id"] is not None:
            heure_value = res_heure[0]["_id"]
            heure_pic = f"{int(heure_value):02d}h00" if isinstance(heure_value, (int, float)) and 0 <= heure_value <= 23 else "—"
        else:
            heure_pic = "—"

        # ── 4. Thèmes avec FILTRAGE selon SEUIL_VOLUME_JOUR ───────────────────
        pipeline_themes = [
            {"$match": {
                "sentiment_label": "NEGATIF",
                "theme_pred": {"$exists": True, "$ne": None},
                "date_clean": {"$gte": hier_24h}
            }},
            {"$group": {
                "_id": "$theme_pred",
                "count":        {"$sum": 1},
                "signal_theme": {"$sum": {"$ifNull": ["$frequence", 1]}},
            }},
            {"$sort": {"signal_theme": -1}},
        ]

        theme_map = {
            "prblm":                "Probleme",
            "service":              "Service Client",
            "prix":                 "Tarifs",
            "reseau":               "Réseau",
            "technique":            "Technique",
            "reseau_technique":     "Réseau Technique",
            "attente":              "Délais d'attente",
            "facturation_tarifs":   "Facturation",
            "service_clientele":    "Service Client",
            "application_digitale": "App Digitale",
            "produit":              "Qualité Produit",
            "installation":         "Installation",
            "saturation":           "Saturation",
            "information":          "Information Générale",
        }

        res_themes = list(_col.aggregate(pipeline_themes))
        
        # ✅ FILTRAGE : Ne garder que les thèmes qui dépassent SEUIL_VOLUME_JOUR
        themes_crise = []
        for r in res_themes:
            if r["_id"]:
                signal_theme = r.get("signal_theme", r["count"])
                if signal_theme >= SEUIL_VOLUME_JOUR:
                    themes_crise.append({
                        "label": theme_map.get(
                            r["_id"].lower() if r["_id"] else "",
                            r["_id"].replace("_", " ").title() if r["_id"] else "?"
                        ),
                        "count": r["count"],
                        "signal_theme": signal_theme,
                    })
        
        # Trier par signal_theme décroissant et garder les 3 premiers
        themes_crise.sort(key=lambda x: x["signal_theme"], reverse=True)
        themes_crise = themes_crise[:3]

        # ── 5. Sources ────────────────────────────────────────────────────────
        pipeline_sources = [
            {"$match": {"sentiment_label": "NEGATIF", "date_clean": {"$gte": hier_24h}}},
            {"$group": {
                "_id": {"$ifNull": ["$source", "Autre"]},
                "count": {"$sum": 1},
                "signal_source": {"$sum": {"$ifNull": ["$frequence", 1]}},
            }},
            {"$sort": {"signal_source": -1}},
        ]
        res_sources       = list(_col.aggregate(pipeline_sources))
        sources_detail    = {r["_id"]: r["signal_source"] for r in res_sources}
        source_principale = max(sources_detail, key=sources_detail.get) if sources_detail else "—"

        # ── 6. Source principale par thème ────────────────────────────────────
        pipeline_theme_source = [
            {"$match": {
                "sentiment_label": "NEGATIF",
                "theme_pred": {"$exists": True, "$ne": None},
                "date_clean": {"$gte": hier_24h}
            }},
            {"$group": {
                "_id": {"theme": "$theme_pred", "source": {"$ifNull": ["$source", "Autre"]}},
                "signal": {"$sum": {"$ifNull": ["$frequence", 1]}},
            }},
            {"$sort": {"signal": -1}},
        ]
        res_theme_source = list(_col.aggregate(pipeline_theme_source))
        theme_source_map = {}
        for row in res_theme_source:
            theme_key  = row["_id"]["theme"]
            source_key = row["_id"]["source"]
            if theme_key not in theme_source_map:
                theme_source_map[theme_key] = source_key

        for t in themes_crise:
            raw_key = next(
                (k for k, v in theme_map.items() if v == t["label"]),
                t["label"].lower().replace(" ", "_"),
            )
            t["source_principale"] = theme_source_map.get(raw_key, source_principale)

        # ── 7. Évaluation conditions ──────────────────────────────────────────
        condition_taux   = taux_auj >= SEUIL_TAUX_JOUR
        condition_volume = volume_pondere >= SEUIL_VOLUME_JOUR
        alarme_active    = condition_taux and condition_volume

        raisons = []
        if condition_taux:
            raisons.append(f"taux négatif à {taux_auj}% (seuil: {SEUIL_TAUX_JOUR}%)")
        if condition_volume:
            raisons.append(f"signal pondéré {volume_pondere} (seuil: {SEUIL_VOLUME_JOUR})")
        raison = " — ".join(raisons) if raisons else ""

        return {
            "alarme_active":     alarme_active,
            "raison":            raison,
            "taux_auj":          taux_auj,
            "volume_negatif":    negatifs,
            "volume_pondere":    volume_pondere,
            "volume_total":      total,
            "volume_positif":    positifs,
            "volume_neutre":     neutres,
            "taux_vs_hier":      taux_vs_hier,
            "volume_vs_hier":    volume_vs_hier,
            "heure_pic":         heure_pic,
            "themes_crise":      themes_crise,
            "date_analyse":      maintenant.strftime("%d/%m/%Y à %H:%M"),
            "seuil_taux":        SEUIL_TAUX_JOUR,
            "seuil_volume":      SEUIL_VOLUME_JOUR,
            "condition_taux":    condition_taux,
            "condition_volume":  condition_volume,
            "source_principale": source_principale,
            "sources_detail":    sources_detail,
        }

    except Exception as e:
        print(f"❌ Erreur get_alarme_journaliere: {e}")
        import traceback
        traceback.print_exc()
        return vide
# ═══════════════════════════════════════════════════════════════════════════════
# 2. BANNIÈRE D'ALERTE
# ═══════════════════════════════════════════════════════════════════════════════

def make_alert_banner(stats):
    cfg.load_seuils_from_db()
    SEUIL_TAUX_JOUR   = cfg.SEUIL_TAUX_JOUR
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR
    alarme  = get_alarme_journaliere()
    taux_fr = stats.get("taux_frustration", 0)
    alerts  = []

    if alarme["alarme_active"]:
        themes_str = ""
        if alarme["themes_crise"]:
            themes_str = " — Thèmes : " + ", ".join(
                f"{t['label']} ({t.get('signal_theme', t['count'])} signaux)"
                for t in alarme["themes_crise"][:2]
            )

        variation_str = ""
        if alarme["taux_vs_hier"] != 0:
            signe = "+" if alarme["taux_vs_hier"] > 0 else ""
            variation_str = f" ({signe}{alarme['taux_vs_hier']}% vs hier)"

        vol_pondere = alarme.get("volume_pondere", alarme["volume_negatif"])

        alerts.append(html.Div([
            html.I(className="fas fa-circle-exclamation",
                   style={"fontSize": "20px", "flexShrink": "0"}),
            html.Div([
                html.Span(
                    f"🚨 Crise détectée aujourd'hui — "
                    f"Taux négatif : {alarme['taux_auj']}%{variation_str} — "
                    f"Signal : {vol_pondere} ({alarme['volume_negatif']} clients)"
                    f"{themes_str}",
                    style={"flex": "1"}
                ),
                html.Span(
                    f"Pic à {alarme['heure_pic']}",
                    style={
                        "fontSize": "11px",
                        "background": "rgba(255,255,255,0.2)",
                        "padding": "2px 8px",
                        "borderRadius": "8px",
                        "whiteSpace": "nowrap",
                        "margin-top": "5px",
                    }
                ),
            ], style={"flex": "1", "display": "flex",
                      "alignItems": "center", "gap": "10px", "flexWrap": "wrap"}),
            html.Button(
                html.I(className="fas fa-times", style={"fontSize": "12px"}),
                className="alert-close-btn",
                id={"type": "alert-close", "id": "critical"},
                n_clicks=0,
                style={
                    "background": "transparent", "border": "none",
                    "color": "currentColor", "cursor": "pointer",
                    "padding": "5px 8px", "borderRadius": "8px",
                    "flexShrink": "0",
                },
            ),
        ], className="alert-banner danger",
           style={"display": "flex", "alignItems": "center", "gap": "12px"}))

    elif alarme["condition_taux"] or alarme["condition_volume"]:
        if alarme["condition_taux"]:
            msg = (
                f"⚠️ Taux négatif journalier élevé — {alarme['taux_auj']}% "
                f"(seuil : {SEUIL_TAUX_JOUR}%) — signal : {alarme.get('volume_pondere', alarme['volume_negatif'])} msgs"
            )
        else:
            msg = (
                f"⚠️ Signal négatif journalier élevé — {alarme.get('volume_pondere', alarme['volume_negatif'])} signaux "
                f"(seuil : {SEUIL_VOLUME_JOUR}) — taux : {alarme['taux_auj']}%"
            )

        alerts.append(html.Div([
            html.I(className="fas fa-triangle-exclamation", style={"fontSize": "20px"}),
            html.Span(msg, style={"flex": "1"}),
            html.Button(
                html.I(className="fas fa-times", style={"fontSize": "12px"}),
                className="alert-close-btn",
                id={"type": "alert-close", "id": "warning"},
                n_clicks=0,
            ),
        ], className="alert-banner warning"))

    if taux_fr > 20:
        alerts.append(html.Div([
            html.I(className="fas fa-face-frown", style={"fontSize": "20px"}),
            html.Span(
                f"Frustrations élevées — {taux_fr}% des messages signalent "
                f"une forte insatisfaction client.",
                style={"flex": "1"}
            ),
            html.Button(
                html.I(className="fas fa-times", style={"fontSize": "12px"}),
                className="alert-close-btn",
                id={"type": "alert-close", "id": "frustration"},
                n_clicks=0,
            ),
        ], className="alert-banner warning"))

    return html.Div(alerts) if alerts else None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MODAL D'ALARME
# ═══════════════════════════════════════════════════════════════════════════════

def make_alarm_modal(stats):
    cfg.load_seuils_from_db()
    SEUIL_TAUX_JOUR   = cfg.SEUIL_TAUX_JOUR
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR
    alarme = get_alarme_journaliere()

    if not alarme["alarme_active"]:
        return html.Div(id="alarm-modal-wrapper", style={"display": "none"})

    taux_auj          = alarme["taux_auj"]
    vol_neg           = alarme["volume_negatif"]
    vol_pondere       = alarme.get("volume_pondere", vol_neg)
    vol_total         = alarme["volume_total"]
    heure_pic         = alarme["heure_pic"]
    taux_vs_hier      = alarme["taux_vs_hier"]
    volume_vs_hier    = alarme["volume_vs_hier"]
    themes            = alarme["themes_crise"]
    source_principale = alarme.get("source_principale", "—")
    sources_detail    = alarme.get("sources_detail", {})
    doublons          = vol_pondere - vol_neg

    def variation_badge(val, suffix="pts"):
        if val == 0:
            return html.Span("stable", style={"color": "#f59e0b", "fontSize": "11px"})
        color = "#e8384f" if val > 0 else "#00a854"
        icon  = "↑" if val > 0 else "↓"
        signe = "+" if val > 0 else ""
        return html.Span(
            f"{icon} {signe}{val} {suffix} vs hier",
            style={"color": color, "fontSize": "11px", "fontWeight": "600"}
        )

    themes_html = []
    for t in themes[:3]:
        src_theme    = t.get("source_principale", source_principale)
        signal_theme = t.get("signal_theme", t["count"])
        count        = t["count"]
        themes_html.append(html.Div([
            html.Span(t["label"],
                      style={"fontSize": "12px", "fontWeight": "600", "color": "#ffffff"}),
            html.Span(f"{signal_theme} signaux",
                      style={"fontSize": "11px", "background": "rgba(232,56,79,0.15)",
                             "color": "#e8384f", "padding": "2px 8px",
                             "borderRadius": "10px", "marginLeft": "8px"}),
            html.Span(f"{count} client{'s' if count > 1 else ''}",
                      style={"fontSize": "10px", "background": "rgba(255,255,255,0.08)",
                             "color": "rgba(255,255,255,0.55)", "padding": "2px 6px",
                             "borderRadius": "10px", "marginLeft": "4px"}),
            html.Span(
                [html.I(className="fas fa-share-nodes",
                        style={"marginRight": "4px", "fontSize": "9px"}), src_theme],
                style={"fontSize": "10px", "background": "rgba(0,48,135,0.25)",
                       "color": "#93b4ff", "padding": "2px 8px",
                       "borderRadius": "10px", "marginLeft": "6px", "fontWeight": "500"}
            ),
        ], style={"display": "flex", "alignItems": "center", "padding": "6px 0",
                  "borderBottom": "1px solid rgba(255,255,255,0.08)",
                  "flexWrap": "wrap", "gap": "4px"}))

    sources_html = []
    total_src    = sum(sources_detail.values()) or 1
    for src, signal_src in sorted(sources_detail.items(), key=lambda x: -x[1])[:5]:
        pct = round(signal_src / total_src * 100)
        sources_html.append(html.Div([
            html.Span(src, style={"fontSize": "11px", "color": "#ffffff", "minWidth": "80px"}),
            html.Div([
                html.Div(style={"height": "6px", "width": f"{pct}%",
                                "background": "linear-gradient(90deg,#e8384f,#f59e0b)",
                                "borderRadius": "3px", "transition": "width 0.6s ease"}),
            ], style={"flex": "1", "background": "rgba(255,255,255,0.08)",
                      "borderRadius": "3px", "margin": "0 8px", "height": "6px"}),
            html.Span(f"{signal_src} signaux ({pct}%)",
                      style={"fontSize": "10px", "color": "rgba(255,255,255,0.55)",
                             "minWidth": "90px", "textAlign": "right"}),
        ], style={"display": "flex", "alignItems": "center", "padding": "4px 0"}))

    return html.Div(id="alarm-modal-wrapper", children=[
        html.Audio(
            id="alarm-audio",
            src="/assets/sounds/mixkit-retro-game-emergency-alarm-1000 (1).wav",
            autoPlay=True, loop=True, style={"display": "none"},
        ),
        html.Div(
            id="alarm-overlay", className="alarm-overlay", style={"display": "flex"},
            children=[
                html.Div(className="alarm-modal", children=[
                    html.Div(className="alarm-pulse-ring"),
                    html.Div(
                        html.I(className="fas fa-bell",
                               style={"fontSize": "28px", "color": RED}),
                        className="alarm-icon-wrap",
                    ),
                    html.Div("⚠ ALERTE CRISE JOURNALIÈRE", className="alarm-label"),
                    html.H3("Taux Négatif Hors Seuil", className="alarm-title"),
                    html.P([
                        "Les deux seuils d'alarme ont été franchis aujourd'hui : ",
                        html.Strong(f"taux > {SEUIL_TAUX_JOUR}%", style={"color": "#fff"}),
                        " ET ",
                        html.Strong(f"signal pondéré > {SEUIL_VOLUME_JOUR}", style={"color": "#fff"}),
                        ". Une intervention est recommandée.",
                    ], className="alarm-desc"),

                    html.Div([
                        # KPI 1 — Taux
                        html.Div([
                            html.Div(f"{taux_auj}%", className="alarm-stat-value alarm-red"),
                            html.Div("Taux négatif aujourd'hui", className="alarm-stat-label"),
                            variation_badge(taux_vs_hier, suffix="pts"),
                        ], className="alarm-stat"),

                        # KPI 2 — Signal pondéré
                        html.Div([
                            html.Div(str(vol_pondere), className="alarm-stat-value alarm-red"),
                            html.Div("Signaux reçus (avec répétitions)", className="alarm-stat-label"),
                            html.Div([
                                html.Span(f"{vol_neg} clients uniques",
                                          style={"fontSize": "10px",
                                                 "background": "rgba(255,255,255,0.08)",
                                                 "color": "rgba(255,255,255,0.7)",
                                                 "padding": "2px 7px", "borderRadius": "8px",
                                                 "marginRight": "4px"}),
                                html.Span(f"+{doublons} répét.",
                                          style={"fontSize": "10px",
                                                 "background": "rgba(245,158,11,0.15)",
                                                 "color": "#f59e0b",
                                                 "padding": "2px 7px",
                                                 "borderRadius": "8px"}) if doublons > 0 else None,
                            ], style={"display": "flex", "alignItems": "center",
                                      "flexWrap": "wrap", "gap": "4px", "marginTop": "4px"}),
                            variation_badge(volume_vs_hier, suffix="signaux"),
                        ], className="alarm-stat"),

                        # KPI 3 — Heure de pic
                        html.Div([
                            html.Div(heure_pic, className="alarm-stat-value alarm-orange"),
                            html.Div("Heure de pic", className="alarm-stat-label"),
                            html.Span("→ surveiller cette heure",
                                      style={"fontSize": "11px", "color": "#f59e0b"}),
                        ], className="alarm-stat"),

                        # KPI 4 — Source
                        html.Div([
                            html.Div(
                                [html.I(className="fas fa-share-nodes",
                                        style={"marginRight": "6px", "fontSize": "14px"}),
                                 source_principale],
                                className="alarm-stat-value",
                                style={"color": "#93b4ff", "fontSize": "16px"},
                            ),
                            html.Div("Source la plus touchée", className="alarm-stat-label"),
                            html.Span(
                                f"{sources_detail.get(source_principale, 0)} signaux",
                                style={"fontSize": "11px", "color": "rgba(255,255,255,0.5)"},
                            ),
                        ], className="alarm-stat"),
                    ], className="alarm-stats"),

                    # Thèmes
                    html.Div([
                        html.Div("Thèmes les plus touchés :",
                                 style={"fontSize": "11px", "color": "rgba(255,255,255,0.6)",
                                        "marginBottom": "8px", "textTransform": "uppercase",
                                        "letterSpacing": "0.5px"}),
                        html.Div([
                            html.Span(style={"display": "inline-block", "width": "8px",
                                            "height": "8px", "borderRadius": "50%",
                                            "background": "#e8384f", "marginRight": "4px"}),
                            html.Span("signaux = SUM(fréquence)",
                                      style={"fontSize": "10px",
                                             "color": "rgba(255,255,255,0.45)",
                                             "marginRight": "12px"}),
                            html.Span(style={"display": "inline-block", "width": "8px",
                                            "height": "8px", "borderRadius": "50%",
                                            "background": "rgba(255,255,255,0.2)",
                                            "marginRight": "4px"}),
                            html.Span("clients = uniques",
                                      style={"fontSize": "10px",
                                             "color": "rgba(255,255,255,0.45)"}),
                        ], style={"marginBottom": "8px"}),
                        html.Div(themes_html) if themes_html else html.Span(
                            "Données thèmes non disponibles",
                            style={"fontSize": "12px", "color": "rgba(255,255,255,0.4)"}),
                    ], style={"background": "rgba(255,255,255,0.05)", "borderRadius": "10px",
                              "padding": "12px 16px", "margin": "12px 0",
                              "width": "100%", "textAlign": "left"}),

                    # Sources
                    html.Div([
                        html.Div("Répartition par source (signaux reçus) :",
                                 style={"fontSize": "11px", "color": "rgba(255,255,255,0.6)",
                                        "marginBottom": "8px", "textTransform": "uppercase",
                                        "letterSpacing": "0.5px"}),
                        html.Div(sources_html) if sources_html else html.Span(
                            "Données sources non disponibles",
                            style={"fontSize": "12px", "color": "rgba(255,255,255,0.4)"}),
                    ], style={"background": "rgba(255,255,255,0.05)", "borderRadius": "10px",
                              "padding": "12px 16px", "margin": "0 0 12px 0",
                              "width": "100%", "textAlign": "left"}),

                    html.Div(
                        f"Analysé le {alarme['date_analyse']}",
                        style={"fontSize": "11px", "color": "rgba(255,255,255,0.45)",
                               "textAlign": "center", "marginBottom": "8px"}
                    ),
                    html.Button(
                        "Fermer", id="alarm-close-btn", className="alarm-btn-stop",
                        n_clicks=0, style={"marginTop": "50px", "width": "100%"},
                    ),
                ]),
            ],
        ),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FONCTIONS DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def get_monthly_stats():
    """Stats agrégées par mois avec volume réel (SUM frequence)."""
    if MONGO_AVAILABLE and _col is not None:
        try:
            pipeline = [
                {"$match": {"mois": {"$exists": True, "$ne": None, "$ne": ""}}},
                {
                    "$group": {
                        "_id": "$mois",
                        "total":        {"$sum": 1},
                        "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                        "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                        "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
                        "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
                        "avg_score":    {"$avg": "$sentiment_score"},
                        "total_reel":   {"$sum": {"$ifNull": ["$frequence", 1]}},
                        "negatifs_reel": {
                            "$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]},
                                               {"$ifNull": ["$frequence", 1]}, 0]}
                        },
                        "positifs_reel": {
                            "$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]},
                                               {"$ifNull": ["$frequence", 1]}, 0]}
                        },
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            results = list(_col.aggregate(pipeline))
            monthly = {}
            for r in results:
                mois       = r["_id"]
                total      = r["total"]      or 1
                total_reel = r["total_reel"] or 1
                monthly[mois] = {
                    "mois":       mois,
                    "total":      r["total"],
                    "negatifs":   r["negatifs"],
                    "positifs":   r["positifs"],
                    "neutres":    r["neutres"],
                    "frustrations": r["frustrations"],
                    "avg_score":  round(float(r["avg_score"] or 0), 3),
                    "total_reel":    r["total_reel"],
                    "negatifs_reel": r["negatifs_reel"],
                    "positifs_reel": r["positifs_reel"],
                    "taux_negatif":           round(r["negatifs"] / total * 100, 1),
                    "taux_satisfaction":       round(r["positifs"] / total * 100, 1),
                    "taux_frustration":        round(r["frustrations"] / total * 100, 1),
                    "taux_negatif_reel":       round(r["negatifs_reel"] / total_reel * 100, 1),
                    "taux_satisfaction_reel":  round(r["positifs_reel"] / total_reel * 100, 1),
                }
            return monthly
        except Exception as e:
            print(f"Erreur get_monthly_stats: {e}")
    return {}


@lru_cache(maxsize=128)
def get_filtered_stats(ttl_hash=None):
    """Stats agrégées sur toute la période avec volume réel (SUM frequence)."""
    del ttl_hash
    if MONGO_AVAILABLE and _col is not None:
        try:
            total_docs = _col.count_documents({})
            if total_docs == 0:
                return _empty_stats()

            result = list(_col.aggregate([{
                "$group": {
                    "_id": None,
                    "total_unique":  {"$sum": 1},
                    "negatifs":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                    "positifs":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                    "neutres":       {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
                    "frustrations":  {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
                    "avg_score":     {"$avg": "$sentiment_score"},
                    "total_reel":    {"$sum": {"$ifNull": ["$frequence", 1]}},
                    "negatifs_reel": {
                        "$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]},
                                           {"$ifNull": ["$frequence", 1]}, 0]}
                    },
                    "positifs_reel": {
                        "$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]},
                                           {"$ifNull": ["$frequence", 1]}, 0]}
                    },
                    "neutres_reel": {
                        "$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},
                                           {"$ifNull": ["$frequence", 1]}, 0]}
                    },
                    "frustrations_reel": {
                        "$sum": {"$cond": ["$frustration_detectee",
                                           {"$ifNull": ["$frequence", 1]}, 0]}
                    },
                }
            }]))

            if not result:
                return _empty_stats()

            r            = result[0]
            total_unique = r["total_unique"] or 1
            total_reel   = r["total_reel"]   or 1

            cs = {
                "total":             r["total_unique"],
                "positifs":          r["positifs"],
                "negatifs":          r["negatifs"],
                "neutres":           r["neutres"],
                "frustrations":      r["frustrations"],
                "total_reel":        r["total_reel"],
                "negatifs_reel":     r["negatifs_reel"],
                "positifs_reel":     r["positifs_reel"],
                "neutres_reel":      r["neutres_reel"],
                "frustrations_reel": r["frustrations_reel"],
                "avg_score":               round(float(r["avg_score"] or 0), 3),
                "taux_satisfaction":       round(r["positifs"]     / total_unique * 100, 1),
                "taux_negatif":            round(r["negatifs"]     / total_unique * 100, 1),
                "taux_frustration":        round(r["frustrations"] / total_unique * 100, 1),
                "taux_negatif_reel":       round(r["negatifs_reel"]     / total_reel * 100, 1),
                "taux_satisfaction_reel":  round(r["positifs_reel"]     / total_reel * 100, 1),
            }

            monthly    = get_monthly_stats()
            mois_liste = sorted(monthly.keys())

            if len(mois_liste) >= 2:
                cm = monthly[mois_liste[-1]]
                pm = monthly[mois_liste[-2]]
                cs.update({
                    "current_month_label":  mois_liste[-1],
                    "previous_month_label": mois_liste[-2],
                    "total_variation":      round((cm["total_reel"] - pm["total_reel"]) / max(pm["total_reel"], 1) * 100, 1),
                    "avg_score_variation":  round(cm["avg_score"] - pm["avg_score"], 3),
                    "negatif_variation":    round(cm["taux_negatif"] - pm["taux_negatif"], 1),
                    "has_comparison":       True,
                    "period_text":          f"vs {mois_liste[-2]}",
                })
            elif len(mois_liste) == 1:
                cs.update({
                    "current_month_label": mois_liste[0], "previous_month_label": None,
                    "total_variation": 0, "avg_score_variation": 0, "negatif_variation": 0,
                    "has_comparison": False, "period_text": "1ère période",
                })
            else:
                cs.update({
                    "has_comparison": False, "period_text": "données initiales",
                    "total_variation": 0, "avg_score_variation": 0, "negatif_variation": 0,
                })
            return cs
        except Exception as e:
            print(f"Erreur MongoDB stats: {e}")
    return _empty_stats()


def _empty_stats():
    return {
        "total": 0, "positifs": 0, "negatifs": 0, "neutres": 0,
        "frustrations": 0, "avg_score": 0,
        "total_reel": 0, "negatifs_reel": 0, "positifs_reel": 0,
        "neutres_reel": 0, "frustrations_reel": 0,
        "taux_satisfaction": 0, "taux_negatif": 0, "taux_frustration": 0,
        "taux_negatif_reel": 0, "taux_satisfaction_reel": 0,
        "total_variation": 0, "avg_score_variation": 0, "negatif_variation": 0,
        "has_comparison": False, "period_text": "aucune donnée",
    }


def get_filtered_evol():
    if MONGO_AVAILABLE and _col is not None:
        try:
            results = list(_col.aggregate([
                {"$match": {"mois": {"$exists": True, "$ne": None, "$ne": ""}}},
                {"$group": {
                    "_id":      "$mois",
                    "avg_score": {"$avg": "$sentiment_score"},
                    "total":    {"$sum": 1},
                    "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                    "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                }},
                {"$sort": {"_id": 1}}
            ]))
            if results:
                return [{
                    "mois":        r["_id"],
                    "avg_score":   round(float(r["avg_score"] or 0), 3),
                    "total":       r["total"],
                    "taux_negatif": round(r["negatifs"] / max(r["total"], 1) * 100, 1),
                } for r in results]
        except Exception as e:
            print(f"Erreur évolution: {e}")
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# 4.1 DONNÉES PAR PÉRIODE
# ═══════════════════════════════════════════════════════════════════════════════

def get_stats_ce_mois():
    """Stats agrégées pour le mois courant avec volume réel."""
    if not MONGO_AVAILABLE or _col is None:
        return _empty_stats()
    try:
        mois_str = now_local().strftime("%Y-%m")
        result   = list(_col.aggregate([
            {"$match": {"mois": mois_str}},
            {"$group": {
                "_id": None,
                "total":        {"$sum": 1},
                "negatifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs":     {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
                "neutres":      {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},  1, 0]}},
                "frustrations": {"$sum": {"$cond": ["$frustration_detectee", 1, 0]}},
                "avg_score":    {"$avg": "$sentiment_score"},
                "total_reel":   {"$sum": {"$ifNull": ["$frequence", 1]}},
                "negatifs_reel": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]},
                                       {"$ifNull": ["$frequence", 1]}, 0]}
                },
                "positifs_reel": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]},
                                       {"$ifNull": ["$frequence", 1]}, 0]}
                },
                "neutres_reel": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEUTRE"]},
                                       {"$ifNull": ["$frequence", 1]}, 0]}
                },
                "frustrations_reel": {
                    "$sum": {"$cond": ["$frustration_detectee",
                                       {"$ifNull": ["$frequence", 1]}, 0]}
                },
            }}
        ]))
        if not result:
            return _empty_stats()
        r          = result[0]
        total      = r["total"]      or 1
        total_reel = r["total_reel"] or 1
        return {
            "total":             r["total"],
            "positifs":          r["positifs"],
            "negatifs":          r["negatifs"],
            "neutres":           r["neutres"],
            "frustrations":      r["frustrations"],
            "avg_score":         round(float(r["avg_score"] or 0), 3),
            "total_reel":        r["total_reel"],
            "negatifs_reel":     r["negatifs_reel"],
            "positifs_reel":     r["positifs_reel"],
            "neutres_reel":      r["neutres_reel"],
            "frustrations_reel": r["frustrations_reel"],
            "taux_satisfaction":      round(r["positifs"]     / total * 100, 1),
            "taux_negatif":           round(r["negatifs"]     / total * 100, 1),
            "taux_frustration":       round(r["frustrations"] / total * 100, 1),
            "taux_negatif_reel":      round(r["negatifs_reel"]     / total_reel * 100, 1),
            "taux_satisfaction_reel": round(r["positifs_reel"]     / total_reel * 100, 1),
            "total_variation": 0, "avg_score_variation": 0, "negatif_variation": 0,
            "has_comparison":  False, "period_text": mois_str, "mois_str": mois_str,
        }
    except Exception as e:
        print(f"Erreur get_stats_ce_mois: {e}")
        return _empty_stats()


def get_sentiments_par_heure_aujourd_hui():
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        hier_24h = now_local() - timedelta(hours=24)
        pipeline = [
            {"$match": {"date_clean": {"$gte": hier_24h}}},
            {"$addFields": {"_ds": {"$cond": {
                "if": {"$eq": [{"$type": "$date_originale"}, "date"]},
                "then": "$date_originale", "else": "$date_annotation"
            }}}},
            {"$addFields": {"_h": {"$hour": {"$add": ["$_ds", 3600000]}}}},
            {"$group": {
                "_id": "$_h",
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                "positifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "POSITIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        results = list(_col.aggregate(pipeline))
        by_hour = {r["_id"]: r for r in results}
        return [
            {"heure": f"{h:02d}h",
             "total":    by_hour.get(h, {}).get("total", 0),
             "negatifs": by_hour.get(h, {}).get("negatifs", 0),
             "positifs": by_hour.get(h, {}).get("positifs", 0)}
            for h in range(24)
        ]
    except Exception as e:
        print(f"Erreur get_sentiments_par_heure: {e}")
        return []


def get_sources_ce_mois():
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        mois_str = now_local().strftime("%Y-%m")
        results  = list(_col.aggregate([
            {"$match": {"mois": mois_str}},
            {"$group": {
                "_id":      {"$ifNull": ["$source", "Autre"]},
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"total": -1}},
            {"$limit": 8},
        ]))
        tot = sum(r["total"] for r in results) or 1
        return [
            {"label": r["_id"], "total": r["total"], "negatifs": r["negatifs"],
             "pct": round(r["total"] / tot * 100, 1),
             "pct_negatif": round(r["negatifs"] / r["total"] * 100, 1) if r["total"] else 0}
            for r in results if r["_id"]
        ]
    except Exception as e:
        print(f"Erreur get_sources_ce_mois: {e}")
        return []


def get_themes_ce_mois():
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        mois_str   = now_local().strftime("%Y-%m")
        total_mois = _col.count_documents({"mois": mois_str})
        if total_mois == 0:
            return []
        results = list(_col.aggregate([
            {"$match": {"mois": mois_str}},
            {"$group": {
                "_id":      "$theme_pred",
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"total": -1}},
            {"$limit": 5},
        ]))
        theme_map = {
            "service": "Service Client", "prix": "Tarifs",
            "attente": "Délais d'attente", "hors_sujet": "Hors Sujet",
            "produit": "Qualité Produit", "reseau": "Réseau Technique",
            "technique": "Problèmes Techniques", "information": "Information Générale",
            "installation": "Installation", "saturation": "Saturation",
            "facturation_tarifs": "Facturation", "service_clientele": "Service Client",
            "application_digitale": "App Digitale", "experience_positive": "Exp. Positive",
            "suggestions_ameliorations": "Suggestions",
        }
        return [{
            "label":       theme_map.get(r["_id"].lower() if r["_id"] else "",
                                         r["_id"].replace("_", " ").title() if r["_id"] else "?"),
            "total":       r["total"],
            "pct_total":   round(r["total"] / total_mois * 100, 1),
            "pct_negatif": round(r["negatifs"] / r["total"] * 100, 1) if r["total"] else 0,
        } for r in results if r["_id"]]
    except Exception as e:
        print(f"Erreur get_themes_ce_mois: {e}")
        return []


def get_langues_ce_mois():
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        mois_str = now_local().strftime("%Y-%m")
        results  = list(_col.aggregate([
            {"$match": {"mois": mois_str}},
            {"$group": {"_id": "$langue_detectee", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]))
        lang_map = {
            "arabe_classique": "Arabe Classique", "arabe_darija": "Darija",
            "francais": "Français", "arabic": "Arabe",
            "mixte": "Mixte", "anglais": "Anglais",
        }
        tot = sum(r["total"] for r in results) or 1
        return [
            {"label": lang_map.get(r["_id"], r["_id"].replace("_", " ").title() if r["_id"] else "?"),
             "total": r["total"], "pct": round(r["total"] / tot * 100, 1)}
            for r in results if r["_id"]
        ]
    except Exception as e:
        print(f"Erreur get_langues_ce_mois: {e}")
        return []

def get_themes_aujourd_hui():
    """Top 5 thèmes des dernières 24h sans filtre seuil d'alarme."""
    if not MONGO_AVAILABLE or _col is None:
        return []
    try:
        hier_24h  = now_local() - timedelta(hours=24)
        total_auj = _col.count_documents({"date_clean": {"$gte": hier_24h}})
        if total_auj == 0:
            return []
        results = list(_col.aggregate([
            {"$match": {
                "date_clean": {"$gte": hier_24h},
                "theme_pred": {"$exists": True, "$ne": None},
            }},
            {"$group": {
                "_id":      "$theme_pred",
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"total": -1}},
            {"$limit": 5},
        ]))
        theme_map = {
            "service":              "Service Client",
            "prix":                 "Tarifs",
            "attente":              "Délais d'attente",
            "reseau":               "Réseau Technique",
            "technique":            "Problèmes Techniques",
            "information":          "Information Générale",
            "installation":         "Installation",
            "saturation":           "Saturation",
            "facturation_tarifs":   "Facturation",
            "service_clientele":    "Service Client",
            "application_digitale": "App Digitale",
            "experience_positive":  "Exp. Positive",
            "reseau_technique":     "Réseau Technique",
            "hors_sujet":           "Hors Sujet",
            "produit":              "Qualité Produit",
            "suggestions_ameliorations": "Suggestions",
        }
        return [{
            "label":       theme_map.get(
                               r["_id"].lower() if r["_id"] else "",
                               r["_id"].replace("_", " ").title() if r["_id"] else "?"
                           ),
            "total":       r["total"],
            "pct_negatif": round(r["negatifs"] / r["total"] * 100, 1) if r["total"] else 0,
        } for r in results if r["_id"]]
    except Exception as e:
        print(f"Erreur get_themes_aujourd_hui: {e}")
        return []
# ═══════════════════════════════════════════════════════════════════════════════
# 4.2 GRAPHIQUES PÉRIODE
# ═══════════════════════════════════════════════════════════════════════════════

def make_activite_heure_chart(theme="light"):
    c    = _colors(theme)
    data = get_sentiments_par_heure_aujourd_hui()
    heures   = [d["heure"]    for d in data]
    totaux   = [d["total"]    for d in data]
    negatifs = [d["negatifs"] for d in data]
    positifs = [d["positifs"] for d in data]
    if not any(totaux):
        fig = go.Figure()
        fig.add_annotation(text="Aucun message reçu aujourd'hui",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 220))
        return fig
    fig = go.Figure()
    fig.add_trace(go.Bar(x=heures, y=positifs, name="Positifs",
                         marker=dict(color=c["success"], line=dict(width=0), cornerradius=4),
                         hovertemplate="%{x} — Positifs : <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Bar(x=heures, y=negatifs, name="Négatifs",
                         marker=dict(color=c["danger"], line=dict(width=0), cornerradius=4),
                         hovertemplate="%{x} — Négatifs : <b>%{y}</b><extra></extra>"))
    layout = _base_layout(c, 220, margin=dict(l=30, r=10, t=10, b=30))
    layout.update(barmode="stack",
                  xaxis=dict(showgrid=False, tickfont=dict(size=8, color=c["text"]), tickangle=-45),
                  yaxis=dict(showgrid=True, gridcolor=c["grid"], tickfont=dict(size=8, color=c["text"])),
                  legend=dict(orientation="h", x=0, y=1.08, font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
                  hovermode="x unified", bargap=0.15)
    fig.update_layout(**layout)
    return fig


def make_sentiments_donut_mois(theme="light"):
    return make_sentiment_donut(get_stats_ce_mois(), theme)


def make_sources_mois_chart(theme="light"):
    c    = _colors(theme)
    data = get_sources_ce_mois()
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée source ce mois",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 240))
        return fig
    labels  = [d["label"]       for d in data]
    totaux  = [d["total"]       for d in data]
    pct_neg = [d["pct_negatif"] for d in data]
    bar_colors = [BLUE, "#1a4fa0", "#2d66bb", "#4a80d4", "#6699e8",
                  "#3a7bd5", "#5b8fe8", "#7aaaf5"][:len(labels)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=totaux, orientation='h',
        marker=dict(color=bar_colors, line=dict(width=0), cornerradius=6),
        text=[f"{v:,}  ({p}% nég.)" for v, p in zip(totaux, pct_neg)],
        textposition='inside', textfont=dict(size=9, color='white', weight='bold'),
        hovertemplate='<b>%{y}</b><br>Volume : <b>%{x:,}</b><br>Taux négatif : <b>%{customdata}%</b><extra></extra>',
        customdata=pct_neg, width=0.65,
    ))
    max_v  = max(totaux) if totaux else 1
    layout = _base_layout(c, 240, margin=dict(l=10, r=10, t=5, b=15))
    layout.update(
        xaxis=dict(showgrid=True, gridcolor=c["grid"], tickfont=dict(size=8, color=c["text"]),
                   range=[0, max_v * 1.15], zeroline=False, showline=True,
                   linecolor=c["grid"], tickformat=',d'),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, color=c["text"]),
                   autorange='reversed'),
        showlegend=False, bargap=0.28)
    fig.update_layout(**layout)
    return fig


def make_themes_mois_chart(theme="light"):
    return make_theme_chart(get_themes_ce_mois(), theme)


def make_langues_mois_chart(theme="light"):
    c    = _colors(theme)
    data = get_langues_ce_mois()
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée langue ce mois",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 220))
        return fig
    labels = [d["label"] for d in data]
    values = [d["total"] for d in data]
    pcts   = [d["pct"]   for d in data]
    bar_colors_light = [BLUE, "#1a4fa0", "#2d66bb", "#4a80d4", "#6699e8", "#88b2f8"]
    bar_colors_dark  = ["#4a80d4", "#5a8ed8", "#6a9cdc", "#7aaae0", "#8ab8e4", "#9ac6e8"]
    bar_colors = bar_colors_dark[:len(labels)] if theme == "dark" else bar_colors_light[:len(labels)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=values,
        marker=dict(color=bar_colors, line=dict(width=0), cornerradius=12),
        text=[f"{v:,}<br>({p}%)" for v, p in zip(values, pcts)],
        textposition='outside', textfont=dict(size=9, color=c["text"], weight='bold'),
        hovertemplate='<b>%{x}</b><br>Volume: <b>%{y:,}</b><extra></extra>', width=0.65,
    ))
    max_val = max(values) if values else 1
    layout  = _base_layout(c, 220, margin=dict(l=20, r=20, t=40, b=50))
    layout.update(
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=c["text"], weight="bold"), tickangle=-25),
        yaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=',d',
                   tickfont=dict(size=9, color=c["text"]), range=[0, max_val * 1.22], zeroline=False),
        showlegend=False, bargap=0.3)
    fig.update_layout(**layout)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 4.3 KPI ROW — CE MOIS
# ═══════════════════════════════════════════════════════════════════════════════

def make_kpi_row_ce_mois(theme="light"):
    stats    = get_stats_ce_mois()
    mois_lbl = now_local().strftime("%B %Y")

    def _card(variant, icon, label, value, value_color, sub):
        return html.Div([
            html.Div([
                html.Div(html.I(className=icon, style={"fontSize": "20px"}),
                         className="kpi-icon-wrap"),
                html.Span(label, className="kpi-label"),
            ], className="kpi-top-row"),
            html.Div(value, className="kpi-value",
                     style={"color": value_color} if value_color else {}),
            html.Div(className="kpi-underline"),
            html.Div([
                html.Span([
                    html.I(className="fas fa-calendar", style={"fontSize": "9px"}),
                    html.Span(f" {mois_lbl}"),
                ], className="kpi-pill neutral"),
                html.Span(sub, className="kpi-period") if sub else None,
            ], className="kpi-footer"),
        ], className=f"kpi-card {variant}")

    taux_neg_color = (RED if stats["taux_negatif"] >= SEUIL_NEGATIF
                      else ORANGE if stats["taux_negatif"] >= 30 else GREEN)

    return html.Div(html.Div([
        _card("kpi-blue",  "fas fa-message",
              "TOTAL COMMENTAIRES",
              f"{stats['total_reel']:,}".replace(",", "\u202f"),
              None,
              f"{stats['total']} uniques · {stats['total_reel']} reçus"),
        _card("kpi-green", "fas fa-chart-line",
              "SCORE SENTIMENT MOYEN",
              f"{stats['avg_score']:+.2f}", None, "> −0.2 = satisfaisant"),
        _card("kpi-red",   "fas fa-face-frown",
              "TAUX NÉGATIF GLOBAL",
              f"{stats['taux_negatif']}%",
              taux_neg_color, f"Seuil : {SEUIL_NEGATIF}%"),
        _card("kpi-amber", "fas fa-triangle-exclamation",
              "FRUSTRATIONS DÉTECTÉES",
              f"{stats['frustrations']:,}".replace(",", "\u202f"),
              None, f"{stats['taux_frustration']}% des messages"),
    ], className="kpi-grid-4"))


def get_theme_stats():
    if MONGO_AVAILABLE and _col is not None:
        try:
            total = _col.count_documents({})
            if total == 0:
                return []
            results = list(_col.aggregate([
                {"$group": {
                    "_id":      "$theme_pred",
                    "total":    {"$sum": 1},
                    "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                }},
                {"$sort": {"total": -1}},
                {"$limit": 5},
            ]))
            theme_map = {
                "service": "Service Client", "prix": "Tarifs",
                "attente": "Délais d'attente", "hors_sujet": "Hors Sujet",
                "produit": "Qualité Produit", "reseau": "Réseau Technique",
                "technique": "Problèmes Techniques", "information": "Information Générale",
                "installation": "Installation", "saturation": "Saturation",
                "facturation_tarifs": "Facturation", "service_clientele": "Service Client",
                "application_digitale": "App Digitale", "experience_positive": "Exp. Positive",
                "suggestions_ameliorations": "Suggestions",
            }
            return [{
                "label":       theme_map.get(r["_id"].lower(), r["_id"].replace("_", " ").title()),
                "total":       r["total"],
                "pct_total":   round(r["total"] / total * 100, 1) if total else 0,
                "pct_negatif": round(r["negatifs"] / r["total"] * 100, 1) if r["total"] else 0,
            } for r in results if r["_id"]]
        except Exception as e:
            print(f"Erreur themes: {e}")
    return []


def get_langue_stats():
    if MONGO_AVAILABLE and _col is not None:
        try:
            results = list(_col.aggregate([
                {"$group": {"_id": "$langue_detectee", "total": {"$sum": 1}}},
                {"$sort": {"total": -1}},
            ]))
            if results:
                lang_map = {
                    "arabe_classique": "Arabe Classique", "arabe_darija": "Darija",
                    "francais": "Français", "arabic": "Arabe",
                    "mixte": "Mixte", "anglais": "Anglais",
                }
                tot = sum(r["total"] for r in results)
                return [{
                    "label": lang_map.get(r["_id"], r["_id"].replace("_", " ").title()),
                    "total": r["total"],
                    "pct":   round(r["total"] / tot * 100, 1),
                } for r in results if r["_id"]]
        except Exception as e:
            print(f"Erreur langues: {e}")
    return []


def get_pics_negatifs(seuil_pic: float = None):
    cfg.load_seuils_from_db()
    if seuil_pic is None:
        seuil_pic = cfg.SEUIL_PIC_CRITIQUE
    vide = {"nb_pics": 0, "mois_courant": "", "pire_jour": "—",
            "pire_taux": 0.0, "total_jours": 0, "seuil": seuil_pic}
    if not MONGO_AVAILABLE or _col is None:
        return vide
    try:
        mois_liste = sorted(get_monthly_stats().keys())
        if not mois_liste:
            return vide
        mois_courant = mois_liste[-1]
        pipeline = [
            {"$match": {"mois": mois_courant, "date_originale": {"$exists": True, "$ne": None}}},
            {"$addFields": {"day_str": {"$dateToString": {"format": "%d", "date": "$date_originale"}}}},
            {"$group": {
                "_id":      "$day_str",
                "total":    {"$sum": 1},
                "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
            }},
            {"$sort": {"_id": 1}},
        ]
        jours = list(_col.aggregate(pipeline))
        if not jours:
            monthly = get_monthly_stats()
            d       = monthly.get(mois_courant, {})
            taux    = d.get("taux_negatif", 0)
            return {"nb_pics": 1 if taux >= seuil_pic else 0, "mois_courant": mois_courant,
                    "pire_jour": "mois entier", "pire_taux": taux, "total_jours": 1,
                    "seuil": seuil_pic}
        pics = []
        for j in jours:
            total    = j["total"] or 1
            taux_neg = round(j["negatifs"] / total * 100, 1)
            if taux_neg >= seuil_pic:
                pics.append({"jour": j["_id"], "taux": taux_neg})
        pire = max(pics, key=lambda x: x["taux"]) if pics else None
        return {"nb_pics": len(pics), "mois_courant": mois_courant,
                "pire_jour": pire["jour"] if pire else "—",
                "pire_taux": pire["taux"] if pire else 0.0,
                "total_jours": len(jours), "seuil": seuil_pic}
    except Exception as e:
        print(f"Erreur get_pics_negatifs: {e}")
        return vide


# ═══════════════════════════════════════════════════════════════════════════════
# 4.6 HISTORIQUE — DESIGN PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

def _tpill(label):
    return html.Span(label, className="hist-tpill")

def _tpill_more(n):
    return html.Span(f"+{n}", style={
        "display": "inline-block", "padding": "3px 10px", "borderRadius": "20px",
        "fontSize": "11px", "background": "var(--stat-bg)",
        "color": "var(--text-secondary)", "border": "1px solid var(--border-color)",
        "whiteSpace": "nowrap",
    })

def _tl_event(heure, action, theme, note, taux=None):
    if action in ("ARRÊT", "Arrêt", "ARRET"):
        dot_cls, lbl_cls, lbl_txt = "hist-tl-dot hist-dot-stop", "hist-tl-lbl hist-lbl-stop", "Arrêt"
    elif action in ("DÉCLENCHÉE", "Déclenchée", "DECLENCHEE", "DÉCLENCHEE"):
        dot_cls, lbl_cls, lbl_txt = "hist-tl-dot hist-dot-start", "hist-tl-lbl hist-lbl-start", "Déclenchée"
    else:
        dot_cls, lbl_cls, lbl_txt = "hist-tl-dot hist-dot-start", "hist-tl-lbl hist-lbl-start", action
    return html.Div([
        html.Div(html.Div(className=dot_cls), className="hist-tl-dot-wrap"),
        html.Div([
            html.Div([
                html.Span(heure, className="hist-tl-time"),
                html.Span(lbl_txt, className=lbl_cls),
                html.Span(theme, className="hist-tl-theme") if theme else None,
            ], className="hist-tl-row1"),
            html.Div(note, className="hist-tl-note") if note else None,
        ], className="hist-tl-right"),
    ], className="hist-tl-evt")

def _theme_block(theme_label, count, taux_max, volume, events_html, source_principale=None):
    taux_color = "#e8384f" if taux_max >= 70 else "#f59e0b"
    return html.Div([
        html.Div([
            html.Div([
                html.Span(theme_label, className="hist-tb-pill"),
                html.Span(f"{count} déclenchement{'s' if count > 1 else ''}",
                          className="hist-tb-count"),
                html.Span(
                    [html.I(className="fas fa-share-nodes",
                            style={"marginRight": "3px", "fontSize": "9px"}),
                     source_principale or "—"],
                    style={"display": "inline-flex", "alignItems": "center",
                           "fontSize": "10px", "background": "rgba(0,48,135,0.12)",
                           "color": "var(--text-secondary)", "padding": "2px 8px",
                           "borderRadius": "10px", "marginLeft": "6px",
                           "border": "1px solid rgba(0,48,135,0.2)", "whiteSpace": "nowrap"}
                ) if source_principale else None,
            ], className="hist-tb-left"),
            html.Div([
                html.Div([
                    html.Div(f"{taux_max}%", className="hist-tb-sv", style={"color": taux_color}),
                    html.Div("Taux max", className="hist-tb-sl"),
                ], style={"textAlign": "right"}),
                html.Div([
                    html.Div(f"{volume} signaux", className="hist-tb-sv"),
                    html.Div("Signal pondéré", className="hist-tb-sl"),
                ], style={"textAlign": "right"}),
            ], className="hist-tb-stats"),
        ], className="hist-tb-head"),
        html.Div(events_html, className="hist-tb-rows"),
    ], className="hist-theme-block")


# ═══════════════════════════════════════════════════════════════════════════════
# _build_modal — AVEC SIGNAL PONDÉRÉ
# ═══════════════════════════════════════════════════════════════════════════════

def _build_modal(r, modal_id):
    is_active   = (r["statut"] == "EN COURS")
    strip_color = "#e8384f" if is_active else "#00a854"
    sub_txt = html.Span(
        f"{len(r.get('themes_detaille', []))} thème(s) déclenché(s) · "
        f"{'Toujours active' if is_active else 'Alerte terminée'}",
        style={"color": "white", "fontSize": "9px"}
    )

    premier_decl = next(
        (d for d in r.get("declenchements", [])
         if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")), None)
    heure_pic_val   = premier_decl.get("heure", "—") if premier_decl else r.get("heure_pic", "—")
    heure_arret_val = r.get("heure_arret")
    if heure_arret_val and heure_pic_val and heure_pic_val != "—":
        duree_txt = f"{heure_pic_val} → {heure_arret_val}"
    elif heure_arret_val:
        duree_txt = f"Arrêt à {heure_arret_val}"
    else:
        duree_txt = "En cours"

    themes_list = r.get("themes_detaille", [])
    taux_values = [d.get("taux", 0) for d in r.get("declenchements", [])
                   if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")
                   and d.get("taux", 0) > 0]
    vol_values  = [d.get("volume", 0) for d in r.get("declenchements", [])
                   if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")
                   and d.get("volume", 0) > 0]
    taux_moyen = round(sum(taux_values) / len(taux_values), 1) if taux_values else r["taux_max"]
    vol_moyen  = round(sum(vol_values)  / len(vol_values))     if vol_values  else r.get("volume_negatif", 0)

    vol_pondere     = sum(t.get("signal_theme", t.get("count", 0)) for t in themes_list)  # → 485
    vol_neg_display = sum(t.get("count", 0) for t in themes_list)                          # → 267
    doublons        = max(0, vol_pondere - vol_neg_display)   
    vol_total_display = r.get("volume_total", 0)
    doublons        = max(0, vol_pondere - vol_neg_display)

    sources_detail    = r.get("sources_detail", {})
    source_principale = r.get("source_principale", "—")
    if not source_principale or source_principale == "—":
        src_counts = {}
        for t in themes_list:
            sp = t.get("source_principale", "")
            if sp and sp != "—":
                src_counts[sp] = src_counts.get(sp, 0) + t.get("count", 1)
        if src_counts:
            source_principale = max(src_counts, key=src_counts.get)

    date_analyse = r.get("date_analyse", "")

    # KPI grid (6 tuiles)
    kpi_grid = html.Div([
        # html.Div([
        #     html.Div("Taux moyen", className="hist-kpi-lbl"),
        #     html.Div(f"{taux_moyen}%", className="hist-kpi-val", style={"color": "#d97706"}),
        #     html.Div("sur les déclenchements", className="hist-kpi-sub"),
        # ], className="hist-kpi-tile"),

        html.Div([
            html.Div("Signaux reçus", className="hist-kpi-lbl"),
            html.Div(str(vol_pondere), className="hist-kpi-val", style={"color": "#e8384f"}),
            html.Div([
                html.Span(
                    f"{vol_neg_display} client{'s' if vol_neg_display != 1 else ''} unique{'s' if vol_neg_display != 1 else ''}",
                    style={"fontSize": "10px", "background": "var(--stat-bg)",
                           "color": "var(--text-secondary)", "padding": "2px 7px",
                           "borderRadius": "8px", "border": "1px solid var(--border-color)",
                           "marginRight": "4px", "whiteSpace": "nowrap"}),
                html.Span(f"+{doublons} répét.",
                          style={"fontSize": "10px", "background": "rgba(245,158,11,0.12)",
                                 "color": "#d97706", "padding": "2px 7px",
                                 "borderRadius": "8px",
                                 "border": "1px solid rgba(245,158,11,0.25)",
                                 "whiteSpace": "nowrap"}) if doublons > 0 else None,
            ], style={"display": "flex", "alignItems": "center",
                      "flexWrap": "wrap", "gap": "4px", "marginTop": "4px"}),
        ], className="hist-kpi-tile"),

        html.Div([
            html.Div("Taux négatif moyen", className="hist-kpi-lbl"),
            html.Div(f"{taux_moyen}%", className="hist-kpi-val",
                     style={"color": "#d97706" if taux_moyen < 90 else "#e8384f"}),
            html.Div("au moment du déclenchement", className="hist-kpi-sub"),
        ], className="hist-kpi-tile"),

        html.Div([
            html.Div("Heure de pic", className="hist-kpi-lbl"),
            html.Div(heure_pic_val, className="hist-kpi-val"),
            html.Div(f"Durée : {duree_txt}", className="hist-kpi-sub"),
        ], className="hist-kpi-tile"),

        html.Div([
            html.Div("Source principale", className="hist-kpi-lbl"),
            html.Div(source_principale if source_principale != "—" else "—",
                     className="hist-kpi-val", style={"color": "#185FA5", "fontSize": "16px"}),
            html.Div(f"{sources_detail.get(source_principale, 0)} signaux"
                     if sources_detail else "—", className="hist-kpi-sub"),
        ], className="hist-kpi-tile"),

        html.Div([
            html.Div("Thèmes actifs", className="hist-kpi-lbl"),
            html.Div(str(len(themes_list)) if themes_list else "—", className="hist-kpi-val"),
            html.Div("simultanés", className="hist-kpi-sub"),
        ], className="hist-kpi-tile"),
    ], className="hist-kpi-grid")

    # Barre sources
    sources_bars_rows = []
    if sources_detail:
        total_src = sum(sources_detail.values()) or 1
        for src, cnt in sorted(sources_detail.items(), key=lambda x: -x[1])[:4]:
            pct = round(cnt / total_src * 100)
            sources_bars_rows.append(html.Div([
                html.Span(src, style={"fontSize": "12px", "color": "var(--text-primary)",
                                      "minWidth": "75px", "flexShrink": "0"}),
                html.Div([html.Div(style={"height": "5px", "width": f"{pct}%",
                                          "background": "linear-gradient(90deg, #e8384f, #f59e0b)",
                                          "borderRadius": "3px"})],
                         style={"flex": "1", "background": "var(--border-color)",
                                "borderRadius": "3px", "margin": "0 10px",
                                "height": "5px", "alignSelf": "center"}),
                html.Span(f"{cnt} signaux ({pct}%)",
                          style={"fontSize": "11px", "color": "var(--text-secondary)",
                                 "minWidth": "100px", "textAlign": "right", "flexShrink": "0"}),
            ], style={"display": "flex", "alignItems": "center", "padding": "5px 0"}))

    sources_section = html.Div([
        html.Div("Répartition sources (signaux reçus)", style={
            "fontSize": "11px", "color": "var(--text-secondary)", "marginTop": "20px",
            "textTransform": "uppercase", "letterSpacing": "0.5px",
            "fontWeight": "600", "marginBottom": "8px"}),
        html.Div([
            html.Span(style={"display": "inline-block", "width": "8px", "height": "8px",
                            "borderRadius": "50%",
                            "background": "linear-gradient(135deg,#e8384f,#f59e0b)",
                            "marginRight": "4px"}),
            html.Span("signaux = SUM(fréquence) — inclut les répétitions",
                      style={"fontSize": "10px", "color": "var(--text-secondary)"}),
        ], style={"marginBottom": "8px"}),
        html.Div(sources_bars_rows),
    ], style={"background": "var(--stat-bg)", "borderRadius": "10px",
              "padding": "12px 16px", "margin": "0 20px 12px",
              "border": "1px solid var(--border-color)"}) if sources_bars_rows else None

    # Timeline
    all_evts = sorted(r.get("declenchements", []),
                      key=lambda d: d.get("timestamp", d.get("heure", "")))
    tl_events = []
    for d in all_evts:
        taux_v = d.get("taux", 0)
        vol_v  = d.get("volume", 0)
        note = f"Taux {taux_v}% · {vol_v} clients négatifs" if taux_v else "—"
        tl_events.append(_tl_event(
            heure=d.get("heure", "—"), action=d.get("action", "DÉCLENCHÉE"),
            theme=d.get("theme", ""), note=note))
    if not tl_events:
        tl_events = [html.Div("Aucun déclenchement enregistré",
                               style={"fontSize": "12px", "color": "var(--text-secondary)",
                                      "padding": "8px 0"})]

    # Blocs par thème
    theme_blocks = []
    for t in themes_list[:20]:
        tl           = t.get("label", "?")
        src_t        = t.get("source_principale", source_principale)
        signal_theme = t.get("signal_theme", t.get("count", 0))
        count_unique = t.get("count", 0)

        evts_theme = sorted(
            [d for d in r.get("declenchements", []) if d.get("theme") == tl],
            key=lambda d: d.get("timestamp", d.get("heure", "")))
        nb_declenchements = sum(
            1 for d in evts_theme
            if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE"))

        rows_html = []
        premier_decl_theme = next(
            (d for d in evts_theme
             if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")), None)
        if premier_decl_theme:
            rows_html.append(html.Div([
                html.Span(premier_decl_theme.get("heure", "—"), className="hist-tb-time"),
                html.Span("Déclenchée", style={"background": "rgba(232,56,79,.12)",
                                               "color": "#c0152a", "padding": "2px 8px",
                                               "borderRadius": "20px", "fontSize": "10px",
                                               "fontWeight": "500", "flexShrink": "0"}),
                html.Span(
                    f"Taux {premier_decl_theme.get('taux', 0)}% · "
                    f"{signal_theme} signaux · {count_unique} client{'s' if count_unique != 1 else ''}",
                    className="hist-tb-note"),
                html.Span(
                    [html.I(className="fas fa-share-nodes",
                            style={"marginRight": "3px", "fontSize": "9px"}), src_t],
                    style={"fontSize": "10px", "background": "rgba(0,48,135,0.08)",
                           "color": "var(--text-secondary)", "padding": "2px 6px",
                           "borderRadius": "8px", "marginLeft": "auto", "flexShrink": "0",
                           "border": "1px solid rgba(0,48,135,0.15)"}),
            ], className="hist-tb-row", style={"flexWrap": "wrap", "gap": "4px"}))

        dernier_arret = next(
            (d for d in reversed(evts_theme)
             if d.get("action", "").upper() in ("ARRÊT", "ARRET")), None)
        if dernier_arret:
            rows_html.append(html.Div([
                html.Span(dernier_arret.get("heure", "—"), className="hist-tb-time"),
                html.Span("Arrêt", style={"background": "rgba(0,168,84,.12)", "color": "#007a3d",
                                          "padding": "2px 8px", "borderRadius": "20px",
                                          "fontSize": "10px", "fontWeight": "500", "flexShrink": "0"}),
                html.Span(
                    f"Taux {dernier_arret.get('taux', 0)}% · {dernier_arret.get('volume', 0)} signaux",
                    className="hist-tb-note"),
            ], className="hist-tb-row"))

        if not rows_html:
            rows_html = [html.Div("Aucun événement", className="hist-tb-row")]

        taux_t = t.get("_first_taux",
                        premier_decl_theme.get("taux", 0) if premier_decl_theme else r["taux_max"])
        theme_blocks.append(_theme_block(tl, nb_declenchements, taux_t, signal_theme, rows_html, src_t))

    return html.Div(id=modal_id, className="hist-modal-overlay", children=[
        html.Div(className="hist-modal-shell", children=[
            html.Div([
                html.Div([
                    html.Div(style={"width": "4px", "height": "44px", "borderRadius": "2px",
                                    "flexShrink": "0", "background": strip_color,
                                    "marginRight": "12px", "alignSelf": "center"}),
                    html.Div(style={"width": "10px", "height": "10px", "borderRadius": "50%",
                                    "background": strip_color,
                                    "boxShadow": f"0 0 0 3px {'rgba(232,56,79,0.15)' if is_active else 'rgba(0,168,84,0.15)'}",
                                    "flexShrink": "0", "marginRight": "10px"}),
                    html.Div([
                        html.Div(f"Alerte du {r['date_str']}", className="hist-modal-title"),
                        html.Div(sub_txt, className="hist-modal-sub"),
                    ]),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Button("✕", className="hist-modal-close",
                            **{"data-hist-close": modal_id}, n_clicks=0),
            ], className="hist-modal-hdr"),

            kpi_grid,
            sources_section,

            html.Div([
                html.Button("Chronologie", className="hist-tab-btn hist-tab-on",
                            id={"type": "hist-tab-btn", "modal": modal_id, "tab": "chron"}, n_clicks=0),
                html.Button("Par thème", className="hist-tab-btn",
                            id={"type": "hist-tab-btn", "modal": modal_id, "tab": "theme"}, n_clicks=0),
            ], className="hist-tab-bar"),

            html.Div([
                html.Div(
                    html.Div([html.Div(className="hist-tl-line")] + tl_events,
                             className="hist-timeline"),
                    id={"type": "hist-panel", "modal": modal_id, "tab": "chron"},
                    **{"data-tab": "chron"}, style={"display": "block"}),
                html.Div(theme_blocks,
                         id={"type": "hist-panel", "modal": modal_id, "tab": "theme"},
                         **{"data-tab": "theme"}, style={"display": "none"}),
            ], className="hist-modal-body"),

            html.Div([
                html.Span(f"Analysé le {date_analyse}" if date_analyse else "",
                          className="hist-foot-note"),
                html.Button("Fermer", className="hist-close-btn",
                            **{"data-hist-close": modal_id}, n_clicks=0),
            ], className="hist-modal-foot"),
        ]),
    ])

def _build_alert_card(r, idx):
    is_active  = (r["statut"] == "EN COURS")
    modal_id   = f"hist-pm-{idx}"

    # Récupérer les seuils
    cfg.load_seuils_from_db()
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR

    # Récupérer les thèmes et filtrer selon le seuil
    themes_list = r.get("themes_detaille", [])
    
    # ✅ FILTRAGE : Ne garder que les thèmes qui dépassent SEUIL_VOLUME_JOUR
    themes_filtres = [
        t for t in themes_list 
        if t.get("signal_theme", t.get("count", 0)) >= SEUIL_VOLUME_JOUR
    ]

    # Calcul taux moyen (uniquement sur thèmes filtrés)
    taux_values = [
        d.get("taux", 0)
        for d in r.get("declenchements", [])
        if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")
        and d.get("taux", 0) > 0
        and d.get("theme") in [t.get("label") for t in themes_filtres]
    ]
    taux_affiche = round(sum(taux_values) / len(taux_values), 1) if taux_values else r.get("taux_max", 0)
    taux_color   = "#e8384f" if taux_affiche >= 70 else "#f59e0b"

    # Volumes (uniquement sur thèmes filtrés)
    vol_neg_filtre = sum(t.get("count", 0) for t in themes_filtres)
    vol_pondere_filtre = sum(t.get("signal_theme", t.get("count", 0)) for t in themes_filtres)
    vol_total = r.get("volume_total", 0)
    doublons = vol_pondere_filtre - vol_neg_filtre

    # ✅ PILLS : uniquement les thèmes filtrés
    pills = []
    for t in themes_filtres[:3]:
        label = t.get("label", "?")
        signal = t.get("signal_theme", t.get("count", 0))
        pills.append(html.Span(f"{label} ({signal})", className="hist-tpill"))
    
    if len(themes_filtres) > 3:
        pills.append(_tpill_more(len(themes_filtres) - 3))
    
    if not pills:
        pills = [_tpill(r.get("theme", "—"))]

    hours_sub = (f"Pic {r.get('heure_pic','—')} → Arrêt {r['heure_arret']}"
                 if r.get("heure_arret") else f"Pic à {r.get('heure_pic','—')}")

    status_badge = html.Span([
        html.Span(className=f"hist-sb-dot {'hist-dot-active' if is_active else 'hist-dot-done'}"),
        "En cours" if is_active else "Terminée",
    ], className=f"hist-sb {'hist-sb-active' if is_active else 'hist-sb-done'}")

    # Source principale (basée sur thèmes filtrés)
    src_principale = r.get("source_principale", "")
    if not src_principale or src_principale == "—":
        src_counts = {}
        for t in themes_filtres:
            sp = t.get("source_principale", "")
            if sp and sp != "—":
                src_counts[sp] = src_counts.get(sp, 0) + t.get("signal_theme", t.get("count", 1))
        if src_counts:
            src_principale = max(src_counts, key=src_counts.get)

    # Construction de la carte
    card = html.Div([
        html.Div([
            html.Div(className=f"hist-card-strip {'hist-strip-active' if is_active else 'hist-strip-done'}"),
            html.Div([
                html.Div([
                    html.Div(r["date_str"], className="hist-date-main"),
                    html.Div(hours_sub, className="hist-date-sub"),
                    html.Div(
                        [html.I(className="fas fa-share-nodes",
                                style={"marginRight": "4px", "fontSize": "9px"}),
                         src_principale or "—"],
                        style={"fontSize": "10px", "color": "var(--text-secondary)",
                               "marginTop": "4px", "display": "flex", "alignItems": "center"}
                    ) if src_principale else None,
                ], className="hist-date-col"),
                html.Div(className="hist-divider"),
                html.Div(pills, className="hist-themes-col"),
                html.Div(className="hist-divider"),
                html.Div([
                    html.Div([
                        html.Div(f"{taux_affiche}%", className="hist-stat-val",
                                 style={"color": taux_color}),
                        html.Div("Taux moyen", className="hist-stat-lbl"),
                    ], className="hist-stat"),
                    html.Div([
                        html.Div(str(vol_pondere_filtre), className="hist-stat-val",
                                 style={"color": "#e8384f"}),
                        html.Div("Signaux reçus", className="hist-stat-lbl"),
                        # html.Div([
                        #     html.Span(f"{vol_neg_filtre} clients",
                        #               style={"fontSize": "9px", "background": "var(--stat-bg)",
                        #                      "color": "var(--text-secondary)", "padding": "1px 5px",
                        #                      "borderRadius": "6px",
                        #                      "border": "1px solid var(--border-color)",
                        #                      "marginRight": "3px"}),
                        #     html.Span(f"+{doublons} rép." if doublons > 0 else "",
                        #               style={"fontSize": "9px",
                        #                      "background": "rgba(245,158,11,0.1)",
                        #                      "color": "#f59e0b", "padding": "1px 5px",
                        #                      "borderRadius": "6px",
                        #                      "border": "1px solid rgba(245,158,11,0.2)"
                        #                      }) if doublons > 0 else None,
                        # ], style={"display": "flex", "alignItems": "center",
                        #           "flexWrap": "wrap", "gap": "2px", "marginTop": "3px"}),
                    ], className="hist-stat"),
                ], className="hist-stats-col"),
                html.Div(className="hist-divider"),
                html.Div(status_badge, style={"flexShrink": "0"}),
                html.Button(
                    [html.I(className="fas fa-eye",
                            style={"fontSize": "12px", "marginRight": "5px"}), "Détails"],
                    className="hist-detail-btn",
                    **{"data-hist-open": modal_id}, n_clicks=0),
            ], className="hist-card-body"),
        ], className="hist-card-inner"),
    ], className=f"hist-alert-card {'hist-card-active' if is_active else ''}")

    # ── Construction du modal ────────────────────────────────────────────────
    if is_active:
        alarme_fraiche = get_alarme_journaliere()
        themes_frais   = alarme_fraiche.get("themes_crise", [])
        
        # ✅ Filtrer les thèmes frais selon le seuil
        themes_frais_filtres = [
            t for t in themes_frais 
            if t.get("signal_theme", t.get("count", 0)) >= SEUIL_VOLUME_JOUR
        ]
        
        decls_existants = r.get("declenchements", [])
        heure_now = now_local().strftime("%Hh%M")
        taux_frais = alarme_fraiche.get("taux_auj", 0)
        vol_frais = alarme_fraiche.get("volume_negatif", 0)
        vol_pondere_frais = alarme_fraiche.get("volume_pondere", vol_frais)
        src_frais = alarme_fraiche.get("source_principale", "—")
        decls_frais = list(decls_existants)

        labels_decls_existants = {
            d.get("theme") for d in decls_existants
            if d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")
        }

        themes_detaille_frais = []
        for tf in themes_frais_filtres:
            label_f   = tf.get("label")
            src_theme = tf.get("source_principale", src_frais)
            decl_ex = next(
                (d for d in decls_existants
                 if d.get("theme") == label_f
                 and d.get("action", "").upper() in ("DÉCLENCHÉE", "DECLENCHEE", "DÉCLENCHEE")),
                None
            )
            heure_decl = decl_ex.get("heure", heure_now) if decl_ex else heure_now
            taux_decl = decl_ex.get("taux", taux_frais) if decl_ex else taux_frais

            if label_f not in labels_decls_existants:
                decls_frais.append({
                    "heure": heure_now, "action": "DÉCLENCHÉE",
                    "taux": taux_frais, "volume": tf.get("count", vol_frais),
                    "theme": label_f, "timestamp": now_local().isoformat()
                })

            themes_detaille_frais.append({
                **tf, "_first_taux": taux_decl, "_first_heure": heure_decl,
                "source_principale": src_theme, "heure_arret": None
            })

        # Garder les thèmes arrêtés depuis le store (filtrés)
        labels_frais = {t.get("label") for t in themes_frais_filtres}
        for t_ex in r.get("themes_detaille", []):
            if t_ex.get("label") not in labels_frais and t_ex.get("signal_theme", t_ex.get("count", 0)) >= SEUIL_VOLUME_JOUR:
                themes_detaille_frais.append(t_ex)

        r_modal = {
            **r,
            "date_analyse":      now_local().strftime("%d/%m/%Y à %H:%M"),
            "themes_detaille":   themes_detaille_frais,
            "themes_crise":      themes_detaille_frais,
            "sources_detail":    alarme_fraiche.get("sources_detail", {}),
            "source_principale": src_frais,
            "volume_negatif":    vol_frais,
            "volume_pondere":    vol_pondere_frais,
            "volume_total":      alarme_fraiche.get("volume_total", 0),
            "taux_max":          max(r.get("taux_max", 0), taux_frais),
            "declenchements":    decls_frais,
        }
    else:
        r_modal = {**r, "date_analyse": r.get("date_analyse", "")}

    modal = _build_modal(r_modal, modal_id)
    return card, modal
def make_historique_alertes_with_current(seuil_taux=60.0, seuil_volume=30, stopped_alarmes=None):
    cfg.load_seuils_from_db()
    seuil_taux      = cfg.SEUIL_TAUX_JOUR
    seuil_volume    = cfg.SEUIL_VOLUME_JOUR
    stopped_alarmes = stopped_alarmes or []
    alarme_actuelle = get_alarme_journaliere()
    aujourdhui_iso  = now_local().strftime("%Y-%m-%d")
    aujourdhui_str  = now_local().strftime("%d/%m/%Y")

    rows = []

    if alarme_actuelle["alarme_active"]:
        entree_existing = next(
            (a for a in stopped_alarmes
             if a.get("date_iso") == aujourdhui_iso and a.get("statut") == "EN COURS"), None)
        if entree_existing:
            themes_frais  = alarme_actuelle.get("themes_crise", [])
            sources_frais = alarme_actuelle.get("sources_detail", {})
            src_frais     = alarme_actuelle.get("source_principale", "—")
            themes_ex        = entree_existing.get("themes_detaille", [])
            themes_ex_labels = {t.get("label") for t in themes_ex}
            for tf in themes_frais:
                label_f = tf.get("label")
                if label_f not in themes_ex_labels:
                    themes_ex.append({
                        **tf, "_first_taux": alarme_actuelle.get("taux_auj", 0),
                        "_first_heure": entree_existing.get("heure_pic", "—"),
                        "source_principale": tf.get("source_principale", src_frais),
                        "heure_arret": None})
            entree_existing["themes_detaille"]   = themes_ex
            entree_existing["themes_crise"]      = themes_ex
            entree_existing["sources_detail"]    = sources_frais
            entree_existing["source_principale"] = src_frais
            entree_existing["volume_total"]      = alarme_actuelle.get("volume_total", 0)
            entree_existing["volume_negatif"]    = alarme_actuelle.get("volume_negatif", 0)
            entree_existing["volume_pondere"]    = alarme_actuelle.get("volume_pondere", 0)
            entree_existing["taux_max"]          = max(entree_existing.get("taux_max", 0),
                                                       alarme_actuelle.get("taux_auj", 0))
            rows.append({**entree_existing, "statut": "EN COURS"})
        else:
            themes_list = alarme_actuelle.get("themes_crise", [])
            theme_label = themes_list[0]["label"] if themes_list else "Multiple"
            rows.append({
                "date_str":          aujourdhui_str,
                "date_iso":          aujourdhui_iso,
                "heure_pic":         aujourdhui_str,
                "heure_arret":       None,
                "theme":             theme_label,
                "taux_max":          alarme_actuelle["taux_auj"],
                "volume_negatif":    alarme_actuelle["volume_negatif"],
                "volume_pondere":    alarme_actuelle.get("volume_pondere", 0),
                "volume_total":      alarme_actuelle["volume_total"],
                "statut":            "EN COURS",
                "declenchements":    [],
                "themes_detaille":   themes_list,
                "date_analyse":      now_local().strftime("%d/%m/%Y à %H:%M"),
                "source_principale": alarme_actuelle.get("source_principale", "—"),
                "sources_detail":    alarme_actuelle.get("sources_detail", {}),
            })

    for a in stopped_alarmes:
        if alarme_actuelle["alarme_active"] and a.get("date_iso") == aujourdhui_iso:
            continue
        taux_max   = a.get("taux_max", a.get("taux_negatif", 0))
        volume_neg = a.get("volume_negatif", a.get("volume_max", 0))
        if taux_max == 0 and volume_neg == 0:
            continue
        rows.append({
            "date_str":          a.get("date_str", a.get("date_iso", "—")),
            "date_iso":          a.get("date_iso", ""),
            "heure_pic":         a.get("heure_pic", "—"),
            "heure_arret":       a.get("heure_arret", None),
            "theme":             a.get("theme_principal", "—"),
            "taux_max":          taux_max,
            "volume_negatif":    volume_neg,
            "volume_pondere":    a.get("volume_pondere", volume_neg),
            "volume_total":      a.get("volume_total", 0),
            "statut":            "TERMINÉE",
            "declenchements":    a.get("declenchements", []),
            "themes_detaille":   a.get("themes_detaille", a.get("themes_crise", [])),
            "date_analyse":      a.get("date_analyse", ""),
            "source_principale": a.get("source_principale", "—"),
            "sources_detail":    a.get("sources_detail", {}),
        })

    if not rows:
        return html.Div([
            html.Div([
                html.Div([
                    html.Div(html.I(className="fas fa-clock-rotate-left",
                                   style={"fontSize": "12px"}), className="card-icon hist-icon"),
                    html.Span("HISTORIQUE DES ALERTES", className="card-title"),
                ], className="card-header"),
            ]),
            html.Div(
                html.Span("Aucune alerte enregistrée sur les 30 derniers jours",
                          style={"color": "#64748b", "fontSize": "13px", "padding": "24px"}),
                style={"textAlign": "center"},
            ),
        ], className="chart-card hist-zone")

    pairs  = [_build_alert_card(r, i) for i, r in enumerate(rows[:30])]
    cards  = [p[0] for p in pairs]
    modals = [p[1] for p in pairs]

    taux_actuel   = alarme_actuelle.get("taux_auj", 0)
    volume_actuel = alarme_actuelle.get("volume_pondere", alarme_actuelle.get("volume_negatif", 0))

    seuil_badge = html.Div([
        html.I(className="fas fa-chart-line", style={"fontSize": "10px", "marginRight": "4px"}),
        html.Span(f"Seuil taux: {seuil_taux}%"),
    ], style={"display": "inline-flex", "alignItems": "center",
              "background": "rgba(0,48,135,0.08)", "borderRadius": "20px",
              "padding": "4px 12px", "fontSize": "11px",
              "border": "1px solid rgba(0,48,135,0.15)", "marginRight": "10px"})

    volume_badge = html.Div([
        html.I(className="fas fa-signal", style={"fontSize": "10px", "marginRight": "4px"}),
        html.Span(f"Seuil signal: {seuil_volume}", style={"fontWeight": "600"}),
    ], style={"display": "inline-flex", "alignItems": "center",
              "background": "rgba(0,48,135,0.08)", "borderRadius": "20px",
              "padding": "4px 12px", "fontSize": "11px",
              "border": "1px solid rgba(0,48,135,0.15)"})

    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div(html.I(className="fas fa-clock-rotate-left",
                                   style={"fontSize": "12px"}), className="card-icon hist-icon"),
                    html.Span("HISTORIQUE DES ALERTES", className="card-title"),
                    html.Div([seuil_badge, volume_badge],
                             style={"display": "flex", "alignItems": "center",
                                    "flexWrap": "wrap", "gap": "8px", "marginLeft": "12px"}),
                    html.Span(f"{len(rows)} événement(s) — 30 derniers jours",
                              className="hist-subtitle", style={"marginLeft": "auto"}),
                ], className="card-header", style={"flex": "1"}),
            ], style={"display": "flex", "alignItems": "center",
                      "justifyContent": "space-between", "flexWrap": "wrap"}),
        ]),
        html.Div(cards, style={"marginTop": "12px"}),
        html.Div(modals, id="hist-modals-container"),
    ], className="chart-card hist-zone", style={"minHeight": "auto", "maxHeight": "none"})


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SCORE SANTÉ
# ═══════════════════════════════════════════════════════════════════════════════

def compute_health_score(stats):
    if stats["total"] == 0:
        return 0, "N/A", NEUTRAL
    s     = max(0, (stats["avg_score"] + 1) / 2 * 100)
    n     = max(0, 100 - stats["taux_negatif"])
    f     = max(0, 100 - stats["taux_frustration"] * 2)
    score = round(s * 0.4 + n * 0.4 + f * 0.2)
    if score >= 70:
        return score, "Satisfaisant", GREEN
    elif score >= 45:
        return score, "Modéré", ORANGE
    return score, "Critique", RED


# ═══════════════════════════════════════════════════════════════════════════════
# 6. GRAPHIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def _colors(theme):
    if theme == "dark":
        return {"bg": "#141c2e", "paper_bg": "#141c2e", "text": "#dce8f5",
                "grid": "#1e2d47", "axis_line": "#1e2d47",
                "primary": "#4a80d4", "secondary": "#6c8dcc",
                "success": "#2ecc71", "warning": "#f39c12",
                "danger": "#f06070", "neutral": "#607b99",
                "bar_fill": "rgba(74,128,212,0.15)"}
    return {"bg": "#ffffff", "paper_bg": "#ffffff", "text": "#1a2a4a",
            "grid": "#e8edf5", "axis_line": "#e8edf5",
            "primary": BLUE, "secondary": BLUE_MID,
            "success": GREEN, "warning": ORANGE,
            "danger": RED, "neutral": NEUTRAL,
            "bar_fill": "rgba(0,48,135,0.10)"}

def _base_layout(c, height, margin=None):
    m = margin or dict(l=10, r=10, t=20, b=10)
    return dict(plot_bgcolor=c["bg"], paper_bgcolor=c["paper_bg"],
                font=dict(color=c["text"], family="'Plus Jakarta Sans', sans-serif", size=9),
                height=height, margin=m)

def make_sentiment_donut(stats, theme="light"):
    c = _colors(theme)
    if stats["total"] == 0:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 240))
        return fig
    labels  = ["Négatif", "Positif", "Neutre"]
    values  = [stats["negatifs"], stats["positifs"], stats["neutres"]]
    palette = [c["danger"], c["success"], c["neutral"]]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.64,
        marker=dict(colors=palette, line=dict(color=c["bg"], width=3)),
        textinfo="percent", textfont=dict(size=11, color="white"),
        hovertemplate="%{label} : <b>%{value:,}</b> (%{percent})<extra></extra>",
        sort=False, pull=[0.06, 0, 0],
    ))
    avg_col = (c["success"] if stats["avg_score"] >= -0.2
               else c["warning"] if stats["avg_score"] >= -0.5
               else c["danger"])
    layout = _base_layout(c, 240, margin=dict(l=10, r=10, t=20, b=10))
    layout.update(showlegend=False, annotations=[
        dict(text=f"<b>{stats['taux_negatif']}%</b>", x=0.5, y=0.60,
             font=dict(size=22, color=c["danger"]), showarrow=False),
        dict(text="taux négatif", x=0.5, y=0.44,
             font=dict(size=10, color=c["text"]), showarrow=False),
        dict(text=f"Score : {stats['avg_score']:+.2f}", x=0.5, y=0.30,
             font=dict(size=9, color=avg_col), showarrow=False),
    ])
    fig.update_layout(**layout)
    return fig

def make_theme_chart(theme_data, theme="light"):
    c = _colors(theme)
    if not theme_data:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 225, margin=dict(l=0, r=0, t=0, b=0)))
        return fig
    top     = theme_data[:5]
    labels  = [d["label"] for d in top]
    volumes = [d["total"]  for d in top]
    pct_n   = [d["pct_negatif"] for d in top]
    bar_colors_light = [BLUE, "#1a4fa0", "#2d66bb", "#4a80d4", "#6699e8"]
    bar_colors_dark  = ["#4a80d4", "#5a8ed8", "#6a9cdc", "#7aaae0", "#8ab8e4"]
    bar_colors = bar_colors_dark[:len(labels)] if theme == "dark" else bar_colors_light[:len(labels)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=volumes, orientation='h',
        marker=dict(color=bar_colors, line=dict(width=0), cornerradius=6),
        text=[f"{v:,}" for v in volumes], textposition='inside',
        textfont=dict(size=10, color='white', weight='bold'),
        hovertemplate='<b>%{y}</b><br>Volume: <b>%{x:,}</b><br>Taux négatif: <b>%{customdata}%</b><extra></extra>',
        customdata=pct_n, cliponaxis=False, width=0.68,
    ))
    max_vol = max(volumes) if volumes else 1
    layout  = _base_layout(c, 225, margin=dict(l=10, r=10, t=5, b=15))
    layout.update(
        xaxis=dict(showgrid=True, gridcolor=c["grid"], tickformat=',d',
                   tickfont=dict(size=8, color=c["text"]), range=[0, max_vol * 1.1],
                   zeroline=False, showline=True, linecolor=c["grid"]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, color=c["text"]),
                   autorange='reversed', showline=False),
        showlegend=False, bargap=0.32)
    fig.update_layout(**layout)
    return fig

def make_evolution_chart(evol_data, theme="light"):
    c = _colors(theme)
    if not evol_data:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée d'évolution", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 265))
        return fig
    mois       = [d["mois"]       for d in evol_data]
    avg_scores = [d["avg_score"]  for d in evol_data]
    volumes    = [d["total"]      for d in evol_data]
    taux_neg   = [d["taux_negatif"] for d in evol_data]
    fig        = go.Figure()
    fig.add_trace(go.Bar(x=mois, y=volumes, name="Volume",
                         marker=dict(color=c["bar_fill"], line=dict(width=0)), yaxis="y2",
                         hovertemplate="<b>%{x}</b><br>Volume : <b>%{y:,}</b><extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color=c["neutral"], opacity=0.4)
    r, g, b_ = int(c["primary"][1:3], 16), int(c["primary"][3:5], 16), int(c["primary"][5:7], 16)
    fig.add_trace(go.Scatter(
        x=mois, y=avg_scores, name="Score moyen",
        mode="lines+markers+text",
        line=dict(color=c["primary"], width=3),
        fill="tozeroy", fillcolor=f"rgba({r},{g},{b_},0.06)",
        marker=dict(size=12, color=c["primary"], symbol="circle",
                    line=dict(color=c["bg"], width=2.5)),
        text=[f"{s:+.3f}" for s in avg_scores],
        textposition="top center", textfont=dict(size=10, color=c["primary"]),
        hovertemplate="<b>%{x}</b><br>Score : <b>%{y:.3f}</b><extra></extra>",
    ))
    dr, dg, db_ = int(c["danger"][1:3], 16), int(c["danger"][3:5], 16), int(c["danger"][5:7], 16)
    for m, tn in zip(mois, taux_neg):
        fig.add_annotation(x=m, y=-0.92, text=f"{tn}%", showarrow=False,
                           font=dict(size=8.5, color=c["danger"]), yref="y",
                           bgcolor=f"rgba({dr},{dg},{db_},0.10)",
                           bordercolor=f"rgba({dr},{dg},{db_},0.25)",
                           borderwidth=1, borderpad=3)
    layout = _base_layout(c, 265, margin=dict(l=50, r=55, t=32, b=42))
    layout.update(
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=c["text"]),
                   type="category", linecolor=c["axis_line"]),
        yaxis=dict(showgrid=True, gridcolor=c["grid"], title="Score sentiment",
                   tickformat=".2f", range=[-1.1, 0.4], title_font=dict(size=8),
                   zeroline=True, zerolinecolor=c["grid"],
                   tickfont=dict(size=9, color=c["text"])),
        yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False,
                    tickfont=dict(size=8, color=c["neutral"]),
                    title_font=dict(size=8, color=c["neutral"])),
        legend=dict(orientation="h", x=0, y=1.06, font=dict(size=9, color=c["text"]),
                    bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified", bargap=0.35)
    fig.update_layout(**layout)
    return fig

def make_langue_pie(theme="light"):
    c         = _colors(theme)
    lang_data = get_langue_stats()
    if not lang_data or lang_data[0]["total"] == 0:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=11, color=c["neutral"]))
        fig.update_layout(**_base_layout(c, 280))
        return fig
    labels = [lang["label"] for lang in lang_data]
    values = [lang["total"] for lang in lang_data]
    pcts   = [lang["pct"]   for lang in lang_data]
    bar_colors_light = [BLUE, "#1a4fa0", "#2d66bb", "#4a80d4", "#6699e8", "#88b2f8"]
    bar_colors_dark  = ["#4a80d4", "#5a8ed8", "#6a9cdc", "#7aaae0", "#8ab8e4", "#9ac6e8"]
    bar_colors = bar_colors_dark[:len(labels)] if theme == "dark" else bar_colors_light[:len(labels)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=values,
        marker=dict(color=bar_colors, line=dict(width=0), cornerradius=12),
        text=[f"{v:,}<br>({p}%)" for v, p in zip(values, pcts)],
        textposition='outside', textfont=dict(size=9, color=c["text"], weight='bold'),
        hovertemplate='<b>%{x}</b><br>Volume: <b>%{y:,}</b><br>Pourcentage: <b>%{customdata}%</b><extra></extra>',
        customdata=pcts, width=0.65,
    ))
    max_val = max(values) if values else 1
    layout  = _base_layout(c, 280, margin=dict(l=20, r=20, t=50, b=60))
    layout.update(
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=c["text"], weight="bold"),
                   type='category', tickangle=-25),
        yaxis=dict(showgrid=True, gridcolor=c["grid"], title="Nombre de commentaires",
                   title_font=dict(size=9, color=c["text"]), tickformat=',d',
                   tickfont=dict(size=9, color=c["text"]), range=[0, max_val * 1.18],
                   zeroline=False, showline=True, linecolor=c["grid"]),
        showlegend=False, bargap=0.3)
    fig.update_layout(**layout)
    return fig

def make_monthly_comparison_card():
    monthly = get_monthly_stats()
    if not monthly:
        return html.Div("Aucune donnée mensuelle disponible.", className="no-data-msg")
    mois_liste = sorted(monthly.keys())
    cards = []
    for i, mois in enumerate(mois_liste):
        d       = monthly[mois]
        is_last = (i == len(mois_liste) - 1)
        if i > 0:
            prev        = monthly[mois_liste[i - 1]]
            delta_score = round(d["avg_score"] - prev["avg_score"], 3)
            delta_neg   = round(d["taux_negatif"] - prev["taux_negatif"], 1)
            ds_color    = GREEN if delta_score > 0 else RED if delta_score < 0 else NEUTRAL
            dn_color    = GREEN if delta_neg < 0 else RED if delta_neg > 0 else NEUTRAL
            ds_icon     = html.I(className="fas fa-arrow-up" if delta_score > 0
                                 else "fas fa-arrow-down" if delta_score < 0 else "fas fa-minus")
            dn_icon     = html.I(className="fas fa-arrow-up" if delta_neg > 0
                                 else "fas fa-arrow-down" if delta_neg < 0 else "fas fa-minus")
            ds_str = f" {abs(delta_score):.3f}" if delta_score != 0 else " stable"
            dn_str = f" {abs(delta_neg):.1f} pts" if delta_neg != 0 else " stable"
        else:
            ds_icon = dn_icon = html.I(className="fas fa-minus")
            ds_str  = dn_str  = " —"
            ds_color = dn_color = NEUTRAL
        avg_col = GREEN if d["avg_score"] >= -0.2 else ORANGE if d["avg_score"] >= -0.5 else RED
        cards.append(html.Div([
            html.Div([html.I(className="fas fa-calendar-alt"), html.Span(mois)],
                     className="monthly-card-title"),
            html.Div([
                html.Span(f"{d['total_reel']:,}".replace(",", "\u202f"), className="monthly-volume"),
                html.Span(" commentaires reçus", className="monthly-unit"),
            ], className="monthly-row"),
            html.Div([
                html.Span("Score", className="monthly-metric-label"),
                html.Span(f"{d['avg_score']:+.3f}", className="monthly-metric-value",
                          style={"color": avg_col}),
                html.Span([ds_icon, html.Span(ds_str)], className="monthly-delta",
                          style={"color": ds_color}),
            ], className="monthly-metric-row"),
            html.Div([
                html.Span("Négatif", className="monthly-metric-label"),
                html.Span(f"{d['taux_negatif']}%", className="monthly-metric-value",
                          style={"color": RED}),
                html.Span([dn_icon, html.Span(dn_str)], className="monthly-delta",
                          style={"color": dn_color}),
            ], className="monthly-metric-row"),
            html.Div([
                html.Span("Positif", className="monthly-metric-label"),
                html.Span(f"{d['taux_satisfaction']}%", className="monthly-metric-value",
                          style={"color": GREEN}),
            ], className="monthly-metric-row"),
        ], className=f"monthly-card {'monthly-card-active' if is_last else ''}"))
    return html.Div([
        html.Div(cards, className="monthly-comparison-grid"),
        html.Div([
            html.I(className="fas fa-arrow-up", style={"color": GREEN, "marginRight": "4px"}),
            html.Span("amélioration  •  "),
            html.I(className="fas fa-arrow-down", style={"color": RED, "marginRight": "4px"}),
            html.Span("dégradation  •  Score > −0.2 = satisfaisant"),
        ], className="monthly-legend"),
    ], style={"height": "100%", "display": "flex", "flexDirection": "column"})


def make_kpi_row(stats):
    cfg.load_seuils_from_db()
    SEUIL_TAUX_JOUR   = cfg.SEUIL_TAUX_JOUR
    SEUIL_NEGATIF     = cfg.SEUIL_NEGATIF
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR
    if stats["total"] == 0:
        return html.Div(html.Div("Aucune donnée disponible", className="kpi-value"),
                        className="kpi-grid")

    total_var = stats.get("total_variation", 0)
    avg_var   = stats.get("avg_score_variation", 0)
    neg_var   = stats.get("negatif_variation", 0)
    has_cmp   = stats.get("has_comparison", False)
    period    = stats.get("period_text", "")

    alarme          = get_alarme_journaliere()
    taux_aujourdhui = alarme["taux_auj"]
    volume_auj      = alarme["volume_pondere"]
    date_aujourdhui = now_local().strftime("%d/%m/%Y")
    taux_vs_hier    = alarme["taux_vs_hier"]

    taux_color = ("#e8384f" if taux_aujourdhui >= SEUIL_TAUX_JOUR
                  else "#f59e0b" if taux_aujourdhui >= 40 else "#00a854")

    def pill(v, positive_is_good=True, suffix="%"):
        if v == 0:
            return html.Span([html.I(className="fas fa-minus-circle",
                                     style={"fontSize": "9px"}), html.Span(" stable")],
                             className="kpi-pill neutral")
        icon = html.I(className="fas fa-arrow-up" if v > 0 else "fas fa-arrow-down",
                      style={"fontSize": "9px"})
        good = (v > 0) if positive_is_good else (v < 0)
        return html.Span([icon, html.Span(f" {abs(v):.1f}{suffix}")],
                         className=f"kpi-pill {'up' if good else 'down'}")

    neutral_pill = html.Span(
        [html.I(className="fas fa-chart-simple", style={"fontSize": "9px"}),
         html.Span(" 1ère période")], className="kpi-pill neutral")

    t_pill  = pill(total_var, True)        if has_cmp else neutral_pill
    av_pill = pill(avg_var, True, " pt")   if has_cmp else neutral_pill
    nv_pill = pill(neg_var, False, " pts") if has_cmp else neutral_pill
    fr_pill = html.Span(
        [html.I(className="fas fa-percent", style={"fontSize": "9px"}),
         html.Span(f" {stats['taux_frustration']}% msgs")], className="kpi-pill neutral")

    if taux_vs_hier > 0:
        taux_pill = html.Span(
            [html.I(className="fas fa-arrow-up", style={"fontSize": "9px"}),
             html.Span(f" {taux_vs_hier:+.1f}% vs hier")], className="kpi-pill down")
    elif taux_vs_hier < 0:
        taux_pill = html.Span(
            [html.I(className="fas fa-arrow-down", style={"fontSize": "9px"}),
             html.Span(f" {taux_vs_hier:+.1f}% vs hier")], className="kpi-pill up")
    else:
        taux_pill = html.Span(
            [html.I(className="fas fa-minus-circle", style={"fontSize": "9px"}),
             html.Span(" stable vs hier")], className="kpi-pill neutral")

    kpi_defs = [
        {"variant": "kpi-blue", "icon": "fas fa-message",
         "label": "TOTAL COMMENTAIRES",
         "value": f"{stats['total_reel']:,}".replace(",", "\u202f"),
         "value_color": None, "pill": t_pill, "period": period if has_cmp else "",
         "tt_title": "Total Commentaires",
         "tt_body": f"Volume réel reçu (doublons inclus via fréquence). "
                    f"Commentaires uniques en base : {stats['total']:,}."},
        {"variant": "kpi-green", "icon": "fas fa-chart-line",
         "label": "SCORE SENTIMENT MOYEN",
         "value": f"{stats['avg_score']:+.2f}",
         "value_color": None, "pill": av_pill, "period": period if has_cmp else "",
         "tt_title": "Score Sentiment Moyen",
         "tt_body": "Score entre -1 (très négatif) et +1 (très positif). > -0.2 = satisfaisant."},
        {"variant": "kpi-red", "icon": "fas fa-face-frown",
         "label": "TAUX NÉGATIF GLOBAL",
         "value": f"{stats['taux_negatif']}%",
         "value_color": None, "pill": nv_pill, "period": period if has_cmp else "",
         "tt_title": "Taux de Commentaires Négatifs",
         "tt_body": "Pourcentage de commentaires classifiés NEGATIF (toute période)."},
        {"variant": "kpi-warning", "icon": "fas fa-calendar-day",
         "label": "TAUX NÉGATIF AUJOURD'HUI",
         "value": f"{taux_aujourdhui}%",
         "value_color": taux_color, "pill": taux_pill, "period": date_aujourdhui,
         "tt_title": "Taux Négatif du Jour",
         "tt_body": (f"Taux de commentaires négatifs des dernières 24h. "
                     f"Seuil critique : {SEUIL_TAUX_JOUR}%. "
                     f"Signal pondéré actuel : {volume_auj} signaux.")},
        {"variant": "kpi-amber", "icon": "fas fa-triangle-exclamation",
         "label": "FRUSTRATIONS DÉTECTÉES",
         "value": f"{stats['frustrations']:,}".replace(",", "\u202f"),
         "value_color": None, "pill": fr_pill, "period": "",
         "tt_title": "Frustrations Détectées",
         "tt_body": (f"Messages avec signaux de frustration forte. "
                     f"Représente {stats['taux_frustration']}% du total.")},
    ]

    return html.Div(html.Div([
        html.Div([
            html.Div([
                html.Div(html.I(className=k["icon"], style={"fontSize": "20px"}),
                         className="kpi-icon-wrap"),
                html.Span(k["label"], className="kpi-label"),
            ], className="kpi-top-row"),
            html.Div(k["value"], className="kpi-value",
                     style={"color": k["value_color"]} if k["value_color"] else {}),
            html.Div(className="kpi-underline"),
            html.Div([
                k["pill"],
                html.Span(k["period"], className="kpi-period") if k["period"] else None,
            ], className="kpi-footer"),
            html.Div([
                html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
                html.Div([
                    html.Div(k["tt_title"], className="tooltip-title"),
                    html.Div(k["tt_body"],  className="tooltip-body"),
                ], className="kpi-card-tooltip"),
            ], className="kpi-tooltip-wrapper"),
        ], className=f"kpi-card {k['variant']}")
        for k in kpi_defs
    ], className="kpi-grid-6"))


def _chart_card_wrap(icon_cls, title, tt_title, tt_body, children, extra_style=None):
    return html.Div([
        html.Div([
            html.Div(html.I(className=icon_cls, style={"fontSize": "14px"}), className="card-icon"),
            html.Span(title, className="card-title"),
            html.Div([
                html.Div(html.I(className="fas fa-circle-info"), className="tooltip-icon"),
                html.Div([
                    html.Div(tt_title, className="tooltip-title"),
                    html.Div(tt_body,  className="tooltip-body"),
                ], className="card-tooltip"),
            ], className="tooltip-wrapper"),
        ], className="card-header"),
        html.Div(children, className="card-content"),
    ], className="chart-card", style=extra_style or {})


# ═══════════════════════════════════════════════════════════════════════════════
# 7. RENDER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def render_dashboard_content(theme="light", user_data=None, stopped_alarmes=None):
    cfg.load_seuils_from_db()
    SEUIL_TAUX_JOUR   = cfg.SEUIL_TAUX_JOUR
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR
    SEUIL_NEGATIF     = cfg.SEUIL_NEGATIF
    stats      = get_filtered_stats(ttl_hash=get_ttl_hash())
    evol       = get_filtered_evol()
    theme_data = get_theme_stats()
    alarme_data = get_alarme_journaliere()

    print(f"🔍 dashboard - user_data: {user_data}")
    print(f"📊 Taux aujourd'hui: {alarme_data['taux_auj']}% | Signal: {alarme_data.get('volume_pondere',0)}")
    print(f"🚨 Alarme active: {alarme_data['alarme_active']}")

    if stats["total"] == 0:
        content = html.Div(className="dashboard-container", children=[
            html.Div([
                html.I(className="fas fa-database",
                       style={"fontSize": "48px", "color": NEUTRAL}),
                html.H3("Aucune donnée disponible",
                        style={"marginTop": "20px", "fontWeight": "700"}),
                html.P("Vérifiez votre connexion MongoDB ou importez des données.",
                       style={"color": NEUTRAL, "fontSize": "14px"}),
            ], style={"textAlign": "center", "padding": "80px 20px",
                      "background": "var(--bg-card)", "borderRadius": "20px"}),
        ])
        return make_page_layout("dashboard", "Tableau de Bord Satisfaction Client",
                                "Aucune donnée disponible", content, theme, user_data)

    mois_dispo = sorted(get_monthly_stats().keys())
    period_sub = (
        f"Analyse des commentaires  •  {stats['total_reel']:,} signaux reçus  •  "
        f"{mois_dispo[0] if mois_dispo else ''}  →  {mois_dispo[-1] if mois_dispo else ''}"
    ).replace(",", "\u202f")

    health_score, health_label, health_color = compute_health_score(stats)
    today_date = now_local().strftime("%d/%m/%Y")

    historique_zone = make_historique_alertes_with_current(
        seuil_taux=SEUIL_TAUX_JOUR,
        seuil_volume=SEUIL_VOLUME_JOUR,
        stopped_alarmes=stopped_alarmes or [],
    )

    style_active = {
        "padding": "6px 16px", "borderRadius": "20px", "border": "none",
        "background": BLUE, "color": "white", "cursor": "pointer",
        "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px"}

    style_inactive = {
        "padding": "6px 16px", "borderRadius": "20px",
        "border": f"1px solid {BLUE}", "background": "transparent",
        "color": BLUE, "cursor": "pointer", "fontSize": "12px",
        "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px"}

    content = html.Div(
        className="dashboard-container", **{"data-theme": theme},
        children=[
         html.Div([
            html.Div([
                # ── Gauche : Période d'analyse ────────────────────────────────
                html.Div([
                    html.I(className="far fa-calendar-alt",
                        style={"marginRight": "6px", "color": BLUE}),
                    html.Span("Période d'analyse :",
                      style={"fontSize": "14px", "color": NEUTRAL,
                             "fontWeight": "500", "whiteSpace": "nowrap",
                             "marginRight": "10px"}),
                    html.Button(
                        [html.I(className="fas fa-globe",
                            style={"fontSize": "11px", "marginRight": "6px"}),
                            "Global"],
                            id="btn-periode-global", n_clicks=0,
                            style=style_active),
                    html.Button(
                        [html.I(className="fas fa-calendar-day",
                        style={"fontSize": "11px", "marginRight": "6px"}),
                        "Ce Mois"],
                        id="btn-periode-mois", n_clicks=0,
                        style=style_inactive),
                ], style={"display": "flex", "alignItems": "center",
                          "flex": "1", "gap": "8px"}),

        # ── Droite : date + boutons action (inchangés) ────────────────
                html.Div([
                    html.Div([
                        html.I(className="far fa-calendar-alt",
                            style={"marginRight": "6px"}),
                        html.Span(f"Mise à jour : {today_date}",
                            className="date-text"),
                    ], className="date-badge"),
                    html.Button(
                        [html.I(className="fas fa-sync-alt",
                        style={"marginRight": "8px"}),
                        "Actualiser"],
                        id="refresh-data-btn",
                className="refresh-btn",
                        n_clicks=0,
                        ),
                    html.Button(
                        [html.I(className="fas fa-trash",
                        style={"marginRight": "6px"}),
                        "Vider historique"],
                        id="clear-store-btn",
                        n_clicks=0,
                        style={
                            "background": "#e8384f",
                            "color": "white",
                    "border": "none",
                    "borderRadius": "8px",
                    "padding": "6px 14px",
                    "cursor": "pointer",
                    "fontSize": "12px",
                    "display": "flex",
                    "alignItems": "center",
                },
                    ),
                ], className="header-actions"),

            ], style={
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "space-between",
                    "padding": "10px 20px",
                    "background": "var(--bg-card)",
                    "borderRadius": "14px",
                    "border": "1px solid var(--border-color)",
                    "boxShadow": "0 1px 4px rgba(0,48,135,0.06)",
                    "flexWrap": "wrap", "gap": "10px",
                }),
            ], className="dashboard-header"),

            dcc.Store(id="alarm-active-store", data={"active": alarme_data["alarme_active"]}),
            dcc.Store(id="alarm-trigger-store", data={"show_banner": False}),

            html.Div(id="alerts-container",
                     children=(make_alert_banner(stats) if alarme_data["alarme_active"] else None)),

            (make_alarm_modal(stats) if alarme_data["alarme_active"]
             else html.Div(id="alarm-modal-wrapper", style={"display": "none"})),

            html.Div(id="global-kpi-wrapper", style={"display": "block"},
                     children=[make_kpi_row(stats)]),

            html.Div(id="global-content-wrapper", style={"display": "block"}, children=[
                html.Div([
                    _chart_card_wrap("fas fa-tags", "TOP THÈMES DÉTECTÉS",
                                     "Top Thèmes Détectés",
                                     "Les 5 thèmes les plus fréquents identifiés par le modèle NLP.",
                                     dcc.Graph(figure=make_theme_chart(theme_data, theme),
                                               config={"displayModeBar": False},
                                               style={"width": "100%"})),
                    _chart_card_wrap("fas fa-chart-pie", "RÉPARTITION DES SENTIMENTS",
                                     "Distribution des Sentiments",
                                     "Répartition globale en trois catégories.",
                                     html.Div([
                                         dcc.Graph(figure=make_sentiment_donut(stats, theme),
                                                   config={"displayModeBar": False},
                                                   style={"width": "100%"}),
                                         html.Div([
                                             html.Div([html.Div(className="legend-dot negative"),
                                                       html.Span(f"Négatifs  {stats['negatifs']:,}".replace(",", "\u202f"))],
                                                      className="legend-item"),
                                             html.Div([html.Div(className="legend-dot positive"),
                                                       html.Span(f"Positifs  {stats['positifs']:,}".replace(",", "\u202f"))],
                                                      className="legend-item"),
                                             html.Div([html.Div(className="legend-dot neutral"),
                                                       html.Span(f"Neutres  {stats['neutres']:,}".replace(",", "\u202f"))],
                                                      className="legend-item"),
                                         ], className="donut-legend-horizontal"),
                                     ])),
                    _chart_card_wrap("fas fa-calendar-alt", "COMPARAISON MENSUELLE",
                                     "Comparaison Mensuelle",
                                     "Évolution mois par mois du volume, du score sentiment et du taux négatif.",
                                     make_monthly_comparison_card()),
                ], className="row-3cols"),

                html.Div([
                    _chart_card_wrap("fas fa-chart-line", "ÉVOLUTION MENSUELLE DU SENTIMENT",
                                     "Évolution Mensuelle", "Score sentiment moyen mois par mois.",
                                     dcc.Graph(figure=make_evolution_chart(evol, theme),
                                               config={"displayModeBar": False},
                                               style={"width": "100%"})),
                    html.Div([
                        html.Div([
                            html.Div(html.I(className="fas fa-language",
                                           style={"fontSize": "14px"}), className="card-icon"),
                            html.Span("LANGUES DÉTECTÉES", className="card-title"),
                            html.Div([
                                html.Div(html.I(className="fas fa-circle-info"),
                                         className="tooltip-icon"),
                                html.Div([
                                    html.Div("Langues Détectées", className="tooltip-title"),
                                    html.Div("Répartition des commentaires selon la langue détectée.",
                                             className="tooltip-body"),
                                ], className="card-tooltip"),
                            ], className="tooltip-wrapper"),
                        ], className="card-header"),
                        html.Div([
                            dcc.Graph(figure=make_langue_pie(theme),
                                      config={"displayModeBar": False},
                                      style={"width": "100%", "flex": "1"}),
                            html.Div([html.Div(style={
                                "height": "100%", "width": f"{health_score}%",
                                "borderRadius": "4px",
                                "background": f"linear-gradient(90deg,{health_color},{health_color}99)",
                                "transition": "width 0.8s ease",
                            })], className="health-bar-track"),
                        ], className="card-content",
                           style={"display": "flex", "flexDirection": "column"}),
                    ], className="chart-card"),
                ], className="row-2cols"),

                historique_zone if historique_zone else None,
            ]),

            html.Div(id="periode-kpi-zone"),
            html.Div(id="periode-charts-zone"),
        ],
    )

    return make_page_layout("dashboard", "Tableau de Bord Satisfaction Client",
                            period_sub, content, theme, user_data)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. LAYOUT + CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

layout = html.Div(id="dashboard-wrapper", **{"data-theme": "light"}, children=[
    dcc.Location(id="url"),
    dcc.Store(id="notif-global-store", storage_type='local', data=[]),
    dcc.Store(id="stopped-alarmes-store", storage_type='local', data=[]),
    dcc.Store(id="alarm-trigger-store", data={"show_banner": False}),
    dcc.Store(id="periode-active-store", data="global"),
    dcc.Interval(id="refresh-interval", interval=60_000, n_intervals=0),
    html.Div(id="full-dashboard-layout"),
])

clientside_callback(
    """
    function(n_intervals) {
        function initHistModals() {
            document.querySelectorAll('.hist-modal-overlay').forEach(function(m) {
                if (m._teleported) return;
                m._teleported = true;
                if (m.parentElement !== document.body) document.body.appendChild(m);
            });
            document.querySelectorAll('[data-hist-open]').forEach(function(btn) {
                if (btn._histBound) return;
                btn._histBound = true;
                var mid = btn.getAttribute('data-hist-open');
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    var m = document.getElementById(mid);
                    if (m) { m.classList.add('open'); document.body.style.overflow = 'hidden'; }
                });
            });
            document.querySelectorAll('[data-hist-close]').forEach(function(btn) {
                if (btn._histCloseBound) return;
                btn._histCloseBound = true;
                var mid = btn.getAttribute('data-hist-close');
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    var m = document.getElementById(mid);
                    if (m) { m.classList.remove('open'); document.body.style.overflow = ''; }
                });
            });
            document.querySelectorAll('.hist-modal-overlay').forEach(function(overlay) {
                if (overlay._histOverlayBound) return;
                overlay._histOverlayBound = true;
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) {
                        overlay.classList.remove('open');
                        document.body.style.overflow = '';
                    }
                });
            });
            document.querySelectorAll('.hist-tab-btn').forEach(function(btn) {
                if (btn._histTabBound) return;
                btn._histTabBound = true;
                btn.addEventListener('click', function() {
                    var shell = btn.closest('.hist-modal-shell');
                    if (!shell) return;
                    var txt = btn.textContent.trim().toLowerCase();
                    var tabName = txt.indexOf('chron') !== -1 ? 'chron' : 'theme';
                    shell.querySelectorAll('.hist-tab-btn').forEach(function(b) {
                        b.classList.remove('hist-tab-on');
                    });
                    btn.classList.add('hist-tab-on');
                    var body = shell.querySelector('.hist-modal-body');
                    if (body) {
                        body.querySelectorAll('[data-tab]').forEach(function(panel) {
                            panel.style.display = (panel.getAttribute('data-tab') === tabName) ? 'block' : 'none';
                        });
                    }
                });
            });
            var alarmCloseBtn = document.getElementById('alarm-close-btn');
            if (alarmCloseBtn && !alarmCloseBtn._alarmBtnBound) {
                alarmCloseBtn._alarmBtnBound = true;
                alarmCloseBtn.addEventListener('click', function() {
                    var overlay = document.getElementById('alarm-overlay');
                    if (overlay) overlay.style.display = 'none';
                    var audio = document.getElementById('alarm-audio');
                    if (audio) { audio.pause(); audio.currentTime = 0; }
                });
            }
            if (!window._histEscBound) {
                window._histEscBound = true;
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        document.querySelectorAll('.hist-modal-overlay.open').forEach(function(m) {
                            m.classList.remove('open');
                        });
                        document.body.style.overflow = '';
                        var overlay = document.getElementById('alarm-overlay');
                        if (overlay) overlay.style.display = 'none';
                        var audio = document.getElementById('alarm-audio');
                        if (audio) { audio.pause(); audio.currentTime = 0; }
                    }
                });
            }
        }
        initHistModals();
        setTimeout(initHistModals, 250);
        setTimeout(initHistModals, 700);
        if (!window._histModalObs) {
            window._histModalObs = new MutationObserver(function(muts) {
                var should = false;
                muts.forEach(function(m) {
                    m.addedNodes.forEach(function(n) {
                        if (n.nodeType === 1 && (
                            (n.classList && n.classList.contains('hist-modal-overlay')) ||
                            (n.querySelector && n.querySelector('.hist-modal-overlay')) ||
                            (n.id === 'alarm-modal-wrapper') ||
                            (n.querySelector && n.querySelector('#alarm-close-btn'))
                        )) should = true;
                    });
                });
                if (should) setTimeout(initHistModals, 120);
            });
            window._histModalObs.observe(document.body, {childList: true, subtree: true});
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("full-dashboard-layout", "data-hist-init"),
    Input("refresh-interval", "n_intervals"),
    prevent_initial_call=False,
)


@callback(
    Output("global-notif-badge", "children"),
    Output("global-notif-badge", "style"),
    Output("notification-bell-icon", "className"),
    Input("notif-global-store", "data"),
    prevent_initial_call=False,
)
def update_global_badge_and_icon(stored_notifs):
    cfg.load_seuils_from_db()
    SEUIL_NEGATIF = cfg.SEUIL_NEGATIF
    unread = 0
    if stored_notifs and isinstance(stored_notifs, list):
        unread = sum(1 for n in stored_notifs if n.get("unread", False))
    stats  = get_filtered_stats(ttl_hash=get_ttl_hash())
    alarme = get_alarme_journaliere()
    has_critical     = stats.get("taux_negatif", 0) >= SEUIL_NEGATIF
    has_daily_crisis = alarme.get("alarme_active", False)
    if has_critical or has_daily_crisis or unread > 0:
        text       = str(unread) if unread > 0 else "!"
        style      = {"display": "flex"}
        icon_class = "icon-btn notification-bell-active"
    else:
        text       = "0"
        style      = {"display": "none"}
        icon_class = "icon-btn"
    return text, style, icon_class


@callback(
    Output("alarm-trigger-store", "data"),
    Output("stopped-alarmes-store", "data"),
    Input("refresh-interval", "n_intervals"),
    State("stopped-alarmes-store", "data"),
    prevent_initial_call=True,
)
def trigger_alert_banner(interval, stored_stopped):
    cfg.load_seuils_from_db()
    stored_stopped    = stored_stopped or []
    alarme            = get_alarme_journaliere()
    maintenant        = now_local()
    aujourdhui_iso    = maintenant.strftime("%Y-%m-%d")
    aujourdhui_str    = maintenant.strftime("%d/%m/%Y")
    heure_courante    = maintenant.strftime("%Hh%M")

    themes_actuels    = alarme.get("themes_crise", [])
    taux_actuel       = alarme.get("taux_auj", 0)
    volume_actuel     = alarme.get("volume_negatif", 0)
    volume_pondere    = alarme.get("volume_pondere", volume_actuel)
    volume_total      = alarme.get("volume_total", 0)
    source_principale = alarme.get("source_principale", "—")
    sources_detail    = alarme.get("sources_detail", {})
    labels_actifs     = {t.get("label") for t in themes_actuels}

    if not alarme["alarme_active"]:
        for i, a in enumerate(stored_stopped):
            if a.get("date_iso") == aujourdhui_iso and a.get("statut") == "EN COURS":
                if a.get("heure_arret") is None:
                    a["heure_arret"] = heure_courante
                    a["statut"]      = "TERMINÉE"
                    a["volume_total"] = volume_total
                    for theme in a.get("themes_detaille", []):
                        label = theme.get("label", "—")
                        if not theme.get("heure_arret"):
                            theme["heure_arret"] = heure_courante
                        deja_arrete = any(
                            d.get("theme") == label and d.get("action", "").upper() in ("ARRÊT", "ARRET")
                            for d in a.get("declenchements", []))
                        if not deja_arrete:
                            a["declenchements"].append({
                                "heure": theme["heure_arret"], "action": "ARRÊT",
                                "taux": taux_actuel, "volume": volume_actuel,
                                "theme": label, "timestamp": maintenant.isoformat()})
                    stored_stopped[i] = a
                    print(f"🛑 ARRÊT GLOBAL à {heure_courante}")
                break
        return {"show_banner": False}, stored_stopped[:50]

    entree_index   = None
    existing_entry = None
    for i, a in enumerate(stored_stopped):
        if a.get("date_iso") == aujourdhui_iso:
            entree_index   = i
            existing_entry = a
            break

    if existing_entry is None:
        themes_detaille_initial = []
        declenchements_initial  = []
        for t in themes_actuels:
            label_t   = t.get("label", "Multiple")
            vol_theme = t.get("count", volume_actuel)
            src_theme = t.get("source_principale", source_principale)
            themes_detaille_initial.append({
                **t, "_first_taux": taux_actuel, "_first_heure": heure_courante,
                "source_principale": src_theme, "heure_arret": None})
            declenchements_initial.append({
                "heure": heure_courante, "action": "DÉCLENCHÉE",
                "taux": taux_actuel, "volume": vol_theme,
                "theme": label_t, "timestamp": maintenant.isoformat()})

        new_entry = {
            "date_iso":          aujourdhui_iso,
            "date_str":          aujourdhui_str,
            "taux_max":          taux_actuel,
            "volume_negatif":    volume_actuel,
            "volume_pondere":    volume_pondere,
            "volume_total":      volume_total,
            "theme_principal":   themes_actuels[0].get("label", "Multiple") if themes_actuels else "Multiple",
            "heure_pic":         heure_courante,
            "heure_arret":       None,
            "statut":            "EN COURS",
            "themes_crise":      themes_actuels,
            "themes_detaille":   themes_detaille_initial,
            "date_analyse":      maintenant.strftime("%d/%m/%Y à %H:%M"),
            "declenchements":    declenchements_initial,
            "source_principale": source_principale,
            "sources_detail":    sources_detail,
        }
        stored_stopped.insert(0, new_entry)
        print(f"✅ CRÉATION alarme: taux={taux_actuel}%, signal={volume_pondere}")
    else:
        if existing_entry.get("statut") == "TERMINÉE":
            existing_entry["statut"]      = "EN COURS"
            existing_entry["heure_arret"] = None
            print(f"🔄 RÉOUVERTURE alarme du {aujourdhui_str}")

        existing_entry["volume_total"]      = volume_total
        existing_entry["date_analyse"]      = maintenant.strftime("%d/%m/%Y à %H:%M")
        existing_entry["sources_detail"]    = sources_detail
        existing_entry["source_principale"] = source_principale

        if volume_actuel > existing_entry.get("volume_negatif", 0):
            existing_entry["volume_negatif"] = volume_actuel
        if volume_pondere > existing_entry.get("volume_pondere", 0):
            existing_entry["volume_pondere"] = volume_pondere

        themes_ex        = existing_entry.get("themes_detaille", [])
        themes_ex_labels = {t.get("label") for t in themes_ex}

        for nt in themes_actuels:
            label_nt     = nt.get("label")
            vol_theme_nt = nt.get("count", volume_actuel)
            src_nt       = nt.get("source_principale", source_principale)
            if label_nt not in themes_ex_labels:
                themes_ex.append({
                    **nt, "_first_taux": taux_actuel, "_first_heure": heure_courante,
                    "source_principale": src_nt, "heure_arret": None})
                existing_entry["declenchements"].append({
                    "heure": heure_courante, "action": "DÉCLENCHÉE",
                    "taux": taux_actuel, "volume": vol_theme_nt,
                    "theme": label_nt, "timestamp": maintenant.isoformat()})
                print(f"   🆕 Nouveau thème: {label_nt} à {heure_courante}")
            else:
                for et in themes_ex:
                    if et.get("label") == label_nt:
                        if nt.get("count", 0) > et.get("count", 0):
                            et["count"] = nt["count"]
                        if nt.get("signal_theme", 0) > et.get("signal_theme", 0):
                            et["signal_theme"] = nt["signal_theme"]
                        et["source_principale"] = src_nt
                        et["heure_arret"] = None
                        break

        for et in themes_ex:
            label_et = et.get("label")
            if label_et not in labels_actifs and et.get("heure_arret") is None:
                et["heure_arret"] = heure_courante
                deja_arrete = any(
                    d.get("theme") == label_et and d.get("action", "").upper() in ("ARRÊT", "ARRET")
                    for d in existing_entry.get("declenchements", []))
                if not deja_arrete:
                    existing_entry["declenchements"].append({
                        "heure": heure_courante, "action": "ARRÊT",
                        "taux": taux_actuel, "volume": volume_actuel,
                        "theme": label_et, "timestamp": maintenant.isoformat()})
                    print(f"   🛑 Thème arrêté: {label_et} à {heure_courante}")

        existing_entry["themes_detaille"] = themes_ex
        existing_entry["themes_crise"]    = themes_ex
        stored_stopped[entree_index]      = existing_entry

    return {"show_banner": True}, stored_stopped[:50]


@callback(
    Output("stopped-alarmes-store", "data", allow_duplicate=True),
    Input("clear-store-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_store(n_clicks):
    if n_clicks:
        return []
    return dash.no_update


@callback(
    Output("alerts-container", "children"),
    Input("alarm-trigger-store", "data"),
    prevent_initial_call=True,
)
def show_alert_banner(trigger_data):
    if not trigger_data or not trigger_data.get("show_banner"):
        return dash.no_update
    stats = get_filtered_stats(ttl_hash=get_ttl_hash())
    return make_alert_banner(stats)


@callback(
    Output("alerts-container", "children", allow_duplicate=True),
    Input({"type": "alert-close", "id": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def close_alert_banner(n_clicks_list):
    if any(n and n > 0 for n in (n_clicks_list or [])):
        return None
    return dash.no_update


@callback(
    Output("refresh-interval", "n_intervals"),
    Input("refresh-data-btn", "n_clicks"),
    prevent_initial_call=True,
)
def manual_refresh(n_clicks):
    if n_clicks:
        get_filtered_stats.cache_clear()
        return n_clicks
    return dash.no_update


@callback(
    Output("alarm-audio", "src"),
    Input("alarm-close-btn", "n_clicks"),
    prevent_initial_call=True,
)
def stop_alarm_sound(n_clicks):
    if n_clicks:
        return ""
    return dash.no_update


@callback(
    Output("full-dashboard-layout", "children", allow_duplicate=True),
    Output("dashboard-wrapper", "data-theme", allow_duplicate=True),
    Input("stopped-alarmes-store", "data"),
    State("theme-store", "data"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def update_dashboard_on_store_change(stopped_alarmes, theme, auth_data):
    get_filtered_stats.cache_clear()
    theme     = theme or "light"
    user_data = None
    if auth_data and auth_data.get("is_authenticated"):
        user_data = auth_data.get("user", {})
    return render_dashboard_content(theme, user_data, stopped_alarmes or []), theme


@callback(
    Output("periode-active-store", "data"),
    Output("btn-periode-global", "style"),
    Output("btn-periode-mois", "style"),
    Input("btn-periode-global", "n_clicks"),
    Input("btn-periode-mois", "n_clicks"),
    prevent_initial_call=True,
)
def set_periode(n_global, n_mois):
    style_active = {
        "padding": "6px 16px", "borderRadius": "20px", "border": "none",
        "background": BLUE, "color": "white", "cursor": "pointer",
        "fontSize": "12px", "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px"}
    style_inactive = {
        "padding": "6px 16px", "borderRadius": "20px",
        "border": f"1px solid {BLUE}", "background": "transparent",
        "color": BLUE, "cursor": "pointer", "fontSize": "12px",
        "fontWeight": "500", "transition": "all 0.2s ease",
        "display": "flex", "alignItems": "center", "gap": "6px"}
    ctx = dash.callback_context
    if not ctx.triggered:
        return "global", style_active, style_inactive
    btn = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn == "btn-periode-mois":
        return "mois", style_inactive, style_active
    return "global", style_active, style_inactive

@callback(
    Output("global-content-wrapper", "style"),
    Input("periode-active-store", "data"),
    prevent_initial_call=False,
)
def toggle_global_content(periode):
    return {"display": "none"} if periode == "mois" else {"display": "block"}


@callback(
    Output("global-kpi-wrapper", "style"),
    Input("periode-active-store", "data"),
    prevent_initial_call=False,
)
def toggle_global_kpi(periode):
    return {"display": "none"} if periode == "mois" else {"display": "block"}


@callback(
    Output("periode-kpi-zone", "children"),
    Output("periode-charts-zone", "children"),
    Input("periode-active-store", "data"),
    Input("refresh-interval", "n_intervals"),
    State("theme-store", "data"),
    State("stopped-alarmes-store", "data"),
    prevent_initial_call=False,
)
def update_periode_content(periode, _intervals, theme, stopped_alarmes):
    theme           = theme or "light"
    stopped_alarmes = stopped_alarmes or []

    if periode != "mois":
        return None, None

    mois_lbl = now_local().strftime("%B %Y")
    cfg.load_seuils_from_db()
    SEUIL_TAUX_JOUR   = cfg.SEUIL_TAUX_JOUR
    SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR

    bandeau_stats = html.Div([
        html.Div(style={"width": "4px", "height": "28px", "borderRadius": "4px",
                        "background": BLUE, "marginRight": "12px"}),
        html.I(className="fas fa-chart-simple",
               style={"fontSize": "16px", "color": BLUE, "marginRight": "10px"}),
        html.Span(f"Statistiques de {mois_lbl}",
                  style={"fontSize": "14px", "fontWeight": "700", "color": BLUE,
                         "letterSpacing": "0.3px"}),
        html.Span("Données agrégées du mois en cours",
                  style={"fontSize": "11px", "color": NEUTRAL, "marginLeft": "12px"}),
    ], style={"display": "flex", "alignItems": "center", "padding": "10px 16px",
              "marginTop": "20px", "background": "var(--bg-card)", "borderRadius": "12px",
              "marginBottom": "20px", "border": f"1px solid {BLUE_LIGHT}",
              "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})

    kpi_zone = html.Div([bandeau_stats, make_kpi_row_ce_mois(theme)],
                        style={"marginBottom": "20px"})

    alarme_auj = get_alarme_journaliere()
    stats_auj  = {
        "total":    alarme_auj["volume_total"],
        "positifs": alarme_auj["volume_positif"],
        "negatifs": alarme_auj["volume_negatif"],
        "neutres":  alarme_auj["volume_neutre"],
        "frustrations": 0, "avg_score": 0,
        "taux_satisfaction": round(alarme_auj["volume_positif"] / max(alarme_auj["volume_total"], 1) * 100, 1),
        "taux_negatif":      alarme_auj["taux_auj"],
        "taux_frustration":  0,
    }

    # Récupérer les top 5 thèmes du jour (sans filtre seuil)
    themes_jour_formatted = get_themes_aujourd_hui()

    section_aujourd_hui = html.Div([
        html.Div([
            html.Div(style={"width": "3px", "height": "18px", "borderRadius": "2px",
                            "background": BLUE, "marginRight": "10px"}),
            html.Span("Aujourd'hui", style={"fontSize": "13px", "fontWeight": "700",
                                            "color": BLUE, "letterSpacing": "0.04em"}),
            html.Span(now_local().strftime("%d/%m/%Y"),
                      style={"fontSize": "11px", "color": NEUTRAL, "marginLeft": "10px"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "12px"}),
        html.Div([
            _chart_card_wrap("fas fa-chart-pie", "Sentiments du Jour",
                             "Sentiments Aujourd'hui",
                             "Répartition des sentiments sur les dernières 24h.",
                             html.Div([
                                 dcc.Graph(figure=make_sentiment_donut(stats_auj, theme),
                                           config={"displayModeBar": False}, style={"width": "100%"}),
                                 html.Div([
                                     html.Div([html.Div(className="legend-dot negative"),
                                               html.Span(f"Négatifs  {stats_auj['negatifs']:,}".replace(",", "\u202f"))],
                                              className="legend-item"),
                                     html.Div([html.Div(className="legend-dot positive"),
                                               html.Span(f"Positifs  {stats_auj['positifs']:,}".replace(",", "\u202f"))],
                                              className="legend-item"),
                                     html.Div([html.Div(className="legend-dot neutral"),
                                               html.Span(f"Neutres  {stats_auj['neutres']:,}".replace(",", "\u202f"))],
                                              className="legend-item"),
                                 ], className="donut-legend-horizontal"),
                             ])),
            _chart_card_wrap("fas fa-tags", "Thèmes Détectés ce Jour",
                             "Thèmes de crise aujourd'hui",
                             "Top thèmes des commentaires négatifs des dernières 24h.",
                             dcc.Graph(figure=make_theme_chart(themes_jour_formatted, theme),
                                       config={"displayModeBar": False}, style={"width": "100%"})),
        ], className="row-2cols", style={"marginBottom": "16px"}),
    ])

    section_mois = html.Div([
        html.Div([
            html.Div(style={"width": "3px", "height": "18px", "borderRadius": "2px",
                            "background": BLUE, "marginRight": "10px"}),
            html.Span(f"Analyse détaillée — {mois_lbl}",
                      style={"fontSize": "13px", "fontWeight": "700",
                             "color": BLUE, "letterSpacing": "0.04em"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "12px"}),
        html.Div([
            _chart_card_wrap("fas fa-chart-pie", "Sentiments du Mois",
                             "Distribution des Sentiments",
                             f"Répartition des sentiments pour {mois_lbl}.",
                             html.Div([
                                 dcc.Graph(figure=make_sentiments_donut_mois(theme),
                                           config={"displayModeBar": False}, style={"width": "100%"}),
                                 html.Div([
                                     html.Div([html.Div(className="legend-dot negative"),
                                               html.Span("Négatifs")], className="legend-item"),
                                     html.Div([html.Div(className="legend-dot positive"),
                                               html.Span("Positifs")], className="legend-item"),
                                     html.Div([html.Div(className="legend-dot neutral"),
                                               html.Span("Neutres")], className="legend-item"),
                                 ], className="donut-legend-horizontal"),
                             ])),
            _chart_card_wrap("fas fa-share-nodes", "Répartition par Source",
                             "Sources de Commentaires",
                             "Canaux d'origine des commentaires ce mois.",
                             dcc.Graph(figure=make_sources_mois_chart(theme),
                                       config={"displayModeBar": False}, style={"width": "100%"})),
        ], className="row-2cols", style={"marginBottom": "16px"}),
        html.Div([
            _chart_card_wrap("fas fa-tags", f"Thèmes Détectés ce Mois",
                             "Top Thèmes", f"Les 5 thèmes les plus fréquents pour {mois_lbl}.",
                             dcc.Graph(figure=make_themes_mois_chart(theme),
                                       config={"displayModeBar": False}, style={"width": "100%"})),
            _chart_card_wrap("fas fa-language", "Distribution des Langues",
                             "Langues Détectées",
                             "Répartition des langues des commentaires ce mois.",
                             dcc.Graph(figure=make_langues_mois_chart(theme),
                                       config={"displayModeBar": False}, style={"width": "100%"})),
        ], className="row-2cols"),
    ])

    historique_zone = make_historique_alertes_with_current(
        seuil_taux=SEUIL_TAUX_JOUR, seuil_volume=SEUIL_VOLUME_JOUR,
        stopped_alarmes=stopped_alarmes)

    charts_zone = html.Div([
        section_aujourd_hui,
        section_mois,
        historique_zone if historique_zone else None,
    ], style={"marginBottom": "20px"})

    return kpi_zone, charts_zone
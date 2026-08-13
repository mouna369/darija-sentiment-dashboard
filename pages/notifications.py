
"""notifications.py - Page des notifications avec suppression individuelle et synchronisation globale"""

import dash
from dash import html, dcc, callback, Input, Output, State, ALL
import sys, os
import json
from functools import lru_cache
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from database import MONGO_AVAILABLE, _col

dash.register_page(__name__, path='/notifications', name='Notifications')

# Configuration des seuils
import config.configuration_seuil as cfg

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE RÉCUPÉRATION DES ALERTES
# ═══════════════════════════════════════════════════════════════════════════════
def get_critical_alert(force_refresh=False):
    """Retourne l'alerte critique si le taux négatif global dépasse le seuil"""
    try:
        # 🔧 RECHARGEMENT DES SEUILS
        cfg.load_seuils_from_db()
        SEUIL_NEGATIF = cfg.SEUIL_NEGATIF
        
        if MONGO_AVAILABLE and _col is not None:
            
            def get_taux_negatif():
                result = list(_col.aggregate([
                    {"$group": {
                        "_id": None,
                        "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                        "total": {"$sum": 1},
                    }}
                ]))
                if result and result[0]["total"] > 0:
                    total = result[0]["total"]
                    neg = result[0]["negatifs"]
                    taux = round(neg / total * 100, 1)
                    print(f"📊 Taux négatif global calculé : {taux}%")
                    return taux
                return 0.0
            
            if force_refresh:
                taux = get_taux_negatif()
            else:
                @lru_cache(maxsize=128)
                def get_taux_cached(ttl_hash=None):
                    del ttl_hash
                    return get_taux_negatif()
                
                taux = get_taux_cached(ttl_hash=round(time.time() / 300))
            
            print(f"🔍 Comparaison: taux={taux}% >= seuil={SEUIL_NEGATIF}% ? {taux >= SEUIL_NEGATIF}")
            
            if taux >= SEUIL_NEGATIF:
                return {
                    "id": "critical_alert",
                    "icon": "fa-circle-exclamation",
                    "color": "#e8384f",
                    "title": "⚠ ALERTE CRITIQUE - Taux Négatif Excessif",
                    "desc": f"Taux négatif global: {taux}% (seuil: {SEUIL_NEGATIF}%). Action requise.",
                    "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "cat": "Critique",
                    "unread": True
                }
            else:
                print(f"✅ Pas d'alerte critique: {taux}% < {SEUIL_NEGATIF}%")
    except Exception as e:
        print(f"Erreur récupération alerte critique: {e}")
    return None


def get_daily_alert(force_refresh=False):
    """
    Retourne l'alerte journalière si le taux négatif des dernières 24h 
    dépasse les seuils (taux >= SEUIL_TAUX_JOUR ET volume >= SEUIL_VOLUME_JOUR)
    """
    try:
        # 🔧 RECHARGEMENT DES SEUILS
        cfg.load_seuils_from_db()
        SEUIL_TAUX_JOUR = cfg.SEUIL_TAUX_JOUR
        SEUIL_VOLUME_JOUR = cfg.SEUIL_VOLUME_JOUR
        
        if MONGO_AVAILABLE and _col is not None:
            
            def get_daily_stats():
                maintenant = datetime.now()
                hier_24h = maintenant - timedelta(hours=24)
                
                pipeline = [
                    {
                        "$match": {
                            "$or": [
                                {"date_originale": {"$gte": hier_24h}},
                                {"date_annotation": {"$gte": hier_24h}},
                            ]
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": 1},
                            "negatifs": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "NEGATIF"]}, 1, 0]}},
                        }
                    }
                ]
                result = list(_col.aggregate(pipeline))
                if result and result[0]["total"] > 0:
                    total = result[0]["total"]
                    neg = result[0]["negatifs"]
                    taux = round(neg / total * 100, 1)
                    return taux, neg, total
                return 0.0, 0, 0
            
            if force_refresh:
                taux, volume, total = get_daily_stats()
            else:
                @lru_cache(maxsize=128)
                def get_daily_cached(ttl_hash=None):
                    del ttl_hash
                    return get_daily_stats()
                
                taux, volume, total = get_daily_cached(ttl_hash=round(time.time() / 300))
            
            condition_taux = taux >= SEUIL_TAUX_JOUR
            condition_volume = volume >= SEUIL_VOLUME_JOUR
            
            print(f"🔍 Alerte journalière: taux={taux}% (seuil={SEUIL_TAUX_JOUR}%) → {condition_taux}, volume={volume} (seuil={SEUIL_VOLUME_JOUR}) → {condition_volume}")
            
            if condition_taux and condition_volume:
                # Trouver le thème principal en crise
                theme_crise = "Général"
                try:
                    pipeline_theme = [
                        {
                            "$match": {
                                "sentiment_label": "NEGATIF",
                                "theme_pred": {"$exists": True, "$ne": None},
                                "$or": [
                                    {"date_originale": {"$gte": datetime.now() - timedelta(hours=24)}},
                                    {"date_annotation": {"$gte": datetime.now() - timedelta(hours=24)}},
                                ]
                            }
                        },
                        {"$group": {"_id": "$theme_pred", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 1},
                    ]
                    theme_result = list(_col.aggregate(pipeline_theme))
                    if theme_result and theme_result[0]["_id"]:
                        theme_map = {
                            "reseau": "Réseau", "technique": "Technique",
                            "attente": "Délais", "facturation_tarifs": "Facturation",
                            "service": "Service Client", "service_clientele": "Service Client"
                        }
                        theme_crise = theme_map.get(theme_result[0]["_id"].lower(), theme_result[0]["_id"])
                except:
                    pass
                
                return {
                    "id": "daily_alert",
                    "icon": "fa-calendar-day",
                    "color": "#e8384f",
                    "title": "⚠ ALERTE JOURNALIÈRE - Crise détectée aujourd'hui",
                    "desc": f"Taux négatif 24h: {taux}% (seuil: {SEUIL_TAUX_JOUR}%) — {volume} commentaires négatifs (seuil: {SEUIL_VOLUME_JOUR}) — Thème principal: {theme_crise}",
                    "time": "Aujourd'hui",
                    "cat": theme_crise,
                    "unread": True
                }
            else:
                print(f"✅ Pas d'alerte journalière: taux={taux}% (<{SEUIL_TAUX_JOUR}%) ou volume={volume} (<{SEUIL_VOLUME_JOUR})")
    except Exception as e:
        print(f"Erreur récupération alerte journalière: {e}")
    return None
# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS STATIQUES
# ═══════════════════════════════════════════════════════════════════════════════

STATIC_NOTIFS = [
    {
        "id": "notif_1",
        "icon": "fa-chart-line",
        "color": "#003087",
        "title": "Rapport mensuel disponible",
        "desc": "Le rapport d'analyse des sentiments du mois dernier est prêt.",
        "time": "Il y a 2 jours",
        "cat": "Rapport",
        "unread": False
    },
    {
        "id": "notif_2",
        "icon": "fa-wifi",
        "color": "#f59e0b",
        "title": "Maintenance réseau prévue",
        "desc": "Maintenance le 25/04/2026 de 02h00 à 04h00.",
        "time": "Il y a 3 jours",
        "cat": "Réseau",
        "unread": False
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
# COULEURS POUR LES BADGES
# ═══════════════════════════════════════════════════════════════════════════════

cat_colors_rgb = {
    "Réseau": (245, 158, 11),      # Orange
    "Critique": (232, 56, 79),     # Rouge
    "Client": (0, 168, 84),        # Vert
    "Service Client": (0, 168, 84), # Vert aussi ← AJOUTÉ
    "Rapport": (0, 48, 135),       # Bleu
    "Sécurité": (0, 168, 84),      # Vert
    "Performance": (0, 48, 135),   # Bleu
    "Facturation": (245, 158, 11), # Orange
    "Service": (232, 56, 79)        # Vert
}

cat_colors_map = {
    "Réseau": "#f59e0b",           # Orange
    "Critique": "#e8384f",         # Rouge
    "Client": "#00a854",           # Vert
    "Service Client": "#00a854",   # Vert ← AJOUTÉ
    "Rapport": "#003087",          # Bleu
    "Sécurité": "#00a854",         # Vert
    "Performance": "#003087",      # Bleu
    "Facturation": "#f59e0b",      # Orange
    "Service": "#e8384f"           # Vert
}

def hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def make_notif_card(n, idx):
    bg = "rgba(0,48,135,0.04)" if n.get("unread", False) else "var(--stat-bg)"
    border = "1px solid rgba(0,48,135,0.12)" if n.get("unread", False) else "1px solid var(--border-color)"
    dot_bg = "#e8384f" if n.get("unread", False) else "transparent"
    fw = "700" if n.get("unread", False) else "500"
    rgb = cat_colors_rgb.get(n.get("cat", "Rapport"), (0, 48, 135))
    badge_color = cat_colors_map.get(n.get("cat", "Rapport"), "#003087")

    return html.Div([
        html.Div(
            html.I(className="fas " + n["icon"]),
            style={
                "width": "46px", "height": "46px", "borderRadius": "12px",
                "flexShrink": "0", "background": hex_to_rgba(n["color"], 0.12),
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "fontSize": "18px", "color": n["color"]
            }
        ),
        html.Div([
            html.Div([
                html.Span(n["title"], style={"fontWeight": fw, "fontSize": "14px", "color": "var(--text-primary)"}),
                html.Span(n.get("cat", "Général"),
                          style={
                              "marginLeft": "8px", "padding": "2px 8px", "borderRadius": "12px",
                              "fontSize": "10px", "fontWeight": "600",
                              "background": f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.15)",
                              "color": badge_color
                          })
            ], style={"marginBottom": "4px", "display": "flex", "alignItems": "center", "flexWrap": "wrap"}),
            html.Div(n["desc"], style={"fontSize": "13px", "color": "var(--text-secondary)", "lineHeight": "1.5"}),
            html.Div(n["time"], style={"fontSize": "11px", "color": "var(--text-secondary)", "marginTop": "6px"})
        ], style={"flex": "1", "marginLeft": "14px"}),
        html.Div(style={
            "width": "8px", "height": "8px", "borderRadius": "50%",
            "background": dot_bg, "flexShrink": "0", "marginLeft": "12px",
            "boxShadow": "0 0 4px rgba(232,56,79,0.5)" if n.get("unread") and n.get("cat") == "Critique" else "none"
        }),
        html.Button(
            html.I(className="fas fa-trash-alt", style={"fontSize": "12px", "color": "var(--text-secondary)"}),
            id={"type": "delete-notif-btn", "index": idx},
            style={
                "background": "transparent", "border": "none", "cursor": "pointer",
                "marginLeft": "12px", "padding": "6px", "borderRadius": "8px",
                "transition": "all 0.2s"
            },
            className="delete-notif-btn"
        )
    ], style={
        "display": "flex", "alignItems": "center", "padding": "16px",
        "borderRadius": "12px", "marginBottom": "10px",
        "background": bg, "border": border, "transition": "all 0.2s"
    }, id=f"notif-card-{n.get('id', 'unknown')}")


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS D'INITIALISATION ET RENDU
# ═══════════════════════════════════════════════════════════════════════════════

def get_initial_notifications():
    critical = get_critical_alert()
    daily = get_daily_alert()
    notifications = []
    
    if daily:
        daily["unread"] = True
        notifications.append(daily)
    
    if critical:
        critical["unread"] = True
        notifications.append(critical)
    
    return notifications + STATIC_NOTIFS


def render_notification_list(notifications):
    if not notifications:
        return html.Div([
            html.I(className="fas fa-bell-slash", style={"fontSize": "48px", "color": "var(--text-secondary)", "opacity": "0.5"}),
            html.H4("Aucune notification", style={"marginTop": "16px", "color": "var(--text-secondary)"}),
            html.P("Vous avez supprimé toutes les notifications.", style={"color": "var(--text-secondary)", "fontSize": "13px"})
        ], style={"textAlign": "center", "padding": "60px 20px"})
    return [make_notif_card(n, idx) for idx, n in enumerate(notifications)]


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

layout = html.Div(id='notif-wrapper', children=[
    dcc.Store(id="notifications-store", data=get_initial_notifications()),
    dcc.Store(id="notif-global-store", storage_type='local', data=get_initial_notifications()),
    dcc.Store(id="auth-store", storage_type='local'),
    dcc.Interval(id="critical-check-interval", interval=300000, n_intervals=0),
    dcc.Interval(id="refresh-interval", interval=300000, n_intervals=0),
    html.Div(id='notif-content')
])


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output('notif-content', 'children'),
    Input('theme-store', 'data'),
    Input('notifications-store', 'data'),
    Input('auth-store', 'data'),
)
def render_page(theme, stored_notifs, auth_data):
    theme = theme or "light"
    if not stored_notifs:
        stored_notifs = []
    
    # Récupérer user_data
    user_data = None
    if auth_data and auth_data.get("is_authenticated"):
        user_data = auth_data.get("user", {})
    
    unread_count = sum(1 for n in stored_notifs if n.get("unread", False))
    notif_cards = render_notification_list(stored_notifs)

    content = html.Div([
        html.Div([
            html.Div([
                html.H2("📬 Centre de Notifications", style={
                    "fontSize": "20px", "fontWeight": "600", "margin": "0", "color": "var(--text-primary)"
                }),
                html.Div([
                    html.Span(f"{unread_count} non lue{'s' if unread_count > 1 else ''}",
                              id="unread-count-badge",
                              style={
                                  "background": "#e8384f" if unread_count > 0 else "var(--border-color)",
                                  "color": "white" if unread_count > 0 else "var(--text-secondary)",
                                  "padding": "4px 12px", "borderRadius": "20px",
                                  "fontSize": "12px", "fontWeight": "600"
                              }),
                    html.Button("🔄 Rafraîchir",
                                id="refresh-notifs-btn",
                                style={
                                    "background": "none", "border": "1px solid var(--border-color)",
                                    "borderRadius": "8px", "padding": "6px 14px", "cursor": "pointer",
                                    "fontSize": "12px", "color": "var(--text-secondary)",
                                    "fontFamily": "'DM Sans', sans-serif", "transition": "all 0.2s"
                                }),
                    html.Button("✓ Tout marquer comme lu",
                                id="mark-all-read-btn",
                                style={
                                    "background": "none", "border": "1px solid var(--border-color)",
                                    "borderRadius": "8px", "padding": "6px 14px", "cursor": "pointer",
                                    "fontSize": "12px", "color": "var(--text-secondary)",
                                    "fontFamily": "'DM Sans', sans-serif", "transition": "all 0.2s"
                                }),
                ], style={"display": "flex", "gap": "12px", "alignItems": "center"})
            ], style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "marginBottom": "20px", "paddingBottom": "12px", "borderBottom": "1px solid var(--border-color)"
            }),
            html.Div(notif_cards, id="notifications-list",
                     style={"maxHeight": "calc(100vh - 200px)", "overflowY": "auto"}),
        ], className="dashboard-card", style={
            "background": "var(--bg-card)", "borderRadius": "16px", "padding": "20px", "boxShadow": "var(--shadow-sm)"
        }),
    ])
    
    return make_page_layout("notifications", "Notifications", "Centre d'alertes et messages", content, theme, user_data)


@callback(
    Output("notifications-store", "data", allow_duplicate=True),
    Output("notif-global-store", "data", allow_duplicate=True),
    Input({"type": "delete-notif-btn", "index": ALL}, "n_clicks"),
    State("notifications-store", "data"),
    prevent_initial_call=True,
)
def delete_notification(click_vals, current_notifs):
    if not current_notifs:
        return current_notifs, current_notifs
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_notifs, current_notifs
    prop_id = ctx.triggered[0]["prop_id"]
    try:
        btn_info = json.loads(prop_id.split(".")[0])
        idx = btn_info["index"]
        if 0 <= idx < len(current_notifs):
            current_notifs.pop(idx)
    except Exception as e:
        print(f"Erreur suppression: {e}")
    return current_notifs, current_notifs
@callback(
    Output("notifications-store", "data", allow_duplicate=True),
    Output("notif-global-store", "data", allow_duplicate=True),
    Input("critical-check-interval", "n_intervals"),
    State("notifications-store", "data"),
    prevent_initial_call=True,
)
def refresh_alerts(n, current_notifs):
    """Rafraîchit les alertes critique et journalière SANS supprimer les existantes"""
    new_critical = get_critical_alert()
    new_daily = get_daily_alert()
    
    if new_daily:
        new_daily["unread"] = True
    
    if new_critical:
        new_critical["unread"] = True
    
    # IMPORTANT: Créer une copie pour ne pas perdre les suppressions
    updated_notifs = current_notifs.copy() if current_notifs else []
    
    # Vérifier si les alertes existent déjà (MAINTENIR les existantes)
    daily_exists = any(n.get("id") == "daily_alert" for n in updated_notifs)
    critical_exists = any(n.get("id") == "critical_alert" for n in updated_notifs)
    
    # Gérer l'alerte journalière (AJOUTER seulement si nouvelle)
    if new_daily and not daily_exists:
        updated_notifs.insert(0, new_daily)
    elif not new_daily and daily_exists:
        # Supprimer l'alerte seulement si elle n'est plus valide
        updated_notifs = [n for n in updated_notifs if n.get("id") != "daily_alert"]
    
    # Gérer l'alerte critique (AJOUTER seulement si nouvelle)
    if new_critical and not critical_exists:
        updated_notifs.insert(0, new_critical)
    elif not new_critical and critical_exists:
        updated_notifs = [n for n in updated_notifs if n.get("id") != "critical_alert"]
    
    return updated_notifs, updated_notifs
@callback(
    Output("notifications-store", "data", allow_duplicate=True),
    Output("notif-global-store", "data", allow_duplicate=True),
    Input("mark-all-read-btn", "n_clicks"),
    State("notifications-store", "data"),
    prevent_initial_call=True,
)
def mark_all_read(n_clicks, current_notifs):
    """Marque toutes les notifications comme lues (sauf les alertes critiques)"""
    if not n_clicks or not current_notifs:
        return current_notifs, current_notifs
    for notif in current_notifs:
        # Ne pas marquer les alertes critiques comme lues automatiquement
        if notif.get("id") not in ["critical_alert", "daily_alert"]:
            notif["unread"] = False
    return current_notifs, current_notifs


@callback(
    Output("notifications-store", "data", allow_duplicate=True),
    Output("notif-global-store", "data", allow_duplicate=True),
    Input("refresh-notifs-btn", "n_clicks"),
    State("notifications-store", "data"),
    prevent_initial_call=True,
)
def force_refresh_notifications(n_clicks, current_notifs):
    """Force le rafraîchissement en re-lisant les données MongoDB"""
    if not n_clicks:
        return current_notifs, current_notifs
    
    # Recharger depuis MongoDB sans cache
    new_critical = get_critical_alert(force_refresh=True)
    new_daily = get_daily_alert(force_refresh=True)
    
    print(f"🔄 REFRESH MANUEL - Alerte critique: {'PRESENTE' if new_critical else 'ABSENTE'}")
    print(f"🔄 REFRESH MANUEL - Alerte journalière: {'PRESENTE' if new_daily else 'ABSENTE'}")
    
    # Reconstruire les notifications
    new_notifs = []
    if new_daily:
        new_daily["unread"] = True
        new_notifs.append(new_daily)
    if new_critical:
        new_critical["unread"] = True
        new_notifs.append(new_critical)
    
    new_notifs.extend(STATIC_NOTIFS)
    
    return new_notifs, new_notifs
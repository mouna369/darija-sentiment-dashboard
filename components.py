
"""Shared layout components for AT Dashboard"""
from dash import html, dcc, callback, Input, Output, clientside_callback

# Couleurs AT
AT_GREEN  = "#009A44"
AT_BLUE   = "#003087"
AT_RED    = "#E2001A"
AT_GREY   = "#7C7C7C"

# Mapping pathname → id de page
PATH_TO_PAGE = {
    "/":              "dashboard",
    "/analytics":     "analytics",
    "/statistique":   "statistique",
    "/stats":         "statistique",   # alias
    "/comments":      "comments",
    "/sources":       "sources",       # ✅ ajouté
    "/invoices":      "invoices",
    "/chatbot":       "chatbot",
    "/settings":      "settings",
    "/notifications": "notifications",
    "/admin":         "admin",
}


def make_sidebar(active_page="dashboard", user_data=None):
    nav_items = [
        {"id": "dashboard",       "icon": "fa-chart-line",    "label": "Tableau de Bord",  "href": "/"},
        {"id": "analytics",       "icon": "fa-chart-bar",     "label": "Analytiques",       "href": "/analytics"},
        {"id": "comments",        "icon": "fa-users",         "label": "Commentaires",      "href": "/comments"},
        {"id": "themes-temporal", "icon": "fa-file-invoice",  "label": "Thèmes & Temporel", "href": "/themes-temporal"},
        {"id": "sources",         "icon": "fa-share-nodes",   "label": "Analyse par Source","href": "/sources"},  # ✅ ajouté
        {"id": "chatbot",         "icon": "fa-robot",         "label": "Chatbot IA",        "href": "/chatbot"},
    ]
    settings_items = [
        {"id": "settings",       "icon": "fa-gear",          "label": "Paramètres",        "href": "/settings"},
        {"id": "notifications",  "icon": "fa-bell",          "label": "Notifications",     "href": "/notifications"},
    ]

    # Lien admin — visible uniquement si role == 'admin'
    admin_items = []
    if user_data and user_data.get('role') in ('admin', 'super_admin'):
        admin_items = [
            {"id": "admin", "icon": "fa-shield-halved",
             "label": "Administration", "href": "/admin"},
        ]

    def nav_item(item):
        is_active = item["id"] == active_page
        extra = []
        if item["id"] == "chatbot":
            extra = [html.Span("IA", style={
                "fontSize": "9px", "fontWeight": "800", "padding": "2px 6px",
                "borderRadius": "10px", "background": "#009A44",
                "color": "white", "marginLeft": "auto", "letterSpacing": "0.5px"
            })]
        return html.A(
            [html.Div(html.I(className=f"fas {item['icon']}"), className="nav-icon"),
             html.Span(item["label"]),
             *extra],
            href=item["href"],
            className=f"nav-link-item {'active' if is_active else ''}"
        )

    if user_data:
        firstname = user_data.get('firstname', '')
        user_firstname = firstname if firstname else "Invité"
        user_initials = firstname[0].upper() if firstname else "U"
    else:
        user_firstname = "Invité"
        user_initials = "AT"

    return html.Div([
        html.Div([
            html.Img(src="/assets/images/logo.png",
                     style={"width": "190px", "filter": "brightness(0) invert(1)"}),
        ], className="sidebar-logo"),

        html.Div([
            html.Div(user_initials, className="profile-avatar"),
            html.Div([
                html.H4(
                    "Super Administrateur" if user_data and user_data.get('role') == 'super_admin'
                else "Administrateur" if user_data and user_data.get('role') == 'admin'
                else "Analyseur"
                ),
                html.Span(user_firstname)
            ], className="profile-info")
        ], className="sidebar-profile"),

        html.Div(
            [html.Div("MENU PRINCIPAL", className="nav-section-title")] +
            [nav_item(i) for i in nav_items] +
            ([html.Div("ADMINISTRATION", className="nav-section-title", style={"marginTop": "8px"})] +
             [nav_item(i) for i in admin_items] if admin_items else []) +
            [html.Div("PARAMÈTRES", className="nav-section-title", style={"marginTop": "8px"})] +
            [nav_item(i) for i in settings_items],
            className="sidebar-nav",
            id="sidebar-nav"
        ),

        html.Div([
            html.A([
                html.Div(html.I(className="fas fa-sign-out-alt"), className="nav-icon"),
                html.Span("Déconnexion")
            ], href="/login", className="nav-link-item",
               style={"color": "rgba(255,100,100,0.8)"}),

            html.Div([
                html.Hr(style={"margin": "8px 0 5px 0", "border": "none", "borderTop": "1px solid rgba(255,255,255,0.1)"}),
                html.Div("© Algérie Télécom | Développé par Rehamnia Mouna & Hadjabderrahmane Yousra", style={
                    "fontSize": "12px",
                    "color": "rgba(255,255,255,0.6)",
                    "textAlign": "center",
                    "padding": "3px 0"
                })
            ], style={"marginTop": "-4px"})
        ], className="sidebar-footer")
    ], className="sidebar")


def make_topbar(title, subtitle, theme_value="light", user_data=None):
    if user_data:
        user_name = user_data.get('firstname', '')
    else:
        user_name = 'Invité'

    return html.Div([
        html.Div([
            html.H1(title, style={"fontSize": "22px", "fontWeight": "700", "margin": "0",
                      "fontFamily": "'Cairo', sans-serif",
                      "color": "var(--text-primary)"}),
            html.P(subtitle, style={"fontSize": "13px", "color": "var(--text-secondary)", "margin": "0"})
        ]),
        html.Div([
            html.Div([
                html.I(className="fas fa-search",
                       style={"color": "var(--text-secondary)", "fontSize": "13px"}),
                dcc.Input(placeholder="Rechercher...", type="text",
                          style={"border": "none", "background": "transparent",
                                 "color": "var(--text-primary)", "outline": "none",
                                 "fontFamily": "'Poppins', sans-serif", "fontSize": "13px",
                                 "width": "180px"})
            ], className="search-box"),

            html.Div(style={"position": "relative"}, children=[
                html.A(
                    html.Div(html.I(className="fas fa-bell"), className="icon-btn", id="notification-bell-icon"),
                    href="/notifications",
                    id="notif-link"
                ),
                html.Div("0", id="global-notif-badge", className="notif-badge", style={"display": "none"})
            ]),

            html.Div([
                html.I(className="fas fa-user-circle",
                       style={"color": "var(--at-green)", "fontSize": "16px"}),
                html.Span(user_name if user_name else "Invité",
                         style={"marginLeft": "8px", "fontSize": "13px", "fontWeight": "500",
                                "color": "var(--text-primary)"})
            ], style={"display": "flex", "alignItems": "center", "padding": "0 10px"}),

            html.Div([
                html.I(className="fas fa-sun",
                       style={"color": "var(--at-green)", "fontSize": "14px"}),
                html.Label([
                    dcc.Checklist(
                        id="theme-toggle",
                        options=[{"label": "", "value": "dark"}],
                        value=["dark"] if theme_value == "dark" else [],
                        style={"display": "none"}
                    ),
                    html.Div(className="theme-slider")
                ], className="theme-toggle"),
                html.I(className="fas fa-moon",
                       style={"color": "var(--at-blue-light)", "fontSize": "14px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),

        ], className="topbar-actions")
    ], className="topbar")


def stat_card(icon, icon_class, value, label, change, change_dir="up"):
    return html.Div([
        html.Div(html.I(className=f"fas {icon}"), className=f"stat-icon {icon_class}"),
        html.Div(value, className="stat-value"),
        html.Div(label, className="stat-label"),
        html.Span(
            [html.I(className=f"fas fa-arrow-{'up' if change_dir == 'up' else 'down'}"),
             f" {change}"],
            className=f"stat-change {change_dir}"
        )
    ], className="stat-card fade-in-1")


def make_page_layout(active_page, title, subtitle, content, theme="light", user_data=None):
    """
    Layout principal.
    active_page : identifiant de la page courante (ex: 'statistique').
    """
    return html.Div([
        # Location pour détecter le pathname côté client
        dcc.Location(id="url-location", refresh=False),

        make_sidebar(active_page, user_data),

        html.Div([
            make_topbar(title, subtitle, theme, user_data),
            html.Div(content, className="page-content")
        ], className="main-content"),

        dcc.Store(id="notif-global-store", storage_type='local', data=[]),

    ], id="app-wrapper", **{"data-theme": theme})


# ─────────────────────────────────────────────────────────────
# Callback clientside : met à jour la classe "active" des liens
# du sidebar en fonction du pathname courant, SANS rechargement.
# ─────────────────────────────────────────────────────────────
clientside_callback(
    """
    function(pathname) {
        // Retirer 'active' de tous les liens sidebar
        var links = document.querySelectorAll('.nav-link-item');
        links.forEach(function(el) {
            el.classList.remove('active');
        });

        // Ajouter 'active' sur le lien dont href correspond au pathname
        links.forEach(function(el) {
            var href = el.getAttribute('href');
            if (href && (
                href === pathname ||
                (pathname === '/statistique' && href === '/statistique') ||
                (pathname === '/stats'       && href === '/statistique') ||
                (pathname === '/sources'     && href === '/sources')
            )) {
                el.classList.add('active');
            }
        });

        // Cas spécial : page d'accueil exacte
        if (pathname === '/') {
            links.forEach(function(el) {
                if (el.getAttribute('href') === '/') {
                    el.classList.add('active');
                }
            });
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output("app-wrapper", "id"),          # output factice (on ne change rien)
    Input("url-location", "pathname"),
    prevent_initial_call=False,
)
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate

dash.register_page(__name__, path='/admin/login', name='Administration - Connexion')

layout = html.Div([
    dcc.Store(id='user-session', storage_type='session'),
    dcc.Location(id='admin-login-redirect', refresh=True),

    html.Div(id='admin-auth-wrapper', **{"data-theme": "light"}, children=[
        html.Div([
          
            # ── Colonne gauche : panel sombre sécurité ──────────────────
            html.Div([
                html.Div([
                    # Logo + badge
                    html.Div([
                        html.Img(
                            src="/assets/images/logo.png",
                            style={"width": "260px",
                                   "filter": "brightness(0) invert(1)",
                                   "marginBottom": "36px"})
                        
                    ]),

                    html.Div([
                        html.I(className="fas fa-shield-halved",
                               style={"fontSize": "40px", "color": "#E2001A",
                                      "marginBottom": "16px"}),
                        html.H2("Espace Administrateur",
                                style={
                                    "color": "white",
                                    "fontFamily": "'Cairo', sans-serif",
                                    "fontSize": "30px", "fontWeight": "800",
                                    "lineHeight": "1.3", "marginBottom": "12px"
                                }),
                        html.P("Accès réservé au personnel autorisé d'Algérie Télécom.",
                               style={"color": "rgba(255,255,255,0.65)",
                                      "fontSize": "14px", "lineHeight": "1.7",
                                      "marginBottom": "36px"}),
                    ]),

                    # Infos sécurité
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-lock",
                                   style={"color": "#E2001A", "marginRight": "10px",
                                          "width": "16px"}),
                            html.Span("Connexion chiffrée et sécurisée")
                        ], style={"color": "rgba(255,255,255,0.80)",
                                  "marginBottom": "12px",
                                  "display": "flex", "alignItems": "center",
                                  "fontSize": "13px"}),
                        html.Div([
                            html.I(className="fas fa-user-shield",
                                   style={"color": "#E2001A", "marginRight": "10px",
                                          "width": "16px"}),
                            html.Span("Droits d'accès RBAC")
                        ], style={"color": "rgba(255,255,255,0.80)",
                                  "marginBottom": "12px",
                                  "display": "flex", "alignItems": "center",
                                  "fontSize": "13px"}),
                        html.Div([
                            html.I(className="fas fa-eye-slash",
                                   style={"color": "#E2001A", "marginRight": "10px",
                                          "width": "16px"}),
                            html.Span("Activité auditée et tracée")
                        ], style={"color": "rgba(255,255,255,0.80)",
                                  "marginBottom": "12px",
                                  "display": "flex", "alignItems": "center",
                                  "fontSize": "13px"}),
                    ]),

                ], style={"maxWidth": "360px"})
            ], style={
                "background": "linear-gradient(135deg, #001a4d 0%, #003087 50%, #005080 100%)",
                "flex": "1",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "padding": "60px",
                "minHeight": "100vh",
                "position": "relative",
                "overflow": "hidden",
                "borderRight": "1px solid rgba(226,0,26,0.3)"
            }),

            # ── Colonne droite : formulaire ──────────────────────────────
            html.Div([

                html.Div([
                    # Header formulaire
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-circle-dot",
                                   style={"color": "#E2001A", "fontSize": "10px",
                                          "marginRight": "6px"}),
                            html.Span("ACCÈS SÉCURISÉ",
                                      style={"fontSize": "11px", "fontWeight": "700",
                                             "color": "#E2001A", "letterSpacing": "2px"})
                        ], style={"display": "flex", "alignItems": "center",
                                  "marginBottom": "20px"}),

                        html.H2("Connexion Admin",
                                style={"fontFamily": "'Cairo', sans-serif",
                                       "fontSize": "26px", "fontWeight": "800",
                                       "color": "var(--text-primary)",
                                       "marginBottom": "6px"}),
                        html.P("Identifiez-vous avec vos accès administrateur",
                               style={"color": "var(--text-secondary)",
                                      "fontSize": "13px", "marginBottom": "32px"}),
                    ]),

                    # Champ email
                    html.Div([
                        html.Label("Adresse email administrateur",
                                   style={"fontSize": "13px", "fontWeight": "600",
                                          "color": "var(--text-primary)",
                                          "marginBottom": "8px", "display": "block"}),
                        html.Div([
                            html.I(className="fas fa-envelope",
                                   style={"position": "absolute", "left": "14px",
                                          "top": "50%", "transform": "translateY(-50%)",
                                          "color": "#999", "fontSize": "14px",
                                          "pointerEvents": "none"}),
                            dcc.Input(
                                id="admin-login-email",
                                type="email",
                                placeholder="admin@algerietelecom.dz",
                                className="form-input",
                                style={"paddingLeft": "42px", "width": "100%"}
                            ),
                        ], style={"position": "relative"}),
                    ], style={"marginBottom": "20px"}),

                    # Champ mot de passe
                    html.Div([
                        html.Label("Mot de passe",
                                   style={"fontSize": "13px", "fontWeight": "600",
                                          "color": "var(--text-primary)",
                                          "marginBottom": "8px", "display": "block"}),
                        html.Div([
                            html.I(className="fas fa-lock",
                                   style={"position": "absolute", "left": "14px",
                                          "top": "50%", "transform": "translateY(-50%)",
                                          "color": "#999", "fontSize": "14px",
                                          "pointerEvents": "none"}),
                            dcc.Input(
                                id="admin-login-password",
                                type="password",
                                placeholder="••••••••",
                                className="form-input",
                                style={"paddingLeft": "42px", "width": "100%"}
                            ),
                        ], style={"position": "relative"}),
                    ], style={"marginBottom": "24px"}),

                    # Message erreur
                    html.Div(id="admin-login-error",
                             style={"display": "none", "marginBottom": "16px"}),

                    # Bouton connexion
                    html.Button([
                        html.I(className="fas fa-right-to-bracket",
                               style={"marginRight": "8px"}),
                        "Accéder au panneau d'administration"
                    ],
                        id="admin-login-btn",
                        className="btn-primary-at",
                        style={
                            "width": "100%",
                            "background": "linear-gradient(135deg, #E2001A, #a00013)",
                            "border": "none"
                        }
                    ),

                    # Séparateur
                    html.Hr(style={"margin": "28px 0",
                                   "borderColor": "var(--border-color)"}),

                    # Lien vers login normal
                    html.Div([
                        # html.I(className="fas fa-arrow-left",
                        #        style={"marginRight": "6px", "fontSize": "12px",
                        #               "color": "var(--text-secondary)"}),
                        # html.Span("Retour à la connexion standard", href="/login",
                        #           style={"fontSize": "13px", "color": "#003087",
                        #               "fontWeight": "600",
                        #               "textDecoration": "none"})
                    ], style={"textAlign": "center"}),

                ], style={"maxWidth": "400px", "width": "100%"})

            ], style={
                "flex": "1",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "padding": "60px 40px",
                "background": "var(--bg-secondary)",
                "minHeight": "100vh"
            }),

        ], style={"display": "flex", "minHeight": "100vh"}),
    ])
])


# ── Callback connexion admin ──────────────────────────────────────────────────

@callback(
    Output('admin-login-error', 'children'),
    Output('admin-login-error', 'style'),
    Output('user-session', 'data', allow_duplicate=True),
    Output('admin-login-redirect', 'pathname'),
    Input('admin-login-btn', 'n_clicks'),
    State('admin-login-email', 'value'),
    State('admin-login-password', 'value'),
    prevent_initial_call=True
)
def admin_login(n_clicks, email, password):
    if not n_clicks:
        raise PreventUpdate

    error_style_visible = {
        "display": "block", "color": "#dc3545", "fontSize": "13px",
        "padding": "10px 14px", "borderRadius": "8px",
        "backgroundColor": "rgba(220,53,69,0.1)", "marginBottom": "16px"
    }
    error_style_hidden = {"display": "none"}

    # Champs vides
    if not email or not password:
        return "Veuillez remplir tous les champs.", error_style_visible, no_update, no_update

    try:
        from pymongo import MongoClient
        from werkzeug.security import check_password_hash
        from config.db_config import db_manager

        # Chercher l'utilisateur dans MongoDB
        user = db_manager.db['dashbo_admin'].find_one({"email": email})

        if not user:
            return "Email ou mot de passe incorrect.", error_style_visible, no_update, no_update

        # ── Vérifier que c'est un admin ──────────────────────────
        role = user.get('role', 'user')
        if role not in ('admin', 'super_admin'):
            return (
                "⛔ Accès refusé — ce compte n'a pas les droits administrateur. "
                "Utilisez la connexion standard.",
                error_style_visible, no_update, no_update
            )

        # ── Vérifier le mot de passe ──────────────────────────────
        if not check_password_hash(user['password'], password):
            return "Email ou mot de passe incorrect.", error_style_visible, no_update, no_update

        # ── Créer la session ──────────────────────────────────────
        session_data = {
            'logged_in': True,
            'user': {
                'firstname': user.get('firstname', ''),
                'lastname':  user.get('lastname', ''),
                'email':     user.get('email', ''),
                'role':      role
            }
        }
        print(f"✅ Admin connecté : {email} | role : {role}")
        return "", error_style_hidden, session_data, "/"

    except Exception as e:
        return f"Erreur serveur : {e}", error_style_visible, no_update, no_update

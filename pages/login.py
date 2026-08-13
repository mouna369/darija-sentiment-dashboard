

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from config.db_config import db_manager

dash.register_page(__name__, path='/login', name='Connexion')

layout = html.Div([
    dcc.Store(id='user-session', storage_type='session'),
    dcc.Location(id='login-redirect', refresh=True),

    html.Div(id='auth-page-wrapper', **{"data-theme": "light"}, children=[
        html.Div([
            # Background shapes
            html.Div([
                html.Div(style={
                    "position": "absolute", "width": "500px", "height": "500px",
                    "borderRadius": "50%", "top": "-150px", "left": "-150px",
                    "background": "radial-gradient(circle, rgba(0,48,135,0.12) 0%, transparent 70%)"
                }),
                html.Div(style={
                    "position": "absolute", "width": "400px", "height": "400px",
                    "borderRadius": "50%", "bottom": "-100px", "right": "-100px",
                    "background": "radial-gradient(circle, rgba(0,154,68,0.12) 0%, transparent 70%)"
                }),
            ], className="auth-bg-shapes"),

            # Left: brand panel
            html.Div([
                html.Div([
                    html.Img(src="/assets/images/logo.png",
                             style={"width": "300px",
                                    "filter": "brightness(0) invert(1)",
                                    "marginBottom": "40px"}),
                    html.H2("Bienvenue sur\nle Dashboard AT", style={
                        "color": "white", "fontFamily": "'Cairo', sans-serif",
                        "fontSize": "32px", "fontWeight": "700",
                        "lineHeight": "1.3", "marginBottom": "16px"
                    }),
                    html.P("Gérez vos services de télécommunications avec notre plateforme intelligente.",
                           style={"color": "rgba(255,255,255,0.75)", "fontSize": "15px",
                                  "lineHeight": "1.6", "marginBottom": "40px"}),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-check-circle",
                                   style={"color": "#00c957", "marginRight": "10px"}),
                            html.Span("Surveillance du réseau en temps réel")
                        ], style={"color": "rgba(255,255,255,0.85)", "marginBottom": "12px",
                                  "display": "flex", "alignItems": "center"}),
                        html.Div([
                            html.I(className="fas fa-check-circle",
                                   style={"color": "#00c957", "marginRight": "10px"}),
                            html.Span("Gestion complète des clients")
                        ], style={"color": "rgba(255,255,255,0.85)", "marginBottom": "12px",
                                  "display": "flex", "alignItems": "center"}),
                        html.Div([
                            html.I(className="fas fa-check-circle",
                                   style={"color": "#00c957", "marginRight": "10px"}),
                            html.Span("Rapports analytiques avancés")
                        ], style={"color": "rgba(255,255,255,0.85)", "marginBottom": "12px",
                                  "display": "flex", "alignItems": "center"}),
                    ]),
                ], style={"maxWidth": "380px"})
            ], style={
                "background": "linear-gradient(135deg, #001a4d 0%, #003087 50%, #005080 100%)",
                "flex": "1", "display": "flex", "alignItems": "center",
                "justifyContent": "center", "padding": "60px",
                "position": "relative", "overflow": "hidden", "minHeight": "100vh"
            }),

            # Right: form
            html.Div([
                # Theme toggle
                html.Div([
                    html.I(className="fas fa-sun",
                           style={"color": "var(--at-green)", "fontSize": "14px"}),
                    html.Label([
                        dcc.Checklist(id="login-theme-toggle",
                                      options=[{"label": "", "value": "dark"}],
                                      value=[], style={"display": "none"}),
                        html.Div(className="theme-slider")
                    ], className="theme-toggle"),
                    html.I(className="fas fa-moon",
                           style={"color": "var(--at-blue)", "fontSize": "14px"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "8px",
                          "position": "absolute", "top": "24px", "right": "24px"}),

                html.Div([
                    html.H2("Connexion", className="auth-title"),
                    html.P("Accédez à votre espace de gestion", className="auth-subtitle"),

                    html.Div([
                        html.Label("Adresse email", className="form-label"),
                        dcc.Input(id="login-email", type="email",
                                  placeholder="votre@email.com",
                                  className="form-input")
                    ], className="form-group"),

                    html.Div([
                        html.Label("Mot de passe", className="form-label"),
                        dcc.Input(id="login-password", type="password",
                                  placeholder="••••••••", className="form-input")
                    ], className="form-group"),

                    html.Div(id="login-error", style={"display": "none"}),

                    html.Button("Se Connecter", id="login-button",
                                className="btn-primary-at"),

                    # ── Lien vers espace admin ────────────────────────────
                    # html.Div([
                    #     html.Div([
                    #         html.I(className="fas fa-shield-halved",
                    #                style={"color": "#E2001A", "marginRight": "6px",
                    #                       "fontSize": "12px"}),
                    #         html.Span("Administrateur ? ",
                    #                   style={"fontSize": "13px",
                    #                          "color": "var(--text-secondary)"}),
                    #         html.A("Espace Admin", href="/admin/login",
                    #                style={"fontSize": "13px", "color": "#E2001A",
                    #                       "fontWeight": "700",
                    #                       "textDecoration": "none"})
                    #     ], style={"display": "flex", "alignItems": "center",
                    #               "justifyContent": "center",
                    #               "padding": "10px 14px",
                    #               "background": "rgba(226,0,26,0.06)",
                    #               "borderRadius": "8px",
                    #               "border": "1px solid rgba(226,0,26,0.15)"})
                    # ], style={"marginTop": "16px"}),

                    # html.Div([
                    #     html.Span("Pas encore de compte? ",
                    #               style={"fontSize": "14px"}),
                    #     html.A("Créer un compte", href="/register",
                    #            style={"fontSize": "14px", "color": "var(--at-blue)",
                    #                   "textDecoration": "none"})
                    # ], style={"textAlign": "center", "marginTop": "16px"}),

                ], style={"maxWidth": "380px", "width": "100%"})

            ], style={
                "flex": "1", "display": "flex", "alignItems": "center",
                "justifyContent": "center", "padding": "60px 40px",
                "background": "var(--bg-secondary)", "position": "relative",
                "minHeight": "100vh"
            }),

        ], style={"display": "flex", "minHeight": "100vh"}),
    ])
])


@callback(
    Output('auth-page-wrapper', 'data-theme'),
    Input('login-theme-toggle', 'value')
)
def toggle_auth_theme(val):
    return "dark" if val and "dark" in val else "light"


@callback(
    Output('login-error', 'children'),
    Output('login-error', 'style'),
    Output('user-session', 'data', allow_duplicate=True),
    Output('login-redirect', 'pathname'),
    Input('login-button', 'n_clicks'),
    State('login-email', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True
)
def login_user(n_clicks, email, password):
    if not n_clicks:
        raise PreventUpdate

    error_style_visible = {
        "display": "block", "color": "#dc3545", "fontSize": "13px",
        "padding": "10px", "borderRadius": "8px",
        "backgroundColor": "rgba(220,53,69,0.1)"
    }
    error_style_hidden = {"display": "none"}

    if not email or not password:
        return ("Veuillez entrer votre email et mot de passe",
                error_style_visible, no_update, no_update)

    result = db_manager.login_user(email, password)

    if result['success']:
        user = result['user']
        role = user.get('role', 'user')

        # ── Si admin essaie de se connecter via /login ────────────
        if role in ('admin', 'super_admin'):
            return (
                [
                    html.I(className="fas fa-shield-halved",
                           style={"marginRight": "6px", "color": "#E2001A"}),
                    "Compte administrateur détecté. ",
                    html.A("Utilisez l'espace admin →", href="/admin/login",
                           style={"color": "#E2001A", "fontWeight": "700"})
                ],
                error_style_visible, no_update, no_update
            )

        # ── Connexion utilisateur normal ──────────────────────────
        session_data = {
            'logged_in': True,
            'user': {
                'firstname': user.get('firstname', ''),
                'lastname':  user.get('lastname', ''),
                'email':     user.get('email', ''),
                'role':      role
            }
        }
        print(f"✅ Connexion user : {email} | role : {role}")
        return "", error_style_hidden, session_data, "/"

    else:
        return result['message'], error_style_visible, no_update, no_update
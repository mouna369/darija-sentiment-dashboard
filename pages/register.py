# # import dash
# # from dash import html, dcc, callback, Input, Output

# # dash.register_page(__name__, path='/register', name='Inscription')

# # layout = html.Div([
# #     html.Div(id='register-page-wrapper', **{"data-theme": "light"}, children=[
# #         html.Div([
# #             # Background shapes
# #             html.Div([
# #                 html.Div(style={
# #                     "position": "absolute", "width": "600px", "height": "600px",
# #                     "borderRadius": "50%", "top": "-200px", "right": "-200px",
# #                     "background": "radial-gradient(circle, rgba(0,154,68,0.1) 0%, transparent 70%)"
# #                 }),
# #                 html.Div(style={
# #                     "position": "absolute", "width": "400px", "height": "400px",
# #                     "borderRadius": "50%", "bottom": "-100px", "left": "-100px",
# #                     "background": "radial-gradient(circle, rgba(0,48,135,0.1) 0%, transparent 70%)"
# #                 }),
# #             ], className="auth-bg-shapes"),

# #             # Right: brand visual
# #             html.Div([
# #                 html.Div([
# #                     html.Img(src="/assets/images/logo.png",
# #                              style={"width": "200px", "filter": "brightness(0) invert(1)", "marginBottom": "40px"}),
# #                     html.H2("Rejoignez la\nplateforme AT", style={
# #                         "color": "white", "fontFamily": "'Cairo', sans-serif",
# #                         "fontSize": "30px", "fontWeight": "700", "lineHeight": "1.3",
# #                         "marginBottom": "20px"
# #                     }),
# #                     html.Div([
# #                         html.Div(style={
# #                             "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
# #                             "padding": "20px", "marginBottom": "16px"
# #                         }, children=[
# #                             html.H4("2.4M+", style={"color": "white", "fontSize": "28px",
# #                                                      "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
# #                             html.P("Abonnés gérés", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
# #                         ]),
# #                         html.Div(style={
# #                             "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
# #                             "padding": "20px", "marginBottom": "16px"
# #                         }, children=[
# #                             html.H4("99.9%", style={"color": "white", "fontSize": "28px",
# #                                                      "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
# #                             html.P("Disponibilité réseau", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
# #                         ]),
# #                         html.Div(style={
# #                             "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
# #                             "padding": "20px"
# #                         }, children=[
# #                             html.H4("48", style={"color": "white", "fontSize": "28px",
# #                                                   "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
# #                             html.P("Wilayas couvertes", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
# #                         ]),
# #                     ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}),
# #                 ], style={"maxWidth": "380px"})
# #             ], style={
# #                 "background": "linear-gradient(135deg, #006b2f 0%, #009A44 50%, #003087 100%)",
# #                 "flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                 "padding": "60px", "position": "relative", "overflow": "hidden", "minHeight": "100vh"
# #             }),

# #             # Left: form
# #             html.Div([
# #                 html.Div([
# #                     # Theme toggle
# #                     html.Div([
# #                     html.I(className="fas fa-sun", style={"color": "var(--at-green)", "fontSize": "14px"}),
# #                     html.Label([
# #                         dcc.Checklist(id="login-theme-toggle", options=[{"label": "", "value": "dark"}],
# #                                       value=[], style={"display": "none"}),
# #                         html.Div(className="theme-slider")
# #                     ], className="theme-toggle"),
# #                     html.I(className="fas fa-moon", style={"color": "var(--at-blue)", "fontSize": "14px"}),
# #                 ], style={"display": "flex", "alignItems": "center", "gap": "8px",
# #                           "position": "absolute", "top": "24px", "right": "24px"}),

# #                     html.H2("Créer un compte", className="auth-title"),
# #                     html.P("Remplissez les informations ci-dessous", className="auth-subtitle"),

# #                     # Name row
# #                     html.Div([
# #                         html.Div([
# #                             html.Label("Prénom", className="form-label"),
# #                             dcc.Input(placeholder="Prénom", type="text", className="form-input")
# #                         ], className="form-group", style={"flex": "1"}),
# #                         html.Div([
# #                             html.Label("Nom", className="form-label"),
# #                             dcc.Input(placeholder="Nom", type="text", className="form-input")
# #                         ], className="form-group", style={"flex": "1"}),
# #                     ], style={"display": "flex", "gap": "14px"}),

# #                     html.Div([
# #                         html.Label("Adresse email", className="form-label"),
# #                         dcc.Input(id="reg-email", type="email", placeholder="email@example.com", className="form-input")
# #                     ], className="form-group"),

# #                     html.Div([
# #                         html.Label("Téléphone", className="form-label"),
# #                         dcc.Input(id="reg-phone", type="tel", placeholder="+213 XX XX XX XX", className="form-input")
# #                     ], className="form-group"),

# #                     html.Div([
# #                         html.Label("Wilaya", className="form-label"),
# #                         dcc.Dropdown(
# #                             options=[{"label": w, "value": w} for w in [
# #                                 "Alger", "Oran", "Constantine", "Annaba", "Blida",
# #                                 "Sétif", "Tizi Ouzou", "Béjaïa", "Tlemcen", "Biskra"
# #                             ]],
# #                             placeholder="Sélectionner votre wilaya",
# #                             style={"fontFamily": "'Poppins', sans-serif"},
# #                             id="reg-wilaya"
# #                         )
# #                     ], className="form-group"),

# #                     html.Div([
# #                         html.Label("Mot de passe", className="form-label"),
# #                         dcc.Input(id="reg-password", type="password", placeholder="Min. 8 caractères", className="form-input")
# #                     ], className="form-group"),

# #                     html.Div([
# #                         html.Label("Confirmer le mot de passe", className="form-label"),
# #                         dcc.Input(id="reg-confirm", type="password", placeholder="••••••••", className="form-input")
# #                     ], className="form-group"),

# #                     html.Div([
# #                         dcc.Checklist(
# #                             options=[{"label": " J'accepte les conditions d'utilisation et la politique de confidentialité",
# #                                       "value": "agree"}],
# #                             value=[],
# #                             style={"fontSize": "12px", "color": "var(--text-secondary)"}
# #                         )
# #                     ], style={"marginBottom": "20px"}),

# #                     html.A(
# #                         html.Button("Créer Mon Compte", className="btn-primary-at"),
# #                         href="/"
# #                     ),

# #                     html.Div([
# #                         html.Span("Déjà inscrit? ", style={"fontSize": "14px", "color": "var(--text-secondary)"}),
# #                         html.A("Se Connecter", href="/login",
# #                                style={"fontSize": "14px", "color": "var(--at-blue)", "fontWeight": "600", "textDecoration": "none"})
# #                     ], style={"textAlign": "center", "marginTop": "20px"}),

# #                 ], style={"maxWidth": "420px", "width": "100%", "position": "relative"})

# #             ], style={
# #                 "flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center",
# #                 "padding": "60px 40px", "background": "var(--bg-secondary)",
# #                 "minHeight": "100vh", "overflowY": "auto"
# #             }),

# #         ], style={"display": "flex", "minHeight": "100vh" }),
# #     ])
# # ])


# # @callback(
# #     Output('register-page-wrapper', 'data-theme'),
# #     Input('register-theme-toggle', 'value')
# # )
# # def toggle_register_theme(val):
# #     return "dark" if val and "dark" in val else "light"
# import dash
# from dash import html, dcc, callback, Input, Output

# dash.register_page(__name__, path='/register', name='Inscription')

# layout = html.Div([
#     html.Div(id='register-page-wrapper', **{"data-theme": "light"}, children=[
#         # Theme toggle - positionné en haut à droite de TOUTE la page
#         html.Div([
#             html.I(className="fas fa-sun", style={"color": "var(--at-green)", "fontSize": "14px"}),
#             html.Label([
#                 dcc.Checklist(id="register-theme-toggle", options=[{"label": "", "value": "dark"}],
#                               value=[], style={"display": "none"}),
#                 html.Div(className="theme-slider")
#             ], className="theme-toggle"),
#             html.I(className="fas fa-moon", style={"color": "var(--at-blue)", "fontSize": "14px"}),
#         ], style={
#            "display": "flex", "alignItems": "center", "gap": "8px",
#                           "position": "absolute", "top": "24px", "right": "24px"}
#         ),
        
#         html.Div([
#             # Background shapes
#             html.Div([
#                 html.Div(style={
#                     "position": "absolute", "width": "600px", "height": "600px",
#                     "borderRadius": "50%", "top": "-200px", "right": "-200px",
#                     "background": "radial-gradient(circle, rgba(0,154,68,0.1) 0%, transparent 70%)"
#                 }),
#                 html.Div(style={
#                     "position": "absolute", "width": "400px", "height": "400px",
#                     "borderRadius": "50%", "bottom": "-100px", "left": "-100px",
#                     "background": "radial-gradient(circle, rgba(0,48,135,0.1) 0%, transparent 70%)"
#                 }),
#             ], className="auth-bg-shapes"),

#             # Right: brand visual
#             html.Div([
#                 html.Div([
#                     html.Img(src="/assets/images/logo.png",
#                              style={"width": "300px", "filter": "brightness(0) invert(1)", "marginBottom": "40px"}),
#                     html.H2("Rejoignez la\nplateforme AT", style={
#                         "color": "white", "fontFamily": "'Cairo', sans-serif",
#                         "fontSize": "30px", "fontWeight": "700", "lineHeight": "1.3",
#                         "marginBottom": "20px"
#                     }),
#                     html.Div([
#                         html.Div(style={
#                             "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
#                             "padding": "20px", "marginBottom": "16px"
#                         }, children=[
#                             html.H4("2.4M+", style={"color": "white", "fontSize": "28px",
#                                                      "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
#                             html.P("Abonnés gérés", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
#                         ]),
#                         html.Div(style={
#                             "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
#                             "padding": "20px", "marginBottom": "16px"
#                         }, children=[
#                             html.H4("99.9%", style={"color": "white", "fontSize": "28px",
#                                                      "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
#                             html.P("Disponibilité réseau", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
#                         ]),
#                         html.Div(style={
#                             "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
#                             "padding": "20px"
#                         }, children=[
#                             html.H4("48", style={"color": "white", "fontSize": "28px",
#                                                   "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
#                             html.P("Wilayas couvertes", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
#                         ]),
#                     ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}),
#                 ], style={"maxWidth": "380px"})
#             ], style={
#                 "background": "linear-gradient(135deg, #006b2f 0%, #009A44 50%, #003087 100%)",
#                 "flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center",
#                 "padding": "60px", "position": "relative", "overflow": "hidden", "minHeight": "100vh"
#             }),

#             # Left: form
#             html.Div([
#                 html.Div([
#                     html.H2("Créer un compte", className="auth-title"),
#                     html.P("Remplissez les informations ci-dessous", className="auth-subtitle"),

#                     # Name row
#                     html.Div([
#                         html.Div([
#                             html.Label("Prénom", className="form-label"),
#                             dcc.Input(placeholder="Prénom", type="text", className="form-input")
#                         ], className="form-group", style={"flex": "1"}),
#                         html.Div([
#                             html.Label("Nom", className="form-label"),
#                             dcc.Input(placeholder="Nom", type="text", className="form-input")
#                         ], className="form-group", style={"flex": "1"}),
#                     ], style={"display": "flex", "gap": "14px"}),

#                     html.Div([
#                         html.Label("Adresse email", className="form-label"),
#                         dcc.Input(id="reg-email", type="email", placeholder="email@example.com", className="form-input")
#                     ], className="form-group"),

#                     html.Div([
#                         html.Label("Téléphone", className="form-label"),
#                         dcc.Input(id="reg-phone", type="tel", placeholder="+213 XX XX XX XX", className="form-input")
#                     ], className="form-group"),

#                     html.Div([
#                         html.Label("Wilaya", className="form-label"),
#                         dcc.Dropdown(
#                             options=[{"label": w, "value": w} for w in [
#                                 "Alger", "Oran", "Constantine", "Annaba", "Blida",
#                                 "Sétif", "Tizi Ouzou", "Béjaïa", "Tlemcen", "Biskra"
#                             ]],
#                             placeholder="Sélectionner votre wilaya",
#                             style={"fontFamily": "'Poppins', sans-serif"},
#                             id="reg-wilaya"
#                         )
#                     ], className="form-group"),

#                     html.Div([
#                         html.Label("Mot de passe", className="form-label"),
#                         dcc.Input(id="reg-password", type="password", placeholder="Min. 8 caractères", className="form-input")
#                     ], className="form-group"),

#                     html.Div([
#                         html.Label("Confirmer le mot de passe", className="form-label"),
#                         dcc.Input(id="reg-confirm", type="password", placeholder="••••••••", className="form-input")
#                     ], className="form-group"),

#                     html.Div([
#                         dcc.Checklist(
#                             options=[{"label": " J'accepte les conditions d'utilisation et la politique de confidentialité",
#                                       "value": "agree"}],
#                             value=[],
#                             style={"fontSize": "12px", "color": "var(--text-secondary)"}
#                         )
#                     ], style={"marginBottom": "20px"}),

#                     html.A(
#                         html.Button("Créer Mon Compte", className="btn-primary-at"),
#                         href="/"
#                     ),

#                     html.Div([
#                         html.Span("Déjà inscrit? ", style={"fontSize": "14px", "color": "var(--text-secondary)"}),
#                         html.A("Se Connecter", href="/login",
#                                style={"fontSize": "14px", "color": "var(--at-blue)", "fontWeight": "600", "textDecoration": "none"})
#                     ], style={"textAlign": "center", "marginTop": "20px"}),

#                 ], style={"maxWidth": "420px", "width": "100%", "position": "relative"})

#             ], style={
#                 "flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center",
#                 "padding": "60px 40px", "background": "var(--bg-secondary)",
#                 "minHeight": "100vh", "overflowY": "auto"
#             }),

#         ], style={"display": "flex", "minHeight": "100vh" }),
#     ])
# ])


# @callback(
#     Output('register-page-wrapper', 'data-theme'),
#     Input('register-theme-toggle', 'value')
# )
# def toggle_register_theme(val):
#     return "dark" if val and "dark" in val else "light"

















# register.py - CORRIGÉ
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import re
from config.db_config import db_manager

dash.register_page(__name__, path='/register', name='Inscription')

layout = html.Div([
    dcc.Location(id='register-redirect', refresh=True),
    
    html.Div(id='register-page-wrapper', **{"data-theme": "light"}, children=[
        # Theme toggle
        html.Div([
            html.I(className="fas fa-sun", style={"color": "var(--at-green)", "fontSize": "14px"}),
            html.Label([
                dcc.Checklist(id="register-theme-toggle", options=[{"label": "", "value": "dark"}],
                              value=[], style={"display": "none"}),
                html.Div(className="theme-slider")
            ], className="theme-toggle"),
            html.I(className="fas fa-moon", style={"color": "var(--at-blue)", "fontSize": "14px"}),
        ], style={
            "display": "flex", "alignItems": "center", "gap": "8px",
            "position": "absolute", "top": "24px", "right": "24px"
        }),
        
        html.Div([
            # Background shapes
            html.Div([
                html.Div(style={
                    "position": "absolute", "width": "600px", "height": "600px",
                    "borderRadius": "50%", "top": "-200px", "right": "-200px",
                    "background": "radial-gradient(circle, rgba(0,154,68,0.1) 0%, transparent 70%)"
                }),
                html.Div(style={
                    "position": "absolute", "width": "400px", "height": "400px",
                    "borderRadius": "50%", "bottom": "-100px", "left": "-100px",
                    "background": "radial-gradient(circle, rgba(0,48,135,0.1) 0%, transparent 70%)"
                }),
            ], className="auth-bg-shapes"),

            # Right: brand visual
            html.Div([
                html.Div([
                    html.Img(src="/assets/images/logo.png",
                             style={"width": "300px", "filter": "brightness(0) invert(1)", "marginBottom": "40px"}),
                    html.H2("Rejoignez la\nplateforme AT", style={
                        "color": "white", "fontFamily": "'Cairo', sans-serif",
                        "fontSize": "30px", "fontWeight": "700", "lineHeight": "1.3",
                        "marginBottom": "20px"
                    }),
                    html.Div([
                        html.Div(style={
                            "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
                            "padding": "20px", "marginBottom": "16px"
                        }, children=[
                            html.H4("2.4M+", style={"color": "white", "fontSize": "28px",
                                                     "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
                            html.P("Abonnés gérés", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
                        ]),
                        html.Div(style={
                            "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
                            "padding": "20px", "marginBottom": "16px"
                        }, children=[
                            html.H4("99.9%", style={"color": "white", "fontSize": "28px",
                                                     "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
                            html.P("Disponibilité réseau", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
                        ]),
                        html.Div(style={
                            "background": "rgba(255,255,255,0.1)", "borderRadius": "16px",
                            "padding": "20px"
                        }, children=[
                            html.H4("48", style={"color": "white", "fontSize": "28px",
                                                  "fontWeight": "700", "margin": "0", "fontFamily": "'Cairo', sans-serif"}),
                            html.P("Wilayas couvertes", style={"color": "rgba(255,255,255,0.7)", "margin": "0", "fontSize": "13px"})
                        ]),
                    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}),
                ], style={"maxWidth": "380px"})
            ], style={
                "background": "linear-gradient(135deg, #006b2f 0%, #009A44 50%, #003087 100%)",
                "flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center",
                "padding": "60px", "position": "relative", "overflow": "hidden", "minHeight": "100vh"
            }),
            # Left: form
            html.Div([
                html.Div([
                    html.Div(id='register-error-message', style={"display": "none"}),
                    html.Div(id='register-success-message', style={"display": "none"}),
                    
                    html.H2("Créer un compte", className="auth-title"),
                    html.P("Remplissez les informations ci-dessous", className="auth-subtitle"),

                    # Name row
                    html.Div([
                        html.Div([
                            html.Label("Prénom", className="form-label"),
                            dcc.Input(id="reg-firstname", placeholder="Prénom", type="text", className="form-input")
                        ], className="form-group", style={"flex": "1"}),
                        html.Div([
                            html.Label("Nom", className="form-label"),
                            dcc.Input(id="reg-lastname", placeholder="Nom", type="text", className="form-input")
                        ], className="form-group", style={"flex": "1"}),
                    ], style={"display": "flex", "gap": "14px"}),

                    html.Div([
                        html.Label("Adresse email", className="form-label"),
                        dcc.Input(id="reg-email", type="email", placeholder="email@example.com", className="form-input")
                    ], className="form-group"),

                    html.Div([
                        html.Label("Téléphone", className="form-label"),
                        dcc.Input(id="reg-phone", type="tel", placeholder="+213 XX XX XX XX", className="form-input")
                    ], className="form-group"),

                    html.Div([
                        html.Label("Wilaya", className="form-label"),
                        dcc.Dropdown(
                            options=[{"label": w, "value": w} for w in ["Alger", "Oran", "Constantine", "Annaba", "Blida", "Sétif", "Tizi Ouzou", "Béjaïa", "Tlemcen", "Biskra"]],
                            placeholder="Sélectionner votre wilaya",
                            id="reg-wilaya"
                        )
                    ], className="form-group"),

                    html.Div([
                        html.Label("Mot de passe", className="form-label"),
                        dcc.Input(id="reg-password", type="password", placeholder="Min. 8 caractères", className="form-input")
                    ], className="form-group"),

                    html.Div([
                        html.Label("Confirmer le mot de passe", className="form-label"),
                        dcc.Input(id="reg-confirm", type="password", placeholder="••••••••", className="form-input")
                    ], className="form-group"),

                    html.Div([
                        dcc.Checklist(
                            id="reg-terms",
                            options=[{"label": " J'accepte les conditions d'utilisation", "value": "agree"}],
                            value=[],
                            style={"fontSize": "12px"}
                        )
                    ], style={"marginBottom": "20px"}),

                    html.Button("Créer Mon Compte", id="register-button", className="btn-primary-at"),

                    html.Div([
                        html.Span("Déjà inscrit? ", style={"fontSize": "14px"}),
                        html.A("Se Connecter", href="/login", style={"fontSize": "14px", "color": "var(--at-blue)", "textDecoration": "none"})
                    ], style={"textAlign": "center", "marginTop": "20px"}),

                ], style={"maxWidth": "420px", "width": "100%", "position": "relative"})

            ], style={
                "flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center",
                "padding": "60px 40px", "background": "var(--bg-secondary)",
                "minHeight": "100vh", "overflowY": "auto"
            }),

        ], style={"display": "flex", "minHeight": "100vh"}),
    ])
])

@callback(
    Output('register-page-wrapper', 'data-theme'),
    Input('register-theme-toggle', 'value')
)
def toggle_register_theme(val):
    return "dark" if val and "dark" in val else "light"

@callback(
    [Output('register-error-message', 'children'),
     Output('register-error-message', 'style'),
     Output('register-success-message', 'children'),
     Output('register-success-message', 'style'),
     Output('register-redirect', 'pathname')],
    Input('register-button', 'n_clicks'),
    [State('reg-firstname', 'value'),
     State('reg-lastname', 'value'),
     State('reg-email', 'value'),
     State('reg-phone', 'value'),
     State('reg-wilaya', 'value'),
     State('reg-password', 'value'),
     State('reg-confirm', 'value'),
     State('reg-terms', 'value')],
    prevent_initial_call=True
)
def register_user(n_clicks, firstname, lastname, email, phone, wilaya, password, confirm, terms):
    if not n_clicks:
        raise PreventUpdate
    
    if not all([firstname, lastname, email, phone, wilaya, password, confirm]):
        return "Tous les champs sont obligatoires", {"display": "block", "color": "#dc3545", "fontSize": "13px", "padding": "10px", "borderRadius": "8px", "backgroundColor": "rgba(220,53,69,0.1)"}, "", {"display": "none"}, no_update
    
    if len(password) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères", {"display": "block", "color": "#dc3545", "fontSize": "13px", "padding": "10px", "borderRadius": "8px", "backgroundColor": "rgba(220,53,69,0.1)"}, "", {"display": "none"}, no_update
    
    if password != confirm:
        return "Les mots de passe ne correspondent pas", {"display": "block", "color": "#dc3545", "fontSize": "13px", "padding": "10px", "borderRadius": "8px", "backgroundColor": "rgba(220,53,69,0.1)"}, "", {"display": "none"}, no_update
    
    if not terms or 'agree' not in terms:
        return "Vous devez accepter les conditions", {"display": "block", "color": "#dc3545", "fontSize": "13px", "padding": "10px", "borderRadius": "8px", "backgroundColor": "rgba(220,53,69,0.1)"}, "", {"display": "none"}, no_update
    
    user_data = {
    "firstname": firstname,
    "lastname": lastname,
    "email": email,
    "password": password_hash,
    "phone": phone,
    "wilaya": wilaya,
    "role": "admin" if email == "tonemail@admin.com" else "user",  # ← condition spéciale
    "is_active": True,
    "created_at": datetime.now(),
    "email_verified": False
}
    result = db_manager.register_user(user_data)
    
    if result['success']:
        return "", {"display": "none"}, "✅ Inscription réussie ! Redirection...", {"display": "block", "color": "#28a745", "fontSize": "13px", "padding": "10px", "borderRadius": "8px", "backgroundColor": "rgba(40,167,69,0.1)"}, "/login"
    else:
        return result['message'], {"display": "block", "color": "#dc3545", "fontSize": "13px", "padding": "10px", "borderRadius": "8px", "backgroundColor": "rgba(220,53,69,0.1)"}, "", {"display": "none"}, no_update
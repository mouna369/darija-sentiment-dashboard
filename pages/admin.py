
# """
# Page Administration — réservée aux utilisateurs avec role='admin' ou 'super_admin'.
# - Modification des seuils d'alerte
# - Liste des utilisateurs avec modal détails + suppression (super_admin uniquement)
# - Création de nouveaux comptes administrateurs (super_admin uniquement)
# - Modification des informations utilisateurs (super_admin uniquement)
# - Modification de l'email (super_admin uniquement)
# """

# import dash
# from dash import html, dcc, callback, Input, Output, State, no_update, ctx, clientside_callback
# from dash.exceptions import PreventUpdate
# import sys, os
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# from components import make_page_layout
# from config.db_config import db_manager
# import config.configuration_seuil as cfg

# dash.register_page(__name__, path='/admin', name='Administration')


# # ══════════════════════════════════════════════════════════════
# # ─── Helpers UI génériques ────────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def section_card(title, icon, children, border_color="#003087"):
#     return html.Div([
#         html.Div([
#             html.I(className=f"fas {icon}",
#                    style={"color": border_color, "marginRight": "10px"}),
#             html.Span(title, style={
#                 "fontWeight": "700", "fontSize": "15px",
#                 "fontFamily": "'Cairo', sans-serif"
#             })
#         ], style={
#             "borderBottom": "1px solid var(--border-color)",
#             "paddingBottom": "14px", "marginBottom": "20px",
#             "display": "flex", "alignItems": "center"
#         }),
#         *children
#     ], style={
#         "background": "var(--bg-card)",
#         "borderRadius": "14px",
#         "padding": "24px",
#         "boxShadow": "0 2px 12px rgba(0,0,0,0.06)",
#         "borderLeft": f"4px solid {border_color}",
#         "marginBottom": "20px"
#     })


# def seuil_row(label, description, input_id, value,
#               unit="%", min_val=0, max_val=100, step=1):
#     return html.Div([
#         html.Div([
#             html.Div(label, style={
#                 "fontWeight": "600", "fontSize": "14px", "marginBottom": "3px",
#                 "color": "var(--text-primary)"
#             }),
#             html.Div(description, style={
#                 "fontSize": "12px", "color": "var(--text-secondary)"
#             })
#         ], style={"flex": "1"}),
#         html.Div([
#             dcc.Input(
#                 id=input_id, type="number", value=value,
#                 min=min_val, max=max_val, step=step,
#                 style={
#                     "width": "90px", "padding": "8px 12px",
#                     "border": "1.5px solid var(--border-color)",
#                     "borderRadius": "8px", "fontSize": "14px",
#                     "fontWeight": "700", "textAlign": "center",
#                     "background": "var(--bg-secondary)",
#                     "color": "var(--text-primary)",
#                     "fontFamily": "'Poppins', sans-serif"
#                 }
#             ),
#             html.Span(unit, style={
#                 "marginLeft": "8px", "fontSize": "13px",
#                 "color": "var(--text-secondary)", "fontWeight": "600"
#             })
#         ], style={"display": "flex", "alignItems": "center"})
#     ], style={
#         "display": "flex", "alignItems": "center",
#         "justifyContent": "space-between",
#         "padding": "14px 0",
#         "borderBottom": "1px solid var(--border-color)"
#     })


# def form_field(label, input_id, placeholder,
#                input_type="text", icon="fa-user"):
#     return html.Div([
#         html.Label(label, style={
#             "fontSize": "12px", "fontWeight": "600",
#             "color": "var(--text-secondary)", "marginBottom": "6px",
#             "display": "block", "textTransform": "uppercase",
#             "letterSpacing": "0.5px"
#         }),
#         html.Div([
#             html.I(className=f"fas {icon}", style={
#                 "position": "absolute", "left": "12px",
#                 "top": "50%", "transform": "translateY(-50%)",
#                 "color": "#999", "fontSize": "13px", "pointerEvents": "none"
#             }),
#             dcc.Input(
#                 id=input_id, type=input_type, placeholder=placeholder,
#                 debounce=False,
#                 style={
#                     "width": "100%", "padding": "10px 12px 10px 36px",
#                     "border": "1.5px solid var(--border-color)",
#                     "borderRadius": "8px", "fontSize": "13px",
#                     "background": "var(--bg-secondary)",
#                     "color": "var(--text-primary)",
#                     "fontFamily": "'Poppins', sans-serif", "outline": "none"
#                 }
#             ),
#         ], style={"position": "relative"}),
#     ], style={"marginBottom": "14px"})


# # ══════════════════════════════════════════════════════════════
# # ─── Modal de confirmation de suppression ─────────────────────
# # ══════════════════════════════════════════════════════════════

# def _make_confirm_modal():
#     return html.Div(
#         id="confirm-delete-modal",
#         style={
#             "display": "none",
#             "position": "fixed", "inset": "0",
#             "zIndex": "10000",
#             "background": "rgba(0,0,0,0.65)",
#             "backdropFilter": "blur(4px)",
#             "alignItems": "center", "justifyContent": "center"
#         },
#         children=[
#             html.Div([
#                 html.Div(
#                     html.I(className="fas fa-triangle-exclamation",
#                            style={"fontSize": "36px", "color": "#E2001A"}),
#                     style={"textAlign": "center", "marginBottom": "16px"}
#                 ),
#                 html.Audio(
#                     id="confirm-delete-sound",
#                     src="/assets/sound/notice-windows-xp-system-sound.mp3",
#                     autoPlay=False,
#                     style={"display": "none"}
#                 ),
#                 html.H3("Confirmer la suppression",
#                         style={
#                             "textAlign": "center", "margin": "0 0 10px",
#                             "fontFamily": "'Cairo', sans-serif",
#                             "fontSize": "17px", "fontWeight": "800",
#                             "color": "var(--text-primary)"
#                         }),
#                 html.Div(id="confirm-delete-message",
#                          style={
#                              "textAlign": "center", "fontSize": "13px",
#                              "color": "var(--text-secondary)",
#                              "marginBottom": "24px", "lineHeight": "1.6"
#                          }),
#                 html.Div([
#                     html.Button([
#                         html.I(className="fas fa-trash", style={"marginRight": "7px"}),
#                         "Oui, supprimer"
#                     ], id="confirm-delete-yes", n_clicks=0,
#                        style={
#                            "background": "linear-gradient(135deg,#E2001A,#a00013)",
#                            "color": "white", "border": "none",
#                            "padding": "10px 22px", "borderRadius": "8px",
#                            "fontSize": "13px", "fontWeight": "700",
#                            "cursor": "pointer", "flex": "1"
#                        }),
#                     html.Button([
#                         html.I(className="fas fa-xmark", style={"marginRight": "7px"}),
#                         "Annuler"
#                     ], id="confirm-delete-no", n_clicks=0,
#                        style={
#                            "background": "var(--bg-secondary)",
#                            "border": "1px solid var(--border-color)",
#                            "color": "var(--text-primary)",
#                            "padding": "10px 22px", "borderRadius": "8px",
#                            "fontSize": "13px", "fontWeight": "600",
#                            "cursor": "pointer", "flex": "1"
#                        }),
#                 ], style={"display": "flex", "gap": "10px"}),
#                 dcc.Store(id="confirm-delete-target"),
#             ], style={
#                 "background": "var(--bg-card)",
#                 "borderRadius": "16px",
#                 "padding": "32px 28px 24px",
#                 "width": "400px",
#                 "maxWidth": "92vw",
#                 "boxShadow": "0 20px 60px rgba(0,0,0,0.35)",
#                 "position": "relative"
#             })
#         ]
#     )


# # ══════════════════════════════════════════════════════════════
# # ─── Modal détails utilisateur ────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def _make_modal():
#     # Champ inline réutilisable pour le formulaire modifier
#     def _field(label, input_id, placeholder, input_type="text"):
#         return html.Div([
#             html.Label(label, style={
#                 "fontSize": "11px", "fontWeight": "700",
#                 "color": "var(--text-secondary)", "marginBottom": "5px",
#                 "display": "block", "textTransform": "uppercase",
#                 "letterSpacing": "0.5px"
#             }),
#             dcc.Input(
#                 id=input_id, type=input_type, placeholder=placeholder,
#                 debounce=False,
#                 style={
#                     "width": "100%", "padding": "9px 12px",
#                     "border": "1.5px solid var(--border-color)",
#                     "borderRadius": "8px", "fontSize": "13px",
#                     "background": "var(--bg-secondary)",
#                     "color": "var(--text-primary)",
#                     "fontFamily": "'Poppins', sans-serif",
#                     "boxSizing": "border-box", "outline": "none"
#                 }
#             ),
#         ], style={"marginBottom": "12px"})

#     return html.Div(
#         id="user-detail-modal",
#         style={
#             "display": "none",
#             "position": "fixed", "inset": "0",
#             "zIndex": "9999",
#             "background": "rgba(0,0,0,0.55)",
#             "backdropFilter": "blur(4px)",
#             "alignItems": "center", "justifyContent": "center"
#         },
#         children=[
#             html.Div([
#                 # ── En-tête du modal ──────────────────────────
#                 html.Div([
#                     html.Div([
#                         html.I(className="fas fa-user-circle",
#                                style={"fontSize": "18px", "color": "#003087",
#                                       "marginRight": "8px"}),
#                         html.Span("Détails du compte",
#                                   style={"fontWeight": "700", "fontSize": "15px",
#                                          "fontFamily": "'Cairo', sans-serif"})
#                     ], style={"display": "flex", "alignItems": "center"}),
#                     html.Button("✕", id="modal-close-btn", n_clicks=0,
#                                 style={
#                                     "background": "none", "border": "none",
#                                     "fontSize": "18px", "cursor": "pointer",
#                                     "color": "var(--text-secondary)",
#                                     "padding": "4px 8px", "borderRadius": "6px"
#                                 })
#                 ], style={
#                     "display": "flex", "justifyContent": "space-between",
#                     "alignItems": "center",
#                     "borderBottom": "1px solid var(--border-color)",
#                     "paddingBottom": "14px", "marginBottom": "16px"
#                 }),

#                 # ── Corps détails (style photo) ───────────────
#                 html.Div(id="modal-body"),

#                 # ── Formulaire modifier — 2 colonnes ─────────
#                 html.Div(id="modal-edit-form", style={"display": "none"}, children=[
#                     html.Div([
#                         html.I(className="fas fa-pen-to-square",
#                                style={"color": "#003087", "marginRight": "8px"}),
#                         html.Span("Modifier les informations",
#                                   style={"fontWeight": "700", "fontSize": "13px",
#                                          "fontFamily": "'Cairo', sans-serif"})
#                     ], style={
#                         "borderTop": "2px solid var(--border-color)",
#                         "paddingTop": "14px", "marginTop": "16px",
#                         "marginBottom": "14px",
#                         "display": "flex", "alignItems": "center"
#                     }),

#                     # 2 colonnes côte à côte — plus de scroll nécessaire
#                     html.Div([
#                         # ── Colonne gauche ──────────────────
#                         html.Div([
#                             _field("Prénom",    "edit-firstname", "Ex: Karim"),
#                             _field("Nom",       "edit-lastname",  "Ex: Benali"),
#                             _field("Téléphone", "edit-phone",
#                                    "+213 XX XX XX XX", input_type="tel"),
#                         ], style={"flex": "1", "minWidth": "0"}),

#                         # ── Colonne droite ──────────────────
#                         html.Div([
#                             _field("Wilaya", "edit-wilaya", "Ex: Alger"),

#                             # Email — super_admin uniquement
#                             html.Div(
#                                 id="edit-email-wrapper",
#                                 style={"display": "none"},
#                                 children=[
#                                     html.Label([
#                                         "Email ",
#                                         html.Span("(Super Admin)", style={
#                                             "color": "#E2001A", "fontSize": "10px"
#                                         })
#                                     ], style={
#                                         "fontSize": "11px", "fontWeight": "700",
#                                         "color": "var(--text-secondary)",
#                                         "marginBottom": "5px", "display": "block",
#                                         "textTransform": "uppercase",
#                                         "letterSpacing": "0.5px"
#                                     }),
#                                     dcc.Input(
#                                         id="edit-email", type="email",
#                                         placeholder="nouvel.email@algerietelecom.dz",
#                                         style={
#                                             "width": "100%",
#                                             "padding": "9px 12px",
#                                             "borderRadius": "8px",
#                                             "border": "1.5px solid #E2001A",
#                                             "background": "rgba(226,0,26,0.04)",
#                                             "color": "var(--text-primary)",
#                                             "fontSize": "13px",
#                                             "fontFamily": "'Poppins', sans-serif",
#                                             "boxSizing": "border-box",
#                                             "outline": "none"
#                                         }
#                                     ),
#                                     html.Div([
#                                         html.I(className="fas fa-triangle-exclamation",
#                                                style={"color": "#E2001A",
#                                                       "marginRight": "5px",
#                                                       "fontSize": "10px"}),
#                                         "Modifier l'email déconnectera l'utilisateur."
#                                     ], style={
#                                         "fontSize": "11px", "color": "#856404",
#                                         "background": "rgba(255,193,7,0.12)",
#                                         "borderRadius": "6px",
#                                         "padding": "5px 8px",
#                                         "marginTop": "6px",
#                                         "marginBottom": "12px",
#                                         "display": "flex", "alignItems": "center"
#                                     }),
#                                 ]
#                             ),

#                             # Rôle
#                             html.Div([
#                                 html.Label("Rôle", style={
#                                     "fontSize": "11px", "fontWeight": "700",
#                                     "color": "var(--text-secondary)",
#                                     "marginBottom": "5px", "display": "block",
#                                     "textTransform": "uppercase",
#                                     "letterSpacing": "0.5px"
#                                 }),
#                                 dcc.Dropdown(
#                                     id="edit-role",
#                                     options=[
#                                         {"label": "Utilisateur",    "value": "user"},
#                                         {"label": "Administrateur", "value": "admin"},
#                                         {"label": "Super Admin",    "value": "super_admin"}
#                                     ],
#                                     style={"width": "100%", "fontSize": "13px"}
#                                 )
#                             ], style={"marginBottom": "12px"}),

#                         ], style={"flex": "1", "minWidth": "0"}),
#                     ], style={"display": "flex", "gap": "16px"}),

#                     html.Div(id="edit-feedback",
#                              style={"fontSize": "12px", "marginTop": "4px"}),
#                 ]),

#                 # ── Footer ────────────────────────────────────
#                 html.Div([
#                     html.Div(id="modal-delete-feedback",
#                              style={"marginBottom": "10px"}),
#                     html.Div([
#                         html.Button([
#                             html.I(className="fas fa-trash",
#                                    style={"marginRight": "6px"}),
#                             "Supprimer"
#                         ], id="modal-delete-btn", n_clicks=0,
#                            style={
#                                "background": "linear-gradient(135deg,#E2001A,#a00013)",
#                                "color": "white", "border": "none",
#                                "padding": "9px 16px", "borderRadius": "8px",
#                                "fontSize": "13px", "fontWeight": "700",
#                                "cursor": "pointer"
#                            }),
#                         html.Div([
#                             html.Button([
#                                 html.I(className="fas fa-pen",
#                                        style={"marginRight": "6px"}),
#                                 "Modifier"
#                             ], id="modal-tab-edit", n_clicks=0,
#                                style={
#                                    "background": "linear-gradient(135deg,#003087,#005080)",
#                                    "color": "white", "border": "none",
#                                    "padding": "9px 16px", "borderRadius": "8px",
#                                    "fontSize": "13px", "fontWeight": "600",
#                                    "cursor": "pointer"
#                                }),
#                             html.Button([
#                                 html.I(className="fas fa-floppy-disk",
#                                        style={"marginRight": "6px"}),
#                                 "Enregistrer"
#                             ], id="edit-save-btn", n_clicks=0,
#                                style={
#                                    "background": "linear-gradient(135deg,#009A44,#007a33)",
#                                    "color": "white", "border": "none",
#                                    "padding": "9px 16px", "borderRadius": "8px",
#                                    "fontSize": "13px", "fontWeight": "600",
#                                    "cursor": "pointer", "display": "none"
#                                }),
#                             html.Button([
#                                 html.I(className="fas fa-xmark",
#                                        style={"marginRight": "6px"}),
#                                 "Fermer"
#                             ], id="modal-cancel-btn", n_clicks=0,
#                                style={
#                                    "background": "var(--bg-secondary)",
#                                    "border": "1px solid var(--border-color)",
#                                    "color": "var(--text-primary)",
#                                    "padding": "9px 16px", "borderRadius": "8px",
#                                    "fontSize": "13px", "fontWeight": "600",
#                                    "cursor": "pointer"
#                                }),
#                         ], style={"display": "flex", "gap": "8px"}),
#                     ], style={"display": "flex", "justifyContent": "space-between",
#                               "alignItems": "center"}),
#                 ], style={
#                     "borderTop": "1px solid var(--border-color)",
#                     "paddingTop": "14px", "marginTop": "16px"
#                 }),

#                 dcc.Store(id="modal-selected-email"),
#                 dcc.Store(id="modal-current-tab", data="details"),

#             ], style={
#                 "background": "var(--bg-card)",
#                 "borderRadius": "16px",
#                 "padding": "24px 28px",
#                 "width": "680px",        # ← plus large pour 2 colonnes
#                 "maxWidth": "95vw",
#                 "maxHeight": "90vh",
#                 "overflowY": "auto",
#                 "boxShadow": "0 20px 60px rgba(0,0,0,0.3)",
#                 "position": "relative"
#             })
#         ]
#     )


# # ══════════════════════════════════════════════════════════════
# # ─── Mise à jour des informations utilisateur ─────────────────
# # ══════════════════════════════════════════════════════════════

# def _update_user_info(current_email, firstname, lastname, phone,
#                       wilaya, role, new_email=None):
#     """
#     Met à jour les informations d'un utilisateur.
#     new_email : si fourni (super_admin seulement), change aussi l'email.
#     Retourne (success: bool, error_msg: str|None)
#     """
#     try:
#         update_fields = {
#             "firstname": firstname.strip(),
#             "lastname":  lastname.strip(),
#             "phone":     phone.strip() if phone else "",
#             "wilaya":    wilaya.strip() if wilaya else "Alger",
#             "role":      role
#         }

#         # Gestion du changement d'email
#         if new_email and new_email.strip().lower() != current_email.lower():
#             new_email_clean = new_email.strip().lower()

#             if "@" not in new_email_clean or "." not in new_email_clean.split("@")[-1]:
#                 return False, "Format d'email invalide."

#             if db_manager.collection.find_one({"email": new_email_clean}):
#                 return False, f"L'email « {new_email_clean} » est déjà utilisé par un autre compte."

#             update_fields["email"] = new_email_clean

#         result = db_manager.collection.update_one(
#             {"email": current_email},
#             {"$set": update_fields}
#         )

#         if "email" in update_fields:
#             return True, None

#         return result.modified_count > 0, None

#     except Exception as e:
#         print(f"Erreur mise à jour: {e}")
#         return False, str(e)


# # ══════════════════════════════════════════════════════════════
# # ─── Liste des utilisateurs ───────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def _build_users_list(is_super=False, current_user_email=None):
#     try:
#         users = list(db_manager.collection.find({}, {"password": 0}))

#         if not users:
#             return html.P("Aucun utilisateur trouvé.",
#                           style={"color": "var(--text-secondary)", "fontSize": "13px"})

#         role_order = {'super_admin': 0, 'admin': 1, 'user': 2}
#         users.sort(key=lambda u: (
#             role_order.get(u.get('role', 'user'), 999),
#             u.get('firstname', '')
#         ))

#         rows = []
#         for u in users:
#             role  = u.get("role", "user")
#             name  = f"{u.get('firstname','')} {u.get('lastname','')}".strip() or "—"
#             email = u.get("email", "—")

#             if role == "super_admin":
#                 badge_color, role_label = "#E2001A", "Super Admin"
#             elif role == "admin":
#                 badge_color, role_label = "#003087", "Admin"
#             else:
#                 badge_color, role_label = "#009A44", "User"

#             avatar = html.Div(
#                 (name[0] if name != "—" else "U").upper(),
#                 style={
#                     "width": "38px", "height": "38px", "borderRadius": "50%",
#                     "background": f"linear-gradient(135deg,{badge_color},#009A44)",
#                     "display": "flex", "alignItems": "center",
#                     "justifyContent": "center", "color": "white",
#                     "fontWeight": "700", "fontSize": "14px", "flexShrink": "0"
#                 }
#             )

#             can_view = is_super or (role != "super_admin")
#             can_view = can_view and (email != current_user_email)

#             actions = html.Div([
#                 html.Span(role_label, style={
#                     "background": badge_color, "color": "white",
#                     "padding": "1px 10px", "borderRadius": "12px",
#                     "fontSize": "11px", "fontWeight": "700",
#                     "marginRight": "8px"
#                 }),
#                 html.Button([
#                     html.I(className="fas fa-eye",
#                            style={"marginRight": "4px", "fontSize": "11px"}),
#                     "Voir"
#                 ],
#                     id={"type": "btn-view-user", "index": email},
#                     n_clicks=0,
#                     style={
#                         "background": "rgba(0,48,135,0.1)",
#                         "border": "1px solid rgba(0,48,135,0.3)",
#                         "color": "#003087", "padding": "4px 10px",
#                         "borderRadius": "6px", "fontSize": "11px",
#                         "fontWeight": "600", "cursor": "pointer",
#                         "marginRight": "6px",
#                         "display": "inline-flex" if can_view else "none"
#                     }
#                 ),
#             ], style={"display": "flex", "alignItems": "center"})

#             rows.append(html.Div([
#                 html.Div([
#                     avatar,
#                     html.Div([
#                         html.Div(name, style={
#                             "fontWeight": "600", "fontSize": "13px",
#                             "color": "var(--text-primary)"
#                         }),
#                         html.Div(email, style={
#                             "fontSize": "11px", "color": "var(--text-secondary)"
#                         })
#                     ])
#                 ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
#                 actions
#             ], style={
#                 "display": "flex", "justifyContent": "space-between",
#                 "alignItems": "center", "padding": "10px 0",
#                 "borderBottom": "1px solid var(--border-color)"
#             }))

#         return html.Div(rows)

#     except Exception as e:
#         return html.P(f"Erreur : {e}",
#                       style={"color": "#E2001A", "fontSize": "12px"})


# # ══════════════════════════════════════════════════════════════
# # ─── Section création de compte ───────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def _build_create_admin_section():
#     return html.Div([
#         html.Div([
#             html.I(className="fas fa-circle-info",
#                    style={"color": "#003087", "marginRight": "8px", "flexShrink": "0"}),
#             html.Span(
#                 "Seul un Super Administrateur peut créer des comptes. "
#                 "Les comptes admin accèdent via /admin/login uniquement.",
#                 style={"fontSize": "12px", "color": "var(--text-secondary)"}
#             )
#         ], style={
#             "display": "flex", "alignItems": "flex-start",
#             "background": "rgba(0,48,135,0.06)", "borderRadius": "8px",
#             "padding": "12px 14px", "marginBottom": "20px", "gap": "8px"
#         }),

#         html.Div([
#             html.Div([
#                 form_field("Prénom", "new-admin-firstname", "Ex: Karim", icon="fa-user"),
#                 form_field("Email", "new-admin-email", "exemple@algerietelecom.dz",
#                            input_type="email", icon="fa-envelope"),
#                 form_field("Mot de passe", "new-admin-password", "Minimum 8 caractères",
#                            input_type="password", icon="fa-lock"),
#             ], style={"flex": "1"}),
#             html.Div([
#                 form_field("Nom", "new-admin-lastname", "Ex: Benali", icon="fa-user"),
#                 form_field("Téléphone", "new-admin-phone", "+213 XX XX XX XX",
#                            icon="fa-phone"),
#                 form_field("Wilaya", "new-admin-wilaya", "Ex: Alger", icon="fa-map-pin"),
#             ], style={"flex": "1"}),
#         ], style={"display": "flex", "gap": "20px"}),

#         html.Div([
#             html.Label("Niveau d'accès", style={
#                 "fontSize": "12px", "fontWeight": "600",
#                 "color": "var(--text-secondary)", "marginBottom": "8px",
#                 "display": "block", "textTransform": "uppercase",
#                 "letterSpacing": "0.5px"
#             }),
#             html.Div([
#                 html.Div([
#                     html.I(className="fas fa-user-shield",
#                            style={"fontSize": "18px", "color": "#003087",
#                                   "marginBottom": "6px"}),
#                     html.Div("Administrateur",
#                              style={"fontWeight": "700", "fontSize": "13px",
#                                     "color": "var(--text-primary)"}),
#                     html.Div("Gestion seuils et dashboard",
#                              style={"fontSize": "11px", "color": "var(--text-secondary)",
#                                     "marginTop": "2px"})
#                 ], id="role-card-admin", n_clicks=0,
#                    style={
#                        "flex": "1", "padding": "16px", "borderRadius": "10px",
#                        "border": "2px solid #003087",
#                        "background": "rgba(0,48,135,0.08)",
#                        "cursor": "pointer", "textAlign": "center"
#                    }),
#                 html.Div([
#                     html.I(className="fas fa-crown",
#                            style={"fontSize": "18px", "color": "#E2001A",
#                                   "marginBottom": "6px"}),
#                     html.Div("Super Admin",
#                              style={"fontWeight": "700", "fontSize": "13px",
#                                     "color": "var(--text-primary)"}),
#                     html.Div("Tous droits + création de comptes",
#                              style={"fontSize": "11px", "color": "var(--text-secondary)",
#                                     "marginTop": "2px"})
#                 ], id="role-card-super", n_clicks=0,
#                    style={
#                        "flex": "1", "padding": "16px", "borderRadius": "10px",
#                        "border": "2px solid var(--border-color)",
#                        "background": "var(--bg-secondary)",
#                        "cursor": "pointer", "textAlign": "center"
#                    }),
#                 html.Div([
#                     html.I(className="fas fa-user",
#                            style={"fontSize": "18px", "color": "#009A44",
#                                   "marginBottom": "6px"}),
#                     html.Div("Utilisateur",
#                              style={"fontWeight": "700", "fontSize": "13px",
#                                     "color": "var(--text-primary)"}),
#                     html.Div("Accès standard à l'application",
#                              style={"fontSize": "11px", "color": "var(--text-secondary)",
#                                     "marginTop": "2px"})
#                 ], id="role-card-user", n_clicks=0,
#                    style={
#                        "flex": "1", "padding": "16px", "borderRadius": "10px",
#                        "border": "2px solid var(--border-color)",
#                        "background": "var(--bg-secondary)",
#                        "cursor": "pointer", "textAlign": "center"
#                    }),
#             ], style={"display": "flex", "gap": "12px", "marginBottom": "20px"}),
#         ]),

#         html.Div(id="create-admin-feedback", style={"marginBottom": "12px"}),

#         html.Button([
#             html.I(className="fas fa-user-plus", style={"marginRight": "8px"}),
#             "Créer le compte"
#         ], id="btn-create-admin", className="btn-primary-at",
#            style={
#                "width": "100%", "padding": "12px", "fontSize": "14px",
#                "fontWeight": "700", "borderRadius": "10px", "cursor": "pointer",
#                "background": "linear-gradient(135deg, #003087, #005080)"
#            }),
#     ])


# # ══════════════════════════════════════════════════════════════
# # ─── make_content ─────────────────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def make_content(theme, user_data=None):
#     cfg.load_seuils_from_db()
#     sn  = cfg.SEUIL_NEGATIF
#     stj = cfg.SEUIL_TAUX_JOUR
#     svj = cfg.SEUIL_VOLUME_JOUR
#     sp  = cfg.SEUIL_PIC_CRITIQUE

#     role     = user_data.get('role', 'user') if user_data else 'user'
#     is_super = role == 'super_admin'

#     return [
#         _make_modal(),
#         _make_confirm_modal(),

#         html.Div([
#             html.Div([
#                 html.I(className="fas fa-shield-halved",
#                        style={"fontSize": "28px", "color": "#003087"}),
#                 html.Div([
#                     html.H2("Panneau de configuration",
#                             style={"margin": "0", "fontFamily": "'Cairo', sans-serif",
#                                    "fontSize": "20px", "fontWeight": "800"}),
#                 ])
#             ], style={"display": "flex", "alignItems": "center", "gap": "14px"}),

#             html.Div([
#                 html.I(className="fas fa-crown" if is_super else "fas fa-user-shield",
#                        style={"marginRight": "6px", "fontSize": "12px"}),
#                 html.Span("Super Administrateur" if is_super else "Administrateur")
#             ], style={
#                 "background": (
#                     "linear-gradient(135deg,#E2001A,#a00013)"
#                     if is_super else
#                     "linear-gradient(135deg,#003087,#009A44)"
#                 ),
#                 "color": "white", "padding": "6px 14px", "borderRadius": "20px",
#                 "fontSize": "12px", "fontWeight": "700",
#                 "display": "flex", "alignItems": "center"
#             })
#         ], style={
#             "display": "flex", "justifyContent": "space-between",
#             "alignItems": "center",
#             "background": "var(--bg-card)", "borderRadius": "14px",
#             "padding": "20px 24px", "marginBottom": "20px",
#             "boxShadow": "0 2px 12px rgba(0,0,0,0.06)"
#         }),

#         html.Div(id="admin-feedback", style={"marginBottom": "16px"}),

#         html.Div([
#             html.Div([
#                 section_card("Seuils d'Alerte Globale", "fa-bell", [
#                     seuil_row("Taux négatif global",
#                               "Déclenche la bannière rouge sur le tableau de bord",
#                               "input-seuil-negatif", sn, unit="%",
#                               min_val=10, max_val=99),
#                 ], border_color="#E2001A"),
#                 section_card("Seuils Journaliers (24h)", "fa-clock", [
#                     seuil_row("Taux négatif journalier",
#                               "Pourcentage de commentaires négatifs sur les 24h",
#                               "input-seuil-taux-jour", stj, unit="%",
#                               min_val=5, max_val=99),
#                     seuil_row("Volume négatif journalier",
#                               "Nombre minimum de messages négatifs pour déclencher l'alarme",
#                               "input-seuil-volume-jour", svj,
#                               unit="msgs", min_val=1, max_val=500, step=1),
#                 ], border_color="#003087"),
#                 section_card("Seuil de Pic Critique", "fa-triangle-exclamation", [
#                     seuil_row("Seuil pic négatif mensuel",
#                               "Taux à partir duquel un pic est comptabilisé dans le mois",
#                               "input-seuil-pic", sp, unit="%", min_val=5, max_val=99),
#                 ], border_color="#009A44"),
#                 html.Button([
#                     html.I(className="fas fa-floppy-disk",
#                            style={"marginRight": "8px"}),
#                     "Sauvegarder les seuils"
#                 ], id="btn-save-seuils", className="btn-primary-at",
#                    style={"width": "100%", "padding": "13px", "fontSize": "14px",
#                           "fontWeight": "700", "borderRadius": "10px",
#                           "cursor": "pointer"}),
#             ], style={"flex": "1.2"}),

#             html.Div([
#                 section_card("Valeurs Actives", "fa-sliders", [
#                     html.Div(id="recap-seuils-actifs",
#                              children=_build_recap(sn, stj, svj, sp))
#                 ], border_color="#003087"),
#                 section_card("Gestion des Utilisateurs", "fa-users-gear", [
#                     html.Div(id="users-count-bar",  children=_build_count_bar()),
#                     html.Div(id="admin-users-list",
#                              children=_build_users_list(
#                                  is_super=is_super,
#                                  current_user_email=user_data.get('email') if user_data else None
#                              ))
#                 ], border_color="#003087"),
#             ], style={"flex": "1"}),

#         ], style={"display": "flex", "gap": "20px",
#                   "alignItems": "flex-start", "marginBottom": "20px"}),

#         section_card(
#             "Créer un Compte", "fa-user-plus",
#             [
#                 _build_create_admin_section() if is_super else
#                 html.Div([
#                     html.I(className="fas fa-lock",
#                            style={"fontSize": "32px", "color": "#bbb",
#                                   "marginBottom": "12px"}),
#                     html.P("Réservé aux Super Administrateurs.",
#                            style={"color": "var(--text-secondary)", "fontSize": "13px"}),
#                 ], style={"textAlign": "center", "padding": "30px"})
#             ],
#             border_color="#E2001A" if is_super else "#bbb"
#         ),
#     ]


# # ══════════════════════════════════════════════════════════════
# # ─── Builders helpers ─────────────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def _build_count_bar():
#     try:
#         total  = db_manager.collection.count_documents({})
#         admins = db_manager.collection.count_documents(
#             {"role": {"$in": ["admin", "super_admin"]}}
#         )
#         users = total - admins
#         return html.Div([
#             html.Span(f"👥 {total} comptes total",
#                       style={"fontSize": "12px", "color": "var(--text-secondary)",
#                              "marginRight": "12px"}),
#             html.Span(f"🛡️ {admins} admin(s)",
#                       style={"fontSize": "12px", "color": "#003087",
#                              "marginRight": "12px"}),
#             html.Span(f"👤 {users} user(s)",
#                       style={"fontSize": "12px", "color": "#009A44"}),
#         ], style={"marginBottom": "14px", "display": "flex", "flexWrap": "wrap",
#                   "gap": "4px"})
#     except:
#         return html.Div()


# def _recap_item(label, value, unit, color):
#     return html.Div([
#         html.Div(label, style={
#             "fontSize": "12px", "color": "var(--text-secondary)", "marginBottom": "4px"
#         }),
#         html.Div([
#             html.Span(str(value), style={
#                 "fontSize": "24px", "fontWeight": "800",
#                 "color": color, "fontFamily": "'Cairo', sans-serif"
#             }),
#             html.Span(f" {unit}", style={
#                 "fontSize": "13px", "color": "var(--text-secondary)"
#             })
#         ])
#     ], style={
#         "background": "var(--bg-secondary)", "borderRadius": "10px",
#         "padding": "14px", "textAlign": "center", "flex": "1"
#     })


# def _build_recap(sn, stj, svj, sp):
#     return html.Div([
#         _recap_item("Alarme globale", sn, "%", "#E2001A"),
#         _recap_item("Alarme 24h", stj, "%", "#003087"),
#         _recap_item("Volume 24h", svj, "msgs", "#003087"),
#         _recap_item("Pic critique", sp, "%", "#009A44"),
#     ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})


# def _get_user_by_email(email):
#     try:
#         return db_manager.collection.find_one({"email": email}, {"password": 0})
#     except:
#         return None


# # ══════════════════════════════════════════════════════════════
# # ─── _build_modal_body — style photo (header bleu + cartes) ──
# # ══════════════════════════════════════════════════════════════

# def _build_modal_body(user):
#     if not user:
#         return html.P("Utilisateur introuvable.", style={"color": "#E2001A"})

#     role  = user.get("role", "user")
#     name  = f"{user.get('firstname','')} {user.get('lastname','')}".strip() or "—"
#     email = user.get("email", "—")

#     if role == "super_admin":
#         badge_color, role_label = "#E2001A", "Super Administrateur"
#     elif role == "admin":
#         badge_color, role_label = "#003087", "Administrateur"
#     else:
#         badge_color, role_label = "#009A44", "Utilisateur"

#     created_at  = user.get("created_at")
#     created_str = created_at.strftime("%d/%m/%Y à %H:%M") if created_at else "—"

#     # Carte d'info individuelle (style grille)
#     def info_card(icon, label, value):
#         return html.Div([
#             html.Div([
#                 html.I(className=f"fas {icon}",
#                        style={"fontSize": "11px", "color": "#003087",
#                               "marginRight": "5px"}),
#                 html.Span(label, style={
#                     "fontSize": "10px", "fontWeight": "700",
#                     "color": "#003087", "textTransform": "uppercase",
#                     "letterSpacing": "0.6px"
#                 })
#             ], style={"marginBottom": "5px"}),
#             html.Div(value or "—", style={
#                 "fontSize": "13px", "fontWeight": "600",
#                 "color": "var(--text-primary)"
#             })
#         ], style={
#             "background": "var(--bg-secondary)",
#             "borderRadius": "10px",
#             "padding": "12px 14px",
#             "flex": "1",
#             "minWidth": "130px"
#         })

#     # Badge statut
#     def status_badge(ok, label_ok, label_ko):
#         return html.Span(
#             ("✓ " + label_ok) if ok else ("✗ " + label_ko),
#             style={
#                 "background": "rgba(0,154,68,0.12)" if ok else "rgba(226,0,26,0.10)",
#                 "color": "#009A44" if ok else "#E2001A",
#                 "padding": "3px 10px", "borderRadius": "12px",
#                 "fontSize": "12px", "fontWeight": "700"
#             }
#         )

#     return html.Div([
#         # ── Header bleu dégradé (style photo) ────────────────
#         html.Div([
#             html.Div(
#                 (name[0] if name != "—" else "U").upper(),
#                 style={
#                     "width": "52px", "height": "52px", "borderRadius": "50%",
#                     "background": "rgba(255,255,255,0.22)",
#                     "border": "2px solid rgba(255,255,255,0.45)",
#                     "display": "flex", "alignItems": "center",
#                     "justifyContent": "center", "color": "white",
#                     "fontWeight": "800", "fontSize": "20px", "flexShrink": "0"
#                 }
#             ),
#             html.Div([
#                 html.Div(name, style={
#                     "fontWeight": "800", "fontSize": "16px",
#                     "color": "white", "marginBottom": "4px",
#                     "fontFamily": "'Cairo', sans-serif"
#                 }),
#                 html.Div([
#                     html.I(className="fas fa-envelope",
#                            style={"fontSize": "11px", "marginRight": "5px",
#                                   "opacity": "0.8"}),
#                     html.Span(email, style={"fontSize": "12px", "opacity": "0.85"})
#                 ], style={"color": "white", "display": "flex", "alignItems": "center"}),
#             ], style={"flex": "1"}),
#             html.Span(role_label, style={
#                 "background": "rgba(255,255,255,0.20)",
#                 "border": "1px solid rgba(255,255,255,0.4)",
#                 "color": "white", "padding": "4px 12px",
#                 "borderRadius": "14px", "fontSize": "11px",
#                 "fontWeight": "700", "whiteSpace": "nowrap"
#             })
#         ], style={
#             "background": "linear-gradient(135deg, #003087 0%, #0050b3 100%)",
#             "borderRadius": "12px",
#             "padding": "18px 20px",
#             "display": "flex", "alignItems": "center", "gap": "14px",
#             "marginBottom": "14px"
#         }),

#         # ── Grille de cartes infos ────────────────────────────
#         html.Div([
#             info_card("fa-phone",    "Téléphone", user.get("phone",  "—")),
#             info_card("fa-map-pin",  "Wilaya",    user.get("wilaya", "—")),
#             info_card("fa-calendar", "Créé le",   created_str),
#             info_card("fa-user-pen", "Créé par",
#                       user.get("created_by", "Inscription publique")),
#         ], style={
#             "display": "flex", "flexWrap": "wrap", "gap": "10px",
#             "marginBottom": "12px"
#         }),

#         # ── Badges statut ─────────────────────────────────────
#         html.Div([
#             html.Div([
#                 html.Span("Compte actif",
#                           style={"fontSize": "12px",
#                                  "color": "var(--text-secondary)",
#                                  "marginRight": "8px"}),
#                 status_badge(user.get("is_active"), "Actif", "Inactif"),
#             ], style={"display": "flex", "alignItems": "center"}),
#             html.Div([
#                 html.Span("Email vérifié",
#                           style={"fontSize": "12px",
#                                  "color": "var(--text-secondary)",
#                                  "marginRight": "8px"}),
#                 status_badge(user.get("email_verified"), "Vérifié", "Non vérifié"),
#             ], style={"display": "flex", "alignItems": "center"}),
#         ], style={
#             "display": "flex", "gap": "20px", "flexWrap": "wrap",
#             "padding": "12px 14px",
#             "background": "var(--bg-secondary)",
#             "borderRadius": "10px"
#         }),
#     ])


# # ══════════════════════════════════════════════════════════════
# # ─── Layout ───────────────────────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# def layout(**kwargs):
#     return html.Div([
#         dcc.Store(id='user-session', storage_type='session'),
#         dcc.Store(id='selected-new-role', data='admin'),
#         dcc.Store(id='modal-selected-email'),
#         dcc.Store(id='modal-current-tab', data='details'),
#         dcc.Location(id='admin-redirect', refresh=True),
#         html.Div(id='admin-page-root')
#     ])


# # ══════════════════════════════════════════════════════════════
# # ─── Callbacks ────────────────────────────────────────────────
# # ══════════════════════════════════════════════════════════════

# @callback(
#     Output('admin-page-root', 'children'),
#     Input('user-session', 'data'),
#     Input('admin-redirect', 'pathname')
# )
# def render_admin_page(session_data, pathname):
#     if not session_data or not session_data.get('logged_in'):
#         return dcc.Location(href='/admin/login', id='_redir1')

#     user = session_data.get('user', {})
#     role = user.get('role', 'user')

#     if role not in ('admin', 'super_admin'):
#         return html.Div([
#             html.Div([
#                 html.I(className="fas fa-ban",
#                        style={"fontSize": "48px", "color": "#E2001A",
#                               "marginBottom": "16px"}),
#                 html.H2("Accès Refusé",
#                         style={"fontFamily": "'Cairo', sans-serif",
#                                "color": "var(--text-primary)"}),
#                 html.P("Cette page est réservée aux administrateurs.",
#                        style={"color": "var(--text-secondary)"}),
#                 html.A("Retour au tableau de bord", href="/",
#                        style={"color": "#003087", "fontWeight": "600",
#                               "textDecoration": "none", "fontSize": "14px"})
#             ], style={
#                 "textAlign": "center", "padding": "80px 40px",
#                 "background": "var(--bg-card)", "borderRadius": "14px",
#                 "maxWidth": "500px", "margin": "80px auto"
#             })
#         ])

#     return make_page_layout(
#         active_page="admin",
#         title="Panneau d'Administration",
#         subtitle="Configuration des seuils • Gestion des utilisateurs",
#         content=make_content('light', user),
#         theme='light',
#         user_data=user
#     )


# # ── Ouvrir / fermer le modal détails ─────────────────────────

# @callback(
#     Output('user-detail-modal',     'style'),
#     Output('modal-body',            'children'),
#     Output('modal-selected-email',  'data'),
#     Output('modal-delete-feedback', 'children'),
#     Output('modal-current-tab',     'data'),
#     Output('modal-body',            'style',  allow_duplicate=True),
#     Output('modal-edit-form',       'style'),
#     Output('modal-tab-edit',        'style',  allow_duplicate=True),
#     Output('edit-save-btn',         'style',  allow_duplicate=True),
#     Input({'type': 'btn-view-user', 'index': dash.ALL}, 'n_clicks'),
#     Input('modal-close-btn',  'n_clicks'),
#     Input('modal-cancel-btn', 'n_clicks'),
#     prevent_initial_call=True
# )
# def open_close_modal(view_clicks, close1, close2):
#     triggered = ctx.triggered_id

#     modal_hidden  = {"display": "none",  "position": "fixed", "inset": "0",
#                      "zIndex": "9999",   "background": "rgba(0,0,0,0.55)",
#                      "backdropFilter": "blur(4px)",
#                      "alignItems": "center", "justifyContent": "center"}
#     modal_visible = {**modal_hidden, "display": "flex"}

#     btn_modifier  = {"background": "linear-gradient(135deg,#003087,#005080)",
#                      "color": "white", "border": "none",
#                      "padding": "9px 16px", "borderRadius": "8px",
#                      "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
#                      "display": "inline-flex", "alignItems": "center"}
#     btn_save_hidden = {"background": "linear-gradient(135deg,#009A44,#007a33)",
#                        "color": "white", "border": "none",
#                        "padding": "9px 16px", "borderRadius": "8px",
#                        "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
#                        "display": "none"}

#     if triggered in ('modal-close-btn', 'modal-cancel-btn'):
#         return (modal_hidden, no_update, no_update, "", "details",
#                 {"display": "block"}, {"display": "none"},
#                 btn_modifier, btn_save_hidden)

#     if isinstance(triggered, dict) and triggered.get('type') == 'btn-view-user':
#         email = triggered.get('index')
#         if not email or not any(v for v in view_clicks if v):
#             raise PreventUpdate
#         user = _get_user_by_email(email)
#         body = _build_modal_body(user)
#         return (modal_visible, body, email, "", "details",
#                 {"display": "block"}, {"display": "none"},
#                 btn_modifier, btn_save_hidden)

#     raise PreventUpdate


# # ── Gestion onglet Détails / Modifier ────────────────────────

# @callback(
#     Output("modal-tab-edit",     "style", allow_duplicate=True),
#     Output("modal-body",         "style", allow_duplicate=True),
#     Output("modal-edit-form",    "style", allow_duplicate=True),
#     Output("modal-current-tab",  "data",  allow_duplicate=True),
#     Output("edit-save-btn",      "style", allow_duplicate=True),
#     Input("modal-tab-edit", "n_clicks"),
#     State("modal-current-tab", "data"),
#     prevent_initial_call=True
# )
# def switch_tab(n_edit, current_tab):
#     btn_modifier_visible = {
#         "background": "linear-gradient(135deg,#003087,#005080)",
#         "color": "white", "border": "none", "padding": "9px 16px",
#         "borderRadius": "8px", "fontSize": "13px", "fontWeight": "600",
#         "cursor": "pointer", "display": "inline-flex", "alignItems": "center"
#     }
#     btn_modifier_hidden  = {**btn_modifier_visible, "display": "none"}
#     btn_save_visible     = {
#         "background": "linear-gradient(135deg,#009A44,#007a33)",
#         "color": "white", "border": "none", "padding": "9px 16px",
#         "borderRadius": "8px", "fontSize": "13px", "fontWeight": "600",
#         "cursor": "pointer", "display": "inline-flex", "alignItems": "center"
#     }
#     btn_save_hidden = {**btn_save_visible, "display": "none"}

#     if current_tab == "edit":
#         return (btn_modifier_visible, {"display": "block"},
#                 {"display": "none"}, "details", btn_save_hidden)
#     else:
#         return (btn_modifier_hidden, {"display": "block"},
#                 {"display": "block"}, "edit", btn_save_visible)


# # ── Charger les données dans le formulaire ────────────────────

# @callback(
#     Output("edit-firstname",     "value"),
#     Output("edit-lastname",      "value"),
#     Output("edit-phone",         "value"),
#     Output("edit-wilaya",        "value"),
#     Output("edit-role",          "value"),
#     Output("edit-email",         "value"),
#     Output("edit-email-wrapper", "style"),
#     Input("modal-selected-email", "data"),
#     State("user-session", "data"),
#     prevent_initial_call=True
# )
# def load_user_for_edit(email, session_data):
#     if not email:
#         return "", "", "", "", "user", "", {"display": "none", "marginBottom": "12px"}

#     visitor_role = (session_data or {}).get('user', {}).get('role', 'user')
#     is_super = visitor_role == 'super_admin'

#     email_wrapper_style = (
#         {"display": "block", "marginBottom": "12px"}
#         if is_super else
#         {"display": "none",  "marginBottom": "12px"}
#     )

#     user = _get_user_by_email(email)
#     if user:
#         return (
#             user.get("firstname", ""),
#             user.get("lastname",  ""),
#             user.get("phone",     ""),
#             user.get("wilaya",    "Alger"),
#             user.get("role",      "user"),
#             user.get("email",     ""),
#             email_wrapper_style
#         )
#     return "", "", "", "", "user", "", {"display": "none", "marginBottom": "12px"}


# # ── Sauvegarder les modifications ────────────────────────────

# @callback(
#     Output("edit-feedback",       "children"),
#     Output("modal-body",          "children", allow_duplicate=True),
#     Output("admin-users-list",    "children", allow_duplicate=True),
#     Output("users-count-bar",     "children", allow_duplicate=True),
#     Output("modal-current-tab",   "data",     allow_duplicate=True),
#     Output("modal-tab-edit",      "style",    allow_duplicate=True),
#     Output("modal-body",          "style",    allow_duplicate=True),
#     Output("modal-edit-form",     "style",    allow_duplicate=True),
#     Output("edit-save-btn",       "style",    allow_duplicate=True),
#     Output("modal-selected-email","data",     allow_duplicate=True),
#     Input("edit-save-btn", "n_clicks"),
#     State("modal-selected-email", "data"),
#     State("edit-firstname",       "value"),
#     State("edit-lastname",        "value"),
#     State("edit-phone",           "value"),
#     State("edit-wilaya",          "value"),
#     State("edit-role",            "value"),
#     State("edit-email",           "value"),
#     State("user-session",         "data"),
#     prevent_initial_call=True
# )
# def save_user_edit(n_clicks, current_email, firstname, lastname,
#                    phone, wilaya, role, new_email, session_data):
#     if not n_clicks or not current_email:
#         raise PreventUpdate

#     btn_modifier  = {"background": "linear-gradient(135deg,#003087,#005080)",
#                      "color": "white", "border": "none",
#                      "padding": "9px 16px", "borderRadius": "8px",
#                      "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
#                      "display": "inline-flex", "alignItems": "center"}
#     btn_save_hidden = {"background": "linear-gradient(135deg,#009A44,#007a33)",
#                        "color": "white", "border": "none",
#                        "padding": "9px 16px", "borderRadius": "8px",
#                        "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
#                        "display": "none"}

#     visitor_role = (session_data or {}).get('user', {}).get('role', 'user')
#     is_super = visitor_role == 'super_admin'

#     if visitor_role not in ('admin', 'super_admin'):
#         return (html.Div("⛔ Réservé aux administrateurs.",
#                          style={"color": "#E2001A"}),
#                 *([no_update] * 9))

#     if not firstname or len(firstname.strip()) < 2:
#         return (html.Div("❌ Prénom requis (min. 2 caractères)",
#                          style={"color": "#E2001A"}),
#                 *([no_update] * 9))
#     if not lastname or len(lastname.strip()) < 2:
#         return (html.Div("❌ Nom requis (min. 2 caractères)",
#                          style={"color": "#E2001A"}),
#                 *([no_update] * 9))

#     email_to_set = new_email if is_super else None

#     success, err_msg = _update_user_info(
#         current_email, firstname, lastname, phone, wilaya, role, email_to_set
#     )

#     if not success:
#         msg = err_msg or "Erreur lors de l'enregistrement"
#         return (html.Div(f"❌ {msg}", style={"color": "#E2001A"}),
#                 *([no_update] * 9))

#     effective_email = (
#         new_email.strip().lower()
#         if (is_super and new_email and
#             new_email.strip().lower() != current_email.lower())
#         else current_email
#     )

#     user = _get_user_by_email(effective_email)
#     body = _build_modal_body(user)

#     return (
#         html.Div("✅ Modifications enregistrées !", style={"color": "#009A44"}),
#         body,
#         _build_users_list(is_super=is_super),
#         _build_count_bar(),
#         "details",
#         btn_modifier,
#         {"display": "block"},
#         {"display": "none"},
#         btn_save_hidden,
#         effective_email,
#     )


# # ── Annuler les modifications ─────────────────────────────────

# @callback(
#     Output("modal-current-tab",  "data",  allow_duplicate=True),
#     Output("modal-tab-edit",     "style", allow_duplicate=True),
#     Output("modal-body",         "style", allow_duplicate=True),
#     Output("modal-edit-form",    "style", allow_duplicate=True),
#     Input("edit-cancel-btn", "n_clicks"),
#     prevent_initial_call=True
# )
# def cancel_edit(n_clicks):
#     if not n_clicks:
#         raise PreventUpdate
#     btn_modifier = {
#         "background": "linear-gradient(135deg,#003087,#005080)",
#         "color": "white", "border": "none", "padding": "9px 16px",
#         "borderRadius": "8px", "fontSize": "13px", "fontWeight": "600",
#         "cursor": "pointer", "display": "inline-flex", "alignItems": "center"
#     }
#     return "details", btn_modifier, {"display": "block"}, {"display": "none"}


# # ── Ouvrir le modal de confirmation ──────────────────────────

# @callback(
#     Output('confirm-delete-modal',   'style'),
#     Output('confirm-delete-message', 'children'),
#     Output('confirm-delete-target',  'data'),
#     Input('modal-delete-btn',                             'n_clicks'),
#     Input({'type': 'btn-delete-user', 'index': dash.ALL}, 'n_clicks'),
#     Input('confirm-delete-no',                            'n_clicks'),
#     State('modal-selected-email', 'data'),
#     prevent_initial_call=True
# )
# def toggle_confirm_modal(n_modal_btn, list_clicks, n_cancel, modal_email):
#     triggered = ctx.triggered_id

#     confirm_hidden  = {"display": "none",  "position": "fixed", "inset": "0",
#                        "zIndex": "10000",  "background": "rgba(0,0,0,0.65)",
#                        "backdropFilter": "blur(4px)",
#                        "alignItems": "center", "justifyContent": "center"}
#     confirm_visible = {**confirm_hidden, "display": "flex"}

#     if triggered == 'confirm-delete-no':
#         return confirm_hidden, no_update, no_update

#     if triggered == 'modal-delete-btn':
#         if not n_modal_btn:
#             raise PreventUpdate
#         email = modal_email
#         if not email:
#             raise PreventUpdate
#         user = _get_user_by_email(email)
#         name = (f"{user.get('firstname','')} {user.get('lastname','')}".strip()
#                 if user else email)
#         msg = html.Span([
#             "Vous êtes sur le point de supprimer définitivement le compte de ",
#             html.Strong(name or email), f" ({email}).",
#             html.Br(), "Cette action est irréversible."
#         ])
#         return confirm_visible, msg, {"email": email, "source": "modal"}

#     if isinstance(triggered, dict) and triggered.get('type') == 'btn-delete-user':
#         if not any(v for v in list_clicks if v):
#             raise PreventUpdate
#         email = triggered.get('index')
#         if not email:
#             raise PreventUpdate
#         user = _get_user_by_email(email)
#         name = (f"{user.get('firstname','')} {user.get('lastname','')}".strip()
#                 if user else email)
#         msg = html.Span([
#             "Vous êtes sur le point de supprimer définitivement le compte de ",
#             html.Strong(name or email), f" ({email}).",
#             html.Br(), "Cette action est irréversible."
#         ])
#         return confirm_visible, msg, {"email": email, "source": "list"}

#     raise PreventUpdate


# # ── Suppression effective après confirmation ──────────────────

# @callback(
#     Output('confirm-delete-modal',  'style',    allow_duplicate=True),
#     Output('admin-users-list',      'children', allow_duplicate=True),
#     Output('users-count-bar',       'children', allow_duplicate=True),
#     Output('admin-feedback',        'children', allow_duplicate=True),
#     Output('user-detail-modal',     'style',    allow_duplicate=True),
#     Output('modal-delete-feedback', 'children', allow_duplicate=True),
#     Input('confirm-delete-yes', 'n_clicks'),
#     State('confirm-delete-target', 'data'),
#     State('user-session',          'data'),
#     prevent_initial_call=True
# )
# def execute_confirmed_delete(n_yes, target, session_data):
#     if not n_yes or not target:
#         raise PreventUpdate

#     confirm_hidden = {"display": "none",  "position": "fixed", "inset": "0",
#                       "zIndex": "10000",  "background": "rgba(0,0,0,0.65)",
#                       "backdropFilter": "blur(4px)",
#                       "alignItems": "center", "justifyContent": "center"}
#     modal_hidden   = {"display": "none",  "position": "fixed", "inset": "0",
#                       "zIndex": "9999",   "background": "rgba(0,0,0,0.55)",
#                       "backdropFilter": "blur(4px)",
#                       "alignItems": "center", "justifyContent": "center"}

#     email  = target.get("email", "")
#     source = target.get("source", "list")

#     current_user  = (session_data or {}).get('user', {})
#     current_role  = current_user.get('role', 'user')
#     current_email = current_user.get('email', '')

#     if current_role not in ('admin', 'super_admin'):
#         return (confirm_hidden, no_update, no_update,
#                 html.Div("⛔ Action réservée aux administrateurs.",
#                          style={"color": "#E2001A", "fontSize": "13px"}),
#                 no_update, no_update)

#     if email == current_email:
#         return (confirm_hidden, no_update, no_update,
#                 html.Div("⛔ Vous ne pouvez pas supprimer votre propre compte.",
#                          style={"color": "#E2001A", "fontSize": "13px"}),
#                 no_update, no_update)

#     target_user = _get_user_by_email(email)
#     if target_user and target_user.get('role') == 'super_admin' and current_role != 'super_admin':
#         return (confirm_hidden, no_update, no_update,
#                 html.Div("⛔ Un administrateur ne peut pas supprimer un Super Admin.",
#                          style={"color": "#E2001A", "fontSize": "13px"}),
#                 no_update, no_update)

#     try:
#         result = db_manager.collection.delete_one({"email": email})
#         if result.deleted_count == 0:
#             return (confirm_hidden, no_update, no_update,
#                     html.Div("❌ Compte introuvable.",
#                              style={"color": "#E2001A", "fontSize": "13px"}),
#                     no_update, no_update)

#         print(f"🗑️ Compte supprimé : {email} par {current_email}")

#         feedback = html.Div([
#             html.I(className="fas fa-check-circle",
#                    style={"marginRight": "8px", "color": "#009A44"}),
#             f"Compte {email} supprimé avec succès."
#         ], style={
#             "color": "#155724", "padding": "12px 16px", "borderRadius": "8px",
#             "fontSize": "13px", "fontWeight": "600",
#             "background": "rgba(0,154,68,0.1)",
#             "display": "flex", "alignItems": "center"
#         })

#         is_super     = current_role == 'super_admin'
#         modal_style  = modal_hidden if source == "modal" else no_update
#         return (
#             confirm_hidden,
#             _build_users_list(is_super=is_super),
#             _build_count_bar(),
#             feedback,
#             modal_style,
#             ""
#         )

#     except Exception as e:
#         return (confirm_hidden, no_update, no_update,
#                 html.Div(f"❌ Erreur : {e}",
#                          style={"color": "#E2001A", "fontSize": "13px"}),
#                 no_update, no_update)


# # ── Sélection rôle (3 cartes) ─────────────────────────────────

# @callback(
#     Output('selected-new-role', 'data'),
#     Output('role-card-admin',   'style'),
#     Output('role-card-super',   'style'),
#     Output('role-card-user',    'style'),
#     Input('role-card-admin', 'n_clicks'),
#     Input('role-card-super', 'n_clicks'),
#     Input('role-card-user',  'n_clicks'),
#     prevent_initial_call=True
# )
# def select_role(n_admin, n_super, n_user):
#     triggered = ctx.triggered_id
#     base = {"flex": "1", "padding": "16px", "borderRadius": "10px",
#             "cursor": "pointer", "textAlign": "center"}
#     active_admin = {**base, "border": "2px solid #003087",
#                     "background": "rgba(0,48,135,0.08)"}
#     active_super = {**base, "border": "2px solid #E2001A",
#                     "background": "rgba(226,0,26,0.08)"}
#     active_user  = {**base, "border": "2px solid #009A44",
#                     "background": "rgba(0,154,68,0.08)"}
#     inactive     = {**base, "border": "2px solid var(--border-color)",
#                     "background": "var(--bg-secondary)"}

#     if triggered == 'role-card-super':
#         return 'super_admin', inactive, active_super, inactive
#     if triggered == 'role-card-user':
#         return 'user', inactive, inactive, active_user
#     return 'admin', active_admin, inactive, inactive


# # ── Sauvegarde seuils ─────────────────────────────────────────

# @callback(
#     Output('admin-feedback',      'children'),
#     Output('recap-seuils-actifs', 'children'),
#     Input('btn-save-seuils', 'n_clicks'),
#     State('input-seuil-negatif',    'value'),
#     State('input-seuil-taux-jour',  'value'),
#     State('input-seuil-volume-jour','value'),
#     State('input-seuil-pic',        'value'),
#     State('user-session', 'data'),
#     prevent_initial_call=True
# )
# def save_seuils(n_clicks, sn, stj, svj, sp, session_data):
#     if not n_clicks:
#         raise PreventUpdate

#     role = (session_data or {}).get('user', {}).get('role', 'user')
#     if role not in ('admin', 'super_admin'):
#         return html.Div("⛔ Action non autorisée.", style={
#             "color": "#E2001A", "padding": "12px", "borderRadius": "8px",
#             "background": "rgba(226,0,26,0.08)", "fontSize": "13px"
#         }), no_update

#     errors = []
#     if sn  is None or not (10 <= sn  <= 99):  errors.append("Alarme globale : 10–99%")
#     if stj is None or not (5  <= stj <= 99):   errors.append("Taux journalier : 5–99%")
#     if svj is None or not (1  <= svj <= 500):  errors.append("Volume journalier : 1–500")
#     if sp  is None or not (5  <= sp  <= 99):   errors.append("Pic critique : 5–99%")

#     if errors:
#         return html.Div([
#             html.Div("⚠️ Erreurs :", style={"fontWeight": "700", "marginBottom": "6px"}),
#             *[html.Div(f"• {e}", style={"fontSize": "12px"}) for e in errors]
#         ], style={"color": "#856404", "padding": "12px", "borderRadius": "8px",
#                   "background": "rgba(255,193,7,0.12)", "fontSize": "13px"}), no_update

#     cfg.SEUIL_NEGATIF      = int(sn)
#     cfg.SEUIL_TAUX_JOUR    = int(stj)
#     cfg.SEUIL_VOLUME_JOUR  = int(svj)
#     cfg.SEUIL_PIC_CRITIQUE = int(sp)

#     try:
#         db_manager.db['config_seuils'].replace_one(
#             {"_id": "seuils_alerte"},
#             {"_id": "seuils_alerte",
#              "SEUIL_NEGATIF":      int(sn),
#              "SEUIL_TAUX_JOUR":    int(stj),
#              "SEUIL_VOLUME_JOUR":  int(svj),
#              "SEUIL_PIC_CRITIQUE": int(sp),
#              "updated_by": (session_data or {}).get('user', {}).get('email', '?')},
#             upsert=True
#         )
#         db_ok = True
#     except Exception:
#         db_ok = False

#     feedback = html.Div([
#         html.I(className="fas fa-check-circle",
#                style={"marginRight": "8px", "color": "#009A44"}),
#         "Seuils mis à jour avec succès !",
#         html.Span(" (MongoDB ✓)" if db_ok else " (mémoire — MongoDB KO)",
#                   style={"fontSize": "11px", "marginLeft": "8px",
#                          "color": "var(--text-secondary)"})
#     ], style={
#         "color": "#155724", "padding": "12px 16px", "borderRadius": "8px",
#         "fontSize": "13px", "fontWeight": "600",
#         "background": "rgba(0,154,68,0.1)", "display": "flex", "alignItems": "center"
#     })
#     return feedback, _build_recap(int(sn), int(stj), int(svj), int(sp))


# # ── Création de compte ────────────────────────────────────────

# @callback(
#     Output('create-admin-feedback', 'children'),
#     Output('admin-users-list',      'children', allow_duplicate=True),
#     Output('users-count-bar',       'children', allow_duplicate=True),
#     Output('new-admin-firstname',   'value'),
#     Output('new-admin-lastname',    'value'),
#     Output('new-admin-email',       'value'),
#     Output('new-admin-password',    'value'),
#     Output('new-admin-phone',       'value'),
#     Output('new-admin-wilaya',      'value'),
#     Input('btn-create-admin', 'n_clicks'),
#     State('new-admin-firstname', 'value'),
#     State('new-admin-lastname',  'value'),
#     State('new-admin-email',     'value'),
#     State('new-admin-password',  'value'),
#     State('new-admin-phone',     'value'),
#     State('new-admin-wilaya',    'value'),
#     State('selected-new-role',   'data'),
#     State('user-session',        'data'),
#     prevent_initial_call=True
# )
# def create_account(n_clicks, firstname, lastname, email,
#                    password, phone, wilaya, new_role, session_data):
#     if not n_clicks:
#         raise PreventUpdate

#     vide = ("", "", "", "", "", "")
#     role = (session_data or {}).get('user', {}).get('role', 'user')

#     if role != 'super_admin':
#         return (html.Div("⛔ Réservé aux Super Administrateurs.",
#                          style={"color": "#E2001A", "padding": "12px",
#                                 "borderRadius": "8px",
#                                 "background": "rgba(226,0,26,0.08)",
#                                 "fontSize": "13px"}),
#                 no_update, no_update, *vide)

#     errors = []
#     if not firstname or len(firstname.strip()) < 2: errors.append("Prénom requis (min. 2 car.)")
#     if not lastname  or len(lastname.strip())  < 2: errors.append("Nom requis (min. 2 car.)")
#     if not email     or "@" not in email:            errors.append("Email invalide")
#     if not password  or len(password) < 8:           errors.append("Mot de passe min. 8 car.")

#     if errors:
#         return (html.Div([
#             html.Div("⚠️ Erreurs :", style={"fontWeight": "700", "marginBottom": "6px"}),
#             *[html.Div(f"• {e}", style={"fontSize": "12px"}) for e in errors]
#         ], style={"color": "#856404", "padding": "12px", "borderRadius": "8px",
#                   "background": "rgba(255,193,7,0.12)", "fontSize": "13px"}),
#                 no_update, no_update, *vide)

#     try:
#         from werkzeug.security import generate_password_hash
#         from datetime import datetime

#         target_collection = (
#             db_manager.collection
#             if new_role == 'user'
#             else db_manager.db['dashbo_admin']
#         )

#         if target_collection.find_one({"email": email.strip().lower()}):
#             return (html.Div(f"❌ L'email {email} est déjà utilisé.",
#                              style={"color": "#E2001A", "padding": "12px",
#                                     "borderRadius": "8px",
#                                     "background": "rgba(226,0,26,0.08)",
#                                     "fontSize": "13px"}),
#                     no_update, no_update, *vide)

#         creator           = (session_data or {}).get('user', {})
#         creator_firstname = creator.get('firstname', '')
#         creator_lastname  = creator.get('lastname',  '')
#         creator_role      = creator.get('role',      'user')
#         creator_email     = creator.get('email',     '?')

#         creator_fullname = f"{creator_firstname} {creator_lastname}".strip() or creator_email
#         role_label = {'super_admin': 'Super Admin', 'admin': 'Admin',
#                       'user': 'User'}.get(creator_role, '')
#         creator_display = f"{creator_fullname} ({role_label})" if role_label else creator_fullname

#         target_collection.insert_one({
#             "firstname":      firstname.strip(),
#             "lastname":       lastname.strip(),
#             "email":          email.strip().lower(),
#             "password":       generate_password_hash(password, method='pbkdf2:sha256'),
#             "phone":          (phone    or "").strip(),
#             "wilaya":         (wilaya   or "Alger").strip(),
#             "role":           new_role  or "admin",
#             "is_active":      True,
#             "created_at":     datetime.utcnow(),
#             "email_verified": True,
#             "created_by":     creator_display,
#         })

#         role_labels = {"admin": "Administrateur", "super_admin": "Super Admin",
#                        "user": "Utilisateur"}
#         feedback = html.Div([
#             html.I(className="fas fa-check-circle",
#                    style={"marginRight": "8px", "color": "#009A44"}),
#             f"Compte {role_labels.get(new_role, new_role)} créé pour {email} ✓"
#         ], style={
#             "color": "#155724", "padding": "12px 16px", "borderRadius": "8px",
#             "fontSize": "13px", "fontWeight": "600",
#             "background": "rgba(0,154,68,0.1)",
#             "display": "flex", "alignItems": "center"
#         })
#         return feedback, _build_users_list(is_super=True), _build_count_bar(), *vide

#     except Exception as e:
#         return (html.Div(f"❌ Erreur serveur : {e}",
#                          style={"color": "#E2001A", "padding": "12px",
#                                 "borderRadius": "8px",
#                                 "background": "rgba(226,0,26,0.08)",
#                                 "fontSize": "13px"}),
#                 no_update, no_update, *vide)


# # ══════════════════════════════════════════════════════════════
# # ─── CLIENTSIDE CALLBACK : SON POUR LE MODAL DE CONFIRMATION ──
# # ══════════════════════════════════════════════════════════════

# clientside_callback(
#     """
#     function(style) {
#         if (style && style.display === 'flex') {
#             setTimeout(function() {
#                 var audio = document.getElementById('confirm-delete-sound');
#                 if (audio) {
#                     audio.volume = 0.7;
#                     audio.currentTime = 0;
#                     audio.play().catch(function(e) {
#                         console.warn('Audio bloqué par le navigateur:', e);
#                     });
#                 }
#             }, 50);
#         }
#         return window.dash_clientside.no_update;
#     }
#     """,
#     Output("confirm-delete-sound", "currentTime"),
#     Input("confirm-delete-modal",  "style"),
#     prevent_initial_call=True
# )

"""
Page Administration — réservée aux utilisateurs avec role='admin' ou 'super_admin'.
- Modification des seuils d'alerte
- Liste des utilisateurs avec modal détails + suppression (super_admin uniquement)
- Création de nouveaux comptes administrateurs (super_admin uniquement)
- Modification des informations utilisateurs (super_admin uniquement)
- Modification de l'email (super_admin uniquement)
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, clientside_callback
from dash.exceptions import PreventUpdate
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from config.db_config import db_manager
import config.configuration_seuil as cfg

dash.register_page(__name__, path='/admin', name='Administration')


# ══════════════════════════════════════════════════════════════
# ─── Helpers UI génériques ────────────────────────────────────
# ══════════════════════════════════════════════════════════════

def section_card(title, icon, children, border_color="#003087"):
    return html.Div([
        html.Div([
            html.I(className=f"fas {icon}",
                   style={"color": border_color, "marginRight": "10px"}),
            html.Span(title, style={
                "fontWeight": "700", "fontSize": "15px",
                "fontFamily": "'Cairo', sans-serif"
            })
        ], style={
            "borderBottom": "1px solid var(--border-color)",
            "paddingBottom": "14px", "marginBottom": "20px",
            "display": "flex", "alignItems": "center"
        }),
        *children
    ], style={
        "background": "var(--bg-card)",
        "borderRadius": "14px",
        "padding": "24px",
        "boxShadow": "0 2px 12px rgba(0,0,0,0.06)",
        "borderLeft": f"4px solid {border_color}",
        "marginBottom": "20px"
    })


def seuil_row(label, description, input_id, value,
              unit="%", min_val=0, max_val=100, step=1):
    return html.Div([
        html.Div([
            html.Div(label, style={
                "fontWeight": "600", "fontSize": "14px", "marginBottom": "3px",
                "color": "var(--text-primary)"
            }),
            html.Div(description, style={
                "fontSize": "12px", "color": "var(--text-secondary)"
            })
        ], style={"flex": "1"}),
        html.Div([
            dcc.Input(
                id=input_id, type="number", value=value,
                min=min_val, max=max_val, step=step,
                style={
                    "width": "90px", "padding": "8px 12px",
                    "border": "1.5px solid var(--border-color)",
                    "borderRadius": "8px", "fontSize": "14px",
                    "fontWeight": "700", "textAlign": "center",
                    "background": "var(--bg-secondary)",
                    "color": "var(--text-primary)",
                    "fontFamily": "'Poppins', sans-serif"
                }
            ),
            html.Span(unit, style={
                "marginLeft": "8px", "fontSize": "13px",
                "color": "var(--text-secondary)", "fontWeight": "600"
            })
        ], style={"display": "flex", "alignItems": "center"})
    ], style={
        "display": "flex", "alignItems": "center",
        "justifyContent": "space-between",
        "padding": "14px 0",
        "borderBottom": "1px solid var(--border-color)"
    })


def form_field(label, input_id, placeholder,
               input_type="text", icon="fa-user"):
    return html.Div([
        html.Label(label, style={
            "fontSize": "12px", "fontWeight": "600",
            "color": "var(--text-secondary)", "marginBottom": "6px",
            "display": "block", "textTransform": "uppercase",
            "letterSpacing": "0.5px"
        }),
        html.Div([
            html.I(className=f"fas {icon}", style={
                "position": "absolute", "left": "12px",
                "top": "50%", "transform": "translateY(-50%)",
                "color": "#999", "fontSize": "13px", "pointerEvents": "none"
            }),
            dcc.Input(
                id=input_id, type=input_type, placeholder=placeholder,
                debounce=False,
                style={
                    "width": "100%", "padding": "10px 12px 10px 36px",
                    "border": "1.5px solid var(--border-color)",
                    "borderRadius": "8px", "fontSize": "13px",
                    "background": "var(--bg-secondary)",
                    "color": "var(--text-primary)",
                    "fontFamily": "'Poppins', sans-serif", "outline": "none"
                }
            ),
        ], style={"position": "relative"}),
    ], style={"marginBottom": "14px"})


# ══════════════════════════════════════════════════════════════
# ─── Modal de confirmation de suppression ─────────────────────
# ══════════════════════════════════════════════════════════════

def _make_confirm_modal():
    return html.Div(
        id="confirm-delete-modal",
        style={
            "display": "none",
            "position": "fixed", "inset": "0",
            "zIndex": "10000",
            "background": "rgba(0,0,0,0.65)",
            "backdropFilter": "blur(4px)",
            "alignItems": "center", "justifyContent": "center"
        },
        children=[
            html.Div([
                html.Div(
                    html.I(className="fas fa-triangle-exclamation",
                           style={"fontSize": "36px", "color": "#E2001A"}),
                    style={"textAlign": "center", "marginBottom": "16px"}
                ),
                html.Audio(
                    id="confirm-delete-sound",
                    src="/assets/sound/notice-windows-xp-system-sound.mp3",
                    autoPlay=False,
                    style={"display": "none"}
                ),
                html.H3("Confirmer la suppression",
                        style={
                            "textAlign": "center", "margin": "0 0 10px",
                            "fontFamily": "'Cairo', sans-serif",
                            "fontSize": "17px", "fontWeight": "800",
                            "color": "var(--text-primary)"
                        }),
                html.Div(id="confirm-delete-message",
                         style={
                             "textAlign": "center", "fontSize": "13px",
                             "color": "var(--text-secondary)",
                             "marginBottom": "24px", "lineHeight": "1.6"
                         }),
                html.Div([
                    html.Button([
                        html.I(className="fas fa-trash", style={"marginRight": "7px"}),
                        "Oui, supprimer"
                    ], id="confirm-delete-yes", n_clicks=0,
                       style={
                           "background": "linear-gradient(135deg,#E2001A,#a00013)",
                           "color": "white", "border": "none",
                           "padding": "10px 22px", "borderRadius": "8px",
                           "fontSize": "13px", "fontWeight": "700",
                           "cursor": "pointer", "flex": "1"
                       }),
                    html.Button([
                        html.I(className="fas fa-xmark", style={"marginRight": "7px"}),
                        "Annuler"
                    ], id="confirm-delete-no", n_clicks=0,
                       style={
                           "background": "var(--bg-secondary)",
                           "border": "1px solid var(--border-color)",
                           "color": "var(--text-primary)",
                           "padding": "10px 22px", "borderRadius": "8px",
                           "fontSize": "13px", "fontWeight": "600",
                           "cursor": "pointer", "flex": "1"
                       }),
                ], style={"display": "flex", "gap": "10px"}),
                dcc.Store(id="confirm-delete-target"),
            ], style={
                "background": "var(--bg-card)",
                "borderRadius": "16px",
                "padding": "32px 28px 24px",
                "width": "400px",
                "maxWidth": "92vw",
                "boxShadow": "0 20px 60px rgba(0,0,0,0.35)",
                "position": "relative"
            })
        ]
    )


# ══════════════════════════════════════════════════════════════
# ─── Modal détails utilisateur ────────────────────────────────
# ══════════════════════════════════════════════════════════════

def _make_modal():
    def _field(label, input_id, placeholder, input_type="text"):
        return html.Div([
            html.Label(label, style={
                "fontSize": "11px", "fontWeight": "700",
                "color": "var(--text-secondary)", "marginBottom": "5px",
                "display": "block", "textTransform": "uppercase",
                "letterSpacing": "0.5px"
            }),
            dcc.Input(
                id=input_id, type=input_type, placeholder=placeholder,
                debounce=False,
                style={
                    "width": "100%", "padding": "9px 12px",
                    "border": "1.5px solid var(--border-color)",
                    "borderRadius": "8px", "fontSize": "13px",
                    "background": "var(--bg-secondary)",
                    "color": "var(--text-primary)",
                    "fontFamily": "'Poppins', sans-serif",
                    "boxSizing": "border-box", "outline": "none"
                }
            ),
        ], style={"marginBottom": "12px"})

    return html.Div(
        id="user-detail-modal",
        style={
            "display": "none",
            "position": "fixed", "inset": "0",
            "zIndex": "9999",
            "background": "rgba(0,0,0,0.55)",
            "backdropFilter": "blur(4px)",
            "alignItems": "center", "justifyContent": "center"
        },
        children=[
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-user-circle",
                               style={"fontSize": "18px", "color": "#003087",
                                      "marginRight": "8px"}),
                        html.Span("Détails du compte",
                                  style={"fontWeight": "700", "fontSize": "15px",
                                         "fontFamily": "'Cairo', sans-serif"})
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.Button("✕", id="modal-close-btn", n_clicks=0,
                                style={
                                    "background": "none", "border": "none",
                                    "fontSize": "18px", "cursor": "pointer",
                                    "color": "var(--text-secondary)",
                                    "padding": "4px 8px", "borderRadius": "6px"
                                })
                ], style={
                    "display": "flex", "justifyContent": "space-between",
                    "alignItems": "center",
                    "borderBottom": "1px solid var(--border-color)",
                    "paddingBottom": "14px", "marginBottom": "16px"
                }),

                html.Div(id="modal-body"),

                html.Div(id="modal-edit-form", style={"display": "none"}, children=[
                    html.Div([
                        html.I(className="fas fa-pen-to-square",
                               style={"color": "#003087", "marginRight": "8px"}),
                        html.Span("Modifier les informations",
                                  style={"fontWeight": "700", "fontSize": "13px",
                                         "fontFamily": "'Cairo', sans-serif"})
                    ], style={
                        "borderTop": "2px solid var(--border-color)",
                        "paddingTop": "14px", "marginTop": "16px",
                        "marginBottom": "14px",
                        "display": "flex", "alignItems": "center"
                    }),

                    html.Div([
                        html.Div([
                            _field("Prénom",    "edit-firstname", "Ex: Karim"),
                            _field("Nom",       "edit-lastname",  "Ex: Benali"),
                            _field("Téléphone", "edit-phone",
                                   "+213 XX XX XX XX", input_type="tel"),
                        ], style={"flex": "1", "minWidth": "0"}),

                        html.Div([
                            _field("Wilaya", "edit-wilaya", "Ex: Alger"),

                            html.Div(
                                id="edit-email-wrapper",
                                style={"display": "none"},
                                children=[
                                    html.Label([
                                        "Email ",
                                        html.Span("(Super Admin)", style={
                                            "color": "#E2001A", "fontSize": "10px"
                                        })
                                    ], style={
                                        "fontSize": "11px", "fontWeight": "700",
                                        "color": "var(--text-secondary)",
                                        "marginBottom": "5px", "display": "block",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.5px"
                                    }),
                                    dcc.Input(
                                        id="edit-email", type="email",
                                        placeholder="nouvel.email@algerietelecom.dz",
                                        style={
                                            "width": "100%",
                                            "padding": "9px 12px",
                                            "borderRadius": "8px",
                                            "border": "1.5px solid #E2001A",
                                            "background": "rgba(226,0,26,0.04)",
                                            "color": "var(--text-primary)",
                                            "fontSize": "13px",
                                            "fontFamily": "'Poppins', sans-serif",
                                            "boxSizing": "border-box",
                                            "outline": "none"
                                        }
                                    ),
                                    html.Div([
                                        html.I(className="fas fa-triangle-exclamation",
                                               style={"color": "#E2001A",
                                                      "marginRight": "5px",
                                                      "fontSize": "10px"}),
                                        "Modifier l'email déconnectera l'utilisateur."
                                    ], style={
                                        "fontSize": "11px", "color": "#856404",
                                        "background": "rgba(255,193,7,0.12)",
                                        "borderRadius": "6px",
                                        "padding": "5px 8px",
                                        "marginTop": "6px",
                                        "marginBottom": "12px",
                                        "display": "flex", "alignItems": "center"
                                    }),
                                ]
                            ),

                            html.Div([
                                html.Label("Rôle", style={
                                    "fontSize": "11px", "fontWeight": "700",
                                    "color": "var(--text-secondary)",
                                    "marginBottom": "5px", "display": "block",
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.5px"
                                }),
                                dcc.Dropdown(
                                    id="edit-role",
                                    options=[
                                        {"label": "Utilisateur",    "value": "user"},
                                        {"label": "Administrateur", "value": "admin"},
                                        {"label": "Super Admin",    "value": "super_admin"}
                                    ],
                                    style={"width": "100%", "fontSize": "13px"}
                                )
                            ], style={"marginBottom": "12px"}),

                        ], style={"flex": "1", "minWidth": "0"}),
                    ], style={"display": "flex", "gap": "16px"}),

                    html.Div(id="edit-feedback",
                             style={"fontSize": "12px", "marginTop": "4px"}),
                ]),

                html.Div([
                    html.Div(id="modal-delete-feedback",
                             style={"marginBottom": "10px"}),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-trash",
                                   style={"marginRight": "6px"}),
                            "Supprimer"
                        ], id="modal-delete-btn", n_clicks=0,
                           style={
                               "background": "linear-gradient(135deg,#E2001A,#a00013)",
                               "color": "white", "border": "none",
                               "padding": "9px 16px", "borderRadius": "8px",
                               "fontSize": "13px", "fontWeight": "700",
                               "cursor": "pointer"
                           }),
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-pen",
                                       style={"marginRight": "6px"}),
                                "Modifier"
                            ], id="modal-tab-edit", n_clicks=0,
                               style={
                                   "background": "linear-gradient(135deg,#003087,#005080)",
                                   "color": "white", "border": "none",
                                   "padding": "9px 16px", "borderRadius": "8px",
                                   "fontSize": "13px", "fontWeight": "600",
                                   "cursor": "pointer"
                               }),
                            html.Button([
                                html.I(className="fas fa-floppy-disk",
                                       style={"marginRight": "6px"}),
                                "Enregistrer"
                            ], id="edit-save-btn", n_clicks=0,
                               style={
                                   "background": "linear-gradient(135deg,#009A44,#007a33)",
                                   "color": "white", "border": "none",
                                   "padding": "9px 16px", "borderRadius": "8px",
                                   "fontSize": "13px", "fontWeight": "600",
                                   "cursor": "pointer", "display": "none"
                               }),
                            html.Button([
                                html.I(className="fas fa-xmark",
                                       style={"marginRight": "6px"}),
                                "Fermer"
                            ], id="modal-cancel-btn", n_clicks=0,
                               style={
                                   "background": "var(--bg-secondary)",
                                   "border": "1px solid var(--border-color)",
                                   "color": "var(--text-primary)",
                                   "padding": "9px 16px", "borderRadius": "8px",
                                   "fontSize": "13px", "fontWeight": "600",
                                   "cursor": "pointer"
                               }),
                        ], style={"display": "flex", "gap": "8px"}),
                    ], style={"display": "flex", "justifyContent": "space-between",
                              "alignItems": "center"}),
                ], style={
                    "borderTop": "1px solid var(--border-color)",
                    "paddingTop": "14px", "marginTop": "16px"
                }),

                dcc.Store(id="modal-selected-email"),
                dcc.Store(id="modal-current-tab", data="details"),

            ], style={
                "background": "var(--bg-card)",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "width": "680px",
                "maxWidth": "95vw",
                "maxHeight": "90vh",
                "overflowY": "auto",
                "boxShadow": "0 20px 60px rgba(0,0,0,0.3)",
                "position": "relative"
            })
        ]
    )


# ══════════════════════════════════════════════════════════════
# ─── Mise à jour des informations utilisateur ─────────────────
# ══════════════════════════════════════════════════════════════

def _update_user_info(current_email, firstname, lastname, phone,
                      wilaya, role, new_email=None):
    try:
        update_fields = {
            "firstname": firstname.strip(),
            "lastname":  lastname.strip(),
            "phone":     phone.strip() if phone else "",
            "wilaya":    wilaya.strip() if wilaya else "Alger",
            "role":      role
        }

        if new_email and new_email.strip().lower() != current_email.lower():
            new_email_clean = new_email.strip().lower()
            if "@" not in new_email_clean or "." not in new_email_clean.split("@")[-1]:
                return False, "Format d'email invalide."
            if db_manager.collection.find_one({"email": new_email_clean}):
                return False, f"L'email « {new_email_clean} » est déjà utilisé par un autre compte."
            update_fields["email"] = new_email_clean

        result = db_manager.collection.update_one(
            {"email": current_email},
            {"$set": update_fields}
        )

        if "email" in update_fields:
            return True, None

        return result.modified_count > 0, None

    except Exception as e:
        print(f"Erreur mise à jour: {e}")
        return False, str(e)


# ══════════════════════════════════════════════════════════════
# ─── Liste des utilisateurs ───────────────────────────────────
# ══════════════════════════════════════════════════════════════

def _build_users_list(is_super=False, current_user_email=None):
    try:
        users = list(db_manager.collection.find({}, {"password": 0}))
        if not users:
            return html.P("Aucun utilisateur trouvé.",
                          style={"color": "var(--text-secondary)", "fontSize": "13px"})

        role_order = {'super_admin': 0, 'admin': 1, 'user': 2}
        users.sort(key=lambda u: (
            role_order.get(u.get('role', 'user'), 999),
            u.get('firstname', '')
        ))

        rows = []
        for u in users:
            role  = u.get("role", "user")
            name  = f"{u.get('firstname','')} {u.get('lastname','')}".strip() or "—"
            email = u.get("email", "—")

            if role == "super_admin":
                badge_color, role_label = "#E2001A", "Super Admin"
            elif role == "admin":
                badge_color, role_label = "#003087", "Admin"
            else:
                badge_color, role_label = "#009A44", "User"

            avatar = html.Div(
                (name[0] if name != "—" else "U").upper(),
                style={
                    "width": "38px", "height": "38px", "borderRadius": "50%",
                    "background": f"linear-gradient(135deg,{badge_color},#009A44)",
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "center", "color": "white",
                    "fontWeight": "700", "fontSize": "14px", "flexShrink": "0"
                }
            )

            can_view = is_super or (role != "super_admin")
            can_view = can_view and (email != current_user_email)

            actions = html.Div([
                html.Span(role_label, style={
                    "background": badge_color, "color": "white",
                    "padding": "1px 10px", "borderRadius": "12px",
                    "fontSize": "11px", "fontWeight": "700", "marginRight": "8px"
                }),
                html.Button([
                    html.I(className="fas fa-eye",
                           style={"marginRight": "4px", "fontSize": "11px"}),
                    "Voir"
                ],
                    id={"type": "btn-view-user", "index": email},
                    n_clicks=0,
                    style={
                        "background": "rgba(0,48,135,0.1)",
                        "border": "1px solid rgba(0,48,135,0.3)",
                        "color": "#003087", "padding": "4px 10px",
                        "borderRadius": "6px", "fontSize": "11px",
                        "fontWeight": "600", "cursor": "pointer",
                        "marginRight": "6px",
                        "display": "inline-flex" if can_view else "none"
                    }
                ),
            ], style={"display": "flex", "alignItems": "center"})

            rows.append(html.Div([
                html.Div([
                    avatar,
                    html.Div([
                        html.Div(name, style={
                            "fontWeight": "600", "fontSize": "13px",
                            "color": "var(--text-primary)"
                        }),
                        html.Div(email, style={
                            "fontSize": "11px", "color": "var(--text-secondary)"
                        })
                    ])
                ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
                actions
            ], style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "padding": "10px 0",
                "borderBottom": "1px solid var(--border-color)"
            }))

        return html.Div(rows)

    except Exception as e:
        return html.P(f"Erreur : {e}",
                      style={"color": "#E2001A", "fontSize": "12px"})


# ══════════════════════════════════════════════════════════════
# ─── Section création de compte ───────────────────────────────
# ══════════════════════════════════════════════════════════════

def _build_create_admin_section():
    return html.Div([
        html.Div([
            html.I(className="fas fa-circle-info",
                   style={"color": "#003087", "marginRight": "8px", "flexShrink": "0"}),
            html.Span(
                "Seul un Super Administrateur peut créer des comptes. "
                "Les comptes admin accèdent via /admin/login uniquement.",
                style={"fontSize": "12px", "color": "var(--text-secondary)"}
            )
        ], style={
            "display": "flex", "alignItems": "flex-start",
            "background": "rgba(0,48,135,0.06)", "borderRadius": "8px",
            "padding": "12px 14px", "marginBottom": "20px", "gap": "8px"
        }),

        html.Div([
            html.Div([
                form_field("Prénom", "new-admin-firstname", "Ex: Karim", icon="fa-user"),
                form_field("Email", "new-admin-email", "exemple@algerietelecom.dz",
                           input_type="email", icon="fa-envelope"),
                form_field("Mot de passe", "new-admin-password", "Minimum 8 caractères",
                           input_type="password", icon="fa-lock"),
            ], style={"flex": "1"}),
            html.Div([
                form_field("Nom", "new-admin-lastname", "Ex: Benali", icon="fa-user"),
                form_field("Téléphone", "new-admin-phone", "+213 XX XX XX XX",
                           icon="fa-phone"),
                form_field("Wilaya", "new-admin-wilaya", "Ex: Alger", icon="fa-map-pin"),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "20px"}),

        html.Div([
            html.Label("Niveau d'accès", style={
                "fontSize": "12px", "fontWeight": "600",
                "color": "var(--text-secondary)", "marginBottom": "8px",
                "display": "block", "textTransform": "uppercase",
                "letterSpacing": "0.5px"
            }),
            html.Div([
                html.Div([
                    html.I(className="fas fa-user-shield",
                           style={"fontSize": "18px", "color": "#003087", "marginBottom": "6px"}),
                    html.Div("Administrateur",
                             style={"fontWeight": "700", "fontSize": "13px",
                                    "color": "var(--text-primary)"}),
                    html.Div("Gestion seuils et dashboard",
                             style={"fontSize": "11px", "color": "var(--text-secondary)",
                                    "marginTop": "2px"})
                ], id="role-card-admin", n_clicks=0,
                   style={
                       "flex": "1", "padding": "16px", "borderRadius": "10px",
                       "border": "2px solid #003087",
                       "background": "rgba(0,48,135,0.08)",
                       "cursor": "pointer", "textAlign": "center"
                   }),
                html.Div([
                    html.I(className="fas fa-crown",
                           style={"fontSize": "18px", "color": "#E2001A", "marginBottom": "6px"}),
                    html.Div("Super Admin",
                             style={"fontWeight": "700", "fontSize": "13px",
                                    "color": "var(--text-primary)"}),
                    html.Div("Tous droits + création de comptes",
                             style={"fontSize": "11px", "color": "var(--text-secondary)",
                                    "marginTop": "2px"})
                ], id="role-card-super", n_clicks=0,
                   style={
                       "flex": "1", "padding": "16px", "borderRadius": "10px",
                       "border": "2px solid var(--border-color)",
                       "background": "var(--bg-secondary)",
                       "cursor": "pointer", "textAlign": "center"
                   }),
                html.Div([
                    html.I(className="fas fa-user",
                           style={"fontSize": "18px", "color": "#009A44", "marginBottom": "6px"}),
                    html.Div("Utilisateur",
                             style={"fontWeight": "700", "fontSize": "13px",
                                    "color": "var(--text-primary)"}),
                    html.Div("Accès standard à l'application",
                             style={"fontSize": "11px", "color": "var(--text-secondary)",
                                    "marginTop": "2px"})
                ], id="role-card-user", n_clicks=0,
                   style={
                       "flex": "1", "padding": "16px", "borderRadius": "10px",
                       "border": "2px solid var(--border-color)",
                       "background": "var(--bg-secondary)",
                       "cursor": "pointer", "textAlign": "center"
                   }),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "20px"}),
        ]),

        html.Div(id="create-admin-feedback", style={"marginBottom": "12px"}),

        html.Button([
            html.I(className="fas fa-user-plus", style={"marginRight": "8px"}),
            "Créer le compte"
        ], id="btn-create-admin", className="btn-primary-at",
           style={
               "width": "100%", "padding": "12px", "fontSize": "14px",
               "fontWeight": "700", "borderRadius": "10px", "cursor": "pointer",
               "background": "linear-gradient(135deg, #003087, #005080)"
           }),
    ])


# ══════════════════════════════════════════════════════════════
# ─── make_content ─────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

def make_content(theme, user_data=None):
    cfg.load_seuils_from_db()
    sn  = cfg.SEUIL_NEGATIF
    stj = cfg.SEUIL_TAUX_JOUR
    svj = cfg.SEUIL_VOLUME_JOUR
    sp  = cfg.SEUIL_PIC_CRITIQUE

    role     = user_data.get('role', 'user') if user_data else 'user'
    is_super = role == 'super_admin'

    return [
        _make_modal(),
        _make_confirm_modal(),

        html.Div([
            html.Div([
                html.I(className="fas fa-shield-halved",
                       style={"fontSize": "28px", "color": "#003087"}),
                html.Div([
                    html.H2("Panneau de configuration",
                            style={"margin": "0", "fontFamily": "'Cairo', sans-serif",
                                   "fontSize": "20px", "fontWeight": "800"}),
                ])
            ], style={"display": "flex", "alignItems": "center", "gap": "14px"}),

            html.Div([
                html.I(className="fas fa-crown" if is_super else "fas fa-user-shield",
                       style={"marginRight": "6px", "fontSize": "12px"}),
                html.Span("Super Administrateur" if is_super else "Administrateur")
            ], style={
                "background": (
                    "linear-gradient(135deg,#E2001A,#a00013)"
                    if is_super else
                    "linear-gradient(135deg,#003087,#009A44)"
                ),
                "color": "white", "padding": "6px 14px", "borderRadius": "20px",
                "fontSize": "12px", "fontWeight": "700",
                "display": "flex", "alignItems": "center"
            })
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center",
            "background": "var(--bg-card)", "borderRadius": "14px",
            "padding": "20px 24px", "marginBottom": "20px",
            "boxShadow": "0 2px 12px rgba(0,0,0,0.06)"
        }),

        html.Div(id="admin-feedback", style={"marginBottom": "16px"}),

        html.Div([
            html.Div([
                # ── Seuil alarme globale ──────────────────────────────────────
                section_card("Seuils d'Alerte Globale", "fa-bell", [
                    seuil_row(
                        "Taux négatif global",
                        "Déclenche la bannière rouge sur le tableau de bord",
                        "input-seuil-negatif", sn,
                        unit="%", min_val=10, max_val=99),
                ], border_color="#E2001A"),

                # ── Seuils journaliers ────────────────────────────────────────
                section_card("Seuils Journaliers (24h)", "fa-clock", [
                    seuil_row(
                        "Taux négatif journalier",
                        "Condition 1 — Pourcentage de commentaires négatifs sur les 24h",
                        "input-seuil-taux-jour", stj,
                        unit="%", min_val=5, max_val=99),
                    seuil_row(
                        "Signal pondéré journalier",
                        "Condition 2 — SUM(fréquence) des négatifs · Ex : 10 clients × freq=10 = 100 signaux",
                        "input-seuil-volume-jour", svj,
                        unit="signaux", min_val=1, max_val=9999, step=1),
                ], border_color="#003087"),

                # ── Seuil pic critique ────────────────────────────────────────
                section_card("Seuil de Pic Critique", "fa-triangle-exclamation", [
                    seuil_row(
                        "Seuil pic négatif mensuel",
                        "Taux à partir duquel un pic est comptabilisé dans le mois",
                        "input-seuil-pic", sp,
                        unit="%", min_val=5, max_val=99),
                ], border_color="#009A44"),

                # ── Note explicative sur le signal ────────────────────────────
                html.Div([
                    html.I(className="fas fa-circle-info",
                           style={"color": "#003087", "marginRight": "10px",
                                  "fontSize": "14px", "flexShrink": "0"}),
                    html.Div([
                        html.Div("Différence entre Condition 1 et Condition 2",
                                 style={"fontWeight": "700", "fontSize": "13px",
                                        "marginBottom": "6px", "color": "var(--text-primary)"}),
                        html.Div([
                            html.Span("Condition 1 (Taux %)",
                                      style={"fontWeight": "600", "color": "#003087"}),
                            html.Span(" → mesure la proportion de négatifs dans le total. "
                                      "Ex : 60 négatifs / 100 total = 60%",
                                      style={"fontSize": "12px", "color": "var(--text-secondary)"}),
                        ], style={"marginBottom": "4px"}),
                        html.Div([
                            html.Span("Condition 2 (Signal pondéré)",
                                      style={"fontWeight": "600", "color": "#E2001A"}),
                            html.Span(" → mesure l'intensité réelle via SUM(fréquence). "
                                      "Un client qui répète son message 10 fois = 10 signaux. "
                                      "L'alarme se déclenche uniquement si les deux conditions sont franchies.",
                                      style={"fontSize": "12px", "color": "var(--text-secondary)"}),
                        ]),
                    ])
                ], style={
                    "display": "flex", "alignItems": "flex-start",
                    "background": "rgba(0,48,135,0.05)",
                    "border": "1px solid rgba(0,48,135,0.15)",
                    "borderRadius": "10px", "padding": "14px 16px",
                    "marginBottom": "20px"
                }),

                html.Button([
                    html.I(className="fas fa-floppy-disk", style={"marginRight": "8px"}),
                    "Sauvegarder les seuils"
                ], id="btn-save-seuils", className="btn-primary-at",
                   style={"width": "100%", "padding": "13px", "fontSize": "14px",
                          "fontWeight": "700", "borderRadius": "10px", "cursor": "pointer"}),
            ], style={"flex": "1.2"}),

            html.Div([
                section_card("Valeurs Actives", "fa-sliders", [
                    html.Div(id="recap-seuils-actifs",
                             children=_build_recap(sn, stj, svj, sp))
                ], border_color="#003087"),
                section_card("Gestion des Utilisateurs", "fa-users-gear", [
                    html.Div(id="users-count-bar",  children=_build_count_bar()),
                    html.Div(id="admin-users-list",
                             children=_build_users_list(
                                 is_super=is_super,
                                 current_user_email=user_data.get('email') if user_data else None
                             ))
                ], border_color="#003087"),
            ], style={"flex": "1"}),

        ], style={"display": "flex", "gap": "20px",
                  "alignItems": "flex-start", "marginBottom": "20px"}),

        section_card(
            "Créer un Compte", "fa-user-plus",
            [
                _build_create_admin_section() if is_super else
                html.Div([
                    html.I(className="fas fa-lock",
                           style={"fontSize": "32px", "color": "#bbb", "marginBottom": "12px"}),
                    html.P("Réservé aux Super Administrateurs.",
                           style={"color": "var(--text-secondary)", "fontSize": "13px"}),
                ], style={"textAlign": "center", "padding": "30px"})
            ],
            border_color="#E2001A" if is_super else "#bbb"
        ),
    ]


# ══════════════════════════════════════════════════════════════
# ─── Builders helpers ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

def _build_count_bar():
    try:
        total  = db_manager.collection.count_documents({})
        admins = db_manager.collection.count_documents(
            {"role": {"$in": ["admin", "super_admin"]}}
        )
        users = total - admins
        return html.Div([
            html.Span(f"👥 {total} comptes total",
                      style={"fontSize": "12px", "color": "var(--text-secondary)",
                             "marginRight": "12px"}),
            html.Span(f"🛡️ {admins} admin(s)",
                      style={"fontSize": "12px", "color": "#003087", "marginRight": "12px"}),
            html.Span(f"👤 {users} user(s)",
                      style={"fontSize": "12px", "color": "#009A44"}),
        ], style={"marginBottom": "14px", "display": "flex", "flexWrap": "wrap", "gap": "4px"})
    except:
        return html.Div()


def _recap_item(label, value, unit, color):
    return html.Div([
        html.Div(label, style={
            "fontSize": "12px", "color": "var(--text-secondary)", "marginBottom": "4px"
        }),
        html.Div([
            html.Span(str(value), style={
                "fontSize": "24px", "fontWeight": "800",
                "color": color, "fontFamily": "'Cairo', sans-serif"
            }),
            html.Span(f" {unit}", style={
                "fontSize": "13px", "color": "var(--text-secondary)"
            })
        ])
    ], style={
        "background": "var(--bg-secondary)", "borderRadius": "10px",
        "padding": "14px", "textAlign": "center", "flex": "1"
    })


def _build_recap(sn, stj, svj, sp):
    return html.Div([
        _recap_item("Alarme globale",      sn,  "%",       "#E2001A"),
        _recap_item("Taux 24h",            stj, "%",       "#003087"),
        _recap_item("Signal 24h",          svj, "signaux", "#003087"),
        _recap_item("Pic critique",        sp,  "%",       "#009A44"),
    ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})


def _get_user_by_email(email):
    try:
        return db_manager.collection.find_one({"email": email}, {"password": 0})
    except:
        return None


# ══════════════════════════════════════════════════════════════
# ─── _build_modal_body ────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

def _build_modal_body(user):
    if not user:
        return html.P("Utilisateur introuvable.", style={"color": "#E2001A"})

    role  = user.get("role", "user")
    name  = f"{user.get('firstname','')} {user.get('lastname','')}".strip() or "—"
    email = user.get("email", "—")

    if role == "super_admin":
        badge_color, role_label = "#E2001A", "Super Administrateur"
    elif role == "admin":
        badge_color, role_label = "#003087", "Administrateur"
    else:
        badge_color, role_label = "#009A44", "Utilisateur"

    created_at  = user.get("created_at")
    created_str = created_at.strftime("%d/%m/%Y à %H:%M") if created_at else "—"

    def info_card(icon, label, value):
        return html.Div([
            html.Div([
                html.I(className=f"fas {icon}",
                       style={"fontSize": "11px", "color": "#003087", "marginRight": "5px"}),
                html.Span(label, style={
                    "fontSize": "10px", "fontWeight": "700",
                    "color": "#003087", "textTransform": "uppercase",
                    "letterSpacing": "0.6px"
                })
            ], style={"marginBottom": "5px"}),
            html.Div(value or "—", style={
                "fontSize": "13px", "fontWeight": "600",
                "color": "var(--text-primary)"
            })
        ], style={
            "background": "var(--bg-secondary)", "borderRadius": "10px",
            "padding": "12px 14px", "flex": "1", "minWidth": "130px"
        })

    def status_badge(ok, label_ok, label_ko):
        return html.Span(
            ("✓ " + label_ok) if ok else ("✗ " + label_ko),
            style={
                "background": "rgba(0,154,68,0.12)" if ok else "rgba(226,0,26,0.10)",
                "color": "#009A44" if ok else "#E2001A",
                "padding": "3px 10px", "borderRadius": "12px",
                "fontSize": "12px", "fontWeight": "700"
            }
        )

    return html.Div([
        html.Div([
            html.Div(
                (name[0] if name != "—" else "U").upper(),
                style={
                    "width": "52px", "height": "52px", "borderRadius": "50%",
                    "background": "rgba(255,255,255,0.22)",
                    "border": "2px solid rgba(255,255,255,0.45)",
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "center", "color": "white",
                    "fontWeight": "800", "fontSize": "20px", "flexShrink": "0"
                }
            ),
            html.Div([
                html.Div(name, style={
                    "fontWeight": "800", "fontSize": "16px",
                    "color": "white", "marginBottom": "4px",
                    "fontFamily": "'Cairo', sans-serif"
                }),
                html.Div([
                    html.I(className="fas fa-envelope",
                           style={"fontSize": "11px", "marginRight": "5px", "opacity": "0.8"}),
                    html.Span(email, style={"fontSize": "12px", "opacity": "0.85"})
                ], style={"color": "white", "display": "flex", "alignItems": "center"}),
            ], style={"flex": "1"}),
            html.Span(role_label, style={
                "background": "rgba(255,255,255,0.20)",
                "border": "1px solid rgba(255,255,255,0.4)",
                "color": "white", "padding": "4px 12px",
                "borderRadius": "14px", "fontSize": "11px",
                "fontWeight": "700", "whiteSpace": "nowrap"
            })
        ], style={
            "background": "linear-gradient(135deg, #003087 0%, #0050b3 100%)",
            "borderRadius": "12px", "padding": "18px 20px",
            "display": "flex", "alignItems": "center", "gap": "14px",
            "marginBottom": "14px"
        }),

        html.Div([
            info_card("fa-phone",    "Téléphone", user.get("phone",  "—")),
            info_card("fa-map-pin",  "Wilaya",    user.get("wilaya", "—")),
            info_card("fa-calendar", "Créé le",   created_str),
            info_card("fa-user-pen", "Créé par",  user.get("created_by", "Inscription publique")),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": "10px", "marginBottom": "12px"}),

        html.Div([
            html.Div([
                html.Span("Compte actif",
                          style={"fontSize": "12px", "color": "var(--text-secondary)",
                                 "marginRight": "8px"}),
                status_badge(user.get("is_active"), "Actif", "Inactif"),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                html.Span("Email vérifié",
                          style={"fontSize": "12px", "color": "var(--text-secondary)",
                                 "marginRight": "8px"}),
                status_badge(user.get("email_verified"), "Vérifié", "Non vérifié"),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "display": "flex", "gap": "20px", "flexWrap": "wrap",
            "padding": "12px 14px", "background": "var(--bg-secondary)",
            "borderRadius": "10px"
        }),
    ])


# ══════════════════════════════════════════════════════════════
# ─── Layout ───────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

def layout(**kwargs):
    return html.Div([
        dcc.Store(id='user-session', storage_type='session'),
        dcc.Store(id='selected-new-role', data='admin'),
        dcc.Store(id='modal-selected-email'),
        dcc.Store(id='modal-current-tab', data='details'),
        dcc.Location(id='admin-redirect', refresh=True),
        html.Div(id='admin-page-root')
    ])


# ══════════════════════════════════════════════════════════════
# ─── Callbacks ────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

@callback(
    Output('admin-page-root', 'children'),
    Input('user-session', 'data'),
    Input('admin-redirect', 'pathname')
)
def render_admin_page(session_data, pathname):
    if not session_data or not session_data.get('logged_in'):
        return dcc.Location(href='/admin/login', id='_redir1')

    user = session_data.get('user', {})
    role = user.get('role', 'user')

    if role not in ('admin', 'super_admin'):
        return html.Div([
            html.Div([
                html.I(className="fas fa-ban",
                       style={"fontSize": "48px", "color": "#E2001A", "marginBottom": "16px"}),
                html.H2("Accès Refusé",
                        style={"fontFamily": "'Cairo', sans-serif",
                               "color": "var(--text-primary)"}),
                html.P("Cette page est réservée aux administrateurs.",
                       style={"color": "var(--text-secondary)"}),
                html.A("Retour au tableau de bord", href="/",
                       style={"color": "#003087", "fontWeight": "600",
                              "textDecoration": "none", "fontSize": "14px"})
            ], style={
                "textAlign": "center", "padding": "80px 40px",
                "background": "var(--bg-card)", "borderRadius": "14px",
                "maxWidth": "500px", "margin": "80px auto"
            })
        ])

    return make_page_layout(
        active_page="admin",
        title="Panneau d'Administration",
        subtitle="Configuration des seuils • Gestion des utilisateurs",
        content=make_content('light', user),
        theme='light',
        user_data=user
    )


@callback(
    Output('user-detail-modal',     'style'),
    Output('modal-body',            'children'),
    Output('modal-selected-email',  'data'),
    Output('modal-delete-feedback', 'children'),
    Output('modal-current-tab',     'data'),
    Output('modal-body',            'style',  allow_duplicate=True),
    Output('modal-edit-form',       'style'),
    Output('modal-tab-edit',        'style',  allow_duplicate=True),
    Output('edit-save-btn',         'style',  allow_duplicate=True),
    Input({'type': 'btn-view-user', 'index': dash.ALL}, 'n_clicks'),
    Input('modal-close-btn',  'n_clicks'),
    Input('modal-cancel-btn', 'n_clicks'),
    prevent_initial_call=True
)
def open_close_modal(view_clicks, close1, close2):
    triggered = ctx.triggered_id

    modal_hidden  = {"display": "none",  "position": "fixed", "inset": "0",
                     "zIndex": "9999",   "background": "rgba(0,0,0,0.55)",
                     "backdropFilter": "blur(4px)",
                     "alignItems": "center", "justifyContent": "center"}
    modal_visible = {**modal_hidden, "display": "flex"}

    btn_modifier  = {"background": "linear-gradient(135deg,#003087,#005080)",
                     "color": "white", "border": "none",
                     "padding": "9px 16px", "borderRadius": "8px",
                     "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
                     "display": "inline-flex", "alignItems": "center"}
    btn_save_hidden = {"background": "linear-gradient(135deg,#009A44,#007a33)",
                       "color": "white", "border": "none",
                       "padding": "9px 16px", "borderRadius": "8px",
                       "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
                       "display": "none"}

    if triggered in ('modal-close-btn', 'modal-cancel-btn'):
        return (modal_hidden, no_update, no_update, "", "details",
                {"display": "block"}, {"display": "none"},
                btn_modifier, btn_save_hidden)

    if isinstance(triggered, dict) and triggered.get('type') == 'btn-view-user':
        email = triggered.get('index')
        if not email or not any(v for v in view_clicks if v):
            raise PreventUpdate
        user = _get_user_by_email(email)
        body = _build_modal_body(user)
        return (modal_visible, body, email, "", "details",
                {"display": "block"}, {"display": "none"},
                btn_modifier, btn_save_hidden)

    raise PreventUpdate


@callback(
    Output("modal-tab-edit",     "style", allow_duplicate=True),
    Output("modal-body",         "style", allow_duplicate=True),
    Output("modal-edit-form",    "style", allow_duplicate=True),
    Output("modal-current-tab",  "data",  allow_duplicate=True),
    Output("edit-save-btn",      "style", allow_duplicate=True),
    Input("modal-tab-edit", "n_clicks"),
    State("modal-current-tab", "data"),
    prevent_initial_call=True
)
def switch_tab(n_edit, current_tab):
    btn_modifier_visible = {
        "background": "linear-gradient(135deg,#003087,#005080)",
        "color": "white", "border": "none", "padding": "9px 16px",
        "borderRadius": "8px", "fontSize": "13px", "fontWeight": "600",
        "cursor": "pointer", "display": "inline-flex", "alignItems": "center"
    }
    btn_modifier_hidden  = {**btn_modifier_visible, "display": "none"}
    btn_save_visible     = {
        "background": "linear-gradient(135deg,#009A44,#007a33)",
        "color": "white", "border": "none", "padding": "9px 16px",
        "borderRadius": "8px", "fontSize": "13px", "fontWeight": "600",
        "cursor": "pointer", "display": "inline-flex", "alignItems": "center"
    }
    btn_save_hidden = {**btn_save_visible, "display": "none"}

    if current_tab == "edit":
        return (btn_modifier_visible, {"display": "block"},
                {"display": "none"}, "details", btn_save_hidden)
    else:
        return (btn_modifier_hidden, {"display": "block"},
                {"display": "block"}, "edit", btn_save_visible)


@callback(
    Output("edit-firstname",     "value"),
    Output("edit-lastname",      "value"),
    Output("edit-phone",         "value"),
    Output("edit-wilaya",        "value"),
    Output("edit-role",          "value"),
    Output("edit-email",         "value"),
    Output("edit-email-wrapper", "style"),
    Input("modal-selected-email", "data"),
    State("user-session", "data"),
    prevent_initial_call=True
)
def load_user_for_edit(email, session_data):
    if not email:
        return "", "", "", "", "user", "", {"display": "none", "marginBottom": "12px"}

    visitor_role = (session_data or {}).get('user', {}).get('role', 'user')
    is_super     = visitor_role == 'super_admin'

    email_wrapper_style = (
        {"display": "block", "marginBottom": "12px"}
        if is_super else
        {"display": "none",  "marginBottom": "12px"}
    )

    user = _get_user_by_email(email)
    if user:
        return (
            user.get("firstname", ""),
            user.get("lastname",  ""),
            user.get("phone",     ""),
            user.get("wilaya",    "Alger"),
            user.get("role",      "user"),
            user.get("email",     ""),
            email_wrapper_style
        )
    return "", "", "", "", "user", "", {"display": "none", "marginBottom": "12px"}


@callback(
    Output("edit-feedback",       "children"),
    Output("modal-body",          "children", allow_duplicate=True),
    Output("admin-users-list",    "children", allow_duplicate=True),
    Output("users-count-bar",     "children", allow_duplicate=True),
    Output("modal-current-tab",   "data",     allow_duplicate=True),
    Output("modal-tab-edit",      "style",    allow_duplicate=True),
    Output("modal-body",          "style",    allow_duplicate=True),
    Output("modal-edit-form",     "style",    allow_duplicate=True),
    Output("edit-save-btn",       "style",    allow_duplicate=True),
    Output("modal-selected-email","data",     allow_duplicate=True),
    Input("edit-save-btn", "n_clicks"),
    State("modal-selected-email", "data"),
    State("edit-firstname",       "value"),
    State("edit-lastname",        "value"),
    State("edit-phone",           "value"),
    State("edit-wilaya",          "value"),
    State("edit-role",            "value"),
    State("edit-email",           "value"),
    State("user-session",         "data"),
    prevent_initial_call=True
)
def save_user_edit(n_clicks, current_email, firstname, lastname,
                   phone, wilaya, role, new_email, session_data):
    if not n_clicks or not current_email:
        raise PreventUpdate

    btn_modifier  = {"background": "linear-gradient(135deg,#003087,#005080)",
                     "color": "white", "border": "none",
                     "padding": "9px 16px", "borderRadius": "8px",
                     "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
                     "display": "inline-flex", "alignItems": "center"}
    btn_save_hidden = {"background": "linear-gradient(135deg,#009A44,#007a33)",
                       "color": "white", "border": "none",
                       "padding": "9px 16px", "borderRadius": "8px",
                       "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
                       "display": "none"}

    visitor_role = (session_data or {}).get('user', {}).get('role', 'user')
    is_super     = visitor_role == 'super_admin'

    if visitor_role not in ('admin', 'super_admin'):
        return (html.Div("⛔ Réservé aux administrateurs.",
                         style={"color": "#E2001A"}), *([no_update] * 9))

    if not firstname or len(firstname.strip()) < 2:
        return (html.Div("❌ Prénom requis (min. 2 caractères)",
                         style={"color": "#E2001A"}), *([no_update] * 9))
    if not lastname or len(lastname.strip()) < 2:
        return (html.Div("❌ Nom requis (min. 2 caractères)",
                         style={"color": "#E2001A"}), *([no_update] * 9))

    email_to_set = new_email if is_super else None
    success, err_msg = _update_user_info(
        current_email, firstname, lastname, phone, wilaya, role, email_to_set)

    if not success:
        msg = err_msg or "Erreur lors de l'enregistrement"
        return (html.Div(f"❌ {msg}", style={"color": "#E2001A"}),
                *([no_update] * 9))

    effective_email = (
        new_email.strip().lower()
        if (is_super and new_email and
            new_email.strip().lower() != current_email.lower())
        else current_email
    )

    user = _get_user_by_email(effective_email)
    body = _build_modal_body(user)

    return (
        html.Div("✅ Modifications enregistrées !", style={"color": "#009A44"}),
        body,
        _build_users_list(is_super=is_super),
        _build_count_bar(),
        "details",
        btn_modifier,
        {"display": "block"},
        {"display": "none"},
        btn_save_hidden,
        effective_email,
    )


@callback(
    Output("modal-current-tab",  "data",  allow_duplicate=True),
    Output("modal-tab-edit",     "style", allow_duplicate=True),
    Output("modal-body",         "style", allow_duplicate=True),
    Output("modal-edit-form",    "style", allow_duplicate=True),
    Input("edit-cancel-btn", "n_clicks"),
    prevent_initial_call=True
)
def cancel_edit(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    btn_modifier = {
        "background": "linear-gradient(135deg,#003087,#005080)",
        "color": "white", "border": "none", "padding": "9px 16px",
        "borderRadius": "8px", "fontSize": "13px", "fontWeight": "600",
        "cursor": "pointer", "display": "inline-flex", "alignItems": "center"
    }
    return "details", btn_modifier, {"display": "block"}, {"display": "none"}


@callback(
    Output('confirm-delete-modal',   'style'),
    Output('confirm-delete-message', 'children'),
    Output('confirm-delete-target',  'data'),
    Input('modal-delete-btn',                              'n_clicks'),
    Input({'type': 'btn-delete-user', 'index': dash.ALL}, 'n_clicks'),
    Input('confirm-delete-no',                             'n_clicks'),
    State('modal-selected-email', 'data'),
    prevent_initial_call=True
)
def toggle_confirm_modal(n_modal_btn, list_clicks, n_cancel, modal_email):
    triggered = ctx.triggered_id

    confirm_hidden  = {"display": "none",  "position": "fixed", "inset": "0",
                       "zIndex": "10000",  "background": "rgba(0,0,0,0.65)",
                       "backdropFilter": "blur(4px)",
                       "alignItems": "center", "justifyContent": "center"}
    confirm_visible = {**confirm_hidden, "display": "flex"}

    if triggered == 'confirm-delete-no':
        return confirm_hidden, no_update, no_update

    if triggered == 'modal-delete-btn':
        if not n_modal_btn:
            raise PreventUpdate
        email = modal_email
        if not email:
            raise PreventUpdate
        user = _get_user_by_email(email)
        name = (f"{user.get('firstname','')} {user.get('lastname','')}".strip()
                if user else email)
        msg = html.Span([
            "Vous êtes sur le point de supprimer définitivement le compte de ",
            html.Strong(name or email), f" ({email}).",
            html.Br(), "Cette action est irréversible."
        ])
        return confirm_visible, msg, {"email": email, "source": "modal"}

    if isinstance(triggered, dict) and triggered.get('type') == 'btn-delete-user':
        if not any(v for v in list_clicks if v):
            raise PreventUpdate
        email = triggered.get('index')
        if not email:
            raise PreventUpdate
        user = _get_user_by_email(email)
        name = (f"{user.get('firstname','')} {user.get('lastname','')}".strip()
                if user else email)
        msg = html.Span([
            "Vous êtes sur le point de supprimer définitivement le compte de ",
            html.Strong(name or email), f" ({email}).",
            html.Br(), "Cette action est irréversible."
        ])
        return confirm_visible, msg, {"email": email, "source": "list"}

    raise PreventUpdate


@callback(
    Output('confirm-delete-modal',  'style',    allow_duplicate=True),
    Output('admin-users-list',      'children', allow_duplicate=True),
    Output('users-count-bar',       'children', allow_duplicate=True),
    Output('admin-feedback',        'children', allow_duplicate=True),
    Output('user-detail-modal',     'style',    allow_duplicate=True),
    Output('modal-delete-feedback', 'children', allow_duplicate=True),
    Input('confirm-delete-yes', 'n_clicks'),
    State('confirm-delete-target', 'data'),
    State('user-session',          'data'),
    prevent_initial_call=True
)
def execute_confirmed_delete(n_yes, target, session_data):
    if not n_yes or not target:
        raise PreventUpdate

    confirm_hidden = {"display": "none",  "position": "fixed", "inset": "0",
                      "zIndex": "10000",  "background": "rgba(0,0,0,0.65)",
                      "backdropFilter": "blur(4px)",
                      "alignItems": "center", "justifyContent": "center"}
    modal_hidden   = {"display": "none",  "position": "fixed", "inset": "0",
                      "zIndex": "9999",   "background": "rgba(0,0,0,0.55)",
                      "backdropFilter": "blur(4px)",
                      "alignItems": "center", "justifyContent": "center"}

    email  = target.get("email", "")
    source = target.get("source", "list")

    current_user  = (session_data or {}).get('user', {})
    current_role  = current_user.get('role', 'user')
    current_email = current_user.get('email', '')

    if current_role not in ('admin', 'super_admin'):
        return (confirm_hidden, no_update, no_update,
                html.Div("⛔ Action réservée aux administrateurs.",
                         style={"color": "#E2001A", "fontSize": "13px"}),
                no_update, no_update)

    if email == current_email:
        return (confirm_hidden, no_update, no_update,
                html.Div("⛔ Vous ne pouvez pas supprimer votre propre compte.",
                         style={"color": "#E2001A", "fontSize": "13px"}),
                no_update, no_update)

    target_user = _get_user_by_email(email)
    if target_user and target_user.get('role') == 'super_admin' and current_role != 'super_admin':
        return (confirm_hidden, no_update, no_update,
                html.Div("⛔ Un administrateur ne peut pas supprimer un Super Admin.",
                         style={"color": "#E2001A", "fontSize": "13px"}),
                no_update, no_update)

    try:
        result = db_manager.collection.delete_one({"email": email})
        if result.deleted_count == 0:
            return (confirm_hidden, no_update, no_update,
                    html.Div("❌ Compte introuvable.",
                             style={"color": "#E2001A", "fontSize": "13px"}),
                    no_update, no_update)

        print(f"🗑️ Compte supprimé : {email} par {current_email}")

        feedback = html.Div([
            html.I(className="fas fa-check-circle",
                   style={"marginRight": "8px", "color": "#009A44"}),
            f"Compte {email} supprimé avec succès."
        ], style={
            "color": "#155724", "padding": "12px 16px", "borderRadius": "8px",
            "fontSize": "13px", "fontWeight": "600",
            "background": "rgba(0,154,68,0.1)",
            "display": "flex", "alignItems": "center"
        })

        is_super    = current_role == 'super_admin'
        modal_style = modal_hidden if source == "modal" else no_update
        return (
            confirm_hidden,
            _build_users_list(is_super=is_super),
            _build_count_bar(),
            feedback,
            modal_style,
            ""
        )

    except Exception as e:
        return (confirm_hidden, no_update, no_update,
                html.Div(f"❌ Erreur : {e}",
                         style={"color": "#E2001A", "fontSize": "13px"}),
                no_update, no_update)


@callback(
    Output('selected-new-role', 'data'),
    Output('role-card-admin',   'style'),
    Output('role-card-super',   'style'),
    Output('role-card-user',    'style'),
    Input('role-card-admin', 'n_clicks'),
    Input('role-card-super', 'n_clicks'),
    Input('role-card-user',  'n_clicks'),
    prevent_initial_call=True
)
def select_role(n_admin, n_super, n_user):
    triggered = ctx.triggered_id
    base = {"flex": "1", "padding": "16px", "borderRadius": "10px",
            "cursor": "pointer", "textAlign": "center"}
    active_admin = {**base, "border": "2px solid #003087",
                    "background": "rgba(0,48,135,0.08)"}
    active_super = {**base, "border": "2px solid #E2001A",
                    "background": "rgba(226,0,26,0.08)"}
    active_user  = {**base, "border": "2px solid #009A44",
                    "background": "rgba(0,154,68,0.08)"}
    inactive     = {**base, "border": "2px solid var(--border-color)",
                    "background": "var(--bg-secondary)"}

    if triggered == 'role-card-super':
        return 'super_admin', inactive, active_super, inactive
    if triggered == 'role-card-user':
        return 'user', inactive, inactive, active_user
    return 'admin', active_admin, inactive, inactive


@callback(
    Output('admin-feedback',      'children'),
    Output('recap-seuils-actifs', 'children'),
    Input('btn-save-seuils', 'n_clicks'),
    State('input-seuil-negatif',    'value'),
    State('input-seuil-taux-jour',  'value'),
    State('input-seuil-volume-jour','value'),
    State('input-seuil-pic',        'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def save_seuils(n_clicks, sn, stj, svj, sp, session_data):
    if not n_clicks:
        raise PreventUpdate

    role = (session_data or {}).get('user', {}).get('role', 'user')
    if role not in ('admin', 'super_admin'):
        return html.Div("⛔ Action non autorisée.", style={
            "color": "#E2001A", "padding": "12px", "borderRadius": "8px",
            "background": "rgba(226,0,26,0.08)", "fontSize": "13px"
        }), no_update

    errors = []
    if sn  is None or not (10 <= sn  <= 99):   errors.append("Alarme globale : 10–99%")
    if stj is None or not (5  <= stj <= 99):    errors.append("Taux journalier : 5–99%")
    if svj is None or not (1  <= svj <= 9999):  errors.append("Signal journalier : 1–9999 signaux")
    if sp  is None or not (5  <= sp  <= 99):    errors.append("Pic critique : 5–99%")

    if errors:
        return html.Div([
            html.Div("⚠️ Erreurs :", style={"fontWeight": "700", "marginBottom": "6px"}),
            *[html.Div(f"• {e}", style={"fontSize": "12px"}) for e in errors]
        ], style={"color": "#856404", "padding": "12px", "borderRadius": "8px",
                  "background": "rgba(255,193,7,0.12)", "fontSize": "13px"}), no_update

    cfg.SEUIL_NEGATIF      = int(sn)
    cfg.SEUIL_TAUX_JOUR    = int(stj)
    cfg.SEUIL_VOLUME_JOUR  = int(svj)
    cfg.SEUIL_PIC_CRITIQUE = int(sp)

    try:
        db_manager.db['config_seuils'].replace_one(
            {"_id": "seuils_alerte"},
            {"_id":                "seuils_alerte",
             "SEUIL_NEGATIF":      int(sn),
             "SEUIL_TAUX_JOUR":    int(stj),
             "SEUIL_VOLUME_JOUR":  int(svj),
             "SEUIL_PIC_CRITIQUE": int(sp),
             "updated_by": (session_data or {}).get('user', {}).get('email', '?')},
            upsert=True
        )
        db_ok = True
    except Exception:
        db_ok = False

    feedback = html.Div([
        html.I(className="fas fa-check-circle",
               style={"marginRight": "8px", "color": "#009A44"}),
        "Seuils mis à jour avec succès !",
        html.Span(" (MongoDB ✓)" if db_ok else " (mémoire — MongoDB KO)",
                  style={"fontSize": "11px", "marginLeft": "8px",
                         "color": "var(--text-secondary)"})
    ], style={
        "color": "#155724", "padding": "12px 16px", "borderRadius": "8px",
        "fontSize": "13px", "fontWeight": "600",
        "background": "rgba(0,154,68,0.1)", "display": "flex", "alignItems": "center"
    })
    return feedback, _build_recap(int(sn), int(stj), int(svj), int(sp))


@callback(
    Output('create-admin-feedback', 'children'),
    Output('admin-users-list',      'children', allow_duplicate=True),
    Output('users-count-bar',       'children', allow_duplicate=True),
    Output('new-admin-firstname',   'value'),
    Output('new-admin-lastname',    'value'),
    Output('new-admin-email',       'value'),
    Output('new-admin-password',    'value'),
    Output('new-admin-phone',       'value'),
    Output('new-admin-wilaya',      'value'),
    Input('btn-create-admin', 'n_clicks'),
    State('new-admin-firstname', 'value'),
    State('new-admin-lastname',  'value'),
    State('new-admin-email',     'value'),
    State('new-admin-password',  'value'),
    State('new-admin-phone',     'value'),
    State('new-admin-wilaya',    'value'),
    State('selected-new-role',   'data'),
    State('user-session',        'data'),
    prevent_initial_call=True
)
def create_account(n_clicks, firstname, lastname, email,
                   password, phone, wilaya, new_role, session_data):
    if not n_clicks:
        raise PreventUpdate

    vide = ("", "", "", "", "", "")
    role = (session_data or {}).get('user', {}).get('role', 'user')

    if role != 'super_admin':
        return (html.Div("⛔ Réservé aux Super Administrateurs.",
                         style={"color": "#E2001A", "padding": "12px",
                                "borderRadius": "8px",
                                "background": "rgba(226,0,26,0.08)",
                                "fontSize": "13px"}),
                no_update, no_update, *vide)

    errors = []
    if not firstname or len(firstname.strip()) < 2: errors.append("Prénom requis (min. 2 car.)")
    if not lastname  or len(lastname.strip())  < 2: errors.append("Nom requis (min. 2 car.)")
    if not email     or "@" not in email:            errors.append("Email invalide")
    if not password  or len(password) < 8:           errors.append("Mot de passe min. 8 car.")

    if errors:
        return (html.Div([
            html.Div("⚠️ Erreurs :", style={"fontWeight": "700", "marginBottom": "6px"}),
            *[html.Div(f"• {e}", style={"fontSize": "12px"}) for e in errors]
        ], style={"color": "#856404", "padding": "12px", "borderRadius": "8px",
                  "background": "rgba(255,193,7,0.12)", "fontSize": "13px"}),
                no_update, no_update, *vide)

    try:
        from werkzeug.security import generate_password_hash
        from datetime import datetime

        target_collection = (
            db_manager.collection
            if new_role == 'user'
            else db_manager.db['dashbo_admin']
        )

        if target_collection.find_one({"email": email.strip().lower()}):
            return (html.Div(f"❌ L'email {email} est déjà utilisé.",
                             style={"color": "#E2001A", "padding": "12px",
                                    "borderRadius": "8px",
                                    "background": "rgba(226,0,26,0.08)",
                                    "fontSize": "13px"}),
                    no_update, no_update, *vide)

        creator           = (session_data or {}).get('user', {})
        creator_firstname = creator.get('firstname', '')
        creator_lastname  = creator.get('lastname',  '')
        creator_role      = creator.get('role',      'user')
        creator_email     = creator.get('email',     '?')
        creator_fullname  = f"{creator_firstname} {creator_lastname}".strip() or creator_email
        role_label        = {'super_admin': 'Super Admin', 'admin': 'Admin',
                              'user': 'User'}.get(creator_role, '')
        creator_display   = f"{creator_fullname} ({role_label})" if role_label else creator_fullname

        target_collection.insert_one({
            "firstname":      firstname.strip(),
            "lastname":       lastname.strip(),
            "email":          email.strip().lower(),
            "password":       generate_password_hash(password, method='pbkdf2:sha256'),
            "phone":          (phone  or "").strip(),
            "wilaya":         (wilaya or "Alger").strip(),
            "role":           new_role or "admin",
            "is_active":      True,
            "created_at":     datetime.utcnow(),
            "email_verified": True,
            "created_by":     creator_display,
        })

        role_labels = {"admin": "Administrateur", "super_admin": "Super Admin",
                       "user": "Utilisateur"}
        feedback = html.Div([
            html.I(className="fas fa-check-circle",
                   style={"marginRight": "8px", "color": "#009A44"}),
            f"Compte {role_labels.get(new_role, new_role)} créé pour {email} ✓"
        ], style={
            "color": "#155724", "padding": "12px 16px", "borderRadius": "8px",
            "fontSize": "13px", "fontWeight": "600",
            "background": "rgba(0,154,68,0.1)",
            "display": "flex", "alignItems": "center"
        })
        return feedback, _build_users_list(is_super=True), _build_count_bar(), *vide

    except Exception as e:
        return (html.Div(f"❌ Erreur serveur : {e}",
                         style={"color": "#E2001A", "padding": "12px",
                                "borderRadius": "8px",
                                "background": "rgba(226,0,26,0.08)",
                                "fontSize": "13px"}),
                no_update, no_update, *vide)


# ══════════════════════════════════════════════════════════════
# ─── CLIENTSIDE : SON MODAL CONFIRMATION ──────────────────────
# ══════════════════════════════════════════════════════════════

clientside_callback(
    """
    function(style) {
        if (style && style.display === 'flex') {
            setTimeout(function() {
                var audio = document.getElementById('confirm-delete-sound');
                if (audio) {
                    audio.volume = 0.7;
                    audio.currentTime = 0;
                    audio.play().catch(function(e) {
                        console.warn('Audio bloqué par le navigateur:', e);
                    });
                }
            }, 50);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("confirm-delete-sound", "currentTime"),
    Input("confirm-delete-modal",  "style"),
    prevent_initial_call=True
)
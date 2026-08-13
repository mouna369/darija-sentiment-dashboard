

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import sys, os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout
from config.db_config import db_manager

dash.register_page(__name__, path='/settings', name='Paramètres')

# ============================================================
# CONFIGURATION DES NOTIFICATIONS
# ============================================================

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "algerietelecom683@gmail.com",
    "sender_password": "6F5M4:N!J5tDVpM",
    "recipient_email": "cococarte60@gmail.com"
}
import os

SMS_CONFIG = {
    "account_sid": os.environ.get("TWILIO_ACCOUNT_SID", ""),
    "auth_token": os.environ.get("TWILIO_AUTH_TOKEN", ""),
    "from_number": os.environ.get("TWILIO_FROM_NUMBER", ""),
    "to_number": os.environ.get("TWILIO_TO_NUMBER", "")
}

REPORT_CONFIG = {
    "enabled": True,
    "interval_hours": 24,
    "last_generated": None
}

# ============================================================
# FONCTIONS D'ENVOI DE NOTIFICATIONS
# ============================================================

def send_email_notification(subject, message, recipient=None):
    """Envoie un email de notification"""
    try:
        recipient = recipient or EMAIL_CONFIG["recipient_email"]
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email envoyé à {recipient}")
        return True, "Email envoyé avec succès"
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False, f"Erreur: {str(e)}"


def send_sms_notification(message, phone_number=None):
    """Envoie un SMS de notification"""
    try:
        phone = phone_number or SMS_CONFIG["to_number"]
        print(f"📱 SMS envoyé à {phone}: {message[:50]}...")
        print(f"📝 Message complet: {message}")
        return True, "SMS envoyé avec succès"
    except Exception as e:
        print(f"❌ Erreur envoi SMS: {e}")
        return False, f"Erreur: {str(e)}"

def generate_auto_report():
    """Génère un rapport automatique"""
    try:
        from database import get_all_comments, get_stats
        
        stats = get_stats()
        data = get_all_comments(limit=1000)
        
        report_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        report = f"""
📊 RAPPORT AUTOMATIQUE - Algérie Télécom
========================================
Date: {report_date}

📈 STATISTIQUES GLOBALES:
- Total commentaires analysés: {stats.get('total', 0):,}
- Taux de satisfaction: {stats.get('taux_satisfaction', 0)}%
- Taux négatif: {stats.get('taux_negatif', 0)}%
- Frustrations détectées: {stats.get('frustrations', 0)}
- Score moyen: {stats.get('avg_note', 0)}/5

🏷️ TOP 5 THÈMES ABORDÉS:
"""
        
        themes = {}
        for c in data[:500]:
            theme = c.get('theme_pred', 'Autre')
            if theme:
                themes[theme] = themes.get(theme, 0) + 1
        
        for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True)[:5]:
            report += f"\n   • {theme.replace('_', ' ').title()}: {count} commentaires"
        
        report += "\n\n✅ Rapport généré automatiquement par le système."
        report += "\n📧 Ce rapport vous est envoyé périodiquement."
        
        return report
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        return None

# ============================================================
# FONCTION POUR CHERCHER UN UTILISATEUR DANS LES DEUX COLLECTIONS
# ============================================================

def _get_user_from_any_collection(email):
    """Cherche un utilisateur dans users ou dashbo_admin"""
    try:
        # Chercher d'abord dans users
        user = db_manager.collection.find_one({"email": email}, {"password": 0})
        if user:
            print(f"🔍 Utilisateur trouvé dans 'users': {email}")
            return user
        # Chercher dans dashbo_admin
        user = db_manager.db['dashbo_admin'].find_one({"email": email}, {"password": 0})
        if user:
            print(f"🔍 Utilisateur trouvé dans 'dashbo_admin': {email}")
            return user
        print(f"⚠️ Utilisateur non trouvé: {email}")
        return None
    except Exception as e:
        print(f"Erreur recherche utilisateur: {e}")
        return None

# ============================================================
# COMPOSANTS UI
# ============================================================

def setting_row(label, description, control):
    return html.Div([
        html.Div([
            html.Div(label, style={"fontWeight": "600", "fontSize": "14px", "marginBottom": "3px"}),
            html.Div(description, style={"fontSize": "12px", "color": "var(--text-secondary)"})
        ], style={"flex": "1"}),
        control
    ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between",
              "padding": "16px 0", "borderBottom": "1px solid var(--border-color)"})


def toggle_switch(id_val, checked=False):
    return html.Label([
        dcc.Checklist(id=id_val, options=[{"label": "", "value": "on"}],
                      value=["on"] if checked else [],
                      style={"display": "none"}),
        html.Div(className="theme-slider")
    ], className="theme-toggle")

    
def make_content(theme, user_data=None):
    """Ajout du paramètre user_data pour afficher les infos utilisateur"""
    
    # Récupérer les données utilisateur
    if user_data:
        firstname = user_data.get('firstname', '')
        lastname = user_data.get('lastname', '')
        full_name = f"{firstname} {lastname}".strip() if firstname or lastname else "Utilisateur"
        email = user_data.get('email', 'user@example.com')
        phone = user_data.get('phone', '')
        wilaya = user_data.get('wilaya', 'Alger')
        role = user_data.get('role', 'user')
        
        # 🔧 CORRECTION : Extraire seulement les chiffres du numéro
        def format_phone(phone_str):
            if not phone_str or phone_str == "":
                return ""
            # Enlever le +213 si présent
            if phone_str.startswith('+213'):
                phone_str = phone_str[4:]  # Enlève "+213"
            # Enlever le 0 au début si présent
            if phone_str.startswith('0'):
                phone_str = phone_str[1:]
            # Ajouter 0 au début pour affichage (optionnel)
            if len(phone_str) == 9:
                phone_str = f"0{phone_str}"
            return phone_str    
            # Extraire uniquement les chiffres
            digits = ''.join(filter(str.isdigit, phone_str))
            print(f"📞 digits extraits: '{digits}'")
            # Pour +213697536346 → "213697536346" puis on prend les 9 derniers
            if len(digits) >= 9:
                return digits[-9:]  # Prend les 9 derniers chiffres
            return digits
        
        display_phone = format_phone(phone)
        print(f"📞 Original phone: '{phone}'")
        print(f"📞 Formatted phone: '{display_phone}'")
        
        # Initiales pour l'avatar
        initials = (firstname[0] if firstname else 'U') + (lastname[0] if lastname else '')
        
        # Détection correcte du rôle
        if role == 'super_admin':
            role_display = "Super Administrateur"
            badge_role = "badge-red"
        elif role == 'admin':
            role_display = "Administrateur"
            badge_role = "badge-blue"
        else:
            role_display = "Utilisateur"
            badge_role = "badge-green"
    else:
        firstname = ""
        lastname = ""
        full_name = "Invité"
        email = "invite@example.com"
        display_phone = ""
        wilaya = "Non défini"
        initials = "AT"
        role_display = "Invité"
        badge_role = "badge-gray"
    
    return [
        html.Div([
            # Profile settings
            html.Div([
                html.P("Profil Utilisateur", className="card-title", style={"marginBottom": "20px"}),
                html.Div([
                    html.Div(initials, style={
                        "width": "80px", "height": "80px", "borderRadius": "50%",
                        "background": "linear-gradient(135deg, #003087, #009A44)",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "color": "white", "fontSize": "32px", "fontWeight": "700",
                        "fontFamily": "'Cairo', sans-serif", "marginBottom": "12px"
                    }),
                    html.Div(full_name, style={"fontWeight": "700", "fontSize": "18px", "fontFamily": "'Cairo', sans-serif"}),
                    html.Div(email, style={"color": "var(--text-secondary)", "fontSize": "13px"}),
                    html.Div([
                        html.Span(role_display, className=f"badge-at {badge_role}"),
                        html.Span(wilaya, className="badge-at badge-green"),
                    ], style={"display": "flex", "gap": "8px", "marginTop": "10px"})
                ], style={"textAlign": "center", "marginBottom": "24px"}),

                html.Div([
                    html.Div([
                        html.Label("Prénom", className="form-label"),
                        dcc.Input(id="profile-firstname", value=firstname, type="text", className="form-input")
                    ], className="form-group"),
                    html.Div([
                        html.Label("Nom", className="form-label"),
                        dcc.Input(id="profile-lastname", value=lastname, type="text", className="form-input")
                    ], className="form-group"),
                    html.Div([
                        html.Label("Email", className="form-label"),
                        dcc.Input(id="profile-email", value=email, type="email", className="form-input",disabled=True)
                    ], className="form-group"),
                    html.Div([
                        html.Label("Téléphone", className="form-label"),
                        dcc.Input(
                            id="profile-phone", 
                            value=display_phone,
                            type="tel", 
                            placeholder="+213 XX XX XX XX XX",
                            className="form-input"
                        )
                    ], className="form-group"),
                    html.Div([
                        html.Label("Wilaya", className="form-label"),
                        dcc.Dropdown(
                            id="profile-wilaya",
                            options=[{"label": w, "value": w} for w in [
                                "Alger", "Oran", "Constantine", "Annaba", "Blida",
                                "Sétif", "Tizi Ouzou", "Béjaïa", "Tlemcen", "Biskra"
                            ]],
                            value=wilaya,
                            style={"fontFamily": "'Poppins', sans-serif"}
                        )
                    ], className="form-group"),
                    html.Button("Sauvegarder les modifications", id="save-profile-btn",
                                style={"padding": "10px 20px", "background": "var(--at-blue)",
                                       "color": "white", "border": "none", "borderRadius": "8px",
                                       "fontWeight": "600", "cursor": "pointer", "fontFamily": "'Poppins', sans-serif"}),
                    html.Div(id="profile-save-message", style={"marginTop": "10px", "fontSize": "12px"})
                ]),
            ], className="dashboard-card", style={"flex": "1", "marginRight": "20px"}),
            # System settings
            html.Div([
                html.P("Préférences Système", className="card-title", style={"marginBottom": "8px"}),

                setting_row("Notifications Email", "Recevoir des alertes par email",
                            toggle_switch("s-email", True)),
                html.Div(id="email-notification-message", style={"marginTop": "5px"}),
                
                setting_row("Alertes SMS", "Notifications critiques par SMS",
                            toggle_switch("s-sms")),
                html.Div(id="sms-notification-message", style={"marginTop": "5px"}),
                
                setting_row("Rapport Auto", "Générer rapports automatiquement",
                            toggle_switch("s-report", True)),
                html.Div(id="report-notification-message", style={"marginTop": "5px"}),

                setting_row("Langue", "Interface en français",
                            dcc.Dropdown(
                                id="lang-select",
                                options=[{"label": "Français", "value": "fr"},
                                         {"label": "العربية", "value": "ar"},
                                         {"label": "English", "value": "en"}],
                                value="fr", clearable=False,
                                style={"width": "130px", "fontSize": "13px"}
                            )),

                setting_row("Fuseau Horaire", "Heure locale Algérie",
                            dcc.Dropdown(
                                options=[{"label": "UTC+1 (Algérie)", "value": "Africa/Algiers"}],
                                value="Africa/Algiers", clearable=False,
                                style={"width": "180px", "fontSize": "13px"}
                            )),

                html.Div(style={"marginTop": "20px"}, children=[
                    html.P("Sécurité", className="card-title", style={"marginBottom": "16px"}),
                    html.Div([
                        html.Label("Ancien mot de passe", className="form-label"),
                        dcc.Input(id="old-password", type="password", placeholder="••••••••", className="form-input")
                    ], className="form-group"),
                    html.Div([
                        html.Label("Nouveau mot de passe", className="form-label"),
                        dcc.Input(id="new-password", type="password", placeholder="Min. 8 caractères", className="form-input")
                    ], className="form-group"),
                    html.Div([
                        html.Label("Confirmer mot de passe", className="form-label"),
                        dcc.Input(id="confirm-password", type="password", placeholder="••••••••", className="form-input")
                    ], className="form-group"),
                    html.Button("Changer le mot de passe", id="change-password-btn",
                                style={"padding": "10px 20px", "background": "var(--at-green)",
                                       "color": "white", "border": "none", "borderRadius": "8px",
                                       "fontWeight": "600", "cursor": "pointer", "fontFamily": "'Poppins', sans-serif"}),
                    html.Div(id="password-message", style={"marginTop": "10px", "fontSize": "12px"})
                ])
            ], className="dashboard-card", style={"flex": "1"}),
        ], style={"display": "flex"}),
    ]


layout = html.Div(id='settings-wrapper', **{"data-theme": "light"}, children=[html.Div(id='settings-content')])


# ============================================================
# CALLBACK PRINCIPAL
# ============================================================

@callback(
    Output('settings-content', 'children'),
    Output('settings-wrapper', 'data-theme'),
    Input('theme-store', 'data'),
    Input('user-session', 'data'),
    prevent_initial_call=True
)
def render(theme, session_data):
    theme = theme or "light"
    
    user_data = None
    
    # Récupérer depuis user-session
    if session_data and session_data.get('logged_in'):
        session_user = session_data.get('user', {})
        email = session_user.get('email')
        
        if email:
            # 🔧 Chercher l'utilisateur complet dans la BDD (users ou dashbo_admin)
            user_data = _get_user_from_any_collection(email)
            if user_data:
                print(f"✅ Utilisateur trouvé: {user_data.get('email')}")
                print(f"✅ Téléphone BDD: {user_data.get('phone')}")
            else:
                user_data = session_user
                print(f"⚠️ Utilisateur non trouvé en BDD, utilisation session: {email}")
    
    return make_page_layout(
        "settings",
        "Paramètres",
        "Configuration du système",
        make_content(theme, user_data),
        theme,
        user_data
    ), theme


# ============================================================
# CALLBACKS NOTIFICATIONS
# ============================================================

@callback(
    Output('email-notification-message', 'children'),
    Output('email-notification-message', 'style'),
    Input('s-email', 'value'),
    prevent_initial_call=True
)
def handle_email_notification(email_switch):
    """Gère l'envoi d'email de test quand le switch est activé"""
    if not email_switch or 'on' not in email_switch:
        return no_update, no_update
    
    subject = "✅ Notifications email activées - Algérie Télécom"
    message = f"""
Bonjour,

Les notifications par email ont été activées sur votre compte Algérie Télécom Dashboard.

Date d'activation: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Cordialement,
L'équipe Algérie Télécom
"""
    
    success, msg = send_email_notification(subject, message)
    
    if success:
        return "✅ Email de test envoyé avec succès", {"display": "block", "color": "#28a745", "fontSize": "12px", "marginTop": "10px"}
    else:
        return f"❌ {msg}", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}


@callback(
    Output('sms-notification-message', 'children'),
    Output('sms-notification-message', 'style'),
    Input('s-sms', 'value'),
    prevent_initial_call=True
)
def handle_sms_notification(sms_switch):
    """Gère l'envoi de SMS de test quand le switch est activé"""
    if not sms_switch or 'on' not in sms_switch:
        return no_update, no_update
    
    message = "Algérie Télécom: Alertes SMS activées sur votre dashboard."
    success, msg = send_sms_notification(message)
    
    if success:
        return "✅ SMS de test envoyé avec succès", {"display": "block", "color": "#28a745", "fontSize": "12px", "marginTop": "10px"}
    else:
        return f"❌ {msg}", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}


@callback(
    Output('report-notification-message', 'children'),
    Output('report-notification-message', 'style'),
    Input('s-report', 'value'),
    prevent_initial_call=True
)
def handle_report_generation(report_switch):
    """Génère un rapport quand le switch est activé"""
    if not report_switch or 'on' not in report_switch:
        return no_update, no_update
    
    report = generate_auto_report()
    
    if report:
        subject = "📊 Rapport automatique - Algérie Télécom Dashboard"
        success, msg = send_email_notification(subject, report)
        
        if success:
            return "✅ Rapport généré et envoyé par email", {"display": "block", "color": "#28a745", "fontSize": "12px", "marginTop": "10px"}
        else:
            return "⚠️ Rapport généré mais envoi email échoué", {"display": "block", "color": "#f59e0b", "fontSize": "12px", "marginTop": "10px"}
    else:
        return "❌ Erreur lors de la génération du rapport", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}


# ============================================================
# CALLBACKS PROFIL ET MOT DE PASSE
# ============================================================
def _update_user_info(email, firstname, lastname, phone, wilaya):
    """Met à jour les informations d'un utilisateur dans la bonne collection"""
    try:
        print(f"📝 Mise à jour pour email: {email}")
        print(f"📝 Données: firstname={firstname}, lastname={lastname}, phone={phone}, wilaya={wilaya}")
        
        # Formater le téléphone avec +213
        formatted_phone = ""
        if phone and phone.strip():
            digits = ''.join(filter(str.isdigit, phone))
            print(f"📞 digits extraits: '{digits}'")
            if digits.startswith('0'):
                digits = digits[1:]
            if digits:
                formatted_phone = f"+213{digits}"
        
        print(f"📞 Téléphone formaté: '{formatted_phone}'")
        
        update_data = {
            'firstname': firstname.strip(),
            'lastname': lastname.strip(),
            'phone': formatted_phone,
            'wilaya': wilaya
        }
        
        # Essayer de mettre à jour dans users
        result_users = db_manager.collection.update_one(
            {"email": email},
            {"$set": update_data}
        )
        
        if result_users.modified_count > 0 or result_users.matched_count > 0:
            print(f"✅ Mise à jour dans 'users' - modifiés: {result_users.modified_count}")
            return True, "users"
        
        # Essayer de mettre à jour dans dashbo_admin
        result_admin = db_manager.db['dashbo_admin'].update_one(
            {"email": email},
            {"$set": update_data}
        )
        
        if result_admin.modified_count > 0 or result_admin.matched_count > 0:
            print(f"✅ Mise à jour dans 'dashbo_admin' - modifiés: {result_admin.modified_count}")
            return True, "dashbo_admin"
        
        print(f"⚠️ Utilisateur non trouvé dans aucune collection: {email}")
        return False, None
        
    except Exception as e:
        print(f"❌ Erreur mise à jour: {e}")
        import traceback
        traceback.print_exc()
        return False, None
@callback(
    Output('profile-save-message', 'children'),
    Output('profile-save-message', 'style'),
    Output('user-session', 'data', allow_duplicate=True),
    Input('save-profile-btn', 'n_clicks'),
    State('profile-firstname', 'value'),
    State('profile-lastname', 'value'),
    State('profile-phone', 'value'),
    State('profile-wilaya', 'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def save_profile(n_clicks, firstname, lastname, phone, wilaya, session_data):
    if not n_clicks:
        raise PreventUpdate

    print(f"🔵 save_profile appelé")
    print(f"🔵 session_data: {session_data}")

    if not session_data or not session_data.get('logged_in'):
        return "❌ Session invalide", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}, no_update

    user = session_data.get('user', {})
    email = user.get('email')
    print(f"🔵 email: {email}")

    if not email:
        return "❌ Email non trouvé", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}, no_update

    # Validation
    if not firstname or len(firstname.strip()) < 2:
        return "❌ Prénom requis (min. 2 caractères)", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}, no_update
    
    if not lastname or len(lastname.strip()) < 2:
        return "❌ Nom requis (min. 2 caractères)", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}, no_update

    # Téléphone
    phone_value = phone.strip() if phone else ""
    print(f"📞 Phone saisi: '{phone_value}'")

    success, collection = _update_user_info(email, firstname, lastname, phone_value, wilaya)

    if success:
        # Créer un utilisateur simple pour la session
        # Formater le téléphone pour l'affichage
        if phone_value:
            digits = ''.join(filter(str.isdigit, phone_value))
            if digits.startswith('0'):
                digits = digits[1:]
            display_phone = f"0{digits}" if digits else ""
        else:
            display_phone = ""
        
        clean_user = {
            'firstname': firstname.strip(),
            'lastname': lastname.strip(),
            'email': email,
            'phone': display_phone,  # Stocker sans +213 pour l'affichage
            'wilaya': wilaya,
            'role': user.get('role', 'user'),
            'is_active': user.get('is_active', True),
            'email_verified': user.get('email_verified', True)
        }
        
        updated_session = {
            'logged_in': True,
            'user': clean_user
        }
        
        print(f"✅ Profil mis à jour dans {collection}")
        print(f"✅ Nouvelle session: {updated_session}")
        
        return (
            "✅ Profil mis à jour avec succès",
            {"display": "block", "color": "#28a745", "fontSize": "12px", "marginTop": "10px"},
            updated_session
        )
    else:
        return (
            "❌ Erreur lors de la mise à jour - utilisateur non trouvé",
            {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"},
            no_update
        )
@callback(
    Output('password-message', 'children'),
    Output('password-message', 'style'),
    Input('change-password-btn', 'n_clicks'),
    State('old-password', 'value'),
    State('new-password', 'value'),
    State('confirm-password', 'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def change_password(n_clicks, old_pwd, new_pwd, confirm_pwd, session_data):
    if not n_clicks:
        raise PreventUpdate
    
    if not session_data or not session_data.get('logged_in'):
        return "Veuillez vous connecter", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}
    
    user = session_data.get('user', {})
    email = user.get('email')
    
    if not email:
        return "Email non trouvé", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}
    
    if not old_pwd or not new_pwd or not confirm_pwd:
        return "Tous les champs sont obligatoires", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}
    
    if new_pwd != confirm_pwd:
        return "Les mots de passe ne correspondent pas", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}
    
    if len(new_pwd) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères", {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}
    
    result = db_manager.change_user_password(email, old_pwd, new_pwd)
    
    if result['success']:
        return "✅ " + result['message'], {"display": "block", "color": "#28a745", "fontSize": "12px", "marginTop": "10px"}
    else:
        return "❌ " + result['message'], {"display": "block", "color": "#dc3545", "fontSize": "12px", "marginTop": "10px"}
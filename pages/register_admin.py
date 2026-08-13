# pages/register_admin.py
import dash
from dash import html, dcc, callback, Input, Output, State
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import flask

dash.register_page(__name__, path="/secret-admin-register", title="Admin Registration")

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['telecom_admin']

def layout():
    """Layout de la page d'inscription admin (cachée)"""
    return html.Div([
        html.Div([
            html.H2("Création de compte Administrateur", 
                    style={"textAlign": "center", "color": "#003087"}),
            html.P("Cette page est réservée à l'administration", 
                   style={"textAlign": "center", "color": "#666"}),
            
            html.Div(id="admin-register-output"),
            
            html.Div([
                html.Label("Prénom :"),
                dcc.Input(id="admin-firstname", type="text", 
                         placeholder="Prénom", className="form-input"),
                
                html.Label("Nom :"),
                dcc.Input(id="admin-lastname", type="text", 
                         placeholder="Nom", className="form-input"),
                
                html.Label("Email :"),
                dcc.Input(id="admin-email", type="email", 
                         placeholder="email@algerietelecom.dz", className="form-input"),
                
                html.Label("Mot de passe :"),
                dcc.Input(id="admin-password", type="password", 
                         placeholder="Mot de passe", className="form-input"),
                
                html.Label("Téléphone :"),
                dcc.Input(id="admin-phone", type="tel", 
                         placeholder="+213 XX XX XX XX", className="form-input"),
                
                html.Label("Wilaya :"),
                dcc.Input(id="admin-wilaya", type="text", 
                         placeholder="Wilaya", className="form-input"),
                
                html.Button("Créer le compte Admin", 
                           id="create-admin-btn", 
                           n_clicks=0,
                           style={"backgroundColor": "#009A44", "color": "white",
                                  "border": "none", "padding": "10px", 
                                  "borderRadius": "5px", "cursor": "pointer",
                                  "width": "100%", "marginTop": "20px"})
            ], style={"maxWidth": "400px", "margin": "0 auto", "padding": "20px"})
        ], style={"maxWidth": "500px", "margin": "50px auto", 
                  "backgroundColor": "white", "padding": "30px",
                  "borderRadius": "10px", "boxShadow": "0 0 20px rgba(0,0,0,0.1)"})
    ], style={"minHeight": "100vh", "backgroundColor": "#f5f5f5", "padding": "20px"})


@callback(
    Output("admin-register-output", "children"),
    Input("create-admin-btn", "n_clicks"),
    State("admin-firstname", "value"),
    State("admin-lastname", "value"),
    State("admin-email", "value"),
    State("admin-password", "value"),
    State("admin-phone", "value"),
    State("admin-wilaya", "value"),
    prevent_initial_call=True
)
def create_admin_account(n_clicks, firstname, lastname, email, password, phone, wilaya):
    """Crée un compte administrateur directement"""
    
    # Vérifier que tous les champs sont remplis
    if not all([firstname, lastname, email, password]):
        return html.Div("❌ Veuillez remplir tous les champs obligatoires", 
                       style={"color": "red", "textAlign": "center", "marginBottom": "10px"})
    
    # Vérifier si l'email existe déjà
    existing = db.dashbo_admin.find_one({"email": email})
    if existing:
        return html.Div(f"❌ L'email {email} est déjà utilisé", 
                       style={"color": "red", "textAlign": "center", "marginBottom": "10px"})
    
    # Hasher le mot de passe
    password_hash = generate_password_hash(password)
    
    # Créer l'utilisateur avec rôle ADMIN
    user_data = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "password": password_hash,
        "phone": phone or "",
        "wilaya": wilaya or "",
        "role": "admin",  # ← Directement admin !
        "is_active": True,
        "created_at": datetime.now(),
        "email_verified": True,
        "created_by": "secret_admin_page"
    }
    
    try:
        db.dashbo_admin.insert_one(user_data)
        return html.Div([
            html.Div(f"✅ Compte administrateur créé avec succès !", 
                    style={"color": "green", "textAlign": "center", "marginBottom": "10px"}),
            html.Div(f"Email: {email} | Rôle: admin", 
                    style={"textAlign": "center", "fontSize": "12px", "color": "#666"}),
            html.Br(),
            html.A("Retour à l'accueil", href="/", 
                  style={"display": "block", "textAlign": "center", "color": "#009A44"})
        ])
    except Exception as e:
        return html.Div(f"❌ Erreur: {str(e)}", 
                       style={"color": "red", "textAlign": "center"})
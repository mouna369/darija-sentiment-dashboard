

import dash
from dash import html, dcc, callback, Input, Output, State, clientside_callback, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import os
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Poppins:wght@300;400;500;600;700&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="Algérie Télécom Dashboard"
)

server = app.server

app.layout = html.Div([
    dcc.Store(id='theme-store', data='light', storage_type='local'),
    dcc.Store(id='auth-store', data={'is_authenticated': False, 'user': None}, storage_type='local'),
    dcc.Store(id='user-session', storage_type='session'),
    dcc.Location(id='url', refresh=False),
    dash.page_container
])

# Callback pour le thème
clientside_callback(
    """
    function(val, current) {
        if (!val) return current || 'light';
        return (val && val.includes('dark')) ? 'dark' : 'light';
    }
    """,
    Output('theme-store', 'data'),
    Input('theme-toggle', 'value'),
    State('theme-store', 'data'),
    prevent_initial_call=True
)

# Callback pour mettre à jour auth-store depuis user-session
@callback(
    Output('auth-store', 'data'),
    Input('user-session', 'data'),
    prevent_initial_call=True
)
def update_auth_store(session_data):
    print(f"🔍 update_auth_store - session_data reçu: {session_data}")
    if session_data and session_data.get('logged_in'):
        auth_data = {
            'is_authenticated': True,
            'user': session_data.get('user', {})
        }
        print(f"✅ auth-store mis à jour: {auth_data}")
        return auth_data
    print(f"⚠️ auth-store: utilisateur non connecté")
    return {'is_authenticated': False, 'user': None}


# ── CALLBACK UNIQUE POUR LA REDIRECTION ────────────────────────────────────────
@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('url', 'pathname'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_all_redirects(pathname, session_data):
    """
    Gère toutes les redirections :
    - /login         → page user  (publique)
    - /admin/login   → page admin (publique)
    - /register      → publique
    - tout le reste  → protégé, redirige vers /login si non connecté
    """

    # ── Pages publiques ────────────────────────────────────────────
    public_pages = ['/login', '/admin/login', '/register']

    # ── Pages protégées ───────────────────────────────────────────
    protected_pages = [
        '/', '/dashboard', '/analytics', '/statistique',
        '/comments', '/themes-temporal', '/chatbot',
        '/settings', '/notifications', '/mobile', '/admin',
        '/sources',   # ✅ ajouté
    ]

    print(f"🔍 handle_all_redirects - pathname: {pathname}")
    print(f"🔍 handle_all_redirects - session_data: {session_data}")

    is_authenticated = session_data and session_data.get('logged_in', False)
    user_role = session_data.get('user', {}).get('role', 'user') if session_data else 'user'

    # Cas 1 : page publique → laisser passer
    if pathname in public_pages:
        print(f"🟢 Page publique: {pathname} - accès autorisé")
        return no_update

    # Cas 2 : page racine '/'
    if pathname == '/':
        if not is_authenticated:
            print(f"🔴 Redirection '/' → '/login' (non authentifié)")
            return '/login'
        return no_update

    # Cas 3 : /admin → vérifier que c'est bien un admin
    if pathname == '/admin':
        if not is_authenticated:
            return '/admin/login'
        if user_role not in ('admin', 'super_admin'):
            print(f"🔴 Accès /admin refusé - role: {user_role}")
            return '/'
        return no_update

    # Cas 4 : autres pages protégées
    if pathname in protected_pages or pathname not in public_pages:
        if not is_authenticated:
            print(f"🔴 Page protégée {pathname} → /login")
            return '/login'
        return no_update

    return no_update


# Callback thème
@callback(
    Output('app-wrapper', 'data-theme', allow_duplicate=True),
    Input('theme-store', 'data'),
    prevent_initial_call=True
)
def update_theme(theme):
    return theme


@callback(
    Output('user-session', 'data', allow_duplicate=True),
    Input('auth-store', 'data'),
    prevent_initial_call=True
)
def sync_user_session_from_auth(auth_data):
    if auth_data and auth_data.get('is_authenticated'):
        session_data = {
            'logged_in': True,
            'user': auth_data.get('user', {})
        }
        print(f"🔄 user-session synchronisé depuis auth-store")
        return session_data
    return no_update


@callback(
    Output('auth-store', 'data', allow_duplicate=True),
    Input('user-session', 'data'),
    prevent_initial_call=True
)
def sync_auth_from_user_session(session_data):
    if session_data and session_data.get('logged_in'):
        return {
            'is_authenticated': True,
            'user': session_data.get('user', {})
        }
    return {'is_authenticated': False, 'user': None}


@callback(
    Output('auth-store', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def refresh_auth_on_navigation(pathname, session_data):
    if session_data and session_data.get('logged_in'):
        return {
            'is_authenticated': True,
            'user': session_data.get('user', {})
        }
    return no_update


# Callback déconnexion
@callback(
    Output('user-session', 'data', allow_duplicate=True),
    Output('url', 'pathname', allow_duplicate=True),
    Input('logout-trigger', 'data'),
    prevent_initial_call=True
)
def handle_logout(trigger):
    if trigger == 'logout':
        print("🔴 Déconnexion - effacement de la session")
        return None, '/login'
    return no_update, no_update


if __name__ == '__main__':
    # app.run(debug=True, port=8050)
    app.run(debug=False, port=int(os.environ.get("PORT", 8050)))
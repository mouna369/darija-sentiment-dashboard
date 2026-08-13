import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components import make_page_layout

dash.register_page(__name__, path='/reports', name='Rapports')


def make_treemap(theme):
    bg, text = "rgba(0,0,0,0)", "#1a2332" if theme == "light" else "#e8edf5"
    fig = go.Figure(go.Treemap(
        labels=['Services', 'Fibre Opt.', 'ADSL Pro', 'ADSL Basic', '4G/LTE', 'VSAT', 'Alger', 'Oran',
                'Constantine', 'Annaba', 'Sétif'],
        parents=['', 'Services', 'Services', 'Services', 'Services', 'Services',
                 'Fibre Opt.', 'ADSL Pro', 'ADSL Basic', '4G/LTE', 'VSAT'],
        values=[0, 45200, 32100, 28400, 18600, 8900, 22000, 14000, 10200, 6800, 5600],
        marker=dict(
            colors=['white', '#003087', '#009A44', '#0050b3', '#006b2f', '#003087',
                    '#4a90d9', '#5cba6a', '#6aabf0', '#7ecc8e', '#8cc2f8'],
        ),
        textfont=dict(color=text, family='Poppins')
    ))
    fig.update_layout(
        paper_bgcolor=bg, margin=dict(l=0, r=0, t=10, b=0), height=300
    )
    return fig


def make_funnel(theme):
    bg, text = "rgba(0,0,0,0)", "#1a2332" if theme == "light" else "#e8edf5"
    fig = go.Figure(go.Funnel(
        y=['Prospects', 'Contacts', 'Devis envoyés', 'Négociation', 'Contrats signés'],
        x=[12400, 8900, 5200, 3100, 2140],
        textinfo='value+percent initial',
        marker=dict(color=['#003087', '#1a4d99', '#0050b3', '#006b2f', '#009A44']),
        textfont=dict(color='white', family='Poppins')
    ))
    fig.update_layout(
        paper_bgcolor=bg, plot_bgcolor=bg,
        font=dict(color=text, family='Poppins'),
        margin=dict(l=0, r=0, t=10, b=0), height=300
    )
    return fig


reports_list = [
    {"title": "Rapport Mensuel Avril 2025", "type": "Mensuel", "date": "01/05/2025", "status": "Prêt"},
    {"title": "Analyse Réseau Q1 2025", "type": "Trimestriel", "date": "05/04/2025", "status": "Prêt"},
    {"title": "Rapport Client Satisfaction", "type": "Semestriel", "date": "01/03/2025", "status": "Prêt"},
    {"title": "Audit Technique Infrastructure", "type": "Annuel", "date": "15/01/2025", "status": "Prêt"},
    {"title": "Rapport Revenus Mars 2025", "type": "Mensuel", "date": "01/04/2025", "status": "En cours"},
    {"title": "Bilan Réseau Sécurité", "type": "Spécial", "date": "20/04/2025", "status": "En cours"},
]


def make_content(theme):
    return [
        # KPI Summary
        html.Div([
            html.Div([
                html.Div("15.8M DA", style={"fontSize": "26px", "fontWeight": "700",
                                             "color": "var(--at-blue)", "fontFamily": "'Cairo', sans-serif"}),
                html.Div("Revenus Avril", style={"fontSize": "13px", "color": "var(--text-secondary)"}),
                html.Div([html.Div(style={"width": "82%"}, className="progress-fill blue")],
                         className="progress-bar-at", style={"marginTop": "10px"})
            ], className="stat-card"),
            html.Div([
                html.Div("2 140", style={"fontSize": "26px", "fontWeight": "700",
                                          "color": "var(--at-green)", "fontFamily": "'Cairo', sans-serif"}),
                html.Div("Nouvelles Connexions", style={"fontSize": "13px", "color": "var(--text-secondary)"}),
                html.Div([html.Div(style={"width": "67%"}, className="progress-fill green")],
                         className="progress-bar-at", style={"marginTop": "10px"})
            ], className="stat-card"),
            html.Div([
                html.Div("94.2%", style={"fontSize": "26px", "fontWeight": "700",
                                          "color": "#ff8c00", "fontFamily": "'Cairo', sans-serif"}),
                html.Div("Satisfaction Client", style={"fontSize": "13px", "color": "var(--text-secondary)"}),
                html.Div([html.Div(style={"width": "94%"}, className="progress-fill blue")],
                         className="progress-bar-at", style={"marginTop": "10px"})
            ], className="stat-card"),
            html.Div([
                html.Div("99.8%", style={"fontSize": "26px", "fontWeight": "700",
                                          "color": "#00b4b4", "fontFamily": "'Cairo', sans-serif"}),
                html.Div("Uptime Réseau", style={"fontSize": "13px", "color": "var(--text-secondary)"}),
                html.Div([html.Div(style={"width": "99%"}, className="progress-fill green")],
                         className="progress-bar-at", style={"marginTop": "10px"})
            ], className="stat-card"),
        ], style={"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "20px", "marginBottom": "24px"}),

        # Charts row
        html.Div([
            html.Div([
                html.Div([
                    html.P("Répartition par Service & Région", className="card-title")
                ], className="card-header-row"),
                dcc.Graph(figure=make_treemap(theme), config={"displayModeBar": False})
            ], className="dashboard-card", style={"flex": "1", "marginRight": "20px"}),

            html.Div([
                html.Div([
                    html.P("Entonnoir Commercial", className="card-title")
                ], className="card-header-row"),
                dcc.Graph(figure=make_funnel(theme), config={"displayModeBar": False})
            ], className="dashboard-card", style={"flex": "1"}),
        ], style={"display": "flex", "marginBottom": "24px"}),

        # Reports list
        html.Div([
            html.Div([
                html.P("Rapports Disponibles", className="card-title"),
                html.Button([html.I(className="fas fa-plus", style={"marginRight": "6px"}), "Générer Rapport"],
                            style={
                                "padding": "8px 16px", "background": "var(--at-blue)",
                                "color": "white", "border": "none", "borderRadius": "8px",
                                "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
                                "fontFamily": "'Poppins', sans-serif"
                            }),
            ], className="card-header-row"),

            html.Div([
                html.Div([
                    html.Div([
                        html.Div(html.I(className="fas fa-file-chart-bar"),
                                 style={"width": "44px", "height": "44px", "borderRadius": "10px",
                                        "background": "rgba(0,48,135,0.1)", "color": "var(--at-blue)",
                                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                                        "fontSize": "18px", "marginRight": "14px", "flexShrink": "0"}),
                        html.Div([
                            html.Div(r["title"], style={"fontWeight": "600", "fontSize": "14px", "marginBottom": "3px"}),
                            html.Div(f'{r["type"]} • {r["date"]}',
                                     style={"fontSize": "12px", "color": "var(--text-secondary)"})
                        ], style={"flex": "1"}),
                        html.Span(r["status"], className=f"badge-at badge-{'green' if r['status'] == 'Prêt' else 'orange'}"),
                        html.Button(html.I(className="fas fa-download"),
                                    style={"background": "none", "border": "1px solid var(--border-color)",
                                           "borderRadius": "8px", "padding": "8px 10px", "cursor": "pointer",
                                           "color": "var(--at-green)", "marginLeft": "12px", "fontSize": "14px"}),
                    ], style={"display": "flex", "alignItems": "center", "padding": "14px 0",
                              "borderBottom": "1px solid var(--border-color)"})
                ]) for r in reports_list
            ]),
        ], className="dashboard-card"),
    ]


layout = html.Div(id='reports-wrapper', **{"data-theme": "light"}, children=[html.Div(id='reports-content')])


@callback(
    Output('reports-content', 'children'),
    Output('reports-wrapper', 'data-theme'),
    Input('theme-store', 'data')
)
def render(theme):
    theme = theme or "light"
    return make_page_layout("reports", "Rapports", "Centre d'analyse et rapports", make_content(theme), theme), theme

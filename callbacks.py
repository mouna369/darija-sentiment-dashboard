"""Global callbacks - theme persistence across pages"""
from dash import callback, Input, Output, State, clientside_callback


# Client-side callback to persist theme toggle across pages
clientside_callback(
    """
    function(n, current) {
        if (n === undefined) return current || 'light';
        // This is called by theme toggles in topbar
        return current === 'dark' ? 'light' : 'dark';
    }
    """,
    Output('theme-store', 'data'),
    Input('theme-toggle', 'value'),
    State('theme-store', 'data'),
    prevent_initial_call=True
)

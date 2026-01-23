import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import pandas as pd
import data_loader
import config
from main_v2 import run_backtest_v2
from main_v4_plotly import create_strategy
import datetime
import os
import json

# Initialize the app
app = dash.Dash(__name__)
app.title = "Stock Strategy Analyzer"
server = app.server

# ==========================================
# Cache Logic
# ==========================================
CACHE_FILE = "data/web_input_cache"

def load_input_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_input_cache(symbol):
    if not symbol:
        return
    cache = load_input_cache()
    # Remove if exists to move to top
    if symbol in cache:
        cache.remove(symbol)
    cache.insert(0, symbol)
    # Keep only last 6
    cache = cache[:6]
    
    # Ensure directory exists (just in case)
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    return cache

# ==========================================
# Layout
# ==========================================
app.layout = html.Div([
    html.H1("Stock Strategy Backtest Dashboard", style={'textAlign': 'center'}),

    # Input Section
    html.Div([
        html.Label("Symbol: ", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Input(
            id='input-symbol',
            type='text',
            value=config.SYMBOL,
            placeholder='e.g. 513180',
            debounce=True, # Wait for Enter key
            list='history-list', # Link to datalist
            style={'marginRight': '10px'}
        ),
        html.Datalist(id='history-list', children=[
            html.Option(value=s) for s in load_input_cache()
        ]),
        html.Button('Confirm / Analyze', id='submit-val', n_clicks=0, style={'cursor': 'pointer'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),

    # Top Chart: Strategy Results (The "Result" Chart)
    # This chart updates based on the selection in the bottom chart
    html.Div([
        html.H3("Strategy Performance (Selected Range)", style={'textAlign': 'center'}),
        dcc.Loading(
            id="loading-strategy",
            children=[dcc.Graph(id='strategy-chart')],
            type="circle"
        ),
    ], style={'marginBottom': '30px', 'borderBottom': '1px solid #ddd', 'paddingBottom': '20px'}),

    # Bottom Chart: Full History (The "Selector" Chart)
    html.Div([
        html.H3("Full History & Range Selector", style={'textAlign': 'center'}),
        html.P("Drag the range slider below or zoom in the chart to select a time interval.", style={'textAlign': 'center', 'color': '#666'}),
        dcc.Loading(
            id="loading-history",
            children=[dcc.Graph(id='history-chart')],
            type="circle"
        ),
    ]),
    
    # Hidden store to keep track of the current valid symbol to prevent errors during typing
    dcc.Store(id='current-symbol-store'),
    # Store for debounced relayout data
    dcc.Store(id='debounced-relayout-data'),
    # Store for loaded data (to avoid repeated loading)
    dcc.Store(id='data-store'),
], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif'})


# ==========================================
# Helper Functions
# ==========================================

def generate_strategy_figure(symbol, start_date, end_date, df=None):
    """
    Runs the backtest logic and generates the strategy comparison figure.
    Closely mimics main_v4_plotly.py logic.
    """
    draw_list = config.DRAW_STRATEGY_LIST
    results = {}
    
    print(f"Running strategies for {symbol}: {start_date} to {end_date}")

    # Run Backtests
    for strat_type in draw_list:
        try:
            strategy, strategy_name = create_strategy(strat_type)
            if strategy is None:
                continue
                
            df_result = run_backtest_v2(symbol, str(start_date), str(end_date), strategy, strategy_name, df=df)
            
            if df_result is not None and not df_result.empty:
                results[strategy_name] = df_result
        except Exception as e:
            print(f"Error executing strategy {strat_type}: {e}")

    # Plotting
    fig = go.Figure()
    
    if not results:
        fig.add_annotation(
            text="No results generated. Data might be insufficient for this range.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(template="plotly_white")
        return fig

    for name, df in results.items():
        # Pre-calculate annualized return for hover data
        # Check if df is empty or too short
        if df.empty: continue
            
        first_date = df['date'].iloc[0]
        
        def calc_annualized(row):
            invested = row['total_invested']
            value = row['final_value']
            
            if invested <= 0:
                return 0.0
                
            days_diff = (row['date'] - first_date).days
            years_diff = days_diff / 365.25
            
            if years_diff < 0.01: 
                return 0.0
                
            try:
                if value <= 0: return -100.0
                return ((value / invested) ** (1 / years_diff) - 1) * 100
            except:
                return 0.0

        df_plot = df.copy()
        df_plot['annualized_hover'] = df_plot.apply(calc_annualized, axis=1)

        fig.add_trace(go.Scatter(
            x=df_plot['date'],
            y=df_plot['return_rate'],
            mode='lines',
            name=f"{name} (Final: {df_plot.iloc[-1]['return_rate']:.2f}%)",
            customdata=df_plot[['total_invested', 'annualized_hover', 'final_value']],
            hovertemplate=(
                "<b>Return: %{y:.2f}%</b><br>" +
                "Invested: %{customdata[0]:,.0f}<br>" +
                "Value: %{customdata[2]:,.0f}<br>" +
                "Annualized: %{customdata[1]:.2f}%" +
                "<extra></extra>"
            )
        ))
    
    fig.update_layout(
        title={
            'text': f"Strategy Comparison ({start_date} to {end_date})",
            'x': 0.5, 'xanchor': 'center',
            'y': 0.95, 'yanchor': 'top'
        },
        xaxis_title="Date",
        yaxis_title="Return Rate (%)",
        hovermode="x unified",
        legend=dict(
            itemclick="toggle",
            itemdoubleclick="toggleothers",
            orientation="h", # Horizontal layout
            yanchor="bottom", y=1.02, # Position above the chart
            xanchor="center", x=0.5, # Center alignment
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        template="plotly_white",
        margin=dict(l=40, r=40, t=80, b=40),
        height=500
    )
    return fig


# ==========================================
# Callbacks
# ==========================================

# 0. Clientside Callback for Debouncing Relayout Data (0.3s)
app.clientside_callback(
    """
    function(relayoutData) {
        return new Promise((resolve) => {
            if (window.debounceTimer) {
                clearTimeout(window.debounceTimer);
            }
            window.debounceTimer = setTimeout(() => {
                resolve(relayoutData);
            }, 500);
        });
    }
    """,
    Output('debounced-relayout-data', 'data'),
    Input('history-chart', 'relayoutData')
)

# 1. Update Current Symbol Store, History Chart (Bottom) & History List & Data Store
@app.callback(
    [Output('history-chart', 'figure'),
     Output('current-symbol-store', 'data'),
     Output('history-list', 'children'),
     Output('data-store', 'data')],
    [Input('submit-val', 'n_clicks')],
    [State('input-symbol', 'value')]
)
def update_history(n_clicks, symbol_input):
    # Default to config symbol if input is empty
    symbol = symbol_input if symbol_input else config.SYMBOL
    
    # Update Cache
    new_cache = save_input_cache(symbol)
    datalist_children = [html.Option(value=s) for s in new_cache]

    # Load full history (from 1990 to now/future to ensure we get everything)
    # We force 'qfq' (Forward Adjusted) as per main scripts
    end_date_future = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y%m%d')
    
    stock_name = None
    try:
        # NOTE: data_loader.load_data handles caching and fetching
        # load_data now returns (DataFrame, stock_name) tuple
        result = data_loader.load_data(symbol, start_date='19900101', end_date=end_date_future, adjust='qfq')
        if result is not None:
            df, stock_name = result
        else:
            df = None
    except Exception as e:
        print(f"Error loading data: {e}")
        df = None
    
    display_name = f"{symbol} - {stock_name}" if stock_name else symbol
    print(f"Debug: Stock name for '{symbol}': {stock_name}")

    fig = go.Figure()

    if df is None or df.empty:
        fig.add_annotation(text=f"Could not load data for {symbol}", showarrow=False)
        return fig, symbol, datalist_children, None
    
    # Convert df to dict for storage (JSON serializable)
    df_dict = df.to_dict('records')

    # Create Line Chart
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['close'], 
        mode='lines', 
        name='Close Price',
        line=dict(color='#1f77b4', width=1.5)
    ))

    # Configure Layout with Range Slider
    fig.update_layout(
        title={
            'text': f"Price History: {display_name}",
            'x': 0.5, 'xanchor': 'center'
        },
        xaxis=dict(
            title="Date",
            rangeslider=dict(visible=True), # The key feature for "Drag to determine interval"
            type="date"
        ),
        yaxis=dict(title="Close Price (Adjusted)"),
        template="plotly_white",
        height=400,
        dragmode='zoom', # Allows zooming which also sets the range
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig, symbol, datalist_children, df_dict


# 2. Update Strategy Chart (Top) based on History Selection
@app.callback(
    Output('strategy-chart', 'figure'),
    [Input('debounced-relayout-data', 'data'),
     Input('current-symbol-store', 'data'),
     Input('data-store', 'data')]
)
def update_strategy(relayoutData, symbol, data_store):
    if not symbol:
        return go.Figure()

    # Determine Start/End dates
    # Default: Use config dates or full range of recent history if not in config?
    # Let's default to config.START_DATE / END_DATE if no user selection yet.
    # But if the user *just* loaded the symbol, they haven't selected yet. 
    # The prompt implies: "Operation on bottom chart -> Top chart updates". 
    # Initially, we should probably show the default config range or the full range?
    # Let's stick to config defaults initially, then override with selection.
    
    start_date = config.START_DATE
    end_date = config.END_DATE
    
    ctx = callback_context
    triggered_prop = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    # Parse relayoutData if it exists
    if relayoutData:
        # Case 1: Range Slider or Zoom
        if 'xaxis.range[0]' in relayoutData:
            start_date = relayoutData['xaxis.range[0]']
            end_date = relayoutData['xaxis.range[1]']
        # Case 2: Autosize or Reset (might return 'xaxis.autorange': True)
        elif 'xaxis.autorange' in relayoutData:
            # Revert to defaults or handle nicely
            pass
        # Case 3: Range Slider used (sometimes keys are different in different Plotly versions, but xaxis.range is standard)
        elif 'xaxis.range' in relayoutData:
             r = relayoutData['xaxis.range']
             start_date = r[0]
             end_date = r[1]
             
    # Clean up dates (remove time part if present, Plotly sends 'YYYY-MM-DD HH:MM:SS.ssss')
    def clean_date(d):
        if isinstance(d, str):
            return d.split(' ')[0].split('T')[0]
        return d
        
    start_date = clean_date(start_date)
    end_date = clean_date(end_date)
    
    # Convert data_store back to DataFrame if available
    df = None
    if data_store:
        df = pd.DataFrame(data_store)
        # Convert date column to Timestamp to ensure proper date comparisons in strategies
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
    
    # Ensure dates are within reason (e.g. not before 1990)
    # The backtest engine handles filtering, but we pass strings.
    
    return generate_strategy_figure(symbol, start_date, end_date, df=df)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)

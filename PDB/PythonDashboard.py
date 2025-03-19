import dash  # Add this import at the top
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, timedelta
from dash import Dash, dcc, html, dash_table, Input, Output, State

# Configuration
DATA_DIR = 'trading_data'
NOTES_FILE = 'trading_notes.json'
CONTRACTS_FILE = 'contracts.json'
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize app
app = Dash(__name__)
app.config.suppress_callback_exceptions = True


# Load or initialize contracts
def load_contracts():
    if os.path.exists(CONTRACTS_FILE):
        with open(CONTRACTS_FILE, 'r') as f:
            return json.load(f)
    # Initialize with default contracts
    default_contracts = {
        'ES': {'tick_value': 12.50, 'tick_size': 0.25},
        'GC': {'tick_value': 10.00, 'tick_size': 0.10}
    }
    with open(CONTRACTS_FILE, 'w') as f:
        json.dump(default_contracts, f)
    return default_contracts


# Data processing functions
def process_raw_data(df):
    df['datetime'] = pd.to_datetime(
        (df['date'] + ' ' + df['time']).str.strip(),
        format='%d%b%y %H:%M:%S.%f',
        dayfirst=True
    )
    df = df.sort_values('datetime').reset_index(drop=True)
    return df


def calculate_trades(df):
    contracts = load_contracts()
    trades = []
    open_positions = {}  # Tracks positions by base contract

    for _, row in df.iterrows():
        full_contract = row['contract']
        base_contract = full_contract.split()[0]
        action = row['B/S']
        size = row['Size']
        price = row['Price']
        timestamp = row['datetime']

        # Initialize position tracking for new contracts
        if base_contract not in open_positions:
            open_positions[base_contract] = {
                'position': 0,
                'entry_price': None,
                'entry_time': None,
                'entry_action': None
            }

        # Update position
        prev_position = open_positions[base_contract]['position']
        new_position = prev_position + (size if action == 'B' else -size)

        # Handle position changes
        if prev_position == 0 and new_position != 0:
            # New position opened
            open_positions[base_contract].update({
                'position': new_position,
                'entry_price': price,
                'entry_time': timestamp,
                'entry_action': action
            })
        elif new_position == 0 and prev_position != 0:
            # Position closed
            entry_price = open_positions[base_contract]['entry_price']
            entry_time = open_positions[base_contract]['entry_time']
            entry_action = open_positions[base_contract]['entry_action']

            specs = contracts[base_contract]
            price_diff = (price - entry_price) if entry_action == 'B' else (entry_price - price)
            ticks = price_diff / specs['tick_size']
            pnl = ticks * specs['tick_value'] * abs(prev_position)

            trades.append({
                'contract': full_contract,
                'entry_time': entry_time,
                'exit_time': timestamp,
                'duration': timestamp - entry_time,
                'entry_price': entry_price,
                'exit_price': price,
                'quantity': abs(prev_position),
                'pnl': pnl,
                'direction': 'Long' if entry_action == 'B' else 'Short'
            })

            # Reset position
            open_positions[base_contract] = {
                'position': 0,
                'entry_price': None,
                'entry_time': None,
                'entry_action': None
            }
        else:
            # Update existing position
            open_positions[base_contract]['position'] = new_position

    return pd.DataFrame(trades)


# Dashboard components
def create_dashboard(trades_df, note=''):
    trades_df = trades_df.copy()
    if not trades_df.empty:
        trades_df['duration_seconds'] = trades_df['duration'].dt.total_seconds()
        trades_df['entry_time'] = trades_df['entry_time'].dt.strftime('%I:%M:%S %p')
        trades_df['exit_time'] = trades_df['exit_time'].dt.strftime('%I:%M:%S %p')

    return html.Div([
        dcc.Graph(
            figure=px.bar(
                trades_df,
                x='contract',
                y='pnl',
                color='direction',
                barmode='group',
                title='PnL by Contract and Direction',
                labels={'pnl': 'Profit/Loss ($)'}
            ) if not trades_df.empty else {}
        ),
        dcc.Graph(
            figure=px.scatter(
                trades_df,
                x='exit_time',
                y='pnl',
                color='contract',
                title='Trade Performance Timeline',
                labels={'pnl': 'Profit/Loss ($)', 'exit_time': 'Exit Time'}
            ) if not trades_df.empty else {}
        ),
        html.Div([
            html.H3("Trade Summary", style={'color': '#2c3e50'}),
            html.P(f"Total PnL: ${trades_df['pnl'].sum():.2f}", style={'fontSize': 18}),
            *[html.P(f"{contract} Total: ${trades_df[trades_df['contract'].str.startswith(contract)]['pnl'].sum():.2f}")
              for contract in trades_df['contract'].str.split().str[0].unique()],
            html.P(f"Total Trades: {len(trades_df)}")
        ], style={'margin': '20px', 'padding': '15px', 'borderRadius': '5px', 'backgroundColor': '#f8f9fa'}),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in trades_df.columns] if not trades_df.empty else [],
            data=trades_df.to_dict('records'),
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '8px'},
            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'}
        )
    ])


# App layout
app.layout = html.Div([
    dcc.Store(id='current-date', data='2025-02-05'),
    dcc.Tabs([
        dcc.Tab(label='Daily View', children=[
            html.Div([
                html.Button('Previous Day', id='prev-day', n_clicks=0),
                html.Button('Next Day', id='next-day', n_clicks=0),
                html.Div(id='date-display', style={'display': 'inline-block', 'margin': '0 20px'})
            ]),
            html.Div(id='dashboard-content'),
            html.Div([
                html.H3("Daily Notes"),
                dcc.Textarea(id='notes-input', style={'width': '100%', 'height': 100}),
                html.Button('Save Note', id='save-note', n_clicks=0)
            ])
        ]),
        dcc.Tab(label='Contract Manager', children=[
            html.Div([
                html.H3("Manage Contracts"),
                html.Div([
                    dcc.Input(id='contract-name', placeholder='Contract Name (e.g., ES)',
                              style={'margin': '5px'}),
                    dcc.Input(id='tick-value', type='number', placeholder='Tick Value',
                              style={'margin': '5px'}),
                    dcc.Input(id='tick-size', type='number', placeholder='Tick Size',
                              step=0.01, style={'margin': '5px'}),
                    html.Button('Save Contract', id='save-contract', n_clicks=0,
                                style={'margin': '5px'})
                ]),
                html.Div(id='contract-status', style={'margin': '10px'}),
                html.H4("Saved Contracts"),
                dash_table.DataTable(
                    id='contracts-table',
                    columns=[
                        {'name': 'Contract', 'id': 'name'},
                        {'name': 'Tick Value', 'id': 'tick_value'},
                        {'name': 'Tick Size', 'id': 'tick_size'}
                    ],
                    style_cell={'textAlign': 'center'}
                )
            ], style={'padding': '20px'})
        ])
    ])
])


# Callbacks
# Update the problematic callback
@app.callback(
    [Output('current-date', 'data'),
     Output('date-display', 'children')],
    [Input('prev-day', 'n_clicks'),
     Input('next-day', 'n_clicks')],
    [State('current-date', 'data')]
)
def update_date(prev_clicks, next_clicks, current_date):
    ctx = dash.callback_context  # Now properly referenced
    if not ctx.triggered:
        return current_date, f"Current Date: {current_date}"

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_dt = datetime.strptime(current_date, '%Y-%m-%d')

    if button_id == 'prev-day':
        new_dt = current_dt - timedelta(days=1)
    elif button_id == 'next-day':
        new_dt = current_dt + timedelta(days=1)
    else:
        return current_date, f"Current Date: {current_date}"

    return new_dt.strftime('%Y-%m-%d'), f"Current Date: {new_dt.strftime('%Y-%m-%d')}"


@app.callback(
    [Output('dashboard-content', 'children'),
     Output('notes-input', 'value')],
    [Input('current-date', 'data')]
)
def update_dashboard(date_str):
    file_path = os.path.join(DATA_DIR, f'trades_{date_str}.xlsx')
    try:
        df = pd.read_excel(file_path, sheet_name='tt-export', header=None)
        df.columns = ["date", "time", "exchange", "contract", "B/S", "Size", "Price", "F", "Direct"]
        processed_df = process_raw_data(df)
        trades_df = calculate_trades(processed_df)
        note = load_notes(date_str)
        return create_dashboard(trades_df), note
    except FileNotFoundError:
        return html.H3("No data available for this date"), ''


def load_notes(date_str):
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f).get(date_str, '')
    except FileNotFoundError:
        return ''


# Update the save_notes callback with allow_duplicate=True
@app.callback(
    Output('notes-input', 'value', allow_duplicate=True),
    [Input('save-note', 'n_clicks')],
    [State('notes-input', 'value'),
     State('current-date', 'data')],
    prevent_initial_call=True
)
def save_notes(n_clicks, note, date_str):
    if n_clicks > 0:
        notes = {}
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                notes = json.load(f)
        notes[date_str] = note
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f)
    return note



@app.callback(
    [Output('contract-status', 'children'),
     Output('contracts-table', 'data')],
    [Input('save-contract', 'n_clicks')],
    [State('contract-name', 'value'),
     State('tick-value', 'value'),
     State('tick-size', 'value')]
)
def save_contract(n_clicks, name, tick_value, tick_size):
    contracts = load_contracts()
    message = ""

    if n_clicks > 0 and all([name, tick_value, tick_size]):
        contracts[name] = {
            'tick_value': float(tick_value),
            'tick_size': float(tick_size)
        }
        with open(CONTRACTS_FILE, 'w') as f:
            json.dump(contracts, f)
        message = f"Contract {name} saved successfully!"

    table_data = [{'name': k, 'tick_value': v['tick_value'], 'tick_size': v['tick_size']}
                  for k, v in contracts.items()]

    return message, table_data


if __name__ == '__main__':
    # Initialize contracts file if not exists
    load_contracts()
    app.run_server(debug=True)

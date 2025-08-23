import dash
from dash import Dash, dcc, html, Input, Output, State, dash_table
import pandas as pd
import os
from datetime import datetime, timedelta

from config import DATA_DIR
from contracts.contract_manager import ContractManager
from data.trade_processor import TradeProcessor
from notes.note_manager import NoteManager
from ui.dashboard_components import DashboardComponents

class TradingDashboard:
    def __init__(self):
        self.app = Dash(__name__)
        self.app.config.suppress_callback_exceptions = True
        
        # Initialize managers
        self.contract_manager = ContractManager()
        self.trade_processor = TradeProcessor(self.contract_manager)
        self.note_manager = NoteManager()
        
        # Setup layout and callbacks
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):

        today = datetime.now().strftime('%Y-%m-%d') # Get today's date as string
        self.app.layout = html.Div([
            dcc.Store(id='current-date', data=today),
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
    
    def _setup_callbacks(self):
        @self.app.callback(
            [Output('current-date', 'data'),
             Output('date-display', 'children')],
            [Input('prev-day', 'n_clicks'),
             Input('next-day', 'n_clicks')],
            [State('current-date', 'data')]
        )
        def update_date(prev_clicks, next_clicks, current_date):
            ctx = dash.callback_context
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

        @self.app.callback(
            [Output('dashboard-content', 'children'),
             Output('notes-input', 'value')],
            [Input('current-date', 'data')]
        )



        #This is the rithmic version
        def update_dashboard(date_str):
            file_path = os.path.join(DATA_DIR, f'{date_str}.csv')
            try:
                df = pd.read_csv(file_path,  header=None)
                trades_df = self.trade_processor.calculate_trades_csv_rithmic(df)
                note = self.note_manager.load_notes(date_str)
                return DashboardComponents.create_dashboard(trades_df), note
            except FileNotFoundError:
                return html.H3("No data available for this date"), ''
        '''
        def update_dashboard(date_str):
            file_path = os.path.join(DATA_DIR, f'{date_str}.csv')
            try:
                df = pd.read_excel(file_path,  header=None)
                df.columns = ["date", "time", "exchange", "contract", "B/S", "Size", "Price", "F", "Direct"]
                processed_df = self.trade_processor.process_raw_data(df)
                trades_df = self.trade_processor.calculate_trades(processed_df)
                note = self.note_manager.load_notes(date_str)
                return DashboardComponents.create_dashboard(trades_df), note
            except FileNotFoundError:
                return html.H3("No data available for this date"), ''
                
                
        '''

        @self.app.callback(
            Output('notes-input', 'value', allow_duplicate=True),
            [Input('save-note', 'n_clicks')],
            [State('notes-input', 'value'),
             State('current-date', 'data')],
            prevent_initial_call=True
        )
        def save_notes(n_clicks, note, date_str):
            if n_clicks > 0:
                self.note_manager.save_notes(date_str, note)
            return note

        @self.app.callback(
            [Output('contract-status', 'children'),
             Output('contracts-table', 'data')],
            [Input('save-contract', 'n_clicks')],
            [State('contract-name', 'value'),
             State('tick-value', 'value'),
             State('tick-size', 'value')]
        )
        def save_contract(n_clicks, name, tick_value, tick_size):
            message = ""
            if n_clicks > 0 and all([name, tick_value, tick_size]):
                self.contract_manager.save_contract(name, tick_value, tick_size)
                message = f"Contract {name} saved successfully!"

            contracts = self.contract_manager.load_contracts()
            table_data = [{'name': k, 'tick_value': v['tick_value'], 'tick_size': v['tick_size']}
                          for k, v in contracts.items()]

            return message, table_data
    
    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    dashboard = TradingDashboard()
    dashboard.run() 
import dash
from dash import Dash, dcc, html, Input, Output, State, dash_table, MATCH, ALL
import pandas as pd
import os
from datetime import datetime, timedelta

from config import DATA_DIR
from contracts.contract_manager import ContractManager
from data.trade_processor import TradeProcessor
from notes.note_manager import NoteManager
from notes.trade_note_manager import TradeNoteManager
from ui.dashboard_components import DashboardComponents
try:
    from ui.monthly_summary import MonthlySummaryComponents
    MONTHLY_SUMMARY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Monthly summary dependencies missing: {e}")
    from ui.monthly_fallback import MonthlyFallback
    MONTHLY_SUMMARY_AVAILABLE = False

class TradingDashboard:
    def __init__(self):
        self.app = Dash(__name__)
        self.app.config.suppress_callback_exceptions = True
        
        # Initialize managers
        self.contract_manager = ContractManager()
        self.trade_processor = TradeProcessor(self.contract_manager)
        self.note_manager = NoteManager()
        self.trade_note_manager = TradeNoteManager()
        
        if MONTHLY_SUMMARY_AVAILABLE:
            self.monthly_summary = MonthlySummaryComponents()
        else:
            self.monthly_summary = MonthlyFallback()
        
        # Setup layout and callbacks
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):

        today = datetime.now().strftime('%Y-%m-%d') # Get today's date as string
        self.app.layout = html.Div([
            dcc.Store(id='current-date', data=today),
            dcc.Store(id='current-year', data=datetime.now().year),
            dcc.Store(id='current-month', data=datetime.now().month),
            dcc.Tabs(id='main-tabs', value='daily-tab', style={
                'backgroundColor': 'var(--bg-primary)',
                'borderRadius': 'var(--radius-large)',
                'padding': '8px',
                'border': '1px solid var(--border-color)'
            }, children=[
                dcc.Tab(label='📊 Daily View', value='daily-tab', style={
                    'backgroundColor': 'var(--bg-secondary)',
                    'color': 'var(--text-primary)',
                    'border': '1px solid var(--border-color)'
                }, children=[
                    # Modern navigation header
                    html.Div([
                        html.Button('‹', id='prev-day', n_clicks=0,
                                  style={'fontSize': '24px', 'width': '50px', 'height': '50px'}),
                        html.Div(id='date-display', 
                               style={'display': 'inline-block', 'margin': '0 24px', 
                                     'fontSize': '20px', 'fontWeight': '600',
                                     'color': 'var(--text-primary)'}),
                        html.Button('›', id='next-day', n_clicks=0,
                                  style={'fontSize': '24px', 'width': '50px', 'height': '50px'})
                    ], className='nav-controls'),
                    
                    # Dashboard content 
                    html.Div(id='dashboard-content', className='fade-in'),
                    
                    # Daily notes section (moved back to main layout for callback access)
                    html.Div([
                        html.H3("📝 Daily Reflection", 
                               className='fade-in',
                               style={'marginBottom': '16px', 'color': 'var(--text-primary)'}),
                        html.P("Capture your overall thoughts about today's trading session:",
                              style={'color': 'var(--text-secondary)', 'marginBottom': '12px'}),
                        dcc.Textarea(
                            id='notes-input',
                            placeholder="📊 How did today's trading go? Key insights, lessons learned, market observations...",
                            style={'width': '100%', 'minHeight': '120px', 'marginBottom': '16px'}
                        ),
                        html.Div([
                            html.Button('💾 Save Daily Notes', id='save-daily-note', n_clicks=0, 
                                       className='profit-button',
                                       style={'width': '48%', 'padding': '14px', 'marginRight': '4%'}),
                            html.Button('💾 Save Trade Analysis', id='save-note', n_clicks=0, 
                                       className='profit-button',
                                       style={'width': '48%', 'padding': '14px'})
                        ], style={'display': 'flex', 'width': '100%'})
                    ], className='trading-card fade-in', style={'marginTop': '24px'})
                ]),
                dcc.Tab(label='📅 Monthly Summary', value='monthly-tab', style={
                    'backgroundColor': 'var(--bg-secondary)',
                    'color': 'var(--text-primary)',
                    'border': '1px solid var(--border-color)'
                }, children=[
                    html.Div(id='monthly-content', children=[
                        html.Div("🔄 Loading monthly summary...", 
                               className='loading-spinner')
                    ])
                ]),
                dcc.Tab(label='⚙️ Contract Manager', value='contracts-tab', style={
                    'backgroundColor': 'var(--bg-secondary)',
                    'color': 'var(--text-primary)',
                    'border': '1px solid var(--border-color)'
                }, children=[
                    html.Div([
                        html.H3("⚙️ Contract Configuration", 
                               style={'marginBottom': '24px', 'color': 'var(--text-primary)'}),
                        
                        # Modern contract input form
                        html.Div([
                            html.Div([
                                html.Label("📋 Contract Symbol", 
                                         style={'fontWeight': '600', 'marginBottom': '8px', 
                                               'color': 'var(--text-primary)'}),
                                dcc.Input(
                                    id='contract-name',
                                    placeholder='ES, GC, NQ, etc.',
                                    style={'width': '100%'}
                                )
                            ], className='col-md-4'),
                            
                            html.Div([
                                html.Label("💰 Tick Value ($)", 
                                         style={'fontWeight': '600', 'marginBottom': '8px', 
                                               'color': 'var(--text-primary)'}),
                                dcc.Input(
                                    id='tick-value',
                                    type='number',
                                    placeholder='12.50',
                                    style={'width': '100%'}
                                )
                            ], className='col-md-4'),
                            
                            html.Div([
                                html.Label("📏 Tick Size", 
                                         style={'fontWeight': '600', 'marginBottom': '8px', 
                                               'color': 'var(--text-primary)'}),
                                dcc.Input(
                                    id='tick-size',
                                    type='number',
                                    step=0.01,
                                    placeholder='0.25',
                                    style={'width': '100%'}
                                )
                            ], className='col-md-4')
                        ], className='row', style={'marginBottom': '20px'}),
                        
                        html.Button('💾 Save Contract', id='save-contract', n_clicks=0,
                                  className='profit-button', 
                                  style={'marginBottom': '20px'}),
                        
                        html.Div(id='contract-status', 
                               style={'margin': '16px 0', 'color': 'var(--profit-green)', 
                                     'fontWeight': '600'}),
                        
                        html.H4("📊 Saved Contracts", 
                               style={'marginTop': '32px', 'marginBottom': '16px', 
                                     'color': 'var(--text-primary)'}),
                        dash_table.DataTable(
                            id='contracts-table',
                            columns=[
                                {'name': '📋 Contract', 'id': 'name'},
                                {'name': '💰 Tick Value', 'id': 'tick_value'},
                                {'name': '📏 Tick Size', 'id': 'tick_size'}
                            ],
                            style_cell={
                                'textAlign': 'center',
                                'backgroundColor': 'var(--bg-secondary)',
                                'color': 'var(--text-primary)',
                                'border': 'none',
                                'padding': '12px'
                            },
                            style_header={
                                'backgroundColor': 'var(--bg-tertiary)',
                                'color': 'var(--text-primary)',
                                'fontWeight': '600',
                                'textTransform': 'uppercase',
                                'fontSize': '14px',
                                'letterSpacing': '0.5px'
                            },
                            style_data={
                                'backgroundColor': 'var(--bg-secondary)',
                                'color': 'var(--text-secondary)',
                                'borderBottom': '1px solid var(--bg-tertiary)'
                            }
                        )
                    ], className='trading-card')
                ])
            ])
        ], style={'backgroundColor': 'var(--bg-primary)', 'minHeight': '100vh', 'padding': '20px'})
    
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
            # Try multiple file patterns and formats (same as monthly summary)
            possible_files = [
                f'{date_str}.csv',
                f'trades_{date_str}.csv', 
                f'{date_str}.xls',
                f'trades_{date_str}.xls',
                f'{date_str}.xlsx',
                f'trades_{date_str}.xlsx'
            ]
            
            file_found = None
            for filename in possible_files:
                file_path = os.path.join(DATA_DIR, filename)
                if os.path.exists(file_path):
                    file_found = file_path
                    print(f"DEBUG: Found file for {date_str}: {filename}")
                    break
            
            if not file_found:
                print(f"DEBUG: No trading file found for {date_str}")
                note = self.note_manager.load_notes(date_str)
                return html.Div([
                    html.H3("No trading data available for this date", 
                           style={'textAlign': 'center', 'color': '#7f8c8d', 'margin': '50px'}),
                    html.P(f"Looking for files like: {date_str}.csv, trades_{date_str}.xls, etc.",
                           style={'textAlign': 'center', 'color': '#95a5a6'}),
                    html.P("Available files in your trading_data folder:", 
                           style={'textAlign': 'center', 'color': '#95a5a6', 'marginTop': '20px'}),
                    html.Pre([f for f in os.listdir(DATA_DIR) if f.endswith(('.csv', '.xls', '.xlsx'))][:10],
                            style={'textAlign': 'center', 'color': '#6c757d', 'fontSize': '12px'})
                ], style={'padding': '20px'}), note
            
            try:
                # Determine file type and process accordingly
                if file_found.endswith('.csv'):
                    trades_df = self.trade_processor.calculate_trades_csv_rithmic(file_found)
                else:
                    # For .xls/.xlsx files, use the original Excel processing method
                    print(f"DEBUG: Processing Excel file: {file_found}")
                    df = pd.read_excel(file_found, header=None)
                    df.columns = ["date", "time", "exchange", "contract", "B/S", "Size", "Price", "F", "Direct"]
                    processed_df = self.trade_processor.process_raw_data(df)
                    trades_df = self.trade_processor.calculate_trades(processed_df)

                # Keep your debug code
                print(f"DEBUG: trades_df shape: {trades_df.shape}")
                print(f"DEBUG: trades_df columns: {list(trades_df.columns)}")
                print(f"DEBUG: trades_df empty: {trades_df.empty}")
                if not trades_df.empty:
                    print(f"DEBUG: First few rows:")
                    print(trades_df.head())
                else:
                    print("DEBUG: DataFrame is empty!")

                note = self.note_manager.load_notes(date_str)
                return DashboardComponents.create_dashboard(trades_df, note, date_str), note
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
                return DashboardComponents.create_dashboard(trades_df, note, date_str), note
            except FileNotFoundError:
                return html.H3("No data available for this date"), ''
                
                
        '''

        # Callback to handle saving trade analysis data only
        @self.app.callback(
            Output('save-note', 'n_clicks'),
            [Input('save-note', 'n_clicks')],
            [State('current-date', 'data'),
             State({'type': 'trade-note', 'index': ALL}, 'value'),
             State({'type': 'trade-color', 'index': ALL}, 'value'),
             State({'type': 'trade-id', 'index': ALL}, 'children')],
            prevent_initial_call=True
        )
        def save_trade_analysis(n_clicks, date_str, trade_notes, trade_colors, trade_ids):
            if n_clicks and n_clicks > 0:
                # Save all trade notes and colors
                saved_count = 0
                for i, trade_id in enumerate(trade_ids):
                    if trade_id:
                        # Save trade note
                        if i < len(trade_notes) and trade_notes[i]:
                            self.trade_note_manager.save_trade_note(trade_id, trade_notes[i])
                        
                        # Save trade color
                        if i < len(trade_colors) and trade_colors[i]:
                            self.trade_note_manager.save_trade_color(trade_id, trade_colors[i])
                        
                        saved_count += 1
                
                print(f"✅ Saved {saved_count} trade analyses for {date_str}")
            
            return n_clicks

        # Callback to handle saving daily notes
        @self.app.callback(
            Output('save-daily-note', 'n_clicks'),
            [Input('save-daily-note', 'n_clicks')],
            [State('notes-input', 'value'),
             State('current-date', 'data')],
            prevent_initial_call=True
        )
        def save_daily_notes(n_clicks, daily_note, date_str):
            if n_clicks and n_clicks > 0:
                if daily_note:
                    self.note_manager.save_notes(date_str, daily_note)
                    print(f"✅ Saved daily note for {date_str}")
                else:
                    print("ℹ️ No daily note to save")
            return n_clicks

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
        
        # Dynamic callback for trade card color changes (visual feedback only)
        @self.app.callback(
            Output({'type': 'trade-card', 'index': MATCH}, 'style'),
            [Input({'type': 'trade-color', 'index': MATCH}, 'value')],
            [State({'type': 'trade-card', 'index': MATCH}, 'style')],
            prevent_initial_call=True
        )
        def update_trade_card_color(color_value, current_style):
            """Update trade card background when color selection changes (visual feedback only)."""
            if not color_value:
                return current_style
                
            # Define the same color mapping as in dashboard_components
            color_mapping = {
                'none': {
                    'background': '#2c2c2e',
                    'border': '#48484a'
                },
                'bad': {
                    'background': 'rgba(255, 69, 58, 0.15)',
                    'border': '#ff453a'
                },
                'uncertain': {
                    'background': 'rgba(255, 149, 0, 0.15)',
                    'border': '#ff9500'
                },
                'attention': {
                    'background': 'rgba(255, 204, 2, 0.15)',
                    'border': '#ffcc02'
                },
                'good': {
                    'background': 'rgba(48, 209, 88, 0.15)',
                    'border': '#30d158'
                },
                'fantastic': {
                    'background': 'rgba(48, 209, 88, 0.25)',
                    'border': '#30d158'
                }
            }
            
            quality_colors = color_mapping.get(color_value, color_mapping['none'])
            
            new_style = current_style.copy()
            new_style['background'] = quality_colors['background']
            new_style['border'] = f'2px solid {quality_colors["border"]}'
            
            return new_style

        # Monthly summary callbacks - try alternative trigger approach
        @self.app.callback(
            Output('monthly-content', 'children'),
            [Input('main-tabs', 'value'),
             Input('current-year', 'data'),
             Input('current-month', 'data')]
        )
        def update_monthly_content(active_tab, year, month):
            print(f"DEBUG: update_monthly_content called - active_tab={active_tab}, year={year}, month={month}")
            
            # Only update when monthly tab is active
            if active_tab != 'monthly-tab':
                print(f"DEBUG: Not monthly tab, returning loading message")
                return html.Div("Loading monthly summary...", style={'padding': '20px', 'textAlign': 'center'})
            
            print(f"DEBUG: Monthly tab is active, creating summary...")
            try:
                result = self.monthly_summary.create_monthly_summary(year, month)
                print(f"DEBUG: Monthly summary created successfully (fallback={not MONTHLY_SUMMARY_AVAILABLE})")
                return result
            except Exception as e:
                print(f"ERROR: Failed to create monthly summary: {e}")
                import traceback
                traceback.print_exc()
                return html.Div([
                    html.H3("Error loading monthly summary", style={'color': 'red'}),
                    html.P(f"Error: {str(e)}"),
                    html.P(f"Dependencies available: {MONTHLY_SUMMARY_AVAILABLE}")
                ])

        @self.app.callback(
            [Output('current-year', 'data'),
             Output('current-month', 'data')],
            [Input('prev-month', 'n_clicks'),
             Input('next-month', 'n_clicks'),
             Input('month-selector', 'value'),
             Input('year-selector', 'value')],
            [State('current-year', 'data'),
             State('current-month', 'data')]
        )
        def update_month_year(prev_clicks, next_clicks, month_val, year_val, current_year, current_month):
            ctx = dash.callback_context
            if not ctx.triggered:
                return current_year, current_month

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if trigger_id == 'prev-month':
                if current_month == 1:
                    return current_year - 1, 12
                else:
                    return current_year, current_month - 1
            elif trigger_id == 'next-month':
                if current_month == 12:
                    return current_year + 1, 1
                else:
                    return current_year, current_month + 1
            elif trigger_id == 'month-selector' and month_val:
                return current_year, month_val
            elif trigger_id == 'year-selector' and year_val:
                return year_val, current_month
            
            return current_year, current_month

        # Calendar day click callback to switch to daily view
        @self.app.callback(
            [Output('main-tabs', 'value'),
             Output('current-date', 'data', allow_duplicate=True)],
            [Input({'type': 'calendar-day', 'date': ALL}, 'n_clicks')],
            [State({'type': 'calendar-day', 'date': ALL}, 'id')],
            prevent_initial_call=True
        )
        def calendar_day_clicked(n_clicks_list, id_list):
            ctx = dash.callback_context
            if not ctx.triggered:
                return 'daily-tab', dash.no_update
            
            # Find which calendar day was clicked
            for i, clicks in enumerate(n_clicks_list):
                if clicks and clicks > 0:
                    clicked_date = id_list[i]['date']
                    return 'daily-tab', clicked_date
            
            return dash.no_update, dash.no_update
    
    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    dashboard = TradingDashboard()
    dashboard.run() 
import calendar
import pandas as pd
import os
from datetime import datetime, timedelta
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from data.trade_processor import TradeProcessor
from contracts.contract_manager import ContractManager
from config import DATA_DIR

class MonthlySummaryComponents:
    def __init__(self):
        self.trade_processor = TradeProcessor(ContractManager())
    
    def create_monthly_summary(self, year=None, month=None):
        """Create monthly summary tab with calendar view"""
        print(f"DEBUG: create_monthly_summary called with year={year}, month={month}")
        
        if year is None or month is None:
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            print(f"DEBUG: Using current date - year={year}, month={month}")
        
        # Get month data
        print(f"DEBUG: Getting monthly data for {year}-{month}")
        monthly_data = self._get_monthly_data(year, month)
        print(f"DEBUG: Found {len(monthly_data)} days with data: {list(monthly_data.keys())}")
        
        return html.Div([
            # Month navigation
            self._create_month_navigation(year, month),
            
            # Monthly statistics
            self._create_monthly_stats(monthly_data, year, month),
            
            # Calendar view
            self._create_calendar_view(monthly_data, year, month),
            
            # Monthly charts
            self._create_monthly_charts(monthly_data, year, month)
        ])
    
    def _create_month_navigation(self, year, month):
        """Create month navigation controls"""
        month_names = [calendar.month_name[i] for i in range(1, 13)]
        
        return html.Div([
            html.Div([
                html.Div([
                    html.Button('◀', id='prev-month', n_clicks=0,
                              style={'padding': '8px 12px', 'margin': '0 5px', 'fontSize': '16px'}),
                    html.H3(f"{calendar.month_name[month]} {year}", 
                           id='month-display',
                           style={'display': 'inline-block', 'margin': '0 20px', 'color': '#2c3e50'}),
                    html.Button('▶', id='next-month', n_clicks=0,
                              style={'padding': '8px 12px', 'margin': '0 5px', 'fontSize': '16px'})
                ], style={'textAlign': 'center', 'marginBottom': '20px'}),
                
                html.Div([
                    dcc.Dropdown(
                        id='month-selector',
                        options=[{'label': name, 'value': i+1} for i, name in enumerate(month_names)],
                        value=month,
                        style={'width': '150px', 'display': 'inline-block', 'margin': '0 10px'}
                    ),
                    dcc.Dropdown(
                        id='year-selector',
                        options=[{'label': str(y), 'value': y} for y in range(2020, 2030)],
                        value=year,
                        style={'width': '100px', 'display': 'inline-block', 'margin': '0 10px'}
                    )
                ], style={'textAlign': 'center', 'marginBottom': '20px'})
            ])
        ], id='month-navigation')
    
    def _create_monthly_stats(self, monthly_data, year, month):
        """Create monthly statistics summary"""
        if not monthly_data:
            return html.Div([
                html.H4("Monthly Statistics", style={'color': '#2c3e50'}),
                html.P("No trading data available for this month", style={'color': '#7f8c8d'})
            ], style={'margin': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
        
        # Calculate monthly statistics
        total_pnl = sum(day_data['total_pnl'] for day_data in monthly_data.values())
        trading_days = len(monthly_data)
        winning_days = sum(1 for day_data in monthly_data.values() if day_data['total_pnl'] > 0)
        losing_days = sum(1 for day_data in monthly_data.values() if day_data['total_pnl'] < 0)
        total_trades = sum(day_data['trade_count'] for day_data in monthly_data.values())
        
        win_rate = (winning_days / trading_days * 100) if trading_days > 0 else 0
        avg_daily_pnl = total_pnl / trading_days if trading_days > 0 else 0
        
        best_day = max(monthly_data.items(), key=lambda x: x[1]['total_pnl'], default=(None, {'total_pnl': 0}))
        worst_day = min(monthly_data.items(), key=lambda x: x[1]['total_pnl'], default=(None, {'total_pnl': 0}))
        
        return html.Div([
            html.H4(f"{calendar.month_name[month]} {year} Statistics", style={'color': '#2c3e50', 'marginBottom': '15px'}),
            
            html.Div([
                html.Div([
                    html.H5("Total P&L", style={'margin': '0', 'color': '#34495e'}),
                    html.H3(f"${total_pnl:,.2f}", style={
                        'margin': '5px 0', 
                        'color': 'green' if total_pnl >= 0 else 'red'
                    })
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'}),
                
                html.Div([
                    html.H5("Trading Days", style={'margin': '0', 'color': '#34495e'}),
                    html.H3(f"{trading_days}", style={'margin': '5px 0', 'color': '#2c3e50'})
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'}),
                
                html.Div([
                    html.H5("Win Rate", style={'margin': '0', 'color': '#34495e'}),
                    html.H3(f"{win_rate:.1f}%", style={'margin': '5px 0', 'color': '#2c3e50'}),
                    html.P(f"{winning_days}W / {losing_days}L", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d'})
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'}),
                
                html.Div([
                    html.H5("Avg Daily P&L", style={'margin': '0', 'color': '#34495e'}),
                    html.H3(f"${avg_daily_pnl:,.2f}", style={
                        'margin': '5px 0', 
                        'color': 'green' if avg_daily_pnl >= 0 else 'red'
                    })
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'})
            ], className='row'),
            
            html.Hr(style={'margin': '15px 0'}),
            
            html.Div([
                html.Div([
                    html.Strong("Best Day: "),
                    html.Span(f"{best_day[0]} (${best_day[1]['total_pnl']:,.2f})" if best_day[0] else "N/A",
                             style={'color': 'green'})
                ], className='col-md-4'),
                
                html.Div([
                    html.Strong("Worst Day: "),
                    html.Span(f"{worst_day[0]} (${worst_day[1]['total_pnl']:,.2f})" if worst_day[0] else "N/A",
                             style={'color': 'red'})
                ], className='col-md-4'),
                
                html.Div([
                    html.Strong("Total Trades: "),
                    html.Span(f"{total_trades}")
                ], className='col-md-4')
            ], className='row')
            
        ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})
    
    def _create_calendar_view(self, monthly_data, year, month):
        """Create interactive calendar view"""
        # Create calendar matrix
        cal = calendar.monthcalendar(year, month)
        
        calendar_cells = []
        
        # Header row with day names
        weekday_headers = []
        for day_name in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            weekday_headers.append(
                html.Div(day_name, style={
                    'padding': '10px',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'backgroundColor': '#34495e',
                    'color': 'white',
                    'border': '1px solid #ddd'
                })
            )
        
        calendar_cells.append(html.Div(weekday_headers, style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(7, 1fr)',
            'gap': '1px'
        }))
        
        # Calendar body
        for week in cal:
            week_cells = []
            for day in week:
                if day == 0:
                    # Empty cell for days not in this month
                    week_cells.append(html.Div("", style={
                        'padding': '40px 10px',
                        'border': '1px solid #ddd',
                        'backgroundColor': '#f8f9fa'
                    }))
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    day_data = monthly_data.get(date_str, {})
                    
                    pnl = day_data.get('total_pnl', 0)
                    trade_count = day_data.get('trade_count', 0)
                    
                    # Determine cell color based on PnL
                    if pnl > 0:
                        bg_color = '#d4edda'  # Light green
                        pnl_color = 'green'
                    elif pnl < 0:
                        bg_color = '#f8d7da'  # Light red
                        pnl_color = 'red'
                    else:
                        bg_color = '#ffffff'
                        pnl_color = '#6c757d'
                    
                    # Make clickable if there's data
                    cell_style = {
                        'padding': '10px',
                        'border': '1px solid #ddd',
                        'backgroundColor': bg_color,
                        'minHeight': '80px',
                        'position': 'relative',
                        'cursor': 'pointer' if trade_count > 0 else 'default',
                        'transition': 'all 0.2s ease'
                    }
                    
                    if trade_count > 0:
                        cell_style['boxShadow'] = '0 2px 4px rgba(0,0,0,0.1)'
                        cell_style[':hover'] = {'transform': 'scale(1.05)'}
                    
                    cell_content = [
                        html.Div(str(day), style={
                            'fontWeight': 'bold',
                            'marginBottom': '5px',
                            'color': '#2c3e50'
                        })
                    ]
                    
                    if trade_count > 0:
                        cell_content.extend([
                            html.Div(f"${pnl:,.0f}", style={
                                'fontSize': '14px',
                                'fontWeight': 'bold',
                                'color': pnl_color
                            }),
                            html.Div(f"{trade_count} trade{'s' if trade_count != 1 else ''}", style={
                                'fontSize': '10px',
                                'color': '#6c757d',
                                'marginTop': '2px'
                            })
                        ])
                    
                    week_cells.append(
                        html.Div(
                            cell_content,
                            id={'type': 'calendar-day', 'date': date_str},
                            style=cell_style,
                            n_clicks=0
                        )
                    )
            
            calendar_cells.append(html.Div(week_cells, style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(7, 1fr)',
                'gap': '1px'
            }))
        
        return html.Div([
            html.H4("Trading Calendar", style={'color': '#2c3e50', 'marginBottom': '15px'}),
            html.Div(calendar_cells),
            html.P("Click on any day with trades to jump to that day's details", style={
                'textAlign': 'center',
                'color': '#6c757d',
                'fontStyle': 'italic',
                'marginTop': '15px'
            })
        ], style={'margin': '20px'})
    
    def _create_monthly_charts(self, monthly_data, year, month):
        """Create monthly performance charts"""
        if not monthly_data:
            return html.Div()
        
        # Prepare data for charts
        dates = sorted(monthly_data.keys())
        daily_pnl = [monthly_data[date]['total_pnl'] for date in dates]
        cumulative_pnl = []
        running_total = 0
        for pnl in daily_pnl:
            running_total += pnl
            cumulative_pnl.append(running_total)
        
        # Daily P&L Chart
        daily_chart = dcc.Graph(
            figure=px.bar(
                x=dates,
                y=daily_pnl,
                title=f"Daily P&L - {calendar.month_name[month]} {year}",
                labels={'x': 'Date', 'y': 'P&L ($)'},
                color=daily_pnl,
                color_continuous_scale=['red', 'white', 'green']
            ).update_layout(showlegend=False)
        )
        
        # Cumulative P&L Chart
        cumulative_chart = dcc.Graph(
            figure=px.line(
                x=dates,
                y=cumulative_pnl,
                title=f"Cumulative P&L - {calendar.month_name[month]} {year}",
                labels={'x': 'Date', 'y': 'Cumulative P&L ($)'}
            ).update_traces(line_color='#2c3e50')
        )
        
        return html.Div([
            html.Div([daily_chart], className='col-md-6'),
            html.Div([cumulative_chart], className='col-md-6')
        ], className='row', style={'margin': '20px'})
    
    def _get_monthly_data(self, year, month):
        """Get all trading data for a specific month"""
        print(f"DEBUG: _get_monthly_data called for {year}-{month}")
        print(f"DEBUG: DATA_DIR = {DATA_DIR}")
        
        monthly_data = {}
        
        # Get all days in the month
        num_days = calendar.monthrange(year, month)[1]
        print(f"DEBUG: Month has {num_days} days")
        
        for day in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            
            # Try multiple file patterns and formats
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
                    print(f"DEBUG: Found file: {filename}")
                    break
            
            if not file_found:
                continue
                
            try:
                # Determine file type and process accordingly
                if file_found.endswith('.csv'):
                    trades_df = self.trade_processor.calculate_trades_csv_rithmic(file_found)
                else:
                    # For .xls/.xlsx files, use the original Excel processing method
                    print(f"DEBUG: Processing Excel file: {file_found}")
                    import pandas as pd
                    df = pd.read_excel(file_found, header=None)
                    df.columns = ["date", "time", "exchange", "contract", "B/S", "Size", "Price", "F", "Direct"]
                    processed_df = self.trade_processor.process_raw_data(df)
                    trades_df = self.trade_processor.calculate_trades(processed_df)
                
                print(f"DEBUG: Processed {file_found}, got {len(trades_df)} trades")
                if not trades_df.empty and 'pnl' in trades_df.columns:
                    total_pnl = trades_df['pnl'].sum()
                    trade_count = len(trades_df)
                    
                    # Get per-contract breakdown
                    contract_summary = {}
                    if 'contract' in trades_df.columns:
                        for contract in trades_df['contract'].str.split().str[0].unique():
                            contract_trades = trades_df[trades_df['contract'].str.startswith(contract)]
                            contract_summary[contract] = {
                                'pnl': contract_trades['pnl'].sum(),
                                'trades': len(contract_trades)
                            }
                    
                    monthly_data[date_str] = {
                        'total_pnl': total_pnl,
                        'trade_count': trade_count,
                        'contracts': contract_summary
                    }
            except Exception as e:
                print(f"Error processing {date_str}: {e}")
                continue
        
        return monthly_data
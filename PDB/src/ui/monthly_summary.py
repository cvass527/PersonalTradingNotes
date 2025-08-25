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
            
            # Trade Quality Analysis
            self._create_trade_quality_analysis(monthly_data, year, month),
            
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
                              style={'padding': '8px 12px', 'margin': '0 5px', 'fontSize': '16px',
                                     'backgroundColor': 'var(--bg-secondary)', 'color': 'var(--text-primary)',
                                     'border': '1px solid var(--border-color)', 'borderRadius': 'var(--radius-medium)'}),
                    html.H3(f"{calendar.month_name[month]} {year}", 
                           id='month-display',
                           style={'display': 'inline-block', 'margin': '0 20px', 'color': 'var(--text-primary)'}),
                    html.Button('▶', id='next-month', n_clicks=0,
                              style={'padding': '8px 12px', 'margin': '0 5px', 'fontSize': '16px',
                                     'backgroundColor': 'var(--bg-secondary)', 'color': 'var(--text-primary)',
                                     'border': '1px solid var(--border-color)', 'borderRadius': 'var(--radius-medium)'})
                ], style={'textAlign': 'center', 'marginBottom': '20px', 'backgroundColor': 'var(--bg-secondary)', 
                         'padding': '16px', 'borderRadius': 'var(--radius-large)', 'border': '1px solid var(--border-color)'}),
                
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
                ], style={'textAlign': 'center', 'marginBottom': '20px', 'backgroundColor': 'var(--bg-secondary)', 
                         'padding': '16px', 'borderRadius': 'var(--radius-large)', 'border': '1px solid var(--border-color)'})
            ])
        ], id='month-navigation')
    
    def _create_monthly_stats(self, monthly_data, year, month):
        """Create monthly statistics summary"""
        if not monthly_data:
            return html.Div([
                html.H4("Monthly Statistics", style={'color': 'var(--text-primary)'}),
                html.P("No trading data available for this month", style={'color': 'var(--text-secondary)'})
            ], className='trading-card', style={'margin': '20px'})
        
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
            html.H4(f"{calendar.month_name[month]} {year} Statistics", style={'color': 'var(--text-primary)', 'marginBottom': '15px'}),
            
            html.Div([
                html.Div([
                    html.H5("Total P&L", style={'margin': '0', 'color': 'var(--text-secondary)'}),
                    html.H3(f"${total_pnl:,.2f}", style={
                        'margin': '5px 0', 
                        'color': 'var(--profit-color)' if total_pnl >= 0 else 'var(--loss-color)'
                    })
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'}),
                
                html.Div([
                    html.H5("Trading Days", style={'margin': '0', 'color': 'var(--text-secondary)'}),
                    html.H3(f"{trading_days}", style={'margin': '5px 0', 'color': 'var(--text-primary)'})
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'}),
                
                html.Div([
                    html.H5("Win Rate", style={'margin': '0', 'color': 'var(--text-secondary)'}),
                    html.H3(f"{win_rate:.1f}%", style={'margin': '5px 0', 'color': 'var(--text-primary)'}),
                    html.P(f"{winning_days}W / {losing_days}L", style={'margin': '0', 'fontSize': '12px', 'color': 'var(--text-tertiary)'})
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'}),
                
                html.Div([
                    html.H5("Avg Daily P&L", style={'margin': '0', 'color': 'var(--text-secondary)'}),
                    html.H3(f"${avg_daily_pnl:,.2f}", style={
                        'margin': '5px 0', 
                        'color': 'var(--profit-color)' if avg_daily_pnl >= 0 else 'var(--loss-color)'
                    })
                ], className='col-md-3', style={'textAlign': 'center', 'padding': '10px'})
            ], className='row'),
            
            html.Hr(style={'margin': '15px 0', 'borderColor': 'var(--border-color)'}),
            
            html.Div([
                html.Div([
                    html.Strong("Best Day: ", style={'color': 'var(--text-primary)'}),
                    html.Span(f"{best_day[0]} (${best_day[1]['total_pnl']:,.2f})" if best_day[0] else "N/A",
                             style={'color': 'var(--profit-color)'})
                ], className='col-md-4'),
                
                html.Div([
                    html.Strong("Worst Day: ", style={'color': 'var(--text-primary)'}),
                    html.Span(f"{worst_day[0]} (${worst_day[1]['total_pnl']:,.2f})" if worst_day[0] else "N/A",
                             style={'color': 'var(--loss-color)'})
                ], className='col-md-4'),
                
                html.Div([
                    html.Strong("Total Trades: ", style={'color': 'var(--text-primary)'}),
                    html.Span(f"{total_trades}", style={'color': 'var(--text-primary)'})
                ], className='col-md-4')
            ], className='row')
            
        ], className='trading-card', style={'margin': '20px'})
    
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
                    'backgroundColor': 'var(--bg-secondary)',
                    'color': 'var(--text-primary)',
                    'border': '1px solid var(--border-color)'
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
                        'border': '1px solid var(--border-color)',
                        'backgroundColor': 'var(--bg-tertiary)'
                    }))
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    day_data = monthly_data.get(date_str, {})
                    
                    pnl = day_data.get('total_pnl', 0)
                    trade_count = day_data.get('trade_count', 0)
                    
                    # Determine cell color based on PnL
                    if pnl > 0:
                        bg_color = 'rgba(48, 209, 88, 0.15)'  # Dark theme green
                        pnl_color = 'var(--profit-color)'
                    elif pnl < 0:
                        bg_color = 'rgba(255, 69, 58, 0.15)'  # Dark theme red
                        pnl_color = 'var(--loss-color)'
                    else:
                        bg_color = 'var(--bg-secondary)'
                        pnl_color = 'var(--text-tertiary)'
                    
                    # Make clickable if there's data
                    cell_style = {
                        'padding': '10px',
                        'border': '1px solid var(--border-color)',
                        'backgroundColor': bg_color,
                        'minHeight': '80px',
                        'position': 'relative',
                        'cursor': 'pointer' if trade_count > 0 else 'default',
                        'transition': 'all 0.2s ease',
                        'color': 'var(--text-primary)'
                    }
                    
                    if trade_count > 0:
                        cell_style['boxShadow'] = '0 2px 4px rgba(0,0,0,0.1)'
                        cell_style[':hover'] = {'transform': 'scale(1.05)'}
                    
                    cell_content = [
                        html.Div(str(day), style={
                            'fontWeight': 'bold',
                            'marginBottom': '5px',
                            'color': 'var(--text-primary)'
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
                                'color': 'var(--text-tertiary)',
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
            html.H4("Trading Calendar", style={'color': 'var(--text-primary)', 'marginBottom': '15px'}),
            html.Div(calendar_cells),
            html.P("Click on any day with trades to jump to that day's details", style={
                'textAlign': 'center',
                'color': 'var(--text-tertiary)',
                'fontStyle': 'italic',
                'marginTop': '15px'
            })
        ], className='trading-card', style={'margin': '20px'})
    
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
        
        # Daily P&L Chart with dark theme
        daily_fig = px.bar(
            x=dates,
            y=daily_pnl,
            title=f"Daily P&L - {calendar.month_name[month]} {year}",
            labels={'x': 'Date', 'y': 'P&L ($)'},
            color=daily_pnl,
            color_continuous_scale=['#ff453a', '#48484a', '#30d158']
        )
        daily_fig.update_layout(
            showlegend=False,
            plot_bgcolor='#2c2c2e',
            paper_bgcolor='#2c2c2e',
            font=dict(color='#ffffff'),
            title_font_color='#ffffff',
            xaxis=dict(gridcolor='#48484a', color='#ffffff'),
            yaxis=dict(gridcolor='#48484a', color='#ffffff')
        )
        daily_chart = dcc.Graph(figure=daily_fig)
        
        # Cumulative P&L Chart with dark theme
        cumulative_fig = px.line(
            x=dates,
            y=cumulative_pnl,
            title=f"Cumulative P&L - {calendar.month_name[month]} {year}",
            labels={'x': 'Date', 'y': 'Cumulative P&L ($)'}
        )
        cumulative_fig.update_traces(line_color='#007aff')
        cumulative_fig.update_layout(
            plot_bgcolor='#2c2c2e',
            paper_bgcolor='#2c2c2e',
            font=dict(color='#ffffff'),
            title_font_color='#ffffff',
            xaxis=dict(gridcolor='#48484a', color='#ffffff'),
            yaxis=dict(gridcolor='#48484a', color='#ffffff')
        )
        cumulative_chart = dcc.Graph(figure=cumulative_fig)
        
        return html.Div([
            html.Div([daily_chart], className='col-md-6'),
            html.Div([cumulative_chart], className='col-md-6')
        ], className='row trading-card', style={'margin': '20px'})
    
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
    
    def _create_trade_quality_analysis(self, monthly_data, year, month):
        """Create trade quality analysis section"""
        if not monthly_data:
            return html.Div()
        
        # Get trade quality data for all days in the month
        quality_data = self._get_trade_quality_data(year, month)
        
        if not quality_data:
            return html.Div([
                html.H4("🎯 Trade Quality Analysis", style={'color': 'var(--text-primary)', 'marginBottom': '15px'}),
                html.P("No trade quality data available for this month", 
                      style={'color': 'var(--text-secondary)', 'textAlign': 'center', 'padding': '20px'})
            ], className='trading-card', style={'margin': '20px'})
        
        # Create quality categories with styling
        quality_categories = {
            'fantastic': {'name': '🌟 Fantastic', 'color': 'rgba(48, 209, 88, 0.25)', 'border': '#30d158'},
            'good': {'name': '✅ Good', 'color': 'rgba(48, 209, 88, 0.15)', 'border': '#30d158'},
            'attention': {'name': '⚠️ Attention', 'color': 'rgba(255, 204, 2, 0.15)', 'border': '#ffcc02'},
            'uncertain': {'name': '🤔 Uncertain', 'color': 'rgba(255, 149, 0, 0.15)', 'border': '#ff9500'},
            'bad': {'name': '❌ Bad', 'color': 'rgba(255, 69, 58, 0.15)', 'border': '#ff453a'}
        }
        
        quality_sections = []
        
        for quality_key, quality_info in quality_categories.items():
            if quality_key in quality_data and quality_data[quality_key]['trades']:
                trades = quality_data[quality_key]['trades']
                total_pnl = quality_data[quality_key]['total_pnl']
                trade_count = len(trades)
                
                # Create trade cards for this quality - show ALL trades
                trade_cards = []
                for trade in trades:  # Show ALL trades, no limit
                    # Clean up contract name (remove quotes)
                    contract_clean = trade.get('contract', 'N/A').replace('"', '')
                    
                    trade_cards.append(
                        html.Div([
                            # Header row with date and P&L
                            html.Div([
                                html.Strong(f"{trade['date']}", style={'color': 'var(--text-primary)'}),
                                html.Span(f" • ${trade['pnl']:,.2f}", 
                                         style={'color': 'var(--profit-color)' if trade['pnl'] >= 0 else 'var(--loss-color)',
                                               'fontWeight': 'bold'})
                            ], style={'marginBottom': '8px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                            
                            # Trade details row
                            html.Div([
                                html.Div([
                                    html.Span("📈 Product: ", style={'color': 'var(--text-tertiary)', 'fontSize': '12px'}),
                                    html.Span(contract_clean, style={'color': 'var(--text-secondary)', 'fontSize': '12px', 'fontWeight': '500'})
                                ], style={'marginBottom': '4px'}),
                                
                                html.Div([
                                    html.Span("📏 Quantity: ", style={'color': 'var(--text-tertiary)', 'fontSize': '12px'}),
                                    html.Span(f"{trade.get('quantity', 0)}", style={'color': 'var(--text-secondary)', 'fontSize': '12px', 'fontWeight': '500'}),
                                    html.Span(f" ({trade.get('direction', 'N/A')})", style={'color': 'var(--text-tertiary)', 'fontSize': '11px'})
                                ], style={'marginBottom': '4px'}),
                                
                                html.Div([
                                    html.Span("⏰ Time: ", style={'color': 'var(--text-tertiary)', 'fontSize': '12px'}),
                                    html.Span(f"{trade.get('entry_time', 'N/A')} → {trade.get('exit_time', 'N/A')}", 
                                             style={'color': 'var(--text-secondary)', 'fontSize': '12px', 'fontFamily': 'monospace'})
                                ], style={'marginBottom': '8px'})
                            ], style={'backgroundColor': 'rgba(0,0,0,0.1)', 'padding': '8px', 'borderRadius': 'var(--radius-small)', 'marginBottom': '8px'}),
                            
                            # Notes section
                            html.P(trade.get('note', 'No notes'), 
                                  style={'color': 'var(--text-secondary)', 'fontSize': '14px', 'margin': '0',
                                        'fontStyle': 'italic' if not trade.get('note') else 'normal',
                                        'lineHeight': '1.4'})
                        ], style={
                            'padding': '16px', 'marginBottom': '12px',
                            'backgroundColor': 'var(--bg-tertiary)', 
                            'borderRadius': 'var(--radius-medium)',
                            'border': f'1px solid {quality_info["border"]}',
                            'borderLeft': f'4px solid {quality_info["border"]}',
                            'transition': 'all 0.2s ease'
                        })
                    )
                
                # Show total count for this category
                trade_cards.append(
                    html.Div(
                        f"Total: {len(trades)} trades in this category",
                        style={'color': 'var(--text-tertiary)', 'fontStyle': 'italic', 'textAlign': 'center',
                               'padding': '8px', 'marginTop': '8px', 'fontSize': '12px',
                               'borderTop': f'1px solid {quality_info["border"]}', 'opacity': '0.7'}
                    )
                )
                
                quality_sections.append(
                    html.Div([
                        html.Div([
                            html.H5(quality_info['name'], style={'color': 'var(--text-primary)', 'margin': '0'}),
                            html.Div([
                                html.Span(f"{trade_count} trades", style={'color': 'var(--text-secondary)', 'marginRight': '16px'}),
                                html.Span(f"${total_pnl:,.2f}", style={
                                    'fontWeight': 'bold', 'fontSize': '18px',
                                    'color': 'var(--profit-color)' if total_pnl >= 0 else 'var(--loss-color)'
                                })
                            ])
                        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '16px'}),
                        
                        html.Div(trade_cards)
                    ], style={
                        'backgroundColor': quality_info['color'],
                        'border': f'2px solid {quality_info["border"]}',
                        'borderRadius': 'var(--radius-large)',
                        'padding': '20px',
                        'marginBottom': '16px'
                    })
                )
        
        if not quality_sections:
            return html.Div([
                html.H4("🎯 Trade Quality Analysis", style={'color': 'var(--text-primary)', 'marginBottom': '15px'}),
                html.P("No rated trades found for this month", 
                      style={'color': 'var(--text-secondary)', 'textAlign': 'center', 'padding': '20px'})
            ], className='trading-card', style={'margin': '20px'})
        
        return html.Div([
            html.H4("🎯 Trade Quality Analysis", style={'color': 'var(--text-primary)', 'marginBottom': '20px'}),
            html.P(f"Analysis of trade quality ratings for {calendar.month_name[month]} {year}", 
                  style={'color': 'var(--text-secondary)', 'marginBottom': '24px'}),
            html.Div(quality_sections)
        ], className='trading-card', style={'margin': '20px'})
    
    def _get_trade_quality_data(self, year, month):
        """Get trade quality data for all days in the month"""
        from notes.trade_note_manager import TradeNoteManager
        
        trade_note_manager = TradeNoteManager()
        print(f"DEBUG: Looking for trade quality data for {year}-{month}")
        
        # Check if any trade colors exist at all
        all_colors = trade_note_manager.load_trade_colors()
        print(f"DEBUG: Total trade colors saved: {len(all_colors)}")
        if all_colors:
            print(f"DEBUG: Sample trade IDs with colors: {list(all_colors.items())[:5]}")
        quality_data = {
            'fantastic': {'trades': [], 'total_pnl': 0},
            'good': {'trades': [], 'total_pnl': 0},
            'attention': {'trades': [], 'total_pnl': 0},
            'uncertain': {'trades': [], 'total_pnl': 0},
            'bad': {'trades': [], 'total_pnl': 0}
        }
        
        # Get all days in the month
        num_days = calendar.monthrange(year, month)[1]
        
        for day in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            
            # Try to find and process the trading file for this day
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
                    break
            
            if not file_found:
                continue
                
            try:
                print(f"DEBUG: Processing file {file_found} for {date_str}")
                import pandas as pd
                
                # Process the trades file to get individual trades using the same method as app.py
                if file_found.endswith('.csv'):
                    trades_df = self.trade_processor.calculate_trades_csv_rithmic(file_found)
                else:
                    # For .xls/.xlsx files, use the original Excel processing method
                    df = pd.read_excel(file_found, header=None)
                    df.columns = ["date", "time", "exchange", "contract", "B/S", "Size", "Price", "F", "Direct"]
                    processed_df = self.trade_processor.process_raw_data(df)
                    trades_df = self.trade_processor.calculate_trades(processed_df)
                
                print(f"DEBUG: Found {len(trades_df)} trades in {date_str}")
                print(f"DEBUG: Trades DataFrame columns: {list(trades_df.columns)}")
                if not trades_df.empty:
                    print(f"DEBUG: First trade sample: {trades_df.iloc[0].to_dict()}")
                
                # Format times for display (same as dashboard_components)
                if 'entry_time' in trades_df.columns:
                    trades_df['entry_time_display'] = trades_df['entry_time'].dt.strftime('%I:%M:%S %p')
                if 'exit_time' in trades_df.columns:
                    trades_df['exit_time_display'] = trades_df['exit_time'].dt.strftime('%I:%M:%S %p')
                
                # Get trade qualities and notes for each trade
                trades_with_ratings = 0
                for index, trade_row in trades_df.iterrows():
                    if 'pnl' not in trade_row or pd.isna(trade_row['pnl']):
                        print(f"DEBUG: Skipping trade {index} - no P&L data")
                        continue
                    
                    # Generate trade ID using the same method as dashboard_components
                    # Use the display formatted times (same as dashboard)
                    entry_time_str = trade_row.get('entry_time_display', str(trade_row.get('entry_time', '')))
                    exit_time_str = trade_row.get('exit_time_display', str(trade_row.get('exit_time', '')))
                    
                    trade_id = trade_note_manager.generate_trade_id(
                        date_str, 
                        str(trade_row.get('contract', '')), 
                        entry_time_str, 
                        exit_time_str
                    )
                    trade_color = trade_note_manager.get_trade_color(trade_id)
                    trade_note = trade_note_manager.get_trade_note(trade_id)
                    
                    print(f"DEBUG: Trade {index} - ID: {trade_id}")
                    print(f"DEBUG: Trade {index} - P&L: {trade_row['pnl']}, Contract: {trade_row.get('contract', 'N/A')}")
                    print(f"DEBUG: Trade {index} - Color: {trade_color}, Note: {trade_note}")
                    
                    if trade_color and trade_color != 'none' and trade_color in quality_data:
                        print(f"DEBUG: ✅ Adding trade to {trade_color} category")
                        trades_with_ratings += 1
                        quality_data[trade_color]['trades'].append({
                            'date': date_str,
                            'pnl': float(trade_row['pnl']),
                            'note': trade_note or '',
                            'trade_id': trade_id,
                            'contract': str(trade_row.get('contract', 'N/A')),
                            'quantity': trade_row.get('quantity', 0),
                            'entry_time': entry_time_str,
                            'exit_time': exit_time_str,
                            'direction': trade_row.get('direction', 'N/A')
                        })
                        quality_data[trade_color]['total_pnl'] += float(trade_row['pnl'])
                    else:
                        print(f"DEBUG: ❌ Trade not added - Color: {trade_color}, Valid: {trade_color in quality_data if trade_color else False}")
                
                print(f"DEBUG: Found {trades_with_ratings} trades with ratings for {date_str}")
                        
            except Exception as e:
                print(f"Error processing trade quality for {date_str}: {e}")
                continue
        
        # Debug: Show final results
        total_rated_trades = sum(len(data['trades']) for data in quality_data.values())
        print(f"DEBUG: FINAL SUMMARY - Total rated trades found: {total_rated_trades}")
        for category, data in quality_data.items():
            if data['trades']:
                print(f"DEBUG: Found {len(data['trades'])} {category} trades with total P&L: ${data['total_pnl']:.2f}")
        
        if total_rated_trades == 0:
            print("DEBUG: ⚠️ No rated trades found! Possible reasons:")
            print("DEBUG: 1. No trades have quality ratings assigned")
            print("DEBUG: 2. Trade IDs don't match between saving and loading")
            print("DEBUG: 3. All trades have 'none' quality rating")
        
        return quality_data
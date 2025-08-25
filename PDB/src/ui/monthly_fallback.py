import calendar
import os
from datetime import datetime
from config import DATA_DIR
from dash import html

class MonthlyFallback:
    """Fallback monthly summary that works without pandas/plotly but still uses dash html"""
    
    def create_monthly_summary(self, year=None, month=None):
        """Create a simple monthly summary using dash html components"""
        if year is None or month is None:
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
        
        # Get month data
        monthly_data = self._get_monthly_data_simple(year, month)
        
        return html.Div([
            html.H2(f"📅 {calendar.month_name[month]} {year} Trading Summary", 
                   className='fade-in',
                   style={'textAlign': 'center', 'marginBottom': '32px', 'color': 'var(--text-primary)'}),
            
            # Modern statistics section
            html.Div([
                html.H3("📊 Statistics", style={'marginBottom': '20px'}),
                html.Div([
                    html.Div([
                        html.Div("Trading Days", className='stats-label'),
                        html.Div(f"{len(monthly_data)}", className='stats-value neutral')
                    ], className='stats-card col-md-4'),
                    
                    html.Div([
                        html.Div("Files Found", className='stats-label'),
                        html.Div(f"{len(monthly_data)}", className='stats-value profit')
                    ], className='stats-card col-md-4'),
                    
                    html.Div([
                        html.Div("Data Ready", className='stats-label'),
                        html.Div("✅", className='stats-value', style={'fontSize': '32px'})
                    ], className='stats-card col-md-4')
                ], className='row'),
                
                html.P(f"📂 Found files: {', '.join(list(monthly_data.keys())[:3])}{'...' if len(monthly_data) > 3 else ''}", 
                      style={'marginTop': '16px', 'color': 'var(--text-tertiary)', 'textAlign': 'center'}),
            ], className='trading-card fade-in'),
            
            # Calendar preview with modern styling
            html.Div([
                html.H3("📈 Interactive Calendar Preview", style={'marginBottom': '20px'}),
                html.P("Your full trading calendar will look like this:", 
                      style={'color': 'var(--text-secondary)', 'marginBottom': '16px'}),
                html.Div([
                    html.Pre(self._create_text_calendar(monthly_data, year, month),
                            style={'fontSize': '14px', 'fontFamily': 'SF Mono, Monaco, monospace',
                                  'color': 'var(--accent-blue)', 'lineHeight': '1.6'})
                ], className='calendar-container')
            ], className='trading-card fade-in'),
            
            # Modern upgrade instructions
            html.Div([
                html.H3("🚀 Unlock Full Power", style={'marginBottom': '20px'}),
                html.P("Install dependencies for the complete experience:", 
                      style={'color': 'var(--text-secondary)', 'marginBottom': '16px'}),
                
                html.Div([
                    html.Code("pip install pandas plotly", 
                             style={'padding': '12px 16px', 'borderRadius': 'var(--radius-medium)',
                                   'backgroundColor': 'var(--bg-tertiary)', 'color': 'var(--accent-blue)',
                                   'fontFamily': 'SF Mono, Monaco, monospace', 'fontSize': '14px',
                                   'display': 'block', 'textAlign': 'center', 'fontWeight': '600'})
                ], style={'marginBottom': '20px'}),
                
                html.P("Then restart your app to unlock:", style={'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.Span("📅", style={'fontSize': '20px', 'marginRight': '8px'}),
                        html.Span("Interactive calendar with clickable days")
                    ], style={'margin': '8px 0', 'color': 'var(--text-secondary)'}),
                    html.Div([
                        html.Span("📊", style={'fontSize': '20px', 'marginRight': '8px'}),
                        html.Span("Real P&L calculations and win rates")
                    ], style={'margin': '8px 0', 'color': 'var(--text-secondary)'}),
                    html.Div([
                        html.Span("📈", style={'fontSize': '20px', 'marginRight': '8px'}),
                        html.Span("Beautiful performance charts and visualizations")
                    ], style={'margin': '8px 0', 'color': 'var(--text-secondary)'}),
                    html.Div([
                        html.Span("🔄", style={'fontSize': '20px', 'marginRight': '8px'}),
                        html.Span("Smooth month navigation and animations")
                    ], style={'margin': '8px 0', 'color': 'var(--text-secondary)'})
                ])
            ], className='trading-card glass-effect fade-in',
               style={'border': '2px solid var(--accent-blue)', 'marginTop': '24px'})
            
        ], className='slide-in')
    
    def _get_monthly_data_simple(self, year, month):
        """Simple version without pandas/processing"""
        monthly_data = {}
        
        # Get all days in the month
        num_days = calendar.monthrange(year, month)[1]
        
        for day in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            
            # Try multiple file patterns
            possible_files = [
                f'{date_str}.csv',
                f'trades_{date_str}.csv', 
                f'{date_str}.xls',
                f'trades_{date_str}.xls',
                f'{date_str}.xlsx',
                f'trades_{date_str}.xlsx'
            ]
            
            for filename in possible_files:
                file_path = os.path.join(DATA_DIR, filename)
                if os.path.exists(file_path):
                    monthly_data[date_str] = {
                        'file': filename,
                        'path': file_path
                    }
                    break
        
        return monthly_data
    
    def _create_text_calendar(self, monthly_data, year, month):
        """Create simple text calendar"""
        cal = calendar.monthcalendar(year, month)
        
        result = "Mon  Tue  Wed  Thu  Fri  Sat  Sun\n"
        result += "-" * 35 + "\n"
        
        for week in cal:
            week_str = ""
            for day in week:
                if day == 0:
                    week_str += "     "
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if date_str in monthly_data:
                        week_str += f"{day:2d}$  "  # Has trading data
                    else:
                        week_str += f"{day:2d}   "  # No data
            result += week_str + "\n"
        
        return result
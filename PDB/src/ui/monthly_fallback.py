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
                   style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '30px'}),
            
            # Statistics section
            html.Div([
                html.H3("📊 Statistics", style={'color': '#34495e'}),
                html.P(f"Trading Days: {len(monthly_data)}", style={'fontSize': '16px'}),
                html.P(f"Files Found: {', '.join(list(monthly_data.keys())[:5])}{' ...' if len(monthly_data) > 5 else ''}", 
                      style={'fontSize': '14px', 'color': '#6c757d'}),
                html.P(f"Data Directory: {DATA_DIR}", style={'fontSize': '12px', 'color': '#6c757d'})
            ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px', 'margin': '20px 0'}),
            
            # Calendar preview
            html.Div([
                html.H3("📈 Calendar View Preview", style={'color': '#34495e'}),
                html.P("Your trading calendar would show:"),
                html.Pre(self._create_text_calendar(monthly_data, year, month),
                        style={'backgroundColor': '#ffffff', 'padding': '15px', 'border': '1px solid #ddd',
                               'borderRadius': '4px', 'fontSize': '14px', 'fontFamily': 'monospace'})
            ], style={'backgroundColor': '#e8f5e8', 'padding': '20px', 'borderRadius': '8px', 'margin': '20px 0'}),
            
            # Instructions
            html.Div([
                html.H3("🔧 To Enable Full Interactive Monthly View:", style={'color': '#34495e'}),
                html.P("Install the required dependencies:"),
                html.Code("pip install pandas plotly", 
                         style={'backgroundColor': '#f1f1f1', 'padding': '8px', 'borderRadius': '4px',
                                'display': 'block', 'margin': '10px 0'}),
                html.P("Then restart your app and you'll get:"),
                html.Ul([
                    html.Li("📅 Interactive calendar with clickable days"),
                    html.Li("📊 Real P&L calculations and statistics"),
                    html.Li("📈 Performance charts and visualizations"),
                    html.Li("🔄 Month navigation controls")
                ])
            ], style={'backgroundColor': '#fff3e0', 'padding': '20px', 'borderRadius': '8px', 'margin': '20px 0'})
            
        ], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})
    
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
import plotly.express as px
from dash import html, dcc, dash_table

class DashboardComponents:
    @staticmethod
    def create_dashboard(trades_df, note=''):
        trades_df = trades_df.copy()
        if not trades_df.empty:
            trades_df['duration_seconds'] = trades_df['duration'].dt.total_seconds()
            trades_df['entry_time'] = trades_df['entry_time'].dt.strftime('%I:%M:%S %p')
            trades_df['exit_time'] = trades_df['exit_time'].dt.strftime('%I:%M:%S %p')

        return html.Div([
            DashboardComponents._create_pnl_chart(trades_df),
            DashboardComponents._create_timeline_chart(trades_df),
            DashboardComponents._create_summary_section(trades_df),
            DashboardComponents._create_trade_table(trades_df)
        ])
    
    @staticmethod
    def _create_pnl_chart(trades_df):
        return dcc.Graph(
            figure=px.bar(
                trades_df,
                x='contract',
                y='pnl',
                color='direction',
                barmode='group',
                title='PnL by Contract and Direction',
                labels={'pnl': 'Profit/Loss ($)'}
            ) if not trades_df.empty else {}
        )
    
    @staticmethod
    def _create_timeline_chart(trades_df):
        return dcc.Graph(
            figure=px.scatter(
                trades_df,
                x='exit_time',
                y='pnl',
                color='contract',
                title='Trade Performance Timeline',
                labels={'pnl': 'Profit/Loss ($)', 'exit_time': 'Exit Time'}
            ) if not trades_df.empty else {}
        )
    
    @staticmethod
    def _create_summary_section(trades_df):
        return html.Div([
            html.H3("Trade Summary", style={'color': '#2c3e50'}),
            html.P(f"Total PnL: ${trades_df['pnl'].sum():.2f}", style={'fontSize': 18}),
            *[html.P(f"{contract} Total: ${trades_df[trades_df['contract'].str.startswith(contract)]['pnl'].sum():.2f}")
              for contract in trades_df['contract'].str.split().str[0].unique()],
            html.P(f"Total Trades: {len(trades_df)}")
        ], style={'margin': '20px', 'padding': '15px', 'borderRadius': '5px', 'backgroundColor': '#f8f9fa'})
    
    @staticmethod
    def _create_trade_table(trades_df):
        return dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in trades_df.columns] if not trades_df.empty else [],
            data=trades_df.to_dict('records'),
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '8px'},
            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'}
        ) 
import plotly.express as px
from dash import html, dcc, dash_table


class DashboardComponents:
    @staticmethod
    def create_dashboard(trades_df, note=''):
        # Handle empty DataFrame case
        if trades_df.empty:
            return html.Div([
                html.H3("No trade data available for this date",
                        style={'textAlign': 'center', 'color': '#7f8c8d', 'margin': '50px'}),
                html.P("Upload a CSV file for this date to see trade analysis.",
                       style={'textAlign': 'center', 'color': '#95a5a6'})
            ])

        trades_df = trades_df.copy()
        # Format time columns if they exist
        if 'duration' in trades_df.columns:
            trades_df['duration_seconds'] = trades_df['duration'].dt.total_seconds()
        if 'entry_time' in trades_df.columns:
            trades_df['entry_time'] = trades_df['entry_time'].dt.strftime('%I:%M:%S %p')
        if 'exit_time' in trades_df.columns:
            trades_df['exit_time'] = trades_df['exit_time'].dt.strftime('%I:%M:%S %p')

        return html.Div([
            DashboardComponents._create_pnl_chart(trades_df),
            DashboardComponents._create_timeline_chart(trades_df),
            DashboardComponents._create_summary_section(trades_df),
            DashboardComponents._create_trade_table(trades_df)
        ])

    @staticmethod
    def _create_pnl_chart(trades_df):
        if trades_df.empty or 'pnl' not in trades_df.columns:
            return dcc.Graph(figure={})

        return dcc.Graph(
            figure=px.bar(
                trades_df,
                x='contract',
                y='pnl',
                color='direction' if 'direction' in trades_df.columns else None,
                barmode='group',
                title='PnL by Contract and Direction',
                labels={'pnl': 'Profit/Loss ($)'}
            )
        )

    @staticmethod
    def _create_timeline_chart(trades_df):
        if trades_df.empty or 'pnl' not in trades_df.columns or 'exit_time' not in trades_df.columns:
            return dcc.Graph(figure={})

        return dcc.Graph(
            figure=px.scatter(
                trades_df,
                x='exit_time',
                y='pnl',
                color='contract' if 'contract' in trades_df.columns else None,
                title='Trade Performance Timeline',
                labels={'pnl': 'Profit/Loss ($)', 'exit_time': 'Exit Time'}
            )
        )

    @staticmethod
    def _create_summary_section(trades_df):
        if trades_df.empty or 'pnl' not in trades_df.columns:
            return html.Div([
                html.H3("Trade Summary", style={'color': '#2c3e50'}),
                html.P("No trades found for this date", style={'fontSize': 18, 'color': '#7f8c8d'})
            ], style={'margin': '20px', 'padding': '15px', 'borderRadius': '5px', 'backgroundColor': '#f8f9fa'})

        # Build summary with safe column access
        summary_items = [
            html.H3("Trade Summary", style={'color': '#2c3e50'}),
            html.P(f"Total PnL: ${trades_df['pnl'].sum():.2f}", style={'fontSize': 18})
        ]

        # Add per-contract summaries if contract column exists
        if 'contract' in trades_df.columns:
            try:
                for contract in trades_df['contract'].str.split().str[0].unique():
                    contract_pnl = trades_df[trades_df['contract'].str.startswith(contract)]['pnl'].sum()
                    summary_items.append(
                        html.P(f"{contract} Total: ${contract_pnl:.2f}")
                    )
            except Exception:
                # If contract parsing fails, just show total
                pass

        summary_items.append(html.P(f"Total Trades: {len(trades_df)}"))

        return html.Div(summary_items,
                        style={'margin': '20px', 'padding': '15px', 'borderRadius': '5px',
                               'backgroundColor': '#f8f9fa'})

    @staticmethod
    def _create_trade_table(trades_df):
        if trades_df.empty:
            return html.Div([
                html.H4("Trade Details"),
                html.P("No trade data to display", style={'color': '#7f8c8d', 'fontStyle': 'italic'})
            ])

        return dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in trades_df.columns],
            data=trades_df.to_dict('records'),
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '8px'},
            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'}
        )
import plotly.express as px
from dash import html, dcc, dash_table
from notes.trade_note_manager import TradeNoteManager


class DashboardComponents:
    @staticmethod
    def create_dashboard(trades_df, note='', date_str=''):
        # Handle empty DataFrame case
        if trades_df.empty:
            return html.Div([
                html.H3("No trade data available for this date",
                        style={'textAlign': 'center', 'color': '#7f8c8d', 'margin': '50px'}),
                html.P("Upload a CSV file for this date to see trade analysis.",
                       style={'textAlign': 'center', 'color': '#95a5a6'})
            ])

        trades_df = trades_df.copy()
        
        # Store original datetime columns for sorting
        if 'entry_time' in trades_df.columns:
            trades_df['entry_time_sort'] = trades_df['entry_time']
        if 'exit_time' in trades_df.columns:
            trades_df['exit_time_sort'] = trades_df['exit_time']
        
        # Format duration for display
        if 'duration' in trades_df.columns:
            trades_df['duration_seconds'] = trades_df['duration'].dt.total_seconds()
        
        # Sort by exit time chronologically BEFORE formatting
        if 'exit_time' in trades_df.columns:
            trades_df = trades_df.sort_values('exit_time').reset_index(drop=True)
        
        # NOW format for display
        if 'entry_time' in trades_df.columns:
            trades_df['entry_time_display'] = trades_df['entry_time'].dt.strftime('%I:%M:%S %p')
        if 'exit_time' in trades_df.columns:
            trades_df['exit_time_display'] = trades_df['exit_time'].dt.strftime('%I:%M:%S %p')

        return html.Div([
            DashboardComponents._create_pnl_chart(trades_df),
            DashboardComponents._create_timeline_chart(trades_df),
            DashboardComponents._create_summary_section(trades_df),
            DashboardComponents._create_trade_cards(trades_df, date_str)
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
                x='exit_time',  # Use datetime object, not formatted string
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
    def _create_trade_cards(trades_df, date_str=''):
        if trades_df.empty:
            return html.Div([
                html.H4("Individual Trade Analysis", style={'color': '#2c3e50', 'marginBottom': '20px'}),
                html.P("No trade data to display", style={'color': '#7f8c8d', 'fontStyle': 'italic'})
            ])

        # Create display version of DataFrame with formatted times
        display_df = trades_df.copy()
        
        # Replace datetime columns with formatted versions for display
        if 'entry_time_display' in display_df.columns:
            display_df['entry_time'] = display_df['entry_time_display']
            display_df = display_df.drop('entry_time_display', axis=1)
        if 'exit_time_display' in display_df.columns:
            display_df['exit_time'] = display_df['exit_time_display'] 
            display_df = display_df.drop('exit_time_display', axis=1)
        
        # Remove sorting helper columns
        display_df = display_df.drop([col for col in display_df.columns if col.endswith('_sort')], axis=1)

        # Initialize trade note manager
        trade_note_manager = TradeNoteManager()
        
        # Create individual trade cards
        trade_cards = []
        
        for idx, row in display_df.iterrows():
            # Create unique trade ID
            trade_id = trade_note_manager.generate_trade_id(
                date_str, 
                str(row.get('contract', '')), 
                str(row.get('entry_time', '')), 
                str(row.get('exit_time', ''))
            )
            
            # Load existing note and color for this trade
            existing_note = trade_note_manager.get_trade_note(trade_id)
            existing_color = trade_note_manager.get_trade_color(trade_id)
            
            # Define color scheme
            color_options = [
                {'label': 'No Rating', 'value': 'none'},
                {'label': '🔴 Bad - Learn from this', 'value': 'bad'},
                {'label': '🟠 Didn\'t work - Uncertain', 'value': 'uncertain'},
                {'label': '🟡 Pay attention - Missed something', 'value': 'attention'},
                {'label': '🟢 Good - Could do better', 'value': 'good'},
                {'label': '💵 Fantastic - Keep doing this', 'value': 'fantastic'}
            ]
            
            # Color mapping for backgrounds
            color_backgrounds = {
                'none': '#ffffff',
                'bad': '#ffebee',        # Light red
                'uncertain': '#fff3e0', # Light orange  
                'attention': '#fffde7', # Light yellow
                'good': '#e8f5e8',      # Light green
                'fantastic': '#e0f2f1'  # Dollar bill green
            }
            
            # Create trade info grid
            trade_info = html.Div([
                html.Div([
                    html.Div([
                        html.Strong("Contract: "),
                        html.Span(str(row.get('contract', 'N/A')))
                    ], className='col-md-2'),
                    html.Div([
                        html.Strong("Direction: "),
                        html.Span(str(row.get('direction', 'N/A')), 
                                style={'color': 'green' if row.get('direction') == 'Long' else 'red'})
                    ], className='col-md-1'),
                    html.Div([
                        html.Strong("Size: "),
                        html.Span(f"{int(row.get('quantity', 0))} lots")
                    ], className='col-md-1'),
                    html.Div([
                        html.Strong("Entry: "),
                        html.Span(f"{row.get('entry_time', 'N/A')} @ ${row.get('entry_price', 0):.2f}")
                    ], className='col-md-3'),
                    html.Div([
                        html.Strong("Exit: "),
                        html.Span(f"{row.get('exit_time', 'N/A')} @ ${row.get('exit_price', 0):.2f}")
                    ], className='col-md-3'),
                    html.Div([
                        html.Strong("P&L: "),
                        html.Span(f"${row.get('pnl', 0):.2f}", 
                                style={'color': 'green' if row.get('pnl', 0) >= 0 else 'red', 'fontWeight': 'bold'})
                    ], className='col-md-2')
                ], className='row', style={'marginBottom': '10px'})
            ])
            
            # Create notes section
            notes_section = html.Div([
                html.Div([
                    html.Div([
                        html.Label("Trade Quality:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id={'type': 'trade-color', 'index': idx},
                            options=color_options,
                            value=existing_color,
                            placeholder="Select trade quality...",
                            style={'marginBottom': '10px'}
                        )
                    ], className='col-md-4'),
                    html.Div([
                        html.Button(
                            'Save All',
                            id={'type': 'save-trade', 'index': idx},
                            n_clicks=0,
                            style={
                                'marginTop': '25px',
                                'padding': '8px 16px',
                                'backgroundColor': '#2c3e50',
                                'color': 'white',
                                'border': 'none',
                                'borderRadius': '4px',
                                'cursor': 'pointer'
                            }
                        )
                    ], className='col-md-2'),
                    html.Div([
                        html.Div(id={'type': 'save-status', 'index': idx}, 
                               style={'marginTop': '28px', 'color': 'green', 'fontWeight': 'bold'})
                    ], className='col-md-6')
                ], className='row'),
                html.Label("Trade Notes:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'marginTop': '10px'}),
                dcc.Textarea(
                    id={'type': 'trade-note', 'index': idx},
                    value=existing_note,
                    placeholder="Enter your analysis, observations, and lessons learned for this trade...",
                    style={
                        'width': '100%',
                        'height': '100px',
                        'padding': '8px',
                        'border': '1px solid #ddd',
                        'borderRadius': '4px',
                        'fontSize': '14px',
                        'resize': 'vertical'
                    }
                )
            ])
            
            # Create trade card with dynamic background color
            card_background = color_backgrounds.get(existing_color, '#ffffff')
            trade_card = html.Div([
                html.H6(f"Trade #{idx + 1}", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                trade_info,
                html.Hr(style={'margin': '15px 0'}),
                notes_section,
                html.Div(trade_id, id={'type': 'trade-id', 'index': idx}, style={'display': 'none'})  # Hidden trade ID
            ], 
            id={'type': 'trade-card', 'index': idx},
            style={
                'border': '1px solid #ddd',
                'borderRadius': '8px',
                'padding': '20px',
                'marginBottom': '20px',
                'backgroundColor': card_background,
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'transition': 'background-color 0.3s ease'
            })
            
            trade_cards.append(trade_card)
        
        return html.Div([
            html.H4("Individual Trade Analysis", style={'color': '#2c3e50', 'marginBottom': '20px'}),
            html.Div(trade_cards)
        ])
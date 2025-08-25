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

        fig = px.bar(
            trades_df,
            x='contract',
            y='pnl',
            color='direction' if 'direction' in trades_df.columns else None,
            barmode='group',
            title='📊 P&L by Contract and Direction',
            labels={'pnl': 'Profit/Loss ($)', 'contract': 'Contract', 'direction': 'Direction'},
            color_discrete_map={'Long': '#34c759', 'Short': '#ff453a'}
        )
        
        # Apply dark theme styling
        fig.update_layout(
            paper_bgcolor='#2c2c2e',
            plot_bgcolor='#3a3a3c',
            font=dict(color='#ffffff', family='SF Pro Display, -apple-system, sans-serif', size=14),
            title=dict(font=dict(size=18, color='#ffffff'), x=0.5),
            xaxis=dict(
                gridcolor='#48484a',
                zerolinecolor='#48484a',
                tickfont=dict(color='#ffffff')
            ),
            yaxis=dict(
                gridcolor='#48484a', 
                zerolinecolor='#48484a',
                tickfont=dict(color='#ffffff')
            ),
            legend=dict(
                font=dict(color='#ffffff'),
                bgcolor='rgba(0,0,0,0.3)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            ),
            margin=dict(t=60, b=60, l=60, r=60)
        )
        
        return dcc.Graph(
            figure=fig,
            style={'backgroundColor': 'transparent'}
        )

    @staticmethod
    def _create_timeline_chart(trades_df):
        if trades_df.empty or 'pnl' not in trades_df.columns or 'exit_time' not in trades_df.columns:
            return dcc.Graph(figure={})

        fig = px.scatter(
            trades_df,
            x='exit_time',  # Use datetime object, not formatted string
            y='pnl',
            color='contract' if 'contract' in trades_df.columns else None,
            title='📈 Trade Performance Timeline',
            labels={'pnl': 'Profit/Loss ($)', 'exit_time': 'Exit Time'},
            size_max=15
        )
        
        # Apply dark theme styling
        fig.update_layout(
            paper_bgcolor='#2c2c2e',
            plot_bgcolor='#3a3a3c',
            font=dict(color='#ffffff', family='SF Pro Display, -apple-system, sans-serif', size=14),
            title=dict(font=dict(size=18, color='#ffffff'), x=0.5),
            xaxis=dict(
                gridcolor='#48484a',
                zerolinecolor='#48484a',
                tickfont=dict(color='#ffffff')
            ),
            yaxis=dict(
                gridcolor='#48484a', 
                zerolinecolor='#48484a',
                tickfont=dict(color='#ffffff')
            ),
            legend=dict(
                font=dict(color='#ffffff'),
                bgcolor='rgba(0,0,0,0.3)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            ),
            margin=dict(t=60, b=60, l=60, r=60)
        )
        
        # Update traces for better visibility
        fig.update_traces(
            marker=dict(size=8, line=dict(width=2, color='rgba(255,255,255,0.3)'))
        )
        
        return dcc.Graph(
            figure=fig,
            style={'backgroundColor': 'transparent'}
        )

    @staticmethod
    def _create_summary_section(trades_df):
        if trades_df.empty or 'pnl' not in trades_df.columns:
            return html.Div([
                html.H3("📊 Trade Summary", className='fade-in'),
                html.P("No trades found for this date", 
                      style={'fontSize': '16px', 'color': 'var(--text-tertiary)'})
            ], className='trading-card')

        total_pnl = trades_df['pnl'].sum()
        winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
        losing_trades = len(trades_df[trades_df['pnl'] < 0]) if 'pnl' in trades_df.columns else 0
        win_rate = (winning_trades / len(trades_df) * 100) if len(trades_df) > 0 else 0
        
        # Create modern stats cards
        stats_cards = [
            html.Div([
                html.Div([
                    html.Div("Total P&L", className='stats-label'),
                    html.Div(f"${total_pnl:.2f}", 
                            className=f'stats-value {"profit" if total_pnl >= 0 else "loss"}')
                ], className='stats-card')
            ], className='col-md-3'),
            
            html.Div([
                html.Div([
                    html.Div("Total Trades", className='stats-label'),
                    html.Div(f"{len(trades_df)}", className='stats-value neutral')
                ], className='stats-card')
            ], className='col-md-3'),
            
            html.Div([
                html.Div([
                    html.Div("Win Rate", className='stats-label'),
                    html.Div(f"{win_rate:.1f}%", 
                            className=f'stats-value {"profit" if win_rate >= 50 else "loss"}')
                ], className='stats-card')
            ], className='col-md-3'),
            
            html.Div([
                html.Div([
                    html.Div("W/L Ratio", className='stats-label'),
                    html.Div(f"{winning_trades}/{losing_trades}", className='stats-value neutral')
                ], className='stats-card')
            ], className='col-md-3')
        ]

        # Add per-contract breakdown if available
        contract_breakdown = []
        if 'contract' in trades_df.columns:
            try:
                for contract in trades_df['contract'].str.split().str[0].unique():
                    contract_trades = trades_df[trades_df['contract'].str.startswith(contract)]
                    contract_pnl = contract_trades['pnl'].sum()
                    contract_breakdown.append(
                        html.Div([
                            html.Span(f"{contract}: ", 
                                    style={'fontWeight': '500', 'color': 'var(--text-secondary)'}),
                            html.Span(f"${contract_pnl:.2f}", 
                                    className=f'{"pnl-positive" if contract_pnl >= 0 else "pnl-negative"}')
                        ], style={'margin': '8px 0'})
                    )
            except Exception:
                pass

        return html.Div([
            html.H3("📊 Daily Performance", className='fade-in', 
                   style={'marginBottom': '24px'}),
            html.Div(stats_cards, className='row fade-in'),
            html.Div([
                html.H5("📈 Contract Breakdown", style={'marginTop': '24px', 'marginBottom': '16px'}),
                html.Div(contract_breakdown)
            ] if contract_breakdown else [], className='fade-in', style={'marginTop': '20px'})
        ], className='trading-card')

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
            
            # Define color scheme with better contrast
            color_options = [
                {'label': '⚪ No Rating', 'value': 'none'},
                {'label': '🔴 Bad - Learn from this', 'value': 'bad'},
                {'label': '🟠 Uncertain - Needs analysis', 'value': 'uncertain'},
                {'label': '🟡 Attention - Could improve', 'value': 'attention'},
                {'label': '🟢 Good - Solid execution', 'value': 'good'},
                {'label': '💎 Fantastic - Perfect trade', 'value': 'fantastic'}
            ]
            
            # Enhanced color mapping with better backgrounds and text contrast
            color_mapping = {
                'none': {
                    'background': 'var(--bg-secondary)',
                    'border': 'var(--bg-elevated)',
                    'text': 'var(--text-primary)'
                },
                'bad': {
                    'background': 'rgba(255, 69, 58, 0.15)',
                    'border': 'var(--loss-red)',
                    'text': '#ff6b6b'
                },
                'uncertain': {
                    'background': 'rgba(255, 149, 0, 0.15)',
                    'border': 'var(--accent-orange)',
                    'text': '#ff9500'
                },
                'attention': {
                    'background': 'rgba(255, 204, 2, 0.15)',
                    'border': '#ffcc02',
                    'text': '#ffcc02'
                },
                'good': {
                    'background': 'rgba(48, 209, 88, 0.15)',
                    'border': 'var(--profit-green)',
                    'text': '#34c759'
                },
                'fantastic': {
                    'background': 'rgba(48, 209, 88, 0.25)',
                    'border': 'var(--profit-green)',
                    'text': '#30d158'
                }
            }
            
            # Create modern trade info grid
            pnl = row.get('pnl', 0)
            direction = row.get('direction', 'N/A')
            
            # Get color scheme for text contrast
            quality_colors = color_mapping.get(existing_color, color_mapping['none'])
            
            trade_info = html.Div([
                # Trade header with P&L prominence
                html.Div([
                    html.Div([
                        html.H6(f"📈 Trade #{idx + 1}", 
                               style={'margin': '0', 'color': 'white', 'fontWeight': '600'}),
                        html.Div(f"${pnl:.2f}", 
                                style={'fontSize': '28px', 'fontWeight': '700', 'margin': '4px 0',
                                      'color': '#ffffff' if pnl >= 0 else '#ff6b6b'})
                    ], className='col-md-6'),
                    html.Div([
                        html.Div([
                            html.Span("📋 ", style={'fontSize': '16px'}),
                            html.Span(str(row.get('contract', 'N/A')), 
                                    style={'fontWeight': '600', 'color': '#ffffff', 'fontSize': '18px'})
                        ], style={'marginBottom': '8px'}),
                        html.Div([
                            html.Span("📊 ", style={'fontSize': '16px'}),
                            html.Span(f"{direction} • {int(row.get('quantity', 0))} lots",
                                    style={'fontWeight': '600', 'color': '#ffffff', 'fontSize': '16px'})
                        ])
                    ], className='col-md-6', style={'textAlign': 'right'})
                ], className='row', style={'marginBottom': '16px'}),
                
                # Trade details with better contrast
                html.Div([
                    html.Div([
                        html.Div("🟢 Entry", style={'fontSize': '14px', 'color': '#ffffff', 'fontWeight': '700', 'marginBottom': '4px'}),
                        html.Div(f"{row.get('entry_time', 'N/A')}", 
                                style={'fontSize': '14px', 'color': 'rgba(255,255,255,0.8)'}),
                        html.Div(f"${row.get('entry_price', 0):.2f}", 
                                style={'fontSize': '18px', 'fontWeight': '600', 'color': '#ffffff'})
                    ], className='col-md-6'),
                    html.Div([
                        html.Div("🔴 Exit", style={'fontSize': '14px', 'color': '#ffffff', 'fontWeight': '700', 'marginBottom': '4px'}),
                        html.Div(f"{row.get('exit_time', 'N/A')}", 
                                style={'fontSize': '14px', 'color': 'rgba(255,255,255,0.8)'}),
                        html.Div(f"${row.get('exit_price', 0):.2f}", 
                                style={'fontSize': '18px', 'fontWeight': '600', 'color': '#ffffff'})
                    ], className='col-md-6')
                ], className='row')
            ])
            
            # Create simplified notes section without individual save button
            notes_section = html.Div([
                html.Hr(style={'margin': '20px 0', 'border': '1px solid rgba(255,255,255,0.2)'}),
                
                html.Div([
                    html.Label("⭐ Trade Quality:", 
                             style={'fontWeight': '600', 'marginBottom': '8px', 
                                   'color': '#ffffff', 'fontSize': '16px'}),
                    dcc.Dropdown(
                        id={'type': 'trade-color', 'index': idx},
                        options=color_options,
                        value=existing_color,
                        placeholder="Rate this trade...",
                        style={'backgroundColor': 'rgba(0,0,0,0.3)', 'color': '#ffffff', 'marginBottom': '16px'}
                    )
                ]),
                
                html.Label("📝 Trade Notes:", 
                         style={'fontWeight': '600', 'marginBottom': '8px', 
                               'color': '#ffffff', 'fontSize': '16px'}),
                dcc.Textarea(
                    id={'type': 'trade-note', 'index': idx},
                    value=existing_note,
                    placeholder="📊 What worked well? What could be improved? Key insights and lessons...",
                    style={
                        'width': '100%', 'minHeight': '100px', 'resize': 'vertical',
                        'backgroundColor': 'rgba(0,0,0,0.3)',
                        'color': '#ffffff',
                        'border': '2px solid rgba(255,255,255,0.2)',
                        'borderRadius': '12px',
                        'padding': '16px'
                    }
                )
            ], style={'marginTop': '16px'})
            
            # Get color scheme for this trade quality
            quality_colors = color_mapping.get(existing_color, color_mapping['none'])
            
            trade_card = html.Div([
                trade_info,
                notes_section,
                html.Div(trade_id, id={'type': 'trade-id', 'index': idx}, style={'display': 'none'})  # Hidden trade ID
            ], 
            id={'type': 'trade-card', 'index': idx},
            className='trade-card fade-in',
            style={
                'background': quality_colors['background'],
                'border': f'2px solid {quality_colors["border"]}',
                'borderRadius': 'var(--radius-large)',
                'padding': '24px',
                'marginBottom': '24px',
                'transition': 'all 0.3s ease',
                'backdropFilter': 'blur(20px)',
                'boxShadow': 'var(--shadow-medium)'
            })
            
            trade_cards.append(trade_card)
        
        return html.Div([
            html.H3("🔍 Individual Trade Analysis", 
                   className='fade-in',
                   style={'marginBottom': '24px', 'color': 'var(--text-primary)'}),
            html.Div(trade_cards, className='slide-in')
        ])
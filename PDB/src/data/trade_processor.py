import pandas as pd
from datetime import datetime

class TradeProcessor:
    def __init__(self, contract_manager):
        self.contract_manager = contract_manager
    
    def process_raw_data(self, df):
        df['datetime'] = pd.to_datetime(
            (df['date'] + ' ' + df['time']).str.strip(),
            format='%d%b%y %H:%M:%S.%f',
            dayfirst=True
        )
        return df.sort_values('datetime').reset_index(drop=True)
    
    def calculate_trades(self, df):
        trades = []
        open_positions = {}  # Tracks positions by base contract

        for _, row in df.iterrows():
            full_contract = row['contract']
            base_contract = full_contract.split()[0]
            action = row['B/S']
            size = row['Size']
            price = row['Price']
            timestamp = row['datetime']

            # Initialize position tracking for new contracts
            if base_contract not in open_positions:
                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }

            # Update position
            prev_position = open_positions[base_contract]['position']
            new_position = prev_position + (size if action == 'B' else -size)

            # Handle position changes
            if prev_position == 0 and new_position != 0:
                # New position opened
                open_positions[base_contract].update({
                    'position': new_position,
                    'entry_price': price,
                    'entry_time': timestamp,
                    'entry_action': action
                })
            elif new_position == 0 and prev_position != 0:
                # Position closed
                entry_price = open_positions[base_contract]['entry_price']
                entry_time = open_positions[base_contract]['entry_time']
                entry_action = open_positions[base_contract]['entry_action']

                specs = self.contract_manager.load_contracts()[base_contract]
                price_diff = (price - entry_price) if entry_action == 'B' else (entry_price - price)
                ticks = price_diff / specs['tick_size']
                pnl = ticks * specs['tick_value'] * abs(prev_position)

                trades.append({
                    'contract': full_contract,
                    'entry_time': entry_time,
                    'exit_time': timestamp,
                    'duration': timestamp - entry_time,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'quantity': abs(prev_position),
                    'pnl': pnl,
                    'direction': 'Long' if entry_action == 'B' else 'Short'
                })

                # Reset position
                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }
            else:
                # Update existing position
                open_positions[base_contract]['position'] = new_position

        return pd.DataFrame(trades) 
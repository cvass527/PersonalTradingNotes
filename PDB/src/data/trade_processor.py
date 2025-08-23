import pandas as pd
import os

from classes.AT import AggregatedTrade
from classes.TD import TradeDate

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

    def calculate_trades_csv_rithmic(self, df):

        # Read the raw lines of the CSV file

        current_file = os.path.abspath(__file__)  # PDB/src/data/trade_processor.py
        src_dir = os.path.dirname(current_file)  # PDB/src/data
        project_src = os.path.dirname(src_dir)  # PDB/src
        project_root = os.path.dirname(project_src)  # PDB <-- your project root

        file_path = os.path.join(project_root, 'trading_data', '2025-08-10.csv')

        print("Looking for file at:", file_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            print("File found!")
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        else:
            print("File not found!")



        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]


        # Find contract names
        contracts = []
        for i, line in enumerate(lines):
            if line.split(',')[0] in ['CLQ5', 'ESU5', 'NGQ25']:  # Extend this list if more contract names are possible
                contracts.append((i, line.split(',')))


        # Instantiate the TradeDate object for the given date
        trade_date = TradeDate('2025-08-10')

        # Process each contract section
        for idx, (start_idx, contract_name) in enumerate(contracts):
            header = lines[start_idx + 1].split(',')



            if idx < len(contracts) - 1:
                end_idx = contracts[idx + 1][0]
            else:
                end_idx = len(lines)


            # Extract trades data rows, ignoring lines with contract names
            trades = [l.split(',') for l in lines[start_idx + 2:end_idx] if
                      l.strip() and l.split(',') not in ['CLQ5', 'ESU5', 'NGQ25']]

            if not trades:
                continue

            # Create DataFrame for the contract's trades
            df = pd.DataFrame(trades, columns=header)

            # Convert numeric columns
            for col in ['Commission & Fees', 'Trade P&L', 'Fill Size']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Aggregate by Entry Order Number
            grouped = df.groupby('Entry Order Number', as_index=False).agg({
                'Commission & Fees': 'sum',
                'Trade P&L': 'sum',
                'Fill Size': 'sum'
            })

            # Convert each row to AggregatedTrade and add to TradeDate
            for _, row in grouped.iterrows():
                agg_trade = AggregatedTrade(
                    entry_order_number=row['Entry Order Number'],
                    commission_fees=row['Commission & Fees'],
                    trade_pnl=row['Trade P&L'],
                    fill_size=row['Fill Size']
                )

                trade_date.add_trade(contract_name[0], agg_trade)

        return trade_date


        return pd.DataFrame(trades)

    def calculate_trades_csv(self, df):
        trades = []
        open_positions = {}  # Tracks positions by base contract

        for _, row in df.iterrows():
            full_contract = row['Symbol']
            base_contract = full_contract.split()[0]
            action = row['Action']
            size = row['Quantity']
            price = row['Price']
            timestamp = row['ConvertedTime']

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
            new_position = prev_position + (size if action == 'BOT' else -size)

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
                price_diff = (price - entry_price) if entry_action == 'BOT' else (entry_price - price)
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
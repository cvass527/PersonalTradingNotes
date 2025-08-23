import pandas as pd
import numpy as np
from datetime import datetime
import re

# For Python 3.8 and below, use typing imports
# For Python 3.9+, you can use built-in list, dict instead
try:
    from typing import Dict, List, Tuple, Optional
except ImportError:
    # Fallback for older Python versions
    Dict = dict
    List = list
    Tuple = tuple
    Optional = None


class TradeProcessor:
    def __init__(self, contract_manager):
        self.contract_manager = contract_manager

    def calculate_trades_csv_rithmic(self, df_or_file_path) -> pd.DataFrame:
        """
        Process Rithmic CSV data into aggregated trades by contract.

        Args:
            df_or_file_path: Either a DataFrame with raw CSV lines or file path

        Returns:
            DataFrame with aggregated trade data by contract
        """
        try:
            # Handle both DataFrame and file path inputs
            if isinstance(df_or_file_path, str):
                with open(df_or_file_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
            elif hasattr(df_or_file_path, 'iloc'):
                # Convert DataFrame back to lines (assuming single column with CSV text)
                lines = df_or_file_path.iloc[:, 0].dropna().tolist()
            else:
                raise ValueError("Input must be DataFrame or file path")

            # Parse the CSV structure
            contracts_data = self._parse_rithmic_csv(lines)

            # In your calculate_trades_csv_rithmic method, add this back:
            print(f"Found contracts: {list(contracts_data.keys())}")

            # Convert to summary DataFrame
            result_df = self._create_summary_dataframe(contracts_data)
            return result_df

        except Exception as e:
            print(f"ERROR processing Rithmic data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _parse_rithmic_csv(self, lines: List[str]) -> Dict[str, Dict]:
        """Parse the Rithmic CSV structure into contract sections."""
        contracts_data = {}
        current_contract = None
        current_section = None

        # Known contract patterns (you can extend this)
        contract_patterns = [r'^[A-Z]{2,3}[A-Z]\d+$', r'^[A-Z]{2,3}[A-Z]\d{2}$']

        for line in lines:
            if not line or line.startswith(',,,'):
                continue

            fields = [field.strip() for field in line.split(',')]

            # Check if this is a contract name line
            if self._is_contract_line(fields[0]):
                current_contract = fields[0]
                contracts_data[current_contract] = {
                    'summary': self._parse_contract_summary(fields),
                    'trades': []
                }
                current_section = 'summary'
                print(f"DEBUG: Set current_contract to {current_contract}, section = summary")
                continue

            # Check if this is a trade header (handle quoted fields)
            clean_fields = [field.strip('"') for field in fields]
            if 'Trade Date' in clean_fields and 'Entry Order Number' in clean_fields:
                print(f"DEBUG: Found trade header for {current_contract}, setting section to trades_header")
                current_section = 'trades_header'
                continue

            # ADD THIS DEBUG to see what lines are being processed:
            if current_contract:
                print(f"DEBUG: Processing line for {current_contract}, section={current_section}, fields={fields[:3]}")

            # Process trade data lines
            if current_contract and current_section == 'trades_header' and len(fields) >= 10:
                print(f"DEBUG: About to call _parse_trade_line")
                print(f"DEBUG: Trying to parse trade line for {current_contract}: {fields[:3]}...")
                try:
                    trade_data = self._parse_trade_line(fields)
                    if trade_data:
                        print(f"DEBUG: Successfully parsed trade: {trade_data['entry_order_number']}")
                        contracts_data[current_contract]['trades'].append(trade_data)
                    else:
                        print(f"DEBUG: _parse_trade_line returned None")
                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse trade line: {line} - {e}")
                    continue

        return contracts_data

    def _is_contract_line(self, field: str) -> bool:
        """Check if a field represents a contract name."""
        # Clean quotes first
        clean_field = field.strip('"')

        # Add this debug:
        if any(contract in clean_field for contract in ['CLQ5', 'ESU5', 'NGQ25']):
            print(f"DEBUG: Testing contract field: '{field}' -> '{clean_field}'")

        if not clean_field or clean_field.isdigit():
            return False

        # Check against known patterns - make sure this is complete!
        patterns = [r'^[A-Z]{2,3}[A-Z]\d+$', r'^[A-Z]{2,3}[A-Z]\d{2}$']
        result = any(re.match(pattern, clean_field) for pattern in patterns)

        # Add this debug:
        if any(contract in clean_field for contract in ['CLQ5', 'ESU5', 'NGQ25']):
            print(f"DEBUG: Pattern match result for '{clean_field}': {result}")

        return result

    def _parse_contract_summary(self, fields: List[str]) -> Dict:
        """Parse contract summary line."""
        try:
            # Clean quotes from all fields
            clean_fields = [field.strip('"') for field in fields]

            return {
                'contract': clean_fields[0],
                'trade_pnl': float(clean_fields[1]) if clean_fields[1] else 0,
                'commission_fees': float(clean_fields[2]) if clean_fields[2] else 0,
                'net_pnl': float(clean_fields[3]) if clean_fields[3] else 0,
                'trade_count': int(clean_fields[4]) if clean_fields[4] else 0,
                'winning_trades': int(clean_fields[5]) if clean_fields[5] else 0,
                'losing_trades': int(clean_fields[6]) if clean_fields[6] else 0,
                'win_percent': float(clean_fields[7]) if clean_fields[7] else 0,
                'lose_percent': float(clean_fields[8]) if clean_fields[8] else 0
            }
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error parsing contract summary: {e}")
            return {'contract': fields[0].strip('"'), 'trade_pnl': 0, 'commission_fees': 0}

    def _parse_trade_line(self, fields: List[str]) -> Optional[Dict]:
        """Parse individual trade line."""
        print(f"DEBUG: _parse_trade_line called with {len(fields)} fields")

        if len(fields) < 14:
            print(f"DEBUG: Too few fields: {len(fields)}, need 14")
            return None

        try:
            # Clean quotes from fields
            clean_fields = [field.strip('"') for field in fields]
            print(f"DEBUG: Clean fields sample: {clean_fields[:5]}")

            result = {
                'trade_date': clean_fields[0],
                'entry_order_number': clean_fields[1],
                'entry_buy_sell': clean_fields[2],
                'entry_time': clean_fields[3],
                'entry_price': float(clean_fields[4]),
                'exit_order_number': clean_fields[5],
                'exit_buy_sell': clean_fields[6],
                'exit_time': clean_fields[7],
                'exit_price': float(clean_fields[8]),
                'trade_life_span': float(clean_fields[9]),
                'fill_size': int(clean_fields[10]),
                'trade_pnl': float(clean_fields[11]),
                'commission_fees': float(clean_fields[12]),
                'net_pnl': float(clean_fields[13])
            }

            print(f"DEBUG: Successfully created trade data: {result['entry_order_number']}")
            return result

        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error in _parse_trade_line: {e}")
            print(f"DEBUG: Fields were: {fields[:5]}")
            return None

        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error in _parse_trade_line: {e}")
            print(f"DEBUG: Fields were: {fields[:5]}")
            return None

    def _create_summary_dataframe(self, contracts_data: Dict) -> pd.DataFrame:
        """Create summary DataFrame that matches your dashboard's expected format."""
        trade_rows = []

        print(f"DEBUG: Processing {len(contracts_data)} contracts")

        for contract, data in contracts_data.items():
            trades = data['trades']
            print(f"DEBUG: Contract {contract} has {len(trades)} trades")

            # Group trades by entry order number (scale in/out positions)
            grouped_trades = self._group_scale_trades(trades)

            # Create individual trade rows (matching your dashboard format)
            for grouped_trade in grouped_trades:
                print(f"DEBUG: Processing grouped trade: {grouped_trade}")

                # Add error handling for datetime parsing
                try:
                    trade_rows.append({
                        'contract': contract,
                        'entry_time': grouped_trade['entry_time'],
                        'exit_time': grouped_trade['exit_time'],
                        'duration': grouped_trade['duration'],
                        'entry_price': grouped_trade['avg_entry_price'],
                        'exit_price': grouped_trade['avg_exit_price'],
                        'quantity': grouped_trade['total_quantity'],
                        'pnl': grouped_trade['total_pnl'],
                        'direction': grouped_trade['direction'],
                        'num_exits': grouped_trade['num_exits']  # Track how many partial exits
                    })
                except Exception as e:
                    print(f"DEBUG: Error processing grouped trade: {e}")
                    continue

        print(f"DEBUG: Created {len(trade_rows)} trade rows")
        df = pd.DataFrame(trade_rows)

        # Sort by exit time chronologically
        if not df.empty and 'exit_time' in df.columns:
            df = df.sort_values('exit_time').reset_index(drop=True)
            print(f"DEBUG: Sorted DataFrame by exit_time")

        return df

    def _group_scale_trades(self, trades: List[Dict]) -> List[Dict]:
        """Group trades that are part of the same position (same entry order number)."""
        if not trades:
            return []

        # Group by entry order number
        grouped = {}
        for trade in trades:
            entry_order = trade['entry_order_number']
            if entry_order not in grouped:
                grouped[entry_order] = []
            grouped[entry_order].append(trade)

        # Convert each group into a single aggregated trade
        result = []
        for entry_order, trade_group in grouped.items():
            if not trade_group:
                continue

            # Sort by exit time to get proper entry/exit times
            trade_group.sort(key=lambda x: x['exit_time'])

            first_trade = trade_group[0]
            last_trade = trade_group[-1]

            # Calculate weighted averages and totals
            total_quantity = sum(t['fill_size'] for t in trade_group)
            total_pnl = sum(t['trade_pnl'] for t in trade_group)

            # Calculate weighted average prices
            total_entry_value = sum(t['entry_price'] * t['fill_size'] for t in trade_group)
            total_exit_value = sum(t['exit_price'] * t['fill_size'] for t in trade_group)
            avg_entry_price = total_entry_value / total_quantity if total_quantity > 0 else 0
            avg_exit_price = total_exit_value / total_quantity if total_quantity > 0 else 0

            # Duration from first entry to last exit
            try:
                entry_time = pd.to_datetime(first_trade['entry_time'])
                exit_time = pd.to_datetime(last_trade['exit_time'])
                duration = exit_time - entry_time
            except Exception:
                entry_time = first_trade['entry_time']
                exit_time = last_trade['exit_time']
                duration = pd.Timedelta(seconds=last_trade['trade_life_span'])

            result.append({
                'entry_time': entry_time,
                'exit_time': exit_time,
                'duration': duration,
                'avg_entry_price': avg_entry_price,
                'avg_exit_price': avg_exit_price,
                'total_quantity': total_quantity,
                'total_pnl': total_pnl,
                'direction': 'Long' if first_trade['entry_buy_sell'] == 'B' else 'Short',
                'num_exits': len(trade_group),  # How many partial exits
                'entry_order_number': entry_order
            })

        return result

    # Keep your existing methods for other formats
    def process_raw_data(self, df):
        """Process raw Excel data format."""
        df['datetime'] = pd.to_datetime(
            (df['date'] + ' ' + df['time']).str.strip(),
            format='%d%b%y %H:%M:%S.%f',
            dayfirst=True
        )
        return df.sort_values('datetime').reset_index(drop=True)

    def calculate_trades(self, df):
        """Calculate trades from processed Excel data."""
        trades = []
        open_positions = {}

        for _, row in df.iterrows():
            full_contract = row['contract']
            base_contract = full_contract.split()[0]
            action = row['B/S']
            size = row['Size']
            price = row['Price']
            timestamp = row['datetime']

            if base_contract not in open_positions:
                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }

            prev_position = open_positions[base_contract]['position']
            new_position = prev_position + (size if action == 'B' else -size)

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

                try:
                    specs = self.contract_manager.load_contracts()[base_contract]
                    price_diff = (price - entry_price) if entry_action == 'B' else (entry_price - price)
                    ticks = price_diff / specs['tick_size']
                    pnl = ticks * specs['tick_value'] * abs(prev_position)
                except KeyError:
                    print(f"Warning: Contract {base_contract} not found in contracts")
                    pnl = 0

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

                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }
            else:
                open_positions[base_contract]['position'] = new_position

        return pd.DataFrame(trades), [r'^[A-Z]{2,3}[A-Z]\d+$', r'^[A-Z]{2,3}[A-Z]\d{2}$']

    def _parse_contract_summary(self, fields: List[str]) -> Dict:
        """Parse contract summary line."""
        try:
            return {
                'contract': fields[0],
                'trade_pnl': float(fields[1]) if fields[1] else 0,
                'commission_fees': float(fields[2]) if fields[2] else 0,
                'net_pnl': float(fields[3]) if fields[3] else 0,
                'trade_count': int(fields[4]) if fields[4] else 0,
                'winning_trades': int(fields[5]) if fields[5] else 0,
                'losing_trades': int(fields[6]) if fields[6] else 0,
                'win_percent': float(fields[7]) if fields[7] else 0,
                'lose_percent': float(fields[8]) if fields[8] else 0
            }
        except (ValueError, IndexError):
            return {'contract': fields[0], 'trade_pnl': 0, 'commission_fees': 0}

    def _parse_trade_line(self, fields: List[str]) -> Optional[Dict]:
        """Parse individual trade line."""
        if len(fields) < 14:
            print(f"DEBUG: Trade line too short: {len(fields)} fields, expected 14")
            return None

        try:
            # Clean quotes from fields
            clean_fields = [field.strip('"') for field in fields]

            print(f"DEBUG: Parsing trade line: {clean_fields[:5]}...")  # Show first 5 fields

            return {
                'trade_date': clean_fields[0],
                'entry_order_number': clean_fields[1],
                'entry_buy_sell': clean_fields[2],
                'entry_time': clean_fields[3],
                'entry_price': float(clean_fields[4]),
                'exit_order_number': clean_fields[5],
                'exit_buy_sell': clean_fields[6],
                'exit_time': clean_fields[7],
                'exit_price': float(clean_fields[8]),
                'trade_life_span': float(clean_fields[9]),
                'fill_size': int(clean_fields[10]),
                'trade_pnl': float(clean_fields[11]),
                'commission_fees': float(clean_fields[12]),
                'net_pnl': float(clean_fields[13])
            }
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error parsing trade line: {e}")
            print(f"DEBUG: Fields were: {fields}")
            return None

    def _create_summary_dataframe(self, contracts_data: Dict) -> pd.DataFrame:
        """Create summary DataFrame that matches your dashboard's expected format."""
        trade_rows = []

        print(f"DEBUG: Processing {len(contracts_data)} contracts")

        for contract, data in contracts_data.items():
            trades = data['trades']
            print(f"DEBUG: Contract {contract} has {len(trades)} trades")

            # Group trades by entry order number (scale in/out positions)
            grouped_trades = self._group_scale_trades(trades)

            # Create individual trade rows (matching your dashboard format)
            for grouped_trade in grouped_trades:
                print(f"DEBUG: Processing grouped trade: {grouped_trade}")

                # Add error handling for datetime parsing
                try:
                    trade_rows.append({
                        'contract': contract,
                        'entry_time': grouped_trade['entry_time'],
                        'exit_time': grouped_trade['exit_time'],
                        'duration': grouped_trade['duration'],
                        'entry_price': grouped_trade['avg_entry_price'],
                        'exit_price': grouped_trade['avg_exit_price'],
                        'quantity': grouped_trade['total_quantity'],
                        'pnl': grouped_trade['total_pnl'],
                        'direction': grouped_trade['direction'],
                        'num_exits': grouped_trade['num_exits']  # Track how many partial exits
                    })
                except Exception as e:
                    print(f"DEBUG: Error processing grouped trade: {e}")
                    continue

        print(f"DEBUG: Created {len(trade_rows)} trade rows")
        return pd.DataFrame(trade_rows)

    def _group_scale_trades(self, trades: List[Dict]) -> List[Dict]:
        """Group trades that are part of the same position (same entry order number)."""
        if not trades:
            return []

        # Group by entry order number
        grouped = {}
        for trade in trades:
            entry_order = trade['entry_order_number']
            if entry_order not in grouped:
                grouped[entry_order] = []
            grouped[entry_order].append(trade)

        # Convert each group into a single aggregated trade
        result = []
        for entry_order, trade_group in grouped.items():
            if not trade_group:
                continue

            # Sort by exit time to get proper entry/exit times
            trade_group.sort(key=lambda x: x['exit_time'])

            first_trade = trade_group[0]
            last_trade = trade_group[-1]

            # Calculate weighted averages and totals
            total_quantity = sum(t['fill_size'] for t in trade_group)
            total_pnl = sum(t['trade_pnl'] for t in trade_group)

            # Calculate weighted average prices
            total_entry_value = sum(t['entry_price'] * t['fill_size'] for t in trade_group)
            total_exit_value = sum(t['exit_price'] * t['fill_size'] for t in trade_group)
            avg_entry_price = total_entry_value / total_quantity if total_quantity > 0 else 0
            avg_exit_price = total_exit_value / total_quantity if total_quantity > 0 else 0

            # Duration from first entry to last exit
            try:
                entry_time = pd.to_datetime(first_trade['entry_time'])
                exit_time = pd.to_datetime(last_trade['exit_time'])
                duration = exit_time - entry_time
            except Exception:
                entry_time = first_trade['entry_time']
                exit_time = last_trade['exit_time']
                duration = pd.Timedelta(seconds=last_trade['trade_life_span'])

            result.append({
                'entry_time': entry_time,
                'exit_time': exit_time,
                'duration': duration,
                'avg_entry_price': avg_entry_price,
                'avg_exit_price': avg_exit_price,
                'total_quantity': total_quantity,
                'total_pnl': total_pnl,
                'direction': 'Long' if first_trade['entry_buy_sell'] == 'B' else 'Short',
                'num_exits': len(trade_group),  # How many partial exits
                'entry_order_number': entry_order
            })

        return result

    # Keep your existing methods for other formats
    def process_raw_data(self, df):
        """Process raw Excel data format."""
        df['datetime'] = pd.to_datetime(
            (df['date'] + ' ' + df['time']).str.strip(),
            format='%d%b%y %H:%M:%S.%f',
            dayfirst=True
        )
        return df.sort_values('datetime').reset_index(drop=True)

    def calculate_trades(self, df):
        """Calculate trades from processed Excel data."""
        trades = []
        open_positions = {}

        for _, row in df.iterrows():
            full_contract = row['contract']
            base_contract = full_contract.split()[0]
            action = row['B/S']
            size = row['Size']
            price = row['Price']
            timestamp = row['datetime']

            if base_contract not in open_positions:
                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }

            prev_position = open_positions[base_contract]['position']
            new_position = prev_position + (size if action == 'B' else -size)

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

                try:
                    specs = self.contract_manager.load_contracts()[base_contract]
                    price_diff = (price - entry_price) if entry_action == 'B' else (entry_price - price)
                    ticks = price_diff / specs['tick_size']
                    pnl = ticks * specs['tick_value'] * abs(prev_position)
                except KeyError:
                    print(f"Warning: Contract {base_contract} not found in contracts")
                    pnl = 0

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

                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }
            else:
                open_positions[base_contract]['position'] = new_position

        return pd.DataFrame(trades)
        return any(re.match(pattern, clean_field) for pattern in patterns)

    def _parse_contract_summary(self, fields: List[str]) -> Dict:
        """Parse contract summary line."""
        try:
            return {
                'contract': fields[0],
                'trade_pnl': float(fields[1]) if fields[1] else 0,
                'commission_fees': float(fields[2]) if fields[2] else 0,
                'net_pnl': float(fields[3]) if fields[3] else 0,
                'trade_count': int(fields[4]) if fields[4] else 0,
                'winning_trades': int(fields[5]) if fields[5] else 0,
                'losing_trades': int(fields[6]) if fields[6] else 0,
                'win_percent': float(fields[7]) if fields[7] else 0,
                'lose_percent': float(fields[8]) if fields[8] else 0
            }
        except (ValueError, IndexError):
            return {'contract': fields[0], 'trade_pnl': 0, 'commission_fees': 0}

    def _parse_trade_line(self, fields: List[str]) -> Optional[Dict]:
        """Parse individual trade line."""
        if len(fields) < 14:
            print(f"DEBUG: Trade line too short: {len(fields)} fields, expected 14")
            return None

        try:
            # Clean quotes from fields
            clean_fields = [field.strip('"') for field in fields]

            print(f"DEBUG: Parsing trade line: {clean_fields[:5]}...")  # Show first 5 fields

            return {
                'trade_date': clean_fields[0],
                'entry_order_number': clean_fields[1],
                'entry_buy_sell': clean_fields[2],
                'entry_time': clean_fields[3],
                'entry_price': float(clean_fields[4]),
                'exit_order_number': clean_fields[5],
                'exit_buy_sell': clean_fields[6],
                'exit_time': clean_fields[7],
                'exit_price': float(clean_fields[8]),
                'trade_life_span': float(clean_fields[9]),
                'fill_size': int(clean_fields[10]),
                'trade_pnl': float(clean_fields[11]),
                'commission_fees': float(clean_fields[12]),
                'net_pnl': float(clean_fields[13])
            }
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error parsing trade line: {e}")
            print(f"DEBUG: Fields were: {fields}")
            return None

    def _create_summary_dataframe(self, contracts_data: Dict) -> pd.DataFrame:
        """Create summary DataFrame that matches your dashboard's expected format."""
        trade_rows = []

        print(f"DEBUG: Processing {len(contracts_data)} contracts")

        for contract, data in contracts_data.items():
            trades = data['trades']
            print(f"DEBUG: Contract {contract} has {len(trades)} trades")

            # Group trades by entry order number (scale in/out positions)
            grouped_trades = self._group_scale_trades(trades)

            # Create individual trade rows (matching your dashboard format)
            for grouped_trade in grouped_trades:
                print(f"DEBUG: Processing grouped trade: {grouped_trade}")

                # Add error handling for datetime parsing
                try:
                    trade_rows.append({
                        'contract': contract,
                        'entry_time': grouped_trade['entry_time'],
                        'exit_time': grouped_trade['exit_time'],
                        'duration': grouped_trade['duration'],
                        'entry_price': grouped_trade['avg_entry_price'],
                        'exit_price': grouped_trade['avg_exit_price'],
                        'quantity': grouped_trade['total_quantity'],
                        'pnl': grouped_trade['total_pnl'],
                        'direction': grouped_trade['direction'],
                        'num_exits': grouped_trade['num_exits']  # Track how many partial exits
                    })
                except Exception as e:
                    print(f"DEBUG: Error processing grouped trade: {e}")
                    continue

        print(f"DEBUG: Created {len(trade_rows)} trade rows")
        return pd.DataFrame(trade_rows)

    def _group_scale_trades(self, trades: List[Dict]) -> List[Dict]:
        """Group trades that are part of the same position (same entry order number)."""
        if not trades:
            return []

        # Group by entry order number
        grouped = {}
        for trade in trades:
            entry_order = trade['entry_order_number']
            if entry_order not in grouped:
                grouped[entry_order] = []
            grouped[entry_order].append(trade)

        # Convert each group into a single aggregated trade
        result = []
        for entry_order, trade_group in grouped.items():
            if not trade_group:
                continue

            # Sort by exit time to get proper entry/exit times
            trade_group.sort(key=lambda x: x['exit_time'])

            first_trade = trade_group[0]
            last_trade = trade_group[-1]

            # Calculate weighted averages and totals
            total_quantity = sum(t['fill_size'] for t in trade_group)
            total_pnl = sum(t['trade_pnl'] for t in trade_group)

            # Calculate weighted average prices
            total_entry_value = sum(t['entry_price'] * t['fill_size'] for t in trade_group)
            total_exit_value = sum(t['exit_price'] * t['fill_size'] for t in trade_group)
            avg_entry_price = total_entry_value / total_quantity if total_quantity > 0 else 0
            avg_exit_price = total_exit_value / total_quantity if total_quantity > 0 else 0

            # Duration from first entry to last exit
            try:
                entry_time = pd.to_datetime(first_trade['entry_time'])
                exit_time = pd.to_datetime(last_trade['exit_time'])
                duration = exit_time - entry_time
            except Exception:
                entry_time = first_trade['entry_time']
                exit_time = last_trade['exit_time']
                duration = pd.Timedelta(seconds=last_trade['trade_life_span'])

            result.append({
                'entry_time': entry_time,
                'exit_time': exit_time,
                'duration': duration,
                'avg_entry_price': avg_entry_price,
                'avg_exit_price': avg_exit_price,
                'total_quantity': total_quantity,
                'total_pnl': total_pnl,
                'direction': 'Long' if first_trade['entry_buy_sell'] == 'B' else 'Short',
                'num_exits': len(trade_group),  # How many partial exits
                'entry_order_number': entry_order
            })

        return result

    # Keep your existing methods for other formats
    def process_raw_data(self, df):
        """Process raw Excel data format."""
        df['datetime'] = pd.to_datetime(
            (df['date'] + ' ' + df['time']).str.strip(),
            format='%d%b%y %H:%M:%S.%f',
            dayfirst=True
        )
        return df.sort_values('datetime').reset_index(drop=True)

    def calculate_trades(self, df):
        """Calculate trades from processed Excel data."""
        trades = []
        open_positions = {}

        for _, row in df.iterrows():
            full_contract = row['contract']
            base_contract = full_contract.split()[0]
            action = row['B/S']
            size = row['Size']
            price = row['Price']
            timestamp = row['datetime']

            if base_contract not in open_positions:
                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }

            prev_position = open_positions[base_contract]['position']
            new_position = prev_position + (size if action == 'B' else -size)

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

                try:
                    specs = self.contract_manager.load_contracts()[base_contract]
                    price_diff = (price - entry_price) if entry_action == 'B' else (entry_price - price)
                    ticks = price_diff / specs['tick_size']
                    pnl = ticks * specs['tick_value'] * abs(prev_position)
                except KeyError:
                    print(f"Warning: Contract {base_contract} not found in contracts")
                    pnl = 0

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

                open_positions[base_contract] = {
                    'position': 0,
                    'entry_price': None,
                    'entry_time': None,
                    'entry_action': None
                }
            else:
                open_positions[base_contract]['position'] = new_position

        return pd.DataFrame(trades)
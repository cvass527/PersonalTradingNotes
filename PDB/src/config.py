import os

# Configuration
DATA_DIR = 'trading_data'
NOTES_FILE = 'trading_notes.json'
CONTRACTS_FILE = 'contracts.json'
os.makedirs(DATA_DIR, exist_ok=True)

# Default contracts configuration
DEFAULT_CONTRACTS = {
    'ES': {'tick_value': 12.50, 'tick_size': 0.25},
    'GC': {'tick_value': 10.00, 'tick_size': 0.10}
} 
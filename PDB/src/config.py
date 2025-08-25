import os

# Configuration - Set paths relative to the src directory
SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # src directory
PDB_DIR = os.path.dirname(SRC_DIR)  # PDB directory
DATA_DIR = os.path.join(SRC_DIR, 'trading_data')
NOTES_FILE = os.path.join(PDB_DIR, 'trading_notes.json')
CONTRACTS_FILE = os.path.join(PDB_DIR, 'contracts.json')
os.makedirs(DATA_DIR, exist_ok=True)

# Default contracts configuration
DEFAULT_CONTRACTS = {
    'ES': {'tick_value': 12.50, 'tick_size': 0.25},
    'GC': {'tick_value': 10.00, 'tick_size': 0.10}
} 
import json
import os
from config import CONTRACTS_FILE, DEFAULT_CONTRACTS

class ContractManager:
    def load_contracts(self):
        if os.path.exists(CONTRACTS_FILE):
            with open(CONTRACTS_FILE, 'r') as f:
                return json.load(f)
        
        with open(CONTRACTS_FILE, 'w') as f:
            json.dump(DEFAULT_CONTRACTS, f)
        return DEFAULT_CONTRACTS
    
    def save_contract(self, name, tick_value, tick_size):
        contracts = self.load_contracts()
        contracts[name] = {
            'tick_value': float(tick_value),
            'tick_size': float(tick_size)
        }
        with open(CONTRACTS_FILE, 'w') as f:
            json.dump(contracts, f)
        return contracts 
import pandas as pd
class TradeDate:
    def __init__(self, date):
        self.date = date
        self.contracts = {}  # {contract: [AggregatedTrade, ...]}

    def add_trade(self, contract, trade):
        if contract not in self.contracts:
            self.contracts[contract] = []
        self.contracts[contract].append(trade)

    def get_trades(self, contract):
        return self.contracts.get(contract, [])


    def trades_to_dataframe(self):
        trade_dicts = []
        for contract, trades in self.contracts.items():
            for trade in trades:
                trade_data = trade.to_dict()
                trade_data['contract'] = contract  # Inject contract info into dict
                trade_dicts.append(trade_data)
        return pd.DataFrame(trade_dicts)

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

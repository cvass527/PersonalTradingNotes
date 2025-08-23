class AggregatedTrade:
    def __init__(self, entry_order_number, commission_fees, trade_pnl, fill_size):
        self.entry_order_number = entry_order_number
        self.commission_fees = commission_fees
        self.trade_pnl = trade_pnl
        self.fill_size = fill_size

    def __repr__(self):
        return (f"AggregatedTrade(order={self.entry_order_number}, "
                f"fees={self.commission_fees}, pnl={self.trade_pnl}, fills={self.fill_size})")

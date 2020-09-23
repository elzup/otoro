from services.slackcli import error_notice, start_notice
from trade_controller import TradeController


def main():
    tc = TradeController('TRBUSDT', 'USDT', 'TRB', 1, 2, 300, 20, 'binance')
    # tc = TradeController('TRXUSDT', 'USDT', 'TRX', 0, 2, 60, 0.004, 'binance')
    tc.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_notice(str(e))
        raise e

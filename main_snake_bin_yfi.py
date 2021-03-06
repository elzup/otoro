from services.slackcli import error_notice, start_notice
from trade_controller import TradeController


def main():
    tc = TradeController('YFIUSDT', 'USDT', 'YFI', 3,
                         leverage=2, size_candle=300, snake_size=9000, market='binance')
    tc.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_notice(str(e))
        raise e

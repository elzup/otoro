from services.slackcli import error_notice, start_notice
from trade_controller import TradeController
from config import config as tconf

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--target", type=str, help="target name")
parser.add_argument("-p", "--precision", type=int, default=0, help="precision")
parser.add_argument("-s", "--snake-size", type=float, help="snake size")
parser.add_argument("-c", "--candle", type=int, help="candle size",
                    default=tconf.size_candle)

args = parser.parse_args()

candle = args.candle
# candle = tconf.size_candle
target = args.target
assert(target)
snake_size = args.snake_size
assert(snake_size)
precision = args.precision
print(target, snake_size, precision)

candle = args.candle


def main():
    tc = TradeController(target.upper() + 'USDT', 'USDT', target.upper(), precision,
                         leverage=2, size_candle=candle, snake_size=snake_size, market='binance')
    tc.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_notice(str(e))
        raise e

import os

product_code = "BTC_JPY"    # currency pair (BTC_JPY,)
logic = "NO_CUT"            # Judge Logic of Entry and Close(NO_CUT, )
sleep_time = 60 * 5             # waiting time to get data(1=1sec)
check_sleep_time = 20       # waiting time to check status
check_count = 10           # the number of check trial
discord_webhook_url = ''


def getenv(key, defo):
    return os.environ[key] if key in os.environ else defo


cycle_debug = getenv("CYCLE_DEBUG", False)
if cycle_debug:
    sleep_time = 5
log = True
plot = getenv("PLOT", False)
plotshow = getenv("PLOT_SHOW", False)
logic_print = getenv("LOGIC_PRINT", True)

# x1.5 / 6 month
# size_candle = 60 * 60 * 1
# cbs_size = 10 * 4

# channel breakout
# x1
size_candle = 60 * 5
h = int(60 * 60 / size_candle)
cbs_size = 39 * h

order_leverage = 1.5

cbs_fx_size = 56 * h
cbs_fx_close_margin = 0.3

# snake
snake_limit_count = 12 * 60
snake_load_size = 12 * 60

snake_size = 30000
snake_close_margin = 0.3
snake_entry_margin = 0.3
snake_entry_min = 0
# snake_size = 15000
# snake_close_margin = 0.2

backtest_range = 100000
backtest_season = 3  # 0, 1, 2 ...
backtest_bgn = backtest_range * backtest_season
backtest_end = backtest_bgn + backtest_range

buy_judge_limit = 2
buy_sleep_time = 20
buy_count = 3
sell_sleep_time = 20
sell_count = 5
close_sleep_time = 10
close_count = 10

sell_rate = 1.008
close_rate = 0.8

get_board_time = 10
get_board_count = 6

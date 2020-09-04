from load_data import keys as conf
from coinapi_rest_v1 import CoinAPIv1

test_key = conf.coin_api_key
api = CoinAPIv1(test_key)
symbols = api.metadata_list_symbols()
print('Symbols')
for symbol in symbols:
    if "BITFLYER" in symbol['symbol_id'] or "COINCHECK" in symbol['symbol_id']:
        print('Symbol ID: %s' % symbol['symbol_id'])

from config import Apikey as conf
from load_data.coinapi_rest_v1 import CoinAPIv1

test_key = conf.coin_api_key
api = CoinAPIv1(test_key)
symbols = api.metadata_list_symbols()
print('Symbols')
for symbol in symbols:
    if(symbol['exchange_id'] == "COINCHECK"):
        print('Symbol ID: %s' % symbol['symbol_id'])

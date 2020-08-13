
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm

output_file_name = "./data/btcjpn_2015_2020_5m_cc.csv"


def parse_csv_line(line):
    return list(map(float, line.split(",")))


def get_local_data():
    f = open(output_file_name)
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    # print(len(list(csvarr)))
    return np.array(csvarr)


res = get_local_data()

x = np.array(list(map(lambda v: pd.to_datetime(v[0], unit="s"), res[-10000:])))
btc = np.array(list(map(lambda v: v[4], res[-10000:])))
hi = np.array(list(map(lambda v: v[2], res[-10000:])))
lo = np.array(list(map(lambda v: v[3], res[-10000:])))

df = pd.DataFrame({'i': x, 'btc': btc, 'hi': hi, 'lo': lo})
# df2 = pd.DataFrame(index=x, data=dict(v=v2))

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

ax.plot('i', 'btc', data=df, color=cm.Set1.colors[0])
ax2 = ax.twinx()
ax2.plot('i', 'hi', data=df, color=cm.Set1.colors[1])
ax2.plot('i', 'lo', data=df, color=cm.Set1.colors[2])
plt.show()


plt.close()

# time.sleep(1)

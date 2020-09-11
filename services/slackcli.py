import slackweb
from services import keys as conf

client = slackweb.Slack(url=conf.slack_webhook_url)


def buy_notice(price, amount):
    if not conf.slack_webhook_url: return
    client.notify(title="BTC buy event",
                  text=f"BUY  :yen: ¥{price * amount} => :bitcoin: *{amount}* BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def sell_notice(price, amount):
    if not conf.slack_webhook_url: return
    client.notify(title="BTC sell event",
                  text=f"SELL :yen: *¥{price * amount}* <= :bitcoin: {amount} BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def short_entry_notice(price, amount):
    if not conf.slack_webhook_url: return
    client.notify(title="BTC short event",
                  text=f"SHORT :arrow_lower_right: {price:,} :yen: *¥{price * amount:,.0f}* => :bitcoin: {amount:8f} BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def long_entry_notice(price, amount):
    if not conf.slack_webhook_url: return
    client.notify(title="BTC long event",
                  text=f"LONG_ :arrow_upper_right: {price:,} :yen: *¥{price * amount:,.0f}* => :bitcoin: {amount:8f} BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def close_notice(price, amount):
    if not conf.slack_webhook_url: return
    client.notify(title="BTC close event",
                  text=f"CLOSE :end: {price:,} :yen: *¥{price * amount:,.1f}* <= :bitcoin: {amount:8f} BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def start_notice():
    if not conf.slack_webhook_url: return
    client.notify(title="Bot Running",
                  text="Bot Running",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


if __name__ == "__main__":
    client.notify(title="BTC buy event",
                  text=":yen: ¥100000 => :bitcoin: 0.3313312 BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")

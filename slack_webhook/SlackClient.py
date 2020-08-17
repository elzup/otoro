import slackweb
from slack_webhook import Apikey as conf

client = slackweb.Slack(url=conf.slack_webhook_url)


def buy_notice(price, amount):
    if not conf.slack_webhook_url:
        return
    client.notify(title="BTC buy event",
                  text=f"BUY  :yen: ¥{price * amount} => :bitcoin: *{amount}* BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def sell_notice(price, amount):
    if not conf.slack_webhook_url:
        return
    client.notify(title="BTC sell event",
                  text=f"SELL :yen: *¥{price * amount}* <= :bitcoin: {amount} BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


def start_notice():
    if not conf.slack_webhook_url:
        return
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

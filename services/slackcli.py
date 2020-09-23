from typing import Callable
import slackweb
from services import keys as conf

client = slackweb.Slack(url=conf.slack_webhook_url)


class SlackNoticeClient:
    def __init__(self, cur_symbol: str, tar_symbol: str):
        self.cur_symbol = cur_symbol
        self.tar_symbol = tar_symbol
        self.notify: Callable[[str], None] = lambda _text: None
        if conf.slack_webhook_url:
            self.notify = lambda text: client.notify(
                text=text,
                icon_emoji=f":{tar_symbol}",
                mrkdwn=True,
                username="otoro {cur_sybmol}{tar_symbol}"
            )

    def short_entry_notice(self, price, amount, cur):
        self.notify(self.trade_message(price, amount, cur, ":short:", "=>"))

    def long_entry_notice(self, price, amount, cur):
        self.notify(self.trade_message(price, amount, cur, ":long:", "=>"))

    def close_notice(self, price, amount, cur):
        self.notify(self.trade_message(price, amount, cur, ":close:", "<="))

    def trade_message(self, price, amount, cur, icon, arrow):
        return f"{icon} {price:,} :{self.cur_symbol}:/:{self.tar_symbol}: {self.cur_symbol.upper()} *¥{cur:,}* {arrow} {amount:,} {self.tar_symbol.upper()}"

    def start_notice(self):
        self.notify("Bot Running")

    def error_notice(self, text):
        self.notify(f"Error: <!here> {text}")


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
    client.notify(text=f"TEST :long: {price:,} :yen: *¥{price * amount:,.0f}* => :bitcoin: {amount:8f} BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro test")


def close_notice(price, amount):
    if not conf.slack_webhook_url: return
    client.notify(title="BTC close event",
                  text=f"CLOSE :end: {price:,} :yen: *¥{price * amount:,.0f}* <= :bitcoin: {amount:8f} BTC",
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


def error_notice(text):
    if not conf.slack_webhook_url: return
    client.notify(title="Error",
                  text=f"Error: @here {text}",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")


if __name__ == "__main__":
    client.notify(title="BTC buy event",
                  text=":yen: ¥100000 => :bitcoin: 0.3313312 BTC",
                  icon_emoji=":bitcoin",
                  mrkdwn=True,
                  username="otoro")

"""
Currency exchange rates Telegram Bot.
Author: Yurii Tereshchenko
"""

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import json
from datetime import datetime, timedelta
import sqlite3
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


TOKEN = "1234567890:AbcdEFghIJklMNopqRStuVwxYZ"


def send_plot(exchange_rates):
    dict_ = exchange_rates["rates"]
    date_value_list = []
    obj_ = ""
    for date, obj in dict_.items():
        date_value = (datetime.strptime(date, "%Y-%m-%d"), obj[list(obj.keys())[0]])
        date_value_list.append(date_value)
        obj_ = obj
    ax = plt.gca()
    date_value_list = sorted(
        date_value_list,
        key=lambda x: x[0],
        reverse=False
    )
    month_day_fmt = mdates.DateFormatter('%d %B')
    ax.xaxis.set_major_formatter(month_day_fmt)
    if len(date_value_list) > 20:
        plt.xticks([])
    else:
        plt.setp(ax.get_xticklabels(), rotation=90, horizontalalignment='right')
        ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(*zip(*date_value_list))
    plt.title(f"Exchange rates %s/%s" %(exchange_rates["base"], list(obj_.keys())[0]))
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.5)
    plt.clf()
    buf.seek(0)
    return buf


def exchange(sell_quantity, sell, buy, rates):
    dict_ = rates["rates"]
    if sell == "USD":
        sell_rate = 1
    else:
        sell_rate = dict_.get(sell, default=None)
    if buy == "USD":
        buy_rate = 1
    else:
        buy_rate = dict_.get(buy, None)
    if sell_rate is None or buy_rate is None:
        return None
    buy_quantity = float(buy_rate) * sell_quantity / float(sell_rate)
    return buy_quantity


def get_rates():
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    now = datetime.timestamp(datetime.now())
    sql = """
        SELECT *
        FROM    rates
        WHERE   ID = (SELECT MAX(ID) FROM rates);
    """
    c.execute(sql)
    conn.commit()
    row = c.fetchone()
    last_id = 1
    loaded_from_database = False
    if row is not None:
        timestamp = row[1]
        last_id = row[0]
        if now - timestamp <= 600:
            exchange_rates = json.loads(row[2])
            loaded_from_database = True
        else:
            exchange_rates = request_exchange_rates()
    else:
        exchange_rates = request_exchange_rates()
    if exchange_rates == "Error":
        c.close()
        conn.close()
        return exchange_rates
    else:
        if not loaded_from_database:
            dumped_json = json.dumps(exchange_rates)
            sql = """ INSERT into rates(ID, timestamp_, rates)
                values(%d, %d, %s)
            """ % (last_id + 1, now, "'" + dumped_json + "'")
            c.execute(sql)
            conn.commit()
    c.close()
    conn.close()
    return exchange_rates


def request_exchange_rates(args=None):
    if args is not None:
        base = args[0]
        symbol = args[1]
        days = int(args[2])
        today = datetime.now().strftime("%Y-%m-%d")

        x_days_ago = datetime.now() - timedelta(days=days)
        x_days_ago = x_days_ago.strftime("%Y-%m-%d")

        request_str = f"https://api.exchangeratesapi.io/history?start_at=%s&end_at=%s&base=%s&symbols=%s" %(x_days_ago, today, base, symbol)
        response = requests.get(request_str)
    else:
        response = requests.get("https://api.exchangeratesapi.io/latest?base=USD")

    if response.status_code == 200:
        response_json = response.json()
        return response_json
    else:
        return "Error"


def error(update, context):
    answer = """/list or /lst: shows current exchange rates based on USD
/exchange 10$ to RUB: converts 10 USD to RUB
/exchange 10 USD to RUB: another format
/history USD/RUB for 7 days: shows a graph of USD to RUB for last 7 days    
    """
    update.message.reply_text(answer)


def start(update: Update, context: CallbackContext) -> None:
    answer = """Welcome to the exchange rates bot!
    
How you can use it:
/list or /lst: shows current exchange rates based on USD
/exchange 10$ to RUB: converts 10 USD to RUB
/exchange 10 USD to RUB: another format
/history USD/RUB for 7 days: shows a graph of USD to RUB for last 7 days
"""
    update.message.reply_text(answer)


def lst(update: Update, context: CallbackContext) -> None:
    answer = ""
    exchange_rates = get_rates()
    if exchange_rates is None:
        update.message.reply_text("Sorry, an error occurred.")
        return
    dict_ = exchange_rates["rates"]
    for key, value in dict_.items():
        answer += ("%s     %.2f\n" % (key, value))
    update.message.reply_text(answer)


def exchange_(update: Update, context: CallbackContext) -> None:
    args = context.args
    exchange_rates = get_rates()

    if '$' in args[0]:
        sell_quantity = args[0].replace('$', '')
        sell_quantity = float(sell_quantity)
        sell = "USD"
        buy = args[2]
        buy_quantity = exchange(sell_quantity, sell, buy, exchange_rates)
    else:
        sell_quantity = float(args[0])
        sell = args[1]
        buy = args[3]
        buy_quantity = exchange(sell_quantity, sell, buy, exchange_rates)
    if buy_quantity is None:
        update.message.reply_text("No exchange rate data is available for the selected currency")
        return
    answer = f"%.2f%s = %.2f%s" % (sell_quantity, sell, buy_quantity, buy)
    update.message.reply_text(answer)


def history(update: Update, context: CallbackContext) -> None:
    args = context.args
    currencies = args[0].split('/')
    base = currencies[0]
    symbol = currencies[1]
    if args[1] != "for" or args[3] != "days":
        answer = "Input format is following:\n/history USD/CAD for 7 days"
        update.message.reply_text(answer)
        return
    days = int(args[2])
    exchange_rates = request_exchange_rates((base, symbol, days))
    if exchange_rates == "Error":
        update.message.reply_text("Sorry, an error occurred.")
        return
    stream_buffer = send_plot(exchange_rates)
    update.message.reply_photo(stream_buffer)
    stream_buffer.close()


if __name__ == '__main__':
    conn = sqlite3.connect("requests.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS rates(
        ID INTEGER NOT NULL PRIMARY KEY,
        timestamp_ timestamp,
        rates TEXT);
    """)
    conn.commit()
    c.close()
    conn.close()
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", start))
    updater.dispatcher.add_handler(CommandHandler("list", lst))
    updater.dispatcher.add_handler(CommandHandler("lst", lst))
    updater.dispatcher.add_handler(CommandHandler("exchange", exchange_))
    updater.dispatcher.add_handler(CommandHandler("history", history))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

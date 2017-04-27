
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
#from matplotlib.finance import candlestick2_ochl
#from matplotlib.finance import candlestick2
from matplotlib.finance import candlestick2_ohlc

import datetime

class Plotter(object):
    def __init__(self, table, session):
        self.table = table
        self.session = session

        
    def plot(self, ticker):
        
        results = self.session.query(self.table) \
                              .filter(self.table.ticker == ticker) \
                              .order_by(self.table.date, self.table.time) \
                              .limit(100)

        fig, ax = plt.subplots()
        fig.set_size_inches(8, 6)
        # fig.subplots_adjust(bottom=0.2)
        # ax.xaxis.set_major_locator(mondays)
        # ax.xaxis.set_minor_locator(alldays)
        # ax.xaxis.set_major_formatter(weekFormatter)
        # ax.xaxis.set_minor_formatter(dayFormatter)

        #plot_day_summary(ax, quotes, ticksize=3)
        opens = []
        closes = []
        highs = []
        lows = []
        dates = []
        for item in results:
            date = item.date
            time = item.time
            date_time_str = date + " " + time
            d = datetime.datetime.strptime(date_time_str, "%y%m%d %H:%M")
            
            dates.append(d)
            opens.append(item.open)
            closes.append(item.close)
            highs.append(item.high)
            lows.append(item.low)

        # print "open = {0}".format('-'.join([str(x) for x in opens]))
        # print "close = {0}".format('-'.join([str(x) for x in closes]))
        # print "high = {0}".format('-'.join([str(x) for x in highs]))
        # print "low = {0}".format('-'.join([str(x) for x in lows]))
        candlestick2_ohlc(ax, opens, highs, lows, closes,
                          colorup='g', colordown='r', width=1.0)
        # candlestick2_ochl(ax,
        #                   opens=opens, closes=closes, highs=highs, lows=lows,
        #                   width=0.4,
        #                   colorup='g', colordown='r', alpha=0.75)
        # candlestick2(ax,
        #              opens, closes, highs, lows,
        #              width=.75, colorup='g', colordown='r', alpha=0.75)

        # ax.xaxis_date()
        ax.autoscale_view()
        plt.setp(plt.gca().get_xticklabels(),
                 rotation=45, horizontalalignment='right')
        plt.savefig("plot-{0}-{1}.png".format(self.table.__tablename__, ticker))
        plt.show()


from sqlalchemy import Column, ForeignKey, Integer, Text, Float
from sqlalchemy import func

from indicator import IIndicator
from common.sqlmodels.sql_model_base import Base

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc

from itertools import izip

class IndicatorHeikinAshi(IIndicator):
    def __init__(self, table, destination_table):
        super(IndicatorHeikinAshi, self).__init__("HeikinAshi",
                                                  HeikinAshi.__tablename__,
                                                  table,
                                                  destination_table)


    def testPerformance3(self, session, ticker):
        from sklearn.linear_model import SGDClassifier
        items = session.query(self.destination_table) \
                       .filter(self.destination_table.ticker == ticker) \
                       .order_by(self.destination_table.date, self.destination_table.time)
        items = list(items)

        real_items = session.query(self.table) \
                       .filter(self.table.ticker == ticker) \
                       .order_by(self.table.date, self.table.time)
        real_items = list(real_items)

        previous_items = []
        nb_previous_items = 4
        previous_real_item = None
        datasetX = []
        datasetY = []
        first = True
        for item, real_item  in izip(items, real_items):
            if len(previous_items) == nb_previous_items:

                tmp = []
                for previous_item in previous_items:
                    tmp.extend([previous_item.low,
                                previous_item.high,
                                previous_item.open,
                                previous_item.close])
                datasetX.append(tmp)
                datasetY.append(1.0 if real_item.close > previous_real_item.close else 0.0) # If the price goes up 1.0,
                
                previous_items.pop(0)
            previous_items.append(item)
            previous_real_item = real_item

        print "Running classifier"
        clf = SGDClassifier(loss="hinge", penalty="l2", shuffle=True)
        clf.fit(datasetX, datasetY)
        
        previous_items = []
        previous_real_item = None
        success = 0.0
        failure = 0.0
        nb_tick = 0.0
        for item, real_item  in izip(items, real_items):
            if len(previous_items) == nb_previous_items:

                tmp = []
                for previous_item in previous_items:
                    tmp.extend([previous_item.low,
                                previous_item.high,
                                previous_item.open,
                                previous_item.close])
                prediction = clf.predict(tmp)[0]
                real_answer = 1.0 if real_item.close > previous_real_item.close else 0.0 # If the price goes up 1.0,
                if prediction == real_answer:
                    success += 1.0
                else:
                    failure += 1.0

                previous_items.pop(0)

            nb_tick += 1.0
            previous_real_item = real_item                    
            previous_items.append(item)

        print "{0}\tSuccess: {1:<10} Failure: {2:<10} Success rate: {3:.3%} Failure rate: {4:.3%}".format(ticker, success, failure, (success / nb_tick), (failure / nb_tick))
        
        
        
    def testPerformance2(self, session, ticker):
        items = session.query(self.destination_table) \
                       .filter(self.destination_table.ticker == ticker) \
                       .order_by(self.destination_table.date, self.destination_table.time)

        real_items = session.query(self.table) \
                       .filter(self.table.ticker == ticker) \
                       .order_by(self.table.date, self.table.time)

        
        previous_item = item
        

        amplitude = 0.0
        success = 0.0
        failure = 0.0
        draw = 0.0
        current_state = "short"
        nb_tick = 0.0
        previous_item = None
        for item, real_item  in izip(items, real_items):
            if previous_item is None:
                previous_close = item.close

            if current_state == "long":
                if real_item.close - previous_close > 0:
                    success += 1.0
                elif real_item.close - previous_close  < 0:
                    failure += 1.0
                else:
                    draw += 1.0
                amplitude += real_item.close - previous_close
            elif current_state == "short":
                if real_item.close - previous_close > 0:
                    failure += 1.0
                elif real_item.close - previous_close < 0:
                    success += 1.0
                else:
                    draw += 1.0
                amplitude += -(real_item.close - previous_close)
            nb_tick += 1.0

            if previous_item is not None:
                bearish = item.close - item.open < 0.0
                previous_bearish = previous_item.close - previous_item.open < 0.0
                has_upper_wick = item.high > max(item.close, item.open)
                has_lower_wick = item.low < min(item.close, item.open)
                size_body = abs(item.close - item.open)
                size_upper_wick = 0 if not has_upper_wick else abs(item.high - max(item.close, item.open))
                size_lower_wick = 0 if not has_upper_wick else abs(item.low - min(item.close, item.open))
                if current_state == "long":
                    if bearish and previous_bearish:
                        current_state = "short"
                else:
                    if not bearish and not previous_bearish:
                        current_state = "long"
                if (size_upper_wick + size_lower_wick) / 2.0 > size_body:
                     if current_state == "long":
                         current_state = "short"
                     # else:
                #         current_state = "long"
            previous_item = item
                
            
        print "{0}\tSuccess: {1:<10} Failure: {2:<10} Success rate: {3:.3%} Draw rate: {4:.3%} Failure rate: {5:.3%} Amplitude: {6:<10}".format(ticker, success, failure, (success / nb_tick), (draw / nb_tick), (failure / nb_tick), amplitude)
            

        
    # https://quantiacs.com/Blog/Intro-to-Algorithmic-Trading-with-Heikin-Ashi.aspx
    def testPerformance(self, session, ticker):
        items = session.query(self.destination_table) \
                       .filter(self.destination_table.ticker == ticker) \
                       .order_by(self.destination_table.date, self.destination_table.time)

        real_items = session.query(self.table) \
                       .filter(self.table.ticker == ticker) \
                       .order_by(self.table.date, self.table.time)
        # initial condition we have 10 000 of "money" in short postion because we didn't buy yet
        current_state = "short"
        previous_item = None
        real_money = 10000.0
        action_money = 0.0
        max_volume = None
        min_volume = None
        avg_volume = 0
        nb_volume_turn = 0
        
        success = 0.0
        failure = 0.0
        draw = 0.0 # not a success neither a failure
        nb_tick = 0.0
        amplitude = 0.0
        for item, real_item  in izip(items, real_items):

            # win/fail simulation is before  previous item because
            # we start as short position
            if current_state == "long":
                if real_item.close - real_item.open > 0:
                    success += 1
                elif real_item.close - real_item.open < 0:
                    failure += 1
                else:
                    draw += 1
                amplitude += real_item.close - real_item.open
            elif current_state == "short":
                if real_item.close - real_item.open > 0:
                    failure += 1
                elif real_item.close - real_item.open < 0:
                    success += 1
                else:
                    draw += 1
                amplitude += -(real_item.close - real_item.open)
            nb_tick += 1

            
            if previous_item is not None:
                    
                
                current_fluctuation = item.close - item.open
                current_candle_size = abs(current_fluctuation)
                previous_fluctuation = previous_item.close - previous_item.open
                previous_candle_size = abs(previous_fluctuation)
                if current_fluctuation < 0 and previous_fluctuation < 0 and \
                   current_candle_size > previous_candle_size and \
                   item.high >= max(item.open, item.close) and \
                   real_item.vol > (1.0/3.0 * avg_volume): 
                    current_state = "long"
                    # print "Buy"
                elif current_fluctuation > 0 and previous_fluctuation > 0 and \
                     current_candle_size > previous_candle_size and \
                     item.low <= min(item.open, item.close) and \
                     real_item.vol > (1.0/3.0 * avg_volume):
                    current_state = "short"
                    # print "Sell"
                # else:
                #     print "Nothing"

                long_exit = not (current_fluctuation < 0) and not (previous_fluctuation < 0) and item.low <= min(item.open, item.close)
                short_exit = current_fluctuation < 0 and previous_fluctuation < 0 and item.high >= max(item.open, item.close)
                if current_state == "long" and long_exit:
                    current_state = "short"
                    # print "Exit Long"
                elif current_state == "short" and short_exit:
                    current_state = "long"
                    # print "Exit Short"

            avg_volume = ((avg_volume * nb_volume_turn) + real_item.vol) / (nb_volume_turn + 1)
            nb_volume_turn += 1
            if max_volume is None:
                max_volume = real_item.vol
            max_volume = max(max_volume, real_item.vol)
            if min_volume is None:
                min_volume = real_item.vol
            min_volume = min(min_volume, real_item.vol)
            previous_item = item
            # print "---------------------------------------------------"
        print "{0}\tSuccess: {1:<10} Failure: {2:<10} Success rate: {3:.3%} Draw rate: {4:.3%} Failure rate: {5:.3%} Amplitude: {6:<10}".format(ticker, success, failure, (success / nb_tick), (draw / nb_tick), (failure / nb_tick), amplitude)
            
        
    def run(self, session, ticker):
        print "[*] Running {0} on ticker {1}".format(HeikinAshi.__tablename__,
                                                     ticker)
        items = session.query(self.table) \
                       .filter(self.table.ticker == ticker) \
                       .order_by(self.table.date, self.table.time)

        
        count = 0
        first = True
        for item in items:

            # calculate first candle
            if first:
                HaClose = (item.open + item.high + \
                           item.low + item.close) / 4.0
                HaOpen = (item.open + item.close) / 2.0
                HaHigh = item.high
                HaLow = item.low                
                first = False

            # Calculate all other candles
            else:
                HaClose = (item.open + item.high + \
                           item.low + item.close) / 4.0
                HaOpen = (previous_ha_item.open + previous_item.close) / 2.0
                HaHigh = max(item.high, HaOpen, HaClose)
                HaLow = min(item.low, HaOpen, HaClose)

            previous_item = item
            previous_ha_item = self.destination_table(ticker=item.ticker,
                                                      per=item.per,
                                                      date=item.date,
                                                      time=item.time,
                                                      close=HaClose, open=HaOpen,
                                                      high=HaHigh, low=HaLow)

            session.add(previous_ha_item)
            count += 1

            if count > 10000:
                print "[+] Flushing 10 000 {0} entries".format(self.name)
                session.flush()
                count = 0
        session.flush()
        session.commit()
            
    # def plot(self, session):
        
    #     fig, ax = plt.subplots()
    #     fig.subplots_adjust(bottom=0.2)
    #     # ax.xaxis.set_major_locator(mondays)
    #     # ax.xaxis.set_minor_locator(alldays)
    #     # ax.xaxis.set_major_formatter(weekFormatter)
    #     #ax.xaxis.set_minor_formatter(dayFormatter)

    #     #plot_day_summary(ax, quotes, ticksize=3)
    #     candlestick_ohlc(ax, quotes, width=0.6)

    #     # ax.xaxis_date()
    #     ax.autoscale_view()
    #     plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

    #     plt.show()


class HeikinAshi(Base):
    __tablename__ = "heikinashi"

    id = Column(Integer, primary_key=True)
    ticker = Column(Text, nullable=False)
    per = Column(Text, nullable=False)
    date = Column(Text, nullable=False)
    time = Column(Text, nullable=False)
    open = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)

class HeikinAshiHour(Base):
    __tablename__ = "heikinashi_hour"

    id = Column(Integer, primary_key=True)
    ticker = Column(Text, nullable=False)
    per = Column(Text, nullable=False)
    date = Column(Text, nullable=False)
    time = Column(Text, nullable=False)
    open = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)

class HeikinAshiDay(Base):
    __tablename__ = "heikinashi_day"

    id = Column(Integer, primary_key=True)
    ticker = Column(Text, nullable=False)
    per = Column(Text, nullable=False)
    date = Column(Text, nullable=False)
    time = Column(Text, nullable=False)
    open = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)


class HeikinAshi30Minutes(Base):
    __tablename__ = "heikinashi_30_minutes"

    id = Column(Integer, primary_key=True)
    ticker = Column(Text, nullable=False)
    per = Column(Text, nullable=False)
    date = Column(Text, nullable=False)
    time = Column(Text, nullable=False)
    open = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)


class HeikinAshi10Minutes(Base):
    __tablename__ = "heikinashi_10_minutes"

    id = Column(Integer, primary_key=True)
    ticker = Column(Text, nullable=False)
    per = Column(Text, nullable=False)
    date = Column(Text, nullable=False)
    time = Column(Text, nullable=False)
    open = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)


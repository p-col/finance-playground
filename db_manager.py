
import datetime

from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import distinct
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

from common.sqlmodels.sql_model_base import Base

from common.sqlmodels.action import Action
from common.sqlmodels.action import ActionHour
from common.sqlmodels.action import ActionDay
from common.sqlmodels.action import Action10Minutes
from common.sqlmodels.action import Action30Minutes

from converter.converter import Converter
from common.sqlmodels.action import IsinInformations

from plotter import Plotter

class DBManager(object):
    def __init__(self, uri):
        self.engine = create_engine(uri)
        Base.metadata.bind = self.engine
        self.DBsession = sessionmaker(bind=self.engine)
        self.session = self.DBsession()

    def dropTables(self):
        Action.__table__.drop(checkfirst=True)
        self.session.commit()

    def createAll(self):
        Base.metadata.create_all(self.engine)

    def insertData(self, file_reader):
        i = 0
        for row in file_reader:
            item = Action(ticker=row[Action.ticker.name],
                          per=row[Action.per.name],
                          date=row[Action.date.name],
                          time=row[Action.time.name],
                          open=row[Action.open.name],
                          high=row[Action.high.name],
                          low=row[Action.low.name],
                          close=row[Action.close.name],
                          vol=row[Action.vol.name])
            self.session.add(item)
            i += 1
            if i % 100000 == 0:
                self.session.flush()
                print "[*] inserted {0} items".format(i)
        self.session.commit()
        print "[+] done"

    def updateISINInformations(self, isin, data):

        import pprint
        pprint.pprint(data)
        # if no result for aparticular isin
        if "error" in data.keys():
            return
        if "data" not in data.keys():
            print "No 'data' key found in data for ising {0}".format(isin)

        for entry in data["data"]:
            info_item = IsinInformations(isin=isin,
                                         compositeFIGI = entry["compositeFIGI"],
                                         exchCode = entry["exchCode"],
                                         figi = entry["figi"],
                                         marketSector = entry["marketSector"],
                                         name = entry["name"],
                                         securityDescription = entry["securityDescription"],
                                         securityType = entry["securityType"],
                                         securityType2 = entry["securityType2"],
                                         shareClassFIGI = entry["shareClassFIGI"],
                                         ticker = entry["ticker"],
                                         uniqueID = entry["uniqueID"],
                                         uniqueIDFutOpt = entry["uniqueIDFutOpt"])
            self.session.add(info_item)
        self.session.flush()
        self.session.commit()

    def getAllUniqueIsin(self):
        # return iterator yielding tuples of size 1
        r = self.session.query(distinct(Action.ticker))
        # return list of all tickers
        return [result[0] for result in r]


    # def buildActionHourTable(self):
    #     tickers = self.session.query(distinct(Action.ticker))
    #     for ticker in tickers:
    #         ticker = ticker[0]
    #         print "[*] Processing ticker {0}".format(ticker)
    #         items = self.session.query(Action) \
    #                             .filter(Action.ticker == ticker) \
    #                             .order_by(Action.date, Action.time)
    #         for item in items:
    #             print 

    def fillHole(self, lastItem, lastDate, nextDate):
        one_minute = datetime.timedelta(0,60) # days, seconds, ...
        current_date = lastDate + one_minute
        while  current_date < nextDate:
            date = current_date.strftime("%y%m%d")
            time = current_date.strftime("%H:%M")
            new_item = Action(ticker=lastItem.ticker,
                              per=lastItem.per,
                              date=date,
                              time=time,
                              open=lastItem.close,
                              high=lastItem.close,
                              low=lastItem.close,
                              close=lastItem.close,
                              vol=0)
            # print "Adding new item at {0}".format(new_item.time)
            current_date += one_minute
            # print "date = {0}".format(date)
            # print "time = {0}".format(time)
            self.session.add(new_item)
            
    
    def fillHoles(self):
        tickers = self.session.query(distinct(Action.ticker))
        tickers = list(tickers)
        ticker_number = 0
        for ticker in tickers:
            ticker = ticker[0]
            
            ticker_number += 1
            print "[*] Processing ticker {0} {1}/{2}".format(ticker,
                                                             ticker_number,
                                                             len(tickers))

            # Request all items of a ticker
            items = self.session.query(Action) \
                                .filter(Action.ticker == ticker) \
                                .order_by(Action.date, Action.time)

            # initialize last items 
            lastItem = None
            lastDate = None
            counter = 0

            # for each items
            for item in items:

                # transform date and time fields into datetime
                date = item.date
                time = item.time
                date_time_str = date + " " + time
                d = datetime.datetime.strptime(date_time_str, "%y%m%d %H:%M")

                # If it's not the first minute of the day
                if lastItem is not None:
                    delta = d - lastDate
                    
                    # if the time delta is above one minute
                    if delta.total_seconds() > 60.0:

                        # if there is a hole above 2 hours ignore it
                        # and set lastitem and lastdate to None
                        if delta.total_seconds() > 60.0 * 60.0 * 2.0:
                            lastItem = None
                            lastDate = None
                            #print "Ignoring hole {0}".format(delta)
                        else:
                            #print "Hole detected {0} starting at {1} ending at {2}".format(delta, lastDate, d)
                            counter += 1
                            # fill the hole with missing information
                            self.fillHole(lastItem, lastDate, d)
                            
                # flush sqlalchemy every 10 000 holes
                if counter > 10000:
                    print "[+] Flushing 10 000 holes"
                    counter = 0
                    self.session.flush()
                lastItem = item
                lastDate = d
                
            self.session.flush()

        # commit all requests
        self.session.commit()
            
    
    

    def runIndicator(self, indicator):
        all_ISINs = self.getAllUniqueIsin()
        for isin in all_ISINs:
            indicator.run(self.session, isin)

    def testIndicatorPerformance(self, indicator):
        all_ISINs = self.getAllUniqueIsin()
        for isin in all_ISINs:
            indicator.testPerformance3(self.session, isin)
        
            
    def convertResolution(self):        
        all_ISINs = list(self.getAllUniqueIsin())
        counter = 0
        for isin in all_ISINs:
            converter = Converter()
            converter.convert(self.session, isin, ActionHour, 9, ActionDay)
            # converter.convert(self.session, isin, Action, 60, ActionHour)
            # converter.convert(self.session, isin, Action, 30, Action30Minutes)
            # converter.convert(self.session, isin, Action, 10, Action10Minutes)
            counter += 1
            print "[+] {0} done {1}/{2}".format(isin, counter, len(all_ISINs))

    def plot(self, table):
        all_ISINs = ["FR0000130007"]
        #all_ISINs = list(self.getAllUniqueIsin())
        counter = 0
        plotter = Plotter(table, self.session)
        for isin in all_ISINs:
            plotter.plot(isin)
            counter += 1
            print "[+] {0} done {1}/{2}".format(isin, counter, len(all_ISINs))
        

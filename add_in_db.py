#!/usr/bin/env python

import requests
import json
import csv
import pprint
import time
from itertools import izip
from itertools import tee

from db_manager import DBManager
from indicators.heikinashi import IndicatorHeikinAshi

from common.sqlmodels.action import Action
from common.sqlmodels.action import ActionDay
from common.sqlmodels.action import ActionHour
from common.sqlmodels.action import Action10Minutes
from common.sqlmodels.action import Action30Minutes

from indicators.heikinashi import HeikinAshi
from indicators.heikinashi import HeikinAshiHour
from indicators.heikinashi import HeikinAshiDay
from indicators.heikinashi import HeikinAshi30Minutes
from indicators.heikinashi import HeikinAshi10Minutes


def getISINData(ISINs):
    url = "https://api.openfigi.com/v1/mapping"
    data = []
    
    # Build requests data for openfigi
    for isin in ISINs:
        data.append({"idType":"ID_ISIN","idValue":"{0}".format(isin)})

    # Request openFIGI
    print "============ data requested ============="
    ret = requests.post(url,
                        headers={"Content-Type": "text/json"},
                        json=data)
    print "================ returned text ============"
    # print ret.text
    print "===================== json =============="
    returned_data = ret.json()

    # associate each ISIN with its data
    refined_data = []
    for isin, isin_data in izip(ISINs, returned_data):
        refined_data.append({"isin": isin, "data": isin_data})

    return refined_data

def import_csv(db, path):
    with open(path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"',
                                skipinitialspace=True)
        db.insertData(reader)

def requestOpenFIGIWithRateLimit(all_tickers, searchs_by_request=5):

    # split ticker list into sublist of size searchs_by_request
    chunk_list = []
    ticker_sublist = []
    for ticker in all_tickers:
        if len(ticker_sublist) == searchs_by_request:
            chunk_list.append(ticker_sublist)
            ticker_sublist = []
        ticker_sublist.append(ticker)
    # append last created sublist
    chunk_list.append(ticker_sublist)

    open_figi_data = []
    for sublist in chunk_list:
        t1 = time.time()
        open_figi_data.extend(getISINData(sublist))
        t2 = time.time()
        wait_time = max(0, 30.0 - (t2 - t1))
        print "waiting {0} to request openfigi".format(wait_time)
        time.sleep(wait_time)
    return open_figi_data

def updateOpenFigiInfo():
    all_tickers = db.getAllUniqueIsin()
    open_figi_data = requestOpenFIGIWithRateLimit(all_tickers, 5)
    for item in open_figi_data:
        db.updateISINInformations(item["isin"], item["data"])
    print "[+] Fidgi info updated"
        
def main():
    #db = DBManager("sqlite:///sqlalchemy_example.db")
    db = DBManager("postgresql://p-col:laboursecestsympa@localhost:5432/bourse")
    # db.dropTables()
    db.createAll()
    # import_csv(db, "data/ALL.txt")
    #getISINData(["FR0000130007", "LU0323134006"])
    #    getISINData(all_tickers)
    #db.buildActionHourTable()
    #db.fillHoles()

    #ha = IndicatorHeikinAshi()
    #db.runIndicator(ha)

    #db.convertResolution()
    # ha = IndicatorHeikinAshi(ActionHour, HeikinAshiHour)
    # db.runIndicator(ha)
    # ha = IndicatorHeikinAshi(Action30Minutes, HeikinAshi30Minutes)
    # db.runIndicator(ha)
    #db.plot(HeikinAshiHour)
    #db.plot(ActionHour)
    # db.runIndicator(ha)

    # db.convertResolution()
    # ha = IndicatorHeikinAshi(ActionDay, HeikinAshiDay)
    # db.runIndicator(ha)
    # db.plot(ActionDay)

    #ha = IndicatorHeikinAshi(ActionDay, HeikinAshiDay)
    ha = IndicatorHeikinAshi(ActionHour, HeikinAshiHour)
    # db.plot(HeikinAshiDay)
    db.testIndicatorPerformance(ha)
    print "[+] DONE"

if __name__ == "__main__":
    main()
#    db.dropTables()
#    getAllUniqueIsin("data/ALL.txt")

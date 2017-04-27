
class Converter(object):
    def __init__(self):
        pass

    def insertChunk(self, session, ticker, chunk, table_destination):
        high = max([x.high for x in chunk])
        low = min([x.low for x in chunk])
        open = chunk[0].open
        close = chunk[-1].close
        endtime = chunk[-1].time
        enddate = chunk[-1].date
        date = chunk[0].date
        time = chunk[0].time
        per = chunk[0].per
        vol = sum([x.vol for x in chunk])
        new_item = table_destination(ticker=ticker, per=per,
                                     date=date, time=time,
                                     endtime=endtime, enddate=enddate,
                                     open=open, high=high,
                                     low=low, close=close,
                                     vol=vol)
        session.add(new_item)
        

    # the chunk size has to fit the number of minute in hour, hours in days etc.
    def convert(self, session, ticker, table_base, chunk_size, table_destination):

        print "Converting table {0} to table {1} for ticker {2}".format(table_base.__tablename__, table_destination.__tablename__, ticker)
        items = session.query(table_base) \
                       .filter(table_base.ticker == ticker) \
                       .order_by(table_base.date, table_base.time) \
                       .yield_per(10000) \
                       .enable_eagerloads(False)
        
        chunk_counter = 0
        item_chunk = []
        counter = 0
        previous_date = items[0].date
        for item in items:

            # If the day changed push current chunk in database
            if item.date != previous_date and chunk_counter != 0:
                self.insertChunk(session, ticker, item_chunk, table_destination)
                counter += 1
                chunk_counter = 0
                item_chunk = []
                

            item_chunk.append(item)
            chunk_counter += 1

            if chunk_counter == chunk_size:
                # calculate and insert new chunk
                self.insertChunk(session, ticker, item_chunk, table_destination)
                counter += 1
                chunk_counter = 0
                item_chunk = []

            previous_date = item.date

            if counter > 10000:
                print "Flushing 10 000 new items for {0} table".format(table_destination.__tablename__)
                session.flush()
                counter = 0
            
            
        if len(item_chunk) > 0:
            self.insertChunk(session, ticker, item_chunk, table_destination)
        session.flush()
        session.commit()

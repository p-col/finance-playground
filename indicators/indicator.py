
# interface for indicator classes
class IIndicator(object):
    def __init__(self, name, table_name, table, destination_table):
        self.name = name
        self.table_name = table_name
        self.table = table
        self.destination_table = destination_table

    def testPerformance(self, session, ticker):
        raise NotImplementedError

    def run(self, session):
        raise NotImplementedError

    def plot(self, session):
        raise NotImplementedError

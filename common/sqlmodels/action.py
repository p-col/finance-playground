
from common.sqlmodels.sql_model_base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import relationship

class ActionDay(Base):
    __tablename__ = "action_day"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(Text)
    per = Column(Text)
    date = Column(Text)
    time = Column(Text)
    enddate = Column(Text)
    endtime = Column(Text)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)

class ActionHour(Base):
    __tablename__ = "action_hour"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(Text)
    per = Column(Text)
    date = Column(Text)
    time = Column(Text)
    enddate = Column(Text)
    endtime = Column(Text)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)

class Action30Minutes(Base):
    __tablename__ = "action_30_minutes"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(Text)
    per = Column(Text)
    date = Column(Text)
    time = Column(Text)
    enddate = Column(Text)
    endtime = Column(Text)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)

class Action10Minutes(Base):
    __tablename__ = "action_10_minutes"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(Text)
    per = Column(Text)
    date = Column(Text)
    time = Column(Text)
    enddate = Column(Text)
    endtime = Column(Text)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)

class Action(Base):
    __tablename__ = "action_base"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(Text)
    per = Column(Text)
    date = Column(Text)
    time = Column(Text)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)

# table containing information about each ISIN
# the data are fetched from OPENFIGI
class IsinInformations(Base):
    __tablename__ = "isin_info"

    id = Column(Integer, primary_key=True)
    isin = Column(Text)
    compositeFIGI = Column(Text)
    exchCode = Column(Text)
    figi = Column(Text)
    marketSector = Column(Text)
    name = Column(Text)
    securityDescription = Column(Text)
    securityType = Column(Text)
    securityType2 = Column(Text)
    shareClassFIGI = Column(Text)
    ticker = Column(Text)
    uniqueID = Column(Text)
    uniqueIDFutOpt = Column(Text)

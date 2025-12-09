from sqlalchemy import Column,Integer,String,create_engine,LargeBinary,Date,ForeignKey,JSON,Time,Boolean
from sqlalchemy.orm import declarative_base,sessionmaker,relationship
from datetime import date

"""database url"""
DATABASE_URL = "postgresql+psycopg2://postgres:Hemang812@127.0.0.1:5432/attandance_app"

"""create engin"""
engine=create_engine(DATABASE_URL)

"""create base"""
base=declarative_base()

"""create session"""
Session=sessionmaker(bind=engine)
session=Session()

"""create table name student info"""
def create_table_student_info():
    class Student_info(base):
        __tablename__='student_info'
        __table_args__ = {'extend_existing': True}
        roll_number=Column(Integer,primary_key=True)
        name=Column(String(200),nullable=False)
        mobile_number=Column(String(10),nullable=False)
        photo=Column(LargeBinary)
    return Student_info    
    
 
"""create a function to create Date_store table"""
def create_table_store_date():
    class Store_date(base):
        __tablename__='store_date'
        __table_args__ = {'extend_existing': True}
        id=Column(Integer,primary_key=True,autoincrement=True)
        latcure=Column(Integer,default=0)
        date=Column(String(15),nullable=False)
    return Store_date

"""create a function to create attandace table"""
def create_table_attandace(table_name):
    class Attandace(base):
        __tablename__=f'{table_name}'
        __table_args__ = {'extend_existing': True}
        student_roll=Column(Integer,ForeignKey('student_info.roll_number'),primary_key=True)
        
        student_attandace = Column(JSON, default=lambda: {"l_1": "a"})

    
    return Attandace    

"""create a function to create setting table"""
"""structure of setting table -->
    # id: Integer, primary key
    # setting_jason: JSON, not nullable
    jason as per ->
    1 )theam: String, not nullable
    2 )auto :boll
    3 )start(key) to end(value) nullable
"""
def create_table_setting():
    class Setting(base):
        __tablename__ = 'setting'
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True, default=1)
        number_of_lacture = Column(Integer, nullable=False, default=0)
        teame=Column(String(10), nullable=False, default='Light')
        auto = Column(Boolean, nullable=False, default='false')
    return Setting

"""create function to store number of lacture and time"""
def create_table_lacture_time():
    class Lacture_time(base):
        __tablename__ = 'lacture_time'
        id = Column(Integer, primary_key=True,autoincrement=True)
        start = Column(Time)
        end = Column(Time)
    return Lacture_time

if __name__=="__main__":
    print("Creating tables...")



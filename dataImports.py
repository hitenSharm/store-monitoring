from models import StoreCheck
from models import RestaurantAvlHours
from models import TimezoneMappings
from database import db
import csv
import pandas as pd
import pytz
from datetime import datetime

def updateStoresCheck(file_path):
    timezone_mapping={}
    stores_csv=pd.read_csv(file_path,chunksize=100) #for memory reasons    
    for stores_frame in stores_csv:
        stores_frame=stores_frame.dropna(subset=['timestamp_utc'])                

        for i,row in stores_frame.iterrows():
            store_id=row['store_id']
            status = row['status']
            timestamp = datetime.strptime(row['timestamp_utc'], "%Y-%m-%d %H:%M:%S.%f %Z")                         
            store_check=StoreCheck(store_id=store_id,timestamp_utc=timestamp,status=status)
            db.session.add(store_check)    
            timezone_mapping[store_id]="America/Chicago" #adds default in mapping
            print('added store chk')                       
            if (i+1) % 100 == 0:  #100 is batch size
                db.session.commit()                     
        db.session.commit()    
    print('done stores check')       
    return timezone_mapping

 
def updateLocalTimes(file_path):
    with open(file_path,'r') as file:
        csv_reader=csv.reader(file)
        next(csv_reader) #skips header        
        for row in csv_reader:
            store_id=row[0]
            day=row[1]
            start_time_local = pd.to_datetime(row[2]).time()
            end_time_local = pd.to_datetime(row[3]).time()
            avl_time=RestaurantAvlHours(store_id=store_id,day_of_week=day,start_time_local=start_time_local,end_time_local=end_time_local)
            db.session.add(avl_time)            
            print('adding store avl')            
        db.session().commit() 
    print('done local times')
            
def mapTimeZones(file_path,timezone_mapping):    
    with open(file_path,'r') as file:
        csv_reader=csv.reader(file)
        next(csv_reader) #skips header
        for row in csv_reader:
            store_id=row[0]
            zone=row[1]
            timeZoneMapping=TimezoneMappings(store_id=store_id,timezone_str=zone)
            db.session.add(timeZoneMapping)                                                     
        db.session().commit()
    print('done tz map')
    return timezone_mapping


def importData():
    from app import app
    with app.app_context():        
        db.create_all()
        StoreCheck.query.delete()
        RestaurantAvlHours.query.delete()
        TimezoneMappings.query.delete()
        db.session.commit()    
        updateLocalTimes('csvs/Menu hours.csv')
        tmz_mapping=updateStoresCheck('csvs/store status.csv')    #as only this has all store ids    
        return mapTimeZones('csvs/zones.csv',tmz_mapping) #update the default zones if present
    


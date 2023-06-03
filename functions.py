from models import RestaurantAvlHours
import datetime
import pytz
from models import StoreCheck
from models import Report
from database import db
#testing later
import random

def convert_time(time_obj,zone):
    #i take a time string in local timezone, convert into the utc->extract hours and minutes and give as an int
    #ex: 12:32:41 -> 1232
    #to fit in the 2360 array     
    time_zone=pytz.timezone(zone)
    current_date=datetime.date.today()
    local_dt = datetime.datetime.combine(current_date, time_obj)
    local_dt_tz = time_zone.localize(local_dt)
    utc_dt = local_dt_tz.astimezone(pytz.UTC)
    utc_time_obj = utc_dt.time()    
    hours = str(utc_time_obj.hour)
    minutes = str(utc_time_obj.minute)    
    # print(utc_time_obj)
    if int(hours)<=9:
        #ex hours=01,03,02,09
        hours="0"+hours
    if int(minutes)<=9:
        #same as hours
        minutes="0"+minutes

    #03:03 should return 303, 00:00 wil give 0, 12:32 wil give 1232

    time_combined = hours+minutes    
    time_int = int(time_combined)
    # print("Combined Time (Integer):", time_int)
    return time_int

#testing purpose----------------------------------------------------------------------------------
def rmLater():
    datetime_strings = [
    "2023-01-25 09:06:42.605777 UTC",
    "2023-01-25 09:16:42.605777 UTC",
    "2023-01-24 07:05:43.626013 UTC",
    "2023-01-24 07:55:43.626013 UTC",
    "2023-01-24 17:05:43.626013 UTC",
    "2023-01-19 01:30:28.322962 UTC",
    "2023-01-20 08:05:15.198261 UTC",
    "2023-01-21 08:04:35.43697 UTC",
    "2023-01-22 09:14:35.43497 UTC",
    "2023-01-18 19:24:36.43497 UTC",
    "2023-01-18 09:25:36.43497 UTC",
    ]
    datetime_array = []

    for datetime_str in datetime_strings:
        dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f %Z")
        status = random.choice(["active", "inactive"])
        datetime_array.append([dt,status])
    sorted_arr=sorted(datetime_array)
    return sorted_arr

#-------------------------------------------------------------------------------------------

def convertTime(value):
    val=str(value)
    if int(val)<=9:
        val="0"+val
    return val

def update_from_poll(store_online,store_id,report_id):
    polls = StoreCheck.query.filter_by(store_id=store_id).order_by(StoreCheck.timestamp_utc.asc()).all()
    last_7days_poll=[]
    for items in polls:
        last_7days_poll.append([items.timestamp_utc,items.status])
    
    rows=7
    cols=2360
    poll_status=[[-1 for j in range(cols)]for i in range(rows)]    
    
    datetime_objects =[]
    for items in last_7days_poll:
        datetime_objects.append(items[0])

    max_date_day = (max(datetime_objects)).day            
    #all updates happen based on max date day -> (25-date.day+6) in this case    
    index=0    
    for dates in datetime_objects:                
        day=6-(max_date_day-dates.day)
        hour_str=convertTime(dates.hour)
        minute_str=convertTime(dates.minute)       
                        
        pollIndex=int(hour_str+minute_str)
        if last_7days_poll[index][1]=="active":
            poll_status[day][pollIndex]=1
        else:
            poll_status[day][pollIndex]=0                

        index+=1
    
    for i in range(rows):
        current_status=-1
        #this decides based on overlap wether we should say if the store is online or not
        for j in range(cols):
            if store_online[i][j]==2:                       
                store_online[i][j]=current_status if current_status!=-1 else 2         
                break
            if current_status==-1 and poll_status[i][j]==-1:
                continue
            if poll_status[i][j]!=-1:
                current_status=poll_status[i][j]
            store_online[i][j]=current_status
    
    count_prev_hour_up=0
    count_prev_day_up=0
    count_week_up=0

    current_time=datetime.datetime.now()
    current_hour=convertTime(current_time.hour)
    current_minute=convertTime(current_time.minute)

    current_hour_index=int(current_hour+current_minute)

    #as i am calculating for prev hopur and i assume max date as current

    for j in range(current_hour_index,current_hour_index-60,-1):
        if store_online[6][j]==1:
            count_prev_hour_up+=1
    
    #print uptime in minutes percent
    uptime_hourly=(count_prev_hour_up/60)*100    
    
    for j in range(2360):
        if store_online[5][j]==1:
            count_prev_day_up+=1
        
    #print uptime last day
    uptime_day=(count_prev_day_up/2360)*100    

    for i in range(rows):
        for j in range(cols):
            if store_online[i][j]==1:
                count_week_up+=1

    #count whole week uptime
    uptime_week=(count_week_up/(2360*7))*100    

    downtime_week=100-uptime_week
    downtime_hour=100-uptime_hourly
    downtime_day=100-uptime_day

    new_report=Report(report_id=report_id,store_id=store_id,uptime_last_hour=uptime_hourly,uptime_last_day=uptime_day,uptime_last_week=uptime_week,downtime_last_hour=downtime_hour,downtime_last_day=downtime_day,downtime_last_week=downtime_week,status="done")
    db.session.add(new_report)    



def calculate(tmz_map,report_id):
    from app import app

    with app.app_context():        

        for store_id in tmz_map:
            #for each store, create a 7*2360 array
            #use the business hours->convert into utc and mark 1 for the business hours on each day
            store_online=[]
            rows=7
            cols=2360
            business_hours_all=RestaurantAvlHours.query.filter_by(store_id=store_id).all()            
            if len(business_hours_all)>0:
                store_online=[[0 for j in range(cols)]for i in range(rows)]
                #change business hours start time and end time in utc and then into --> 00:00 to 23:59 format
                #inaccuracy of 0.02 at max
                for item in business_hours_all:
                    day=item.day_of_week                    
                    start_time=convert_time(item.start_time_local,tmz_map[store_id])
                    end_time=convert_time(item.end_time_local,tmz_map[store_id])
                    #turn that part of array into 1's
                    for i in range(start_time,end_time+1):
                        store_online[day][i]=1
                    store_online[day][end_time]=2
                    #mark the end of that day for later poll update                                                                
            else:
                store_online=[[1 for j in range(cols)]for i in range(rows)]
                #open 24/7                                
            update_from_poll(store_online,store_id,report_id)                    
        db.session.commit()


                
            
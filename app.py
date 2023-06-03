from flask import Flask,request
from database import db
from dataImports import importData
from functions import calculate
import uuid
import csv
from models import Report
from apscheduler.schedulers.background import BackgroundScheduler

import gc
gc.set_threshold(0)
scheduler = BackgroundScheduler()
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///restaurant.db'
db.init_app(app)

#start a scheduler that runs each hour and clears old models and imports new data!

timezone_map={}
def task_to_schedule():
    global timezone_map
    timezone_map=importData() 

def initialize_scheduler():    
    scheduler.add_job(task_to_schedule, 'interval', hours=1)
    scheduler.start()
    

@app.route('/generate-report')
def startGeneration():    
    report_id=str(uuid.uuid4())
    print(report_id)
    calculate(timezone_map,report_id)
    print("done")    
    return report_id

@app.route('/get-report',methods=['POST'])
def getReport():
    reportId=request.json.get('report_id')
    report = Report.query.filter_by(report_id=reportId).all()
    if report:
        filename = f"{reportId}.csv"
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Report ID', 'Store ID', 'Uptime Last Hour', 'Uptime Last Day', 'Uptime Last Week',
                            'Downtime Last Hour', 'Downtime Last Day', 'Downtime Last Week', 'Status'])
            
            for report in report:            
                writer.writerow([report.report_id, report.store_id, report.uptime_last_hour, report.uptime_last_day,
                                report.uptime_last_week, report.downtime_last_hour, report.downtime_last_day,
                                report.downtime_last_week, report.status])
        return reportId
    return "Not Found/Running"




if __name__== "__main__":    
    initialize_scheduler()    
    timezone_map=importData()   
    app.run(debug=True)

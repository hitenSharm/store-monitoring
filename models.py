from datetime import datetime
from database import db

class StoreCheck(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    store_id = db.Column(db.Integer)
    timestamp_utc = db.Column(db.DateTime)
    status = db.Column(db.String(10))

    def __repr__(self):
        return f"<Store(id={self.id}, store_id={self.store_id}, timestamp_utc={self.timestamp_utc}, status={self.status})>"

class RestaurantAvlHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer)
    day_of_week = db.Column(db.Integer)
    start_time_local = db.Column(db.Time)
    end_time_local = db.Column(db.Time)

class TimezoneMappings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer)
    timezone_str = db.Column(db.String(50))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id= db.Column(db.String(50), nullable=False)
    store_id = db.Column(db.String(50), nullable=False)
    uptime_last_hour = db.Column(db.Integer)
    uptime_last_day = db.Column(db.Integer)
    uptime_last_week = db.Column(db.Integer)
    downtime_last_hour = db.Column(db.Integer)
    downtime_last_day = db.Column(db.Integer)
    downtime_last_week = db.Column(db.Integer)
    status = db.Column(db.String(50))
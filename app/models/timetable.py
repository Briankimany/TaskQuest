
from sqlalchemy import Enum as PgEnum
import enum
from sqlalchemy.ext.mutable import MutableDict
from .base import db
from sqlalchemy.ext.hybrid import hybrid_property

class WeekDay(enum.IntEnum):
    
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6
    SUN = 7

class Timetable(db.Model):
    """Daily schedule for a user."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    goal_text = db.Column(db.Text, nullable=True)
    meta_data = db.Column(MutableDict.as_mutable(db.JSON), default=dict)
    finalized = db.Column(db.Boolean,default=False)

    user = db.relationship('User', backref=db.backref('timetables', lazy=True))
    
    def __repr__(self):
        return f'<Timetable {self.date}>'


class TimetableEntry(db.Model):
    """Individual scheduled task."""
    id = db.Column(db.Integer, primary_key=True)

    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activity.id'), nullable=False)

    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    cyclic = db.Column(db.Boolean, default=False)
    weekday = db.Column(PgEnum(WeekDay), nullable=True)  # Used only if cyclic=True
    description = db.Column(db.String)
    # Relationships
    timetable = db.relationship('Timetable', backref=db.backref('entries', lazy=True, cascade="all, delete-orphan"))
    sub_activity = db.relationship('SubActivity', backref=db.backref('timetable_entries', lazy=True))


    @hybrid_property
    def exp_gain(self):
       
        if self.completion_log:
            return self.completion_log.exp_impact
        return self.sub_activity.calculate_potential_exp()
      
    def __repr__(self):
        return f'<TTEntry {self.sub_activity.name} at {self.start_time} exp {self.exp_gain}>'
    def to_dict(self):
        return {
            "id":self.id,
            "timetable_id":self.timetable_id,
            "start_time":str(self.start_time),
            "end_time":str(self.end_time), 
            "activity_name":self.sub_activity.name,
            'cyclic':self.cyclic,
            'weekday':self.weekday
        }

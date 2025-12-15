from datetime import datetime
from app import db


class PersonalRecord(db.Model):
    """Personal records model."""
    __tablename__ = 'personal_records'

    record_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'))
    record_type = db.Column(db.String(20))  # '1RM', 'rep_max', 'volume', 'distance', 'pace'
    value = db.Column(db.Numeric(10, 2))
    date_achieved = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_user_records(cls, user_id, record_type=None):
        """Get user's personal records."""
        query = cls.query.filter_by(user_id=user_id)
        if record_type:
            query = query.filter_by(record_type=record_type)
        return query.order_by(cls.date_achieved.desc()).all()

    @classmethod
    def get_exercise_pr(cls, user_id, exercise_id, record_type='1RM'):
        """Get user's PR for an exercise."""
        return cls.query.filter_by(
            user_id=user_id,
            exercise_id=exercise_id,
            record_type=record_type
        ).order_by(cls.value.desc()).first()

    @classmethod
    def check_and_update_pr(cls, user_id, exercise_id, record_type, new_value, date_achieved):
        """Check if new value is a PR and update if so."""
        current_pr = cls.get_exercise_pr(user_id, exercise_id, record_type)

        if not current_pr or new_value > float(current_pr.value):
            # New PR!
            new_record = cls(
                user_id=user_id,
                exercise_id=exercise_id,
                record_type=record_type,
                value=new_value,
                date_achieved=date_achieved,
                notes=f'Auto-detected PR: {new_value}'
            )
            db.session.add(new_record)
            db.session.commit()
            return True
        return False

    @classmethod
    def get_recent_prs(cls, user_id, limit=5):
        """Get user's most recent PRs."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.date_achieved.desc()
        ).limit(limit).all()

    def __repr__(self):
        return f'<PersonalRecord {self.record_type}: {self.value}>'

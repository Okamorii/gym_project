from datetime import datetime, date, timedelta
from app import db


class PlannedWorkout(db.Model):
    """Planned workout model for weekly planning."""
    __tablename__ = 'planned_workouts'

    plan_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    planned_date = db.Column(db.Date, nullable=False)
    workout_type = db.Column(db.String(20), nullable=False)  # 'upper_body', 'running', 'rest'
    description = db.Column(db.String(255))
    target_duration = db.Column(db.Integer)  # minutes
    target_distance = db.Column(db.Numeric(6, 2))  # km for running
    completed = db.Column(db.Boolean, default=False)
    completed_session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.session_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to actual workout session
    completed_session = db.relationship('WorkoutSession', foreign_keys=[completed_session_id])

    @classmethod
    def get_week_plan(cls, user_id, week_start=None):
        """Get planned workouts for a week."""
        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        return cls.query.filter(
            cls.user_id == user_id,
            cls.planned_date >= week_start,
            cls.planned_date <= week_end
        ).order_by(cls.planned_date).all()

    @classmethod
    def get_day_plan(cls, user_id, plan_date):
        """Get planned workouts for a specific day."""
        return cls.query.filter_by(
            user_id=user_id,
            planned_date=plan_date
        ).all()

    @classmethod
    def create_week_plan(cls, user_id, week_start, plans):
        """Create a week's worth of planned workouts."""
        # Delete existing plans for this week
        week_end = week_start + timedelta(days=6)
        cls.query.filter(
            cls.user_id == user_id,
            cls.planned_date >= week_start,
            cls.planned_date <= week_end
        ).delete()

        # Create new plans
        for plan in plans:
            new_plan = cls(
                user_id=user_id,
                planned_date=plan['date'],
                workout_type=plan['type'],
                description=plan.get('description'),
                target_duration=plan.get('duration'),
                target_distance=plan.get('distance')
            )
            db.session.add(new_plan)

        db.session.commit()

    @classmethod
    def mark_completed(cls, plan_id, session_id=None):
        """Mark a planned workout as completed."""
        plan = cls.query.get(plan_id)
        if plan:
            plan.completed = True
            plan.completed_session_id = session_id
            db.session.commit()
            return True
        return False

    @classmethod
    def get_completion_stats(cls, user_id, weeks=4):
        """Get completion statistics for the past N weeks."""
        start_date = date.today() - timedelta(weeks=weeks)

        plans = cls.query.filter(
            cls.user_id == user_id,
            cls.planned_date >= start_date,
            cls.planned_date <= date.today()
        ).all()

        if not plans:
            return {'total': 0, 'completed': 0, 'rate': 0}

        total = len(plans)
        completed = sum(1 for p in plans if p.completed)

        return {
            'total': total,
            'completed': completed,
            'rate': round(completed / total * 100) if total > 0 else 0
        }

    def __repr__(self):
        return f'<PlannedWorkout {self.planned_date} - {self.workout_type}>'

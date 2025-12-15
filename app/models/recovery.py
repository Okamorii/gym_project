from datetime import datetime, date
from app import db


class RecoveryLog(db.Model):
    """Recovery tracking model."""
    __tablename__ = 'recovery_logs'

    recovery_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    sleep_quality = db.Column(db.Integer)  # 1-10
    energy_level = db.Column(db.Integer)  # 1-10
    muscle_soreness = db.Column(db.Integer)  # 1-10
    motivation_score = db.Column(db.Integer)  # 1-10
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def overall_recovery_score(self):
        """Calculate overall recovery score (average of all metrics)."""
        metrics = [
            self.sleep_quality,
            self.energy_level,
            10 - (self.muscle_soreness or 0),  # Invert soreness (lower is better)
            self.motivation_score
        ]
        valid_metrics = [m for m in metrics if m is not None]
        if not valid_metrics:
            return None
        return round(sum(valid_metrics) / len(valid_metrics), 1)

    @classmethod
    def get_today_log(cls, user_id):
        """Get today's recovery log."""
        return cls.query.filter_by(
            user_id=user_id,
            log_date=date.today()
        ).first()

    @classmethod
    def get_user_logs(cls, user_id, limit=14):
        """Get user's recent recovery logs."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.log_date.desc()
        ).limit(limit).all()

    @classmethod
    def get_weekly_average(cls, user_id):
        """Get weekly average recovery metrics."""
        from datetime import timedelta
        week_start = date.today() - timedelta(days=7)

        logs = cls.query.filter(
            cls.user_id == user_id,
            cls.log_date >= week_start
        ).all()

        if not logs:
            return None

        return {
            'avg_sleep': round(sum(l.sleep_quality or 0 for l in logs) / len(logs), 1),
            'avg_energy': round(sum(l.energy_level or 0 for l in logs) / len(logs), 1),
            'avg_soreness': round(sum(l.muscle_soreness or 0 for l in logs) / len(logs), 1),
            'avg_motivation': round(sum(l.motivation_score or 0 for l in logs) / len(logs), 1),
            'logs_count': len(logs)
        }

    def __repr__(self):
        return f'<RecoveryLog {self.log_date}>'

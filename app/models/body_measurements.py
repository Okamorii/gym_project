from datetime import datetime, date, timedelta
from app import db


class BodyMeasurement(db.Model):
    """Body measurements tracking model."""
    __tablename__ = 'body_measurements'

    measurement_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    measurement_date = db.Column(db.Date, nullable=False, default=date.today)

    # Core measurements
    weight_kg = db.Column(db.Numeric(5, 2))  # Body weight
    body_fat_pct = db.Column(db.Numeric(4, 1))  # Body fat percentage

    # Circumference measurements (in cm)
    chest_cm = db.Column(db.Numeric(5, 1))
    waist_cm = db.Column(db.Numeric(5, 1))
    hips_cm = db.Column(db.Numeric(5, 1))
    left_arm_cm = db.Column(db.Numeric(4, 1))
    right_arm_cm = db.Column(db.Numeric(4, 1))
    left_thigh_cm = db.Column(db.Numeric(5, 1))
    right_thigh_cm = db.Column(db.Numeric(5, 1))
    left_calf_cm = db.Column(db.Numeric(4, 1))
    right_calf_cm = db.Column(db.Numeric(4, 1))
    neck_cm = db.Column(db.Numeric(4, 1))
    shoulders_cm = db.Column(db.Numeric(5, 1))

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def waist_to_hip_ratio(self):
        """Calculate waist-to-hip ratio (health indicator)."""
        if self.waist_cm and self.hips_cm and float(self.hips_cm) > 0:
            return round(float(self.waist_cm) / float(self.hips_cm), 2)
        return None

    @property
    def arm_avg_cm(self):
        """Average arm circumference."""
        arms = [a for a in [self.left_arm_cm, self.right_arm_cm] if a]
        if arms:
            return round(sum(float(a) for a in arms) / len(arms), 1)
        return None

    @property
    def thigh_avg_cm(self):
        """Average thigh circumference."""
        thighs = [t for t in [self.left_thigh_cm, self.right_thigh_cm] if t]
        if thighs:
            return round(sum(float(t) for t in thighs) / len(thighs), 1)
        return None

    @classmethod
    def get_latest(cls, user_id):
        """Get most recent measurement."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.measurement_date.desc()
        ).first()

    @classmethod
    def get_user_measurements(cls, user_id, limit=30):
        """Get user's recent measurements."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.measurement_date.desc()
        ).limit(limit).all()

    @classmethod
    def get_progress(cls, user_id, field, weeks=12):
        """Get progress data for a specific measurement field."""
        start_date = date.today() - timedelta(weeks=weeks)
        measurements = cls.query.filter(
            cls.user_id == user_id,
            cls.measurement_date >= start_date,
            getattr(cls, field).isnot(None)
        ).order_by(cls.measurement_date.asc()).all()

        return [{
            'date': str(m.measurement_date),
            'value': float(getattr(m, field))
        } for m in measurements]

    @classmethod
    def get_comparison(cls, user_id):
        """Compare latest measurements to previous."""
        measurements = cls.query.filter_by(user_id=user_id).order_by(
            cls.measurement_date.desc()
        ).limit(2).all()

        if len(measurements) < 2:
            return None

        latest, previous = measurements[0], measurements[1]
        comparison = {}

        fields = ['weight_kg', 'body_fat_pct', 'chest_cm', 'waist_cm',
                  'hips_cm', 'left_arm_cm', 'right_arm_cm', 'left_thigh_cm',
                  'right_thigh_cm', 'neck_cm', 'shoulders_cm']

        for field in fields:
            latest_val = getattr(latest, field)
            prev_val = getattr(previous, field)
            if latest_val is not None and prev_val is not None:
                diff = float(latest_val) - float(prev_val)
                comparison[field] = {
                    'current': float(latest_val),
                    'previous': float(prev_val),
                    'change': round(diff, 1),
                    'pct_change': round((diff / float(prev_val)) * 100, 1) if float(prev_val) != 0 else 0
                }

        comparison['days_between'] = (latest.measurement_date - previous.measurement_date).days
        return comparison

    def __repr__(self):
        return f'<BodyMeasurement {self.measurement_date} - {self.weight_kg}kg>'

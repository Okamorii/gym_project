from datetime import datetime
from app import db


class Exercise(db.Model):
    """Exercise library model."""
    __tablename__ = 'exercises'

    exercise_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    muscle_group = db.Column(db.String(50))
    exercise_type = db.Column(db.String(20))  # 'strength' or 'cardio'
    video_reference_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    strength_logs = db.relationship('StrengthLog', backref='exercise', lazy='dynamic')
    personal_records = db.relationship('PersonalRecord', backref='exercise', lazy='dynamic')

    # Substitutions (self-referential many-to-many)
    substitutes = db.relationship(
        'Exercise',
        secondary='exercise_substitutions',
        primaryjoin='Exercise.exercise_id==ExerciseSubstitution.exercise_id',
        secondaryjoin='Exercise.exercise_id==ExerciseSubstitution.substitute_id',
        backref='substitute_for'
    )

    def get_substitutes_with_history(self, user_id):
        """Get substitutes with user's last performance."""
        from sqlalchemy import text
        result = db.session.execute(
            text('SELECT * FROM get_exercise_substitutes(:ex_id, :u_id)'),
            {'ex_id': self.exercise_id, 'u_id': user_id}
        )
        return [dict(row._mapping) for row in result]

    def calculate_1rm(self, weight, reps):
        """Calculate estimated 1RM using Epley formula."""
        if reps == 1:
            return weight
        if reps <= 0 or weight <= 0:
            return 0
        return round(weight * (1 + reps / 30), 2)

    @classmethod
    def get_by_muscle_group(cls, muscle_group):
        """Get all exercises for a muscle group."""
        return cls.query.filter_by(muscle_group=muscle_group).all()

    @classmethod
    def get_strength_exercises(cls):
        """Get all strength exercises."""
        return cls.query.filter_by(exercise_type='strength').all()

    @classmethod
    def get_cardio_exercises(cls):
        """Get all cardio exercises."""
        return cls.query.filter_by(exercise_type='cardio').all()

    def __repr__(self):
        return f'<Exercise {self.name}>'


class ExerciseSubstitution(db.Model):
    """Exercise substitution mapping."""
    __tablename__ = 'exercise_substitutions'

    substitution_id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    substitute_id = db.Column(db.Integer, db.ForeignKey('exercises.exercise_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('exercise_id', 'substitute_id'),
        db.CheckConstraint('exercise_id != substitute_id'),
    )

    @classmethod
    def add_substitution(cls, exercise_id, substitute_id):
        """Add bidirectional substitution."""
        # Add both directions
        sub1 = cls(exercise_id=exercise_id, substitute_id=substitute_id)
        sub2 = cls(exercise_id=substitute_id, substitute_id=exercise_id)

        try:
            db.session.add(sub1)
            db.session.add(sub2)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @classmethod
    def remove_substitution(cls, exercise_id, substitute_id):
        """Remove bidirectional substitution."""
        cls.query.filter(
            ((cls.exercise_id == exercise_id) & (cls.substitute_id == substitute_id)) |
            ((cls.exercise_id == substitute_id) & (cls.substitute_id == exercise_id))
        ).delete()
        db.session.commit()

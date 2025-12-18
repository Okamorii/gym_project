"""Tests for database models."""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app import db
from app.models import (
    User, Exercise, WorkoutSession, StrengthLog, RunningLog,
    RecoveryLog, PersonalRecord, BodyMeasurement
)


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, app):
        """Test user creation."""
        with app.app_context():
            user = User(username='newuser', email='new@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            assert user.user_id is not None
            assert user.username == 'newuser'
            assert user.email == 'new@example.com'

    def test_password_hashing(self, app):
        """Test password is properly hashed."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('mypassword')

            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword')
            assert not user.check_password('wrongpassword')

    def test_unique_username(self, app, sample_user):
        """Test username uniqueness constraint."""
        with app.app_context():
            duplicate = User(username='testuser', email='other@example.com')
            duplicate.set_password('password')
            db.session.add(duplicate)

            with pytest.raises(Exception):
                db.session.commit()


class TestExerciseModel:
    """Tests for Exercise model."""

    def test_create_exercise(self, app):
        """Test exercise creation."""
        with app.app_context():
            exercise = Exercise(
                name='Test Exercise',
                muscle_group='Chest',
                exercise_type='strength'
            )
            db.session.add(exercise)
            db.session.commit()

            assert exercise.exercise_id is not None
            assert exercise.name == 'Test Exercise'

    def test_get_by_muscle_group(self, app, sample_exercises):
        """Test filtering exercises by muscle group."""
        with app.app_context():
            chest_exercises = Exercise.query.filter_by(muscle_group='Chest').all()
            assert len(chest_exercises) >= 1
            assert all(ex.muscle_group == 'Chest' for ex in chest_exercises)


class TestStrengthLogModel:
    """Tests for StrengthLog model."""

    def test_estimated_1rm(self, app, sample_strength_session):
        """Test 1RM estimation using Epley formula."""
        with app.app_context():
            log = StrengthLog.query.first()

            # Epley formula: weight * (1 + reps/30)
            # 80 * (1 + 10/30) = 80 * 1.333 = 106.67
            expected_1rm = 80 * (1 + 10/30)
            assert abs(float(log.estimated_1rm) - expected_1rm) < 0.1

    def test_volume_calculation(self, app, sample_strength_session):
        """Test volume calculation."""
        with app.app_context():
            log = StrengthLog.query.first()

            # Volume = sets * reps * weight
            expected_volume = 3 * 10 * 80
            assert log.volume == expected_volume


class TestRunningLogModel:
    """Tests for RunningLog model."""

    def test_pace_calculation(self, app, sample_running_session):
        """Test pace calculation."""
        with app.app_context():
            log = RunningLog.query.first()

            # Pace = duration / distance
            expected_pace = 45 / 8.5
            assert abs(float(log.pace_per_km) - expected_pace) < 0.1

    def test_trimp_calculation(self, app, sample_running_session):
        """Test TRIMP score calculation."""
        with app.app_context():
            log = RunningLog.query.first()

            # Should have a TRIMP score > 0 when HR data present
            assert log.trimp_score is not None
            assert log.trimp_score > 0


class TestRecoveryLogModel:
    """Tests for RecoveryLog model."""

    def test_overall_recovery_score(self, app, sample_recovery):
        """Test overall recovery score calculation."""
        with app.app_context():
            recovery = RecoveryLog.query.first()

            # Score = avg(sleep, energy, 10-soreness, motivation)
            # = avg(8, 7, 10-3, 9) = avg(8, 7, 7, 9) = 7.75
            expected_score = (8 + 7 + (10 - 3) + 9) / 4
            assert abs(recovery.overall_recovery_score - expected_score) < 0.1

    def test_readiness_level(self, app, sample_recovery):
        """Test readiness level determination."""
        with app.app_context():
            recovery = RecoveryLog.query.first()
            readiness = recovery.readiness_level

            assert readiness is not None
            assert 'level' in readiness
            assert 'label' in readiness
            assert 'advice' in readiness

    def test_get_today_log(self, app, sample_recovery, sample_user):
        """Test getting today's recovery log."""
        with app.app_context():
            today_log = RecoveryLog.get_today_log(sample_user.user_id)
            assert today_log is not None
            assert today_log.log_date == date.today()


class TestBodyMeasurementModel:
    """Tests for BodyMeasurement model."""

    def test_create_measurement(self, app, sample_user):
        """Test body measurement creation."""
        with app.app_context():
            measurement = BodyMeasurement(
                user_id=sample_user.user_id,
                weight_kg=Decimal('75.5'),
                body_fat_pct=Decimal('15.0'),
                waist_cm=Decimal('82.0'),
                hips_cm=Decimal('95.0')
            )
            db.session.add(measurement)
            db.session.commit()

            assert measurement.measurement_id is not None
            assert measurement.weight_kg == Decimal('75.5')

    def test_waist_to_hip_ratio(self, app, sample_user):
        """Test waist-to-hip ratio calculation."""
        with app.app_context():
            measurement = BodyMeasurement(
                user_id=sample_user.user_id,
                waist_cm=Decimal('82.0'),
                hips_cm=Decimal('100.0')
            )
            db.session.add(measurement)
            db.session.commit()

            # WHR = waist / hips = 82 / 100 = 0.82
            assert measurement.waist_to_hip_ratio == 0.82

    def test_get_latest(self, app, sample_user):
        """Test getting latest measurement."""
        with app.app_context():
            # Create two measurements
            old = BodyMeasurement(
                user_id=sample_user.user_id,
                measurement_date=date.today() - timedelta(days=7),
                weight_kg=Decimal('76.0')
            )
            new = BodyMeasurement(
                user_id=sample_user.user_id,
                measurement_date=date.today(),
                weight_kg=Decimal('75.0')
            )
            db.session.add(old)
            db.session.add(new)
            db.session.commit()

            latest = BodyMeasurement.get_latest(sample_user.user_id)
            assert latest.weight_kg == Decimal('75.0')


class TestWorkoutSessionModel:
    """Tests for WorkoutSession model."""

    def test_create_session(self, app, sample_user):
        """Test workout session creation."""
        with app.app_context():
            session = WorkoutSession(
                user_id=sample_user.user_id,
                session_date=date.today(),
                session_type='upper_body'
            )
            db.session.add(session)
            db.session.commit()

            assert session.session_id is not None

    def test_total_volume(self, app, sample_strength_session, sample_exercises):
        """Test total volume calculation for session."""
        with app.app_context():
            session = WorkoutSession.query.first()

            # Add another log to the session
            bench = Exercise.query.filter_by(name='Bench Press').first()
            log2 = StrengthLog(
                session_id=session.session_id,
                exercise_id=bench.exercise_id,
                sets=3,
                reps=8,
                weight_kg=85
            )
            db.session.add(log2)
            db.session.commit()

            # Total volume = (3*10*80) + (3*8*85) = 2400 + 2040 = 4440
            expected = 2400 + 2040
            assert session.total_volume == expected

    def test_get_user_sessions(self, app, sample_user, sample_strength_session):
        """Test getting user's sessions."""
        with app.app_context():
            sessions = WorkoutSession.get_user_sessions(sample_user.user_id)
            assert len(sessions) >= 1
            assert all(s.user_id == sample_user.user_id for s in sessions)

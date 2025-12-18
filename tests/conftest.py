"""Pytest configuration and fixtures."""
import pytest
from datetime import date, timedelta
from app import create_app, db
from app.models import User, Exercise, WorkoutSession, StrengthLog, RunningLog, RecoveryLog


@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(user)
        return user


@pytest.fixture
def sample_exercises(app):
    """Create sample exercises."""
    with app.app_context():
        exercises = [
            Exercise(name='Bench Press', muscle_group='Chest', exercise_type='strength'),
            Exercise(name='Squat', muscle_group='Legs', exercise_type='strength'),
            Exercise(name='Deadlift', muscle_group='Back', exercise_type='strength'),
            Exercise(name='Easy Run', muscle_group='Cardio', exercise_type='cardio'),
        ]
        for ex in exercises:
            db.session.add(ex)
        db.session.commit()

        return Exercise.query.all()


@pytest.fixture
def authenticated_client(client, sample_user, app):
    """Create an authenticated test client."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_user.user_id)
        sess['_fresh'] = True

    return client


@pytest.fixture
def sample_strength_session(app, sample_user, sample_exercises):
    """Create a sample strength training session."""
    with app.app_context():
        session = WorkoutSession(
            user_id=sample_user.user_id,
            session_date=date.today(),
            session_type='upper_body',
            duration_minutes=60
        )
        db.session.add(session)
        db.session.commit()

        # Add some strength logs
        bench = Exercise.query.filter_by(name='Bench Press').first()
        log = StrengthLog(
            session_id=session.session_id,
            exercise_id=bench.exercise_id,
            sets=3,
            reps=10,
            weight_kg=80
        )
        db.session.add(log)
        db.session.commit()

        return session


@pytest.fixture
def sample_running_session(app, sample_user):
    """Create a sample running session."""
    with app.app_context():
        session = WorkoutSession(
            user_id=sample_user.user_id,
            session_date=date.today(),
            session_type='running',
            duration_minutes=45
        )
        db.session.add(session)
        db.session.commit()

        log = RunningLog(
            session_id=session.session_id,
            run_type='easy',
            distance_km=8.5,
            duration_minutes=45,
            avg_heart_rate=145,
            max_heart_rate=165
        )
        db.session.add(log)
        db.session.commit()

        return session


@pytest.fixture
def sample_recovery(app, sample_user):
    """Create sample recovery log."""
    with app.app_context():
        recovery = RecoveryLog(
            user_id=sample_user.user_id,
            log_date=date.today(),
            sleep_quality=8,
            energy_level=7,
            muscle_soreness=3,
            motivation_score=9
        )
        db.session.add(recovery)
        db.session.commit()

        return recovery

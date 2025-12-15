from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from app import db
from app.models import WorkoutSession, StrengthLog, RunningLog, PersonalRecord, Exercise
from sqlalchemy import func, text

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@login_required
def index():
    """Analytics dashboard."""
    return render_template('analytics/index.html')


@analytics_bp.route('/strength')
@login_required
def strength_analytics():
    """Strength training analytics."""
    # Get all exercises user has logged
    exercises = db.session.query(Exercise).join(StrengthLog).join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).distinct().all()

    # Get PRs
    prs = PersonalRecord.get_user_records(current_user.user_id, record_type='1RM')

    return render_template(
        'strength.html',
        exercises=exercises,
        prs=prs
    )


@analytics_bp.route('/running')
@login_required
def running_analytics():
    """Running analytics."""
    return render_template('analytics/running.html')


@analytics_bp.route('/api/strength-volume')
@login_required
def strength_volume_data():
    """Get weekly strength volume data for charts."""
    weeks = request.args.get('weeks', 12, type=int)

    result = db.session.execute(
        text('''
            SELECT week_start, muscle_group, total_volume
            FROM weekly_strength_volume
            WHERE user_id = :user_id
            ORDER BY week_start DESC
            LIMIT :limit
        '''),
        {'user_id': current_user.user_id, 'limit': weeks * 10}
    )

    # Organize by week and muscle group
    data = {}
    for row in result:
        week = str(row.week_start)
        if week not in data:
            data[week] = {}
        data[week][row.muscle_group] = float(row.total_volume or 0)

    return jsonify(data)


@analytics_bp.route('/api/exercise-progress/<int:exercise_id>')
@login_required
def exercise_progress(exercise_id):
    """Get progress data for a specific exercise."""
    history = StrengthLog.get_exercise_history(current_user.user_id, exercise_id, limit=50)

    data = [{
        'date': str(log.session.session_date),
        'weight': float(log.weight_kg) if log.weight_kg else 0,
        'reps': log.reps,
        'estimated_1rm': log.estimated_1rm,
        'volume': log.volume
    } for log in reversed(history)]

    return jsonify(data)


@analytics_bp.route('/api/running-progress')
@login_required
def running_progress():
    """Get running progress data."""
    weeks = request.args.get('weeks', 12, type=int)

    result = db.session.execute(
        text('''
            SELECT week_start, total_distance_km, run_count, total_duration_min, avg_trimp
            FROM weekly_running_mileage
            WHERE user_id = :user_id
            ORDER BY week_start DESC
            LIMIT :limit
        '''),
        {'user_id': current_user.user_id, 'limit': weeks}
    )

    data = [{
        'week': str(row.week_start),
        'distance': float(row.total_distance_km or 0),
        'runs': row.run_count,
        'duration': row.total_duration_min or 0,
        'avg_trimp': float(row.avg_trimp or 0) if row.avg_trimp else 0
    } for row in reversed(list(result))]

    return jsonify(data)


@analytics_bp.route('/api/run-type-distribution')
@login_required
def run_type_distribution():
    """Get distribution of run types."""
    result = db.session.query(
        RunningLog.run_type,
        func.count(RunningLog.log_id).label('count'),
        func.sum(RunningLog.distance_km).label('total_distance')
    ).join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).group_by(RunningLog.run_type).all()

    data = [{
        'type': row.run_type or 'other',
        'count': row.count,
        'distance': float(row.total_distance or 0)
    } for row in result]

    return jsonify(data)


@analytics_bp.route('/api/muscle-group-volume')
@login_required
def muscle_group_volume():
    """Get volume distribution by muscle group."""
    result = db.session.query(
        Exercise.muscle_group,
        func.sum(StrengthLog.sets * StrengthLog.reps * StrengthLog.weight_kg).label('total_volume')
    ).join(StrengthLog).join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).group_by(Exercise.muscle_group).all()

    data = [{
        'muscle_group': row.muscle_group or 'Other',
        'volume': float(row.total_volume or 0)
    } for row in result]

    return jsonify(data)


@analytics_bp.route('/api/recovery-trends')
@login_required
def recovery_trends():
    """Get recovery trends data."""
    result = db.session.execute(
        text('''
            SELECT week_start, avg_sleep, avg_energy, avg_soreness, avg_motivation
            FROM recovery_trends
            WHERE user_id = :user_id
            ORDER BY week_start DESC
            LIMIT 12
        '''),
        {'user_id': current_user.user_id}
    )

    data = [{
        'week': str(row.week_start),
        'sleep': float(row.avg_sleep or 0),
        'energy': float(row.avg_energy or 0),
        'soreness': float(row.avg_soreness or 0),
        'motivation': float(row.avg_motivation or 0)
    } for row in reversed(list(result))]

    return jsonify(data)


@analytics_bp.route('/api/workout-frequency')
@login_required
def workout_frequency():
    """Get workout frequency by day of week."""
    result = db.session.query(
        func.extract('dow', WorkoutSession.session_date).label('day_of_week'),
        WorkoutSession.session_type,
        func.count(WorkoutSession.session_id).label('count')
    ).filter(
        WorkoutSession.user_id == current_user.user_id
    ).group_by(
        func.extract('dow', WorkoutSession.session_date),
        WorkoutSession.session_type
    ).all()

    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    data = {day: {'strength': 0, 'running': 0} for day in days}

    for row in result:
        day_idx = int(row.day_of_week)
        day_name = days[day_idx]
        if row.session_type == 'upper_body':
            data[day_name]['strength'] = row.count
        elif row.session_type == 'running':
            data[day_name]['running'] = row.count

    return jsonify(data)


@analytics_bp.route('/api/pr-timeline')
@login_required
def pr_timeline():
    """Get PR timeline."""
    prs = PersonalRecord.query.filter_by(user_id=current_user.user_id).order_by(
        PersonalRecord.date_achieved.desc()
    ).limit(20).all()

    data = [{
        'date': str(pr.date_achieved),
        'exercise': pr.exercise.name if pr.exercise else 'Unknown',
        'type': pr.record_type,
        'value': float(pr.value)
    } for pr in prs]

    return jsonify(data)

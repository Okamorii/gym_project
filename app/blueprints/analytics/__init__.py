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
        'analytics/strength.html',
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


@analytics_bp.route('/api/activity-heatmap')
@login_required
def activity_heatmap():
    """Get workout activity data for heatmap (last 52 weeks)."""
    weeks = request.args.get('weeks', 52, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    # Get all workouts in date range
    workouts = db.session.query(
        WorkoutSession.session_date,
        WorkoutSession.session_type,
        func.count(WorkoutSession.session_id).label('count')
    ).filter(
        WorkoutSession.user_id == current_user.user_id,
        WorkoutSession.session_date >= start_date,
        WorkoutSession.session_date <= end_date
    ).group_by(
        WorkoutSession.session_date,
        WorkoutSession.session_type
    ).all()

    # Build date -> activity mapping
    activity = {}
    for row in workouts:
        date_str = str(row.session_date)
        if date_str not in activity:
            activity[date_str] = {'strength': 0, 'running': 0, 'total': 0}
        if row.session_type == 'upper_body':
            activity[date_str]['strength'] += row.count
        elif row.session_type == 'running':
            activity[date_str]['running'] += row.count
        activity[date_str]['total'] += row.count

    # Build weekly data for the heatmap
    weeks_data = []
    current = start_date - timedelta(days=start_date.weekday())  # Start from Monday

    while current <= end_date:
        week = []
        for day_offset in range(7):
            day = current + timedelta(days=day_offset)
            day_str = str(day)
            day_activity = activity.get(day_str, {'total': 0, 'strength': 0, 'running': 0})
            week.append({
                'date': day_str,
                'count': day_activity['total'],
                'strength': day_activity['strength'],
                'running': day_activity['running']
            })
        weeks_data.append(week)
        current += timedelta(weeks=1)

    return jsonify({
        'weeks': weeks_data,
        'start_date': str(start_date),
        'end_date': str(end_date)
    })


@analytics_bp.route('/comparison')
@login_required
def comparison():
    """Week-over-week comparison view."""
    return render_template('analytics/comparison.html')


@analytics_bp.route('/api/week-comparison')
@login_required
def week_comparison():
    """Get this week vs last week comparison data."""
    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(weeks=1)
    last_week_end = this_week_start - timedelta(days=1)

    def get_week_stats(start_date, end_date):
        """Get stats for a specific week."""
        # Strength stats
        strength_result = db.session.query(
            func.count(func.distinct(WorkoutSession.session_id)).label('sessions'),
            func.sum(StrengthLog.sets * StrengthLog.reps * StrengthLog.weight_kg).label('volume'),
            func.count(StrengthLog.log_id).label('sets_logged')
        ).select_from(WorkoutSession).outerjoin(StrengthLog).filter(
            WorkoutSession.user_id == current_user.user_id,
            WorkoutSession.session_type == 'upper_body',
            WorkoutSession.session_date >= start_date,
            WorkoutSession.session_date <= end_date
        ).first()

        # Running stats
        running_result = db.session.query(
            func.count(func.distinct(WorkoutSession.session_id)).label('sessions'),
            func.sum(RunningLog.distance_km).label('distance'),
            func.sum(RunningLog.duration_minutes).label('duration')
        ).select_from(WorkoutSession).outerjoin(RunningLog).filter(
            WorkoutSession.user_id == current_user.user_id,
            WorkoutSession.session_type == 'running',
            WorkoutSession.session_date >= start_date,
            WorkoutSession.session_date <= end_date
        ).first()

        # Volume by muscle group
        muscle_volume = db.session.query(
            Exercise.muscle_group,
            func.sum(StrengthLog.sets * StrengthLog.reps * StrengthLog.weight_kg).label('volume')
        ).join(StrengthLog).join(WorkoutSession).filter(
            WorkoutSession.user_id == current_user.user_id,
            WorkoutSession.session_date >= start_date,
            WorkoutSession.session_date <= end_date
        ).group_by(Exercise.muscle_group).all()

        return {
            'strength': {
                'sessions': strength_result.sessions or 0,
                'volume': float(strength_result.volume or 0),
                'sets': strength_result.sets_logged or 0
            },
            'running': {
                'sessions': running_result.sessions or 0,
                'distance': float(running_result.distance or 0),
                'duration': running_result.duration or 0
            },
            'muscle_volume': {row.muscle_group: float(row.volume or 0) for row in muscle_volume}
        }

    this_week = get_week_stats(this_week_start, today)
    last_week = get_week_stats(last_week_start, last_week_end)

    # Calculate changes
    def calc_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round((current - previous) / previous * 100, 1)

    return jsonify({
        'this_week': {
            'start': str(this_week_start),
            'end': str(today),
            'stats': this_week
        },
        'last_week': {
            'start': str(last_week_start),
            'end': str(last_week_end),
            'stats': last_week
        },
        'changes': {
            'strength_volume': calc_change(this_week['strength']['volume'], last_week['strength']['volume']),
            'strength_sessions': calc_change(this_week['strength']['sessions'], last_week['strength']['sessions']),
            'running_distance': calc_change(this_week['running']['distance'], last_week['running']['distance']),
            'running_sessions': calc_change(this_week['running']['sessions'], last_week['running']['sessions'])
        }
    })


@analytics_bp.route('/api/pr-history/<int:exercise_id>')
@login_required
def pr_history(exercise_id):
    """Get PR progression history for an exercise."""
    # Get all strength logs for this exercise, ordered by date
    logs = db.session.query(
        WorkoutSession.session_date,
        func.max(StrengthLog.weight_kg).label('max_weight'),
        func.max(StrengthLog.weight_kg * (1 + StrengthLog.reps / 30.0)).label('max_1rm')
    ).join(StrengthLog).filter(
        WorkoutSession.user_id == current_user.user_id,
        StrengthLog.exercise_id == exercise_id
    ).group_by(WorkoutSession.session_date).order_by(WorkoutSession.session_date).all()

    # Track PR progression (only include new PRs)
    data = []
    current_pr = 0

    for log in logs:
        est_1rm = float(log.max_1rm) if log.max_1rm else 0
        max_weight = float(log.max_weight) if log.max_weight else 0

        data.append({
            'date': str(log.session_date),
            'max_weight': max_weight,
            'estimated_1rm': round(est_1rm, 1),
            'is_pr': est_1rm > current_pr
        })

        if est_1rm > current_pr:
            current_pr = est_1rm

    return jsonify(data)


@analytics_bp.route('/api/running-zones')
@login_required
def running_zones():
    """Get heart rate zone distribution for running."""
    # Get all runs with heart rate data
    runs = db.session.query(
        RunningLog.avg_heart_rate,
        RunningLog.max_heart_rate,
        RunningLog.duration_minutes,
        RunningLog.run_type
    ).join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id,
        RunningLog.avg_heart_rate.isnot(None)
    ).all()

    # Calculate zones based on max HR (use 220 - age estimate or user's recorded max)
    max_hr_recorded = max([r.max_heart_rate for r in runs if r.max_heart_rate], default=190)
    estimated_max_hr = max(max_hr_recorded, 190)

    # Zone definitions (% of max HR)
    zones = {
        'zone1': {'name': 'Recovery', 'min': 0.50, 'max': 0.60, 'minutes': 0, 'color': '#94a3b8'},
        'zone2': {'name': 'Aerobic', 'min': 0.60, 'max': 0.70, 'minutes': 0, 'color': '#22c55e'},
        'zone3': {'name': 'Tempo', 'min': 0.70, 'max': 0.80, 'minutes': 0, 'color': '#eab308'},
        'zone4': {'name': 'Threshold', 'min': 0.80, 'max': 0.90, 'minutes': 0, 'color': '#f97316'},
        'zone5': {'name': 'VO2 Max', 'min': 0.90, 'max': 1.00, 'minutes': 0, 'color': '#ef4444'}
    }

    # Categorize each run into zones based on avg HR
    for run in runs:
        if run.avg_heart_rate and run.duration_minutes:
            hr_pct = run.avg_heart_rate / estimated_max_hr
            for zone_key, zone in zones.items():
                if zone['min'] <= hr_pct < zone['max']:
                    zone['minutes'] += run.duration_minutes
                    break
            else:
                # If above all zones, add to zone5
                if hr_pct >= 0.90:
                    zones['zone5']['minutes'] += run.duration_minutes

    total_minutes = sum(z['minutes'] for z in zones.values())

    return jsonify({
        'zones': [{
            'zone': k,
            'name': v['name'],
            'minutes': v['minutes'],
            'percentage': round(v['minutes'] / total_minutes * 100, 1) if total_minutes > 0 else 0,
            'color': v['color'],
            'hr_range': f"{int(estimated_max_hr * v['min'])}-{int(estimated_max_hr * v['max'])} bpm"
        } for k, v in zones.items()],
        'total_minutes': total_minutes,
        'estimated_max_hr': estimated_max_hr
    })

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date
from app import db
from app.models import WorkoutSession, RunningLog

running_bp = Blueprint('running', __name__)


def parse_decimal(value):
    """Parse decimal number accepting both comma (5,54) and period (5.54)."""
    if value is None or value == '':
        return None
    try:
        # Replace comma with period for European format
        cleaned = str(value).replace(',', '.')
        return float(cleaned)
    except (ValueError, TypeError):
        return None

# Run types based on Campus.coach methodology
RUN_TYPES = [
    ('easy', 'Easy Run', 'Comfortable conversational pace'),
    ('tempo', 'Tempo Run', 'Sustained comfortably hard effort'),
    ('interval', 'Interval', 'High intensity with rest periods'),
    ('long', 'Long Run', 'Extended duration for endurance'),
    ('other', 'Other', 'Recovery, fartlek, or other runs')
]


@running_bp.route('/')
@login_required
def index():
    """List running sessions."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    sessions = WorkoutSession.query.filter_by(
        user_id=current_user.user_id,
        session_type='running'
    ).order_by(
        WorkoutSession.session_date.desc()
    ).paginate(page=page, per_page=per_page)

    # Weekly stats
    weekly_distance = RunningLog.get_weekly_mileage(current_user.user_id)

    return render_template(
        'running/index.html',
        sessions=sessions,
        weekly_distance=weekly_distance,
        run_types=RUN_TYPES
    )


@running_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_session():
    """Log a new running session."""
    if request.method == 'POST':
        session_date = request.form.get('session_date', date.today())
        run_type = request.form.get('run_type')
        distance_km = parse_decimal(request.form.get('distance_km'))
        duration_minutes = request.form.get('duration_minutes', type=int)
        avg_heart_rate = request.form.get('avg_heart_rate', type=int)
        max_heart_rate = request.form.get('max_heart_rate', type=int)
        elevation_gain = request.form.get('elevation_gain_meters', type=int)
        perceived_effort = request.form.get('perceived_effort')
        weather = request.form.get('weather_conditions')
        route_notes = request.form.get('route_notes')
        notes = request.form.get('notes')

        # Calculate pace if distance and duration provided
        avg_pace = None
        if distance_km and duration_minutes and distance_km > 0:
            avg_pace = round(duration_minutes / distance_km, 2)

        # Create session
        session = WorkoutSession(
            user_id=current_user.user_id,
            session_date=session_date,
            session_type='running',
            duration_minutes=duration_minutes,
            notes=notes
        )
        db.session.add(session)
        db.session.flush()  # Get session_id

        # Get interval details (available for any run type when toggle is on)
        has_intervals = request.form.get('has_intervals') == 'on'
        interval_details = request.form.get('interval_details') if has_intervals else None

        # Create running log
        run_log = RunningLog(
            session_id=session.session_id,
            run_type=run_type,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            avg_pace_per_km=avg_pace,
            elevation_gain_meters=elevation_gain,
            avg_heart_rate=avg_heart_rate,
            max_heart_rate=max_heart_rate,
            perceived_effort=perceived_effort,
            weather_conditions=weather,
            route_notes=route_notes,
            interval_details=interval_details
        )
        db.session.add(run_log)
        db.session.commit()

        # Check for volume spike warning
        check_and_warn_volume_spike()

        flash('Run logged successfully!', 'success')

        # Show TRIMP if HR data provided
        if run_log.trimp_score:
            flash(f'Training load (TRIMP): {run_log.trimp_score}', 'info')

        return redirect(url_for('running.view_session', session_id=session.session_id))

    return render_template('running/new_session.html', run_types=RUN_TYPES, today=date.today())


@running_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    """View a running session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('running.index'))

    run_log = session.running_logs.first()

    return render_template('running/view_session.html', session=session, run_log=run_log)


@running_bp.route('/session/<int:session_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_session(session_id):
    """Edit a running session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('running.index'))

    run_log = session.running_logs.first()

    if request.method == 'POST':
        session.session_date = request.form.get('session_date', session.session_date)
        session.notes = request.form.get('notes')

        run_log.run_type = request.form.get('run_type')
        run_log.distance_km = parse_decimal(request.form.get('distance_km'))
        run_log.duration_minutes = request.form.get('duration_minutes', type=int)
        run_log.avg_heart_rate = request.form.get('avg_heart_rate', type=int)
        run_log.max_heart_rate = request.form.get('max_heart_rate', type=int)
        run_log.elevation_gain_meters = request.form.get('elevation_gain_meters', type=int)
        run_log.perceived_effort = request.form.get('perceived_effort')
        run_log.weather_conditions = request.form.get('weather_conditions')
        run_log.route_notes = request.form.get('route_notes')
        has_intervals = request.form.get('has_intervals') == 'on'
        run_log.interval_details = request.form.get('interval_details') if has_intervals else None

        # Recalculate pace
        if run_log.distance_km and run_log.duration_minutes and run_log.distance_km > 0:
            run_log.avg_pace_per_km = round(run_log.duration_minutes / float(run_log.distance_km), 2)

        session.duration_minutes = run_log.duration_minutes

        db.session.commit()
        flash('Run updated successfully!', 'success')
        return redirect(url_for('running.view_session', session_id=session_id))

    return render_template(
        'running/edit_session.html',
        session=session,
        run_log=run_log,
        run_types=RUN_TYPES
    )


@running_bp.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    """Delete a running session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('running.index'))

    db.session.delete(session)
    db.session.commit()

    flash('Run deleted.', 'success')
    return redirect(url_for('running.index'))


@running_bp.route('/stats')
@login_required
def stats():
    """Running statistics and history."""
    history = RunningLog.get_user_running_history(current_user.user_id, limit=50)

    # Calculate stats
    total_distance = sum(float(r.distance_km or 0) for r in history)
    total_runs = len(history)
    avg_distance = total_distance / total_runs if total_runs > 0 else 0

    # Best performances
    if history:
        longest_run = max(history, key=lambda r: float(r.distance_km or 0))
        fastest_pace = min(
            (r for r in history if r.avg_pace_per_km),
            key=lambda r: float(r.avg_pace_per_km),
            default=None
        )
    else:
        longest_run = None
        fastest_pace = None

    return render_template(
        'running/stats.html',
        history=history,
        total_distance=round(total_distance, 2),
        total_runs=total_runs,
        avg_distance=round(avg_distance, 2),
        longest_run=longest_run,
        fastest_pace=fastest_pace
    )


@running_bp.route('/weekly-mileage')
@login_required
def weekly_mileage():
    """Get weekly mileage data (for AJAX/charts)."""
    from app import db
    from sqlalchemy import text

    result = db.session.execute(
        text('''
            SELECT week_start, total_distance_km, run_count, avg_trimp
            FROM weekly_running_mileage
            WHERE user_id = :user_id
            ORDER BY week_start DESC
            LIMIT 12
        '''),
        {'user_id': current_user.user_id}
    )

    data = [{
        'week': str(row.week_start),
        'distance': float(row.total_distance_km or 0),
        'runs': row.run_count,
        'avg_trimp': float(row.avg_trimp or 0)
    } for row in result]

    return jsonify(data)


def check_and_warn_volume_spike():
    """Check if current week has volume spike and show warning."""
    from app import db
    from sqlalchemy import text

    try:
        result = db.session.execute(
            text('SELECT * FROM check_running_volume_spike(:user_id) LIMIT 1'),
            {'user_id': current_user.user_id}
        ).fetchone()

        if result and result.is_spike:
            flash(
                f'Warning: Running volume increased by {result.increase_percent}% this week. '
                f'Consider reducing mileage to prevent injury.',
                'warning'
            )
    except Exception:
        pass

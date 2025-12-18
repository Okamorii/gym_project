from flask import Blueprint, Response, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import csv
import io
from app.models import WorkoutSession, StrengthLog, RunningLog, RecoveryLog, PersonalRecord

export_bp = Blueprint('export', __name__)


@export_bp.route('/')
@login_required
def index():
    """Redirect to profile with export section."""
    return redirect(url_for('auth.profile'))


@export_bp.route('/strength')
@login_required
def export_strength():
    """Export strength training data as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Date', 'Exercise', 'Muscle Group', 'Sets', 'Reps', 'Weight (kg)',
        'RPE', 'Rest (sec)', 'Volume', 'Est. 1RM', 'Session Notes'
    ])

    # Get all strength logs for user
    logs = StrengthLog.query.join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).order_by(WorkoutSession.session_date.desc()).all()

    for log in logs:
        writer.writerow([
            log.session.session_date.isoformat(),
            log.exercise.name,
            log.exercise.muscle_group or '',
            log.sets,
            log.reps,
            float(log.weight_kg) if log.weight_kg else '',
            log.rpe or '',
            log.rest_seconds or '',
            round(log.volume, 1),
            log.estimated_1rm,
            log.session.notes or ''
        ])

    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=strength_data_{timestamp}.csv'
        }
    )


@export_bp.route('/running')
@login_required
def export_running():
    """Export running data as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Date', 'Run Type', 'Distance (km)', 'Duration (min)', 'Pace (min/km)',
        'Avg HR', 'Max HR', 'Elevation (m)', 'Perceived Effort', 'Weather', 'Notes'
    ])

    # Get all running logs for user
    logs = RunningLog.query.join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).order_by(WorkoutSession.session_date.desc()).all()

    for log in logs:
        writer.writerow([
            log.session.session_date.isoformat(),
            log.run_type or '',
            float(log.distance_km) if log.distance_km else '',
            log.duration_minutes or '',
            float(log.avg_pace_per_km) if log.avg_pace_per_km else '',
            log.avg_heart_rate or '',
            log.max_heart_rate or '',
            log.elevation_gain_meters or '',
            log.perceived_effort or '',
            log.weather_conditions or '',
            log.route_notes or ''
        ])

    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=running_data_{timestamp}.csv'
        }
    )


@export_bp.route('/recovery')
@login_required
def export_recovery():
    """Export recovery data as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Date', 'Sleep Quality', 'Energy Level', 'Muscle Soreness',
        'Motivation', 'Sleep Hours', 'Notes'
    ])

    # Get all recovery logs for user
    logs = RecoveryLog.query.filter_by(
        user_id=current_user.user_id
    ).order_by(RecoveryLog.log_date.desc()).all()

    for log in logs:
        writer.writerow([
            log.log_date.isoformat(),
            log.sleep_quality or '',
            log.energy_level or '',
            log.muscle_soreness or '',
            log.motivation_score or '',
            float(log.sleep_hours) if log.sleep_hours else '',
            log.notes or ''
        ])

    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=recovery_data_{timestamp}.csv'
        }
    )


@export_bp.route('/prs')
@login_required
def export_prs():
    """Export personal records as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Date Achieved', 'Exercise', 'Record Type', 'Value', 'Notes'
    ])

    # Get all PRs for user
    prs = PersonalRecord.query.filter_by(
        user_id=current_user.user_id
    ).order_by(PersonalRecord.date_achieved.desc()).all()

    for pr in prs:
        writer.writerow([
            pr.date_achieved.isoformat() if pr.date_achieved else '',
            pr.exercise.name if pr.exercise else 'N/A',
            pr.record_type or '',
            float(pr.value) if pr.value else '',
            pr.notes or ''
        ])

    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=personal_records_{timestamp}.csv'
        }
    )


@export_bp.route('/all')
@login_required
def export_all():
    """Export all data as a single combined CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Strength section
    writer.writerow(['=== STRENGTH TRAINING DATA ==='])
    writer.writerow([
        'Date', 'Exercise', 'Muscle Group', 'Sets', 'Reps', 'Weight (kg)',
        'RPE', 'Volume', 'Est. 1RM'
    ])

    strength_logs = StrengthLog.query.join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).order_by(WorkoutSession.session_date.desc()).all()

    for log in strength_logs:
        writer.writerow([
            log.session.session_date.isoformat(),
            log.exercise.name,
            log.exercise.muscle_group or '',
            log.sets,
            log.reps,
            float(log.weight_kg) if log.weight_kg else '',
            log.rpe or '',
            round(log.volume, 1),
            log.estimated_1rm
        ])

    writer.writerow([])

    # Running section
    writer.writerow(['=== RUNNING DATA ==='])
    writer.writerow([
        'Date', 'Run Type', 'Distance (km)', 'Duration (min)', 'Pace (min/km)',
        'Avg HR', 'Max HR'
    ])

    running_logs = RunningLog.query.join(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.user_id
    ).order_by(WorkoutSession.session_date.desc()).all()

    for log in running_logs:
        writer.writerow([
            log.session.session_date.isoformat(),
            log.run_type or '',
            float(log.distance_km) if log.distance_km else '',
            log.duration_minutes or '',
            float(log.avg_pace_per_km) if log.avg_pace_per_km else '',
            log.avg_heart_rate or '',
            log.max_heart_rate or ''
        ])

    writer.writerow([])

    # Recovery section
    writer.writerow(['=== RECOVERY DATA ==='])
    writer.writerow([
        'Date', 'Sleep Quality', 'Energy Level', 'Muscle Soreness', 'Motivation'
    ])

    recovery_logs = RecoveryLog.query.filter_by(
        user_id=current_user.user_id
    ).order_by(RecoveryLog.log_date.desc()).all()

    for log in recovery_logs:
        writer.writerow([
            log.log_date.isoformat(),
            log.sleep_quality or '',
            log.energy_level or '',
            log.muscle_soreness or '',
            log.motivation_score or ''
        ])

    writer.writerow([])

    # PRs section
    writer.writerow(['=== PERSONAL RECORDS ==='])
    writer.writerow(['Date', 'Exercise', 'Record Type', 'Value'])

    prs = PersonalRecord.query.filter_by(
        user_id=current_user.user_id
    ).order_by(PersonalRecord.date_achieved.desc()).all()

    for pr in prs:
        writer.writerow([
            pr.date_achieved.isoformat() if pr.date_achieved else '',
            pr.exercise.name if pr.exercise else 'N/A',
            pr.record_type or '',
            float(pr.value) if pr.value else ''
        ])

    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=workout_tracker_export_{timestamp}.csv'
        }
    )

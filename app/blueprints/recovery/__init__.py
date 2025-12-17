from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date, datetime
from app import db
from app.models import RecoveryLog

recovery_bp = Blueprint('recovery', __name__)


@recovery_bp.route('/')
@login_required
def index():
    """List recovery logs."""
    logs = RecoveryLog.get_user_logs(current_user.user_id, limit=14)
    weekly_avg = RecoveryLog.get_weekly_average(current_user.user_id)
    today_log = RecoveryLog.get_today_log(current_user.user_id)

    return render_template(
        'recovery/index.html',
        logs=logs,
        weekly_avg=weekly_avg,
        today_log=today_log
    )


@recovery_bp.route('/log', methods=['GET', 'POST'])
@login_required
def log_recovery():
    """Log daily recovery metrics."""
    today_log = RecoveryLog.get_today_log(current_user.user_id)

    if request.method == 'POST':
        log_date_str = request.form.get('log_date')
        log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date() if log_date_str else date.today()
        sleep_quality = request.form.get('sleep_quality', type=int)
        energy_level = request.form.get('energy_level', type=int)
        muscle_soreness = request.form.get('muscle_soreness', type=int)
        motivation_score = request.form.get('motivation_score', type=int)
        notes = request.form.get('notes', '')

        # Check for existing log on this date
        existing = RecoveryLog.query.filter_by(
            user_id=current_user.user_id,
            log_date=log_date
        ).first()

        if existing:
            # Update existing log
            existing.sleep_quality = sleep_quality
            existing.energy_level = energy_level
            existing.muscle_soreness = muscle_soreness
            existing.motivation_score = motivation_score
            existing.notes = notes
            flash('Recovery log updated!', 'success')
        else:
            # Create new log
            log = RecoveryLog(
                user_id=current_user.user_id,
                log_date=log_date,
                sleep_quality=sleep_quality,
                energy_level=energy_level,
                muscle_soreness=muscle_soreness,
                motivation_score=motivation_score,
                notes=notes
            )
            db.session.add(log)
            flash('Recovery logged!', 'success')

        db.session.commit()
        return redirect(url_for('recovery.index'))

    return render_template(
        'recovery/log.html',
        today=date.today(),
        existing=today_log
    )


@recovery_bp.route('/<int:recovery_id>')
@login_required
def view_log(recovery_id):
    """View a specific recovery log."""
    log = RecoveryLog.query.get_or_404(recovery_id)

    if log.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('recovery.index'))

    return render_template('recovery/view.html', log=log)


@recovery_bp.route('/<int:recovery_id>/delete', methods=['POST'])
@login_required
def delete_log(recovery_id):
    """Delete a recovery log."""
    log = RecoveryLog.query.get_or_404(recovery_id)

    if log.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('recovery.index'))

    db.session.delete(log)
    db.session.commit()

    flash('Recovery log deleted.', 'success')
    return redirect(url_for('recovery.index'))

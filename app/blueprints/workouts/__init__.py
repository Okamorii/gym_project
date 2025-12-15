from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date
from app import db
from app.models import WorkoutSession, StrengthLog, Exercise, PersonalRecord

workouts_bp = Blueprint('workouts', __name__)


@workouts_bp.route('/')
@login_required
def index():
    """List workout sessions."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    sessions = WorkoutSession.query.filter_by(
        user_id=current_user.user_id,
        session_type='upper_body'
    ).order_by(
        WorkoutSession.session_date.desc()
    ).paginate(page=page, per_page=per_page)

    return render_template('workouts/index.html', sessions=sessions)


@workouts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_session():
    """Start a new workout session."""
    if request.method == 'POST':
        session_date = request.form.get('session_date', date.today())
        notes = request.form.get('notes', '')

        # Check for existing session today
        existing = WorkoutSession.get_today_session(
            current_user.user_id,
            session_type='upper_body'
        )

        if existing and str(existing.session_date) == str(session_date):
            flash('You already have a session for this date. Continue logging there.', 'info')
            return redirect(url_for('workouts.log_exercise', session_id=existing.session_id))

        # Create new session
        session = WorkoutSession(
            user_id=current_user.user_id,
            session_date=session_date,
            session_type='upper_body',
            notes=notes
        )
        db.session.add(session)
        db.session.commit()

        flash('Workout session started!', 'success')
        return redirect(url_for('workouts.log_exercise', session_id=session.session_id))

    exercises = Exercise.get_strength_exercises()
    return render_template('workouts/new_session.html', exercises=exercises, today=date.today())


@workouts_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    """View a workout session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    logs = session.strength_logs.all()

    return render_template('workouts/view_session.html', session=session, logs=logs)


@workouts_bp.route('/session/<int:session_id>/log', methods=['GET', 'POST'])
@login_required
def log_exercise(session_id):
    """Log exercises to a session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    if request.method == 'POST':
        exercise_id = request.form.get('exercise_id', type=int)
        sets = request.form.get('sets', type=int)
        reps = request.form.get('reps', type=int)
        weight_kg = request.form.get('weight_kg', type=float)
        rpe = request.form.get('rpe', type=int)
        rest_seconds = request.form.get('rest_seconds', type=int)

        if not all([exercise_id, sets, reps]):
            flash('Exercise, sets, and reps are required.', 'error')
        else:
            log = StrengthLog(
                session_id=session_id,
                exercise_id=exercise_id,
                sets=sets,
                reps=reps,
                weight_kg=weight_kg,
                rpe=rpe,
                rest_seconds=rest_seconds
            )
            db.session.add(log)
            db.session.commit()

            # Check for PR
            if weight_kg:
                estimated_1rm = log.estimated_1rm
                is_pr = PersonalRecord.check_and_update_pr(
                    user_id=current_user.user_id,
                    exercise_id=exercise_id,
                    record_type='1RM',
                    new_value=estimated_1rm,
                    date_achieved=session.session_date
                )
                if is_pr:
                    flash(f'New PR! Estimated 1RM: {estimated_1rm}kg', 'success')
                else:
                    flash('Set logged successfully.', 'success')

    exercises = Exercise.get_strength_exercises()
    current_logs = session.strength_logs.all()

    return render_template(
        'workouts/log_exercise.html',
        session=session,
        exercises=exercises,
        current_logs=current_logs
    )


@workouts_bp.route('/session/<int:session_id>/finish', methods=['POST'])
@login_required
def finish_session(session_id):
    """Finish a workout session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    duration = request.form.get('duration_minutes', type=int)
    notes = request.form.get('notes', '')

    session.duration_minutes = duration
    session.notes = notes
    db.session.commit()

    flash('Workout completed!', 'success')
    return redirect(url_for('workouts.view_session', session_id=session_id))


@workouts_bp.route('/exercise/<int:exercise_id>/history')
@login_required
def exercise_history(exercise_id):
    """View history for an exercise."""
    exercise = Exercise.query.get_or_404(exercise_id)
    history = StrengthLog.get_exercise_history(current_user.user_id, exercise_id, limit=20)
    best_1rm = StrengthLog.get_best_1rm(current_user.user_id, exercise_id)

    return render_template(
        'workouts/exercise_history.html',
        exercise=exercise,
        history=history,
        best_1rm=best_1rm
    )


@workouts_bp.route('/exercise/<int:exercise_id>/substitutes')
@login_required
def get_substitutes(exercise_id):
    """Get exercise substitutes with last performance (for AJAX)."""
    exercise = Exercise.query.get_or_404(exercise_id)
    substitutes = exercise.get_substitutes_with_history(current_user.user_id)

    return jsonify({
        'exercise': exercise.name,
        'substitutes': substitutes
    })


@workouts_bp.route('/exercise/<int:exercise_id>/last-performance')
@login_required
def last_performance(exercise_id):
    """Get last performance for an exercise (for AJAX)."""
    last = StrengthLog.get_last_performance(current_user.user_id, exercise_id)

    if last:
        return jsonify({
            'found': True,
            'sets': last.sets,
            'reps': last.reps,
            'weight_kg': float(last.weight_kg) if last.weight_kg else None,
            'rpe': last.rpe,
            'date': str(last.session.session_date)
        })

    return jsonify({'found': False})


@workouts_bp.route('/log/<int:log_id>/delete', methods=['POST'])
@login_required
def delete_log(log_id):
    """Delete a strength log entry."""
    log = StrengthLog.query.get_or_404(log_id)
    session = log.session

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    db.session.delete(log)
    db.session.commit()

    flash('Log entry deleted.', 'success')
    return redirect(url_for('workouts.log_exercise', session_id=session.session_id))


@workouts_bp.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    """Delete a workout session."""
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('workouts.index'))

    db.session.delete(session)
    db.session.commit()

    flash('Workout session deleted.', 'success')
    return redirect(url_for('workouts.index'))

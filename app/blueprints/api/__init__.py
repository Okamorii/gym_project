from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import date
from app import db
from app.models import (
    User, Exercise, WorkoutSession, StrengthLog,
    RunningLog, PersonalRecord, RecoveryLog
)

api_bp = Blueprint('api', __name__)


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login - returns JWT tokens."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account deactivated'}), 401

    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    user.update_last_login()

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.user_id,
            'username': user.username,
            'email': user.email
        }
    })


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def api_refresh():
    """Refresh access token."""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token})


@api_bp.route('/auth/me')
@jwt_required()
def api_me():
    """Get current user info."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.user_id,
        'username': user.username,
        'email': user.email,
        'total_workouts': user.total_workouts,
        'workouts_this_week': user.workouts_this_week
    })


# =============================================================================
# EXERCISES
# =============================================================================

@api_bp.route('/exercises')
@jwt_required()
def api_exercises():
    """Get all exercises."""
    exercise_type = request.args.get('type')

    query = Exercise.query
    if exercise_type:
        query = query.filter_by(exercise_type=exercise_type)

    exercises = query.all()

    return jsonify([{
        'id': e.exercise_id,
        'name': e.name,
        'description': e.description,
        'muscle_group': e.muscle_group,
        'type': e.exercise_type
    } for e in exercises])


@api_bp.route('/exercises/<int:exercise_id>/substitutes')
@jwt_required()
def api_exercise_substitutes(exercise_id):
    """Get exercise substitutes with last performance."""
    user_id = get_jwt_identity()
    exercise = Exercise.query.get_or_404(exercise_id)

    substitutes = exercise.get_substitutes_with_history(user_id)

    return jsonify({
        'exercise': exercise.name,
        'substitutes': substitutes
    })


@api_bp.route('/exercises/<int:exercise_id>/history')
@jwt_required()
def api_exercise_history(exercise_id):
    """Get exercise history."""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 10, type=int)

    history = StrengthLog.get_exercise_history(user_id, exercise_id, limit)

    return jsonify([{
        'date': str(log.session.session_date),
        'sets': log.sets,
        'reps': log.reps,
        'weight_kg': float(log.weight_kg) if log.weight_kg else None,
        'rpe': log.rpe,
        'estimated_1rm': log.estimated_1rm
    } for log in history])


# =============================================================================
# WORKOUTS
# =============================================================================

@api_bp.route('/workouts', methods=['GET'])
@jwt_required()
def api_list_workouts():
    """List user's workout sessions."""
    user_id = get_jwt_identity()
    session_type = request.args.get('type')
    limit = request.args.get('limit', 20, type=int)

    sessions = WorkoutSession.get_user_sessions(user_id, session_type, limit)

    return jsonify([{
        'id': s.session_id,
        'date': str(s.session_date),
        'type': s.session_type,
        'duration': s.duration_minutes,
        'notes': s.notes
    } for s in sessions])


@api_bp.route('/workouts', methods=['POST'])
@jwt_required()
def api_create_workout():
    """Create a new workout session."""
    user_id = get_jwt_identity()
    data = request.get_json()

    session = WorkoutSession(
        user_id=user_id,
        session_date=data.get('date', date.today()),
        session_type=data.get('type', 'upper_body'),
        duration_minutes=data.get('duration'),
        notes=data.get('notes')
    )

    db.session.add(session)
    db.session.commit()

    return jsonify({
        'id': session.session_id,
        'date': str(session.session_date),
        'type': session.session_type
    }), 201


@api_bp.route('/workouts/<int:session_id>')
@jwt_required()
def api_get_workout(session_id):
    """Get a workout session with logs."""
    user_id = get_jwt_identity()
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    if session.session_type == 'running':
        logs = [{
            'id': log.log_id,
            'run_type': log.run_type,
            'distance_km': float(log.distance_km) if log.distance_km else None,
            'duration': log.duration_minutes,
            'pace': float(log.avg_pace_per_km) if log.avg_pace_per_km else None,
            'avg_hr': log.avg_heart_rate,
            'trimp': log.trimp_score
        } for log in session.running_logs]
    else:
        logs = [{
            'id': log.log_id,
            'exercise_id': log.exercise_id,
            'exercise_name': log.exercise.name,
            'sets': log.sets,
            'reps': log.reps,
            'weight_kg': float(log.weight_kg) if log.weight_kg else None,
            'rpe': log.rpe,
            'estimated_1rm': log.estimated_1rm
        } for log in session.strength_logs]

    return jsonify({
        'id': session.session_id,
        'date': str(session.session_date),
        'type': session.session_type,
        'duration': session.duration_minutes,
        'notes': session.notes,
        'logs': logs
    })


@api_bp.route('/workouts/<int:session_id>/logs', methods=['POST'])
@jwt_required()
def api_add_log(session_id):
    """Add a log entry to a workout session."""
    user_id = get_jwt_identity()
    session = WorkoutSession.query.get_or_404(session_id)

    if session.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()

    if session.session_type == 'running':
        log = RunningLog(
            session_id=session_id,
            run_type=data.get('run_type'),
            distance_km=data.get('distance_km'),
            duration_minutes=data.get('duration'),
            avg_pace_per_km=data.get('pace'),
            avg_heart_rate=data.get('avg_hr'),
            max_heart_rate=data.get('max_hr'),
            perceived_effort=data.get('effort'),
            weather_conditions=data.get('weather'),
            route_notes=data.get('notes')
        )
    else:
        log = StrengthLog(
            session_id=session_id,
            exercise_id=data.get('exercise_id'),
            sets=data.get('sets'),
            reps=data.get('reps'),
            weight_kg=data.get('weight_kg'),
            rpe=data.get('rpe'),
            rest_seconds=data.get('rest')
        )

        # Check for PR
        if data.get('weight_kg'):
            is_pr = PersonalRecord.check_and_update_pr(
                user_id=user_id,
                exercise_id=data.get('exercise_id'),
                record_type='1RM',
                new_value=log.estimated_1rm,
                date_achieved=session.session_date
            )

    db.session.add(log)
    db.session.commit()

    response = {'id': log.log_id}
    if session.session_type != 'running' and data.get('weight_kg'):
        response['estimated_1rm'] = log.estimated_1rm
        response['is_pr'] = is_pr if 'is_pr' in locals() else False

    return jsonify(response), 201


# =============================================================================
# RECOVERY
# =============================================================================

@api_bp.route('/recovery', methods=['GET'])
@jwt_required()
def api_list_recovery():
    """List recovery logs."""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 14, type=int)

    logs = RecoveryLog.get_user_logs(user_id, limit)

    return jsonify([{
        'id': log.recovery_id,
        'date': str(log.log_date),
        'sleep': log.sleep_quality,
        'energy': log.energy_level,
        'soreness': log.muscle_soreness,
        'motivation': log.motivation_score,
        'overall': log.overall_recovery_score
    } for log in logs])


@api_bp.route('/recovery', methods=['POST'])
@jwt_required()
def api_add_recovery():
    """Add recovery log."""
    user_id = get_jwt_identity()
    data = request.get_json()

    log_date = data.get('date', date.today())

    # Check for existing log today
    existing = RecoveryLog.query.filter_by(
        user_id=user_id,
        log_date=log_date
    ).first()

    if existing:
        # Update existing
        existing.sleep_quality = data.get('sleep', existing.sleep_quality)
        existing.energy_level = data.get('energy', existing.energy_level)
        existing.muscle_soreness = data.get('soreness', existing.muscle_soreness)
        existing.motivation_score = data.get('motivation', existing.motivation_score)
        existing.notes = data.get('notes', existing.notes)
        db.session.commit()
        log = existing
    else:
        log = RecoveryLog(
            user_id=user_id,
            log_date=log_date,
            sleep_quality=data.get('sleep'),
            energy_level=data.get('energy'),
            muscle_soreness=data.get('soreness'),
            motivation_score=data.get('motivation'),
            notes=data.get('notes')
        )
        db.session.add(log)
        db.session.commit()

    return jsonify({
        'id': log.recovery_id,
        'date': str(log.log_date),
        'overall': log.overall_recovery_score
    }), 201


# =============================================================================
# STATS
# =============================================================================

@api_bp.route('/stats/summary')
@jwt_required()
def api_stats_summary():
    """Get user stats summary."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    weekly_distance = RunningLog.get_weekly_mileage(user_id)
    recovery_avg = RecoveryLog.get_weekly_average(user_id)

    return jsonify({
        'total_workouts': user.total_workouts,
        'workouts_this_week': user.workouts_this_week,
        'weekly_distance_km': weekly_distance,
        'recovery': recovery_avg
    })


@api_bp.route('/stats/prs')
@jwt_required()
def api_prs():
    """Get user's personal records."""
    user_id = get_jwt_identity()
    record_type = request.args.get('type')

    prs = PersonalRecord.get_user_records(user_id, record_type)

    return jsonify([{
        'id': pr.record_id,
        'exercise': pr.exercise.name if pr.exercise else None,
        'type': pr.record_type,
        'value': float(pr.value),
        'date': str(pr.date_achieved)
    } for pr in prs])

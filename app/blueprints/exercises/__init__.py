from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Exercise, ExerciseSubstitution, StrengthLog, MUSCLE_GROUPS

exercises_bp = Blueprint('exercises', __name__)


@exercises_bp.route('/')
@login_required
def index():
    """Browse exercise library."""
    # Get filter parameters
    muscle_group = request.args.get('muscle_group', '')
    exercise_type = request.args.get('type', '')
    search = request.args.get('search', '')

    # Build query
    query = Exercise.query

    if muscle_group:
        # Filter by muscle group (searches within comma-separated list)
        query = query.filter(Exercise.muscle_group.ilike(f'%{muscle_group}%'))
    if exercise_type:
        query = query.filter(Exercise.exercise_type == exercise_type)
    if search:
        query = query.filter(Exercise.name.ilike(f'%{search}%'))

    exercises = query.order_by(Exercise.muscle_group, Exercise.name).all()

    return render_template(
        'exercises/index.html',
        exercises=exercises,
        muscle_groups=MUSCLE_GROUPS,
        current_muscle_group=muscle_group,
        current_type=exercise_type,
        current_search=search
    )


@exercises_bp.route('/<int:exercise_id>')
@login_required
def view(exercise_id):
    """View exercise details."""
    exercise = Exercise.query.get_or_404(exercise_id)

    # Get user's history with this exercise
    history = StrengthLog.query.join(StrengthLog.session).filter(
        StrengthLog.exercise_id == exercise_id,
        StrengthLog.session.has(user_id=current_user.user_id)
    ).order_by(StrengthLog.created_at.desc()).limit(10).all()

    # Get best 1RM
    best_1rm = StrengthLog.get_best_1rm(current_user.user_id, exercise_id)

    # Get substitutes
    substitutes = exercise.substitutes

    return render_template(
        'exercises/view.html',
        exercise=exercise,
        history=history,
        best_1rm=best_1rm,
        substitutes=substitutes
    )


@exercises_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new exercise."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        # Get multiple muscle groups from checkboxes
        selected_muscles = request.form.getlist('muscle_groups')
        exercise_type = request.form.get('exercise_type', 'strength')
        video_url = request.form.get('video_reference_url', '').strip()

        if not name:
            flash('Exercise name is required.', 'error')
            return render_template('exercises/new.html', muscle_groups=MUSCLE_GROUPS)

        # Check for duplicate
        existing = Exercise.query.filter(Exercise.name.ilike(name)).first()
        if existing:
            flash('An exercise with this name already exists.', 'error')
            return render_template('exercises/new.html', muscle_groups=MUSCLE_GROUPS)

        exercise = Exercise(
            name=name,
            description=description or None,
            exercise_type=exercise_type,
            video_reference_url=video_url or None
        )
        exercise.muscle_groups_list = selected_muscles
        db.session.add(exercise)
        db.session.commit()

        flash(f'Exercise "{name}" created!', 'success')
        return redirect(url_for('exercises.view', exercise_id=exercise.exercise_id))

    return render_template('exercises/new.html', muscle_groups=MUSCLE_GROUPS)


@exercises_bp.route('/<int:exercise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(exercise_id):
    """Edit an exercise."""
    exercise = Exercise.query.get_or_404(exercise_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        # Get multiple muscle groups from checkboxes
        selected_muscles = request.form.getlist('muscle_groups')
        exercise_type = request.form.get('exercise_type', 'strength')
        video_url = request.form.get('video_reference_url', '').strip()

        if not name:
            flash('Exercise name is required.', 'error')
            return render_template('exercises/edit.html', exercise=exercise, muscle_groups=MUSCLE_GROUPS)

        # Check for duplicate (excluding current)
        existing = Exercise.query.filter(
            Exercise.name.ilike(name),
            Exercise.exercise_id != exercise_id
        ).first()
        if existing:
            flash('An exercise with this name already exists.', 'error')
            return render_template('exercises/edit.html', exercise=exercise, muscle_groups=MUSCLE_GROUPS)

        exercise.name = name
        exercise.description = description or None
        exercise.muscle_groups_list = selected_muscles
        exercise.exercise_type = exercise_type
        exercise.video_reference_url = video_url or None
        db.session.commit()

        flash('Exercise updated!', 'success')
        return redirect(url_for('exercises.view', exercise_id=exercise_id))

    return render_template('exercises/edit.html', exercise=exercise, muscle_groups=MUSCLE_GROUPS)


@exercises_bp.route('/<int:exercise_id>/substitutes', methods=['GET', 'POST'])
@login_required
def manage_substitutes(exercise_id):
    """Manage exercise substitutes."""
    exercise = Exercise.query.get_or_404(exercise_id)

    if request.method == 'POST':
        action = request.form.get('action')
        substitute_id = request.form.get('substitute_id', type=int)

        if action == 'add' and substitute_id:
            if substitute_id == exercise_id:
                flash('Cannot add exercise as its own substitute.', 'error')
            else:
                success = ExerciseSubstitution.add_substitution(exercise_id, substitute_id)
                if success:
                    sub = Exercise.query.get(substitute_id)
                    flash(f'Added "{sub.name}" as substitute.', 'success')
                else:
                    flash('Substitute already exists.', 'info')

        elif action == 'remove' and substitute_id:
            ExerciseSubstitution.remove_substitution(exercise_id, substitute_id)
            sub = Exercise.query.get(substitute_id)
            flash(f'Removed "{sub.name}" as substitute.', 'success')

        return redirect(url_for('exercises.manage_substitutes', exercise_id=exercise_id))

    # Get current substitutes
    current_subs = exercise.substitutes

    # Get available exercises (same muscle group, not already substitutes)
    current_sub_ids = [s.exercise_id for s in current_subs]
    available = Exercise.query.filter(
        Exercise.exercise_id != exercise_id,
        ~Exercise.exercise_id.in_(current_sub_ids) if current_sub_ids else True,
        Exercise.exercise_type == exercise.exercise_type
    ).order_by(Exercise.muscle_group, Exercise.name).all()

    return render_template(
        'exercises/substitutes.html',
        exercise=exercise,
        current_subs=current_subs,
        available=available
    )


@exercises_bp.route('/api/search')
@login_required
def api_search():
    """Search exercises (for AJAX)."""
    query = request.args.get('q', '')
    exercise_type = request.args.get('type', '')

    exercises = Exercise.query
    if query:
        exercises = exercises.filter(Exercise.name.ilike(f'%{query}%'))
    if exercise_type:
        exercises = exercises.filter(Exercise.exercise_type == exercise_type)

    exercises = exercises.limit(20).all()

    return jsonify([{
        'id': e.exercise_id,
        'name': e.name,
        'muscle_group': e.muscle_group,
        'type': e.exercise_type
    } for e in exercises])

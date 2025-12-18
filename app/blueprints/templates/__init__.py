from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import WorkoutTemplate, TemplateExercise, Exercise

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/')
@login_required
def index():
    """List all workout templates."""
    templates = WorkoutTemplate.get_user_templates(current_user.user_id)
    return render_template('templates/index.html', templates=templates)


@templates_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_template():
    """Create a new workout template."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        workout_type = request.form.get('workout_type', 'upper_body')

        if not name:
            flash('Template name is required.', 'error')
            return redirect(url_for('templates.new_template'))

        # Check for duplicate name
        existing = WorkoutTemplate.query.filter_by(
            user_id=current_user.user_id,
            name=name,
            is_active=True
        ).first()

        if existing:
            flash('A template with this name already exists.', 'error')
            return redirect(url_for('templates.new_template'))

        template = WorkoutTemplate(
            user_id=current_user.user_id,
            name=name,
            description=description,
            workout_type=workout_type
        )
        db.session.add(template)
        db.session.commit()

        flash('Template created! Now add exercises.', 'success')
        return redirect(url_for('templates.edit_template', template_id=template.template_id))

    return render_template('templates/new.html')


@templates_bp.route('/<int:template_id>')
@login_required
def view_template(template_id):
    """View a workout template."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('templates.index'))

    exercises = template.get_exercises_with_last_performance(current_user.user_id)
    return render_template('templates/view.html', template=template, exercises=exercises)


@templates_bp.route('/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    """Edit a workout template."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('templates.index'))

    if request.method == 'POST':
        template.name = request.form.get('name', template.name).strip()
        template.description = request.form.get('description', '').strip()
        template.workout_type = request.form.get('workout_type', template.workout_type)
        db.session.commit()
        flash('Template updated.', 'success')
        return redirect(url_for('templates.edit_template', template_id=template_id))

    all_exercises = Exercise.get_strength_exercises()
    template_exercises = template.exercises.all()

    return render_template(
        'templates/edit.html',
        template=template,
        template_exercises=template_exercises,
        all_exercises=all_exercises
    )


@templates_bp.route('/<int:template_id>/add-exercise', methods=['POST'])
@login_required
def add_exercise(template_id):
    """Add an exercise to a template."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        return jsonify({'error': 'Access denied'}), 403

    exercise_id = request.form.get('exercise_id', type=int)
    target_sets = request.form.get('target_sets', 3, type=int)
    target_reps = request.form.get('target_reps', 10, type=int)
    notes = request.form.get('notes', '').strip()

    if not exercise_id:
        flash('Please select an exercise.', 'error')
        return redirect(url_for('templates.edit_template', template_id=template_id))

    # Check if exercise already in template
    existing = TemplateExercise.query.filter_by(
        template_id=template_id,
        exercise_id=exercise_id
    ).first()

    if existing:
        flash('This exercise is already in the template.', 'warning')
        return redirect(url_for('templates.edit_template', template_id=template_id))

    # Get next order index
    max_order = db.session.query(db.func.max(TemplateExercise.order_index)).filter_by(
        template_id=template_id
    ).scalar() or 0

    te = TemplateExercise(
        template_id=template_id,
        exercise_id=exercise_id,
        order_index=max_order + 1,
        target_sets=target_sets,
        target_reps=target_reps,
        notes=notes
    )
    db.session.add(te)
    db.session.commit()

    flash('Exercise added to template.', 'success')
    return redirect(url_for('templates.edit_template', template_id=template_id))


@templates_bp.route('/<int:template_id>/remove-exercise/<int:te_id>', methods=['POST'])
@login_required
def remove_exercise(template_id, te_id):
    """Remove an exercise from a template."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('templates.index'))

    te = TemplateExercise.query.get_or_404(te_id)

    if te.template_id != template_id:
        flash('Invalid request.', 'error')
        return redirect(url_for('templates.edit_template', template_id=template_id))

    db.session.delete(te)
    db.session.commit()

    flash('Exercise removed from template.', 'success')
    return redirect(url_for('templates.edit_template', template_id=template_id))


@templates_bp.route('/<int:template_id>/reorder', methods=['POST'])
@login_required
def reorder_exercises(template_id):
    """Reorder exercises in a template (AJAX)."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        return jsonify({'error': 'Access denied'}), 403

    order = request.json.get('order', [])

    for idx, te_id in enumerate(order):
        te = TemplateExercise.query.get(te_id)
        if te and te.template_id == template_id:
            te.order_index = idx

    db.session.commit()
    return jsonify({'success': True})


@templates_bp.route('/<int:template_id>/duplicate', methods=['POST'])
@login_required
def duplicate_template(template_id):
    """Duplicate a template."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('templates.index'))

    new_template = template.duplicate()
    db.session.commit()

    flash(f'Template duplicated as "{new_template.name}".', 'success')
    return redirect(url_for('templates.edit_template', template_id=new_template.template_id))


@templates_bp.route('/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete a template (soft delete)."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('templates.index'))

    template.is_active = False
    db.session.commit()

    flash('Template deleted.', 'success')
    return redirect(url_for('templates.index'))


@templates_bp.route('/<int:template_id>/exercises-data')
@login_required
def get_exercises_data(template_id):
    """Get template exercises with last performance (for AJAX loading into workout)."""
    template = WorkoutTemplate.query.get_or_404(template_id)

    if template.user_id != current_user.user_id:
        return jsonify({'error': 'Access denied'}), 403

    exercises = template.get_exercises_with_last_performance(current_user.user_id)

    return jsonify({
        'template_name': template.name,
        'exercises': exercises
    })


@templates_bp.route('/api/list')
@login_required
def api_list_templates():
    """Get list of templates for dropdown (AJAX)."""
    workout_type = request.args.get('type', 'upper_body')
    templates = WorkoutTemplate.get_by_type(current_user.user_id, workout_type)

    return jsonify({
        'templates': [{
            'id': t.template_id,
            'name': t.name,
            'exercise_count': t.exercises.count()
        } for t in templates]
    })

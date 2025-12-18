from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
from app import db
from app.models import PlannedWorkout, WorkoutSession

planning_bp = Blueprint('planning', __name__)


@planning_bp.route('/')
@login_required
def index():
    """Show weekly planning view."""
    # Get week offset from query params (0 = current week)
    week_offset = request.args.get('week', 0, type=int)

    today = date.today()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)

    # Get planned workouts for this week
    plans = PlannedWorkout.get_week_plan(current_user.user_id, week_start)

    # Get actual workouts for this week
    actual_workouts = WorkoutSession.query.filter(
        WorkoutSession.user_id == current_user.user_id,
        WorkoutSession.session_date >= week_start,
        WorkoutSession.session_date <= week_end
    ).all()

    # Create a dict for easy lookup
    actual_by_date = {}
    for workout in actual_workouts:
        if workout.session_date not in actual_by_date:
            actual_by_date[workout.session_date] = []
        actual_by_date[workout.session_date].append(workout)

    # Build week data
    week_days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_plans = [p for p in plans if p.planned_date == day_date]
        day_actual = actual_by_date.get(day_date, [])

        week_days.append({
            'date': day_date,
            'day_name': day_date.strftime('%A'),
            'is_today': day_date == today,
            'is_past': day_date < today,
            'plans': day_plans,
            'actual': day_actual
        })

    # Completion stats
    stats = PlannedWorkout.get_completion_stats(current_user.user_id)

    return render_template(
        'planning/index.html',
        week_days=week_days,
        week_start=week_start,
        week_end=week_end,
        week_offset=week_offset,
        stats=stats,
        today=today
    )


@planning_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_plan():
    """Add a planned workout."""
    if request.method == 'POST':
        planned_date = request.form.get('planned_date')
        workout_type = request.form.get('workout_type')
        description = request.form.get('description', '').strip()
        target_duration = request.form.get('target_duration', type=int)
        target_distance = request.form.get('target_distance', type=float)

        if not planned_date or not workout_type:
            flash('Date and workout type are required.', 'error')
            return redirect(url_for('planning.index'))

        plan = PlannedWorkout(
            user_id=current_user.user_id,
            planned_date=planned_date,
            workout_type=workout_type,
            description=description or None,
            target_duration=target_duration,
            target_distance=target_distance
        )
        db.session.add(plan)
        db.session.commit()

        flash('Workout planned!', 'success')
        return redirect(url_for('planning.index'))

    # For GET, show quick add form
    plan_date = request.args.get('date', date.today().isoformat())
    return render_template('planning/add.html', plan_date=plan_date)


@planning_bp.route('/<int:plan_id>/complete', methods=['POST'])
@login_required
def complete_plan(plan_id):
    """Mark a plan as completed."""
    plan = PlannedWorkout.query.get_or_404(plan_id)

    if plan.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('planning.index'))

    session_id = request.form.get('session_id', type=int)
    PlannedWorkout.mark_completed(plan_id, session_id)

    flash('Marked as completed!', 'success')
    return redirect(url_for('planning.index'))


@planning_bp.route('/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """Delete a planned workout."""
    plan = PlannedWorkout.query.get_or_404(plan_id)

    if plan.user_id != current_user.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('planning.index'))

    db.session.delete(plan)
    db.session.commit()

    flash('Plan deleted.', 'success')
    return redirect(url_for('planning.index'))


@planning_bp.route('/quick-plan', methods=['POST'])
@login_required
def quick_plan():
    """Quick plan for multiple days at once."""
    data = request.get_json()

    if not data or 'plans' not in data:
        return jsonify({'error': 'No plans provided'}), 400

    for plan_data in data['plans']:
        plan = PlannedWorkout(
            user_id=current_user.user_id,
            planned_date=plan_data['date'],
            workout_type=plan_data['type'],
            description=plan_data.get('description')
        )
        db.session.add(plan)

    db.session.commit()

    return jsonify({'success': True, 'count': len(data['plans'])})


@planning_bp.route('/template/<template_name>')
@login_required
def apply_template(template_name):
    """Apply a predefined weekly template."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    templates = {
        'nippard_upper': [
            {'day': 0, 'type': 'upper_body', 'desc': 'Upper Body - Push Focus'},
            {'day': 1, 'type': 'running', 'desc': 'Easy Run'},
            {'day': 2, 'type': 'rest', 'desc': 'Rest/Recovery'},
            {'day': 3, 'type': 'upper_body', 'desc': 'Upper Body - Pull Focus'},
            {'day': 4, 'type': 'running', 'desc': 'Tempo Run'},
            {'day': 5, 'type': 'running', 'desc': 'Long Run'},
            {'day': 6, 'type': 'rest', 'desc': 'Rest/Recovery'},
        ],
        'running_focus': [
            {'day': 0, 'type': 'running', 'desc': 'Easy Run'},
            {'day': 1, 'type': 'upper_body', 'desc': 'Strength Training'},
            {'day': 2, 'type': 'running', 'desc': 'Interval Training'},
            {'day': 3, 'type': 'rest', 'desc': 'Rest/Recovery'},
            {'day': 4, 'type': 'running', 'desc': 'Tempo Run'},
            {'day': 5, 'type': 'upper_body', 'desc': 'Strength Training'},
            {'day': 6, 'type': 'running', 'desc': 'Long Run'},
        ],
        'balanced': [
            {'day': 0, 'type': 'upper_body', 'desc': 'Strength Training'},
            {'day': 1, 'type': 'running', 'desc': 'Easy Run'},
            {'day': 2, 'type': 'rest', 'desc': 'Active Recovery'},
            {'day': 3, 'type': 'upper_body', 'desc': 'Strength Training'},
            {'day': 4, 'type': 'running', 'desc': 'Tempo Run'},
            {'day': 5, 'type': 'running', 'desc': 'Long Run'},
            {'day': 6, 'type': 'rest', 'desc': 'Rest Day'},
        ]
    }

    if template_name not in templates:
        flash('Template not found.', 'error')
        return redirect(url_for('planning.index'))

    # Clear existing plans for the week
    week_end = week_start + timedelta(days=6)
    PlannedWorkout.query.filter(
        PlannedWorkout.user_id == current_user.user_id,
        PlannedWorkout.planned_date >= week_start,
        PlannedWorkout.planned_date <= week_end
    ).delete()

    # Apply template
    for item in templates[template_name]:
        plan = PlannedWorkout(
            user_id=current_user.user_id,
            planned_date=week_start + timedelta(days=item['day']),
            workout_type=item['type'],
            description=item['desc']
        )
        db.session.add(plan)

    db.session.commit()

    flash(f'Applied {template_name.replace("_", " ").title()} template!', 'success')
    return redirect(url_for('planning.index'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
import calendar
from app import db
from app.models import PlannedWorkout, WorkoutSession, WorkoutTemplate

planning_bp = Blueprint('planning', __name__)


@planning_bp.route('/')
@login_required
def index():
    """Show monthly calendar planning view."""
    # Get month/year from query params
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    # Handle month overflow
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1

    # Get first and last day of month
    first_day = date(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = date(year, month, last_day_num)

    # Get start of calendar (may include days from previous month)
    cal_start = first_day - timedelta(days=first_day.weekday())
    # Get end of calendar (may include days from next month)
    cal_end = last_day + timedelta(days=(6 - last_day.weekday()))

    # Get all plans for the visible calendar range
    plans = PlannedWorkout.query.filter(
        PlannedWorkout.user_id == current_user.user_id,
        PlannedWorkout.planned_date >= cal_start,
        PlannedWorkout.planned_date <= cal_end
    ).all()

    # Get actual workouts for the visible range
    actual_workouts = WorkoutSession.query.filter(
        WorkoutSession.user_id == current_user.user_id,
        WorkoutSession.session_date >= cal_start,
        WorkoutSession.session_date <= cal_end
    ).all()

    # Create lookup dicts
    plans_by_date = {}
    for plan in plans:
        if plan.planned_date not in plans_by_date:
            plans_by_date[plan.planned_date] = []
        plans_by_date[plan.planned_date].append(plan)

    actual_by_date = {}
    for workout in actual_workouts:
        if workout.session_date not in actual_by_date:
            actual_by_date[workout.session_date] = []
        actual_by_date[workout.session_date].append(workout)

    # Build calendar weeks
    calendar_weeks = []
    current_date = cal_start
    while current_date <= cal_end:
        week = []
        for _ in range(7):
            day_plans = plans_by_date.get(current_date, [])
            day_actual = actual_by_date.get(current_date, [])

            week.append({
                'date': current_date,
                'day': current_date.day,
                'is_today': current_date == today,
                'is_current_month': current_date.month == month,
                'is_past': current_date < today,
                'plans': day_plans,
                'actual': day_actual
            })
            current_date += timedelta(days=1)
        calendar_weeks.append(week)

    # Get user's workout templates for the quick-add dropdown
    templates = WorkoutTemplate.get_user_templates(current_user.user_id)

    # Completion stats
    stats = PlannedWorkout.get_completion_stats(current_user.user_id)

    # Month navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render_template(
        'planning/index.html',
        calendar_weeks=calendar_weeks,
        year=year,
        month=month,
        month_name=calendar.month_name[month],
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        stats=stats,
        today=today,
        templates=templates
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
        template_id = request.form.get('template_id', type=int)

        if not planned_date or not workout_type:
            flash('Date and workout type are required.', 'error')
            return redirect(url_for('planning.index'))

        plan = PlannedWorkout(
            user_id=current_user.user_id,
            planned_date=planned_date,
            workout_type=workout_type,
            description=description or None,
            target_duration=target_duration,
            target_distance=target_distance,
            template_id=template_id if template_id else None
        )
        db.session.add(plan)
        db.session.commit()

        flash('Workout planned!', 'success')

        # Redirect back to the same month view
        plan_dt = date.fromisoformat(planned_date)
        return redirect(url_for('planning.index', year=plan_dt.year, month=plan_dt.month))

    # For GET, show quick add form
    plan_date = request.args.get('date', date.today().isoformat())
    templates = WorkoutTemplate.get_user_templates(current_user.user_id)
    return render_template('planning/add.html', plan_date=plan_date, templates=templates)


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

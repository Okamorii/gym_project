"""Tests for Flask routes/blueprints."""
import pytest
from datetime import date
from flask import url_for


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data

    def test_register_page_loads(self, client):
        """Test register page loads correctly."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data or b'register' in response.data

    def test_login_with_valid_credentials(self, client, sample_user, app):
        """Test login with valid credentials."""
        with app.app_context():
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword123'
            }, follow_redirects=True)

            # Should redirect to dashboard on success
            assert response.status_code == 200

    def test_login_with_invalid_credentials(self, client, sample_user, app):
        """Test login with invalid credentials."""
        with app.app_context():
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'wrongpassword'
            })

            # Should stay on login page or show error
            assert response.status_code in [200, 302]

    def test_logout(self, authenticated_client, app):
        """Test logout functionality."""
        with app.app_context():
            response = authenticated_client.get('/logout', follow_redirects=True)
            assert response.status_code == 200


class TestDashboardRoutes:
    """Tests for dashboard routes."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard redirects when not logged in."""
        response = client.get('/')
        # Should redirect to login
        assert response.status_code == 302

    def test_dashboard_loads_when_authenticated(self, authenticated_client, app):
        """Test dashboard loads for authenticated user."""
        with app.app_context():
            response = authenticated_client.get('/')
            assert response.status_code == 200


class TestWorkoutRoutes:
    """Tests for workout routes."""

    def test_workouts_index_requires_login(self, client):
        """Test workouts page redirects when not logged in."""
        response = client.get('/workouts/')
        assert response.status_code == 302

    def test_new_session_page_loads(self, authenticated_client, app):
        """Test new workout session page loads."""
        with app.app_context():
            response = authenticated_client.get('/workouts/new')
            assert response.status_code == 200


class TestRunningRoutes:
    """Tests for running routes."""

    def test_running_index_requires_login(self, client):
        """Test running page redirects when not logged in."""
        response = client.get('/running/')
        assert response.status_code == 302

    def test_new_run_page_loads(self, authenticated_client, app):
        """Test new run session page loads."""
        with app.app_context():
            response = authenticated_client.get('/running/new')
            assert response.status_code == 200


class TestRecoveryRoutes:
    """Tests for recovery routes."""

    def test_recovery_page_loads(self, authenticated_client, app):
        """Test recovery page loads."""
        with app.app_context():
            response = authenticated_client.get('/recovery/')
            assert response.status_code == 200


class TestAnalyticsRoutes:
    """Tests for analytics routes."""

    def test_analytics_index_loads(self, authenticated_client, app):
        """Test analytics index loads."""
        with app.app_context():
            response = authenticated_client.get('/analytics/')
            assert response.status_code == 200

    def test_activity_heatmap_api(self, authenticated_client, app):
        """Test activity heatmap API endpoint."""
        with app.app_context():
            response = authenticated_client.get('/analytics/api/activity-heatmap')
            assert response.status_code == 200
            assert response.content_type == 'application/json'

    def test_workout_frequency_api(self, authenticated_client, app):
        """Test workout frequency API endpoint."""
        with app.app_context():
            response = authenticated_client.get('/analytics/api/workout-frequency')
            assert response.status_code == 200
            assert response.content_type == 'application/json'


class TestBodyRoutes:
    """Tests for body measurement routes."""

    def test_body_index_loads(self, authenticated_client, app):
        """Test body measurements page loads."""
        with app.app_context():
            response = authenticated_client.get('/body/')
            assert response.status_code == 200

    def test_add_measurement_page_loads(self, authenticated_client, app):
        """Test add measurement page loads."""
        with app.app_context():
            response = authenticated_client.get('/body/add')
            assert response.status_code == 200

    def test_add_measurement(self, authenticated_client, app):
        """Test adding a body measurement."""
        with app.app_context():
            response = authenticated_client.post('/body/add', data={
                'measurement_date': str(date.today()),
                'weight_kg': '75.5',
                'body_fat_pct': '15',
                'chest_cm': '100',
                'waist_cm': '82'
            }, follow_redirects=True)
            assert response.status_code == 200


class TestExerciseRoutes:
    """Tests for exercise routes."""

    def test_exercises_index_loads(self, authenticated_client, app, sample_exercises):
        """Test exercises page loads."""
        with app.app_context():
            response = authenticated_client.get('/exercises/')
            assert response.status_code == 200


class TestPlanningRoutes:
    """Tests for planning routes."""

    def test_planning_index_loads(self, authenticated_client, app):
        """Test planning page loads."""
        with app.app_context():
            response = authenticated_client.get('/planning/')
            assert response.status_code == 200


class TestTemplateRoutes:
    """Tests for template routes."""

    def test_templates_index_loads(self, authenticated_client, app):
        """Test templates page loads."""
        with app.app_context():
            response = authenticated_client.get('/templates/')
            assert response.status_code == 200

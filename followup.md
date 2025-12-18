# Workout Tracker - Development Followup

## Project Overview

A Flask-based workout tracking application for monitoring upper body strength training (2x/week, Jeff Nippard's program) and running sessions (4x/week, Campus.coach methodology). Runs on PostgreSQL 16 with Python 3.13.

---

## What Has Been Completed

### 1. Database Layer (PostgreSQL)

**File:** `setup_database.sql`

**Tables Created:**
- `users` - User authentication with password hashing
- `exercises` - Exercise library (15 strength + 4 cardio exercises pre-seeded)
- `workout_sessions` - Session records (date, type, duration, notes)
- `strength_logs` - Sets, reps, weight, RPE, rest time per exercise
- `running_logs` - Distance, duration, pace, heart rate, run type, weather
- `personal_records` - PRs for lifts and running
- `recovery_logs` - Sleep, energy, soreness, motivation (1-10 scales)
- `exercise_substitutions` - Bidirectional exercise substitutes

**Functions Created:**
- `calculate_1rm(weight, reps)` - Epley formula for estimated 1RM
- `calculate_trimp(duration, avg_hr, max_hr)` - Training impulse score
- `calculate_volume(sets, reps, weight)` - Volume calculation
- `check_running_volume_spike(user_id)` - Detects >10% mileage increase
- `check_strength_volume_spike(user_id)` - Detects >20% volume increase
- `calculate_workout_streak(user_id)` - Consecutive workout days
- `get_exercise_substitutes(exercise_id, user_id)` - Substitutes with history
- `add_substitution(ex1, ex2)` - Bidirectional substitution helper

**Views Created:**
- `strength_logs_with_1rm` - Strength logs with calculated 1RM
- `running_logs_with_trimp` - Running logs with TRIMP scores
- `weekly_running_mileage` - Aggregated weekly running stats
- `weekly_strength_volume` - Aggregated weekly volume by muscle group
- `user_dashboard_summary` - User stats overview
- `auto_detected_prs` - Auto-detected strength PRs
- `running_prs` - Running PRs (5K, 10K, longest, best pace)
- `recovery_trends` - Weekly recovery averages

---

### 2. Flask Application Structure

```
/app
  __init__.py              # App factory, extensions (SQLAlchemy, Login, JWT)
  config.py                # Configuration settings
  /models
    __init__.py            # Model exports
    user.py                # User model with auth methods
    exercise.py            # Exercise model with substitutes, MUSCLE_GROUPS
    workout.py             # WorkoutSession, StrengthLog, RunningLog
    records.py             # PersonalRecord model
    recovery.py            # RecoveryLog model
    planning.py            # PlannedWorkout model
  /blueprints
    /auth                  # Login (username), register, logout, profile
    /dashboard             # Main dashboard view
    /workouts              # Strength training logging with PR detection
    /running               # Running session logging
    /recovery              # Recovery logging
    /exercises             # Exercise library browser
    /analytics             # Charts and progress visualization
    /planning              # Weekly workout planning
    /export                # CSV data export
    /api                   # REST API with JWT authentication
  /templates
    base.html              # Base template with nav, PR celebration modal
    /auth
      login.html           # Username-based login
      register.html
      profile.html         # Includes data export section
    /dashboard
      index.html
    /workouts
      index.html
      new_session.html
      log_exercise.html    # With volume spike alerts
      view_session.html
    /running
      index.html
      new_session.html
      view_session.html
      edit_session.html
      stats.html
    /recovery
      index.html
      log.html
      view.html
    /exercises
      index.html
      view.html
      new.html             # Multiple muscle checkbox selection
      edit.html
      substitutes.html
    /planning
      index.html           # Weekly calendar view
      add.html
    /analytics
      index.html
      strength.html
      running.html
  /static
    /css
      style.css            # Mobile-first responsive CSS
    /js
      app.js               # Validation, PR celebration, mobile nav
    manifest.json          # PWA manifest
    sw.js                  # Service worker
```

---

### 3. Blueprints Implemented

#### Auth Blueprint (`/auth`)
- `GET/POST /login` - User login with remember me
- `GET/POST /register` - User registration with validation
- `GET /logout` - Logout
- `GET/POST /profile` - Profile management, password change

#### Dashboard Blueprint (`/dashboard`)
- `GET /` - Main dashboard with stats overview

#### Workouts Blueprint (`/workouts`)
- `GET /` - List strength sessions
- `GET/POST /new` - Start new strength session
- `GET /session/<id>` - View session
- `GET/POST /session/<id>/log` - Log exercise to session

#### Running Blueprint (`/running`)
- `GET /` - List running sessions with weekly mileage
- `GET/POST /new` - Log new running session
- `GET /session/<id>` - View run details
- `GET/POST /session/<id>/edit` - Edit run
- `POST /session/<id>/delete` - Delete run
- `GET /stats` - Running statistics
- `GET /weekly-mileage` - Weekly mileage data (JSON)

#### Analytics Blueprint (`/analytics`)
- `GET /` - Analytics dashboard
- `GET /strength` - Strength analytics with PRs, exercise progress
- `GET /running` - Running analytics with charts
- `GET /api/strength-volume` - Weekly volume data (JSON)
- `GET /api/exercise-progress/<id>` - Exercise progress data (JSON)
- `GET /api/running-progress` - Running progress data (JSON)
- `GET /api/run-type-distribution` - Run type distribution (JSON)
- `GET /api/muscle-group-volume` - Volume by muscle group (JSON)
- `GET /api/recovery-trends` - Recovery trends data (JSON)
- `GET /api/workout-frequency` - Workout frequency by day (JSON)
- `GET /api/pr-timeline` - PR timeline data (JSON)

#### API Blueprint (`/api`)
- `POST /auth/login` - JWT login
- `POST /auth/refresh` - Refresh JWT token
- `GET /auth/me` - Current user info
- `GET /exercises` - List exercises
- `GET /exercises/<id>/substitutes` - Exercise substitutes
- `GET /exercises/<id>/history` - Exercise history
- `GET /workouts` - List workouts
- `POST /workouts` - Create workout
- `GET /workouts/<id>` - Get workout with logs
- `POST /workouts/<id>/logs` - Add log entry
- `GET /recovery` - List recovery logs
- `POST /recovery` - Add/update recovery log
- `GET /stats/summary` - Stats summary
- `GET /stats/prs` - Personal records

---

### 4. Frontend (Templates & CSS)

**Base Template Features:**
- Mobile-first responsive design
- Top navbar (desktop) + bottom nav (mobile)
- Flash message display
- Dark theme (CSS custom properties)

**CSS Includes:**
- Navigation (navbar, bottom nav, hamburger menu)
- Cards and containers
- Forms (inputs, selects, textareas)
- Buttons (primary, secondary, success, danger)
- Stats grids and stat items
- PR lists and workout lists
- Run type badges (color-coded by type)
- Effort badges
- Analytics cards with icons
- Chart containers
- Profile page styling
- Pagination
- Flash messages (success, error, warning, info)
- Responsive breakpoints

---

### 5. Bug Fixes Applied (Previous Sessions)

1. **Template Path Fixes in Running Blueprint:**
   - `index()` - Changed `'index.html'` to `'running/index.html'`
   - `edit_session()` - Changed `'edit_session.html'` to `'running/edit_session.html'`
   - `stats()` - Changed `'stats.html'` to `'running/stats.html'`

2. **Template Path Fixes in Analytics Blueprint:**
   - `strength_analytics()` - Changed `'strength.html'` to `'analytics/strength.html'`

3. **Missing Templates Created:**
   - `running/view_session.html` - View run details
   - `running/edit_session.html` - Edit run form
   - `running/stats.html` - Running statistics page
   - `analytics/index.html` - Analytics dashboard
   - `analytics/strength.html` - Strength analytics with Chart.js
   - `analytics/running.html` - Running analytics with Chart.js
   - `auth/profile.html` - User profile management

4. **CSS Additions:**
   - Page header styling
   - Analytics navigation cards
   - PR list layout (flexbox)
   - Stats list items
   - Chart container sizing
   - Run type badges (easy, tempo, interval, long, other)
   - Effort badges
   - Session view detail sections
   - Profile page info rows
   - Empty states and loading indicators
   - Pagination styling

---

### 6. Features Completed (December 17, 2025)

#### 6.1 Missing Workout View Template
- Created `workouts/view_session.html` with session details, exercise logs, stats grid, and action buttons

#### 6.2 Dashboard Bug Fix
- Fixed `now()` undefined error by passing `datetime.now()` to template context
- Changed template from `now()` function call to `now` variable

#### 6.3 Recovery Logging UI
**New Blueprint:** `/app/blueprints/recovery/__init__.py`
- `GET /recovery/` - List recovery logs with 7-day averages
- `GET/POST /recovery/log` - Log daily recovery with slider inputs
- `GET /recovery/<id>` - View recovery log details
- `POST /recovery/<id>/delete` - Delete recovery log

**New Templates:**
- `recovery/index.html` - Recovery dashboard with weekly stats
- `recovery/log.html` - Form with sliders (Sleep, Energy, Soreness, Motivation 1-10)
- `recovery/view.html` - Detailed view with progress bars

**Features:**
- Slider-based input for better mobile UX
- Auto-update existing log if same date
- Overall recovery score calculation
- Color-coded scores (good/moderate/poor)

#### 6.4 Exercise Library Browser
**New Blueprint:** `/app/blueprints/exercises/__init__.py`
- `GET /exercises/` - Browse & filter exercises
- `GET /exercises/<id>` - View exercise details with history
- `GET/POST /exercises/new` - Create new exercises
- `GET/POST /exercises/<id>/edit` - Edit exercises
- `GET/POST /exercises/<id>/substitutes` - Manage substitutes
- `GET /exercises/api/search` - AJAX search endpoint

**New Templates:**
- `exercises/index.html` - Filterable list grouped by muscle
- `exercises/view.html` - Details, personal stats, history, substitutes
- `exercises/new.html` - Create form with datalist suggestions
- `exercises/edit.html` - Edit form
- `exercises/substitutes.html` - Manage substitute relationships

**Features:**
- Filter by muscle group, type (strength/cardio), or search
- Personal best 1RM display
- Recent workout history per exercise
- Bidirectional substitute management

#### 6.5 Analytics Visualization Enhancement
**Updated Templates with Chart.js:**

`analytics/index.html`:
- Workout frequency chart by day of week
- Recovery trends line chart
- Recent PRs list
- Dark theme styling

`analytics/strength.html`:
- Exercise progress dual-line chart (Est. 1RM + Weight)
- Mini stats (Best 1RM, Latest 1RM, Progress %)
- Muscle group volume doughnut chart
- Weekly volume trend stacked bar chart

`analytics/running.html`:
- Date range filter (4/8/12 weeks)
- Summary stats (total km, runs, avg, hours)
- Weekly mileage bar chart
- Run type distribution doughnut
- Training load (TRIMP) trend chart

**CSS Additions:**
- Chart containers with fixed heights
- Date range filter buttons
- Mini stats row with positive/negative colors

#### 6.6 PWA Features (Progressive Web App)
**manifest.json** (`/static/manifest.json`):
- App name, icons (72px-512px), theme colors
- Standalone display mode
- App shortcuts for quick logging

**Service Worker** (`/static/sw.js`):
- Static asset caching
- Network-first for HTML, cache-first for static
- Offline fallback page
- Background sync support

**Offline Page** (`/templates/offline.html`):
- User-friendly offline message
- Retry button

**iOS Support:**
- `apple-mobile-web-app-capable`
- `apple-touch-icon`
- Status bar styling

**Base Template Updates:**
- Service worker registration
- PWA meta tags
- Viewport with `viewport-fit=cover`

---

## Next Steps To Do

### ~~Phase 1: Exercise Library~~ ✅ COMPLETED
~~1. **Exercise Library Browser** - View all exercises with descriptions, muscle groups, video links~~
~~2. **Exercise Creation UI** - Form to add new exercises to the library~~
~~3. **Exercise Substitutes Management** - UI to define equivalent/replacement exercises for each exercise~~
~~4. **Exercise Edit/Delete** - Ability to modify or remove exercises~~

### ~~Phase 2: Core Functionality Completion~~ ✅ COMPLETED
~~5. **Dashboard Content** - Wire up actual stats, quick actions, PR feed, weekly progress display~~
~~6. **Workout Session View/Edit** - Create `view_session.html` for strength workouts~~
~~7. **Recovery Logging UI** - Web interface to log daily sleep, energy, soreness, motivation~~
~~8. **PR Detection & Celebration** - Show PR notifications/badges when beating records during logging~~

### ~~Phase 3: Alerts & UX Improvements~~ ✅ COMPLETED
~~9. **Volume Spike Alerts** - Display warnings prominently when running >10% or lifting >20% volume increase~~
~~10. **Mobile Nav Toggle** - Implement hamburger menu functionality in app.js~~
~~11. **PWA Setup** - Create manifest.json and service worker for offline capability and home screen install~~

### ~~Phase 4: Planning & Data Management~~ ✅ COMPLETED
~~12. **Weekly Planning** - Template and plan upcoming workouts~~
~~13. **Data Export** - CSV export for backup~~
~~14. **Error Validation UI** - Client-side validation, unusual entry warnings (e.g., 400kg bench press)~~
~~15. **Chart Improvements** - More interactive charts, date range filters~~

### ~~Phase 5: Docker Containerization~~ ✅ COMPLETED
~~16. **Dockerfile** - Create Docker image for the Flask app~~
~~17. **docker-compose.yml** - Orchestrate Flask + PostgreSQL containers~~
~~18. **Docker Volumes** - Persist database data and uploads~~
~~19. **Environment Variables** - Move secrets to `.env` file for Docker~~
~~20. **Docker Documentation** - Update README with Docker commands~~

---

## Remaining Tasks (Priority Order)

**All core tasks completed!** The application is fully functional with Docker deployment.

---

## Future Enhancements (Phase 6)

### High Priority
~~21. **Workout Templates** - Save and reuse workout structures (e.g., "Upper Body Day A" with pre-filled exercises, sets, reps)~~ ✅ COMPLETED
22. **Goal Setting** - Set targets (e.g., "Bench 100kg", "Run 5K in 25min") with progress tracking and visual indicators
~~23. **Rest Timer** - Built-in countdown timer between sets with manual override option~~ ✅ COMPLETED

### Medium Priority
24. **Body Measurements** - Track weight, body fat %, chest, arms, waist measurements over time
25. **Workout Consistency Calendar** - GitHub-style heatmap showing workout days
26. **Fatigue/Readiness Score** - Combine recovery metrics (sleep, soreness, energy) into single daily score
27. **Photo Progress** - Upload progress photos linked to dates
28. **Running Pace Zones** - Show time spent in each heart rate/pace zone

### Low Priority
29. **Dark/Light Theme Toggle** - User preference for theme switching
30. **Password Reset** - Email-based password recovery flow
31. **Weekly Summary Email** - Automated weekly recap of workouts, PRs, and stats
32. **Comparison Analytics** - "This month vs last month" side-by-side comparison view

### Quick Fixes
- **Fix Docker healthcheck** - Container shows "unhealthy" despite working
- **Add favicon** - Missing favicon causes 404 errors in browser

---

## Completion Status

| Feature | Status |
|---------|--------|
| Database Schema | ✅ Complete |
| Flask App Structure | ✅ Complete |
| Auth (Login/Register/Profile) | ✅ Complete |
| Dashboard | ✅ Complete |
| Strength Workouts | ✅ Complete |
| Running Sessions | ✅ Complete |
| Recovery Logging | ✅ Complete |
| Exercise Library | ✅ Complete |
| Analytics & Charts | ✅ Complete |
| PWA (Installable App) | ✅ Complete |
| Docker Deployment | ✅ Complete |
| REST API (JWT) | ✅ Complete |
| Multiple Muscle Groups | ✅ Complete |
| PR Detection UI | ✅ Complete |
| Volume Spike Alerts | ✅ Complete |
| Mobile Nav Toggle | ✅ Complete |
| Weekly Planning | ✅ Complete |
| Data Export | ✅ Complete |
| Input Validation | ✅ Complete |

**Overall: 100% Complete** (Core Features)

---

### 7. Features Completed (December 17, 2025 - Session 2)

#### 7.1 Multiple Muscle Groups per Exercise
- Updated `exercise.py` model with `MUSCLE_GROUPS` constant and helper properties
- Changed `muscle_group` column to VARCHAR(200) to store comma-separated values
- Created checkbox-based UI for selecting multiple muscles per exercise
- Seeded existing exercises with appropriate multiple muscle groups
- Templates updated: `exercises/new.html`, `exercises/edit.html`, `exercises/view.html`

#### 7.2 Login Changed to Username
- Modified auth blueprint to use username instead of email for login
- Updated `login.html` template
- Updated API login endpoint

#### 7.3 PR Detection & Celebration Modal
- Added PR celebration modal to `base.html` with confetti animation
- Added `showPrCelebration()`, `closePrModal()`, `createConfetti()` functions to `app.js`
- Modified workouts blueprint to capture previous PR value and trigger celebration
- Added `is_pr` property to StrengthLog model
- PR badges now display in workout log views

#### 7.4 Volume Spike Alerts UI
- Enhanced dashboard template with improved alert display
- Added volume spike banner to `log_exercise.html`
- Added `check_strength_volume_spike()` function to workouts blueprint
- CSS styling for alerts with dismiss functionality

#### 7.5 Mobile Navigation Toggle
- Implemented hamburger menu with JavaScript in `app.js`
- Compact dropdown menu (right-aligned, not full-page)
- Hamburger-to-X animation on toggle
- Click-outside-to-close functionality

#### 7.6 Weekly Planning Feature
**New Model:** `app/models/planning.py`
- `PlannedWorkout` model with user_id, planned_date, workout_type, description, completed

**New Blueprint:** `app/blueprints/planning/__init__.py`
- `GET /planning/` - Weekly calendar view
- `GET/POST /planning/add` - Add planned workout
- `POST /planning/<id>/toggle` - Toggle completed status
- `POST /planning/<id>/delete` - Delete planned workout

**Templates:**
- `planning/index.html` - Week calendar with workout indicators
- `planning/add.html` - Form with date, type, description

**Features:**
- Navigate between weeks
- Quick templates (Nippard Upper, Running Focus, Balanced)
- Click dates to log completed workouts

#### 7.7 Data Export (CSV)
**New Blueprint:** `app/blueprints/export/__init__.py`
- `GET /export/strength` - Export strength training data
- `GET /export/running` - Export running data
- `GET /export/recovery` - Export recovery logs
- `GET /export/prs` - Export personal records
- `GET /export/all` - Export all data combined

**Profile Integration:**
- Added export section to `auth/profile.html`
- Buttons for individual and combined exports

#### 7.8 Input Validation UI
**JavaScript Validation System (`app.js`):**
- `validationRules` object with limits for strength, running, recovery inputs
- Hard limits (block submit) and soft warnings (confirm dialog)
- Visual feedback with `.input-error` and `.input-warning` classes
- `validateInput()`, `showInputError()`, `showInputWarning()`, `clearInputFeedback()`
- `setupFormValidation()` auto-initializes on page load

**Validation Limits:**
- Weight: 0-500kg (warning >300kg)
- Sets: 1-20 (warning >10)
- Reps: 1-100 (warning >30)
- RPE: 1-10
- Distance: 0-100km (warning >50km)
- Heart Rate: 40-220 (warning <60 or >200)

---

## How to Run

### Docker Deployment (Recommended)

Docker provides the easiest deployment method with automatic database setup and container orchestration.

**Prerequisites:**
- Docker Engine 20.10+
- Docker Compose v2.0+

**Quick Start:**
```bash
# Clone and navigate to project
cd /root/gym

# Copy environment file and customize
cp .env.example .env
nano .env  # Edit secrets

# Build and start containers
docker compose up -d

# View logs
docker compose logs -f

# App will be available at http://192.168.0.117:5000
```

**Using Makefile Commands:**
```bash
# Show all available commands
make help

# Build images
make build

# Start containers
make up

# Stop containers
make down

# View logs
make logs

# Open shell in web container
make shell

# Connect to database
make db-shell

# Backup database
make backup

# Restore database
make restore FILE=backups/backup_XXXXXX.sql

# Clean up everything (including data)
make clean
```

**Docker Files:**
| File | Purpose |
|------|---------|
| `Dockerfile` | Flask app image definition |
| `docker-compose.yml` | Multi-container orchestration |
| `docker-entrypoint.sh` | Startup script with DB init |
| `.dockerignore` | Files excluded from image |
| `.env.example` | Environment template |
| `Makefile` | Convenience commands |

**Environment Variables:**
```bash
# Flask
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
POSTGRES_USER=workout
POSTGRES_PASSWORD=workout123
POSTGRES_DB=workout_tracker
```

**Volumes:**
- `workout_postgres_data` - PostgreSQL data persistence
- `workout_uploads_data` - File uploads (if any)

**Container Architecture:**
```
┌─────────────────────────────────────────┐
│           workout_network               │
│  ┌─────────────┐    ┌─────────────────┐ │
│  │  workout_db │◄───│  workout_app    │ │
│  │  (postgres) │    │  (flask/gunicorn)│ │
│  │  :5432      │    │  :5000          │ │
│  └─────────────┘    └─────────────────┘ │
└─────────────────────────────────────────┘
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `setup_database.sql` | Complete database schema |
| `app/__init__.py` | Flask app factory |
| `app/config.py` | Configuration |
| `app/models/*.py` | SQLAlchemy models |
| `app/blueprints/*/` | Route handlers |
| `app/templates/base.html` | Base template |
| `app/static/css/style.css` | All styles |
| `run.py` | App entry point |
| `Dockerfile` | Docker image definition |
| `docker-compose.yml` | Container orchestration |
| `Makefile` | Docker convenience commands |
| `project.md` | Original requirements |
| `CLAUDE.md` | Claude Code instructions |

// ============================================
// WORKOUT TRACKER - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Flash message close buttons
    document.querySelectorAll('.flash-close').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.remove();
        });
    });

    // Auto-dismiss flash messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.flash').forEach(flash => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 300);
        });
    }, 5000);

    // Mobile nav toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });

        // Close menu when clicking a non-dropdown link
        navMenu.querySelectorAll('.nav-link:not(.nav-dropdown-toggle)').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });

        // Close menu when clicking dropdown item
        navMenu.querySelectorAll('.nav-dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });

        // Mobile dropdown toggles
        navMenu.querySelectorAll('.nav-dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const dropdown = toggle.closest('.nav-dropdown');

                // On mobile, toggle dropdown visibility
                if (window.innerWidth < 768) {
                    // Close other dropdowns
                    navMenu.querySelectorAll('.nav-dropdown').forEach(d => {
                        if (d !== dropdown) d.classList.remove('active');
                    });
                    dropdown.classList.toggle('active');
                }
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
                // Also close all dropdowns
                navMenu.querySelectorAll('.nav-dropdown').forEach(d => {
                    d.classList.remove('active');
                });
            }
        });
    }

    // Form validation feedback
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
            }
        });
    });

    // Delete confirmations
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this?')) {
                e.preventDefault();
            }
        });
    });

    // Interval Builder Toggle and Preview
    const hasIntervalsToggle = document.getElementById('has_intervals');
    const intervalBuilder = document.getElementById('interval_builder');
    const intervalPreview = document.getElementById('interval_preview');
    const intervalDetailsHidden = document.getElementById('interval_details');

    if (hasIntervalsToggle && intervalBuilder) {
        // Toggle interval builder visibility
        hasIntervalsToggle.addEventListener('change', function() {
            intervalBuilder.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                intervalDetailsHidden.value = '';
                if (intervalPreview) intervalPreview.textContent = '';
            } else {
                updateIntervalPreview();
            }
        });

        // Update preview when any interval field changes
        const intervalFields = intervalBuilder.querySelectorAll('select, input');
        intervalFields.forEach(field => {
            field.addEventListener('change', updateIntervalPreview);
            field.addEventListener('input', updateIntervalPreview);
        });

        // Initial preview if intervals are enabled
        if (hasIntervalsToggle.checked) {
            updateIntervalPreview();
        }
    }

    function updateIntervalPreview() {
        if (!intervalPreview || !intervalDetailsHidden) return;

        const warmupDuration = document.getElementById('warmup_duration')?.value;
        const warmupPace = document.getElementById('warmup_pace')?.value;
        const intervalCount = document.getElementById('interval_count')?.value;
        const intervalDuration = document.getElementById('interval_duration')?.value;
        const intervalPace = document.getElementById('interval_pace')?.value;
        const recoveryDuration = document.getElementById('recovery_duration')?.value;
        const recoveryType = document.getElementById('recovery_type')?.value;
        const cooldownDuration = document.getElementById('cooldown_duration')?.value;
        const cooldownPace = document.getElementById('cooldown_pace')?.value;

        let parts = [];

        // Warm up
        if (warmupDuration) {
            parts.push(`${warmupDuration}min warm up (${warmupPace})`);
        }

        // Intervals
        if (intervalCount && intervalDuration) {
            let intervalText = `${intervalCount}x${intervalDuration}`;
            if (intervalPace) {
                intervalText += ` @ ${intervalPace}`;
            }
            if (recoveryDuration) {
                intervalText += ` / ${recoveryDuration} ${recoveryType}`;
            }
            parts.push(intervalText);
        }

        // Cool down
        if (cooldownDuration) {
            parts.push(`${cooldownDuration}min cool down (${cooldownPace})`);
        }

        const summary = parts.join(' + ');
        intervalPreview.textContent = summary || 'Configure intervals above...';
        intervalDetailsHidden.value = summary;
    }
});

// ============================================
// API Helper Functions
// ============================================

const api = {
    baseUrl: '/api/v1',
    token: localStorage.getItem('access_token'),

    async request(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Try to refresh token
            await this.refreshToken();
            // Retry request
            return this.request(endpoint, options);
        }

        return response.json();
    },

    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            window.location.href = '/login';
            return;
        }

        const response = await fetch(this.baseUrl + '/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${refreshToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('access_token', data.access_token);
        } else {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
    },

    get(endpoint) {
        return this.request(endpoint);
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
};

// ============================================
// Chart.js Helper (if loaded)
// ============================================

const charts = {
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#a0a0b0'
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#a0a0b0' },
                grid: { color: '#2a2a40' }
            },
            y: {
                ticks: { color: '#a0a0b0' },
                grid: { color: '#2a2a40' }
            }
        }
    },

    colors: {
        primary: '#6366f1',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444'
    },

    createLineChart(ctx, labels, datasets) {
        if (typeof Chart === 'undefined') return null;

        return new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: this.defaultOptions
        });
    },

    createBarChart(ctx, labels, datasets) {
        if (typeof Chart === 'undefined') return null;

        return new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets },
            options: this.defaultOptions
        });
    },

    createPieChart(ctx, labels, data) {
        if (typeof Chart === 'undefined') return null;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data,
                    backgroundColor: [
                        '#6366f1', '#22c55e', '#f59e0b',
                        '#ef4444', '#8b5cf6', '#06b6d4'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#a0a0b0' }
                    }
                }
            }
        });
    }
};

// ============================================
// Utility Functions
// ============================================

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
}

function formatPace(pacePerKm) {
    const minutes = Math.floor(pacePerKm);
    const seconds = Math.round((pacePerKm - minutes) * 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}/km`;
}

function calculate1RM(weight, reps) {
    if (reps === 1) return weight;
    if (reps <= 0 || weight <= 0) return 0;
    return Math.round(weight * (1 + reps / 30) * 100) / 100;
}

// Service Worker Registration (for PWA)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(reg => console.log('SW registered'))
            .catch(err => console.log('SW registration failed'));
    });
}

// ============================================
// PR Celebration Functions
// ============================================

function showPrCelebration(exerciseName, newValue, previousValue) {
    const modal = document.getElementById('prModal');
    const exerciseEl = document.getElementById('prExercise');
    const oldValueEl = document.getElementById('prOldValue');
    const newValueEl = document.getElementById('prNewValue');
    const improvementEl = document.getElementById('prImprovement');
    const oldContainer = document.getElementById('prOld');

    if (!modal) return;

    exerciseEl.textContent = exerciseName;
    newValueEl.textContent = newValue;

    if (previousValue && previousValue > 0) {
        oldValueEl.textContent = previousValue;
        oldContainer.style.display = 'flex';
        const improvement = (newValue - previousValue).toFixed(1);
        improvementEl.textContent = `+${improvement}kg improvement!`;
    } else {
        oldContainer.style.display = 'none';
        improvementEl.textContent = 'First PR recorded!';
    }

    modal.style.display = 'flex';

    // Create confetti effect
    createConfetti();

    // Vibrate if supported (mobile)
    if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100, 50, 200]);
    }
}

function closePrModal() {
    const modal = document.getElementById('prModal');
    if (modal) {
        modal.style.display = 'none';
        // Clear confetti
        const confettiContainer = document.querySelector('.pr-confetti');
        if (confettiContainer) {
            confettiContainer.innerHTML = '';
        }
    }
}

function createConfetti() {
    const confettiContainer = document.querySelector('.pr-confetti');
    if (!confettiContainer) return;

    confettiContainer.innerHTML = '';

    const colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ff9ff3'];

    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti-piece';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = Math.random() * 2 + 's';
        confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
        confetti.style.width = (Math.random() * 8 + 5) + 'px';
        confetti.style.height = (Math.random() * 8 + 5) + 'px';
        confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
        confettiContainer.appendChild(confetti);
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('prModal');
    if (e.target === modal) {
        closePrModal();
    }
});

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closePrModal();
    }
});

// ============================================
// Volume Spike Alert Functions
// ============================================

function dismissAlert(button) {
    const alert = button.closest('.alert');
    if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(-20px)';
        setTimeout(() => alert.remove(), 300);
    }
}

// ============================================
// Input Validation Functions
// ============================================

const validationRules = {
    strength: {
        weight_kg: { min: 0, max: 500, warningMax: 300, label: 'Weight' },
        sets: { min: 1, max: 20, warningMax: 10, label: 'Sets' },
        reps: { min: 1, max: 100, warningMax: 30, label: 'Reps' },
        rpe: { min: 1, max: 10, label: 'RPE' },
        rest_seconds: { min: 0, max: 600, warningMax: 300, label: 'Rest time' }
    },
    running: {
        distance_km: { min: 0, max: 100, warningMax: 50, label: 'Distance' },
        duration_minutes: { min: 1, max: 600, warningMax: 300, label: 'Duration' },
        avg_heart_rate: { min: 40, max: 220, warningMin: 60, warningMax: 200, label: 'Avg HR' },
        max_heart_rate: { min: 40, max: 250, warningMin: 80, warningMax: 210, label: 'Max HR' },
        elevation_gain_meters: { min: 0, max: 5000, warningMax: 2000, label: 'Elevation' }
    },
    recovery: {
        sleep_quality: { min: 1, max: 10, label: 'Sleep quality' },
        energy_level: { min: 1, max: 10, label: 'Energy level' },
        muscle_soreness: { min: 1, max: 10, label: 'Soreness' },
        motivation_score: { min: 1, max: 10, label: 'Motivation' },
        sleep_hours: { min: 0, max: 24, warningMin: 4, warningMax: 12, label: 'Sleep hours' }
    }
};

function validateInput(input, rules) {
    const value = parseFloat(input.value);
    const rule = rules[input.name];

    if (!rule || isNaN(value)) return { valid: true };

    // Check hard limits
    if (value < rule.min) {
        return {
            valid: false,
            error: `${rule.label} cannot be less than ${rule.min}`
        };
    }
    if (value > rule.max) {
        return {
            valid: false,
            error: `${rule.label} cannot be more than ${rule.max}`
        };
    }

    // Check soft warnings
    if (rule.warningMin && value < rule.warningMin) {
        return {
            valid: true,
            warning: `${rule.label} of ${value} seems unusually low. Are you sure?`
        };
    }
    if (rule.warningMax && value > rule.warningMax) {
        return {
            valid: true,
            warning: `${rule.label} of ${value} seems unusually high. Are you sure?`
        };
    }

    return { valid: true };
}

function showInputError(input, message) {
    clearInputFeedback(input);
    input.classList.add('input-error');

    const feedback = document.createElement('div');
    feedback.className = 'input-feedback error';
    feedback.textContent = message;
    input.parentNode.appendChild(feedback);
}

function showInputWarning(input, message) {
    clearInputFeedback(input);
    input.classList.add('input-warning');

    const feedback = document.createElement('div');
    feedback.className = 'input-feedback warning';
    feedback.textContent = message;
    input.parentNode.appendChild(feedback);
}

function clearInputFeedback(input) {
    input.classList.remove('input-error', 'input-warning');
    const existing = input.parentNode.querySelector('.input-feedback');
    if (existing) existing.remove();
}

function setupFormValidation(form, ruleSet) {
    const rules = validationRules[ruleSet];
    if (!rules) return;

    // Validate on blur
    form.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('blur', function() {
            const result = validateInput(this, rules);
            if (!result.valid) {
                showInputError(this, result.error);
            } else if (result.warning) {
                showInputWarning(this, result.warning);
            } else {
                clearInputFeedback(this);
            }
        });

        // Clear on focus
        input.addEventListener('focus', function() {
            clearInputFeedback(this);
        });
    });

    // Validate on submit
    form.addEventListener('submit', function(e) {
        let hasError = false;
        let warnings = [];

        form.querySelectorAll('input[type="number"]').forEach(input => {
            const result = validateInput(input, rules);
            if (!result.valid) {
                showInputError(input, result.error);
                hasError = true;
            } else if (result.warning) {
                warnings.push(result.warning);
            }
        });

        if (hasError) {
            e.preventDefault();
            return false;
        }

        if (warnings.length > 0) {
            const confirmMsg = 'Please review:\n\n' + warnings.join('\n') + '\n\nContinue anyway?';
            if (!confirm(confirmMsg)) {
                e.preventDefault();
                return false;
            }
        }
    });
}

// Auto-initialize validation on page load
document.addEventListener('DOMContentLoaded', function() {
    // Strength workout form
    const exerciseForm = document.getElementById('exerciseForm');
    if (exerciseForm) {
        setupFormValidation(exerciseForm, 'strength');
    }

    // Running form
    const runningForm = document.querySelector('form[action*="/running/"]');
    if (runningForm) {
        setupFormValidation(runningForm, 'running');
    }

    // Recovery form
    const recoveryForm = document.querySelector('form[action*="/recovery/"]');
    if (recoveryForm) {
        setupFormValidation(recoveryForm, 'recovery');
    }
});

// ============================================
// Rest Timer Functions
// ============================================

const restTimer = {
    seconds: 0,
    totalSeconds: 90,
    interval: null,
    isRunning: false,
    defaultDuration: 90, // Default rest time in seconds
    circumference: 283, // 2 * PI * 45 (radius)

    init() {
        const timerContainer = document.getElementById('restTimerContainer');
        if (!timerContainer) return;

        this.display = document.getElementById('timerDisplay');
        this.progressCircle = document.getElementById('timerProgress');
        this.startBtn = document.getElementById('timerStart');
        this.stopBtn = document.getElementById('timerStop');
        this.resetBtn = document.getElementById('timerReset');
        this.add15Btn = document.getElementById('timerAdd15');
        this.restInput = document.getElementById('rest_seconds');
        this.presetBtns = document.querySelectorAll('.timer-preset');

        // Event listeners
        this.startBtn?.addEventListener('click', () => this.start());
        this.stopBtn?.addEventListener('click', () => this.pause());
        this.resetBtn?.addEventListener('click', () => this.reset());
        this.add15Btn?.addEventListener('click', () => this.addTime(15));

        // Preset buttons
        this.presetBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                this.presetBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const duration = parseInt(btn.dataset.seconds);
                this.defaultDuration = duration;
                localStorage.setItem('restTimerDefault', duration);
                this.setDuration(duration);
            });
        });

        // Load saved default from localStorage
        const savedDefault = localStorage.getItem('restTimerDefault');
        if (savedDefault) {
            this.defaultDuration = parseInt(savedDefault);
            // Update active preset button
            this.presetBtns.forEach(btn => {
                btn.classList.toggle('active', parseInt(btn.dataset.seconds) === this.defaultDuration);
            });
        }

        this.seconds = this.defaultDuration;
        this.totalSeconds = this.defaultDuration;
        this.updateDisplay();
    },

    setDuration(seconds) {
        this.seconds = seconds;
        this.totalSeconds = seconds;
        this.updateDisplay();
    },

    start() {
        if (this.isRunning) return;

        // If timer is at 0, use default duration
        if (this.seconds === 0) {
            this.seconds = this.defaultDuration;
            this.totalSeconds = this.defaultDuration;
        }

        this.isRunning = true;
        this.startBtn.style.display = 'none';
        this.stopBtn.style.display = 'inline-flex';

        // Add running class for visual feedback
        document.getElementById('restTimerContainer')?.classList.add('timer-running');

        // Request notification permission on first use
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        this.interval = setInterval(() => {
            this.seconds--;
            this.updateDisplay();

            if (this.seconds <= 0) {
                this.timerComplete();
            }
        }, 1000);
    },

    pause() {
        if (!this.isRunning) return;

        clearInterval(this.interval);
        this.isRunning = false;
        this.startBtn.style.display = 'inline-flex';
        this.stopBtn.style.display = 'none';

        document.getElementById('restTimerContainer')?.classList.remove('timer-running');
    },

    reset() {
        this.pause();
        this.seconds = this.defaultDuration;
        this.totalSeconds = this.defaultDuration;
        this.progressCircle?.classList.remove('warning', 'complete');
        this.updateDisplay();
    },

    addTime(extraSeconds) {
        this.seconds += extraSeconds;
        this.totalSeconds += extraSeconds;
        this.updateDisplay();
    },

    timerComplete() {
        this.pause();
        this.seconds = 0;
        this.updateDisplay();

        // Fill rest input with full duration
        if (this.restInput) {
            this.restInput.value = this.totalSeconds;
        }

        // Visual feedback
        document.getElementById('restTimerContainer')?.classList.add('timer-complete');
        this.progressCircle?.classList.add('complete');
        setTimeout(() => {
            document.getElementById('restTimerContainer')?.classList.remove('timer-complete');
        }, 3000);

        // Play sound
        this.playAlertSound();

        // Vibrate on mobile
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200, 100, 200]);
        }

        // Show notification if permission granted
        if (Notification.permission === 'granted') {
            new Notification('Rest Complete!', {
                body: 'Time for your next set!',
                icon: '/static/icons/icon-192.png',
                tag: 'rest-timer',
                requireInteraction: false
            });
        }
    },

    playAlertSound() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

            // Play two beeps
            [0, 300].forEach(delay => {
                setTimeout(() => {
                    const oscillator = audioCtx.createOscillator();
                    const gainNode = audioCtx.createGain();

                    oscillator.connect(gainNode);
                    gainNode.connect(audioCtx.destination);

                    oscillator.frequency.value = 880;
                    oscillator.type = 'sine';
                    gainNode.gain.value = 0.3;

                    oscillator.start();
                    setTimeout(() => oscillator.stop(), 150);
                }, delay);
            });

            setTimeout(() => audioCtx.close(), 600);
        } catch (e) {
            // Audio not supported
        }
    },

    updateDisplay() {
        if (!this.display) return;

        const mins = Math.floor(this.seconds / 60);
        const secs = this.seconds % 60;
        this.display.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;

        // Update circular progress
        if (this.progressCircle && this.totalSeconds > 0) {
            const progress = this.seconds / this.totalSeconds;
            const offset = this.circumference * (1 - progress);
            this.progressCircle.style.strokeDashoffset = offset;

            // Update colors based on time remaining
            this.progressCircle.classList.remove('warning', 'complete');
            if (this.seconds <= 10 && this.seconds > 0) {
                this.progressCircle.classList.add('warning');
                this.display.classList.add('timer-warning');
            } else if (this.seconds === 0) {
                this.progressCircle.classList.add('complete');
                this.display.classList.remove('timer-warning');
            } else {
                this.display.classList.remove('timer-warning');
            }
        }
    },

    // Auto-start after form submission (called from page)
    autoStart() {
        this.reset();
        this.start();

        // Request notification permission for timer alerts
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
};

// Initialize rest timer on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    restTimer.init();
});

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
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
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

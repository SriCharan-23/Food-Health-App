/* ═══════════════════════════════════════════════════════════════════
   NutriAI — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════════ */

let currentGoal = 'maintenance';
let lastAnalysis = null;
let calorieChart = null;
let macroChart = null;

// ── Init ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadUserProfile();
    loadHistory();
    loadInsights();
    setupNavigation();
    setupSearch();
    autoDetectMealType();
});

// ── Navigation ────────────────────────────────────────────────────

function setupNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    // Goal selector
    const goalSelect = document.getElementById('goalSelect');
    goalSelect.addEventListener('change', () => {
        currentGoal = goalSelect.value;
        fetch('/api/user/goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal: currentGoal })
        }).then(() => {
            showToast('Goal updated to ' + goalSelect.options[goalSelect.selectedIndex].text, 'success');
            loadInsights();
        }).catch(() => showToast('Failed to update goal', 'error'));
    });
}

// ── Auto-detect Meal Type by Time ─────────────────────────────────

function autoDetectMealType() {
    const hour = new Date().getHours();
    const select = document.getElementById('mealType');
    if (hour >= 5 && hour < 11) select.value = 'breakfast';
    else if (hour >= 11 && hour < 15) select.value = 'lunch';
    else if (hour >= 15 && hour < 18) select.value = 'snack';
    else select.value = 'dinner';
}

// ── Search with Debounce ──────────────────────────────────────────

let searchTimeout = null;

function setupSearch() {
    const input = document.getElementById('foodInput');
    const dropdown = document.getElementById('searchSuggestions');

    input.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const q = input.value.trim();
        if (q.length < 2) {
            dropdown.classList.remove('show');
            return;
        }
        searchTimeout = setTimeout(() => searchFood(q), 400);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            dropdown.classList.remove('show');
            analyzeFood();
        }
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.form-group')) {
            dropdown.classList.remove('show');
        }
    });
}

async function searchFood(query) {
    const dropdown = document.getElementById('searchSuggestions');
    try {
        const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await resp.json();
        if (data.results && data.results.length > 0) {
            dropdown.innerHTML = data.results.map(r => `
                <div class="suggestion-item" onclick="selectSuggestion('${escapeHtml(r.name)}')">
                    <span class="suggestion-name">${escapeHtml(r.name)}</span>
                    <span class="suggestion-cal">${r.calories} kcal</span>
                </div>
            `).join('');
            dropdown.classList.add('show');
        } else {
            dropdown.classList.remove('show');
        }
    } catch {
        dropdown.classList.remove('show');
    }
}

function selectSuggestion(name) {
    document.getElementById('foodInput').value = name;
    document.getElementById('searchSuggestions').classList.remove('show');
    analyzeFood();
}

// ── Analyze Food ──────────────────────────────────────────────────

async function analyzeFood() {
    const foodInput = document.getElementById('foodInput');
    const food = foodInput.value.trim();
    if (!food) {
        showToast('Please enter a food item', 'error');
        return;
    }

    const btn = document.getElementById('analyzeBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');

    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';

    try {
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                food_name: food,
                meal_type: document.getElementById('mealType').value,
                mood: document.getElementById('moodSelect').value,
                hunger: document.getElementById('hungerSelect').value,
                goal: currentGoal,
            })
        });

        const data = await resp.json();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        lastAnalysis = data;
        renderResults(data);
        document.getElementById('resultsCard').style.display = 'block';
        document.getElementById('resultsCard').scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
        showToast('Analysis failed. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// ── Render Results ────────────────────────────────────────────────

function renderResults(data) {
    const n = data.nutrition;
    const container = document.getElementById('resultsContent');

    container.innerHTML = `
        <!-- Header -->
        <div class="result-header">
            <div>
                <div class="result-food-name">${escapeHtml(n.name)}</div>
                <div class="result-source">📦 ${escapeHtml(n.serving_size)} · via ${escapeHtml(n.source)}</div>
            </div>
            <div class="score-badge ${data.badge.class}">
                ${data.score}/100 · ${data.badge.label}
            </div>
        </div>

        <!-- Macro Pie Chart -->
        <div class="macro-chart-wrap">
            <canvas id="macroPieChart"></canvas>
        </div>

        <!-- Macro Grid -->
        <div class="macro-grid">
            <div class="macro-item cal">
                <div class="macro-value">${n.calories}</div>
                <div class="macro-label">Calories</div>
            </div>
            <div class="macro-item protein">
                <div class="macro-value">${n.protein}g</div>
                <div class="macro-label">Protein</div>
            </div>
            <div class="macro-item fat">
                <div class="macro-value">${n.fat}g</div>
                <div class="macro-label">Fat</div>
            </div>
            <div class="macro-item carbs">
                <div class="macro-value">${n.carbs}g</div>
                <div class="macro-label">Carbs</div>
            </div>
            <div class="macro-item sugar">
                <div class="macro-value">${n.sugar}g</div>
                <div class="macro-label">Sugar</div>
            </div>
            <div class="macro-item fiber">
                <div class="macro-value">${n.fiber}g</div>
                <div class="macro-label">Fiber</div>
            </div>
        </div>

        <!-- 🍽️ Meal Analysis / ⚠️ Health Insights -->
        <div class="result-section">
            <div class="result-section-title">⚠️ Health Insights</div>
            ${data.insights.map(i => `
                <div class="insight-item">
                    <span class="insight-icon">${i.icon}</span>
                    <span class="insight-text">${escapeHtml(i.text)}</span>
                </div>
            `).join('')}
        </div>

        <!-- 🔄 Better Alternatives -->
        <div class="result-section">
            <div class="result-section-title">🔄 Better Alternatives</div>
            ${data.alternatives.map(a => `
                <div class="alt-item">
                    <div>
                        <div class="alt-name">${escapeHtml(a.name)}</div>
                        <div class="alt-why">${escapeHtml(a.why)}</div>
                    </div>
                    <div class="alt-save">${escapeHtml(a.save || '')}</div>
                </div>
            `).join('')}
        </div>

        <!-- 💡 Habit Suggestion -->
        <div class="result-section">
            <div class="result-section-title">💡 Habit Suggestion</div>
            <div class="habit-card">
                <span class="habit-icon">${data.habit.icon}</span>
                <span class="habit-text">${escapeHtml(data.habit.text)}</span>
            </div>
        </div>

        <!-- Log Button -->
        <div class="log-btn-wrap">
            <button class="btn-primary" onclick="logMeal()">
                📝 Log This Meal
            </button>
        </div>
    `;

    // Render macro pie chart
    renderMacroPie(n);
}

function renderMacroPie(n) {
    const ctx = document.getElementById('macroPieChart');
    if (!ctx) return;

    if (macroChart) macroChart.destroy();

    macroChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Protein', 'Fat', 'Carbs'],
            datasets: [{
                data: [n.protein, n.fat, n.carbs],
                backgroundColor: ['#6366f1', '#ec4899', '#06b6d4'],
                borderWidth: 0,
                hoverOffset: 6,
            }]
        },
        options: {
            responsive: true,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#8892a8', font: { size: 11, family: 'Inter' }, padding: 12, usePointStyle: true }
                }
            }
        }
    });
}

// ── Log Meal ──────────────────────────────────────────────────────

async function logMeal() {
    if (!lastAnalysis) return;

    try {
        const resp = await fetch('/api/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                food_name: lastAnalysis.nutrition.name,
                meal_type: lastAnalysis.meal_type,
                nutrition: lastAnalysis.nutrition,
                mood: document.getElementById('moodSelect').value,
                hunger: document.getElementById('hungerSelect').value,
            })
        });

        const data = await resp.json();
        if (data.success) {
            showToast(`✅ ${data.message}`, 'success');
            loadHistory();
            loadInsights();
            updateMealCount();
        } else {
            showToast(data.error || 'Failed to log meal', 'error');
        }
    } catch {
        showToast('Failed to log meal', 'error');
    }
}

// ── Load History ──────────────────────────────────────────────────

async function loadHistory() {
    try {
        const resp = await fetch('/api/history?days=7');
        const data = await resp.json();

        // Update meal count stat
        document.getElementById('statMeals').textContent = data.count || 0;

        // Render meal list
        const list = document.getElementById('mealList');
        if (!data.meals || data.meals.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📋</div>
                    <p>No meals logged yet. Analyze and log your first meal!</p>
                </div>`;
            return;
        }

        const mealTypeEmoji = { breakfast: '🌅', lunch: '🌞', dinner: '🌙', snack: '🍿' };

        list.innerHTML = data.meals.map(m => {
            const date = new Date(m.logged_at);
            const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const day = date.toLocaleDateString([], { month: 'short', day: 'numeric' });
            return `
                <div class="meal-item">
                    <div class="meal-info">
                        <div class="meal-name">${mealTypeEmoji[m.meal_type] || '🍽️'} ${escapeHtml(m.food_name)}</div>
                        <div class="meal-meta">${m.meal_type} · ${day} at ${time}</div>
                    </div>
                    <div class="meal-cal">${m.calories} kcal</div>
                </div>`;
        }).join('');

        // Load calorie trend chart
        loadCalorieChart();

    } catch {
        console.log('Failed to load history');
    }
}

async function loadCalorieChart() {
    try {
        const resp = await fetch('/api/insights');
        const data = await resp.json();

        if (!data.daily_totals || data.daily_totals.length === 0) return;

        const labels = data.daily_totals.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        });
        const cals = data.daily_totals.map(d => Math.round(d.total_cal || 0));

        const ctx = document.getElementById('calorieChart');
        if (!ctx) return;

        if (calorieChart) calorieChart.destroy();

        calorieChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Calories',
                    data: cals,
                    backgroundColor: cals.map(c => c > 2200 ? 'rgba(244,63,94,0.6)' : c > 1800 ? 'rgba(245,158,11,0.6)' : 'rgba(16,185,129,0.6)'),
                    borderColor: cals.map(c => c > 2200 ? '#f43f5e' : c > 1800 ? '#f59e0b' : '#10b981'),
                    borderWidth: 1,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: '#5a6580', font: { size: 11 } }, grid: { display: false } },
                    y: { ticks: { color: '#5a6580', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' }, beginAtZero: true }
                }
            }
        });
    } catch {
        console.log('Failed to load chart');
    }
}

// ── Load Insights ─────────────────────────────────────────────────

async function loadInsights() {
    try {
        const resp = await fetch('/api/insights');
        const data = await resp.json();

        const container = document.getElementById('insightsContent');

        if ((!data.patterns || data.patterns.length === 0) && (!data.daily_totals || data.daily_totals.length === 0)) {
            container.innerHTML = `
                <div class="glass-card">
                    <div class="empty-state">
                        <div class="empty-icon">💡</div>
                        <p>Log a few meals to unlock personalized insights and pattern detection!</p>
                    </div>
                </div>`;
            return;
        }

        let html = '';

        // Patterns
        if (data.patterns && data.patterns.length > 0) {
            data.patterns.forEach(p => {
                const isDanger = p.type === 'high_sugar' || p.type === 'rising_calories';
                html += `
                    <div class="glass-card pattern-card ${isDanger ? 'danger' : ''}">
                        <div class="result-section-title">⚠️ ${escapeHtml(p.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()))}</div>
                        <p class="insight-text">${escapeHtml(p.msg)}</p>
                    </div>`;
            });
        }

        // Daily tip
        if (data.tip) {
            html += `
                <div class="glass-card tip-card">
                    <div class="result-section-title">💡 Today's Tip</div>
                    <div class="habit-card">
                        <span class="habit-icon">${data.tip.icon}</span>
                        <span class="habit-text">${escapeHtml(data.tip.text)}</span>
                    </div>
                </div>`;
        }

        // Daily summary
        if (data.daily_totals && data.daily_totals.length > 0) {
            const today = data.daily_totals[data.daily_totals.length - 1];
            html += `
                <div class="glass-card">
                    <div class="result-section-title">📊 Latest Day Summary</div>
                    <div class="macro-grid">
                        <div class="macro-item cal">
                            <div class="macro-value">${Math.round(today.total_cal || 0)}</div>
                            <div class="macro-label">Calories</div>
                        </div>
                        <div class="macro-item protein">
                            <div class="macro-value">${Math.round(today.total_protein || 0)}g</div>
                            <div class="macro-label">Protein</div>
                        </div>
                        <div class="macro-item carbs">
                            <div class="macro-value">${Math.round(today.total_carbs || 0)}g</div>
                            <div class="macro-label">Carbs</div>
                        </div>
                    </div>
                </div>`;
        }

        container.innerHTML = html || container.innerHTML;

    } catch {
        console.log('Failed to load insights');
    }
}

// ── Load User Profile ─────────────────────────────────────────────

async function loadUserProfile() {
    try {
        const resp = await fetch('/api/user');
        const user = await resp.json();
        currentGoal = user.health_goal || 'maintenance';
        document.getElementById('goalSelect').value = currentGoal;
    } catch {
        console.log('Failed to load user profile');
    }
}

function updateMealCount() {
    const el = document.getElementById('statMeals');
    const cur = parseInt(el.textContent) || 0;
    el.textContent = cur + 1;
}

// ── Toast Notifications ───────────────────────────────────────────

function showToast(message, type = 'info') {
    const container = document.getElementById('toast');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ── Utilities ─────────────────────────────────────────────────────

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

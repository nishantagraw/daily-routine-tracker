/**
 * Daily Routine Tracker - Frontend JavaScript
 * Handles UI interactions, API calls, and chart rendering
 */

// Configuration
// Use relative URLs for production, localhost for development
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:5200/api'
    : '/api';
let currentView = 'weekly';
let currentWeek = 1;
let habitsData = [];
let datesData = [];

// LocalStorage keys for data persistence
const STORAGE_KEY = 'routine_tracker_data';

// Save data to localStorage
function saveToLocalStorage() {
    const data = { habits: habitsData, dates: datesData };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

// Load data from localStorage
function loadFromLocalStorage() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
        try {
            return JSON.parse(saved);
        } catch (e) {
            console.error('Failed to parse localStorage data:', e);
        }
    }
    return null;
}

// Chart instances
let habitProgressChart = null;
let weeklyTrendChart = null;
let dailyCompletionChart = null;

// ===================================
// Initialization
// ===================================

document.addEventListener('DOMContentLoaded', async () => {
    // Set initial week based on current date (Jan 10 = week 1)
    const today = new Date();
    if (today.getMonth() === 0 && today.getDate() >= 10) {
        currentWeek = Math.ceil((today.getDate() - 9) / 7);
        currentWeek = Math.min(currentWeek, 4);
    }

    updateWeekButtons();

    // Initialize the app
    await initializeApp();
});

async function initializeApp() {
    showLoading();

    try {
        // Try to initialize with server
        const initResponse = await fetch(`${API_BASE}/init`, {
            method: 'POST'
        });

        if (!initResponse.ok) {
            throw new Error('Server returned error');
        }

        // Load data
        await loadStats();
        await loadHabits();

        hideLoading();

    } catch (error) {
        console.error('Failed to initialize from server:', error);

        // Try to load from localStorage as fallback
        const localData = loadFromLocalStorage();
        if (localData && localData.habits && localData.habits.length > 0) {
            habitsData = localData.habits;
            datesData = localData.dates || [];
            renderHabitTable();
            renderCharts();
            hideLoading();
            console.log('Loaded data from localStorage');
        } else {
            hideLoading();
            showError('Failed to connect to server. Make sure the backend is running.');
        }
    }
}

// ===================================
// Data Loading
// ===================================

// Calculate stats from local data instantly
function calculateLocalStats() {
    let totalCompleted = 0;
    let totalMissed = 0;
    let bestStreak = 0;

    habitsData.forEach(habit => {
        let streak = 0;
        const status = habit.daily_status || {};

        Object.values(status).forEach(s => {
            if (s === '✓') {
                totalCompleted++;
                streak++;
                bestStreak = Math.max(bestStreak, streak);
            } else if (s === '✗') {
                totalMissed++;
                streak = 0;
            }
        });
    });

    const total = totalCompleted + totalMissed;
    const progress = total > 0 ? Math.round((totalCompleted / total) * 100) : 0;

    return { progress, totalCompleted, totalMissed, bestStreak };
}

// Update stats display instantly
function updateStatsDisplay() {
    const stats = calculateLocalStats();

    document.getElementById('overallProgress').textContent = `${stats.progress}%`;
    document.getElementById('progressBar').style.width = `${stats.progress}%`;
    document.getElementById('bestStreak').textContent = stats.bestStreak;
    document.getElementById('totalCompleted').textContent = stats.totalCompleted;
    document.getElementById('totalMissed').textContent = stats.totalMissed;
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();

        // Update stat cards with default values if undefined
        const progress = stats.overall_progress ?? 0;
        const streak = stats.best_streak ?? 0;
        const completed = stats.total_completed ?? 0;
        const missed = stats.total_missed ?? 0;

        document.getElementById('overallProgress').textContent = progress > 0 ? `${progress}%` : '0%';
        document.getElementById('progressBar').style.width = `${progress}%`;
        document.getElementById('bestStreak').textContent = streak;
        document.getElementById('totalCompleted').textContent = completed;
        document.getElementById('totalMissed').textContent = missed;

    } catch (error) {
        console.error('Failed to load stats:', error);
        // Use local stats on error
        updateStatsDisplay();
    }
}

async function loadHabits() {
    try {
        let response;
        let serverHabits = [];
        let serverDates = [];

        if (currentView === 'weekly') {
            response = await fetch(`${API_BASE}/week/${currentWeek}`);
            const weekData = await response.json();
            serverHabits = weekData.habits || [];
            serverDates = weekData.dates || [];
        } else {
            response = await fetch(`${API_BASE}/habits`);
            const data = await response.json();
            serverHabits = data.habits || [];
            serverDates = data.dates || [];
        }

        // Merge with localStorage data (localStorage takes priority for status)
        const localData = loadFromLocalStorage();
        if (localData && localData.habits) {
            // Create a map of local habits for quick lookup
            const localHabitsMap = {};
            localData.habits.forEach(h => {
                localHabitsMap[h.name] = h.daily_status || {};
            });

            // Merge local status into server habits
            serverHabits.forEach(habit => {
                if (localHabitsMap[habit.name]) {
                    habit.daily_status = { ...habit.daily_status, ...localHabitsMap[habit.name] };
                }
            });
        }

        habitsData = serverHabits;
        datesData = serverDates;

        // Save merged data to localStorage
        saveToLocalStorage();

        renderHabitTable();
        renderCharts();

    } catch (error) {
        console.error('Failed to load habits:', error);

        // Try to load from localStorage if server fails
        const localData = loadFromLocalStorage();
        if (localData) {
            habitsData = localData.habits || [];
            datesData = localData.dates || [];
            renderHabitTable();
            renderCharts();
        }
    }
}

// ===================================
// Table Rendering
// ===================================

function renderHabitTable() {
    const headerRow = document.getElementById('tableHeaders');
    const tableBody = document.getElementById('habitTableBody');

    // Clear existing
    headerRow.innerHTML = '<th class="habit-col">Habit</th>';
    tableBody.innerHTML = '';

    // Add date headers
    datesData.forEach(date => {
        const th = document.createElement('th');
        th.textContent = date;
        th.classList.add('date-col');
        headerRow.appendChild(th);
    });

    // Add progress and actions headers (removed streak)
    headerRow.innerHTML += '<th class="progress-col">Progress</th><th class="actions-col">Actions</th>';

    // Add habit rows
    habitsData.forEach((habit, index) => {
        const tr = document.createElement('tr');
        tr.style.animationDelay = `${index * 0.05}s`;

        // Habit name cell
        const nameTd = document.createElement('td');
        nameTd.textContent = habit.name;
        tr.appendChild(nameTd);

        // Status cells for each date
        datesData.forEach(date => {
            const td = document.createElement('td');
            td.classList.add('status-cell');

            const status = habit.daily_status[date] || '';

            if (status === '✓') {
                td.innerHTML = '<span class="status-completed">✓</span>';
                td.dataset.status = 'completed';
            } else if (status === '✗') {
                td.innerHTML = '<span class="status-missed">✗</span>';
                td.dataset.status = 'missed';
            } else {
                td.innerHTML = '<span class="status-pending">○</span>';
                td.dataset.status = 'pending';
            }

            td.onclick = () => toggleStatus(habit.name, date, td);
            td.dataset.tooltip = `Click to toggle`;

            tr.appendChild(td);
        });

        // Calculate progress locally
        const dailyStatus = habit.daily_status || {};
        let completed = 0;
        let total = 0;

        datesData.forEach(date => {
            const s = dailyStatus[date];
            if (s === '✓') completed++;
            if (s === '✓' || s === '✗') total++;
        });

        const habitProgress = total > 0 ? Math.round((completed / total) * 100) : 0;
        const barColor = habitProgress >= 70 ? '#22c55e' : habitProgress >= 40 ? '#f59e0b' : '#64748b';

        // Progress bar cell
        const progressTd = document.createElement('td');
        progressTd.classList.add('progress-cell');
        progressTd.innerHTML = `
            <div class="habit-progress-bar">
                <div class="habit-progress-fill" style="width: ${habitProgress}%; background: ${barColor}"></div>
            </div>
            <span class="habit-progress-text">${habitProgress}%</span>
        `;
        tr.appendChild(progressTd);

        // Actions cell (removed streak)
        const actionsTd = document.createElement('td');
        actionsTd.classList.add('actions-cell');
        actionsTd.innerHTML = `
            <button class="edit-btn" onclick="editHabit('${habit.name.replace(/'/g, "\\'")}')" title="Edit">✏️</button>
            <button class="delete-btn" onclick="deleteHabit('${habit.name.replace(/'/g, "\\'")}')" title="Delete">🗑️</button>
        `;
        tr.appendChild(actionsTd);

        tableBody.appendChild(tr);
    });
}

// ===================================
// Status Toggle
// ===================================

async function toggleStatus(habitName, date, cell) {
    const currentStatus = cell.dataset.status;
    let newStatus = '';
    let newSymbol = '';

    // Cycle through: pending -> completed -> missed -> pending
    if (currentStatus === 'pending') {
        newStatus = 'completed';
        newSymbol = '✓';
    } else if (currentStatus === 'completed') {
        newStatus = 'missed';
        newSymbol = '✗';
    } else {
        newStatus = 'pending';
        newSymbol = '';
    }

    // Optimistic update
    if (newStatus === 'completed') {
        cell.innerHTML = '<span class="status-completed">✓</span>';
    } else if (newStatus === 'missed') {
        cell.innerHTML = '<span class="status-missed">✗</span>';
    } else {
        cell.innerHTML = '<span class="status-pending">○</span>';
    }
    cell.dataset.status = newStatus;

    // Add animation
    cell.style.transform = 'scale(1.3)';
    setTimeout(() => {
        cell.style.transform = 'scale(1)';
    }, 150);

    // Update local data and save to localStorage immediately
    const habit = habitsData.find(h => h.name === habitName);
    if (habit) {
        if (!habit.daily_status) habit.daily_status = {};
        habit.daily_status[date] = newSymbol;
        saveToLocalStorage();

        // Update stats and charts IMMEDIATELY (before server call)
        updateStatsDisplay();
        renderCharts();
    }

    // Update server (in background, don't wait)
    fetch(`${API_BASE}/habits/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            habit_name: habitName,
            date: date,
            status: newSymbol
        })
    }).catch(e => console.log('Server sync failed, but local save succeeded'));
}

// ===================================
// View Toggle
// ===================================

function setView(view) {
    currentView = view;

    // Update button states
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Show/hide week selector
    const weekSelector = document.getElementById('weekSelector');
    weekSelector.style.display = view === 'weekly' ? 'flex' : 'none';

    // Reload data
    loadHabits();
}

function selectWeek(week) {
    currentWeek = week;
    updateWeekButtons();
    loadHabits();
}

function updateWeekButtons() {
    document.querySelectorAll('.week-btn').forEach((btn, index) => {
        btn.classList.toggle('active', index + 1 === currentWeek);
    });
}

// ===================================
// Charts
// ===================================

function renderCharts() {
    renderWeeklyTrendChart();
    renderDailyCompletionChart();
}

function renderHabitProgressChart() {
    const ctx = document.getElementById('habitProgressChart').getContext('2d');

    if (habitProgressChart) {
        habitProgressChart.destroy();
    }

    // Calculate overall completion stats
    let totalCompleted = 0;
    let totalMissed = 0;
    let totalPending = 0;

    habitsData.forEach(habit => {
        const status = habit.daily_status || {};
        datesData.forEach(date => {
            const s = status[date];
            if (s === '✓') totalCompleted++;
            else if (s === '✗') totalMissed++;
            else totalPending++;
        });
    });

    habitProgressChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['✓ Done', '✗ Missed', '○ Pending'],
            datasets: [{
                data: [totalCompleted, totalMissed, totalPending],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.9)',
                    'rgba(239, 68, 68, 0.9)',
                    'rgba(100, 116, 139, 0.4)'
                ],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: getComputedStyle(document.body).getPropertyValue('--text-secondary').trim(),
                        font: { size: 12 },
                        padding: 12,
                        boxWidth: 14
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.label}: ${context.raw}`
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function renderWeeklyTrendChart() {
    const ctx = document.getElementById('weeklyTrendChart').getContext('2d');

    if (weeklyTrendChart) {
        weeklyTrendChart.destroy();
    }

    // Calculate completion rate per date
    const completionByDate = {};
    datesData.forEach(date => {
        let completed = 0;
        let total = 0;
        habitsData.forEach(habit => {
            const status = habit.daily_status[date];
            if (status === '✓') completed++;
            if (status === '✓' || status === '✗') total++;
        });
        completionByDate[date] = total > 0 ? Math.round((completed / total) * 100) : 0;
    });

    const labels = Object.keys(completionByDate);
    const data = Object.values(completionByDate);

    weeklyTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Completion Rate',
                data: data,
                borderColor: 'rgba(139, 92, 246, 1)',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgba(139, 92, 246, 1)',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.raw}% completed`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim(),
                        callback: (value) => `${value}%`
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim()
                    }
                }
            }
        }
    });
}

function renderDailyCompletionChart() {
    const ctx = document.getElementById('dailyCompletionChart').getContext('2d');

    if (dailyCompletionChart) {
        dailyCompletionChart.destroy();
    }

    // Calculate completed vs missed per date
    const completedByDate = [];
    const missedByDate = [];

    datesData.forEach(date => {
        let completed = 0;
        let missed = 0;
        habitsData.forEach(habit => {
            const status = habit.daily_status[date];
            if (status === '✓') completed++;
            if (status === '✗') missed++;
        });
        completedByDate.push(completed);
        missedByDate.push(missed);
    });

    dailyCompletionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: datesData,
            datasets: [
                {
                    label: 'Completed',
                    data: completedByDate,
                    backgroundColor: 'rgba(34, 197, 94, 0.8)',
                    borderRadius: 4,
                    borderSkipped: false
                },
                {
                    label: 'Missed',
                    data: missedByDate,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderRadius: 4,
                    borderSkipped: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: getComputedStyle(document.body).getPropertyValue('--text-secondary').trim(),
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: false,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim(),
                        stepSize: 1
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim()
                    }
                }
            }
        }
    });
}

// ===================================
// Add Habit Modal
// ===================================

let selectedEmoji = '📌';

function openAddHabitModal() {
    document.getElementById('addHabitModal').classList.add('active');
    document.getElementById('newHabitName').value = '';
    document.getElementById('newHabitName').focus();
}

function closeAddHabitModal() {
    document.getElementById('addHabitModal').classList.remove('active');
}

// Emoji picker
document.querySelectorAll('.emoji-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.emoji-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedEmoji = btn.dataset.emoji;
    });
});

async function addNewHabit() {
    const name = document.getElementById('newHabitName').value.trim();

    if (!name) {
        alert('Please enter a habit name');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/habits/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                emoji: selectedEmoji
            })
        });

        const result = await response.json();

        if (result.success) {
            closeAddHabitModal();
            await loadHabits();
            await loadStats();
        } else {
            alert(result.error || 'Failed to add habit');
        }

    } catch (error) {
        console.error('Failed to add habit:', error);
        alert('Failed to add habit. Please try again.');
    }
}

// ===================================
// Delete Habit
// ===================================

async function deleteHabit(habitName) {
    if (!confirm(`Are you sure you want to delete "${habitName}"?\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/habits/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                habit_name: habitName
            })
        });

        const result = await response.json();

        if (result.success) {
            await loadHabits();
            await loadStats();
        } else {
            alert(result.error || 'Failed to delete habit');
        }

    } catch (error) {
        console.error('Failed to delete habit:', error);
        alert('Failed to delete habit. Please try again.');
    }
}

// ===================================
// Edit Habit
// ===================================

async function editHabit(oldName) {
    // Extract just the name part (without emoji)
    const namePart = oldName.replace(/^[\uD800-\uDBFF][\uDC00-\uDFFF]\s*/, '').replace(/^.\s*/, '');

    const newName = prompt(`Edit habit name:\n\nCurrent: ${oldName}\n\nEnter new name (without emoji):`, namePart);

    if (!newName || newName.trim() === '' || newName.trim() === namePart) {
        return;
    }

    // Get emoji from old name
    const emojiMatch = oldName.match(/^([\uD800-\uDBFF][\uDC00-\uDFFF]|.)\s*/);
    const emoji = emojiMatch ? emojiMatch[1] : '📌';

    try {
        const response = await fetch(`${API_BASE}/habits/edit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_name: oldName,
                new_name: newName.trim(),
                emoji: emoji
            })
        });

        const result = await response.json();

        if (result.success) {
            await loadHabits();
            await loadStats();
        } else {
            alert(result.error || 'Failed to update habit');
        }

    } catch (error) {
        console.error('Failed to edit habit:', error);
        alert('Failed to edit habit. Please try again.');
    }
}

// ===================================
// Theme Toggle
// ===================================

function toggleTheme() {
    const body = document.body;

    if (body.classList.contains('dark-mode')) {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    }

    // Re-render charts with new theme colors
    setTimeout(() => {
        renderCharts();
    }, 300);
}

// Load saved theme
(function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
    }
})();

// ===================================
// Utility Functions
// ===================================

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showError(message) {
    alert(message);
}

// Close modal on outside click
document.getElementById('addHabitModal').addEventListener('click', (e) => {
    if (e.target.id === 'addHabitModal') {
        closeAddHabitModal();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAddHabitModal();
    }
});

// Auto-refresh every 30 seconds
setInterval(async () => {
    await loadStats();
    await loadHabits();
}, 30000);

// ===================================
// Google Sheets Setup
// ===================================

let sheetsConnected = false;

function updateConnectionStatus(connected, sheetUrl = null) {
    sheetsConnected = connected;
    const statusEl = document.getElementById('connectionStatus');
    const bannerEl = document.getElementById('sheetsBanner');
    const sheetLink = document.getElementById('sheetLink');

    if (connected) {
        statusEl.classList.add('connected');
        statusEl.querySelector('.status-text').textContent = 'Connected to Google Sheets';
        bannerEl.classList.add('hidden');

        if (sheetUrl) {
            sheetLink.href = sheetUrl;
            sheetLink.style.display = 'flex';
        }
    } else {
        statusEl.classList.remove('connected');
        statusEl.querySelector('.status-text').textContent = 'Local Storage Only';
        bannerEl.classList.remove('hidden');
        sheetLink.style.display = 'none';
    }
}

// Check connection status on load
async function checkSheetsConnection() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        const config = await response.json();

        updateConnectionStatus(
            config.sheets_connected,
            config.spreadsheet_id ? `https://docs.google.com/spreadsheets/d/${config.spreadsheet_id}` : null
        );
    } catch (error) {
        console.error('Failed to check sheets connection:', error);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(checkSheetsConnection, 1000);
});

function openSheetsSetupModal() {
    document.getElementById('sheetsSetupModal').classList.add('active');
    document.getElementById('sheetIdInput').value = '';
    document.getElementById('sheetIdInput').focus();
}

function closeSheetsSetupModal() {
    document.getElementById('sheetsSetupModal').classList.remove('active');
}

function copyServiceEmail() {
    const email = document.getElementById('serviceEmail').textContent;
    navigator.clipboard.writeText(email).then(() => {
        const btn = document.querySelector('.copy-btn');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = '#22c55e';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    });
}

async function connectGoogleSheets() {
    const sheetId = document.getElementById('sheetIdInput').value.trim();

    if (!sheetId) {
        alert('Please enter a Sheet ID');
        return;
    }

    // Validate Sheet ID format (should be alphanumeric with dashes/underscores)
    if (!/^[a-zA-Z0-9_-]+$/.test(sheetId)) {
        alert('Invalid Sheet ID format. Please copy the ID from the Google Sheets URL.');
        return;
    }

    try {
        showLoading();

        const response = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                spreadsheet_id: sheetId
            })
        });

        const result = await response.json();

        hideLoading();

        if (result.success) {
            closeSheetsSetupModal();
            updateConnectionStatus(true, result.spreadsheet_url);
            alert('✅ Google Sheets connected successfully!\n\nYour habits will now sync with Google Sheets.\nYou can access them from your phone too!');

            // Reload data
            await loadHabits();
            await loadStats();
        } else {
            alert('❌ Failed to connect: ' + (result.error || 'Unknown error') + '\n\nMake sure you:\n1. Shared the sheet with the service account email\n2. Copied the correct Sheet ID');
        }

    } catch (error) {
        hideLoading();
        console.error('Failed to connect sheets:', error);
        alert('Failed to connect to Google Sheets. Please try again.');
    }
}

// Close sheets modal on outside click
document.getElementById('sheetsSetupModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'sheetsSetupModal') {
        closeSheetsSetupModal();
    }
});

// Update escape key handler
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAddHabitModal();
        closeSheetsSetupModal();
    }
});

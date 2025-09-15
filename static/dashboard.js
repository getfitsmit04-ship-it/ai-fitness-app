/* static/js/dashboard.js
   Dashboard behaviour: week tabs, preview card, missed workout controls
   Depends: none (fetches from /api/get_plan)
*/
(function () {
    'use strict';

    // ----- DOM cache -----
    const weekTabsContainer = document.querySelector('.week-tabs');
    const previewTitle = document.getElementById('preview-title');
    const exerciseList = document.getElementById('exercise-list');
    const startWorkoutBtn = document.getElementById('start-workout-btn');
    const missedDoTodayBtn = document.getElementById('do-today-btn'); // optional
    const container = document.querySelector('.container');

    if (!weekTabsContainer || !previewTitle || !exerciseList || !startWorkoutBtn) {
        // Not on dashboard page; nothing to do
        return;
    }

    // ----- State -----
    const state = {
        weeklyPlan: {},   // will be populated by API
        today: new Date(),
        dayNames: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    };

    // ----- Helpers -----
    function formatShortDayName(date) {
        return state.dayNames[date.getDay()].substring(0, 3);
    }

    function getFirstDayOfWeek(date) {
        const d = new Date(date);
        d.setDate(d.getDate() - d.getDay()); // Sunday as first day of week
        d.setHours(0,0,0,0);
        return d;
    }

    async function fetchJson(url, opts = {}) {
        try {
            const res = await fetch(url, opts);
            if (!res.ok) {
                throw new Error(`HTTP ${res.status} - ${res.statusText}`);
            }
            return await res.json();
        } catch (err) {
            console.error('fetchJson error:', err);
            throw err;
        }
    }

    // ----- Rendering -----
    function createDayTabElements() {
        // Build 7 tabs starting from first day of week (Sunday)
        const frag = document.createDocumentFragment();
        const firstDay = getFirstDayOfWeek(state.today);

        for (let i = 0; i < 7; i++) {
            const date = new Date(firstDay);
            date.setDate(firstDay.getDate() + i);

            const tab = document.createElement('button');
            tab.className = 'tab';
            tab.type = 'button';
            tab.dataset.day = state.dayNames[date.getDay()]; // full day name, e.g., "Monday"

            const dayNameEl = document.createElement('div');
            dayNameEl.className = 'day-name';
            dayNameEl.textContent = formatShortDayName(date);

            const dayDateEl = document.createElement('div');
            dayDateEl.className = 'day-date';
            dayDateEl.textContent = date.getDate();

            tab.appendChild(dayNameEl);
            tab.appendChild(dayDateEl);

            if (date.toDateString() === state.today.toDateString()) {
                tab.classList.add('active');
            }

            frag.appendChild(tab);
        }
        // clear and append
        weekTabsContainer.innerHTML = '';
        weekTabsContainer.appendChild(frag);
    }

    function clearPreview() {
        previewTitle.textContent = "No workout selected";
        exerciseList.innerHTML = '';
        startWorkoutBtn.disabled = true;
        startWorkoutBtn.textContent = 'Start Workout';
        startWorkoutBtn.onclick = null;
    }

    function renderPreviewForDay(dayName) {
        // dayName is like "Monday"
        const plan = state.weeklyPlan[dayName];
        const isToday = dayName === state.dayNames[state.today.getDay()];

        if (!plan || !plan.exercises || plan.exercises.length === 0) {
            previewTitle.textContent = `${dayName}: Rest Day`;
            exerciseList.innerHTML = '<li>Enjoy your recovery!</li>';
            startWorkoutBtn.textContent = 'Rest Day';
            startWorkoutBtn.disabled = true;
            startWorkoutBtn.onclick = null;
            return;
        }

        previewTitle.textContent = `${dayName}'s Workout: ${plan.workout_name || 'Workout'}`;
        exerciseList.innerHTML = plan.exercises.map(ex => `<li>${escapeHtml(ex)}</li>`).join('');

        if (isToday) {
            startWorkoutBtn.textContent = 'Start Workout';
            startWorkoutBtn.disabled = false;
            startWorkoutBtn.onclick = () => {
                // navigate to workout route; use pathname-friendly day name
                window.location.href = `/workout/${encodeURIComponent(dayName)}`;
            };
        } else {
            startWorkoutBtn.textContent = 'Preview Only';
            startWorkoutBtn.disabled = true;
            startWorkoutBtn.onclick = null;
        }
    }

    // simple escaping to avoid injection via server values
    function escapeHtml(str = '') {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // ----- Event handlers -----
    function onWeekTabClick(e) {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        // mark active
        weekTabsContainer.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const dayName = tab.dataset.day;
        renderPreviewForDay(dayName);
    }

    // missed-workout optional button (if present in DOM)
    function attachMissedWorkoutHandler() {
        if (!missedDoTodayBtn) return;
        missedDoTodayBtn.addEventListener('click', () => {
            // find today's tab and simulate click so preview updates & button becomes active
            const todayName = state.dayNames[state.today.getDay()];
            const todayTab = weekTabsContainer.querySelector(`.tab[data-day="${todayName}"]`);
            if (todayTab) {
                todayTab.click();
            }
            // Scroll into view a little (mobile friendly)
            todayTab?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    // ----- Initialization -----
    async function init() {
        try {
            createDayTabElements();
            // fetch plan
            const planData = await fetchJson('/api/get_plan');
            // planData is expected as { Monday: { workout_name, exercises: [...] }, ... }
            state.weeklyPlan = planData || {};
            // show today's preview by default
            const todayName = state.dayNames[state.today.getDay()];
            renderPreviewForDay(todayName);
        } catch (err) {
            console.error('Failed to initialize dashboard:', err);
            previewTitle.textContent = "Could not load plan. Please refresh.";
            exerciseList.innerHTML = '<li class="error">Unable to load workout data.</li>';
            startWorkoutBtn.disabled = true;
        }

        // attach events
        weekTabsContainer.addEventListener('click', onWeekTabClick);
        attachMissedWorkoutHandler();

        // Accessibility: keyboard navigation of tabs
        weekTabsContainer.addEventListener('keydown', (e) => {
            const active = weekTabsContainer.querySelector('.tab.active');
            if (!active) return;
            let newIndex;
            const tabs = Array.from(weekTabsContainer.querySelectorAll('.tab'));
            const idx = tabs.indexOf(active);
            if (e.key === 'ArrowRight') newIndex = Math.min(tabs.length - 1, idx + 1);
            if (e.key === 'ArrowLeft') newIndex = Math.max(0, idx - 1);
            if (typeof newIndex === 'number' && newIndex !== idx) {
                tabs[newIndex].click();
                tabs[newIndex].focus();
            }
        });
    }

    // Run init on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', init);
})();

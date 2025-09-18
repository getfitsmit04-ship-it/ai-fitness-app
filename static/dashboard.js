// static/js/dashboard.js
(function () {
    'use strict';

    // ----- DOM Elements -----
    const weekTabsContainer = document.querySelector('.week-tabs');
    const previewTitle = document.getElementById('preview-title');
    const exerciseList = document.getElementById('exercise-list');
    const startWorkoutBtn = document.getElementById('start-workout-btn');
    const missedDoTodayBtn = document.getElementById('do-today-btn');

    if (!weekTabsContainer || !previewTitle || !exerciseList || !startWorkoutBtn) return;

    // ----- State -----
    const state = {
        weeklyPlan: {},
        today: new Date(),
        dayNames: ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    };

    // ----- Helpers -----
    const escapeHtml = str => String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;').replace(/'/g,'&#039;');

    const formatShortDayName = date => state.dayNames[date.getDay()].substring(0,3);

    const getTodayName = () => state.dayNames[state.today.getDay()];

    async function fetchJson(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    }

    // ----- Render Tabs & Preview -----
    function createDayTabs() {
        const frag = document.createDocumentFragment();
        const todayName = getTodayName();
        state.dayNames.forEach(dayName => {
            const tab = document.createElement('button');
            tab.className = 'tab';
            tab.dataset.day = dayName;
            tab.textContent = dayName.substring(0,3);
            if (dayName === todayName) tab.classList.add('active');
            frag.appendChild(tab);
        });
        weekTabsContainer.innerHTML = '';
        weekTabsContainer.appendChild(frag);
    }

    function renderPreview(dayName) {
        const plan = state.weeklyPlan[dayName];
        const isToday = dayName === getTodayName();

        if (!plan || !plan.exercises?.length) {
            previewTitle.textContent = `${dayName}: Rest Day`;
            exerciseList.innerHTML = '<li>Enjoy your recovery!</li>';
            startWorkoutBtn.textContent = 'Rest Day';
            startWorkoutBtn.disabled = true;
            return;
        }

        previewTitle.textContent = `${dayName}: ${plan.workout_name || 'Workout'}`;
        exerciseList.innerHTML = plan.exercises.map(ex => `<li>${escapeHtml(ex)}</li>`).join('');
        startWorkoutBtn.textContent = isToday ? 'Start Workout' : 'Preview Only';
        startWorkoutBtn.disabled = !isToday;

        if (isToday) {
            startWorkoutBtn.onclick = () => window.location.href = `/workout/${encodeURIComponent(dayName)}`;
        } else startWorkoutBtn.onclick = null;
    }

    function attachEvents() {
        // Tab click
        weekTabsContainer.addEventListener('click', e => {
            const tab = e.target.closest('.tab');
            if (!tab) return;
            weekTabsContainer.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderPreview(tab.dataset.day);
        });

        // Keyboard nav
        weekTabsContainer.addEventListener('keydown', e => {
            const active = weekTabsContainer.querySelector('.tab.active');
            if (!active) return;
            const tabs = Array.from(weekTabsContainer.querySelectorAll('.tab'));
            const idx = tabs.indexOf(active);
            let newIdx;
            if (e.key === 'ArrowRight') newIdx = Math.min(tabs.length-1, idx+1);
            if (e.key === 'ArrowLeft') newIdx = Math.max(0, idx-1);
            if (newIdx !== undefined && newIdx !== idx) {
                tabs[newIdx].click();
                tabs[newIdx].focus();
            }
        });

        // Missed workout button
        if (missedDoTodayBtn) {
            missedDoTodayBtn.addEventListener('click', () => {
                const todayTab = weekTabsContainer.querySelector(`.tab[data-day="${getTodayName()}"]`);
                todayTab?.click();
                todayTab?.scrollIntoView({ behavior:'smooth', block:'center' });
            });
        }
    }

    // ----- Initialization -----
    async function init() {
        createDayTabs();
        attachEvents();

        try {
            const planData = await fetchJson('/api/get_plan');
            state.weeklyPlan = planData || {};
            renderPreview(getTodayName());
        } catch (err) {
            console.error('Dashboard load failed:', err);
            previewTitle.textContent = "Failed to load plan.";
            exerciseList.innerHTML = '<li class="error">Unable to load workout data.</li>';
            startWorkoutBtn.disabled = true;
        }
    }

    document.addEventListener('DOMContentLoaded', init);

})();

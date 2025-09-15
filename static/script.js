/* static/js/script.js
   Dashboard interactivity for AI Fitness
   Displays weekly workout tabs and today's workout preview
*/

(function () {
    'use strict';

    // ----- DOM Elements -----
    const weekTabsContainer = document.querySelector('.week-tabs');
    const previewTitle = document.getElementById('preview-title');
    const exerciseList = document.getElementById('exercise-list');
    const startWorkoutBtn = document.getElementById('start-workout-btn');

    let workoutPlan = {}; // Will be fetched from API
    let today = new Date().toLocaleDateString('en-US', { weekday: 'long' });

    // ----- Initialize -----
    async function initDashboard() {
        try {
            workoutPlan = await fetchWorkoutPlan();
            populateWeekTabs();
            showWorkoutPreview(today);
        } catch (err) {
            console.error('Error loading dashboard:', err);
            previewTitle.textContent = "Failed to load today's workout.";
        }
    }

    // ----- Fetch workout plan from server -----
    async function fetchWorkoutPlan() {
        const res = await fetch('/api/get_plan');
        if (!res.ok) throw new Error('Failed to fetch plan');
        return await res.json();
    }

    // ----- Populate week tabs dynamically -----
    function populateWeekTabs() {
        weekTabsContainer.innerHTML = '';
        const daysOfWeek = Object.keys(workoutPlan);
        daysOfWeek.forEach(day => {
            const tab = document.createElement('button');
            tab.textContent = day;
            tab.className = day === today ? 'active' : '';
            tab.addEventListener('click', () => showWorkoutPreview(day));
            weekTabsContainer.appendChild(tab);
        });
    }

    // ----- Show workout preview for a given day -----
    function showWorkoutPreview(day) {
        // Highlight active tab
        weekTabsContainer.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
        const activeTab = Array.from(weekTabsContainer.children).find(btn => btn.textContent === day);
        if (activeTab) activeTab.classList.add('active');

        const workout = workoutPlan[day];
        if (!workout || !workout.exercises.length) {
            previewTitle.textContent = `${day}: Rest Day!`;
            exerciseList.innerHTML = '';
            startWorkoutBtn.disabled = true;
            return;
        }

        previewTitle.textContent = `${day}: ${workout.workout_name}`;
        exerciseList.innerHTML = '';
        workout.exercises.forEach((exName, i) => {
            const li = document.createElement('li');
            li.innerHTML = `<b>${i + 1}.</b> ${exName} <br> <i>Instructions: Move carefully, lift safely, and have fun!</i>`;
            exerciseList.appendChild(li);
        });

        startWorkoutBtn.disabled = false;

        // Attach click event to start workout
        startWorkoutBtn.onclick = () => {
            window.location.href = `/workout/${day}`;
        };
    }

    // ----- Initialize on DOM ready -----
    document.addEventListener('DOMContentLoaded', initDashboard);

})();

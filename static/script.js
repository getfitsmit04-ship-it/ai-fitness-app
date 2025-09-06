document.addEventListener('DOMContentLoaded', function() {
    // Ensure this script only runs on the dashboard page
    if (document.querySelector('.week-tabs')) {
        const today = new Date();
        const weekTabsContainer = document.querySelector('.week-tabs');
        const previewTitle = document.getElementById('preview-title');
        const exerciseList = document.getElementById('exercise-list');
        const startWorkoutBtn = document.getElementById('start-workout-btn');
        let weeklyPlan = {}; // This will be filled with data from the server

        const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        
        // --- Functions ---
        
        // NEW Function: Fetches the plan from our Flask API
        async function fetchWorkoutPlan() {
            try {
                // The cache-busting timestamp from the HTML is not needed here
                // as this is an API call, not a static file load.
                const response = await fetch('/api/get_plan');
                if (!response.ok) {
                    throw new Error('Failed to fetch workout plan from server');
                }
                weeklyPlan = await response.json();
                
                // After fetching the REAL data, build the page
                generateWeekTabs();
                updatePreview(dayNames[today.getDay()]);

            } catch (error) {
                console.error("Error fetching workout plan:", error);
                previewTitle.textContent = "Could not load plan. Please refresh.";
            }
        }

        // This function creates the clickable day tabs
        function generateWeekTabs() {
            weekTabsContainer.innerHTML = '';
            const firstDayOfWeek = new Date(today);
            firstDayOfWeek.setDate(today.getDate() - today.getDay());

            for (let i = 0; i < 7; i++) {
                const date = new Date(firstDayOfWeek);
                date.setDate(firstDayOfWeek.getDate() + i);
                
                const dayName = dayNames[date.getDay()];
                const dayDate = date.getDate();

                const tab = document.createElement('div');
                tab.classList.add('tab');
                tab.dataset.day = dayName;

                const dayNameEl = document.createElement('div');
                dayNameEl.classList.add('day-name');
                dayNameEl.textContent = dayName.substring(0, 3);
                
                const dayDateEl = document.createElement('div');
                dayDateEl.classList.add('day-date');
                dayDateEl.textContent = dayDate;

                tab.appendChild(dayNameEl);
                tab.appendChild(dayDateEl);

                if (date.toDateString() === today.toDateString()) {
                    tab.classList.add('active');
                }
                
                weekTabsContainer.appendChild(tab);
            }
        }

        // This function updates the preview card based on the selected day
        function updatePreview(dayName) {
            const workout = weeklyPlan[dayName];
            const isToday = dayName === dayNames[today.getDay()];
            
            // Check if a workout exists and has exercises
            if (workout && workout.exercises && workout.exercises.length > 0) {
                previewTitle.textContent = `${dayName}'s Workout: ${workout.workout_name}`;
                exerciseList.innerHTML = workout.exercises.map(ex => `<li>${ex}</li>`).join('');
                
                if (isToday) {
                    startWorkoutBtn.textContent = 'Start Workout';
                    // We will add functionality to this button later
                    startWorkoutBtn.disabled = false;
                    startWorkoutBtn.onclick = () => { window.location.href = `/workout/${dayName}`; };
                } else {
                    startWorkoutBtn.textContent = 'Preview Only';
                    startWorkoutBtn.disabled = true;
                }

            } else { // This is for Rest Days
                previewTitle.textContent = `${dayName}: Rest Day`;
                exerciseList.innerHTML = '<li>Enjoy your recovery!</li>';
                startWorkoutBtn.textContent = 'Rest Day';
                startWorkoutBtn.disabled = true;
            }
        }

        // --- Event Listeners ---
        weekTabsContainer.addEventListener('click', (e) => {
            const clickedTab = e.target.closest('.tab');
            if (clickedTab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                clickedTab.classList.add('active');
                updatePreview(clickedTab.dataset.day);
            }
        });

        // --- Initial Load ---
        // This is the most important change: call the function that gets server data.
        fetchWorkoutPlan();
    }
});
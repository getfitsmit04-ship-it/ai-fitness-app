/* static/js/workout.js
   Handles workout session interactivity
   Step-by-step exercise guidance with simple explanations
*/

(function () {
    'use strict';

    // ----- DOM Elements -----
    const exerciseNameEl = document.getElementById('exercise-name');
    const exerciseGifEl = document.getElementById('exercise-gif');
    const exerciseDetailsEl = document.getElementById('exercise-details');
    const loggingInterfaceEl = document.getElementById('logging-interface');
    const instructionsPanelEl = document.getElementById('instructions-panel');
    const exerciseInstructionsEl = document.getElementById('exercise-instructions');
    const progressBarEl = document.getElementById('progress-bar');

    const prevBtn = document.getElementById('prev-exercise-btn');
    const nextBtn = document.getElementById('next-exercise-btn');
    const restOverlayEl = document.getElementById('rest-timer-overlay');
    const timerCountdownEl = document.getElementById('timer-countdown');
    const skipRestBtn = document.getElementById('skip-rest-btn');
    const timerSoundEl = document.getElementById('timer-sound');
    const sessionSummaryEl = document.querySelector('.session-summary');
    const caloriesBurnedEl = document.getElementById('calories-burned');
    const weightLogForm = document.getElementById('weight-log-form');

    // ----- Variables -----
    let exercises = workoutPlan.structure || [];
    let currentIndex = 0;
    let totalCalories = 0;

    // ----- Initialize session -----
    function initWorkout() {
        if (!exercises.length) {
            exerciseNameEl.textContent = "No exercises scheduled today!";
            nextBtn.disabled = true;
            prevBtn.disabled = true;
            return;
        }
        showExercise(currentIndex);
    }

    // ----- Display current exercise -----
    function showExercise(index) {
        const ex = exercises[index];
        if (!ex) return;

        // Progress
        progressBarEl.style.width = `${((index + 1) / exercises.length) * 100}%`;

        exerciseNameEl.textContent = `${ex.type}: ${ex.details.name}`;

        // Show media if available
        if (ex.details.gif) {
            exerciseGifEl.src = ex.details.gif;
            exerciseGifEl.style.display = 'block';
        } else {
            exerciseGifEl.style.display = 'none';
        }

        // Simple, child-friendly instructions
        exerciseInstructionsEl.innerHTML = ex.details.instructions || "<p>Move gently and carefully, like a superhero practicing!</p>";
        instructionsPanelEl.style.display = 'block';

        // Logging interface
        loggingInterfaceEl.innerHTML = `
            <div class="form-group">
                <label>Sets:</label>
                <input type="number" min="1" value="3" class="sets-input">
                <label>Reps:</label>
                <input type="number" min="1" value="10" class="reps-input">
                <label>Weight (kg):</label>
                <input type="number" step="0.5" value="0" class="weight-input">
            </div>
        `;

        // Previous/Next button states
        prevBtn.disabled = index === 0;
        nextBtn.textContent = index === exercises.length - 1 ? "Finish" : "Next";
    }

    // ----- Go to previous exercise -----
    prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            showExercise(currentIndex);
        }
    });

    // ----- Go to next exercise -----
    nextBtn.addEventListener('click', () => {
        const ex = exercises[currentIndex];
        const sets = parseInt(document.querySelector('.sets-input').value) || 0;
        const reps = parseInt(document.querySelector('.reps-input').value) || 0;
        const weight = parseFloat(document.querySelector('.weight-input').value) || 0;

        // Estimate calories burned: simple formula
        totalCalories += sets * reps * (weight || 1) * 0.1;

        // Attach logged data to exercise
        ex.log = { sets, reps, weight };

        if (currentIndex < exercises.length - 1) {
            // Start rest timer before next exercise
            startRestTimer(90, () => {
                currentIndex++;
                showExercise(currentIndex);
            });
        } else {
            // Workout complete
            showSessionSummary();
        }
    });

    // ----- Rest timer -----
    function startRestTimer(seconds, callback) {
        restOverlayEl.style.display = 'flex';
        let remaining = seconds;
        timerCountdownEl.textContent = remaining;

        timerSoundEl.play().catch(() => {});

        const timerInterval = setInterval(() => {
            remaining--;
            timerCountdownEl.textContent = remaining;
            if (remaining <= 0) {
                clearInterval(timerInterval);
                restOverlayEl.style.display = 'none';
                callback();
            }
        }, 1000);

        skipRestBtn.onclick = () => {
            clearInterval(timerInterval);
            restOverlayEl.style.display = 'none';
            callback();
        };
    }

    // ----- Session summary -----
    function showSessionSummary() {
        exerciseNameEl.textContent = "Workout Complete!";
        exerciseGifEl.style.display = 'none';
        exerciseDetailsEl.style.display = 'none';
        loggingInterfaceEl.style.display = 'none';
        instructionsPanelEl.style.display = 'none';
        prevBtn.style.display = 'none';
        nextBtn.style.display = 'none';
        progressBarEl.style.width = '100%';

        caloriesBurnedEl.textContent = Math.round(totalCalories);
        sessionSummaryEl.style.display = 'block';
    }

    // ----- Submit today's weight -----
    weightLogForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const todaysWeight = parseFloat(document.getElementById('todays-weight').value) || null;

        // Prepare log details
        const logDetails = {};
        exercises.forEach(ex => {
            if (ex.log) logDetails[ex.details.name] = ex.log;
        });

        try {
            const res = await fetch('/api/save_workout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dayOfWeek: today,
                    logDetails,
                    todaysWeight
                })
            });

            if (res.ok) {
                alert('Workout saved successfully! Keep up the great work!');
                window.location.href = '/dashboard';
            } else {
                alert('Error saving workout. Please try again.');
            }
        } catch (err) {
            console.error(err);
            alert('Error saving workout. Please try again.');
        }
    });

    // ----- Initialize -----
    document.addEventListener('DOMContentLoaded', initWorkout);

})();

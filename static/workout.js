document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('workout-session')) {
        const exerciseNameEl = document.getElementById('exercise-name');
        const progressBarEl = document.getElementById('progress-bar');
        const exerciseGif = document.getElementById('exercise-gif');
        const detailsEl = document.getElementById('exercise-details');
        const loggingEl = document.getElementById('logging-interface');
        const instructionsPanel = document.getElementById('instructions-panel');
        const instructionsEl = document.getElementById('exercise-instructions');
        const prevBtn = document.getElementById('prev-exercise-btn');
        const nextBtn = document.getElementById('next-exercise-btn');
        const sessionSummaryEl = document.querySelector('.session-summary');
        const workoutCardEl = document.querySelector('.workout-card');
        const restOverlay = document.getElementById('rest-timer-overlay');
        const countdownEl = document.getElementById('timer-countdown');
        const skipRestBtn = document.getElementById('skip-rest-btn');
        const timerSound = document.getElementById('timer-sound');
        let currentExerciseIndex = 0, sessionLog = {}, totalCalories = 0, restTimerInterval;
        const totalExercises = workoutPlan.structure.length;
        const dayOfWeek = new URL(window.location.href).pathname.split('/').pop();
        const savedIndex = localStorage.getItem(`currentExerciseIndex_${dayOfWeek}`);
        const savedLog = localStorage.getItem(`sessionLog_${dayOfWeek}`);
        const savedCalories = localStorage.getItem(`totalCalories_${dayOfWeek}`);
        if (savedIndex) currentExerciseIndex = parseInt(savedIndex, 10);
        if (savedLog) sessionLog = JSON.parse(savedLog);
        if (savedCalories) totalCalories = parseFloat(savedCalories);
        const METS_VALUES = { 'Warm-up': 3.5, 'Main': 5.0, 'Cardio': 7.0, 'Cool-down': 2.5 };
        function calculateCalories(exercise, weightKg) {
            const mets = METS_VALUES[exercise.type] || 4.0;
            let durationMinutes = 5;
            if (exercise.type === 'Main') { const sets = parseInt(exercise.target.split(' ')[0], 10); durationMinutes = sets * 1.5; } 
            else if (exercise.duration) { durationMinutes = parseInt(exercise.duration.split('-')[0], 10); }
            return Math.round((mets * 3.5 * weightKg) / 200 * durationMinutes);
        }
        function saveProgress() { localStorage.setItem(`currentExerciseIndex_${dayOfWeek}`, currentExerciseIndex); localStorage.setItem(`sessionLog_${dayOfWeek}`, JSON.stringify(sessionLog)); localStorage.setItem(`totalCalories_${dayOfWeek}`, totalCalories); }
        function clearProgress() { localStorage.removeItem(`currentExerciseIndex_${dayOfWeek}`); localStorage.removeItem(`sessionLog_${dayOfWeek}`); localStorage.removeItem(`totalCalories_${dayOfWeek}`); }
        function startRestTimer(durationString) {
            let seconds = 60;
            if (durationString) { const parts = durationString.match(/\d+/g); if (parts) seconds = parseInt(parts[0], 10); }
            countdownEl.textContent = seconds; restOverlay.style.display = 'flex';
            restTimerInterval = setInterval(() => {
                seconds--; countdownEl.textContent = seconds;
                if (seconds <= 0) { timerSound.play(); clearInterval(restTimerInterval); restOverlay.style.display = 'none'; moveToNextExercise(); }
            }, 1000);
        }
        function moveToNextExercise() { if (currentExerciseIndex < totalExercises - 1) { currentExerciseIndex++; displayExercise(currentExerciseIndex); saveProgress(); } else { showSummary(); } }
        function displayExercise(index) {
            const exercise = workoutPlan.structure[index]; const exerciseDetails = exercise.details;
            exerciseNameEl.textContent = `(${index + 1}/${totalExercises}) ${exerciseDetails.name}`;
            progressBarEl.style.width = `${((index + 1) / totalExercises) * 100}%`;
            detailsEl.innerHTML = ''; loggingEl.innerHTML = ''; instructionsPanel.style.display = 'none'; exerciseGif.style.display = 'none';
            
            // *** THIS IS THE FIX ***
            // Show GIF and instructions if they exist
            if (exerciseDetails.gif_url) {
                exerciseGif.src = exerciseDetails.gif_url;
                exerciseGif.style.display = 'block';
            }
             if (exerciseDetails.instructions) {
                instructionsPanel.style.display = 'block';
                instructionsEl.innerHTML = exerciseDetails.instructions;
            }
            // *** END OF FIX ***

            if (exercise.type === 'Main') {
                detailsEl.innerHTML = `<p><strong>Target:</strong> ${exercise.target}</p>`;
                const sets = parseInt(exercise.target.split(' ')[0], 10);
                for (let i = 1; i <= sets; i++) {
                    const log = sessionLog[exerciseDetails.name]?.[i] || { weight: '', reps: '' };
                    loggingEl.innerHTML += `<div class="set-row"><span class="set-label">Set ${i}</span><div class="form-group"><label>Weight (kg)</label><input type="number" data-set="${i}" data-type="weight" value="${log.weight}" placeholder="kg"></div><div class="form-group"><label>Reps</label><input type="number" data-set="${i}" data-type="reps" value="${log.reps}" placeholder="reps"></div></div>`;
                }
            } else { detailsEl.innerHTML = `<p><strong>Duration:</strong> ${exercise.duration}</p>`; }
            
            prevBtn.disabled = index === 0;
            const isLastExercise = index === totalExercises - 1;
            nextBtn.textContent = isLastExercise ? "Finish Workout" : "Complete & Rest";
            if (exercise.type !== 'Main') { nextBtn.textContent = isLastExercise ? "Finish Workout" : "Next Step"; }
        }
        function showSummary() { workoutCardEl.style.display = 'none'; document.querySelector('.workout-header').style.display = 'none'; sessionSummaryEl.style.display = 'block'; document.getElementById('calories-burned').textContent = totalCalories; }
        nextBtn.addEventListener('click', () => {
            const exercise = workoutPlan.structure[currentExerciseIndex]; const caloriesBurned = calculateCalories(exercise, userProfile.weight); totalCalories += caloriesBurned;
            const exerciseName = exercise.details.name;
            if (!sessionLog[exerciseName]) sessionLog[exerciseName] = {}; sessionLog[exerciseName].caloriesBurned = caloriesBurned;
            alert(`Great work on ${exerciseName}!\nApproximate calories burned: ${caloriesBurned}`);
            if (exercise.type === 'Main' && currentExerciseIndex < totalExercises - 1) { startRestTimer(exercise.rest); } else { moveToNextExercise(); }
        });
        skipRestBtn.addEventListener('click', () => { clearInterval(restTimerInterval); restOverlay.style.display = 'none'; moveToNextExercise(); });
        prevBtn.addEventListener('click', () => { if (currentExerciseIndex > 0) { currentExerciseIndex--; displayExercise(currentExerciseIndex); } });
        loggingEl.addEventListener('change', (e) => {
            if (e.target.tagName === 'INPUT') {
                const exerciseName = workoutPlan.structure[currentExerciseIndex].details.name;
                const set = e.target.dataset.set; const type = e.target.dataset.type; const value = e.target.value;
                if (!sessionLog[exerciseName]) sessionLog[exerciseName] = {}; if (!sessionLog[exerciseName][set]) sessionLog[exerciseName][set] = { weight: '', reps: '' };
                sessionLog[exerciseName][set][type] = value;
                saveProgress();
            }
        });
        document.getElementById('weight-log-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = { dayOfWeek: dayOfWeek, logDetails: sessionLog, todaysWeight: document.getElementById('todays-weight').value };
            try {
                const response = await fetch('/api/save_workout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                if (!response.ok) throw new Error('Server responded with an error');
                alert("Workout saved! Your new plan is ready for next week."); clearProgress(); window.location.href = '/dashboard';
            } catch (error) { console.error("Failed to save workout:", error); alert("Could not save workout."); }
        });
        displayExercise(currentExerciseIndex);
    }
});
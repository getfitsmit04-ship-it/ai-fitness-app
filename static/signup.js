document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.querySelector('form[action="/signup"]');
    if (!signupForm) {
        return;
    }
    
    // --- DOM Elements ---
    const allRequiredInputs = signupForm.querySelectorAll('input[required], select[required]');
    const workoutDayCheckboxes = signupForm.querySelectorAll('input[name="workout_days"]');
    const physiqueGoalCheckboxes = signupForm.querySelectorAll('input[name="physique_goal"]');
    const submitButton = signupForm.querySelector('button[type="submit"]');

    const previousLogSection = document.getElementById('previous-log-section');
    const daySelectors = previousLogSection.querySelectorAll('.day-selector input');
    const exerciseList = document.getElementById('exercise-list-dynamic');

    // --- Initial State ---
    submitButton.disabled = true;
    submitButton.textContent = 'Please Fill Out Your Profile';

    // --- Functions ---
    function validateForm() {
        let allValid = true;
        
        allRequiredInputs.forEach(input => {
            if (!input.value.trim()) {
                allValid = false;
            }
        });

        const oneDaySelected = Array.from(workoutDayCheckboxes).some(cb => cb.checked);
        if (!oneDaySelected) {
            allValid = false;
        }

        const oneGoalSelected = Array.from(physiqueGoalCheckboxes).some(cb => cb.checked);
        if (!oneGoalSelected) {
            allValid = false;
        }
        
        if (allValid) {
            submitButton.disabled = false;
            submitButton.textContent = 'Create Account & Start';
        } else {
            submitButton.disabled = true;
            submitButton.textContent = 'Please Fill Out Your Profile';
        }
    }

    function handleDaySelection(e) {
        if (e.target.checked) {
            daySelectors.forEach(day => {
                if(day !== e.target) day.checked = false;
            });
            exerciseList.style.display = 'block';
        } else {
            exerciseList.style.display = 'none';
        }
    }

    function handleExerciseSelection(e) {
        const logInputs = e.target.closest('.exercise-item').querySelector('.log-inputs');
        if (e.target.checked) {
            logInputs.style.display = 'flex';
        } else {
            logInputs.style.display = 'none';
        }
    }

    // --- Event Listeners ---
    signupForm.addEventListener('input', validateForm);
    signupForm.addEventListener('change', validateForm);

    daySelectors.forEach(selector => selector.addEventListener('change', handleDaySelection));

    document.querySelectorAll('.exercise-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleExerciseSelection);
    });

    // --- Initial Call ---
    validateForm();
});
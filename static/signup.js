// Only run this script on the signup page
const signupForm = document.querySelector('form[action="/signup"]');
if (!signupForm) return;
// --- DOM Elements ---
const allRequiredInputs = signupForm.querySelectorAll('[required]');
const workoutDayCheckboxes = signupForm.querySelectorAll('input[name="workout_days"]');
const physiqueGoalCheckboxes = signupForm.querySelectorAll('input[name="physique_goal"]');
const submitButton = signupForm.querySelector('button[type="submit"]');

const previousLogSection = document.getElementById('previous-log-section');
const daySelectors = previousLogSection.querySelectorAll('.day-selector input');
const exerciseLists = previousLogSection.querySelectorAll('.exercise-list');

// --- Initial State ---
submitButton.disabled = true;
submitButton.textContent = 'Please Fill Out Your Profile';

// --- Functions ---

function validateForm() {
    let allValid = true;
    // Check standard required inputs
    allRequiredInputs.forEach(input => {
        if (!input.value.trim()) {
            allValid = false;
        }
    });

    // Check that at least one workout day is selected
    const oneDaySelected = Array.from(workoutDayCheckboxes).some(cb => cb.checked);
    if (!oneDaySelected) allValid = false;

    // Check that at least one physique goal is selected
    const oneGoalSelected = Array.from(physiqueGoalCheckboxes).some(cb => cb.checked);
    if (!oneGoalSelected) allValid = false;
    
    if (allValid) {
        submitButton.disabled = false;
        submitButton.textContent = 'Create Account & Start';
    } else {
        submitButton.disabled = true;
        submitButton.textContent = 'Please Fill Out Your Profile';
    }
}

function handleDaySelection(e) {
    const selectedDay = e.target.value;
    const targetListId = `exercise-list-${selectedDay.toLowerCase()}`;

    // Hide all exercise lists
    exerciseLists.forEach(list => list.style.display = 'none');

    if (e.target.checked) {
        // Uncheck other days
        daySelectors.forEach(day => {
            if(day !== e.target) day.checked = false;
        });
        // Show the target list
        const targetList = document.getElementById(targetListId);
        if (targetList) targetList.style.display = 'block';
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
signupForm.addEventListener('change', validateForm); // For selects and checkboxes

daySelectors.forEach(selector => selector.addEventListener('change', handleDaySelection));

document.querySelectorAll('.exercise-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', handleExerciseSelection);
});

// --- Initial Call ---
validateForm();
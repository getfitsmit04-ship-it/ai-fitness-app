/* static/js/signup.js
   Multi-step signup form logic for AI Fitness
   Handles step navigation, validation, and dynamic exercise log display
*/

(function () {
    'use strict';

    // ----- DOM Elements -----
    const form = document.querySelector('.auth-form');
    const steps = document.querySelectorAll('.form-step');
    const submitBtn = form.querySelector('button[type="submit"]');
    const prevDayCheckboxes = document.querySelectorAll('input[name="prev_day"]');
    const exerciseListContainer = document.getElementById('exercise-list-dynamic');

    let currentStep = 0;

    // ----- Initialize -----
    function initForm() {
        addNavigationButtons();
        showStep(currentStep);
        submitBtn.disabled = true;
        attachEventListeners();
    }

    // ----- Add Next/Previous Buttons Dynamically -----
    function addNavigationButtons() {
        steps.forEach((step, index) => {
            // Skip submit button step
            if (index < steps.length - 1) {
                const nextBtn = document.createElement('button');
                nextBtn.type = 'button';
                nextBtn.textContent = 'Next';
                nextBtn.classList.add('next-btn');
                step.appendChild(nextBtn);
            }
            if (index > 0) {
                const prevBtn = document.createElement('button');
                prevBtn.type = 'button';
                prevBtn.textContent = 'Previous';
                prevBtn.classList.add('prev-btn');
                step.appendChild(prevBtn);
            }
        });

        const nextBtns = form.querySelectorAll('.next-btn');
        const prevBtns = form.querySelectorAll('.prev-btn');

        nextBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (currentStep < steps.length - 1) {
                    currentStep++;
                    showStep(currentStep);
                }
            });
        });

        prevBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (currentStep > 0) {
                    currentStep--;
                    showStep(currentStep);
                }
            });
        });
    }

    // ----- Show a specific step -----
    function showStep(stepIndex) {
        steps.forEach((step, i) => {
            step.style.display = i === stepIndex ? 'block' : 'none';
        });
        checkFormCompletion();
    }

    // ----- Event Listeners -----
    function attachEventListeners() {
        // Validate form fields
        form.addEventListener('input', checkFormCompletion);
        form.addEventListener('change', checkFormCompletion);

        // Show/hide previous exercises
        prevDayCheckboxes.forEach(cb => {
            cb.addEventListener('change', handlePrevDayChange);
        });
    }

    // ----- Show exercise log inputs if a day is selected -----
    function handlePrevDayChange() {
        const anyDaySelected = Array.from(prevDayCheckboxes).some(cb => cb.checked);
        exerciseListContainer.style.display = anyDaySelected ? 'block' : 'none';
    }

    // ----- Check if all required fields are filled -----
    function checkFormCompletion() {
        let allFilled = true;

        // Step 1: Account Info
        const username = form.querySelector('#username');
        const password = form.querySelector('#password');
        if (!username.value.trim() || !password.value.trim()) allFilled = false;

        // Step 2: Personal Details
        const age = form.querySelector('#age');
        const height = form.querySelector('#height');
        const weight = form.querySelector('#weight');
        const gender = form.querySelector('#gender');
        if (!age.value || !height.value || !weight.value || !gender.value) allFilled = false;

        // Step 3: Fitness Plan
        const workoutDays = form.querySelectorAll('input[name="workout_days"]:checked');
        const physiqueGoals = form.querySelectorAll('input[name="physique_goal"]:checked');
        const duration = form.querySelector('#duration');
        const equipment = form.querySelector('#equipment');
        if (!workoutDays.length || !physiqueGoals.length || !duration.value || !equipment.value) allFilled = false;

        submitBtn.disabled = !allFilled;
    }

    // ----- Initialize on DOM ready -----
    document.addEventListener('DOMContentLoaded', initForm);

})();

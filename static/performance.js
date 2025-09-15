/* static/js/performance.js
   Performance tracking logic for AI Fitness
   Uses Chart.js to display user weight, total workout volume, and exercise progression
*/

(function () {
    'use strict';

    // ----- DOM Elements -----
    const weightChartCtx = document.getElementById('weightChart');
    const volumeChartCtx = document.getElementById('volumeChart');
    const exerciseChartsContainer = document.getElementById('exercise-charts-container');

    // ----- State -----
    let performanceData = null;

    // ----- Fetch Performance Data -----
    async function fetchPerformanceData() {
        try {
            const response = await fetch('/api/get_performance_data');
            if (!response.ok) throw new Error('Failed to fetch performance data.');
            const data = await response.json();
            performanceData = data;
            renderCharts();
        } catch (err) {
            console.error(err);
        }
    }

    // ----- Render Charts -----
    function renderCharts() {
        if (!performanceData) return;

        // 1. Bodyweight Chart
        if (weightChartCtx && performanceData.weight_logs.labels.length) {
            new Chart(weightChartCtx, {
                type: 'line',
                data: {
                    labels: performanceData.weight_logs.labels,
                    datasets: [{
                        label: 'Weight (kg)',
                        data: performanceData.weight_logs.data,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59,130,246,0.2)',
                        tension: 0.3,
                        fill: true,
                        pointRadius: 5,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: true } },
                    scales: {
                        y: { beginAtZero: false },
                        x: { ticks: { maxRotation: 45, minRotation: 0 } }
                    }
                }
            });
        }

        // 2. Total Workout Volume Chart
        if (volumeChartCtx && performanceData.volume_logs.labels.length) {
            new Chart(volumeChartCtx, {
                type: 'bar',
                data: {
                    labels: performanceData.volume_logs.labels,
                    datasets: [{
                        label: 'Total Volume (kg)',
                        data: performanceData.volume_logs.data,
                        backgroundColor: '#f97316'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: true } },
                    scales: {
                        y: { beginAtZero: true },
                        x: { ticks: { maxRotation: 45, minRotation: 0 } }
                    }
                }
            });
        }

        // 3. Individual Exercise Charts
        if (exerciseChartsContainer && performanceData.exercise_progression) {
            exerciseChartsContainer.innerHTML = '';
            Object.keys(performanceData.exercise_progression).forEach(exercise => {
                const wrapper = document.createElement('div');
                wrapper.classList.add('exercise-chart-card');
                const canvas = document.createElement('canvas');
                canvas.id = `chart-${exercise.replace(/\s+/g, '-')}`;
                wrapper.innerHTML = `<h4>${exercise}</h4>`;
                wrapper.appendChild(canvas);
                exerciseChartsContainer.appendChild(wrapper);

                const exData = performanceData.exercise_progression[exercise];
                new Chart(canvas.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: exData.labels,
                        datasets: [{
                            label: 'Estimated 1RM (kg)',
                            data: exData.data,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16,185,129,0.2)',
                            tension: 0.3,
                            fill: true,
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: true } },
                        scales: { y: { beginAtZero: true } }
                    }
                });
            });
        }
    }

    // ----- Initialize -----
    document.addEventListener('DOMContentLoaded', fetchPerformanceData);

})();

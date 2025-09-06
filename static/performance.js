document.addEventListener('DOMContentLoaded', function() {
    const weightChartCanvas = document.getElementById('weightChart');
    const volumeChartCanvas = document.getElementById('volumeChart');
    const exerciseChartsContainer = document.getElementById('exercise-charts-container');

    Chart.defaults.color = '#A0A0A0';
    Chart.defaults.borderColor = '#333333';

    async function fetchPerformanceData() {
        try {
            const response = await fetch('/api/get_performance_data');
            if (!response.ok) throw new Error('Failed to fetch performance data');
            const data = await response.json();
            
            if (data.weight_logs && data.weight_logs.labels.length > 0) createWeightChart(data.weight_logs);
            else weightChartCanvas.parentElement.innerHTML += "<p>No bodyweight data logged yet.</p>";

            if (data.volume_logs && data.volume_logs.labels.length > 0) createVolumeChart(data.volume_logs);
            else volumeChartCanvas.parentElement.innerHTML += "<p>No workout volume data yet.</p>";

            if (data.exercise_progression) createExerciseCharts(data.exercise_progression);

        } catch (error) {
            console.error("Error fetching data:", error);
            weightChartCanvas.parentElement.innerHTML = "<p>Could not load chart data.</p>";
        }
    }

    function createWeightChart(chartData) {
        new Chart(weightChartCanvas, { type: 'line', data: { labels: chartData.labels, datasets: [{ label: 'Bodyweight (kg)', data: chartData.data, borderColor: '#007BFF', backgroundColor: 'rgba(0, 123, 255, 0.1)', fill: true, tension: 0.1 }] }, options: { scales: { y: { beginAtZero: false } } } });
    }
    function createVolumeChart(chartData) {
        new Chart(volumeChartCanvas, { type: 'bar', data: { labels: chartData.labels, datasets: [{ label: 'Total Volume (kg)', data: chartData.data, backgroundColor: 'rgba(0, 123, 255, 0.7)', borderColor: '#007BFF', borderWidth: 1 }] }, options: { scales: { y: { beginAtZero: true } } } });
    }
    function createExerciseCharts(progressionData) {
        for (const exerciseName in progressionData) {
            if (progressionData[exerciseName].data.length > 1) { // Only show charts for exercises with progress
                const chartData = progressionData[exerciseName];
                const container = document.createElement('div');
                container.className = 'chart-container';
                container.innerHTML = `<h3>${exerciseName} Progress</h3><p class="chart-subtitle">Estimated 1-Rep Max (e1RM)</p><canvas id="chart-${exerciseName.replace(/\s+/g, '')}"></canvas>`;
                exerciseChartsContainer.appendChild(container);
                const canvas = document.getElementById(`chart-${exerciseName.replace(/\s+/g, '')}`);
                new Chart(canvas, { type: 'line', data: { labels: chartData.labels, datasets: [{ label: 'e1RM (kg)', data: chartData.data, borderColor: '#28a745', backgroundColor: 'rgba(40, 167, 69, 0.1)', fill: true, tension: 0.1 }] }, options: { scales: { y: { beginAtZero: false } } } });
            }
        }
    }
    if (weightChartCanvas) fetchPerformanceData();
});
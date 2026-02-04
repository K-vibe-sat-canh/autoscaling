/* =============================================================================
   AutoScaling Command Center - JavaScript
   ============================================================================= */

const API_URL = 'http://localhost:8000';

// Charts
let forecastChart = null;
let scalingChart = null;

// =============================================================================
// INITIALIZATION
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Check API status
    checkApiStatus();
    setInterval(checkApiStatus, 10000); // Check every 10s
    
    // Setup tabs
    setupTabs();
    
    // Setup slider
    const slider = document.getElementById('forecastSteps');
    const sliderValue = document.getElementById('forecastStepsValue');
    slider.addEventListener('input', () => {
        sliderValue.textContent = slider.value;
    });
    
    // Load initial metrics
    loadMetrics();
});

// =============================================================================
// API STATUS CHECK
// =============================================================================
async function checkApiStatus() {
    const statusBadge = document.getElementById('apiStatus');
    const statusText = statusBadge.querySelector('.status-text');
    
    try {
        const response = await fetch(`${API_URL}/health`, { timeout: 2000 });
        if (response.ok) {
            statusBadge.className = 'status-badge online';
            statusText.textContent = 'API ONLINE';
        } else {
            throw new Error('API error');
        }
    } catch (error) {
        statusBadge.className = 'status-badge offline';
        statusText.textContent = 'API OFFLINE';
    }
}

// =============================================================================
// TAB NAVIGATION
// =============================================================================
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            // Add active to clicked
            btn.classList.add('active');
            const tabId = btn.dataset.tab;
            document.getElementById(tabId).classList.remove('hidden');
        });
    });
}

// =============================================================================
// FORECAST
// =============================================================================
async function runForecast() {
    const steps = document.getElementById('forecastSteps').value;
    const currentServers = document.getElementById('currentServers').value;
    const resultSection = document.getElementById('forecastResult');
    
    try {
        // Show loading
        const btn = event.target;
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Đang dự báo...';
        
        // Fetch forecast
        const response = await fetch(`${API_URL}/forecast?timestamp=now&steps=${steps}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            // Update metrics
            document.getElementById('modelName').textContent = data.model;
            document.getElementById('modelRmse').textContent = data.metrics.model_rmse;
            document.getElementById('modelMape').textContent = data.metrics.model_mape;
            document.getElementById('predCount').textContent = data.predictions.length;
            
            // Draw chart
            drawForecastChart(data.predictions, currentServers);
            
            // Get scaling recommendation
            const maxPredicted = Math.max(...data.predictions.map(p => p.predicted_requests));
            await getScalingRecommendation(maxPredicted, currentServers);
            
            // Show results
            resultSection.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Forecast error:', error);
        alert('❌ Lỗi khi gọi API. Kiểm tra Backend đã chạy chưa!');
    } finally {
        // Reset button
        const btn = event.target;
        btn.disabled = false;
        btn.innerHTML = '🚀 Chạy Dự Báo';
    }
}

function drawForecastChart(predictions, currentServers) {
    const ctx = document.getElementById('forecastChart').getContext('2d');
    
    // Destroy old chart
    if (forecastChart) {
        forecastChart.destroy();
    }
    
    const labels = predictions.map(p => {
        const date = new Date(p.timestamp);
        return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    });
    const values = predictions.map(p => p.predicted_requests);
    
    const capacity = currentServers * 1000;
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Predicted Requests',
                    data: values,
                    borderColor: '#1f77b4',
                    backgroundColor: 'rgba(31, 119, 180, 0.2)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: 'Scale Up (85%)',
                    data: Array(labels.length).fill(capacity * 0.85),
                    borderColor: '#e74c3c',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Scale Down (30%)',
                    data: Array(labels.length).fill(capacity * 0.30),
                    borderColor: '#2ecc71',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: `Dự báo lưu lượng ${predictions.length * 15} phút tới`,
                    color: '#fff',
                    font: { size: 16 }
                },
                legend: {
                    labels: { color: '#b0b0b0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#b0b0b0' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                },
                y: {
                    ticks: { color: '#b0b0b0' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    title: {
                        display: true,
                        text: 'Requests',
                        color: '#b0b0b0'
                    }
                }
            }
        }
    });
}

async function getScalingRecommendation(predictedRequests, currentServers) {
    try {
        const response = await fetch(
            `${API_URL}/recommend-scaling?predicted_requests=${predictedRequests}&current_servers=${currentServers}`
        );
        const data = await response.json();
        
        const card = document.getElementById('scalingCard');
        const action = data.action;
        
        // Update card style
        card.className = 'scaling-card ' + 
            (action.includes('UP') ? 'scale-up' : action.includes('DOWN') ? 'scale-down' : 'maintain');
        
        // Update content
        card.querySelector('.scaling-icon').textContent = 
            action.includes('UP') ? '⬆️' : action.includes('DOWN') ? '⬇️' : '➡️';
        card.querySelector('.scaling-action').textContent = action;
        card.querySelector('.scaling-reason').textContent = data.reason;
        
        // Update details
        document.getElementById('targetServers').textContent = data.target_servers;
        document.getElementById('costHourly').textContent = data.cost_estimate.hourly;
        document.getElementById('costMonthly').textContent = data.cost_estimate.monthly;
        
    } catch (error) {
        console.error('Scaling recommendation error:', error);
    }
}

// =============================================================================
// COST REPORT
// =============================================================================
async function runCostReport() {
    const simHours = document.getElementById('simHours').value;
    const resultSection = document.getElementById('costResult');
    
    try {
        const btn = event.target;
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Đang tính toán...';
        
        const response = await fetch(`${API_URL}/cost-report?simulation_hours=${simHours}`);
        const data = await response.json();
        
        // Update cost cards
        const static_ = data.cost_comparison.static_deployment;
        const auto = data.cost_comparison.auto_scaling;
        const savings = data.savings;
        
        document.getElementById('staticCost').textContent = static_.total_cost;
        document.getElementById('staticServers').textContent = static_.servers;
        document.getElementById('staticHourly').textContent = static_.cost_per_hour + '/hour';
        
        document.getElementById('autoCost').textContent = auto.total_cost;
        document.getElementById('avgServers').textContent = auto.avg_servers;
        
        document.getElementById('savingsAmount').textContent = savings.amount;
        document.getElementById('savingsPercent').textContent = savings.percentage;
        document.getElementById('savingsMonthly').textContent = savings.monthly_projection;
        
        // Conclusion
        document.getElementById('conclusionText').textContent = data.conclusion;
        
        // Stats
        document.getElementById('dataPoints').textContent = data.data_points_used;
        document.getElementById('scalingEvents').textContent = data.scaling_events;
        
        // Draw scaling chart
        if (data.scaling_history && data.scaling_history.length > 0) {
            drawScalingChart(data.scaling_history);
            populateEventsTable(data.scaling_history);
        }
        
        resultSection.classList.remove('hidden');
        
    } catch (error) {
        console.error('Cost report error:', error);
        alert('❌ Lỗi khi tạo báo cáo. Kiểm tra Backend!');
    } finally {
        const btn = event.target;
        btn.disabled = false;
        btn.innerHTML = '📊 Tạo Báo Cáo Chi Phí';
    }
}

function drawScalingChart(events) {
    const ctx = document.getElementById('scalingChart').getContext('2d');
    
    if (scalingChart) {
        scalingChart.destroy();
    }
    
    const scaleUp = events.filter(e => e.action === 'scale_up');
    const scaleDown = events.filter(e => e.action === 'scale_down');
    
    scalingChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Scale Up',
                    data: scaleUp.map(e => ({
                        x: new Date(e.timestamp).getTime(),
                        y: e.to_servers
                    })),
                    backgroundColor: '#e74c3c',
                    pointRadius: 10,
                    pointStyle: 'triangle'
                },
                {
                    label: 'Scale Down',
                    data: scaleDown.map(e => ({
                        x: new Date(e.timestamp).getTime(),
                        y: e.to_servers
                    })),
                    backgroundColor: '#2ecc71',
                    pointRadius: 10,
                    pointStyle: 'triangle',
                    rotation: 180
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: `Scaling Events Timeline (${events.length} events)`,
                    color: '#fff',
                    font: { size: 16 }
                },
                legend: {
                    labels: { color: '#b0b0b0' }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            return new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
                        }
                    },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                },
                y: {
                    ticks: { color: '#b0b0b0' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    title: {
                        display: true,
                        text: 'Servers',
                        color: '#b0b0b0'
                    }
                }
            }
        }
    });
}

function populateEventsTable(events) {
    const tbody = document.querySelector('#eventsTable tbody');
    tbody.innerHTML = '';
    
    events.forEach(event => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${event.timestamp}</td>
            <td style="color: ${event.action === 'scale_up' ? '#e74c3c' : '#2ecc71'}">
                ${event.action === 'scale_up' ? '⬆️ Scale Up' : '⬇️ Scale Down'}
            </td>
            <td>${event.from_servers}</td>
            <td>${event.to_servers}</td>
            <td>${event.load.toLocaleString()}</td>
        `;
        tbody.appendChild(row);
    });
}

// =============================================================================
// METRICS
// =============================================================================
async function loadMetrics() {
    try {
        const response = await fetch(`${API_URL}/metrics`);
        const data = await response.json();
        
        // Current metrics
        document.getElementById('currentLoad').textContent = `${data.current_load.toLocaleString()} req/min`;
        document.getElementById('runningServers').textContent = data.running_servers;
        document.getElementById('cost24h').textContent = `$${data.cost_24h.toFixed(2)}`;
        
        // Model accuracy
        const acc = data.model_accuracy;
        document.getElementById('metricsRmse').textContent = acc.rmse;
        document.getElementById('metricsMae').textContent = acc.mae;
        document.getElementById('metricsMape').textContent = `${(acc.mape * 100).toFixed(1)}%`;
        
    } catch (error) {
        console.error('Metrics error:', error);
    }
}

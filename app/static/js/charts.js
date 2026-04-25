// STRIDE Doughnut Chart
let strideChart;

function initStrideChart(strideData) {
    const ctx = document.getElementById('strideChart').getContext('2d');
    const categories = Object.keys(strideData);
    const counts = Object.values(strideData);
    
    const colors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
        '#9b59b6', '#1abc9c', '#e67e22', '#34495e'
    ];
    
    if (strideChart) {
        strideChart.destroy();
    }
    
    strideChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: counts,
                backgroundColor: colors.slice(0, categories.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.raw} threats` } }
            }
        }
    });
}

// Optional: Update chart with new data via AJAX
async function refreshStrideChart() {
    const resp = await fetch('/dashboard/api/threats-data');
    const data = await resp.json();
    initStrideChart(data.stride_counts);
}

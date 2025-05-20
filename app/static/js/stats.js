

const dummyStats = {
    user: {
        attributes: {
            INT: 8, STA: 6, FCS: 7, CHA: 5, DSC: 9
        }
    },
    completion_history: {
        "2025-04-26": 2, "2025-04-27": 1, "2025-04-28": 0,
        "2025-04-29": 3, "2025-04-30": 2, "2025-05-01": 5,
        "2025-05-02": 4, "2025-05-03": 2, "2025-05-04": 3,
        "2025-05-05": 1, "2025-05-06": 0, "2025-05-07": 3,
        "2025-05-08": 2, "2025-05-09": 1
    }
};

function loadStats() {
    return fetch('/api/stats')
        .then(res => res.json())
        .catch(() => {
            console.warn("Using dummy stats data");
            return dummyStats;
        });
}
function renderAttributesChart(data) {
    const ctx = document.getElementById('attributesChart').getContext('2d');
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Intelligence (INT)', 'Stamina (STA)', 'Focus (FCS)', 'Charisma (CHA)', 'Discipline (DSC)'],
            datasets: [{
                label: 'Attributes',
                data: [
                    data.user.attributes.INT,
                    data.user.attributes.STA,
                    data.user.attributes.FCS,
                    data.user.attributes.CHA,
                    data.user.attributes.DSC
                ],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2
            }]
        },
        options: {
            scales: { r: { beginAtZero: true, ticks: { display: false } } },
            plugins: { legend: { display: false } }
        }
    });
}
function renderCompletionChart(history) {
    const data = processCompletionHistory(history);
    const ctx = document.getElementById('completionChart').getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Completed Activities',
                data: data.values,
                backgroundColor: 'rgba(75, 192, 192, 0.8)'
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Number of Activities' } },
                x: { title: { display: true, text: 'Date' } }
            },
            plugins: { title: { display: true, text: 'Daily Activity Completion' } }
        }
    });
}
function renderDisciplineChart(labelCount) {
    const data = generateDummyDisciplineData(labelCount);
    const labels = processCompletionHistory(dummyStats.completion_history).labels;
    const ctx = document.getElementById('disciplineChart').getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Discipline Factor',
                data: data,
                borderColor: 'rgba(153, 102, 255, 1)',
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 1, title: { display: true, text: 'Discipline Factor' } },
                x: { title: { display: true, text: 'Date' } }
            },
            plugins: { title: { display: true, text: 'Discipline Factor Trend' } }
        }
    });
}

function processCompletionHistory(history) {
    const labels = [];
    const values = [];
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 13);

    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        labels.push(dateStr);
        values.push(history[dateStr] || 0);
    }

    return { labels, values };
}

function generateDummyDisciplineData(length) {
    const values = [];
    let last = 0.7;
    for (let i = 0; i < length; i++) {
        const delta = (Math.random() - 0.5) * 0.2;
        last = Math.min(1, Math.max(0, last + delta));
        values.push(last);
    }
    return values;
}
document.addEventListener('DOMContentLoaded', function() {
    loadStats().then(data => {
        renderAttributesChart(data);
        renderCompletionChart(data.completion_history);
        renderDisciplineChart(14); // Always 14 days
    }).catch(error => {
        console.error('Failed to render stats:', error);
    });
});


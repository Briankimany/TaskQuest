/**
 * Stats — Chart.js visualizations
 */
var dummyStats = {
    user: { attributes: { INT: 8, STA: 6, FCS: 7, CHA: 5, DSC: 9 } },
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
        .then(function (r) { return r.json(); })
        .catch(function () { return dummyStats; });
}

function getChartColors() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        accent: isDark ? '#7EC8A0' : '#4A6741',
        warm: isDark ? '#D4A574' : '#8B6F47',
        calm: isDark ? '#7EB8DA' : '#5B7B94',
        text: isDark ? '#A0A0A0' : '#6B6B6B',
        grid: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
    };
}

function renderAttributesChart(data) {
    var c = getChartColors();
    var ctx = document.getElementById('attributesChart').getContext('2d');
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['INT', 'STA', 'FCS', 'CHA', 'DSC'],
            datasets: [{
                label: 'Attributes',
                data: [
                    data.user.attributes.INT, data.user.attributes.STA,
                    data.user.attributes.FCS, data.user.attributes.CHA,
                    data.user.attributes.DSC
                ],
                backgroundColor: c.accent + '20',
                borderColor: c.accent,
                borderWidth: 2,
                pointBackgroundColor: c.accent
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    ticks: { display: false },
                    grid: { color: c.grid },
                    pointLabels: { color: c.text, font: { size: 12, family: "'Inter', sans-serif" } }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderCompletionChart(history) {
    var c = getChartColors();
    var data = processCompletionHistory(history);
    var ctx = document.getElementById('completionChart').getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Completed',
                data: data.values,
                backgroundColor: c.accent + 'CC',
                borderRadius: 4
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, ticks: { color: c.text }, grid: { color: c.grid } },
                x: { ticks: { color: c.text, maxRotation: 45 }, grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderDisciplineChart(labelCount) {
    var c = getChartColors();
    var data = generateDummyDisciplineData(labelCount);
    var labels = processCompletionHistory(dummyStats.completion_history).labels;
    var ctx = document.getElementById('disciplineChart').getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Discipline',
                data: data,
                borderColor: c.calm,
                backgroundColor: c.calm + '20',
                fill: true,
                tension: 0.3,
                pointRadius: 3
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 1, ticks: { color: c.text }, grid: { color: c.grid } },
                x: { ticks: { color: c.text, maxRotation: 45 }, grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function processCompletionHistory(history) {
    var labels = [], values = [];
    var endDate = new Date();
    var startDate = new Date();
    startDate.setDate(endDate.getDate() - 13);
    for (var d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        var dateStr = d.toISOString().split('T')[0];
        labels.push(dateStr);
        values.push(history[dateStr] || 0);
    }
    return { labels: labels, values: values };
}

function generateDummyDisciplineData(length) {
    var values = [], last = 0.7;
    for (var i = 0; i < length; i++) {
        last = Math.min(1, Math.max(0, last + (Math.random() - 0.5) * 0.2));
        values.push(last);
    }
    return values;
}

document.addEventListener('DOMContentLoaded', function () {
    loadStats().then(function (data) {
        renderAttributesChart(data);
        renderCompletionChart(data.completion_history);
        renderDisciplineChart(14);
    }).catch(function (err) {
        console.error('Failed to render stats:', err);
    });
});

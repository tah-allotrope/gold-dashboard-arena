// Vietnam Gold & Market Dashboard — Dark Fintech Frontend

const DATA_URL = 'data.json';
const REFRESH_INTERVAL = 30 * 60 * 1000;
const FRESHNESS_THRESHOLDS = { fresh: 35 * 60 * 1000, stale: 65 * 60 * 1000 };

// Period -> max days for filtering timeseries
const PERIOD_DAYS = { '1D': 1, '1W': 7, '1M': 30, '1Y': 365, '3Y': 1095 };

// Store raw timeseries + chart instances globally
let timeseriesData = {};
let chartInstances = {};

// ---- Formatting helpers ----

function formatVietnameseNumber(value, decimalPlaces = 0) {
    if (!value && value !== 0) return '--';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '--';
    const parts = num.toFixed(decimalPlaces).split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    if (decimalPlaces > 0 && decimalPart) {
        return `${formattedInteger},${decimalPart}`;
    }
    return formattedInteger;
}

function parseTimestampToLocalTime(timestamp) {
    if (!timestamp) return null;
    const dt = new Date(timestamp);
    if (isNaN(dt.getTime())) return null;
    return dt.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}

function getFreshnessClass(timestamp) {
    const age = Date.now() - new Date(timestamp).getTime();
    if (age < FRESHNESS_THRESHOLDS.fresh) return 'fresh';
    if (age < FRESHNESS_THRESHOLDS.stale) return 'stale';
    return 'old';
}

function formatChangeBadge(el, changePercent) {
    if (changePercent === null || changePercent === undefined) {
        el.textContent = '--';
        el.className = 'change-badge';
        return;
    }
    const pct = parseFloat(changePercent);
    const sign = pct >= 0 ? '+' : '';
    el.textContent = `${sign}${formatVietnameseNumber(pct, 2)}%`;
    el.className = 'change-badge ' + (pct >= 0 ? 'positive' : 'negative');
}

// ---- Card update functions ----

function updateGoldCard(data, history) {
    if (!data) return;
    const card = document.getElementById('goldCard');
    document.getElementById('goldSell').textContent = formatVietnameseNumber(data.sell_price, 0);
    document.getElementById('goldBuy').textContent = formatVietnameseNumber(data.buy_price, 0);
    document.getElementById('goldSellSmall').textContent = formatVietnameseNumber(data.sell_price, 0);
    document.getElementById('goldUnit').textContent = data.unit || 'VND/tael';
    document.getElementById('goldSource').textContent = data.source || '--';

    // 1D change for the top badge
    const badge = document.getElementById('goldBadge');
    const dayChange = history && history.find(c => c.period === '1D');
    formatChangeBadge(badge, dayChange ? dayChange.change_percent : null);

    card.className = 'metric-card ' + getFreshnessClass(data.timestamp);
}

function updateUsdCard(data, history) {
    if (!data) return;
    const card = document.getElementById('usdCard');
    document.getElementById('usdRate').textContent = formatVietnameseNumber(data.sell_rate, 0);
    document.getElementById('usdSource').textContent = data.source || '--';

    const badge = document.getElementById('usdBadge');
    const dayChange = history && history.find(c => c.period === '1D');
    formatChangeBadge(badge, dayChange ? dayChange.change_percent : null);

    card.className = 'metric-card ' + getFreshnessClass(data.timestamp);
}

function updateBtcCard(data, history) {
    if (!data) return;
    const card = document.getElementById('btcCard');
    document.getElementById('btcRate').textContent = formatVietnameseNumber(data.btc_to_vnd, 0);
    document.getElementById('btcSource').textContent = data.source || '--';

    const changeEl = document.getElementById('btcChange');
    const activeBtn = document.querySelector('[data-chart="btc"] .period-btn.active');
    const activePeriod = activeBtn ? activeBtn.dataset.period : '1M';
    const periodChange = history && history.find(c => c.period === activePeriod);
    if (periodChange && periodChange.change_percent !== null) {
        const pct = parseFloat(periodChange.change_percent);
        const sign = pct >= 0 ? '+' : '';
        const arrow = pct >= 0 ? '↗' : '↘';
        changeEl.textContent = `${arrow} ${sign}${formatVietnameseNumber(pct, 2)}%`;
        changeEl.className = 'chart-change ' + (pct >= 0 ? 'positive' : 'negative');
    } else {
        changeEl.textContent = '--';
        changeEl.className = 'chart-change';
    }

    card.className = 'chart-card ' + getFreshnessClass(data.timestamp);
}

function resetGoldCard() {
    const card = document.getElementById('goldCard');
    document.getElementById('goldSell').textContent = '--';
    document.getElementById('goldBuy').textContent = '--';
    document.getElementById('goldSellSmall').textContent = '--';
    document.getElementById('goldUnit').textContent = 'VND/tael';
    document.getElementById('goldSource').textContent = 'Unavailable';
    formatChangeBadge(document.getElementById('goldBadge'), null);
    card.className = 'metric-card old';
}

function resetUsdCard() {
    const card = document.getElementById('usdCard');
    document.getElementById('usdRate').textContent = '--';
    document.getElementById('usdSource').textContent = 'Unavailable';
    formatChangeBadge(document.getElementById('usdBadge'), null);
    card.className = 'metric-card old';
}

function resetBtcCard() {
    const card = document.getElementById('btcCard');
    document.getElementById('btcRate').textContent = '--';
    document.getElementById('btcSource').textContent = 'Unavailable';
    const changeEl = document.getElementById('btcChange');
    changeEl.textContent = '--';
    changeEl.className = 'chart-change';
    card.className = 'chart-card old';
}

function resetVn30Card() {
    const card = document.getElementById('vn30Card');
    document.getElementById('vn30Value').textContent = '--';
    document.getElementById('vn30Source').textContent = 'Unavailable';
    const changeEl = document.getElementById('vn30Change');
    changeEl.textContent = '--';
    changeEl.className = 'chart-change';
    card.className = 'chart-card old';
}

function updateVn30Card(data, history) {
    if (!data) return;
    const card = document.getElementById('vn30Card');
    document.getElementById('vn30Value').textContent = formatVietnameseNumber(data.index_value, 2);
    document.getElementById('vn30Source').textContent = data.source || '--';

    const changeEl = document.getElementById('vn30Change');
    const activeBtn = document.querySelector('[data-chart="vn30"] .period-btn.active');
    const activePeriod = activeBtn ? activeBtn.dataset.period : '1M';
    const periodChange = history && history.find(c => c.period === activePeriod);
    if (periodChange && periodChange.change_percent !== null) {
        const pct = parseFloat(periodChange.change_percent);
        const sign = pct >= 0 ? '+' : '';
        const arrow = pct >= 0 ? '↗' : '↘';
        changeEl.textContent = `${arrow} ${sign}${formatVietnameseNumber(pct, 2)}%`;
        changeEl.className = 'chart-change ' + (pct >= 0 ? 'positive' : 'negative');
    } else {
        changeEl.textContent = '--';
        changeEl.className = 'chart-change';
    }

    card.className = 'chart-card ' + getFreshnessClass(data.timestamp);
}

// ---- History badges (metric cards) ----

function updateHistoryBadges(containerId, changes) {
    const container = document.getElementById(containerId);
    if (!container || !changes) return;
    let hasAnyData = false;

    changes.forEach(change => {
        const badge = container.querySelector(`[data-period="${change.period}"]`);
        if (!badge) return;
        const valueEl = badge.querySelector('.period-value');
        if (!valueEl) return;

        if (change.change_percent === null || change.change_percent === undefined) {
            valueEl.textContent = 'N/A';
            badge.className = 'history-badge badge-na';
            return;
        }
        hasAnyData = true;
        const pct = parseFloat(change.change_percent);
        const sign = pct >= 0 ? '+' : '';
        valueEl.textContent = `${sign}${formatVietnameseNumber(pct, 2)}%`;
        badge.className = 'history-badge ' + (pct >= 0 ? 'badge-positive' : 'badge-negative');
    });

    let hint = container.querySelector('.history-hint');
    if (!hasAnyData) {
        if (!hint) {
            hint = document.createElement('div');
            hint.className = 'history-hint';
            hint.textContent = 'Historical data accumulating...';
            container.appendChild(hint);
        }
    } else if (hint) {
        hint.remove();
    }
}

// ---- Chart rendering ----

function filterTimeseries(series, periodKey) {
    if (!series || !series.length) return { labels: [], values: [] };
    const days = PERIOD_DAYS[periodKey] || 30;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    const cutoffStr = cutoff.toISOString().slice(0, 10);

    const filtered = series.filter(p => p[0] >= cutoffStr);
    // If filter yields too few points, show all data
    const data = filtered.length >= 2 ? filtered : series;
    return {
        labels: data.map(p => p[0]),
        values: data.map(p => p[1])
    };
}

function createOrUpdateChart(canvasId, assetKey, periodKey) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const series = timeseriesData[assetKey];
    const { labels, values } = filterTimeseries(series, periodKey);

    // Build gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.parentElement.clientHeight || 140);
    gradient.addColorStop(0, 'rgba(0, 200, 83, 0.35)');
    gradient.addColorStop(1, 'rgba(0, 200, 83, 0.0)');

    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                borderColor: '#00c853',
                borderWidth: 2,
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHitRadius: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#21262d',
                    titleColor: '#e6edf3',
                    bodyColor: '#8b949e',
                    borderColor: 'rgba(255,255,255,0.06)',
                    borderWidth: 1,
                    padding: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(ctx) {
                            return formatVietnameseNumber(ctx.parsed.y, 0);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: {
                        color: '#484f58',
                        font: { size: 10, family: 'Inter' },
                        maxTicksLimit: 6,
                        maxRotation: 0,
                        callback: function(val, idx) {
                            const label = this.getLabelForValue(val);
                            // Show short date: "Jan 5" or "Mar"
                            const d = new Date(label);
                            if (isNaN(d)) return label;
                            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                        }
                    }
                },
                y: {
                    display: true,
                    position: 'right',
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: {
                        color: '#484f58',
                        font: { size: 10, family: 'Inter' },
                        maxTicksLimit: 4,
                        callback: function(val) {
                            if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
                            if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
                            if (val >= 1e3) return (val / 1e3).toFixed(1) + 'K';
                            return val;
                        }
                    }
                }
            },
            interaction: { mode: 'nearest', axis: 'x', intersect: false },
            animation: { duration: 400 }
        }
    };

    // Destroy existing chart if any, then create new
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    chartInstances[canvasId] = new Chart(ctx, config);
}

// ---- Period selector wiring ----

function updateChartChangeText(chartKey, period) {
    const historyKey = chartKey === 'btc' ? 'bitcoin' : 'vn30';
    const changeElId = chartKey === 'btc' ? 'btcChange' : 'vn30Change';
    const changeEl = document.getElementById(changeElId);
    if (!changeEl || !lastData || !lastData.history) return;

    const history = lastData.history[historyKey];
    const periodChange = history && history.find(c => c.period === period);
    if (periodChange && periodChange.change_percent !== null) {
        const pct = parseFloat(periodChange.change_percent);
        const sign = pct >= 0 ? '+' : '';
        const arrow = pct >= 0 ? '↗' : '↘';
        changeEl.textContent = `${arrow} ${sign}${formatVietnameseNumber(pct, 2)}%`;
        changeEl.className = 'chart-change ' + (pct >= 0 ? 'positive' : 'negative');
    } else {
        changeEl.textContent = '--';
        changeEl.className = 'chart-change';
    }
}

function initPeriodSelectors() {
    document.querySelectorAll('.period-selector').forEach(selector => {
        const chartKey = selector.dataset.chart; // 'btc' or 'vn30'
        selector.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                selector.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const period = btn.dataset.period;
                const canvasId = chartKey === 'btc' ? 'btcChart' : 'vn30Chart';
                const assetKey = chartKey === 'btc' ? 'bitcoin' : 'vn30';
                createOrUpdateChart(canvasId, assetKey, period);
                updateChartChangeText(chartKey, period);
            });
        });
    });
}

// ---- Header update ----

function updateLastUpdateTime(data) {
    const fromGeneratedAt = parseTimestampToLocalTime(data && data.generated_at);
    if (fromGeneratedAt) {
        document.getElementById('lastUpdateTime').textContent = `Updated ${fromGeneratedAt}`;
        return;
    }

    const candidates = [
        data && data.gold && data.gold.timestamp,
        data && data.usd_vnd && data.usd_vnd.timestamp,
        data && data.bitcoin && data.bitcoin.timestamp,
        data && data.vn30 && data.vn30.timestamp,
    ];
    for (const ts of candidates) {
        const parsed = parseTimestampToLocalTime(ts);
        if (parsed) {
            document.getElementById('lastUpdateTime').textContent = `Updated ${parsed}`;
            return;
        }
    }

    document.getElementById('lastUpdateTime').textContent = 'Updated --';
}

// ---- Main fetch ----

let lastData = null;

async function fetchData() {
    try {
        const response = await fetch(`${DATA_URL}?t=${Date.now()}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        lastData = data;

        const goldHistory = data.history && data.history.gold;
        const usdHistory = data.history && data.history.usd_vnd;
        const btcHistory = data.history && data.history.bitcoin;
        const vn30History = data.history && data.history.vn30;

        // Update metric cards
        if (data.gold) updateGoldCard(data.gold, goldHistory);
        else resetGoldCard();

        if (data.usd_vnd) updateUsdCard(data.usd_vnd, usdHistory);
        else resetUsdCard();

        // Update chart cards
        if (data.bitcoin) updateBtcCard(data.bitcoin, btcHistory);
        else resetBtcCard();

        if (data.vn30) updateVn30Card(data.vn30, vn30History);
        else resetVn30Card();

        // Update history badges on metric cards
        if (goldHistory) updateHistoryBadges('goldHistory', goldHistory);
        else updateHistoryBadges('goldHistory', []);

        if (usdHistory) updateHistoryBadges('usdHistory', usdHistory);
        else updateHistoryBadges('usdHistory', []);

        // Store timeseries and render charts
        if (data.timeseries) {
            timeseriesData = data.timeseries;
            const btcPeriod = document.querySelector('[data-chart="btc"] .period-btn.active');
            const vn30Period = document.querySelector('[data-chart="vn30"] .period-btn.active');
            createOrUpdateChart('btcChart', 'bitcoin', btcPeriod ? btcPeriod.dataset.period : '1M');
            createOrUpdateChart('vn30Chart', 'vn30', vn30Period ? vn30Period.dataset.period : '1M');
        }

        updateLastUpdateTime(data);

    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('lastUpdateTime').textContent = 'Error loading data';
    }
}

// ---- Init ----

initPeriodSelectors();

document.getElementById('refreshBtn').addEventListener('click', () => fetchData());

fetchData();

setInterval(fetchData, REFRESH_INTERVAL);

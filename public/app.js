// Vietnam Gold & Market Dashboard - Frontend Logic

const DATA_URL = 'data.json';
const REFRESH_INTERVAL = 10 * 60 * 1000; // 10 minutes in milliseconds
const FRESHNESS_THRESHOLDS = {
    fresh: 5 * 60 * 1000,  // < 5 minutes
    stale: 10 * 60 * 1000  // < 10 minutes
};

// Vietnamese number formatting
function formatVietnameseNumber(value, decimalPlaces = 0) {
    if (!value && value !== 0) return '--';
    
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '--';
    
    // Split into integer and decimal parts
    const parts = num.toFixed(decimalPlaces).split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    
    // Format integer part with dots as thousand separators
    const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    
    // Combine with comma as decimal separator if needed
    if (decimalPlaces > 0 && decimalPart) {
        return `${formattedInteger},${decimalPart}`;
    }
    
    return formattedInteger;
}

// Calculate data freshness
function getFreshnessClass(timestamp) {
    const now = new Date();
    const dataTime = new Date(timestamp);
    const age = now - dataTime;
    
    if (age < FRESHNESS_THRESHOLDS.fresh) return 'fresh';
    if (age < FRESHNESS_THRESHOLDS.stale) return 'stale';
    return 'old';
}

// Format timestamp for display
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // If less than 1 minute, show "Just now"
    if (diff < 60000) return 'Just now';
    
    // If less than 1 hour, show minutes ago
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} min ago`;
    }
    
    // If today, show time
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    // Otherwise show date and time
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Update Gold card
function updateGoldCard(data) {
    if (!data) return;
    
    const card = document.getElementById('goldCard');
    const buyElement = document.getElementById('goldBuy');
    const sellElement = document.getElementById('goldSell');
    const unitElement = document.getElementById('goldUnit');
    const sourceElement = document.getElementById('goldSource');
    const timestampElement = document.getElementById('goldTimestamp');
    
    buyElement.textContent = formatVietnameseNumber(data.buy_price, 0);
    sellElement.textContent = formatVietnameseNumber(data.sell_price, 0);
    unitElement.textContent = data.unit || 'VND/tael';
    sourceElement.textContent = data.source || '--';
    timestampElement.textContent = formatTimestamp(data.timestamp);
    
    // Update freshness indicator
    card.className = 'card ' + getFreshnessClass(data.timestamp);
}

// Update USD/VND card
function updateUsdCard(data) {
    if (!data) return;
    
    const card = document.getElementById('usdCard');
    const rateElement = document.getElementById('usdRate');
    const sourceElement = document.getElementById('usdSource');
    const timestampElement = document.getElementById('usdTimestamp');
    
    rateElement.textContent = formatVietnameseNumber(data.sell_rate, 0);
    sourceElement.textContent = data.source || '--';
    timestampElement.textContent = formatTimestamp(data.timestamp);
    
    card.className = 'card ' + getFreshnessClass(data.timestamp);
}

// Update Bitcoin card
function updateBtcCard(data) {
    if (!data) return;
    
    const card = document.getElementById('btcCard');
    const rateElement = document.getElementById('btcRate');
    const sourceElement = document.getElementById('btcSource');
    const timestampElement = document.getElementById('btcTimestamp');
    
    rateElement.textContent = formatVietnameseNumber(data.btc_to_vnd, 0);
    sourceElement.textContent = data.source || '--';
    timestampElement.textContent = formatTimestamp(data.timestamp);
    
    card.className = 'card ' + getFreshnessClass(data.timestamp);
}

// Update VN30 card
function updateVn30Card(data) {
    if (!data) return;
    
    const card = document.getElementById('vn30Card');
    const valueElement = document.getElementById('vn30Value');
    const changeElement = document.getElementById('vn30Change');
    const sourceElement = document.getElementById('vn30Source');
    const timestampElement = document.getElementById('vn30Timestamp');
    
    valueElement.textContent = formatVietnameseNumber(data.index_value, 2);
    
    if (data.change_percent !== null && data.change_percent !== undefined) {
        const changePercent = parseFloat(data.change_percent);
        const sign = changePercent >= 0 ? '+' : '';
        changeElement.textContent = `${sign}${formatVietnameseNumber(changePercent, 2)}%`;
        changeElement.className = 'change-indicator ' + (changePercent >= 0 ? 'positive' : 'negative');
    } else {
        changeElement.textContent = '--';
        changeElement.className = 'change-indicator';
    }
    
    sourceElement.textContent = data.source || '--';
    timestampElement.textContent = formatTimestamp(data.timestamp);
    
    card.className = 'card ' + getFreshnessClass(data.timestamp);
}

// Update historical change badges for a card
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

    // Show hint when no historical data is available yet
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

// Update last update time in header
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('lastUpdateTime').textContent = `Last updated: ${timeString}`;
}

// Fetch and display data
async function fetchData() {
    try {
        // Add cache-busting parameter to ensure fresh data
        const response = await fetch(`${DATA_URL}?t=${Date.now()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update all cards
        if (data.gold) updateGoldCard(data.gold);
        if (data.usd_vnd) updateUsdCard(data.usd_vnd);
        if (data.bitcoin) updateBtcCard(data.bitcoin);
        if (data.vn30) updateVn30Card(data.vn30);
        
        // Update historical change badges
        if (data.history) {
            if (data.history.gold) updateHistoryBadges('goldHistory', data.history.gold);
            if (data.history.usd_vnd) updateHistoryBadges('usdHistory', data.history.usd_vnd);
            if (data.history.bitcoin) updateHistoryBadges('btcHistory', data.history.bitcoin);
            if (data.history.vn30) updateHistoryBadges('vn30History', data.history.vn30);
        }
        
        updateLastUpdateTime();
        
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('lastUpdateTime').textContent = 'Error loading data';
    }
}

// Manual refresh button
document.getElementById('refreshBtn').addEventListener('click', () => {
    fetchData();
});

// Initial load
fetchData();

// Auto-refresh every 10 minutes
setInterval(fetchData, REFRESH_INTERVAL);

// Update timestamps every minute
setInterval(() => {
    // Re-fetch to update relative timestamps
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const timestampElement = card.querySelector('.timestamp');
        if (timestampElement && timestampElement.dataset.timestamp) {
            timestampElement.textContent = formatTimestamp(timestampElement.dataset.timestamp);
        }
    });
}, 60000);

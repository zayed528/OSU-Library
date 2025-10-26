// API Configuration
const API_BASE_URL = 'http://localhost:8001/api';

// Global state
let allTables = [];

// Initialize dashboard
async function initDashboard() {
    try {
        await loadAllFloors();
        updateLastUpdated();
        
        // Refresh every 30 seconds
        setInterval(() => {
            loadAllFloors();
            updateLastUpdated();
        }, 30000);
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to load data. Please check if the backend server is running.');
    }
}

// Load all floors data
async function loadAllFloors() {
    try {
        // Get all library tables
        const response = await fetch(`${API_BASE_URL}/library/tables`);
        if (!response.ok) throw new Error('Failed to fetch tables');
        
        const data = await response.json();
        allTables = data.tables || [];
        
        // Group tables by floor
        const floorData = groupByFloor(allTables);
        
        // Update overall stats
        updateOverallStats(allTables);
        
        // Render floors
        renderFloors(floorData);
        
    } catch (error) {
        console.error('Error loading floors:', error);
        showError('Could not connect to server. Make sure the backend is running on port 8001.');
    }
}

// Group tables by floor
function groupByFloor(tables) {
    const floors = {};
    
    tables.forEach(table => {
        const floorId = table.floorId || 'Unknown';
        if (!floors[floorId]) {
            floors[floorId] = [];
        }
        floors[floorId].push(table);
    });
    
    return floors;
}

// Calculate stats for tables
function calculateStats(tables) {
    let totalSeats = 0;
    let occupiedSeats = 0;
    let availableSeats = 0;
    
    tables.forEach(table => {
        if (table.seats && Array.isArray(table.seats)) {
            table.seats.forEach(seat => {
                totalSeats++;
                if (seat.status === 'OCCUPIED') {
                    occupiedSeats++;
                } else if (seat.status === 'FREE') {
                    availableSeats++;
                }
            });
        }
    });
    
    const occupancyRate = totalSeats > 0 ? (occupiedSeats / totalSeats * 100).toFixed(1) : 0;
    
    return { totalSeats, occupiedSeats, availableSeats, occupancyRate };
}

// Update overall stats
function updateOverallStats(tables) {
    const stats = calculateStats(tables);
    
    document.getElementById('totalSeats').textContent = stats.totalSeats;
    document.getElementById('availableSeats').textContent = stats.availableSeats;
    document.getElementById('occupiedSeats').textContent = stats.occupiedSeats;
    document.getElementById('occupancyRate').textContent = `${stats.occupancyRate}%`;
}

// Render floors
function renderFloors(floorData) {
    const container = document.getElementById('floorsContainer');
    container.innerHTML = '';
    
    // Sort floor IDs numerically (F1, F2, F3, etc.)
    const sortedFloorIds = Object.keys(floorData).sort((a, b) => {
        // Extract numbers from floor IDs (e.g., "F1" -> 1, "F2" -> 2)
        const numA = parseInt(a.replace(/\D/g, '')) || 0;
        const numB = parseInt(b.replace(/\D/g, '')) || 0;
        return numA - numB;
    });
    
    sortedFloorIds.forEach(floorId => {
        const tables = floorData[floorId];
        const stats = calculateStats(tables);
        
        const floorCard = createFloorCard(floorId, tables, stats);
        container.appendChild(floorCard);
    });
}

// Create floor card element
function createFloorCard(floorId, tables, stats) {
    const card = document.createElement('div');
    card.className = 'floor-card';
    card.id = `floor-${floorId}`;
    
    // Format floor name: "F1" -> "Floor 1", "F2" -> "Floor 2"
    const floorNumber = floorId.replace(/\D/g, ''); // Extract numbers only
    const floorDisplayName = `Floor ${floorNumber}`;
    
    card.innerHTML = `
        <div class="floor-header" onclick="toggleFloor('${floorId}')">
            <div class="floor-info">
                <h3 class="floor-name">${floorDisplayName}</h3>
                <div class="floor-stats">
                    <div class="floor-stat">
                        <span class="floor-stat-value" style="color: var(--green)">${stats.availableSeats}</span>
                        <span class="floor-stat-label">Available</span>
                    </div>
                    <div class="floor-stat">
                        <span class="floor-stat-value" style="color: var(--scarlet-red)">${stats.occupiedSeats}</span>
                        <span class="floor-stat-label">Occupied</span>
                    </div>
                    <div class="floor-stat">
                        <span class="floor-stat-value">${stats.totalSeats}</span>
                        <span class="floor-stat-label">Total</span>
                    </div>
                </div>
                <div class="occupancy-bar">
                    <div class="occupancy-fill" style="width: ${stats.occupancyRate}%"></div>
                </div>
                <div class="occupancy-percentage">${stats.occupancyRate}%</div>
            </div>
            <svg class="expand-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
        </div>
        <div class="tables-section">
            <div class="tables-grid">
                ${tables.map(table => createTableCard(table)).join('')}
            </div>
        </div>
    `;
    
    return card;
}

// Create table card HTML
function createTableCard(table) {
    const tags = table.tags || [];
    const seats = table.seats || [];
    
    return `
        <div class="table-card">
            <div class="table-header">
                <span class="table-id">${table.tableId}</span>
                <span class="table-type">${table.type || 'study'}</span>
            </div>
            ${tags.length > 0 ? `
                <div class="table-tags">
                    ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            ` : ''}
            <div class="seats-grid">
                ${seats.map((seat, index) => `
                    <div class="seat ${seat.status.toLowerCase().replace('_', '-')}">
                        ${seat.seatId || `S${index}`}: ${seat.status}
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Toggle floor expansion
function toggleFloor(floorId) {
    const card = document.getElementById(`floor-${floorId}`);
    card.classList.toggle('expanded');
}

// Update last updated timestamp
function updateLastUpdated() {
    const now = new Date();
    const formatted = now.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('lastUpdated').textContent = formatted;
}

// Show error message
function showError(message) {
    const container = document.getElementById('floorsContainer');
    container.innerHTML = `
        <div style="background: #FFEBEE; padding: 30px; border-radius: 12px; text-align: center;">
            <h3 style="color: var(--scarlet-red); margin-bottom: 10px;">⚠️ Error</h3>
            <p style="color: var(--light-gray);">${message}</p>
            <p style="color: var(--light-gray); margin-top: 10px; font-size: 14px;">
                Make sure the backend server is running:<br>
                <code style="background: white; padding: 5px 10px; border-radius: 4px; display: inline-block; margin-top: 5px;">
                    cd forum/backend && python3 main.py
                </code>
            </p>
        </div>
    `;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);

// =============================================
// CS2 Dashboard - Data & Interactions
// =============================================

// Initialize Supabase client
const supabase = window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

// State management
const state = {
    liveMatches: [],
    upcomingMatches: [],
    valueBets: [],
    hotPlayers: [],
    predictions: [],
    isLoading: true
};

// =============================================
// Data Fetching Functions
// =============================================

async function fetchLiveMatches() {
    try {
        const { data, error } = await supabase
            .from('cs2_matches')
            .select(`
                *,
                team1:cs2_teams!team1_id(*),
                team2:cs2_teams!team2_id(*)
            `)
            .eq('status', 'live')
            .order('scheduled_at', { ascending: true });

        if (error) throw error;
        state.liveMatches = data || [];
        return data;
    } catch (error) {
        console.error('Error fetching live matches:', error);
        return [];
    }
}

async function fetchUpcomingMatches() {
    try {
        const { data, error } = await supabase
            .from('cs2_matches')
            .select(`
                *,
                team1:cs2_teams!team1_id(*),
                team2:cs2_teams!team2_id(*),
                predictions:cs2_predictions(*)
            `)
            .eq('status', 'upcoming')
            .order('scheduled_at', { ascending: true })
            .limit(20);

        if (error) throw error;
        state.upcomingMatches = data || [];
        return data;
    } catch (error) {
        console.error('Error fetching upcoming matches:', error);
        return [];
    }
}

async function fetchValueBets() {
    try {
        // Get predictions with edge > 5%
        const { data, error } = await supabase
            .from('cs2_predictions')
            .select(`
                *,
                player:cs2_players(*),
                match:cs2_matches(
                    *,
                    team1:cs2_teams!team1_id(*),
                    team2:cs2_teams!team2_id(*)
                )
            `)
            .gte('confidence', 0.65)
            .order('confidence', { ascending: false })
            .limit(10);

        if (error) throw error;
        state.valueBets = data || [];
        return data;
    } catch (error) {
        console.error('Error fetching value bets:', error);
        return [];
    }
}

async function fetchHotPlayers() {
    try {
        const { data, error } = await supabase
            .from('cs2_player_aggregates')
            .select(`
                *,
                player:cs2_players(
                    *,
                    team:cs2_teams(*)
                )
            `)
            .eq('time_period', 'last_5')
            .order('avg_rating', { ascending: false })
            .limit(6);

        if (error) throw error;
        state.hotPlayers = data || [];
        return data;
    } catch (error) {
        console.error('Error fetching hot players:', error);
        return [];
    }
}

async function fetchPlayerProps(matchId) {
    try {
        const { data, error } = await supabase
            .from('cs2_player_props')
            .select(`
                *,
                player:cs2_players(*),
                prediction:cs2_predictions(*)
            `)
            .eq('match_id', matchId)
            .order('fetched_at', { ascending: false });

        if (error) throw error;
        return data || [];
    } catch (error) {
        console.error('Error fetching player props:', error);
        return [];
    }
}

// =============================================
// Rendering Functions
// =============================================

function renderLiveMatches() {
    const container = document.getElementById('live-matches');
    if (!container) return;

    if (state.liveMatches.length === 0) {
        // Keep demo content for now
        return;
    }

    const html = state.liveMatches.map(match => createMatchCard(match, true)).join('');
    container.innerHTML = html || container.innerHTML;
}

function createMatchCard(match, isLive = false) {
    const team1 = match.team1 || { name: 'TBD', logo_url: null };
    const team2 = match.team2 || { name: 'TBD', logo_url: null };
    const prediction = match.predictions?.[0];
    const confidence = prediction ? Math.round(prediction.confidence * 100) : 50;

    return `
        <div class="match-card ${isLive ? 'live' : ''}" data-match-id="${match.id}">
            <div class="match-header">
                <div class="match-meta">
                    ${isLive ? '<span class="live-badge">● LIVE</span>' : ''}
                    <span class="tournament">${match.tournament_name || 'CS2 Match'}</span>
                </div>
                <div class="match-score">${match.best_of ? `BO${match.best_of}` : ''}</div>
            </div>
            
            <div class="teams-display">
                <div class="team team-1">
                    <div class="team-logo">${getTeamEmoji(team1.name)}</div>
                    <div class="team-info">
                        <span class="team-name">${team1.name}</span>
                        <span class="team-odds">${getOdds(match, 'team1')}</span>
                    </div>
                    <div class="team-score">${match.team1_score || 0}</div>
                </div>
                <div class="vs-divider">
                    <span class="map-score">vs</span>
                </div>
                <div class="team team-2">
                    <div class="team-score">${match.team2_score || 0}</div>
                    <div class="team-info">
                        <span class="team-name">${team2.name}</span>
                        <span class="team-odds">${getOdds(match, 'team2')}</span>
                    </div>
                    <div class="team-logo">${getTeamEmoji(team2.name)}</div>
                </div>
            </div>
            
            <div class="prediction-bar">
                <div class="prediction-label">
                    <span>Model Prediction</span>
                    <span class="confidence">${confidence}% confidence</span>
                </div>
                <div class="prediction-meter">
                    <div class="meter-fill" style="width: ${confidence}%"></div>
                </div>
            </div>
            
            <button class="expand-btn" onclick="toggleMatchDetails(this)">
                View Player Props
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </button>
            
            <div class="match-details" id="details-${match.id}">
                <h4>Player Props</h4>
                <div class="props-grid" id="props-${match.id}">
                    <div class="loading">Loading props...</div>
                </div>
            </div>
        </div>
    `;
}

function renderValueBets() {
    const container = document.getElementById('value-bets');
    if (!container || state.valueBets.length === 0) return;

    const html = state.valueBets.slice(0, 3).map((bet, index) => createValueBetCard(bet, index === 0)).join('');
    container.innerHTML = html || container.innerHTML;
}

function createValueBetCard(bet, isHot = false) {
    const player = bet.player || { name: 'Unknown', team: {} };
    const match = bet.match || { team1: {}, team2: {} };
    const edge = ((bet.predicted_value - (1 / 1.90)) * 100).toFixed(1); // Example calculation

    return `
        <div class="value-bet-card ${isHot ? 'hot' : ''}">
            ${isHot ? '<div class="vb-badge">HOT</div>' : ''}
            <div class="vb-header">
                <div class="vb-match">
                    <span class="vb-teams">${match.team1?.name || 'TBD'} vs ${match.team2?.name || 'TBD'}</span>
                    <span class="vb-time">${formatMatchTime(match.scheduled_at)}</span>
                </div>
                <div class="vb-edge">
                    <span class="edge-value">+${edge}%</span>
                    <span class="edge-label">Edge</span>
                </div>
            </div>
            <div class="vb-content">
                <div class="vb-player">
                    <img src="https://img.icons8.com/color/48/user-male-circle--v1.png" alt="Player" class="player-avatar">
                    <div class="player-info">
                        <span class="player-name">${player.name}</span>
                        <span class="player-team">${player.team?.name || 'Team'}</span>
                    </div>
                </div>
                <div class="vb-prop">
                    <span class="prop-name">${bet.prediction_type}</span>
                    <span class="prop-odds">@ 1.90</span>
                </div>
            </div>
            <div class="vb-analysis">
                <div class="analysis-row">
                    <span class="analysis-label">Our Probability</span>
                    <span class="analysis-value">${(bet.predicted_value * 100).toFixed(1)}%</span>
                </div>
                <div class="analysis-row">
                    <span class="analysis-label">Model Confidence</span>
                    <span class="analysis-value">${(bet.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
            <div class="vb-confidence">
                <div class="confidence-meter">
                    <div class="confidence-fill" style="width: ${bet.confidence * 100}%"></div>
                </div>
                <span class="confidence-label">${(bet.confidence * 100).toFixed(0)}% Model Confidence</span>
            </div>
        </div>
    `;
}

function renderHotPlayers() {
    const container = document.getElementById('hot-players');
    if (!container || state.hotPlayers.length === 0) return;

    const html = state.hotPlayers.slice(0, 3).map((agg, index) => createPlayerCard(agg, index + 1)).join('');
    container.innerHTML = html || container.innerHTML;
}

function createPlayerCard(aggregate, rank) {
    const player = aggregate.player || { name: 'Unknown', team: {} };
    const trend = aggregate.avg_rating > 1.2 ? 'fire' : aggregate.avg_rating > 1.0 ? 'up' : 'stable';
    const trendLabel = trend === 'fire' ? '🔥 On Fire' : trend === 'up' ? '↗️ Trending' : '→ Stable';

    return `
        <div class="player-card ${trend === 'fire' ? 'hot' : ''}">
            <div class="player-rank">${rank}</div>
            <div class="player-header">
                <div class="player-avatar-large">${getPlayerEmoji(rank)}</div>
                <div class="player-main-info">
                    <span class="player-name">${player.name}</span>
                    <span class="player-team">${player.team?.name || 'Team'}</span>
                </div>
                <div class="player-form-badge ${trend}">${trendLabel}</div>
            </div>
            <div class="player-stats-grid">
                <div class="player-stat">
                    <span class="stat-value">${aggregate.avg_rating?.toFixed(2) || 'N/A'}</span>
                    <span class="stat-label">Rating</span>
                </div>
                <div class="player-stat">
                    <span class="stat-value">${aggregate.avg_kills?.toFixed(1) || 'N/A'}</span>
                    <span class="stat-label">Avg Kills</span>
                </div>
                <div class="player-stat">
                    <span class="stat-value">${aggregate.avg_adr?.toFixed(1) || 'N/A'}</span>
                    <span class="stat-label">ADR</span>
                </div>
                <div class="player-stat trend-up">
                    <span class="stat-value">+${((aggregate.avg_rating - 1) * 100).toFixed(0)}%</span>
                    <span class="stat-label">vs Avg</span>
                </div>
            </div>
            <div class="player-form-chart">
                ${generateFormBars()}
            </div>
        </div>
    `;
}

// =============================================
// Helper Functions
// =============================================

function getTeamEmoji(teamName) {
    const emojis = {
        'Vitality': '🦂',
        'G2': '🔵',
        'NAVI': '🔴',
        'FaZe': '⚫',
        'Astralis': '⭐',
        'MOUZ': '🐁',
        'Liquid': '💧',
        'Cloud9': '☁️',
        'ENCE': '🇫🇮',
        'Heroic': '🦸'
    };
    return emojis[teamName] || '🎮';
}

function getPlayerEmoji(rank) {
    const emojis = ['🎯', '⚡', '💎', '🔥', '⭐', '🏆'];
    return emojis[rank - 1] || '🎮';
}

function getOdds(match, team) {
    // Would fetch from odds table in real implementation
    return team === 'team1' ? '1.72' : '2.15';
}

function formatMatchTime(timestamp) {
    if (!timestamp) return 'TBD';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = date - now;
    
    if (diff < 0) return 'Started';
    if (diff < 3600000) return `${Math.round(diff / 60000)}m`;
    if (diff < 86400000) return `${Math.round(diff / 3600000)}h`;
    return date.toLocaleDateString();
}

function generateFormBars() {
    const heights = [70, 85, 90, 75, 95].map(h => Math.random() * 30 + 70);
    return heights.map(h => `<div class="form-bar" style="height: ${h}%"></div>`).join('');
}

// =============================================
// Interaction Handlers
// =============================================

function toggleMatchDetails(button) {
    const card = button.closest('.match-card');
    const details = card.querySelector('.match-details');
    const matchId = card.dataset.matchId;
    
    button.classList.toggle('expanded');
    details.classList.toggle('show');
    
    // Load props if opening
    if (details.classList.contains('show')) {
        loadPlayerProps(matchId);
    }
}

async function loadPlayerProps(matchId) {
    const propsContainer = document.getElementById(`props-${matchId}`);
    if (!propsContainer) return;
    
    const props = await fetchPlayerProps(matchId);
    
    if (props.length === 0) {
        // Show demo props if no real data
        return;
    }
    
    propsContainer.innerHTML = props.map(prop => createPropCard(prop)).join('');
}

function createPropCard(prop) {
    const hasValue = prop.prediction && prop.prediction.confidence > 0.6;
    const player = prop.player || { name: 'Unknown' };
    
    return `
        <div class="prop-card ${hasValue ? 'value-bet' : ''}">
            <div class="prop-header">
                <span class="player-name">${player.name}</span>
                ${hasValue ? '<span class="value-badge">Value</span>' : ''}
            </div>
            <div class="prop-type">${prop.prop_type} Over/Under</div>
            <div class="prop-line">
                <span class="line-value">O ${prop.line}</span>
                <span class="line-odds">@ ${prop.over_odds?.toFixed(2) || '1.90'}</span>
            </div>
            <div class="prop-prediction">
                <div class="pred-bar">
                    <div class="pred-fill over" style="width: ${(prop.prediction?.predicted_value || 0.5) * 100}%"></div>
                </div>
                <span class="pred-value">${Math.round((prop.prediction?.predicted_value || 0.5) * 100)}% Over</span>
            </div>
        </div>
    `;
}

function scrollToValueBets() {
    const section = document.getElementById('value-bets-section');
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

function openMatchModal(matchId) {
    // Could implement a modal for detailed match view
    console.log('Opening match:', matchId);
}

// =============================================
// Real-time Updates
// =============================================

function setupRealtimeSubscriptions() {
    // Subscribe to live match updates
    supabase
        .channel('live-matches')
        .on('postgres_changes', {
            event: '*',
            schema: 'public',
            table: 'cs2_matches',
            filter: 'status=eq.live'
        }, (payload) => {
            console.log('Match update:', payload);
            fetchLiveMatches().then(renderLiveMatches);
        })
        .subscribe();

    // Subscribe to new predictions
    supabase
        .channel('predictions')
        .on('postgres_changes', {
            event: 'INSERT',
            schema: 'public',
            table: 'cs2_predictions'
        }, (payload) => {
            console.log('New prediction:', payload);
            fetchValueBets().then(renderValueBets);
        })
        .subscribe();
}

// =============================================
// Initialization
// =============================================

async function initDashboard() {
    console.log('Initializing CS2 Dashboard...');
    
    // Fetch all data in parallel
    await Promise.all([
        fetchLiveMatches(),
        fetchUpcomingMatches(),
        fetchValueBets(),
        fetchHotPlayers()
    ]);
    
    // Render components
    renderLiveMatches();
    renderValueBets();
    renderHotPlayers();
    
    // Setup real-time updates
    setupRealtimeSubscriptions();
    
    // Update value alert badge
    updateValueAlert();
    
    state.isLoading = false;
    console.log('Dashboard initialized');
}

function updateValueAlert() {
    const alert = document.getElementById('value-alert');
    if (!alert) return;
    
    const count = state.valueBets.filter(b => b.confidence > 0.7).length;
    if (count === 0) {
        alert.style.display = 'none';
    } else {
        alert.querySelector('strong').textContent = `${count} High-Value Bets Detected!`;
    }
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', initDashboard);

// Auto-refresh every 30 seconds
setInterval(() => {
    fetchLiveMatches().then(renderLiveMatches);
    fetchValueBets().then(renderValueBets);
}, 30000);

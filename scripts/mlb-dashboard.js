// =============================================
// MLB Dashboard - Data & Interactions
// =============================================

// Initialize Supabase client
const supabase = window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

// State management
const state = {
    liveGames: [],
    upcomingGames: [],
    valueBets: [],
    hotPlayers: [],
    isLoading: true
};

// =============================================
// Data Fetching Functions
// =============================================

async function fetchLiveGames() {
    try {
        const { data, error } = await supabase
            .from('mlb_games')
            .select(`
                *,
                home_team:mlb_teams!home_team_id(*),
                away_team:mlb_teams!away_team_id(*)
            `)
            .eq('status', 'live')
            .order('scheduled_at', { ascending: true });

        if (error) throw error;
        state.liveGames = data || [];
        return state.liveGames;
    } catch (error) {
        console.error('Error fetching live games:', error);
        state.liveGames = [];
        return [];
    }
}

async function fetchUpcomingGames() {
    try {
        const { data, error } = await supabase
            .from('mlb_games')
            .select(`
                *,
                home_team:mlb_teams!home_team_id(*),
                away_team:mlb_teams!away_team_id(*),
                predictions:mlb_predictions(*)
            `)
            .eq('status', 'scheduled')
            .order('scheduled_at', { ascending: true })
            .limit(20);

        if (error) throw error;
        state.upcomingGames = data || [];
        return state.upcomingGames;
    } catch (error) {
        console.error('Error fetching upcoming games:', error);
        state.upcomingGames = [];
        return [];
    }
}

async function fetchValueBets() {
    try {
        // Highest-confidence predictions first (you can later add an "edge" column)
        const { data, error } = await supabase
            .from('mlb_predictions')
            .select(`
                *,
                player:mlb_players(*),
                game:mlb_games(
                    *,
                    home_team:mlb_teams!home_team_id(*),
                    away_team:mlb_teams!away_team_id(*)
                )
            `)
            .gte('confidence', 0.65)
            .order('confidence', { ascending: false })
            .limit(10);

        if (error) throw error;
        state.valueBets = data || [];
        return state.valueBets;
    } catch (error) {
        console.error('Error fetching value bets:', error);
        state.valueBets = [];
        return [];
    }
}

async function fetchHotPlayers() {
    try {
        const { data, error } = await supabase
            .from('mlb_player_aggregates')
            .select(`
                *,
                player:mlb_players(
                    *,
                    team:mlb_teams(*)
                )
            `)
            .eq('time_period', 'last_5')
            .order('batting_avg', { ascending: false })
            .limit(6);

        if (error) throw error;
        state.hotPlayers = data || [];
        return state.hotPlayers;
    } catch (error) {
        console.error('Error fetching hot players:', error);
        state.hotPlayers = [];
        return [];
    }
}

async function fetchPlayerProps(gameId) {
    try {
        const { data, error } = await supabase
            .from('mlb_player_props')
            .select(`
                *,
                player:mlb_players(*),
                prediction:mlb_predictions(*)
            `)
            .eq('game_id', gameId)
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

function renderLiveGames() {
    const container = document.getElementById('live-matches');
    if (!container) return;

    if (state.liveGames.length === 0) {
        container.innerHTML = '';
        return;
    }

    const html = state.liveGames.map(game => createGameCard(game, true)).join('');
    container.innerHTML = html;
}

function renderUpcomingGames() {
    const container = document.getElementById('upcoming-matches');
    if (!container) return;

    if (state.upcomingGames.length === 0) {
        container.innerHTML = '';
        return;
    }

    const html = state.upcomingGames.map(game => createGameCard(game, false)).join('');
    container.innerHTML = html;
}

function createGameCard(game, isLive = false) {
    const home = game.home_team || { name: 'TBD', abbreviation: null };
    const away = game.away_team || { name: 'TBD', abbreviation: null };
    const prediction = (game.predictions || []).find(p => p.prediction_type === 'game_winner') || (game.predictions || [])[0];

    const confidencePct = prediction?.confidence != null ? Math.round(prediction.confidence * 100) : null;
    const predicted = prediction?.predicted_value != null ? Math.round(prediction.predicted_value * 100) : null;

    const label = prediction?.prediction_type ? prettyPredictionType(prediction.prediction_type) : 'Model Prediction';
    const subLabel = (predicted != null && confidencePct != null)
        ? `${predicted}% (conf ${confidencePct}%)`
        : '—';

    const meter = confidencePct != null ? confidencePct : 50;

    return `
        <div class="match-card ${isLive ? 'live' : ''}" data-game-id="${game.id}">
            <div class="match-header">
                <div class="match-meta">
                    ${isLive ? '<span class="live-badge">● LIVE</span>' : ''}
                    <span class="tournament">${game.venue || 'MLB'}</span>
                </div>
                <div class="match-score">${formatGameTime(game.scheduled_at)}</div>
            </div>
            
            <div class="teams-display">
                <div class="team team-1">
                    <div class="team-logo">${getTeamEmoji(home.abbreviation || home.name)}</div>
                    <div class="team-info">
                        <span class="team-name">${away.name}</span>
                        <span class="team-odds">${getOddsPlaceholder()}</span>
                    </div>
                    <div class="team-score">${game.away_score ?? (isLive ? 0 : '')}</div>
                </div>
                <div class="vs-divider">
                    <span class="map-score">vs</span>
                </div>
                <div class="team team-2">
                    <div class="team-score">${game.home_score ?? (isLive ? 0 : '')}</div>
                    <div class="team-info">
                        <span class="team-name">${home.name}</span>
                        <span class="team-odds">${getOddsPlaceholder()}</span>
                    </div>
                    <div class="team-logo">${getTeamEmoji(away.abbreviation || away.name)}</div>
                </div>
            </div>
            
            <div class="prediction-bar">
                <div class="prediction-label">
                    <span>${label}</span>
                    <span class="confidence">${subLabel}</span>
                </div>
                <div class="prediction-meter">
                    <div class="meter-fill" style="width: ${meter}%"></div>
                </div>
            </div>
            
            <button class="expand-btn" onclick="toggleGameDetails(this)">
                View Player Props
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </button>
            
            <div class="match-details" id="details-${game.id}">
                <h4>Player Props</h4>
                <div class="props-grid" id="props-${game.id}">
                    <div class="loading">Loading props...</div>
                </div>
            </div>
        </div>
    `;
}

function renderValueBets() {
    const container = document.getElementById('value-bets');
    if (!container) return;

    if (state.valueBets.length === 0) {
        container.innerHTML = '';
        return;
    }

    const html = state.valueBets.slice(0, 3).map((bet, idx) => createValueBetCard(bet, idx === 0)).join('');
    container.innerHTML = html;
}

function createValueBetCard(bet, isHot = false) {
    const player = bet.player || { full_name: 'Unknown', team: {} };
    const game = bet.game || { home_team: {}, away_team: {} };

    // Placeholder "edge" until we store market implied prob in DB
    const modelProb = bet.predicted_value ?? 0.5;
    const edgePct = ((modelProb - 0.5) * 100).toFixed(1);

    return `
        <div class="value-bet-card ${isHot ? 'hot' : ''}">
            ${isHot ? '<div class="vb-badge">TOP</div>' : ''}
            <div class="vb-header">
                <div class="vb-match">
                    <span class="vb-teams">${game.away_team?.name || 'TBD'} @ ${game.home_team?.name || 'TBD'}</span>
                    <span class="vb-time">${formatGameTime(game.scheduled_at)}</span>
                </div>
                <div class="vb-edge">
                    <span class="edge-value">${edgePct.startsWith('-') ? '' : '+'}${edgePct}%</span>
                    <span class="edge-label">Edge</span>
                </div>
            </div>
            <div class="vb-content">
                <div class="vb-player">
                    <img src="https://img.icons8.com/color/48/user-male-circle--v1.png" alt="Player" class="player-avatar">
                    <div class="player-info">
                        <span class="player-name">${player.full_name || `${player.first_name || ''} ${player.last_name || ''}`.trim() || 'Unknown'}</span>
                        <span class="player-team">${player.team?.name || ''}</span>
                    </div>
                </div>
                <div class="vb-prop">
                    <span class="prop-name">${prettyPredictionType(bet.prediction_type || 'prediction')}</span>
                    <span class="prop-odds">@ —</span>
                </div>
            </div>
            <div class="vb-analysis">
                <div class="analysis-row">
                    <span class="analysis-label">Our Probability</span>
                    <span class="analysis-value">${(modelProb * 100).toFixed(1)}%</span>
                </div>
                <div class="analysis-row">
                    <span class="analysis-label">Model Confidence</span>
                    <span class="analysis-value">${((bet.confidence ?? 0) * 100).toFixed(0)}%</span>
                </div>
            </div>
            <div class="vb-confidence">
                <div class="confidence-meter">
                    <div class="confidence-fill" style="width: ${(bet.confidence ?? 0) * 100}%"></div>
                </div>
                <span class="confidence-label">${((bet.confidence ?? 0) * 100).toFixed(0)}% Model Confidence</span>
            </div>
        </div>
    `;
}

function renderHotPlayers() {
    const container = document.getElementById('hot-players');
    if (!container) return;

    if (state.hotPlayers.length === 0) {
        container.innerHTML = '';
        return;
    }

    const html = state.hotPlayers.slice(0, 3).map((agg, idx) => createPlayerCard(agg, idx + 1)).join('');
    container.innerHTML = html;
}

function createPlayerCard(aggregate, rank) {
    const player = aggregate.player || { full_name: 'Unknown', team: {} };
    const avgHits = aggregate.avg_hits != null ? Number(aggregate.avg_hits).toFixed(2) : '—';
    const battingAvg = aggregate.batting_avg != null ? Number(aggregate.batting_avg).toFixed(3) : '—';
    const slg = aggregate.slugging_pct != null ? Number(aggregate.slugging_pct).toFixed(3) : '—';

    return `
        <div class="player-card">
            <div class="player-rank">${rank}</div>
            <div class="player-header">
                <div class="player-avatar-large">${getPlayerEmoji(rank)}</div>
                <div class="player-main-info">
                    <span class="player-name">${player.full_name || 'Unknown'}</span>
                    <span class="player-team">${player.team?.name || ''}</span>
                </div>
                <div class="player-form-badge up">↗️ Hot</div>
            </div>
            <div class="player-stats-grid">
                <div class="player-stat">
                    <span class="stat-value">${avgHits}</span>
                    <span class="stat-label">Avg Hits</span>
                </div>
                <div class="player-stat">
                    <span class="stat-value">${battingAvg}</span>
                    <span class="stat-label">AVG</span>
                </div>
                <div class="player-stat">
                    <span class="stat-value">${slg}</span>
                    <span class="stat-label">SLG</span>
                </div>
                <div class="player-stat">
                    <span class="stat-value">${aggregate.games_played ?? '—'}</span>
                    <span class="stat-label">Games</span>
                </div>
            </div>
            <div class="player-form-chart">
                ${generateFormBars()}
            </div>
        </div>
    `;
}

// =============================================
// Interaction Handlers
// =============================================

function toggleGameDetails(button) {
    const card = button.closest('.match-card');
    const details = card.querySelector('.match-details');
    const gameId = card.dataset.gameId;

    button.classList.toggle('expanded');
    details.classList.toggle('show');

    if (details.classList.contains('show')) {
        loadPlayerProps(gameId);
    }
}

async function loadPlayerProps(gameId) {
    const propsContainer = document.getElementById(`props-${gameId}`);
    if (!propsContainer) return;

    const props = await fetchPlayerProps(gameId);

    if (!props.length) {
        propsContainer.innerHTML = `<div class="loading">No props available yet</div>`;
        return;
    }

    propsContainer.innerHTML = props.map(prop => createPropCard(prop)).join('');
}

function createPropCard(prop) {
    const player = prop.player || { full_name: 'Unknown' };
    const hasValue = prop.prediction && prop.prediction.confidence > 0.6;

    return `
        <div class="prop-card ${hasValue ? 'value-bet' : ''}">
            <div class="prop-header">
                <span class="player-name">${player.full_name || 'Unknown'}</span>
                ${hasValue ? '<span class="value-badge">Value</span>' : ''}
            </div>
            <div class="prop-type">${prop.prop_type} Over/Under</div>
            <div class="prop-line">
                <span class="line-value">O ${prop.line}</span>
                <span class="line-odds">@ ${prop.over_odds?.toFixed?.(2) || '—'}</span>
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
    if (section) section.scrollIntoView({ behavior: 'smooth' });
}

// =============================================
// Helper Functions
// =============================================

function getTeamEmoji(teamKey) {
    const emojis = {
        NYY: '🗽',
        BOS: '🍀',
        LAD: '💙',
        NYM: '🟠',
        CHC: '🐻',
        STL: '🎺',
        ATL: '🍑',
        HOU: '🚀',
        PHI: '🔔',
        SF: '🌉'
    };
    return emojis[teamKey] || '⚾';
}

function getPlayerEmoji(rank) {
    const emojis = ['⚾', '🔥', '💎', '⭐', '🏆', '🎯'];
    return emojis[rank - 1] || '⚾';
}

function getOddsPlaceholder() {
    // Real odds can be loaded from mlb_odds later
    return '—';
}

function formatGameTime(timestamp) {
    if (!timestamp) return 'TBD';
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return 'TBD';

    const now = new Date();
    const diff = date - now;

    if (diff < -2 * 60 * 60 * 1000) return 'Final';
    if (diff < 0) return 'Live';
    if (diff < 60 * 60 * 1000) return `${Math.round(diff / 60000)}m`;
    if (diff < 24 * 60 * 60 * 1000) return `${Math.round(diff / 3600000)}h`;
    return date.toLocaleDateString();
}

function prettyPredictionType(type) {
    return String(type || '')
        .replaceAll('_', ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

function generateFormBars() {
    const heights = [70, 85, 90, 75, 95].map(() => Math.random() * 30 + 70);
    return heights.map(h => `<div class="form-bar" style="height: ${h}%"></div>`).join('');
}

// =============================================
// Real-time Updates
// =============================================

function setupRealtimeSubscriptions() {
    // Subscribe to live game updates
    supabase
        .channel('mlb-live-games')
        .on('postgres_changes', {
            event: '*',
            schema: 'public',
            table: 'mlb_games',
            filter: 'status=eq.live'
        }, () => {
            fetchLiveGames().then(() => {
                renderLiveGames();
                updateStats();
            });
        })
        .subscribe();

    // Subscribe to new predictions
    supabase
        .channel('mlb-predictions')
        .on('postgres_changes', {
            event: 'INSERT',
            schema: 'public',
            table: 'mlb_predictions'
        }, () => {
            fetchValueBets().then(() => {
                renderValueBets();
                updateStats();
            });
        })
        .subscribe();
}

// =============================================
// Stats
// =============================================

function updateStats() {
    const valueBetsEl = document.getElementById('stat-value-bets');
    const liveGamesEl = document.getElementById('stat-live-games');
    const predictionsEl = document.getElementById('stat-predictions');
    const avgEdgeEl = document.getElementById('stat-avg-edge');

    if (valueBetsEl) valueBetsEl.textContent = String(state.valueBets.length || 0);
    if (liveGamesEl) liveGamesEl.textContent = String(state.liveGames.length || 0);
    if (predictionsEl) predictionsEl.textContent = String(state.valueBets.length || 0);

    // Placeholder until "edge" is stored
    if (avgEdgeEl) avgEdgeEl.textContent = '—';

    updateValueAlert();
}

function updateValueAlert() {
    const alert = document.getElementById('value-alert');
    if (!alert) return;

    const count = state.valueBets.filter(b => (b.confidence ?? 0) > 0.7).length;
    if (count === 0) {
        alert.style.display = 'none';
    } else {
        alert.style.display = 'flex';
        const strong = alert.querySelector('strong');
        if (strong) strong.textContent = `${count} High-Value Bets Detected!`;
    }
}

// =============================================
// Initialization
// =============================================

async function initDashboard() {
    console.log('Initializing MLB Dashboard...');

    await Promise.all([
        fetchLiveGames(),
        fetchUpcomingGames(),
        fetchValueBets(),
        fetchHotPlayers()
    ]);

    renderLiveGames();
    renderUpcomingGames();
    renderValueBets();
    renderHotPlayers();

    setupRealtimeSubscriptions();
    updateStats();

    state.isLoading = false;
    console.log('MLB Dashboard initialized');
}

document.addEventListener('DOMContentLoaded', initDashboard);

// Auto-refresh every 30 seconds
setInterval(() => {
    fetchLiveGames().then(() => {
        renderLiveGames();
        updateStats();
    });
    fetchUpcomingGames().then(renderUpcomingGames);
    fetchValueBets().then(() => {
        renderValueBets();
        updateStats();
    });
}, 30000);


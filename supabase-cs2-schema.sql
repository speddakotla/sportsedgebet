-- =============================================
-- CS2 Data Schema for SportsEdgeBet
-- Run this in Supabase SQL Editor AFTER main schema
-- =============================================

-- =============================================
-- CS2 TEAMS TABLE 
-- =============================================
CREATE TABLE public.cs2_teams (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL, -- ID from PandaScore/Abios
    name TEXT NOT NULL,
    slug TEXT,
    acronym TEXT,
    logo_url TEXT,
    country TEXT,
    ranking INTEGER,
    source TEXT NOT NULL, -- 'pandascore', 'abios'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs2_teams_external ON public.cs2_teams(external_id);
CREATE INDEX idx_cs2_teams_name ON public.cs2_teams(name);

-- =============================================
-- CS2 PLAYERS TABLE
-- =============================================
CREATE TABLE public.cs2_players (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL, -- In-game name
    real_name TEXT,
    team_id UUID REFERENCES public.cs2_teams(id) ON DELETE SET NULL,
    country TEXT,
    age INTEGER,
    role TEXT, -- 'awper', 'rifler', 'igl', 'entry', 'support'
    image_url TEXT,
    source TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs2_players_external ON public.cs2_players(external_id);
CREATE INDEX idx_cs2_players_team ON public.cs2_players(team_id);
CREATE INDEX idx_cs2_players_name ON public.cs2_players(name);

-- =============================================
-- CS2 MATCHES TABLE
-- =============================================
CREATE TABLE public.cs2_matches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    tournament_name TEXT,
    tournament_id TEXT,
    team1_id UUID REFERENCES public.cs2_teams(id),
    team2_id UUID REFERENCES public.cs2_teams(id),
    winner_id UUID REFERENCES public.cs2_teams(id),
    team1_score INTEGER,
    team2_score INTEGER,
    best_of INTEGER, -- 1, 3, 5
    status TEXT NOT NULL, -- 'upcoming', 'live', 'finished', 'canceled'
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    source TEXT NOT NULL,
    raw_data JSONB, -- Store full API response for ML
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs2_matches_external ON public.cs2_matches(external_id);
CREATE INDEX idx_cs2_matches_status ON public.cs2_matches(status);
CREATE INDEX idx_cs2_matches_scheduled ON public.cs2_matches(scheduled_at);
CREATE INDEX idx_cs2_matches_teams ON public.cs2_matches(team1_id, team2_id);

-- =============================================
-- CS2 PLAYER STATS TABLE (per match)
-- =============================================
CREATE TABLE public.cs2_player_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    player_id UUID REFERENCES public.cs2_players(id) ON DELETE CASCADE NOT NULL,
    match_id UUID REFERENCES public.cs2_matches(id) ON DELETE CASCADE NOT NULL,
    map_name TEXT, -- 'de_mirage', 'de_inferno', etc.
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    headshots INTEGER DEFAULT 0,
    headshot_percentage DECIMAL(5,2),
    adr DECIMAL(6,2), -- Average Damage per Round
    kast DECIMAL(5,2), -- Kill/Assist/Survived/Traded percentage
    rating DECIMAL(4,2), -- HLTV rating
    first_kills INTEGER DEFAULT 0,
    first_deaths INTEGER DEFAULT 0,
    clutches_won INTEGER DEFAULT 0,
    clutches_played INTEGER DEFAULT 0,
    flash_assists INTEGER DEFAULT 0,
    source TEXT NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, match_id, map_name)
);

CREATE INDEX idx_cs2_player_stats_player ON public.cs2_player_stats(player_id);
CREATE INDEX idx_cs2_player_stats_match ON public.cs2_player_stats(match_id);
CREATE INDEX idx_cs2_player_stats_created ON public.cs2_player_stats(created_at);

-- =============================================
-- CS2 ODDS TABLE
-- =============================================
CREATE TABLE public.cs2_odds (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    match_id UUID REFERENCES public.cs2_matches(id) ON DELETE CASCADE NOT NULL,
    bookmaker TEXT NOT NULL, -- 'pinnacle', 'bet365', etc.
    market_type TEXT NOT NULL, -- 'match_winner', 'map_winner', 'player_kills', 'handicap'
    selection TEXT NOT NULL, -- Team name, player name, or specific selection
    odds_decimal DECIMAL(8,3) NOT NULL,
    odds_american INTEGER,
    line DECIMAL(6,2), -- For handicaps/totals
    is_live BOOLEAN DEFAULT FALSE,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs2_odds_match ON public.cs2_odds(match_id);
CREATE INDEX idx_cs2_odds_market ON public.cs2_odds(market_type);
CREATE INDEX idx_cs2_odds_fetched ON public.cs2_odds(fetched_at);

-- =============================================
-- CS2 PLAYER PROPS TABLE (betting lines)
-- =============================================
CREATE TABLE public.cs2_player_props (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    match_id UUID REFERENCES public.cs2_matches(id) ON DELETE CASCADE NOT NULL,
    player_id UUID REFERENCES public.cs2_players(id) ON DELETE CASCADE NOT NULL,
    bookmaker TEXT NOT NULL,
    prop_type TEXT NOT NULL, -- 'kills', 'deaths', 'assists', 'headshots', 'adr'
    line DECIMAL(6,2) NOT NULL, -- The over/under line
    over_odds DECIMAL(8,3),
    under_odds DECIMAL(8,3),
    is_live BOOLEAN DEFAULT FALSE,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs2_props_match ON public.cs2_player_props(match_id);
CREATE INDEX idx_cs2_props_player ON public.cs2_player_props(player_id);
CREATE INDEX idx_cs2_props_type ON public.cs2_player_props(prop_type);

-- =============================================
-- ML PREDICTIONS TABLE
-- =============================================
CREATE TABLE public.cs2_predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    match_id UUID REFERENCES public.cs2_matches(id) ON DELETE CASCADE,
    player_id UUID REFERENCES public.cs2_players(id) ON DELETE CASCADE,
    prediction_type TEXT NOT NULL, -- 'match_winner', 'player_kills_over', etc.
    predicted_value DECIMAL(8,3), -- Probability or predicted stat
    confidence DECIMAL(5,4), -- Model confidence 0-1
    model_version TEXT NOT NULL,
    features_used JSONB, -- Store feature snapshot for analysis
    actual_result DECIMAL(8,3), -- Filled after match
    was_correct BOOLEAN, -- Filled after match
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_cs2_predictions_match ON public.cs2_predictions(match_id);
CREATE INDEX idx_cs2_predictions_player ON public.cs2_predictions(player_id);
CREATE INDEX idx_cs2_predictions_type ON public.cs2_predictions(prediction_type);
CREATE INDEX idx_cs2_predictions_model ON public.cs2_predictions(model_version);

-- =============================================
-- DATA FETCH LOG TABLE (for monitoring)
-- =============================================
CREATE TABLE public.data_fetch_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source TEXT NOT NULL, -- 'pandascore', 'abios', 'oddspapi'
    endpoint TEXT NOT NULL,
    status TEXT NOT NULL, -- 'success', 'error', 'rate_limited'
    records_fetched INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fetch_log_source ON public.data_fetch_log(source);
CREATE INDEX idx_fetch_log_created ON public.data_fetch_log(created_at);

-- =============================================
-- AGGREGATED PLAYER STATS (for ML features)
-- =============================================
CREATE TABLE public.cs2_player_aggregates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    player_id UUID REFERENCES public.cs2_players(id) ON DELETE CASCADE NOT NULL,
    time_period TEXT NOT NULL, -- 'last_5', 'last_10', 'last_30_days', 'all_time'
    matches_played INTEGER DEFAULT 0,
    avg_kills DECIMAL(6,2),
    avg_deaths DECIMAL(6,2),
    avg_assists DECIMAL(6,2),
    avg_adr DECIMAL(6,2),
    avg_rating DECIMAL(4,2),
    avg_headshot_pct DECIMAL(5,2),
    avg_first_kills DECIMAL(6,2),
    win_rate DECIMAL(5,4),
    std_kills DECIMAL(6,2), -- Standard deviation for volatility
    std_rating DECIMAL(4,2),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, time_period)
);

CREATE INDEX idx_cs2_aggregates_player ON public.cs2_player_aggregates(player_id);
CREATE INDEX idx_cs2_aggregates_period ON public.cs2_player_aggregates(time_period);

-- =============================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================
CREATE TRIGGER update_cs2_teams_updated_at
    BEFORE UPDATE ON public.cs2_teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_cs2_players_updated_at
    BEFORE UPDATE ON public.cs2_players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_cs2_matches_updated_at
    BEFORE UPDATE ON public.cs2_matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================
-- RLS POLICIES (read-only for authenticated users)
-- =============================================
ALTER TABLE public.cs2_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_player_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_player_props ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cs2_player_aggregates ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read CS2 data
CREATE POLICY "Authenticated users can read teams" ON public.cs2_teams FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read players" ON public.cs2_players FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read matches" ON public.cs2_matches FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read stats" ON public.cs2_player_stats FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read odds" ON public.cs2_odds FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read props" ON public.cs2_player_props FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read predictions" ON public.cs2_predictions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read aggregates" ON public.cs2_player_aggregates FOR SELECT TO authenticated USING (true);

-- =============================================
-- USEFUL VIEWS FOR ML
-- =============================================

-- Player form view (recent performance)
CREATE OR REPLACE VIEW public.cs2_player_form AS
SELECT 
    p.id AS player_id,
    p.name,
    p.team_id,
    t.name AS team_name,
    agg_5.avg_kills AS last5_avg_kills,
    agg_5.avg_rating AS last5_avg_rating,
    agg_10.avg_kills AS last10_avg_kills,
    agg_10.avg_rating AS last10_avg_rating,
    agg_30.avg_kills AS last30d_avg_kills,
    agg_30.avg_rating AS last30d_avg_rating
FROM public.cs2_players p
LEFT JOIN public.cs2_teams t ON p.team_id = t.id
LEFT JOIN public.cs2_player_aggregates agg_5 ON p.id = agg_5.player_id AND agg_5.time_period = 'last_5'
LEFT JOIN public.cs2_player_aggregates agg_10 ON p.id = agg_10.player_id AND agg_10.time_period = 'last_10'
LEFT JOIN public.cs2_player_aggregates agg_30 ON p.id = agg_30.player_id AND agg_30.time_period = 'last_30_days';

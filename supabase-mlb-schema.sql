-- =============================================
-- MLB Data Schema for SportsEdgeBet
-- Run this in Supabase SQL Editor AFTER main schema
-- =============================================

-- =============================================
-- MLB TEAMS TABLE 
-- =============================================
CREATE TABLE public.mlb_teams (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL, -- ID from MLB Stats API
    name TEXT NOT NULL,
    abbreviation TEXT, -- NYY, LAD, etc.
    city TEXT,
    venue_name TEXT,
    venue_city TEXT,
    division TEXT, -- AL East, NL West, etc.
    league TEXT, -- AL, NL
    logo_url TEXT,
    source TEXT NOT NULL DEFAULT 'mlb_stats',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mlb_teams_external ON public.mlb_teams(external_id);
CREATE INDEX idx_mlb_teams_name ON public.mlb_teams(name);
CREATE INDEX idx_mlb_teams_division ON public.mlb_teams(division);

-- =============================================
-- MLB PLAYERS TABLE
-- =============================================
CREATE TABLE public.mlb_players (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    team_id UUID REFERENCES public.mlb_teams(id) ON DELETE SET NULL,
    position TEXT, -- P, C, 1B, 2B, 3B, SS, LF, CF, RF, DH
    bats TEXT, -- L, R, S
    throws TEXT, -- L, R
    jersey_number INTEGER,
    birth_date DATE,
    height_inches INTEGER,
    weight_lbs INTEGER,
    image_url TEXT,
    source TEXT NOT NULL DEFAULT 'mlb_stats',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mlb_players_external ON public.mlb_players(external_id);
CREATE INDEX idx_mlb_players_team ON public.mlb_players(team_id);
CREATE INDEX idx_mlb_players_name ON public.mlb_players(full_name);

-- =============================================
-- MLB GAMES TABLE
-- =============================================
CREATE TABLE public.mlb_games (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL, -- gamePk from MLB Stats API
    game_date DATE NOT NULL,
    game_type TEXT, -- R (regular), P (playoff), etc.
    home_team_id UUID REFERENCES public.mlb_teams(id),
    away_team_id UUID REFERENCES public.mlb_teams(id),
    winner_id UUID REFERENCES public.mlb_teams(id),
    home_score INTEGER,
    away_score INTEGER,
    status TEXT NOT NULL, -- 'scheduled', 'live', 'final', 'postponed', 'canceled'
    detailed_state TEXT, -- 'Pre-Game', 'In Progress', 'Final', etc.
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    venue TEXT,
    attendance INTEGER,
    source TEXT NOT NULL DEFAULT 'mlb_stats',
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mlb_games_external ON public.mlb_games(external_id);
CREATE INDEX idx_mlb_games_status ON public.mlb_games(status);
CREATE INDEX idx_mlb_games_date ON public.mlb_games(game_date);
CREATE INDEX idx_mlb_games_scheduled ON public.mlb_games(scheduled_at);
CREATE INDEX idx_mlb_games_teams ON public.mlb_games(home_team_id, away_team_id);

-- =============================================
-- MLB PLAYER STATS TABLE (per game)
-- =============================================
CREATE TABLE public.mlb_player_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    player_id UUID REFERENCES public.mlb_players(id) ON DELETE CASCADE NOT NULL,
    game_id UUID REFERENCES public.mlb_games(id) ON DELETE CASCADE NOT NULL,
    team_id UUID REFERENCES public.mlb_teams(id),
    -- Batting stats
    at_bats INTEGER DEFAULT 0,
    hits INTEGER DEFAULT 0,
    runs INTEGER DEFAULT 0,
    rbis INTEGER DEFAULT 0,
    home_runs INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    stolen_bases INTEGER DEFAULT 0,
    batting_average DECIMAL(5,3),
    on_base_pct DECIMAL(5,3),
    slugging_pct DECIMAL(5,3),
    -- Pitching stats
    innings_pitched DECIMAL(4,1),
    earned_runs INTEGER DEFAULT 0,
    hits_allowed INTEGER DEFAULT 0,
    walks_allowed INTEGER DEFAULT 0,
    strikeouts_thrown INTEGER DEFAULT 0,
    home_runs_allowed INTEGER DEFAULT 0,
    era DECIMAL(5,2),
    whip DECIMAL(4,2),
    source TEXT NOT NULL DEFAULT 'mlb_stats',
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, game_id)
);

CREATE INDEX idx_mlb_player_stats_player ON public.mlb_player_stats(player_id);
CREATE INDEX idx_mlb_player_stats_game ON public.mlb_player_stats(game_id);
CREATE INDEX idx_mlb_player_stats_created ON public.mlb_player_stats(created_at);

-- =============================================
-- MLB ODDS TABLE
-- =============================================
CREATE TABLE public.mlb_odds (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    game_id UUID REFERENCES public.mlb_games(id) ON DELETE CASCADE NOT NULL,
    bookmaker TEXT NOT NULL, -- 'draftkings', 'fanduel', 'betmgm', etc.
    market_type TEXT NOT NULL, -- 'moneyline', 'spread', 'total', 'player_prop'
    selection TEXT NOT NULL, -- Team name, player name, or specific selection
    odds_decimal DECIMAL(8,3) NOT NULL,
    odds_american INTEGER,
    line DECIMAL(6,2), -- For spreads/totals
    is_live BOOLEAN DEFAULT FALSE,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mlb_odds_game ON public.mlb_odds(game_id);
CREATE INDEX idx_mlb_odds_market ON public.mlb_odds(market_type);
CREATE INDEX idx_mlb_odds_fetched ON public.mlb_odds(fetched_at);

-- =============================================
-- MLB PLAYER PROPS TABLE (betting lines)
-- =============================================
CREATE TABLE public.mlb_player_props (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    game_id UUID REFERENCES public.mlb_games(id) ON DELETE CASCADE NOT NULL,
    player_id UUID REFERENCES public.mlb_players(id) ON DELETE CASCADE NOT NULL,
    bookmaker TEXT NOT NULL,
    prop_type TEXT NOT NULL, -- 'hits', 'home_runs', 'runs', 'rbis', 'strikeouts', 'pitching_strikeouts', etc.
    line DECIMAL(6,2) NOT NULL, -- The over/under line
    over_odds DECIMAL(8,3),
    under_odds DECIMAL(8,3),
    is_live BOOLEAN DEFAULT FALSE,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mlb_props_game ON public.mlb_player_props(game_id);
CREATE INDEX idx_mlb_props_player ON public.mlb_player_props(player_id);
CREATE INDEX idx_mlb_props_type ON public.mlb_player_props(prop_type);

-- =============================================
-- ML PREDICTIONS TABLE
-- =============================================
CREATE TABLE public.mlb_predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    game_id UUID REFERENCES public.mlb_games(id) ON DELETE CASCADE,
    player_id UUID REFERENCES public.mlb_players(id) ON DELETE CASCADE,
    prediction_type TEXT NOT NULL, -- 'game_winner', 'player_hits_over', 'total_runs_over', etc.
    predicted_value DECIMAL(8,3), -- Probability or predicted stat
    confidence DECIMAL(5,4), -- Model confidence 0-1
    model_version TEXT NOT NULL,
    features_used JSONB,
    actual_result DECIMAL(8,3),
    was_correct BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_mlb_predictions_game ON public.mlb_predictions(game_id);
CREATE INDEX idx_mlb_predictions_player ON public.mlb_predictions(player_id);
CREATE INDEX idx_mlb_predictions_type ON public.mlb_predictions(prediction_type);
CREATE INDEX idx_mlb_predictions_model ON public.mlb_predictions(model_version);

-- =============================================
-- AGGREGATED PLAYER STATS (for ML features)
-- =============================================
CREATE TABLE public.mlb_player_aggregates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    player_id UUID REFERENCES public.mlb_players(id) ON DELETE CASCADE NOT NULL,
    time_period TEXT NOT NULL, -- 'last_5', 'last_10', 'last_30_days', 'season', 'career'
    games_played INTEGER DEFAULT 0,
    -- Batting aggregates
    avg_at_bats DECIMAL(5,2),
    avg_hits DECIMAL(5,2),
    avg_runs DECIMAL(5,2),
    avg_rbis DECIMAL(5,2),
    avg_home_runs DECIMAL(5,2),
    batting_avg DECIMAL(5,3),
    on_base_pct DECIMAL(5,3),
    slugging_pct DECIMAL(5,3),
    -- Pitching aggregates
    avg_innings_pitched DECIMAL(4,1),
    avg_earned_runs DECIMAL(5,2),
    avg_strikeouts DECIMAL(5,2),
    era DECIMAL(5,2),
    whip DECIMAL(4,2),
    -- Volatility metrics
    std_hits DECIMAL(5,2),
    std_home_runs DECIMAL(4,2),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, time_period)
);

CREATE INDEX idx_mlb_aggregates_player ON public.mlb_player_aggregates(player_id);
CREATE INDEX idx_mlb_aggregates_period ON public.mlb_player_aggregates(time_period);

-- =============================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================
CREATE TRIGGER update_mlb_teams_updated_at
    BEFORE UPDATE ON public.mlb_teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_mlb_players_updated_at
    BEFORE UPDATE ON public.mlb_players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_mlb_games_updated_at
    BEFORE UPDATE ON public.mlb_games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================
-- RLS POLICIES (read-only for authenticated users)
-- =============================================
ALTER TABLE public.mlb_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_games ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_player_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_player_props ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mlb_player_aggregates ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read MLB data
CREATE POLICY "Authenticated users can read teams" ON public.mlb_teams FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read players" ON public.mlb_players FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read games" ON public.mlb_games FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read stats" ON public.mlb_player_stats FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read odds" ON public.mlb_odds FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read props" ON public.mlb_player_props FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read predictions" ON public.mlb_predictions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can read aggregates" ON public.mlb_player_aggregates FOR SELECT TO authenticated USING (true);

-- =============================================
-- USEFUL VIEWS FOR ML
-- =============================================

-- Player form view (recent performance)
CREATE OR REPLACE VIEW public.mlb_player_form AS
SELECT 
    p.id AS player_id,
    p.full_name,
    p.team_id,
    t.name AS team_name,
    p.position,
    agg_5.avg_hits AS last5_avg_hits,
    agg_5.batting_avg AS last5_batting_avg,
    agg_10.avg_hits AS last10_avg_hits,
    agg_10.batting_avg AS last10_batting_avg,
    agg_season.avg_hits AS season_avg_hits,
    agg_season.batting_avg AS season_batting_avg
FROM public.mlb_players p
LEFT JOIN public.mlb_teams t ON p.team_id = t.id
LEFT JOIN public.mlb_player_aggregates agg_5 ON p.id = agg_5.player_id AND agg_5.time_period = 'last_5'
LEFT JOIN public.mlb_player_aggregates agg_10 ON p.id = agg_10.player_id AND agg_10.time_period = 'last_10'
LEFT JOIN public.mlb_player_aggregates agg_season ON p.id = agg_season.player_id AND agg_season.time_period = 'season';

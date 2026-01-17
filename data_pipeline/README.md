# CS2 Data Pipeline

Automated data collection and ML prediction system for CS2 esports betting.

## Architecture

```
data_pipeline/
├── fetchers/           # API fetchers for each data source
│   ├── pandascore.py   # PandaScore API (player stats, matches)
│   ├── abios.py        # Abios Gaming API (player props, K/D)
│   └── oddspapi.py     # OddsPapi.io (sharp odds lines)
├── ml/                 # Machine learning pipeline
│   ├── features.py     # Feature engineering
│   ├── train.py        # Model training
│   └── predict.py      # Generate predictions
├── config.py           # Configuration
├── database.py         # Supabase operations
├── main.py             # Pipeline orchestrator
└── requirements.txt    # Dependencies
```

## Setup

### 1. Install Dependencies

```bash
cd data_pipeline
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env_example.txt` to `.env` and fill in your API keys:

```bash
cp env_example.txt .env
```

Required secrets:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Service role key (NOT anon key)
- `PANDASCORE_API_KEY` - Get from https://pandascore.co/
- `ABIOS_CLIENT_ID` & `ABIOS_CLIENT_SECRET` - Get from https://abiosgaming.com/
- `ODDSPAPI_API_KEY` - Get from https://oddspapi.io/

### 3. Set Up Database

Run the schema in Supabase SQL Editor:

```sql
-- First run the main schema
\i supabase-schema.sql

-- Then run the CS2 schema
\i supabase-cs2-schema.sql
```

### 4. Configure GitHub Secrets

Add these secrets to your GitHub repository for automated pipelines:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `PANDASCORE_API_KEY`
- `ABIOS_CLIENT_ID`
- `ABIOS_CLIENT_SECRET`
- `ODDSPAPI_API_KEY`

## Usage

### Manual Data Sync

```bash
# Regular sync (upcoming matches, live data)
python main.py

# Full historical sync
python main.py --full-sync

# Specific source only
python main.py --source pandascore
python main.py --source abios
python main.py --source odds
```

### Automated Pipeline (GitHub Actions)

The pipeline runs automatically:
- **Every 30 minutes** during peak hours (10am-2am UTC)
- **Daily full sync** at 6am UTC
- **Weekly model retraining** on Sundays at 5am UTC

Manual trigger: Go to Actions → CS2 Data Pipeline → Run workflow

### ML Predictions

```bash
# Train models (requires historical data)
cd ml
python train.py --save-model

# Generate predictions
python predict.py
```

## API Rate Limits & Costs

| API | Free Tier | Paid Tier |
|-----|-----------|-----------|
| PandaScore | Limited | ~$50/mo |
| Abios | On request | Custom |
| OddsPapi.io | Limited | ~$30/mo |

The pipeline respects rate limits automatically. Adjust `API_RATE_LIMIT_DELAY` in config if needed.

## Data Flow

1. **Fetch** → APIs return raw JSON
2. **Transform** → Normalize to standard schema
3. **Store** → Upsert to Supabase PostgreSQL
4. **Aggregate** → Calculate player rolling stats
5. **Features** → Generate ML features
6. **Predict** → Run models on upcoming matches
7. **Alert** → Surface value bets to users

## Model Types

### Player Kills Over/Under
- **Input**: Player form, line value, opponent strength
- **Output**: Probability of going over the line
- **Model**: XGBoost classifier

### Match Winner
- **Input**: Team stats, head-to-head, map pool
- **Output**: Win probability for each team
- **Model**: LightGBM classifier

## Monitoring

Check the `data_fetch_log` table in Supabase to monitor:
- Fetch success/failure rates
- Records processed
- API response times
- Errors

```sql
SELECT * FROM data_fetch_log 
ORDER BY created_at DESC 
LIMIT 20;
```

## Development

### Adding a New API Source

1. Create new fetcher in `fetchers/`
2. Inherit from `BaseFetcher`
3. Implement `fetch_*` methods
4. Add to `fetchers/__init__.py`
5. Add to `main.py` orchestrator

### Adding New ML Models

1. Create model class in `ml/`
2. Define feature columns
3. Implement `train()` and `predict()`
4. Add to training pipeline
5. Update GitHub Actions workflow

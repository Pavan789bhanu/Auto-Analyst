# AutoAnalyst

AI-powered automated data analysis platform. Upload CSV datasets, ask questions in plain English, and receive AI-generated Python analysis pipelines with preprocessing, statistical analysis, and Plotly visualizations.

## Architecture

```
frontend/          Next.js dashboard (auth, upload, analyze, history)
backend/           Flask REST API (JWT auth, SQLite, local/S3 storage)
data_analyst_system.py   DSPy multi-agent analysis engine
```

### AI Agent Pipeline

1. **Planner Agent** — Creates an execution plan from your query
2. **Preprocessing Agent** — EDA, cleaning, transformations (pandas/numpy)
3. **Statistical Analytics Agent** — Regression, hypothesis tests (statsmodels)
4. **Data Viz Agent** — Plotly visualizations
5. **Code Combiner Agent** — Merges all code into one script

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key (for running analyses)

### 1. Backend

```bash
cd backend
export SECRET_KEY="your-jwt-secret"
export OPENAI_API_KEY="your-openai-api-key"
pip install -r requirements.txt
python app.py
```

API runs at `http://localhost:5000`

### 2. Frontend

```bash
cd frontend
cp .env.local.example .env.local   # or create .env.local
npm install
npm run dev
```

Dashboard runs at `http://localhost:3000`

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | JWT signing secret |
| `OPENAI_API_KEY` | Yes* | OpenAI API key for analysis |
| `USE_S3` | No | Set `true` to use AWS S3 storage |
| `S3_BUCKET` | No | S3 bucket name (default: `auto-data-analyst`) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |

\* Required only when running analyses

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL (default: `http://localhost:5000`) |

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | No | Health check |
| `/api/auth/register` | POST | No | Create account |
| `/api/auth/login` | POST | No | Sign in |
| `/api/auth/me` | GET | JWT | User profile + stats |
| `/api/datasets` | GET | JWT | List datasets |
| `/api/datasets/upload` | POST | JWT | Upload CSV |
| `/api/analyses` | GET | JWT | List analyses |
| `/api/analyses` | POST | JWT | Run analysis |
| `/api/analyses/:id` | GET | JWT | Get analysis details |

Legacy routes (`/login`, `/upload`, `/query`, `/results`) remain for backward compatibility.

## Production Deployment

### Backend (Gunicorn)

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend

```bash
cd frontend
npm run build
npm start
```

### AWS S3 (optional)

```bash
export USE_S3=true
export S3_BUCKET=auto-data-analyst
export AWS_REGION=ap-southeast-2
```

## Design System

The dashboard UI follows the [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) design intelligence skill:

- **Style**: Data-dense analytics dashboard
- **Colors**: Blue primary (#1E40AF) + amber accent (#D97706)
- **Typography**: Fira Sans + Fira Code
- **Patterns**: KPI cards, drag-and-drop upload, code viewer with copy

## License

MIT

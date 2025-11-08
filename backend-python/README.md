# ArcPay Python Backend

> FastAPI + SQLAlchemy + OpenAI backend for ArcPay

## 🚀 Quick Start

### 1. Install Python 3.9+

```bash
python --version  # Should be 3.9 or higher
```

### 2. Create Virtual Environment

```bash
cd backend-python

# Create venv
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env

# Edit .env and add your keys:
# - CIRCLE_API_KEY
# - OPENAI_API_KEY
# - CIRCLE_WALLET_ID
```

### 5. Run Server

```bash
python main.py
```

Server starts at: http://localhost:8000

API docs: http://localhost:8000/docs (automatic Swagger UI!)

---

## 📁 File Structure

```
backend-python/
├── main.py                 # FastAPI app & routes
├── config.py               # Settings management
├── database.py             # SQLAlchemy models & CRUD
├── circle_integration.py   # Circle API client
├── ai_agent.py            # OpenAI integration
├── scheduler.py           # APScheduler for cron jobs
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables
```

---

## 🔧 Tech Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: SQL ORM (SQLite by default)
- **APScheduler**: Background job scheduler
- **OpenAI**: GPT for natural language processing
- **Requests**: HTTP client for Circle API
- **Pydantic**: Data validation

---

## 🎯 API Endpoints

All endpoints documented at: http://localhost:8000/docs

### POST /api/parse-intent
Parse natural language payment command

```json
{
  "input": "Pay 50 USDC to Alice every week"
}
```

### POST /api/create-payment
Create scheduled payment

```json
{
  "walletId": "wallet-123",
  "recipient": "0x742d35Cc...",
  "amount": 50,
  "interval": "weekly"
}
```

### GET /api/payments?walletId=xxx
Get active payments

### GET /api/history?walletId=xxx&limit=50
Get payment history

### GET /api/balance?walletId=xxx
Get wallet balance

### POST /api/cancel-payment
Cancel a payment

### POST /api/query
Ask questions about payments

---

## 🔄 How It Works

1. **API Server** (FastAPI)
   - Handles HTTP requests from frontend
   - Validates inputs with Pydantic
   - Routes to appropriate handlers

2. **Database** (SQLAlchemy + SQLite)
   - Stores scheduled payments
   - Records execution history
   - Provides ORM for queries

3. **AI Agent** (OpenAI)
   - Parses natural language
   - Extracts payment details
   - Handles user queries

4. **Circle Integration**
   - Creates wallets
   - Checks balances
   - Transfers USDC

5. **Scheduler** (APScheduler)
   - Runs every 60 seconds
   - Checks for due payments
   - Executes automatically

---

## 🔑 Getting API Keys

### OpenAI API Key

1. Go to https://platform.openai.com
2. Sign up / Log in
3. Go to API Keys
4. Create new key
5. Copy and paste in .env

**Cost**: ~$0.002 per request (very cheap for this use case)

### Circle API Key

1. Go to https://console.circle.com
2. Sign up (free)
3. API Keys → Create Key
4. Copy to .env

---

## 📊 Database

Uses SQLite by default (file: `arcpay.db`)

**Tables:**
- `scheduled_payments` - Active payment schedules
- `payment_history` - Execution records

**To use PostgreSQL instead:**
```env
DATABASE_URL=postgresql://user:password@localhost/arcpay
```

Then:
```bash
pip install psycopg2-binary
python main.py  # Auto-creates tables
```

---

## 🧪 Testing

### Test API Directly

```bash
# Parse intent
curl -X POST http://localhost:8000/api/parse-intent \
  -H "Content-Type: application/json" \
  -d '{"input": "Pay 50 USDC to Alice every week"}'

# Get balance
curl http://localhost:8000/api/balance?walletId=your_wallet_id
```

### Interactive API Docs

Open http://localhost:8000/docs

You can test all endpoints interactively!

---

## 🚀 Deployment

### Option 1: Railway.app (Easiest)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Add environment variables
5. Deploy!

### Option 2: Render.com

1. Go to https://render.com
2. New Web Service
3. Connect GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables
7. Deploy!

### Option 3: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t arcpay-backend .
docker run -p 8000:8000 --env-file .env arcpay-backend
```

---

## 🐛 Troubleshooting

### "No module named 'openai'"

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### "Circle API Error: Unauthorized"

- Check CIRCLE_API_KEY in .env
- Ensure no extra spaces
- Try regenerating the key

### "Scheduler not running"

- Check `SCHEDULER_ENABLED=true` in .env
- Check logs for errors
- Verify database is accessible

### Frontend can't connect

- Check CORS_ORIGINS in .env includes your frontend URL
- Make sure server is running
- Check firewall settings

---

## 📚 Learn More

- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **OpenAI API**: https://platform.openai.com/docs
- **Circle API**: https://developers.circle.com
- **APScheduler**: https://apscheduler.readthedocs.io

---

## 🆚 vs Cloudflare Workers

| Feature | Python (FastAPI) | Cloudflare Workers |
|---------|------------------|-------------------|
| **Language** | Python | JavaScript |
| **Deployment** | Traditional server | Serverless edge |
| **Database** | SQLite/PostgreSQL | D1 (SQLite) |
| **Scheduler** | APScheduler | Cron Triggers |
| **AI** | OpenAI API | Workers AI (built-in) |
| **Cost** | Server costs | Free tier generous |
| **Ease** | More familiar | More setup |

**Why Python?**
- ✅ More familiar for many developers
- ✅ Rich ecosystem (pandas, numpy, etc.)
- ✅ Easy local development
- ✅ Better debugging
- ✅ More AI/ML libraries

---

**Ready to build! 🚀**


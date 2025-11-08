# ArcPay - AI Payment Automation

> Automate recurring USDC payments on Arc blockchain with natural language

**Demo**: [Video Link]  
**Live**: [Deployed URL]

---

## What is ArcPay?

ArcPay lets you create automated payments using simple English:

```
"Pay 50 USDC to Alice every week"
```

The AI understands, schedules, and executes automatically. No manual transactions needed.

---

## Tech Stack

- **Blockchain**: Arc Testnet (fully supported by Circle)
- **Token**: USDC
- **Wallets**: Circle Developer-Controlled Wallets
- **Backend**: Python + FastAPI
- **AI**: OpenAI GPT
- **Frontend**: React + Vite
- **Database**: SQLite

---

## Quick Start (30 minutes)

### 1. Prerequisites

- Python 3.9+
- Node.js 18+
- Git

### 2. Get API Keys

**Circle** (for wallets):
- Sign up: https://developers.circle.com
- Get API key from dashboard

**OpenAI** (for AI):
- Sign up: https://platform.openai.com
- Get API key (first $5 free)

### 3. Setup Backend

```bash
cd backend-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your API keys

# Create wallets
python setup_wallets.py

# Start server
python main.py
```

Backend runs at: http://localhost:8000

### 4. Fund Wallet

Go to https://faucet.circle.com
- Select "Arc Testnet"
- Enter your payer wallet address
- Request test USDC

### 5. Setup Frontend

```bash
cd frontend

# Install
npm install

# Configure
cp .env.example .env
nano .env  # Add backend URL and wallet ID

# Start
npm run dev
```

Frontend runs at: http://localhost:5173

### 6. Test

1. Open http://localhost:5173
2. Create payment: "Send 2 USDC to [address] every 2 minutes"
3. Wait 2 minutes
4. Watch it execute automatically!

---

## Project Structure

```
ArcFlux/
├── backend-python/      # FastAPI backend
│   ├── main.py         # API endpoints
│   ├── ai_agent.py     # OpenAI integration
│   ├── circle_integration.py  # Circle Wallets
│   ├── scheduler.py    # Auto-execution
│   └── database.py     # SQLAlchemy models
│
└── frontend/           # React dashboard
    └── src/
        ├── App.jsx
        └── components/
            ├── Dashboard.jsx
            ├── CreatePayment.jsx
            └── PaymentHistory.jsx
```

---

## How It Works

1. **User types**: Natural language payment command
2. **AI parses**: Extracts amount, recipient, schedule
3. **Database stores**: Payment schedule saved
4. **Scheduler runs**: Checks every minute for due payments
5. **Circle executes**: Sends USDC on Arc blockchain
6. **History records**: Transaction tracked forever

---

## Key Features

- ✅ Natural language interface (AI-powered)
- ✅ Automatic execution (cron-based)
- ✅ Arc blockchain integration
- ✅ Circle Wallets (secure custody)
- ✅ Payment history tracking
- ✅ Real-time balance display

---

## Use Cases

- **Rent payments**: Never miss rent again
- **Payroll**: Automated employee salaries
- **Subscriptions**: Recurring creator payments
- **Invoices**: Supply chain automation

---

## API Endpoints

**Backend** (http://localhost:8000):
- `POST /api/parse-intent` - Parse natural language
- `POST /api/create-payment` - Schedule payment
- `GET /api/payments` - List active payments
- `GET /api/history` - View execution history
- `GET /api/balance` - Check wallet balance

**Docs**: http://localhost:8000/docs (interactive Swagger UI)

---

## Deployment

### Backend (Railway/Render)

```bash
# Railway
railway up

# Render
# Push to GitHub, connect repo, deploy
```

### Frontend (Vercel)

```bash
npm run build
# Upload dist/ to Vercel or connect GitHub repo
```

---

## Troubleshooting

**"Module not found"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**"Circle API Error"**
- Check API key in `.env`
- Ensure no extra spaces

**"Balance shows 0"**
- Fund wallet at https://faucet.circle.com
- Wait 30 seconds

**"Payment not executing"**
- Check backend is running
- Wait full interval period
- Check logs: backend shows execution

---

## Resources

- **Circle Docs**: https://developers.circle.com
- **Arc Docs**: https://docs.arc.network
- **OpenAI Docs**: https://platform.openai.com/docs

---

## License

MIT License - Open source for the community

---

## Hackathon

Built for Arc x Circle Hackathon 2024

**Tracks**: RWA Payments + On-chain Actions  
**Innovation**: AI-powered blockchain automation  
**Impact**: Eliminates missed payments, reduces errors

---

**Questions?** See the Quick Start section above or check the backend-python/README.md for detailed setup instructions.


347190
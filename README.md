# ArcFlux - AI Payment Automation

> Automate recurring USDC payments on Arc blockchain with natural language. Built with AI agents, risk assessment, and voice commands.

**Demo**: [Video Link]  
**Live**: [Deployed URL]

---

## What is ArcFlux?

ArcFlux is an AI-powered payment automation platform that lets you manage USDC payments on the Arc blockchain using natural language:

```
"Pay 50 USDC to Alice every week"
"Send 100 USDC to John for rent"
"Buy $50 worth of stock in tech sector"
```

The AI understands your intent, assesses risk, and executes payments automatically. No manual transactions needed.

---

## ✨ Key Features

### 🤖 AI-Powered Agents
- **Payment Agent**: MLAI-powered natural language payment processing
- **Query Agent**: Ask questions about your payments and get dashboard visualizations
- **Guardian Agent**: Intelligent risk assessment for all transactions
- **Stock Agent**: Purchase stocks using natural language commands

### 🔐 Security & Risk Management
- **Risk Assessment**: Every payment is evaluated for risk before execution
- **Guardian System**: Blocks high-risk transactions automatically
- **User Authentication**: Secure login/registration system
- **Wallet Management**: Per-user wallet creation with Circle API

### 💰 Payment Features
- **Natural Language Interface**: Create payments using simple English
- **Recurring Payments**: Schedule automatic recurring transactions
- **One-Time Payments**: Immediate execution for instant transfers
- **Contact Management**: Save and manage recipient addresses
- **Payment History**: Complete transaction history with blockchain verification

### 📊 Analytics & Insights
- **Financial Dashboard**: Visualize spending patterns and analytics
- **Balance Monitoring**: Real-time wallet balance tracking
- **Spending Analysis**: Insights into payment patterns
- **Transaction Charts**: Visual breakdown of recipients and spending over time

### 🎤 Voice Commands
- **Voice Input**: Transcribe audio commands using ElevenLabs
- **Voice-to-Payment**: Convert spoken commands to payments

### 📈 Stock Purchases
- **Stock Recommendations**: AI suggests stocks based on your criteria
- **Sector-Based Selection**: Choose stocks by sector or preference
- **Automated Execution**: Complete stock purchases with risk assessment

---

## Tech Stack

### Backend
- **Framework**: Python + FastAPI
- **Database**: SQLite (with SQLAlchemy ORM)
- **Scheduler**: APScheduler for automatic payment execution
- **AI**: OpenAI GPT-4 for natural language processing
- **Blockchain**: Circle Developer-Controlled Wallets on Arc Testnet
- **Token**: USDC (Circle's native stablecoin)

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router
- **State Management**: React Hooks

### AI & Services
- **OpenAI**: GPT-4 for payment parsing and queries
- **Circle API**: Wallet management and USDC transfers
- **ElevenLabs**: Voice transcription (optional)
- **MLAI API**: Payment agent processing

---

## Quick Start (30 minutes)

### 1. Prerequisites

- Python 3.9+
- Node.js 18+
- Git
- Circle API account
- OpenAI API account

### 2. Get API Keys

**Circle** (for wallets):
- Sign up: https://developers.circle.com
- Get API key from dashboard
- Create Entity Secret

**OpenAI** (for AI):
- Sign up: https://platform.openai.com
- Get API key (first $5 free)

**ElevenLabs** (optional, for voice):
- Sign up: https://elevenlabs.io
- Get API key

**MLAI API** (for payment agent):
- Sign up: https://mlai.com (or your MLAI provider)
- Get API key

### 3. Setup Backend

```bash
cd backend-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys
```

**Required environment variables:**
```env
CIRCLE_API_KEY=your_circle_api_key
CIRCLE_ENTITY_SECRET=your_entity_secret
OPENAI_API_KEY=your_openai_api_key
MLAI_API_KEY=your_mlai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key  # Optional
```

```bash
# Start server
python main.py
```

Backend runs at: http://localhost:8000

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure (optional - uses defaults if not set)
cp .env.example .env
nano .env  # Add backend URL
```

**Environment variables (optional):**
```env
VITE_API_URL=http://localhost:8000
```

```bash
# Start development server
npm run dev
```

Frontend runs at: http://localhost:5173

### 5. First Steps

1. **Register Account**: Go to http://localhost:5173 and sign up
2. **Generate Wallet**: Add your Circle API key in Profile Settings to create your wallet
3. **Fund Wallet**: Go to https://faucet.circle.com and request test USDC on Arc Testnet
4. **Add Contacts**: Add recipient addresses in the Dashboard
5. **Create Payment**: Use natural language to create your first payment

---

## Project Structure

```
ArcFlux/
├── backend-python/           # FastAPI backend
│   ├── main.py              # API endpoints
│   ├── ai_agent.py          # OpenAI integration
│   ├── payment_agent.py     # MLAI payment agent
│   ├── query_agent.py       # Query agent with dashboard
│   ├── guardian_agent.py    # Risk assessment agent
│   ├── stock_agent.py       # Stock purchase agent
│   ├── circle_integration.py # Circle Wallets SDK
│   ├── scheduler.py         # Auto-execution scheduler
│   ├── database.py          # SQLAlchemy models
│   ├── balance_monitor.py   # Balance monitoring
│   ├── wallet_creation.py   # Wallet generation
│   ├── voice/               # Voice transcription
│   └── requirements.txt     # Python dependencies
│
└── frontend/                # React frontend
    └── src/
        ├── App.jsx          # Main app with routing
        └── components/
            ├── Dashboard.jsx           # Main dashboard
            ├── CreatePayment.jsx       # Payment creation
            ├── PaymentHistory.jsx      # Transaction history
            ├── QueryAgent.jsx          # Query interface
            ├── ContactsCenter.jsx      # Contact management
            ├── UserProfile.jsx         # User settings
            ├── WalletSetup.jsx         # Wallet generation
            ├── VoiceInput.jsx          # Voice commands
            ├── Login.jsx               # Authentication
            └── Signup.jsx              # Registration
```

---

## How It Works

### Payment Flow

1. **User Input**: Natural language payment command
2. **AI Parsing**: Payment Agent extracts amount, recipient, schedule
3. **Risk Assessment**: Guardian Agent evaluates transaction risk
4. **Contact Matching**: Matches recipient to saved contacts
5. **Database Storage**: Payment schedule saved (if recurring)
6. **Execution**: 
   - One-time: Executes immediately
   - Recurring: Scheduled for automatic execution
7. **Blockchain**: Circle SDK sends USDC on Arc blockchain
8. **History**: Transaction tracked and recorded

### Stock Purchase Flow

1. **User Request**: "Buy $50 worth of tech stocks"
2. **Stock Agent**: Analyzes request and suggests stocks
3. **User Selection**: User selects from recommendations
4. **Risk Assessment**: Guardian Agent evaluates purchase
5. **Execution**: USDC transferred to stock purchase address
6. **Recording**: Transaction recorded in history

### Query & Dashboard Flow

1. **User Query**: "Show me my spending dashboard"
2. **Query Agent**: Analyzes request and fetches data
3. **Dashboard Generation**: Creates visualizations and insights
4. **Display**: Shows charts, stats, and recommendations

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Wallet Management
- `POST /api/wallet/generate` - Generate wallet for user
- `GET /api/user/profile` - Get user profile
- `GET /api/balance` - Get wallet balance

### Payments
- `POST /api/parse-intent` - Parse natural language payment
- `POST /api/create-payment` - Create scheduled payment
- `GET /api/payments` - List active payments
- `POST /api/cancel-payment` - Cancel payment
- `GET /api/history` - View payment history

### AI Agents
- `POST /api/query` - Query agent (with dashboard support)
- `POST /api/agent/pay` - Payment agent with risk assessment

### Contacts
- `POST /api/contacts` - Create contact
- `GET /api/contacts` - List contacts
- `DELETE /api/contacts/{id}` - Delete contact

### Voice
- `POST /api/transcribe-audio` - Transcribe audio file

### Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /` - Health check

---

## Key Features Explained

### 🔒 Risk Assessment

Every payment is evaluated by the Guardian Agent before execution:

- **Balance Check**: Ensures sufficient funds
- **Risk Scoring**: Calculates risk based on amount, recipient, and history
- **Decision Making**: Approves, flags, or denies transactions
- **Reasoning**: Provides explanation for decisions

**Risk Levels:**
- 🟢 **Low Risk**: Approved automatically
- 🟡 **Medium Risk**: Requires confirmation
- 🔴 **High Risk**: Blocked automatically

### 📊 Dashboard & Analytics

The Query Agent generates interactive dashboards with:

- **Summary Stats**: Balance, total spent, transaction count
- **Spending Charts**: Visual breakdown by recipient and time
- **Insights**: AI-generated insights about spending patterns
- **Transaction History**: Recent transactions with details

**Trigger dashboard by asking:**
- "Show me my dashboard"
- "Visualize my spending"
- "Generate analytics"
- "Display my financial summary"

### 💬 Natural Language Interface

Create payments using simple English:

**Examples:**
- "Send 50 USDC to Alice every week"
- "Pay 100 USDC to John for rent monthly"
- "Transfer 25 USDC to Bob once"
- "Buy $50 worth of tech stocks"

### 🎤 Voice Commands

Record audio and convert to payment commands:

1. Click voice input button
2. Record your command
3. Audio transcribed to text
4. Process as payment command

---

## Use Cases

### Personal Finance
- **Rent Payments**: Never miss rent again
- **Bill Automation**: Auto-pay recurring bills
- **Savings Goals**: Automated savings transfers
- **Investment**: Automated stock purchases

### Business
- **Payroll**: Automated employee salaries
- **Vendor Payments**: Recurring supplier payments
- **Subscriptions**: Creator/subscription payments
- **Invoices**: Supply chain automation

### Investment
- **Dollar-Cost Averaging**: Regular stock purchases
- **Sector Investing**: Automated sector-based investing
- **Portfolio Rebalancing**: Automated rebalancing

---

## Deployment

### Backend (Railway/Render)

```bash
# Railway
railway up

# Render
# Push to GitHub, connect repo, set environment variables, deploy
```

**Environment Variables:**
- `CIRCLE_API_KEY`
- `CIRCLE_ENTITY_SECRET`
- `OPENAI_API_KEY`
- `MLAI_API_KEY`
- `ELEVENLABS_API_KEY` (optional)
- `DATABASE_URL` (for PostgreSQL)

### Frontend (Vercel/Netlify)

```bash
npm run build
# Upload dist/ to Vercel or connect GitHub repo
```

**Environment Variables:**
- `VITE_API_URL` - Backend API URL

---

## Troubleshooting

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Circle API Error"
- Check API key in `.env`
- Ensure Entity Secret is set
- Verify API key has correct permissions
- Check for extra spaces in environment variables

### "Balance shows 0"
- Fund wallet at https://faucet.circle.com
- Select "Arc Testnet"
- Wait 30 seconds for balance to update
- Check wallet address is correct

### "Payment not executing"
- Check backend is running
- Verify scheduler is enabled
- Check database for payment records
- Review backend logs for errors
- Ensure wallet has sufficient balance

### "Authentication failed"
- Check user exists in database
- Verify password is correct
- Clear browser localStorage
- Check backend logs for errors

### "Wallet generation failed"
- Verify Circle API key is valid
- Check Entity Secret is correct
- Ensure API key has wallet creation permissions
- Review backend logs for detailed error

### "Risk assessment error"
- Check Guardian Agent is configured
- Verify OpenAI API key is set
- Check backend logs for AI errors

---

## Development

### Running Tests

```bash
# Backend tests
cd backend-python
pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure

**Backend Agents:**
- `ai_agent.py`: OpenAI integration for parsing
- `payment_agent.py`: MLAI-powered payment processing
- `query_agent.py`: Query processing and dashboard generation
- `guardian_agent.py`: Risk assessment and security
- `stock_agent.py`: Stock purchase processing

**Frontend Components:**
- `Dashboard.jsx`: Main dashboard with stats
- `CreatePayment.jsx`: Payment creation form
- `QueryAgent.jsx`: Query interface with dashboard
- `ContactsCenter.jsx`: Contact management
- `UserProfile.jsx`: User settings and wallet setup

### Adding New Features

1. **Backend**: Add endpoint in `main.py`
2. **Database**: Add model in `database.py`
3. **Frontend**: Create component in `components/`
4. **Routing**: Add route in `App.jsx`

---

## Resources

- **Circle Docs**: https://developers.circle.com
- **Arc Docs**: https://docs.arc.network
- **OpenAI Docs**: https://platform.openai.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev

---

## License

MIT License - Open source for the community

---

## Hackathon

Built for Arc x Circle Hackathon 2024

**Tracks**: RWA Payments + On-chain Actions  
**Innovation**: AI-powered blockchain automation with risk assessment  
**Impact**: Eliminates missed payments, reduces errors, provides intelligent security

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Support

**Questions?** 
- Check the Troubleshooting section above
- Review the backend-python/README.md for detailed setup
- Check the DASHBOARD_CODE_REFERENCE.md for dashboard details
- Open an issue on GitHub

---

**Built with ❤️ using Arc, Circle, OpenAI, ElevenLabs, MLAI API and Cloudflare agents.**

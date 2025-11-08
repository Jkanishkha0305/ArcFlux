# 🚀 How to Start ArcPay

## Quick Start Guide

### 1. Start Backend (Terminal 1)

```bash
cd backend-python

# Activate conda environment (if using conda)
conda activate arcpay

# OR use venv (if using venv)
# source venv/bin/activate

# Start the backend server
python main.py
```

**Backend runs on:** http://localhost:8000

You should see:
```
🚀 Starting ArcPay API...
✓ ArcPay API ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 2. Start Frontend (Terminal 2)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the frontend dev server
npm run dev
```

**Frontend runs on:** http://localhost:5173

You should see:
```
VITE v5.0.7  ready in XXX ms

➜  Local:   http://localhost:5173/
```

---

## 🎯 Access the Application

1. **Open your browser:** http://localhost:5173
2. **You should see:** ArcPay Dashboard with your wallet balance

---

## ✅ Verify Everything Works

1. **Check backend:** http://localhost:8000/api/balance?walletId=YOUR_WALLET_ID
2. **Check frontend:** http://localhost:5173 (should show dashboard)

---

## 🔧 Troubleshooting

### Backend won't start?
- Make sure port 8000 is not in use: `lsof -ti:8000 | xargs kill -9`
- Check your `.env` file has correct API keys
- Make sure conda/venv is activated

### Frontend won't start?
- Make sure port 5173 is not in use
- Run `npm install` if you see module errors
- Check `frontend/.env` has `VITE_API_URL` and `VITE_WALLET_ID`

### Connection errors?
- Make sure backend is running first
- Check `VITE_API_URL` in `frontend/.env` matches backend URL
- Check CORS settings in backend

---

## 📝 Environment Files

**Backend:** `backend-python/.env`
```env
CIRCLE_API_KEY=your_key_here
CIRCLE_WALLET_ID=your_wallet_id
CIRCLE_ENTITY_SECRET=your_entity_secret
OPENAI_API_KEY=your_openai_key
```

**Frontend:** `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
VITE_WALLET_ID=your_wallet_id
```

---

## 🛑 Stop Services

- **Backend:** Press `Ctrl+C` in Terminal 1
- **Frontend:** Press `Ctrl+C` in Terminal 2


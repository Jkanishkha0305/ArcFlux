# Authentication & Automatic Wallet Creation

## ✅ What's Implemented

### 1. **Login/Signup Required**
- Users must now log in or sign up to access the app
- No more fallback to allow access without authentication
- Login and Signup pages are accessible at `/login` and `/signup`

### 2. **Automatic Wallet Creation on Signup**
When a user signs up, the following happens automatically:

1. **User Account Created**
   - Email, password (hashed), and name stored
   - Account is activated immediately

2. **Circle Wallet Created**
   - Wallet Set is created for the user
   - Wallet is created on Arc Testnet
   - Wallet ID, Wallet Address, and Entity Secret are generated

3. **Secure Storage**
   - Wallet ID stored in user account
   - Wallet Address (blockchain address) stored
   - Entity Secret (encrypted) stored as hex string
   - Wallet Set ID stored

4. **Ready to Use**
   - User can immediately start using their wallet
   - No manual wallet setup required

### 3. **User-Specific Wallet Operations**
- Each user has their own wallet
- All operations use the user's entity secret
- Wallet information is securely stored in the database
- Users can see their wallet address on the dashboard

## 🔐 Security Features

- **Password Hashing**: Passwords are hashed using bcrypt
- **Entity Secret Storage**: Entity secrets are stored as hex strings in the database
- **JWT Tokens**: Authentication uses JWT tokens
- **User Isolation**: Each user's wallet operations are isolated

## 📊 Database Schema

### User Table
```sql
- id: String (primary key)
- email: String (unique, indexed)
- password_hash: String (bcrypt hashed)
- name: String
- wallet_id: String (nullable, indexed)
- wallet_address: String (nullable)
- entity_secret: String (nullable) - hex format
- wallet_set_id: String (nullable)
- created_at: Integer (timestamp)
- is_active: Boolean
```

## 🚀 How It Works

### Signup Flow
1. User fills out signup form (name, email, password)
2. Backend creates Circle wallet:
   - Gets Circle's public key
   - Generates entity secret (32 bytes)
   - Encrypts entity secret
   - Creates wallet set
   - Creates wallet on Arc Testnet
3. User account created with wallet info
4. JWT token generated and returned
5. User redirected to dashboard

### Login Flow
1. User enters email and password
2. Backend verifies credentials
3. JWT token generated
4. User data (including wallet_id) returned
5. User redirected to dashboard

### Wallet Operations
- All wallet operations (balance, transfers, etc.) use the user's entity secret
- The system automatically detects which user owns a wallet
- Operations are scoped to the authenticated user

## 🔧 Configuration

Make sure you have `CIRCLE_API_KEY` set in your `.env` file:

```env
CIRCLE_API_KEY=your_circle_api_key_here
```

The wallet creation will use this API key to create wallets for new users.

## 📝 Notes

- If wallet creation fails during signup, the user account is still created
- User can use the app, but wallet operations will be limited
- Wallet creation can be retried later if needed
- All wallets are created on Arc Testnet
- Users need to fund their wallets from the Circle faucet

## 🧪 Testing

1. **Signup**:
   ```bash
   POST /api/auth/register
   {
     "email": "test@example.com",
     "password": "password123",
     "name": "Test User"
   }
   ```

2. **Login**:
   ```bash
   POST /api/auth/login
   {
     "email": "test@example.com",
     "password": "password123"
   }
   ```

3. **Check Wallet**:
   - Login to the app
   - Check dashboard - wallet address should be displayed
   - Wallet ID is stored in user account

## 🐛 Troubleshooting

### Wallet Creation Fails
- Check `CIRCLE_API_KEY` is set correctly
- Check Circle API is accessible
- Check API key has permissions to create wallets

### Can't Login
- Make sure you've signed up first
- Check email and password are correct
- Check backend is running

### Wallet Not Showing
- Check database has wallet information
- Verify wallet was created successfully during signup
- Check user account has wallet_id and wallet_address


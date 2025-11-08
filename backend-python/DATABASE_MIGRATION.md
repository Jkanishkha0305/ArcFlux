# Database Migration Guide

## Important: User Model Updated

The User model has been updated to include wallet information. If you have an existing database, you need to migrate it.

### New User Model Fields

The User table now includes:
- `wallet_address` - Wallet blockchain address
- `entity_secret` - Encrypted entity secret (hex format)
- `wallet_set_id` - Wallet set ID from Circle

### Migration Options

#### Option 1: Delete and Recreate (Development Only)

If you're in development and don't have important data:

```bash
cd backend-python
rm arcflux.db
python main.py  # This will recreate the database with new schema
```

#### Option 2: Manual Migration (Recommended for Production)

1. The database will be automatically updated when you restart the server
2. SQLAlchemy will add the new columns automatically
3. Existing users will have `NULL` values for new fields (which is fine - they can create wallets later)

### Verification

After migration, verify the schema:

```python
from database import User, init_db, get_db
from sqlalchemy import inspect

init_db()
db = next(get_db())
inspector = inspect(db.bind)

columns = [col['name'] for col in inspector.get_columns('users')]
print("User table columns:", columns)

# Should include: wallet_address, entity_secret, wallet_set_id
```

### Notes

- Existing users without wallets will have `NULL` values for wallet fields
- New users will automatically get wallets created on signup
- Wallet creation happens in the `/api/auth/register` endpoint


# Fix for Pydantic Compatibility Issue

## Problem
The Circle SDK requires Pydantic v1.x, but the project was using Pydantic v2.5.0, which caused this error:
```
pydantic.errors.PydanticUserError: `const` is removed, use `Literal` instead
```

## Solution
Downgraded Pydantic to v1.10.13 to be compatible with the Circle SDK.

## Changes Made

1. **Updated `requirements.txt`**:
   - Changed `pydantic==2.5.0` to `pydantic==1.10.13`
   - Removed `pydantic-settings==2.1.0` (not compatible with Pydantic v1)
   - Using `BaseSettings` from Pydantic v1 directly

2. **Updated `config.py`**:
   - Changed from `pydantic-settings` to `pydantic.BaseSettings`
   - Updated the Settings class to inherit from `BaseSettings` (Pydantic v1 syntax)

## Installation

**IMPORTANT: Use the `arcpay` conda environment, not the base environment!**

1. Activate the arcpay conda environment:
   ```bash
   conda activate arcpay
   ```

2. Install/update Pydantic in the arcpay environment:
   ```bash
   cd backend-python
   conda run -n arcpay pip uninstall -y pydantic pydantic-core pydantic-settings
   conda run -n arcpay pip install "pydantic==1.10.13"
   ```

   OR if you're already in the arcpay environment:
   ```bash
   pip uninstall -y pydantic pydantic-core pydantic-settings
   pip install "pydantic==1.10.13"
   ```

3. Install other dependencies in the arcpay environment:
   ```bash
   conda run -n arcpay pip install -r requirements.txt
   ```

4. Verify the installation:
   ```bash
   conda run -n arcpay python -c "import pydantic; print(pydantic.__version__)"  # Should show 1.10.13
   conda run -n arcpay python -c "from circle.web3 import developer_controlled_wallets; print('✅ Circle SDK works!')"
   ```

## Notes

- FastAPI 0.104.1 works with both Pydantic v1 and v2
- The Circle SDK is not in requirements.txt - it should be installed separately if needed
- If you see dependency conflicts with other packages (like mcp, surya-ocr), those are from other projects in your global environment and won't affect ArcFlux if you use a virtual/conda environment

## Testing

After installing Pydantic v1.10.13, test that the Circle SDK imports correctly:
```bash
python -c "from circle.web3 import developer_controlled_wallets; print('Success!')"
```

If you still see errors, make sure you're in the correct conda/virtual environment.


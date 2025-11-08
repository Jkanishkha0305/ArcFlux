import React, { useState } from 'react';

function WalletSetup({ apiUrl, userId, onWalletGenerated }) {
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    if (!apiKey || apiKey.trim().length < 10) {
      setError('Please enter a valid Circle API key');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/api/wallet/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey.trim(),
          user_id: userId
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.detail || errorData.error || 'Failed to generate wallet');
        setLoading(false);
        return;
      }

      const data = await response.json();

      if (data.success) {
        setSuccess(true);
        setApiKey('');
        
        // Update user info in localStorage
        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        userData.wallet_id = data.wallet.wallet_id;
        userData.wallet_address = data.wallet.wallet_address;
        userData.has_api_key = true;
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Call callback to update parent component
        if (onWalletGenerated) {
          onWalletGenerated(userData);
        }
        
        // Reload page after 2 seconds to show wallet info
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        setError(data.error || 'Failed to generate wallet');
      }
    } catch (err) {
      console.error('Wallet generation error:', err);
      setError('Could not connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <h3 className="text-xl font-bold text-gray-900 mb-2">Generate Your Wallet</h3>
      <p className="text-sm text-gray-600 mb-6">
        Enter your Circle API key to generate your wallet. You can get your API key from{' '}
        <a
          href="https://console.circle.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 underline"
        >
          Circle Console
        </a>
        .
      </p>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800">
          ✅ Wallet generated successfully! Your wallet is being set up...
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Circle API Key
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter your Circle API key"
            required
            disabled={loading || success}
          />
          <p className="mt-1 text-xs text-gray-500">
            Your API key is stored securely and will not be shared.
          </p>
        </div>

        <button
          type="submit"
          disabled={loading || success}
          className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? 'Generating Wallet...' : success ? 'Wallet Generated!' : 'Generate Wallet'}
        </button>
      </form>
    </div>
  );
}

export default WalletSetup;


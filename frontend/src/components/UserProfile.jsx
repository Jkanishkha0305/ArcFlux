import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import WalletSetup from './WalletSetup';

function UserProfile({ apiUrl, user, onWalletGenerated }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user && user.id) {
      loadProfile();
    }
  }, [user]);

  async function loadProfile() {
    if (!user || !user.id) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/api/user/profile?user_id=${user.id}`);
      if (!response.ok) {
        throw new Error('Failed to load profile');
      }
      const data = await response.json();
      if (data.success) {
        setProfile(data.user);
      }
    } catch (err) {
      console.error('Error loading profile:', err);
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  }

  const handleWalletGenerated = (updatedUser) => {
    setProfile(updatedUser);
    if (onWalletGenerated) {
      onWalletGenerated(updatedUser);
    }
    // Reload profile to get latest data
    loadProfile();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-gray-600">Loading profile...</div>
      </div>
    );
  }

  const displayUser = profile || user;
  const hasWallet = displayUser?.wallet_id && displayUser?.wallet_address;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-6">
            Profile Settings
          </h1>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* User Information */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <div className="text-gray-900">{displayUser?.name || 'N/A'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <div className="text-gray-900">{displayUser?.email || 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* Wallet Information */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Wallet Information</h2>
            
            {!hasWallet ? (
              <div>
                <p className="text-gray-600 mb-4">
                  You don't have a wallet yet. Generate one by entering your Circle API key.
                </p>
                <WalletSetup
                  apiUrl={apiUrl}
                  userId={displayUser?.id}
                  onWalletGenerated={handleWalletGenerated}
                />
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Wallet ID</label>
                  <div className="text-gray-900 font-mono text-sm break-all">{displayUser.wallet_id}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Wallet Address</label>
                  <div className="text-gray-900 font-mono text-sm break-all">{displayUser.wallet_address}</div>
                  <a
                    href={`https://testnet.arcscan.com/address/${displayUser.wallet_address}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-xs mt-1 inline-block"
                  >
                    View on Arc Explorer →
                  </a>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Key Status</label>
                  <div className="text-gray-900">
                    {displayUser.api_key_display || (displayUser.has_api_key ? '****-****-****-****' : 'Not set')}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {displayUser.has_api_key 
                      ? 'Your API key is securely stored and cannot be changed.'
                      : 'API key is not set.'}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <Link
              to="/"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserProfile;


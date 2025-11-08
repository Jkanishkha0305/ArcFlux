/**
 * ============================================
 * NEW DASHBOARD - FANCY HOMEPAGE
 * ============================================
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PaymentHistorySidebar from './PaymentHistorySidebar';
import ContactsCenter from './ContactsCenter';
import QueryAgent from './QueryAgent';
import WalletSetup from './WalletSetup';

function Dashboard({ apiUrl, walletId, user, onWalletGenerated }) {
  const [balance, setBalance] = useState('0.00');
  const [activePayments, setActivePayments] = useState(0);
  const [totalTransferred, setTotalTransferred] = useState('0.00');
  const [loading, setLoading] = useState(true);
  const [showWalletSetup, setShowWalletSetup] = useState(false);
  
  // Use wallet_id from user object if available, otherwise fall back to prop
  const effectiveWalletId = user?.wallet_id || walletId;
  const hasWallet = !!effectiveWalletId;
  
  // Show wallet setup if user doesn't have a wallet
  useEffect(() => {
    if (user && !hasWallet) {
      setShowWalletSetup(true);
    }
  }, [user, hasWallet]);

  useEffect(() => {
    if (effectiveWalletId) {
      loadStats();
      const interval = setInterval(loadStats, 30000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [effectiveWalletId]);

  async function loadStats() {
    if (!effectiveWalletId) {
      setLoading(false);
      return;
    }
    try {
      // Load balance
      const balanceResponse = await fetch(`${apiUrl}/api/balance?walletId=${effectiveWalletId}`);
      if (balanceResponse.ok) {
        const balanceData = await balanceResponse.json();
        setBalance(balanceData.balance || '0.00');
      }

      // Load active payments
      const paymentsResponse = await fetch(`${apiUrl}/api/payments?walletId=${effectiveWalletId}`);
      if (paymentsResponse.ok) {
        const paymentsData = await paymentsResponse.json();
        const active = (paymentsData.payments || []).filter(p => p.status === 'active').length;
        setActivePayments(active);
        
        // Calculate total transferred from active payments
        const total = (paymentsData.payments || [])
          .filter(p => p.status === 'active')
          .reduce((sum, p) => sum + (parseFloat(p.total_sent) || 0), 0);
        setTotalTransferred(total.toFixed(2));
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Top Stats Bar */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Welcome back, {user?.name || 'User'} 👋
              </h2>
              <p className="text-sm text-gray-600 mt-1">Manage your payments effortlessly</p>
            </div>
            <Link
              to="/create"
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-200"
            >
              + New Payment
            </Link>
          </div>
          
          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <p className="text-xs text-blue-600 font-medium mb-1">Active Transactions</p>
              <p className="text-2xl font-bold text-blue-900">
                {loading ? '...' : activePayments}
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <p className="text-xs text-purple-600 font-medium mb-1">Total Transferred</p>
              <p className="text-2xl font-bold text-purple-900">
                {loading ? '...' : `${totalTransferred} USDC`}
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <p className="text-xs text-green-600 font-medium mb-1">Wallet Balance</p>
              <p className="text-2xl font-bold text-green-900">
                {loading ? '...' : `${balance} USDC`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Wallet Setup Prompt - Show if user doesn't have wallet */}
        {showWalletSetup && user && !hasWallet && (
          <div className="mb-6">
            <WalletSetup
              apiUrl={apiUrl}
              userId={user.id}
              onWalletGenerated={(updatedUser) => {
                setShowWalletSetup(false);
                if (onWalletGenerated) {
                  onWalletGenerated(updatedUser);
                }
              }}
            />
            <div className="mt-4 text-center">
              <Link
                to="/profile"
                className="text-blue-600 hover:text-blue-800 text-sm underline"
              >
                Or set up wallet in Profile Settings →
              </Link>
            </div>
          </div>
        )}

        {/* Main Content - Only show if wallet exists */}
        {hasWallet ? (
          <div className="grid grid-cols-12 gap-6" style={{ minHeight: 'calc(100vh - 350px)' }}>
            {/* Left - Payment History */}
            <div className="col-span-3">
              <PaymentHistorySidebar apiUrl={apiUrl} walletId={effectiveWalletId} />
            </div>

            {/* Center-Left - Query Agent (Chat Interface) */}
            <div className="col-span-5">
              <QueryAgent apiUrl={apiUrl} walletId={effectiveWalletId} />
            </div>

            {/* Right - Contacts (3 Columns) */}
            <div className="col-span-4">
              <ContactsCenter apiUrl={apiUrl} walletId={effectiveWalletId} />
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">
              Set up your wallet to get started with ArcFlux.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;

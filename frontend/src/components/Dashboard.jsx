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
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 flex flex-col">
      {/* Top Stats Bar */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 shadow-sm flex-shrink-0">
        <div className="w-full px-6 py-3">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Welcome back, {user?.name || 'User'} 👋
              </h2>
              <p className="text-xs text-gray-600 mt-0.5">Manage your payments effortlessly</p>
            </div>
            <Link
              to="/create"
              className="px-4 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-200 text-sm"
            >
              + New Payment
            </Link>
          </div>
          
          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-3 border border-blue-200">
              <p className="text-xs text-blue-600 font-medium mb-0.5">Active Transactions</p>
              <p className="text-xl font-bold text-blue-900">
                {loading ? '...' : activePayments}
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-3 border border-purple-200">
              <p className="text-xs text-purple-600 font-medium mb-0.5">Total Transferred</p>
              <p className="text-xl font-bold text-purple-900">
                {loading ? '...' : `${totalTransferred} USDC`}
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-3 border border-green-200">
              <p className="text-xs text-green-600 font-medium mb-0.5">Wallet Balance</p>
              <p className="text-xl font-bold text-green-900">
                {loading ? '...' : `${balance} USDC`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="w-full px-6 py-4 flex-1 min-h-0 overflow-hidden flex flex-col">
        {/* Wallet Setup Prompt - Show if user doesn't have wallet */}
        {showWalletSetup && user && !hasWallet && (
          <div className="mb-4 flex-shrink-0">
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
            <div className="mt-3 text-center">
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
        <div className="flex-1 min-h-0">
          {hasWallet ? (
            <div className="grid grid-cols-3 gap-6 h-full min-h-0">
              {/* Left - Payment History */}
              <div className="h-[85%] min-h-0 flex flex-col">
                <PaymentHistorySidebar apiUrl={apiUrl} walletId={effectiveWalletId} />
              </div>

              {/* Center - Query Agent (Chat Interface) */}
              <div className="h-[85%] min-h-0 flex flex-col">
                <QueryAgent apiUrl={apiUrl} walletId={effectiveWalletId} />
              </div>

              {/* Right - Contacts */}
              <div className="h-[85%] min-h-0 flex flex-col">
                <ContactsCenter apiUrl={apiUrl} walletId={effectiveWalletId} />
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-center px-6">
              <p className="text-gray-600">
                Set up your wallet to get started with ArcFlux.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

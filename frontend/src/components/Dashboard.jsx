/**
 * ============================================
 * DASHBOARD COMPONENT
 * ============================================
 * 
 * The main overview page showing:
 * - Wallet balance
 * - Active payments
 * - Recent transactions
 * - Quick stats
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function Dashboard({ apiUrl, walletId }) {
  // ============================================
  // STATE: Data that changes over time
  // ============================================
  const [balance, setBalance] = useState('0.00');
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ============================================
  // EFFECT: Run code when component loads
  // ============================================
  // useEffect runs after the component renders
  // Empty [] means it only runs once when page loads
  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    
    // Cleanup: stop interval when component unmounts
    return () => clearInterval(interval);
  }, [apiUrl, walletId]);

  /**
   * Load all dashboard data from API
   */
  async function loadDashboardData() {
    if (!walletId) {
      setError('No wallet ID configured. Please set up your wallet first.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      // Fetch balance and payments in parallel
      // Promise.all waits for both to complete
      const [balanceData, paymentsData] = await Promise.all([
        fetchBalance(),
        fetchPayments(),
      ]);

      setBalance(balanceData);
      setPayments(paymentsData);
      setError(null);
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  /**
   * Fetch wallet balance from API
   */
  async function fetchBalance() {
    const response = await fetch(`${apiUrl}/api/balance?walletId=${walletId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch balance');
    }

    const data = await response.json();
    return data.balance;
  }

  /**
   * Fetch active payments from API
   */
  async function fetchPayments() {
    const response = await fetch(`${apiUrl}/api/payments?walletId=${walletId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch payments');
    }

    const data = await response.json();
    return data.payments || [];
  }

  /**
   * Format interval for display
   */
  function formatInterval(intervalMs) {
    const seconds = intervalMs / 1000;
    const minutes = seconds / 60;
    const hours = minutes / 60;
    const days = hours / 24;

    if (days >= 1) return `${Math.round(days)} day(s)`;
    if (hours >= 1) return `${Math.round(hours)} hour(s)`;
    if (minutes >= 1) return `${Math.round(minutes)} minute(s)`;
    return `${Math.round(seconds)} second(s)`;
  }

  /**
   * Format timestamp to readable date
   */
  function formatDate(timestamp) {
    return new Date(timestamp).toLocaleString();
  }

  /**
   * Calculate time until next payment
   */
  function timeUntilNext(nextExecutionTime) {
    const now = Date.now();
    const diff = nextExecutionTime - now;

    if (diff < 0) return 'Due now';

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `in ${days} day(s)`;
    if (hours > 0) return `in ${hours} hour(s)`;
    if (minutes > 0) return `in ${minutes} minute(s)`;
    return 'in less than a minute';
  }

  // ============================================
  // RENDER: What shows on screen
  // ============================================

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error</h3>
        <p className="text-red-600">{error}</p>
        <p className="text-sm text-red-500 mt-2">
          Make sure you've set up your wallet and deployed the backend.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ============================================
          PAGE HEADER
          ============================================ */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Monitor your automated USDC payments on Arc blockchain
        </p>
      </div>

      {/* ============================================
          STATS CARDS
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Balance Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Wallet Balance</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {balance} <span className="text-lg text-gray-500">USDC</span>
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Active Payments Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Active Payments</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{payments.length}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        {/* Total Sent Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Sent</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {payments.reduce((sum, p) => sum + (p.total_sent || 0), 0).toFixed(2)}
                <span className="text-lg text-gray-500"> USDC</span>
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <svg className="w-8 h-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================
          ACTIVE PAYMENTS LIST
          ============================================ */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Active Payments</h2>
            <Link
              to="/create"
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Payment
            </Link>
          </div>
        </div>

        <div className="p-6">
          {payments.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No active payments</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first automated payment.
              </p>
              <div className="mt-6">
                <Link
                  to="/create"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-blue-700"
                >
                  Create Payment
                </Link>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {payments.map((payment) => (
                <div key={payment.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Active
                        </span>
                        <span className="text-sm text-gray-500">
                          Every {formatInterval(payment.interval_ms)}
                        </span>
                      </div>
                      <div className="mt-2">
                        <p className="text-lg font-semibold text-gray-900">
                          {payment.amount} USDC
                        </p>
                        <p className="text-sm text-gray-600">
                          To: {payment.recipient_address.slice(0, 10)}...{payment.recipient_address.slice(-8)}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Executed: {payment.execution_count}x</span>
                        <span>Total sent: {payment.total_sent} USDC</span>
                        <span className="text-primary">Next: {timeUntilNext(payment.next_execution_time)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;


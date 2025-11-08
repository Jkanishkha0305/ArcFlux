/**
 * ============================================
 * PAYMENT HISTORY COMPONENT
 * ============================================
 * 
 * Shows a complete log of all executed payments.
 * Each transaction is recorded on the blockchain!
 */

import React, { useState, useEffect } from 'react';

function PaymentHistory({ apiUrl, walletId }) {
  // ============================================
  // STATE
  // ============================================
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ============================================
  // LOAD HISTORY ON MOUNT
  // ============================================
  useEffect(() => {
    loadHistory();
  }, [apiUrl, walletId]);

  /**
   * Fetch payment history from API
   */
  async function loadHistory() {
    if (!walletId) {
      setError('No wallet ID configured');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      const response = await fetch(`${apiUrl}/api/history?walletId=${walletId}&limit=100`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }

      const data = await response.json();
      setHistory(data.history || []);
      setError(null);
    } catch (err) {
      console.error('Error loading history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  /**
   * Format date/time
   */
  function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  /**
   * Shorten address for display
   */
  function shortenAddress(address) {
    if (!address) return 'N/A';
    return `${address.slice(0, 8)}...${address.slice(-6)}`;
  }

  /**
   * Get status badge styling
   */
  function getStatusBadge(status) {
    const styles = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  }

  /**
   * View transaction on Arc explorer
   */
  function viewOnExplorer(txHash) {
    const explorerUrl = import.meta.env.VITE_EXPLORER_URL || 'https://testnet.arcscan.com';
    window.open(`${explorerUrl}/tx/${txHash}`, '_blank');
  }

  // ============================================
  // RENDER
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
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ============================================
          PAGE HEADER
          ============================================ */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Payment History</h1>
          <p className="mt-2 text-gray-600">
            Complete record of all executed payments
          </p>
        </div>
        <button
          onClick={loadHistory}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* ============================================
          STATS SUMMARY
          ============================================ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Transactions</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{history.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Successful</p>
          <p className="mt-1 text-2xl font-bold text-green-600">
            {history.filter(h => h.status === 'completed').length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Volume</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {history.reduce((sum, h) => sum + h.amount, 0).toFixed(2)} USDC
          </p>
        </div>
      </div>

      {/* ============================================
          HISTORY TABLE
          ============================================ */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {history.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No payment history</h3>
            <p className="mt-1 text-sm text-gray-500">
              Payments will appear here once they execute.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date & Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    To
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transaction
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {history.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDateTime(item.executed_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {item.amount} USDC
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600 font-mono">
                        {shortenAddress(item.to_address)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(item.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {item.transaction_hash ? (
                        <button
                          onClick={() => viewOnExplorer(item.transaction_hash)}
                          className="text-primary hover:text-blue-700 font-medium"
                        >
                          View on Explorer →
                        </button>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ============================================
          INFO BOX
          ============================================ */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-800">
              Blockchain Transparency
            </h4>
            <p className="mt-1 text-sm text-blue-700">
              Every payment is recorded on the Arc blockchain. Click "View on Explorer" to see the transaction details, including block number, gas fees, and confirmation status.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PaymentHistory;


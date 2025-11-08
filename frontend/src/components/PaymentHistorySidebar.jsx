import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function PaymentHistorySidebar({ apiUrl, walletId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
    const interval = setInterval(loadHistory, 30000);
    return () => clearInterval(interval);
  }, [walletId]);

  async function loadHistory() {
    if (!walletId) {
      setLoading(false);
      return;
    }
    try {
      const response = await fetch(`${apiUrl}/api/history?walletId=${walletId}&limit=10`);
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setHistory(data.history || []);
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setLoading(false);
    }
  }

  function formatDate(timestamp) {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function shortenAddress(address) {
    if (!address) return 'N/A';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  }

  return (
    <div className="bg-white/90 backdrop-blur-lg rounded-2xl shadow-xl border border-gray-200/50 h-full flex flex-col max-h-full">
      <div className="px-4 py-3 border-b border-gray-200 flex-shrink-0">
        <h3 className="text-lg font-bold text-gray-900 flex items-center">
          <svg className="w-6 h-6 mr-3 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Recent History
        </h3>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>No transactions yet</p>
          </div>
        ) : (
          history.map((item) => (
            <div
              key={item.id || item.transaction_hash}
              className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer border border-gray-200/50"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1.5">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                      item.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : item.status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {item.status || 'pending'}
                    </span>
                    <span className="text-xs text-gray-500">{formatDate(item.executed_at)}</span>
                  </div>
                  <p className="text-base font-bold text-gray-900">{item.amount} USDC</p>
                  <p className="text-xs text-gray-600 font-mono">{shortenAddress(item.to_address)}</p>
                </div>
                {item.transaction_hash && (
                  <button
                    onClick={() => window.open(`https://testnet.arcscan.com/tx/${item.transaction_hash}`, '_blank')}
                    className="text-blue-600 hover:text-blue-800"
                    title="View on Explorer"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
      <div className="px-4 py-3 border-t border-gray-200 flex-shrink-0">
        <Link
          to="/history"
          className="text-sm text-blue-600 hover:text-blue-800 font-semibold flex items-center justify-center"
        >
          View All History →
        </Link>
      </div>
    </div>
  );
}

export default PaymentHistorySidebar;

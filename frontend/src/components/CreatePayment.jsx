/**
 * ============================================
 * CREATE PAYMENT COMPONENT
 * ============================================
 * 
 * This is where the AI magic happens!
 * 
 * User types: "Pay 50 USDC to Alice every week"
 * AI parses it → shows confirmation → creates payment
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import VoiceInput from './VoiceInput';

function CreatePayment({ apiUrl, walletId }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // ============================================
  // STATE MANAGEMENT
  // ============================================
  const [userInput, setUserInput] = useState('');
  const [parsedIntent, setParsedIntent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [selectedStockCommand, setSelectedStockCommand] = useState(null); // Store command with selected stock

  // Check if contact was passed from URL
  useEffect(() => {
    const contactAddress = searchParams.get('contact');
    const contactName = searchParams.get('name');
    if (contactAddress && !userInput) {
      // Pre-fill with contact info
      setUserInput(`Pay 10 USDC to ${contactName || contactAddress}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  /**
   * ============================================
   * STEP 1: PARSE USER INPUT WITH AI AGENT
   * ============================================
   *
   * Send natural language to payment agent.
   * Agent resolves contact names to addresses.
   */
  async function handleParseIntent(e) {
    e.preventDefault();

    if (!userInput.trim()) {
      setError('Please enter a payment command');
      return;
    }

    if (!walletId) {
      setError('Wallet ID is missing. Please set up your wallet first in Profile Settings.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/api/agent/pay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          walletId: walletId,
          command: userInput,
          execute: false  // Just parse, don't execute yet
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to parse payment command');
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || data.detail || 'Unknown error');
      }

      // Check if this is a stock purchase
      const plan = data.plan;
      
      if (plan.action === 'buy_stock') {
        // Handle stock purchase
        if (plan.needsSelection && plan.recommendations) {
          // Show stock recommendations
          setParsedIntent({
            type: 'stock_purchase',
            recommendations: plan.recommendations,
            prompt: plan.prompt,
            needsSelection: true
          });
        } else if (plan.stock) {
          // Stock selected, show confirmation
          // Store the command for execution (it should already have the stock symbol)
          setSelectedStockCommand(userInput);
          setParsedIntent({
            type: 'stock_purchase',
            stock: plan.stock,
            amount: plan.amount,
            riskAssessment: plan.riskAssessment,
            needsSelection: false
          });
        }
      } else {
        // Regular payment
        const contact = plan.contact;
        setParsedIntent({
          type: 'one-time',
          amount: plan.amount,
          recipient: contact ? contact.address : plan.contactAddress,
          recipientName: contact ? contact.name : plan.contactName,
          interval: 'once'
        });
      }
      setError(null);
    } catch (err) {
      console.error('Parse error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  /**
   * ============================================
   * STEP 2: CREATE SCHEDULED PAYMENT
   * ============================================
   * 
   * User confirms → create payment in database
   * → starts automatic execution
   */
  async function handleCreatePayment() {
    if (!parsedIntent) return;
    
    // Check if walletId is available
    if (!walletId) {
      setError('Wallet ID is missing. Please set up your wallet first in Profile Settings.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Determine interval - handle "one-time" payments
      let interval = parsedIntent.interval;
      if (parsedIntent.type === 'one-time' || !interval || interval === 'none') {
        interval = 'once';
      }
      
      console.log('Creating payment with:', {
        walletId,
        recipient: parsedIntent.recipient,
        amount: parsedIntent.amount,
        interval
      });

      const response = await fetch(`${apiUrl}/api/create-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          walletId: walletId,
          recipient: parsedIntent.recipient,
          amount: parsedIntent.amount,
          interval: interval,
        }),
      });

      // Parse response
      let data;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Non-JSON response - read as text
        const text = await response.text();
        console.error('Non-JSON response:', text, response.status);
        throw new Error(text || `Server error: ${response.status} ${response.statusText}`);
      }
      
      if (!response.ok) {
        // Try to get error detail from response
        const errorMsg = data.detail || data.error || data.message || `Failed to create payment (${response.status})`;
        console.error('Payment creation error:', errorMsg, data);
        throw new Error(errorMsg);
      }
      
      if (!data.success) {
        throw new Error(data.error || data.detail || 'Unknown error');
      }

      // Success!
      setSuccess(true);
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/');
      }, 2000);

    } catch (err) {
      console.error('Create error:', err);
      // Show the actual error message
      const errorMessage = err.message || 'Failed to create payment. Please try again.';
      setError(errorMessage);
      
      // If it's a wallet error, suggest setting up wallet
      if (errorMessage.toLowerCase().includes('wallet') || errorMessage.toLowerCase().includes('api key')) {
        setTimeout(() => {
          if (window.confirm('Would you like to set up your wallet now?')) {
            navigate('/profile');
          }
        }, 1000);
      }
    } finally {
      setLoading(false);
    }
  }

  /**
   * Handle stock selection
   */
  async function handleSelectStock(symbol) {
    if (!walletId) {
      setError('Wallet ID is missing. Please set up your wallet first in Profile Settings.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Re-submit command with selected stock
      const response = await fetch(`${apiUrl}/api/agent/pay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          walletId: walletId,
          command: `${userInput} ${symbol}`,  // Append selected symbol
          execute: false
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to select stock');
      }

      const data = await response.json();
      const plan = data.plan;

      if (plan.stock) {
        // Store the command with the selected stock for execution
        setSelectedStockCommand(`${userInput} ${symbol}`);
        setParsedIntent({
          type: 'stock_purchase',
          stock: plan.stock,
          amount: plan.amount,
          riskAssessment: plan.riskAssessment,
          needsSelection: false
        });
      }
    } catch (err) {
      console.error('Stock selection error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  /**
   * Start over with new input
   */
  function handleReset() {
    setUserInput('');
    setParsedIntent(null);
    setError(null);
    setSuccess(false);
    setSelectedStockCommand(null);
  }

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="max-w-3xl mx-auto">
      {/* ============================================
          PAGE HEADER
          ============================================ */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create Payment</h1>
        <p className="mt-2 text-gray-600">
          Use natural language to schedule automatic USDC payments
        </p>
      </div>

      {/* ============================================
          SUCCESS MESSAGE
          ============================================ */}
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                Payment scheduled successfully!
              </h3>
              <p className="mt-1 text-sm text-green-700">
                Redirecting to dashboard...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ============================================
          MAIN FORM
          ============================================ */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        
        {!parsedIntent ? (
          // ============================================
          // STEP 1: INPUT FORM
          // ============================================
          <>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Describe your payment
                <span className="ml-2 text-xs text-gray-500">(or use voice input)</span>
              </label>
              <div className="relative">
                <textarea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  className="w-full px-4 py-3 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                  rows="4"
                  placeholder='Example: "Pay 50 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8 every week"'
                />
                <div className="absolute bottom-3 right-3">
                  <VoiceInput
                    onTranscript={(transcript) => setUserInput(transcript)}
                    disabled={loading}
                    apiUrl={apiUrl}
                  />
                </div>
              </div>
            </div>

            {/* Example Commands */}
            <div className="mb-6 bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                💡 Example Commands
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• "Send 100 USDC to Alice every month"</li>
                <li>• "Pay 25 USDC to 0x123...abc every 5 minutes"</li>
                <li>• "Transfer 50 USDC to Bob weekly"</li>
                <li>• "Buy stock in banking sector for 100 USDC"</li>
                <li>• "Purchase BNKX stock for 50 USDC"</li>
              </ul>
            </div>

            <button
              onClick={handleParseIntent}
              disabled={loading || !userInput.trim()}
              className="w-full px-6 py-3 bg-primary text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Parsing...' : '✨ Parse with AI'}
            </button>
          </>
        ) : parsedIntent.type === 'stock_purchase' && parsedIntent.needsSelection ? (
          // ============================================
          // STOCK SELECTION
          // ============================================
          <>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Select a Stock
            </h3>
            <p className="text-sm text-gray-600 mb-4">{parsedIntent.prompt}</p>
            
            <div className="space-y-3 mb-6">
              {parsedIntent.recommendations && parsedIntent.recommendations.map((stock, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectStock(stock.symbol)}
                  disabled={loading}
                  className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all disabled:opacity-50"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-semibold text-gray-900">{stock.symbol}</div>
                      <div className="text-sm text-gray-600">{stock.name}</div>
                      <div className="text-xs text-gray-500 mt-1">{stock.sector}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">{stock.price} USDC</div>
                      <div className="text-xs text-gray-500">Score: {stock.valuationScore?.toFixed(2)}</div>
                    </div>
                  </div>
                  {stock.memo && (
                    <div className="text-xs text-gray-600 mt-2">{stock.memo}</div>
                  )}
                </button>
              ))}
            </div>

            <button
              onClick={handleReset}
              disabled={loading}
              className="w-full px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              ← Back
            </button>
          </>
        ) : parsedIntent.type === 'stock_purchase' ? (
          // ============================================
          // STOCK PURCHASE CONFIRMATION
          // ============================================
          <>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Review Stock Purchase
            </h3>

            <div className="space-y-4 mb-6">
              <div className="flex justify-between py-3 border-b border-gray-200">
                <span className="text-gray-600">Stock</span>
                <div className="text-right">
                  <div className="font-medium text-gray-900">{parsedIntent.stock.symbol}</div>
                  <div className="text-sm text-gray-600">{parsedIntent.stock.name}</div>
                </div>
              </div>

              <div className="flex justify-between py-3 border-b border-gray-200">
                <span className="text-gray-600">Amount</span>
                <span className="font-medium text-gray-900">
                  {parsedIntent.amount} USDC
                </span>
              </div>

              {parsedIntent.riskAssessment && (
                <div className="flex justify-between py-3 border-b border-gray-200">
                  <span className="text-gray-600">Risk Level</span>
                  <span className={`font-medium ${
                    parsedIntent.riskAssessment.riskLevel === 'low' ? 'text-green-600' :
                    parsedIntent.riskAssessment.riskLevel === 'medium' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {parsedIntent.riskAssessment.riskLevel.toUpperCase()}
                  </span>
                </div>
              )}
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-yellow-800">
                    Important
                  </h4>
                  <p className="mt-1 text-sm text-yellow-700">
                    This stock purchase will execute immediately. Make sure your wallet has sufficient balance.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleReset}
                disabled={loading}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={async () => {
                  // Execute stock purchase
                  setLoading(true);
                  setError(null);
                  try {
                    // Use the command with selected stock if available, otherwise use original input
                    const commandToExecute = selectedStockCommand || userInput;
                    const response = await fetch(`${apiUrl}/api/agent/pay`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        walletId: walletId,
                        command: commandToExecute,
                        execute: true
                      }),
                    });

                    if (!response.ok) {
                      const data = await response.json();
                      throw new Error(data.detail || 'Failed to execute stock purchase');
                    }

                    const data = await response.json();
                    if (!data.success) {
                      throw new Error(data.error || data.detail || 'Unknown error');
                    }

                    setSuccess(true);
                    setTimeout(() => {
                      navigate('/');
                    }, 2000);
                  } catch (err) {
                    console.error('Stock purchase error:', err);
                    setError(err.message);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Purchasing...' : '✓ Confirm & Purchase'}
              </button>
            </div>
          </>
        ) : (
          // ============================================
          // STEP 2: CONFIRMATION
          // ============================================
          <>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Review Payment Details
            </h3>

            <div className="space-y-4 mb-6">
              {/* Payment Type */}
              <div className="flex justify-between py-3 border-b border-gray-200">
                <span className="text-gray-600">Type</span>
                <span className="font-medium text-gray-900 capitalize">
                  {parsedIntent.type}
                </span>
              </div>

              {/* Amount */}
              <div className="flex justify-between py-3 border-b border-gray-200">
                <span className="text-gray-600">Amount</span>
                <span className="font-medium text-gray-900">
                  {parsedIntent.amount} USDC
                </span>
              </div>

              {/* Recipient */}
              <div className="flex justify-between py-3 border-b border-gray-200">
                <span className="text-gray-600">Recipient</span>
                <div className="text-right">
                  {parsedIntent.recipientName && (
                    <div className="font-medium text-gray-900">
                      {parsedIntent.recipientName}
                    </div>
                  )}
                  <span className="font-medium text-gray-900 text-sm">
                    {parsedIntent.recipient}
                  </span>
                </div>
              </div>

              {/* Interval */}
              {parsedIntent.type === 'recurring' && (
                <div className="flex justify-between py-3 border-b border-gray-200">
                  <span className="text-gray-600">Frequency</span>
                  <span className="font-medium text-gray-900">
                    Every {parsedIntent.interval}
                  </span>
                </div>
              )}
            </div>

            {/* Important Notice */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-yellow-800">
                    Important
                  </h4>
                  <p className="mt-1 text-sm text-yellow-700">
                    This payment will execute automatically. Make sure your wallet has sufficient balance.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={handleReset}
                disabled={loading}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={handleCreatePayment}
                disabled={loading}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Creating...' : '✓ Confirm & Create'}
              </button>
            </div>
          </>
        )}

        {/* ============================================
            ERROR MESSAGE
            ============================================ */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ============================================
          INFO SECTION
          ============================================ */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">
          How it works
        </h4>
        <ol className="text-sm text-blue-800 space-y-2">
          <li>1. Describe your payment in natural language</li>
          <li>2. AI parses and structures your command</li>
          <li>3. Review and confirm the details</li>
          <li>4. Payment executes automatically on schedule</li>
          <li>5. Track execution on dashboard</li>
        </ol>
      </div>
    </div>
  );
}

export default CreatePayment;


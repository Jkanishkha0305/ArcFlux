import React, { useState, useRef, useEffect } from 'react';

// Dashboard Display Component
function DashboardDisplay({ dashboard }) {
  const summary = dashboard.summary || {};
  const charts = dashboard.charts || {};
  const insights = dashboard.insights || [];

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-xs text-gray-600">Balance</div>
          <div className="text-lg font-bold text-blue-900">{summary.balance?.toFixed(2) || 0} USDC</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="text-xs text-gray-600">Total Spent</div>
          <div className="text-lg font-bold text-green-900">{summary.totalSpent?.toFixed(2) || 0} USDC</div>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg">
          <div className="text-xs text-gray-600">Transactions</div>
          <div className="text-lg font-bold text-purple-900">{summary.transactionCount || 0}</div>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg">
          <div className="text-xs text-gray-600">Recipients</div>
          <div className="text-lg font-bold text-orange-900">{summary.uniqueRecipients || 0}</div>
        </div>
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="text-xs font-semibold text-yellow-900 mb-2">💡 Insights</div>
          <ul className="text-xs text-yellow-800 space-y-1">
            {insights.map((insight, i) => (
              <li key={i}>• {insight}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Charts */}
      {charts.recipientBreakdown && charts.recipientBreakdown.data && charts.recipientBreakdown.data.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-900 mb-2">{charts.recipientBreakdown.title}</div>
          <div className="space-y-2">
            {charts.recipientBreakdown.data.map((item, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-xs text-gray-600 truncate flex-1">{item.recipient}</span>
                <span className="text-xs font-semibold text-gray-900 ml-2">{item.amount.toFixed(2)} USDC</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Spending Over Time */}
      {charts.spendingOverTime && charts.spendingOverTime.data && charts.spendingOverTime.data.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-900 mb-2">{charts.spendingOverTime.title}</div>
          <div className="space-y-1">
            {charts.spendingOverTime.data.slice(0, 5).map((item, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="text-gray-600">{item.date ? new Date(item.date).toLocaleDateString() : 'N/A'}</span>
                <span className="font-semibold text-gray-900">{item.amount.toFixed(2)} USDC</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function QueryAgent({ apiUrl, walletId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [lastStockRecommendations, setLastStockRecommendations] = useState(null);
  const [lastStockCommand, setLastStockCommand] = useState(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function handleSendMessage(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', text: input };
    setMessages([...messages, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      // Check if this is a payment/stock purchase command
      const paymentKeywords = ['buy', 'purchase', 'pay', 'send', 'transfer', 'stock', 'stocks', 'equity'];
      const confirmationKeywords = ['yes', 'confirm', 'execute', 'proceed', 'go ahead'];
      const isPaymentCommand = paymentKeywords.some(keyword => currentInput.toLowerCase().includes(keyword));
      const isConfirmation = confirmationKeywords.some(keyword => currentInput.toLowerCase().includes(keyword));
      
      // Check if we have stored stock recommendations (means user is in stock purchase flow)
      const hasStockContext = lastStockRecommendations && lastStockRecommendations.length > 0;
      
      // Route to payment agent if:
      // 1. It's a payment/stock command, OR
      // 2. It's a confirmation and we have stock context
      if (isPaymentCommand || (isConfirmation && hasStockContext)) {
        // Check if user is confirming a purchase (yes/confirm) but no stock symbol mentioned
        const isConfirmationWithoutSymbol = isConfirmation && 
                               !currentInput.match(/\b[A-Z]{3,5}\b/); // No stock symbol in message
        
        // If confirming and we have last stock command, append the first recommended stock
        let commandToSend = currentInput;
        let shouldExecute = false;
        
        // Check if we have a stored command with selected stock (from previous stock selection)
        const hasSelectedStockCommand = lastStockCommand && lastStockCommand.match(/\b[A-Z]{3,5}\b/);
        
        if (isConfirmationWithoutSymbol) {
          if (hasSelectedStockCommand) {
            // Stock was already selected in previous step, execute directly
            commandToSend = lastStockCommand;
            shouldExecute = true;
          } else if (lastStockRecommendations && lastStockRecommendations.length > 0 && lastStockCommand) {
            // User is confirming but no stock selected yet, use the first recommended stock and execute
            const firstStock = lastStockRecommendations[0];
            commandToSend = `${lastStockCommand} ${firstStock.symbol}`;
            shouldExecute = true; // Execute directly - backend will handle stock selection and execution
          } else {
            // No context, can't proceed
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              text: 'I need more information. Please specify which stock you want to buy, or start a new stock purchase request.'
            }]);
            setLoading(false);
            return;
          }
        } else {
          shouldExecute = currentInput.toLowerCase().includes('yes') || 
                         currentInput.toLowerCase().includes('confirm') || 
                         currentInput.toLowerCase().includes('execute');
        }
        
        // Route to payment agent
        const response = await fetch(`${apiUrl}/api/agent/pay`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            walletId: walletId,
            command: commandToSend,
            execute: shouldExecute
          }),
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to process payment command');
        }
        
        const data = await response.json();
        
        if (data.success) {
          if (data.plan && data.plan.recommendations) {
            // Stock recommendations - store for later use
            setLastStockRecommendations(data.plan.recommendations);
            setLastStockCommand(currentInput);
            
            const recommendationsText = data.plan.recommendations.map((stock, idx) => 
              `${idx + 1}. ${stock.symbol} (${stock.name}) - ${stock.price} USDC - ${stock.sector}`
            ).join('\n');
            
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              text: `${data.message || data.plan.prompt || 'Here are stock recommendations:'}\n\n${recommendationsText}\n\nTo purchase, reply with the stock symbol (e.g., "buy BNKX") or "buy [symbol]".`
            }]);
          } else if (data.transaction) {
            // Transaction executed - clear stored recommendations
            setLastStockRecommendations(null);
            setLastStockCommand(null);
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              text: data.message || `Transaction executed successfully! Transaction ID: ${data.transaction.transactionId || 'N/A'}`
            }]);
          } else if (data.plan && data.plan.stock) {
            // Stock selected and ready for confirmation - store for execution
            setLastStockRecommendations(null); // Clear recommendations since stock is selected
            const stock = data.plan.stock;
            const risk = data.plan.riskAssessment;
            // Store the command with selected stock for execution
            setLastStockCommand(`${lastStockCommand || currentInput} ${stock.symbol}`);
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              text: `${data.message || `Stock purchase plan for ${stock.symbol} (${stock.name})`}\n\nAmount: ${data.plan.amount} USDC\nRisk Level: ${risk?.riskLevel || 'N/A'}\n\nReply "yes" or "confirm" to execute the purchase.`
            }]);
          } else {
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              text: data.message || 'Command processed successfully.'
            }]);
          }
        } else {
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            text: data.error || data.detail || 'Failed to process command.'
          }]);
        }
      } else {
        // Regular query - use query agent
        const response = await fetch(`${apiUrl}/api/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: currentInput, walletId })
        });
        
        if (!response.ok) {
          throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        // Check if dashboard data is present
        if (data.dashboard) {
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            text: data.answer || 'Here\'s your financial dashboard.',
            dashboard: data.dashboard
          }]);
        } else {
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            text: data.answer || data.success ? (data.answer || 'Sorry, I could not process your request.') : 'Error: Could not process your request.'
          }]);
        }
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: `Error: ${err.message || 'Could not connect to the AI agent. Please make sure the backend is running.'}` 
      }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white/90 backdrop-blur-lg rounded-2xl shadow-xl border border-gray-200/50 h-full flex flex-col max-h-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-5 py-3 rounded-t-2xl flex items-center flex-shrink-0">
        <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mr-3">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <h3 className="font-bold text-lg">AI Assistant</h3>
          <p className="text-sm text-white/80">Ask me about your transactions or balance</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50 min-h-0">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-6">
            <p className="mb-1.5 text-base">👋 Hi! I'm your AI assistant.</p>
            <p className="text-xs mb-3">Ask me about your balance, transactions, or payments!</p>
            <div className="mt-3 text-xs text-gray-400 space-y-0.5">
              <p className="font-semibold">Try asking:</p>
              <p>"What's my balance?"</p>
              <p>"Show me a dashboard"</p>
              <p>"Visualize my spending"</p>
              <p>"How many active payments do I have?"</p>
            </div>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[75%] rounded-xl px-3 py-1.5 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'bg-white text-gray-900 border border-gray-200'
              }`}
            >
              <p className="text-xs whitespace-pre-wrap">{msg.text}</p>
            </div>
            {/* Dashboard Display */}
            {msg.dashboard && (
              <div className="mt-2 max-w-[90%] bg-white border border-gray-200 rounded-lg p-4">
                <DashboardDisplay dashboard={msg.dashboard} />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSendMessage} className="p-3 border-t border-gray-200 bg-white rounded-b-2xl flex-shrink-0">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your balance or transactions..."
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}

export default QueryAgent;

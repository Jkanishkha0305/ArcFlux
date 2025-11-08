/**
 * ============================================
 * MAIN APP COMPONENT
 * ============================================
 * 
 * This is the root component of ArcPay frontend.
 * It sets up routing and manages global state.
 * 
 * React Docs: https://react.dev/
 * React Router: https://reactrouter.com/
 */

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import CreatePayment from './components/CreatePayment';
import PaymentHistory from './components/PaymentHistory';

/**
 * Main App Component
 * 
 * Think of this as the "container" that holds everything.
 * It manages:
 * - Navigation between pages
 * - Global state (wallet ID, API URL)
 * - Layout (header, sidebar, content area)
 */
function App() {
  // ============================================
  // STATE MANAGEMENT
  // ============================================
  // useState is React's way of storing data that can change
  // When state changes, React re-renders the component
  
  // API URL for backend
  const [apiUrl] = useState(
    import.meta.env.VITE_API_URL || 'http://localhost:8787'
  );
  
  // User's wallet ID (from Circle)
  const [walletId] = useState(
    import.meta.env.VITE_WALLET_ID || ''
  );

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* ============================================
            HEADER / NAVIGATION BAR
            ============================================ */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              {/* Logo */}
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-primary">
                  🚀 ArcPay
                </h1>
                <span className="ml-3 text-sm text-gray-500">
                  AI Payment Automation
                </span>
              </div>

              {/* Navigation Links */}
              <div className="flex items-center space-x-4">
                <NavLink to="/">Dashboard</NavLink>
                <NavLink to="/create">Create Payment</NavLink>
                <NavLink to="/history">History</NavLink>
              </div>
            </div>
          </div>
        </nav>

        {/* ============================================
            MAIN CONTENT AREA
            ============================================ */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* React Router handles switching between pages */}
          <Routes>
            <Route 
              path="/" 
              element={<Dashboard apiUrl={apiUrl} walletId={walletId} />} 
            />
            <Route 
              path="/create" 
              element={<CreatePayment apiUrl={apiUrl} walletId={walletId} />} 
            />
            <Route 
              path="/history" 
              element={<PaymentHistory apiUrl={apiUrl} walletId={walletId} />} 
            />
          </Routes>
        </main>

        {/* ============================================
            FOOTER
            ============================================ */}
        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-gray-500">
              Built with Arc, Circle, and Cloudflare Workers AI
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

/**
 * ============================================
 * NAVIGATION LINK COMPONENT
 * ============================================
 * 
 * Custom navigation link with active state styling.
 * Changes color when you're on that page.
 */
function NavLink({ to, children }) {
  return (
    <Link
      to={to}
      className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-primary hover:bg-gray-50 transition-colors"
    >
      {children}
    </Link>
  );
}

export default App;

/**
 * ============================================
 * HOW REACT WORKS (SIMPLIFIED)
 * ============================================
 * 
 * 1. Components are functions that return HTML-like code (JSX)
 * 2. Props = data passed from parent to child component
 * 3. State = data that can change and triggers re-renders
 * 4. When state changes, React automatically updates the UI
 * 
 * Example:
 * const [count, setCount] = useState(0);
 * // count = current value (0)
 * // setCount = function to update it
 * 
 * <button onClick={() => setCount(count + 1)}>
 *   Clicked {count} times
 * </button>
 * 
 * When button clicked → setCount called → count increases → UI updates
 */


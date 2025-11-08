/**
 * ============================================
 * MAIN APP COMPONENT
 * ============================================
 * 
 * This is the root component of ArcFlux frontend.
 * It sets up routing and manages global state.
 * 
 * React Docs: https://react.dev/
 * React Router: https://reactrouter.com/
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import CreatePayment from './components/CreatePayment';
import PaymentHistory from './components/PaymentHistory';
import Login from './components/Login';
import Signup from './components/Signup';
import UserProfile from './components/UserProfile';

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
    import.meta.env.VITE_API_URL || 'http://localhost:8000'
  );
  
  // User's wallet ID (from environment - fallback only, should use user.wallet_id)
  const [walletId] = useState(
    import.meta.env.VITE_WALLET_ID || ''
  );
  
  // Note: After login, wallet_id should come from user object, not env var

  // User authentication state
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Error parsing user data:', err);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
      }
    } else {
      // Require authentication - redirect to login
      setIsAuthenticated(false);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  const handleWalletGenerated = (updatedUser) => {
    // Update user state with wallet information
    setUser(updatedUser);
    // Update localStorage
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={isAuthenticated && user ? <Navigate to="/" /> : <Login apiUrl={apiUrl} onLogin={handleLogin} />} 
        />
        <Route 
          path="/signup" 
          element={isAuthenticated && user ? <Navigate to="/" /> : <Signup apiUrl={apiUrl} onLogin={handleLogin} />} 
        />

        {/* Protected Routes */}
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <div className="min-h-screen bg-gray-50">
                {/* Header / Navigation Bar */}
                <nav className="bg-white shadow-sm border-b border-gray-200">
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                      {/* Logo */}
                      <div className="flex items-center">
                        <img 
                          src="/logo.png" 
                          alt="ArcFlux Logo" 
                          className="h-10 w-auto mr-3"
                        />
                        <div className="flex flex-col">
                          <h1 className="text-2xl font-bold text-primary">
                            ArcFlux
                          </h1>
                          <span className="text-xs text-gray-500">
                            AI Payment Automation
                          </span>
                        </div>
                      </div>

                      {/* Navigation Links */}
                      <div className="flex items-center space-x-4">
                        <NavLink to="/">Dashboard</NavLink>
                        <NavLink to="/create">Create Payment</NavLink>
                        <NavLink to="/history">History</NavLink>
                        <NavLink to="/profile">Profile</NavLink>
                        {user && user.email && (
                          <button
                            onClick={handleLogout}
                            className="px-3 py-2 text-sm text-gray-700 hover:text-red-600 transition-colors"
                          >
                            Logout
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </nav>

                {/* Main Content Area */}
                <Routes>
                  <Route 
                    path="/" 
                    element={<Dashboard apiUrl={apiUrl} walletId={walletId} user={user} onWalletGenerated={handleWalletGenerated} />} 
                  />
                  <Route 
                    path="/create" 
                    element={<CreatePayment apiUrl={apiUrl} walletId={user?.wallet_id || walletId} />} 
                  />
                  <Route 
                    path="/history" 
                    element={<PaymentHistory apiUrl={apiUrl} walletId={user?.wallet_id || walletId} />} 
                  />
                  <Route 
                    path="/profile" 
                    element={<UserProfile apiUrl={apiUrl} user={user} onWalletGenerated={handleWalletGenerated} />} 
                  />
                </Routes>

                {/* Footer */}
                <footer className="bg-white border-t border-gray-200 mt-12">
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <p className="text-center text-sm text-gray-500">
                      Built with Arc, Circle, ElevenLabs, MLAI API and Cloudflare agents.
                    </p>
                  </div>
                </footer>
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
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


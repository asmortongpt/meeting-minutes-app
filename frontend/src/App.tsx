import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import EnhancedMeetingForm from './pages/EnhancedMeetingForm'
import EnhancedMeetingList from './pages/EnhancedMeetingList'
import Logo from './components/Logo'
import StealthModeOverlay from './components/StealthModeOverlay'
import { StealthProvider, useStealthMode } from './contexts/StealthContext'
import { FileText, List, Plus, Calendar, TrendingUp, Settings, Menu, X } from 'lucide-react'

function Navigation() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { stealthMode } = useStealthMode();

  const isActive = (path: string) => location.pathname === path;

  // Hide navigation in stealth mode
  if (stealthMode) {
    return null;
  }

  const navLinks = [
    { to: '/', icon: List, label: 'All Meetings' },
    { to: '/new', icon: Plus, label: 'New Meeting' },
  ];

  return (
    <nav className="bg-white/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center group">
              <Logo size="md" variant="full" />
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:ml-8 md:flex md:space-x-4">
              {navLinks.map(({ to, icon: Icon, label }) => (
                <Link
                  key={to}
                  to={to}
                  className={`
                    inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive(to)
                      ? 'bg-gradient-to-r from-purple-100 to-indigo-100 text-indigo-700 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {label}
                </Link>
              ))}
            </div>
          </div>

          {/* Right side actions */}
          <div className="flex items-center gap-3">
            {/* Quick Stats Badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200/50">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-xs font-medium text-indigo-700">Online</span>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-3 space-y-1">
            {navLinks.map(({ to, icon: Icon, label }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileMenuOpen(false)}
                className={`
                  flex items-center px-4 py-3 rounded-lg text-sm font-medium transition-all
                  ${isActive(to)
                    ? 'bg-gradient-to-r from-purple-100 to-indigo-100 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-100'
                  }
                `}
              >
                <Icon className="h-5 w-5 mr-3" />
                {label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}

function AppContent() {
  const { stealthMode } = useStealthMode();

  return (
    <div className={`min-h-screen ${stealthMode ? 'bg-white' : 'bg-gradient-to-br from-gray-50 via-purple-50/30 to-indigo-50/40'}`}>
      <Navigation />

      <main className={`${stealthMode ? 'pt-0' : 'max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8'}`}>
        <Routes>
          <Route path="/" element={<EnhancedMeetingList />} />
          <Route path="/new" element={<EnhancedMeetingForm />} />
          <Route path="/edit/:id" element={<EnhancedMeetingForm />} />
        </Routes>
      </main>

      {/* Footer - hide in stealth mode */}
      {!stealthMode && (
        <footer className="mt-auto border-t border-gray-200 bg-white/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-2">
                <Logo size="sm" variant="icon" />
                <span className="text-sm text-gray-600">
                  &copy; 2024 Meeting Minutes Pro. All rights reserved.
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <a href="#" className="hover:text-indigo-600 transition-colors">Privacy</a>
                <span>•</span>
                <a href="#" className="hover:text-indigo-600 transition-colors">Terms</a>
                <span>•</span>
                <a href="#" className="hover:text-indigo-600 transition-colors">Support</a>
              </div>
            </div>
          </div>
        </footer>
      )}

      {/* Stealth Mode Overlay - Always present */}
      <StealthModeOverlay />
    </div>
  );
}

function App() {
  return (
    <Router>
      <StealthProvider>
        <AppContent />
      </StealthProvider>
    </Router>
  )
}

export default App

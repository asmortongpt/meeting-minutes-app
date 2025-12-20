import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import EnhancedMeetingForm from './pages/EnhancedMeetingForm'
import EnhancedMeetingList from './pages/EnhancedMeetingList'
import { FileText, List, Sparkles } from 'lucide-react'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
        <nav className="bg-white shadow-lg border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                    <FileText className="h-6 w-6 text-white" />
                  </div>
                  <span className="ml-3 text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    Meeting Minutes Pro
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <Link
                    to="/"
                    className="border-transparent text-gray-600 hover:border-blue-500 hover:text-blue-600 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                  >
                    <List className="h-4 w-4 mr-2" />
                    All Meetings
                  </Link>
                  <Link
                    to="/new"
                    className="border-transparent text-gray-600 hover:border-blue-500 hover:text-blue-600 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    New Meeting
                  </Link>
                </div>
              </div>
              <div className="flex items-center">
                <div className="flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-full">
                  <Sparkles className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-medium text-blue-900">AI-Powered</span>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<EnhancedMeetingList />} />
            <Route path="/new" element={<EnhancedMeetingForm />} />
            <Route path="/edit/:id" element={<EnhancedMeetingForm />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

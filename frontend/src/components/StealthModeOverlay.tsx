import React, { useState, useEffect } from 'react';
import { useStealthMode } from '../contexts/StealthContext';
import { Eye, EyeOff, FileText, Settings } from 'lucide-react';

const StealthModeOverlay: React.FC = () => {
  const { bossKeyPressed, stealthMode, toggleStealthMode, disguisedTitle, setDisguisedTitle } = useStealthMode();
  const [showSettings, setShowSettings] = useState(false);
  const [tempTitle, setTempTitle] = useState(disguisedTitle);

  // Boss key creates a fake Google Docs screen
  if (bossKeyPressed) {
    return (
      <div className="fixed inset-0 z-[9999] bg-white">
        {/* Fake Google Docs Interface */}
        <div className="w-full h-full flex flex-col">
          {/* Fake Google Docs Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <svg className="w-10 h-10" viewBox="0 0 48 48">
                  <path fill="#1976D2" d="M41,10H25v28h16c0.553,0,1-0.447,1-1V11C42,10.447,41.553,10,41,10z"/>
                  <path fill="#FFF" d="M32 15H39V18H32zM32 25H39V28H32zM32 30H39V33H32zM32 20H39V23H32zM25 15H30V18H25zM25 25H30V28H25zM25 30H30V33H25zM25 20H30V23H25z"/>
                  <path fill="#1976D2" d="M27 42L6 38 6 10 27 6z"/>
                  <path fill="#FFF" d="M12 15H23V18H12zM12 25H23V28H12zM12 30H23V33H12zM12 20H23V23H12z"/>
                </svg>
                <div>
                  <div className="text-sm font-medium text-gray-900">Untitled document</div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>File</span>
                    <span>Edit</span>
                    <span>View</span>
                    <span>Insert</span>
                    <span>Format</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">
                Share
              </button>
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm">
                A
              </div>
            </div>
          </div>

          {/* Fake Document Content */}
          <div className="flex-1 bg-gray-100 p-8 overflow-auto">
            <div className="max-w-3xl mx-auto bg-white shadow-lg min-h-[11in] p-16">
              <div className="space-y-4 text-gray-800">
                <h1 className="text-2xl font-bold mb-4">Project Status Report</h1>
                <p className="text-gray-600 leading-relaxed">
                  This document outlines the current status of ongoing projects and initiatives.
                  The team has made significant progress on key deliverables this quarter.
                </p>
                <h2 className="text-xl font-semibold mt-6">Key Achievements</h2>
                <ul className="list-disc list-inside space-y-2 text-gray-600">
                  <li>Completed phase 1 of infrastructure upgrade</li>
                  <li>Delivered customer portal improvements</li>
                  <li>Reduced system response time by 40%</li>
                </ul>
                <h2 className="text-xl font-semibold mt-6">Next Steps</h2>
                <p className="text-gray-600 leading-relaxed">
                  The team will focus on implementing the remaining features and conducting
                  comprehensive testing before the scheduled release date.
                </p>
                <div className="mt-8 pt-4 border-t border-gray-200 text-xs text-gray-400 text-center">
                  Press Ctrl+Shift+H (or Cmd+Shift+H) to return to Meeting Minutes Pro
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Stealth mode provides minimal UI
  if (stealthMode) {
    return (
      <>
        {/* Stealth Mode Indicator - Minimal floating button */}
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="w-10 h-10 bg-gray-300 hover:bg-gray-400 rounded-full shadow-lg flex items-center justify-center text-gray-600 transition-all"
            title="Stealth Mode Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="fixed bottom-16 right-4 z-50 bg-white rounded-lg shadow-2xl p-4 w-80 border border-gray-200">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Privacy Settings</h3>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Stealth Mode</span>
                    <button
                      onClick={toggleStealthMode}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        stealthMode ? 'bg-indigo-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          stealthMode ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </label>
                  <p className="text-xs text-gray-500 mt-1">Minimal interface for privacy</p>
                </div>

                <div>
                  <label className="text-sm text-gray-700 block mb-1">Disguised Tab Title</label>
                  <input
                    type="text"
                    value={tempTitle}
                    onChange={(e) => setTempTitle(e.target.value)}
                    onBlur={() => setDisguisedTitle(tempTitle)}
                    className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="e.g., Google Docs - Untitled"
                  />
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <h4 className="text-xs font-semibold text-gray-700 mb-2">Keyboard Shortcuts</h4>
                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex justify-between">
                      <span>Boss Key (Hide):</span>
                      <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">Ctrl+Shift+H</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Toggle Stealth:</span>
                      <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">Ctrl+Shift+S</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Normal mode - show stealth mode toggle in corner
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={toggleStealthMode}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-lg hover:shadow-xl transition-all hover:border-indigo-400 group"
        title="Enable Stealth Mode"
      >
        <EyeOff className="w-4 h-4 text-gray-600 group-hover:text-indigo-600" />
        <span className="text-sm text-gray-700 group-hover:text-indigo-700 font-medium">
          Enable Stealth
        </span>
      </button>
    </div>
  );
};

export default StealthModeOverlay;

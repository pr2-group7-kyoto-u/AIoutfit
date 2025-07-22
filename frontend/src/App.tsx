import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import FrontPage from './pages/FrontPage';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import SuggestionPage from './pages/SuggestionPage'; 
import SettingsPage from './pages/SettingsPage';
import UploadPage from './pages/UploadPage';
import CheckPage from './pages/CheckPage';
import HistoryPage from './pages/HistoryPage';

import { AuthProvider } from './hooks/useAuth';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/FrontPage" element={<FrontPage />} />
            <Route path="/" element={<HomePage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/suggestion" element={<SuggestionPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/uploadclothing" element={<UploadPage />} />
            <Route path="/checkclothing" element={<CheckPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
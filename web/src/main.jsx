import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import App from './App.jsx';
import Home from './pages/Home.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Playground from './pages/Playground.jsx';
import Endpoints from './pages/Endpoints.jsx';
import Pricing from './pages/Pricing.jsx';
import Settings from './pages/Settings.jsx';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path='/' element={<App />}> 
        <Route index element={<Home />} />
        <Route path='dashboard' element={<Dashboard />} />
        <Route path='playground' element={<Playground />} />
        <Route path='endpoints' element={<Endpoints />} />
        <Route path='pricing' element={<Pricing />} />
        <Route path='settings' element={<Settings />} />
      </Route>
    </Routes>
  </BrowserRouter>
);

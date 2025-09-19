import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import "./styles.css";

// IMPORTANT: enable WTN auto-open & banner
import './wtnHook';
import WtnPrompt from './components/WtnPrompt';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
    {/* Renders globally so any page benefits */}
    <WtnPrompt />
  </React.StrictMode>,
);

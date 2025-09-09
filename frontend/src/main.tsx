// path: frontend/src/main.tsx
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import { ToastProvider } from './components/Toast'

// Optional: register a very small service worker so the shell works offline
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </React.StrictMode>
)

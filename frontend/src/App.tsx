import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { LiveMonitor } from './pages/LiveMonitor';
import { ModelPerformance } from './pages/ModelPerformance';
import { SystemMetrics } from './pages/SystemMetrics';

// Basic routing setup for demonstration purposes.
// TODO: Implement react-router-dom once integrated.
const App: React.FC = () => {
  const [currentPath] = useState(window.location.pathname);

  // Default to LiveMonitor
  let Content = LiveMonitor;
  if (currentPath === '/performance') Content = ModelPerformance;
  if (currentPath === '/metrics') Content = SystemMetrics;

  return (
    <AppLayout>
      <Content />
    </AppLayout>
  );
};

export default App;

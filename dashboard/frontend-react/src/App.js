import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tab,
  Tabs,
  AppBar,
  Toolbar,
  IconButton,
  Badge,
  Fab
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  BugReport,
  Psychology,
  Settings,
  Refresh,
  Notifications
} from '@mui/icons-material';
import { Toaster } from 'react-hot-toast';

import DashboardOverview from './components/DashboardOverview';
import TestCaseManager from './components/TestCaseManager';
import BugTracker from './components/BugTracker';
import AIInsights from './components/AIInsights';
import IntegrationSettings from './components/IntegrationSettings';
import { dashboardService } from './services/api';

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await dashboardService.getEnhancedSummary();
      setDashboardData(data);
      
      // Check for new notifications
      checkNotifications(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Show more helpful error message
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  };

  const checkNotifications = (data) => {
    const newNotifications = [];
    
    if (data.bug_tracking.critical > 0) {
      newNotifications.push({
        type: 'critical',
        message: `${data.bug_tracking.critical} kritiska buggar behöver uppmärksamhet`
      });
    }
    
    if (data.ai_insights.pending > 5) {
      newNotifications.push({
        type: 'info',
        message: `${data.ai_insights.pending} AI-förslag väntar på granskning`
      });
    }
    
    setNotifications(newNotifications);
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const renderTabContent = () => {
    switch (currentTab) {
      case 0:
        return <DashboardOverview data={dashboardData} loading={loading} />;
      case 1:
        return <TestCaseManager />;
      case 2:
        return <BugTracker />;
      case 3:
        return <AIInsights />;
      case 4:
        return <IntegrationSettings />;
      default:
        return <DashboardOverview data={dashboardData} loading={loading} />;
    }
  };

  return (
    <Box sx={{ flexGrow: 1, bgcolor: 'background.default', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Toolbar>
          <DashboardIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            QA Learning Platform - Dashboard
          </Typography>
          
          <IconButton color="inherit">
            <Badge badgeContent={notifications.length} color="error">
              <Notifications />
            </Badge>
          </IconButton>
        </Toolbar>
        
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}
          textColor="inherit"
          indicatorColor="secondary"
        >
          <Tab icon={<DashboardIcon />} label="Översikt" />
          <Tab icon={<Settings />} label="Test Cases" />
          <Tab icon={<BugReport />} label="Bug Tracking" />
          <Tab icon={<Psychology />} label="AI Insights" />
          <Tab icon={<Settings />} label="Integrationer" />
        </Tabs>
      </AppBar>

      <Box sx={{ p: 3 }}>
        {renderTabContent()}
      </Box>

      <Fab
        color="primary"
        aria-label="refresh"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={loadDashboardData}
      >
        <Refresh />
      </Fab>

      <Toaster position="top-right" />
    </Box>
  );
}

export default App;
import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  TrendingUp,
  CheckCircle,
  Error,
  Assessment
} from '@mui/icons-material';

const DashboardOverview = ({ data, loading }) => {
  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>
          Laddar dashboard data...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="error">
        Kunde inte ladda dashboard data. Kontrollera att backend körs på port 6001.
      </Alert>
    );
  }

  const MetricCard = ({ title, value, icon, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h3" color={`${color}.main`}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard Översikt
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Totala Tester"
            value={data.test_execution?.total_tests || 0}
            icon={<Assessment color="primary" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Godkända"
            value={data.test_execution?.passed_tests || 0}
            icon={<CheckCircle color="success" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Misslyckade"
            value={data.test_execution?.failed_tests || 0}
            icon={<Error color="error" />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Coverage"
            value={`${data.test_execution?.coverage || 0}%`}
            icon={<TrendingUp color="info" />}
            color="info"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Case Management
              </Typography>
              <Typography variant="h4" color="primary">
                {data.test_management?.total || 0}
              </Typography>
              <Typography color="textSecondary">
                Totala test cases
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Aktiva: {data.test_management?.active || 0} | 
                Kritiska: {data.test_management?.critical || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bug Tracking
              </Typography>
              <Typography variant="h4" color="error">
                {data.bug_tracking?.total || 0}
              </Typography>
              <Typography color="textSecondary">
                Totala bug reports
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Öppna: {data.bug_tracking?.open || 0} | 
                Kritiska: {data.bug_tracking?.critical || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                AI Insights
              </Typography>
              <Typography variant="h4" color="secondary">
                {data.ai_insights?.total || 0}
              </Typography>
              <Typography color="textSecondary">
                AI-förslag
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Pending: {data.ai_insights?.pending || 0} | 
                Confidence: {data.ai_insights?.avg_confidence || 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardOverview;
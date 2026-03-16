import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import { toast } from 'react-hot-toast';
import { integrationService } from '../services/api';

const IntegrationSettings = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [settings, setSettings] = useState({
    github: { token: '', repo: '', active: false },
    jira: { url: '', username: '', token: '', active: false },
    slack: { webhook_url: '', active: false }
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await integrationService.getSettings();
      const settingsMap = {};
      data.forEach(setting => {
        settingsMap[setting.service] = {
          ...setting.config,
          active: setting.active
        };
      });
      setSettings(prev => ({ ...prev, ...settingsMap }));
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async (service) => {
    try {
      await integrationService.saveSettings({
        service_name: service,
        config: { ...settings[service] },
        is_active: settings[service].active
      });
      toast.success(`${service} inställningar sparade!`);
    } catch (error) {
      toast.error('Fel vid sparande');
    }
  };

  const updateSetting = (service, key, value) => {
    setSettings(prev => ({
      ...prev,
      [service]: {
        ...prev[service],
        [key]: value
      }
    }));
  };

  const renderGitHubSettings = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          GitHub Integration
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.github.active}
                  onChange={(e) => updateSetting('github', 'active', e.target.checked)}
                />
              }
              label="Aktivera GitHub integration"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="GitHub Token"
              type="password"
              value={settings.github.token || ''}
              onChange={(e) => updateSetting('github', 'token', e.target.value)}
              helperText="Personal Access Token från GitHub"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Repository"
              value={settings.github.repo || ''}
              onChange={(e) => updateSetting('github', 'repo', e.target.value)}
              helperText="Format: username/repository"
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={() => saveSettings('github')}
            >
              Spara GitHub Inställningar
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  const renderJiraSettings = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Jira Integration
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.jira.active}
                  onChange={(e) => updateSetting('jira', 'active', e.target.checked)}
                />
              }
              label="Aktivera Jira integration"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Jira URL"
              value={settings.jira.url || ''}
              onChange={(e) => updateSetting('jira', 'url', e.target.value)}
              helperText="https://yourcompany.atlassian.net"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Användarnamn"
              value={settings.jira.username || ''}
              onChange={(e) => updateSetting('jira', 'username', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="API Token"
              type="password"
              value={settings.jira.token || ''}
              onChange={(e) => updateSetting('jira', 'token', e.target.value)}
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={() => saveSettings('jira')}
            >
              Spara Jira Inställningar
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  const renderSlackSettings = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Slack Integration
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.slack.active}
                  onChange={(e) => updateSetting('slack', 'active', e.target.checked)}
                />
              }
              label="Aktivera Slack notifieringar"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Webhook URL"
              value={settings.slack.webhook_url || ''}
              onChange={(e) => updateSetting('slack', 'webhook_url', e.target.value)}
              helperText="Slack Incoming Webhook URL"
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={() => saveSettings('slack')}
            >
              Spara Slack Inställningar
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Integration Inställningar
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        Konfigurera externa integrationer för automatisk bug tracking och notifieringar.
      </Alert>

      <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 3 }}>
        <Tab label="GitHub" />
        <Tab label="Jira" />
        <Tab label="Slack" />
      </Tabs>

      {currentTab === 0 && renderGitHubSettings()}
      {currentTab === 1 && renderJiraSettings()}
      {currentTab === 2 && renderSlackSettings()}
    </Box>
  );
};

export default IntegrationSettings;
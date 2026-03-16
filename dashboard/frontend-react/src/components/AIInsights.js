import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tabs,
  Tab,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  Psychology as AIIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Code as CodeIcon,
  TrendingUp as TrendIcon,
  BugReport as BugIcon
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';
import { aiService } from '../services/api';

const AIInsights = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [suggestions, setSuggestions] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [codeDialogOpen, setCodeDialogOpen] = useState(false);
  const [analysisCode, setAnalysisCode] = useState('');

  useEffect(() => {
    loadSuggestions();
  }, []);

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      const data = await aiService.getSuggestions();
      setSuggestions(data);
    } catch (error) {
      toast.error('Fel vid laddning av AI-förslag');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveSuggestion = async (id) => {
    try {
      await aiService.approveSuggestion(id, true);
      toast.success('AI-förslag godkänt!');
      loadSuggestions();
    } catch (error) {
      toast.error('Fel vid godkännande');
    }
  };

  const handleRejectSuggestion = async (id) => {
    try {
      await aiService.rejectSuggestion(id);
      toast.success('AI-förslag avvisat');
      loadSuggestions();
    } catch (error) {
      toast.error('Fel vid avvisning');
    }
  };

  const handleAnalyzeCode = async () => {
    if (!analysisCode.trim()) {
      toast.error('Ange kod för analys');
      return;
    }

    try {
      const result = await aiService.generateTests(analysisCode, 'manual_analysis.py');
      toast.success(`${result.suggestions_created} nya test-förslag skapade!`);
      setCodeDialogOpen(false);
      setAnalysisCode('');
      loadSuggestions();
    } catch (error) {
      toast.error('Fel vid kodanalys');
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (score) => {
    if (score >= 0.8) return 'Hög';
    if (score >= 0.6) return 'Medium';
    return 'Låg';
  };

  const renderSuggestions = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6">AI Test-förslag</Typography>
        <Button
          variant="contained"
          startIcon={<CodeIcon />}
          onClick={() => setCodeDialogOpen(true)}
        >
          Analysera Kod
        </Button>
      </Box>

      {suggestions.length === 0 ? (
        <Alert severity="info">
          Inga AI-förslag tillgängliga. Kör test-analys för att generera förslag.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {suggestions.map((suggestion) => (
            <Grid item xs={12} key={suggestion.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {suggestion.test_name}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Chip 
                          label={suggestion.test_type} 
                          size="small" 
                          color="primary" 
                        />
                        <Chip 
                          label={`Förtroende: ${getConfidenceLabel(suggestion.confidence_score)}`}
                          size="small" 
                          color={getConfidenceColor(suggestion.confidence_score)}
                        />
                        <Chip 
                          label={suggestion.generated_from} 
                          size="small" 
                          variant="outlined"
                        />
                      </Box>

                      <LinearProgress 
                        variant="determinate" 
                        value={suggestion.confidence_score * 100}
                        sx={{ mb: 2, height: 8, borderRadius: 4 }}
                        color={getConfidenceColor(suggestion.confidence_score)}
                      />

                      <Button
                        size="small"
                        onClick={() => setSelectedSuggestion(suggestion)}
                        sx={{ mb: 1 }}
                      >
                        Visa Kod
                      </Button>
                    </Box>

                    {suggestion.status === 'pending' && (
                      <Box>
                        <IconButton
                          color="success"
                          onClick={() => handleApproveSuggestion(suggestion.id)}
                          title="Godkänn förslag"
                        >
                          <ApproveIcon />
                        </IconButton>
                        <IconButton
                          color="error"
                          onClick={() => handleRejectSuggestion(suggestion.id)}
                          title="Avvisa förslag"
                        >
                          <RejectIcon />
                        </IconButton>
                      </Box>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  const renderPatterns = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Test-mönster Analys
      </Typography>
      
      {patterns.length === 0 ? (
        <Alert severity="info">
          Inga mönster detekterade. Kör fler tester för att generera mönsteranalys.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {patterns.map((pattern, index) => (
            <Grid item xs={12} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {pattern.type === 'flaky_tests' ? 'Instabila Tester' : 
                     pattern.type === 'slow_tests' ? 'Långsamma Tester' : pattern.type}
                  </Typography>
                  <Typography color="textSecondary" paragraph>
                    {pattern.description}
                  </Typography>
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <strong>Rekommendation:</strong> {pattern.recommendation}
                  </Alert>
                  {pattern.tests && (
                    <List dense>
                      {pattern.tests.slice(0, 5).map((test, testIndex) => (
                        <ListItem key={testIndex}>
                          <ListItemText 
                            primary={typeof test === 'string' ? test : test.name}
                            secondary={test.duration ? `Varaktighet: ${test.duration}s` : null}
                          />
                        </ListItem>
                      ))}
                      {pattern.tests.length > 5 && (
                        <ListItem>
                          <ListItemText 
                            primary={`... och ${pattern.tests.length - 5} till`}
                          />
                        </ListItem>
                      )}
                    </List>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  const renderAnalytics = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        AI Analytics Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AIIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Totala Förslag</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {suggestions.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ApproveIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Godkända</Typography>
              </Box>
              <Typography variant="h3" color="success.main">
                {suggestions.filter(s => s.status === 'approved').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Genomsnittligt Förtroende</Typography>
              </Box>
              <Typography variant="h3" color="info.main">
                {suggestions.length > 0 
                  ? Math.round(suggestions.reduce((acc, s) => acc + s.confidence_score, 0) / suggestions.length * 100)
                  : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Box>
      <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 3 }}>
        <Tab label="AI Förslag" />
        <Tab label="Mönster Analys" />
        <Tab label="Analytics" />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {currentTab === 0 && renderSuggestions()}
      {currentTab === 1 && renderPatterns()}
      {currentTab === 2 && renderAnalytics()}

      {/* Code Analysis Dialog */}
      <Dialog open={codeDialogOpen} onClose={() => setCodeDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Analysera Kod för Test-förslag</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={15}
            label="Klistra in kod här"
            value={analysisCode}
            onChange={(e) => setAnalysisCode(e.target.value)}
            sx={{ mt: 2 }}
            placeholder="def my_function():
    # Din kod här
    return result"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCodeDialogOpen(false)}>Avbryt</Button>
          <Button onClick={handleAnalyzeCode} variant="contained">
            Analysera & Generera Tester
          </Button>
        </DialogActions>
      </Dialog>

      {/* Code Preview Dialog */}
      <Dialog 
        open={!!selectedSuggestion} 
        onClose={() => setSelectedSuggestion(null)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          Test Kod: {selectedSuggestion?.test_name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mt: 2 }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '14px' }}>
              {selectedSuggestion?.test_code}
            </pre>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedSuggestion(null)}>Stäng</Button>
          {selectedSuggestion?.status === 'pending' && (
            <>
              <Button 
                onClick={() => {
                  handleApproveSuggestion(selectedSuggestion.id);
                  setSelectedSuggestion(null);
                }}
                color="success"
                variant="contained"
              >
                Godkänn
              </Button>
              <Button 
                onClick={() => {
                  handleRejectSuggestion(selectedSuggestion.id);
                  setSelectedSuggestion(null);
                }}
                color="error"
              >
                Avvisa
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIInsights;
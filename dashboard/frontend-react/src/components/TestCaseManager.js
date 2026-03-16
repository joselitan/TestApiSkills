import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Grid,
  IconButton,
  Fab
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';
import { testCaseService } from '../services/api';

const TestCaseManager = () => {
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [filters, setFilters] = useState({});
  const [stats, setStats] = useState({});

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    test_type: 'unit',
    priority: 'medium',
    status: 'active',
    tags: []
  });

  useEffect(() => {
    loadTestCases();
    loadStats();
  }, [filters]);

  const loadTestCases = async () => {
    try {
      setLoading(true);
      const data = await testCaseService.getAll(filters);
      setTestCases(data);
    } catch (error) {
      toast.error('Fel vid laddning av test cases');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await testCaseService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleSave = async () => {
    try {
      if (editingCase) {
        await testCaseService.update(editingCase.id, formData);
        toast.success('Test case uppdaterat!');
      } else {
        await testCaseService.create(formData);
        toast.success('Test case skapat!');
      }
      
      setDialogOpen(false);
      setEditingCase(null);
      resetForm();
      loadTestCases();
      loadStats();
    } catch (error) {
      toast.error('Fel vid sparande');
    }
  };

  const handleEdit = (testCase) => {
    setEditingCase(testCase);
    setFormData({
      name: testCase.name,
      description: testCase.description,
      test_type: testCase.test_type,
      priority: testCase.priority,
      status: testCase.status,
      tags: testCase.tags || []
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Är du säker på att du vill radera detta test case?')) {
      try {
        await testCaseService.delete(id);
        toast.success('Test case raderat!');
        loadTestCases();
        loadStats();
      } catch (error) {
        toast.error('Fel vid radering');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      test_type: 'unit',
      priority: 'medium',
      status: 'active',
      tags: []
    });
  };

  const handleAddTag = (event) => {
    if (event.key === 'Enter' && event.target.value.trim()) {
      const newTag = event.target.value.trim();
      if (!formData.tags.includes(newTag)) {
        setFormData({
          ...formData,
          tags: [...formData.tags, newTag]
        });
      }
      event.target.value = '';
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const columns = [
    { field: 'name', headerName: 'Namn', width: 200 },
    { field: 'test_type', headerName: 'Typ', width: 120 },
    { 
      field: 'priority', 
      headerName: 'Prioritet', 
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          color={
            params.value === 'critical' ? 'error' :
            params.value === 'high' ? 'warning' :
            params.value === 'medium' ? 'info' : 'default'
          }
          size="small"
        />
      )
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          color={params.value === 'active' ? 'success' : 'default'}
          size="small"
        />
      )
    },
    { 
      field: 'tags', 
      headerName: 'Tags', 
      width: 200,
      renderCell: (params) => (
        <Box>
          {params.value?.slice(0, 2).map(tag => (
            <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5 }} />
          ))}
          {params.value?.length > 2 && <span>+{params.value.length - 2}</span>}
        </Box>
      )
    },
    {
      field: 'actions',
      headerName: 'Åtgärder',
      width: 120,
      renderCell: (params) => (
        <Box>
          <IconButton onClick={() => handleEdit(params.row)} size="small">
            <EditIcon />
          </IconButton>
          <IconButton onClick={() => handleDelete(params.row.id)} size="small" color="error">
            <DeleteIcon />
          </IconButton>
        </Box>
      )
    }
  ];

  return (
    <Box>
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Totala Test Cases
              </Typography>
              <Typography variant="h4">
                {stats.total || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Aktiva
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.active || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Kritiska
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.critical || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Test Typ</InputLabel>
                <Select
                  value={filters.test_type || ''}
                  onChange={(e) => setFilters({...filters, test_type: e.target.value})}
                >
                  <MenuItem value="">Alla</MenuItem>
                  <MenuItem value="unit">Unit</MenuItem>
                  <MenuItem value="integration">Integration</MenuItem>
                  <MenuItem value="ui">UI</MenuItem>
                  <MenuItem value="api">API</MenuItem>
                  <MenuItem value="performance">Performance</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.status || ''}
                  onChange={(e) => setFilters({...filters, status: e.target.value})}
                >
                  <MenuItem value="">Alla</MenuItem>
                  <MenuItem value="active">Aktiv</MenuItem>
                  <MenuItem value="inactive">Inaktiv</MenuItem>
                  <MenuItem value="deprecated">Deprecated</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Prioritet</InputLabel>
                <Select
                  value={filters.priority || ''}
                  onChange={(e) => setFilters({...filters, priority: e.target.value})}
                >
                  <MenuItem value="">Alla</MenuItem>
                  <MenuItem value="low">Låg</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">Hög</MenuItem>
                  <MenuItem value="critical">Kritisk</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Data Grid */}
      <Card>
        <CardContent>
          <Box sx={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={testCases}
              columns={columns}
              loading={loading}
              pageSize={25}
              rowsPerPageOptions={[25, 50, 100]}
              disableSelectionOnClick
            />
          </Box>
        </CardContent>
      </Card>

      {/* Add Button */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 80, right: 16 }}
        onClick={() => {
          resetForm();
          setEditingCase(null);
          setDialogOpen(true);
        }}
      >
        <AddIcon />
      </Fab>

      {/* Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingCase ? 'Redigera Test Case' : 'Skapa Nytt Test Case'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Namn"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Beskrivning"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Test Typ</InputLabel>
                <Select
                  value={formData.test_type}
                  onChange={(e) => setFormData({...formData, test_type: e.target.value})}
                >
                  <MenuItem value="unit">Unit</MenuItem>
                  <MenuItem value="integration">Integration</MenuItem>
                  <MenuItem value="ui">UI</MenuItem>
                  <MenuItem value="api">API</MenuItem>
                  <MenuItem value="performance">Performance</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Prioritet</InputLabel>
                <Select
                  value={formData.priority}
                  onChange={(e) => setFormData({...formData, priority: e.target.value})}
                >
                  <MenuItem value="low">Låg</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">Hög</MenuItem>
                  <MenuItem value="critical">Kritisk</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Lägg till tags (tryck Enter)"
                onKeyPress={handleAddTag}
                helperText="Tryck Enter för att lägga till en tag"
              />
              <Box sx={{ mt: 1 }}>
                {formData.tags.map(tag => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => handleRemoveTag(tag)}
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Avbryt</Button>
          <Button onClick={handleSave} variant="contained">
            {editingCase ? 'Uppdatera' : 'Skapa'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TestCaseManager;
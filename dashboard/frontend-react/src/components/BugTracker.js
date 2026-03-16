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
  Alert
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add as AddIcon } from '@mui/icons-material';
import { toast } from 'react-hot-toast';
import { bugService } from '../services/api';

const BugTracker = () => {
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    severity: 'medium',
    status: 'open',
    assigned_to: ''
  });

  useEffect(() => {
    loadBugs();
  }, []);

  const loadBugs = async () => {
    try {
      setLoading(true);
      const data = await bugService.getAll();
      setBugs(data);
    } catch (error) {
      toast.error('Fel vid laddning av bug reports');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await bugService.create(formData);
      toast.success('Bug report skapad!');
      setDialogOpen(false);
      resetForm();
      loadBugs();
    } catch (error) {
      toast.error('Fel vid sparande');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      severity: 'medium',
      status: 'open',
      assigned_to: ''
    });
  };

  const columns = [
    { field: 'title', headerName: 'Titel', width: 250 },
    { 
      field: 'severity', 
      headerName: 'Severity', 
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
          color={
            params.value === 'open' ? 'error' :
            params.value === 'in_progress' ? 'warning' :
            params.value === 'resolved' ? 'success' : 'default'
          }
          size="small"
        />
      )
    },
    { field: 'assigned_to', headerName: 'Tilldelad', width: 150 },
    { field: 'created_at', headerName: 'Skapad', width: 150 }
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Bug Tracking</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            resetForm();
            setDialogOpen(true);
          }}
        >
          Ny Bug Report
        </Button>
      </Box>

      <Card>
        <CardContent>
          <Box sx={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={bugs}
              columns={columns}
              loading={loading}
              pageSize={25}
              rowsPerPageOptions={[25, 50, 100]}
              disableSelectionOnClick
            />
          </Box>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Skapa Bug Report</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Titel"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Beskrivning"
                multiline
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={formData.severity}
                  onChange={(e) => setFormData({...formData, severity: e.target.value})}
                >
                  <MenuItem value="low">Låg</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">Hög</MenuItem>
                  <MenuItem value="critical">Kritisk</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Tilldelad till"
                value={formData.assigned_to}
                onChange={(e) => setFormData({...formData, assigned_to: e.target.value})}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Avbryt</Button>
          <Button onClick={handleSave} variant="contained">Skapa</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BugTracker;
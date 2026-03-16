import axios from 'axios';

// Use full URL since React runs on different port
const API_BASE = 'http://localhost:6001/api';

// Configure axios defaults
axios.defaults.timeout = 10000;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Dashboard Services
export const dashboardService = {
  getSummary: () => axios.get(`${API_BASE}/dashboard/summary`).then(res => res.data),
  getEnhancedSummary: () => axios.get(`${API_BASE}/dashboard/enhanced-summary`).then(res => res.data),
  getTestTypes: () => axios.get(`${API_BASE}/dashboard/test-types`).then(res => res.data),
  getPerformance: () => axios.get(`${API_BASE}/dashboard/performance`).then(res => res.data),
};

// Test Case Management Services
export const testCaseService = {
  getAll: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return axios.get(`${API_BASE}/test-cases?${params}`).then(res => res.data);
  },
  create: (testCase) => axios.post(`${API_BASE}/test-cases`, testCase).then(res => res.data),
  update: (id, updates) => axios.put(`${API_BASE}/test-cases/${id}`, updates).then(res => res.data),
  delete: (id) => axios.delete(`${API_BASE}/test-cases/${id}`).then(res => res.data),
  getStats: () => axios.get(`${API_BASE}/test-cases/stats`).then(res => res.data),
  bulkImport: (testCases) => axios.post(`${API_BASE}/test-cases/bulk-import`, testCases).then(res => res.data),
};

// Bug Tracking Services
export const bugService = {
  getAll: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return axios.get(`${API_BASE}/bugs?${params}`).then(res => res.data);
  },
  create: (bug) => axios.post(`${API_BASE}/bugs`, bug).then(res => res.data),
  createGitHubIssue: (bugId) => axios.post(`${API_BASE}/bugs/${bugId}/github-issue`).then(res => res.data),
  createJiraTicket: (bugId) => axios.post(`${API_BASE}/bugs/${bugId}/jira-ticket`).then(res => res.data),
  getStats: () => axios.get(`${API_BASE}/bugs/stats`).then(res => res.data),
  testGitHubIntegration: (config) => axios.post(`${API_BASE}/integrations/github/test`, config).then(res => res.data),
  sendSlackNotification: (data) => axios.post(`${API_BASE}/integrations/slack/notify`, data).then(res => res.data),
};

// AI Testing Services
export const aiService = {
  getSuggestions: (status) => {
    const params = status ? `?status=${status}` : '';
    return axios.get(`${API_BASE}/ai/suggestions${params}`).then(res => res.data);
  },
  analyzeFailures: (failures) => axios.post(`${API_BASE}/ai/analyze-failures`, { failures }).then(res => res.data),
  generateTests: (code, filePath) => axios.post(`${API_BASE}/ai/generate-tests`, { code, file_path: filePath }).then(res => res.data),
  approveSuggestion: (id, generateFile = false) => axios.post(`${API_BASE}/ai/suggestions/${id}/approve`, { generate_file: generateFile }).then(res => res.data),
  rejectSuggestion: (id) => axios.post(`${API_BASE}/ai/suggestions/${id}/reject`).then(res => res.data),
  detectPatterns: (testRuns) => axios.post(`${API_BASE}/ai/patterns/detect`, { test_runs: testRuns }).then(res => res.data),
  identifyCoverageGaps: (coverageData) => axios.post(`${API_BASE}/ai/coverage/gaps`, { coverage_data: coverageData }).then(res => res.data),
};

// Integration Services
export const integrationService = {
  getSettings: () => axios.get(`${API_BASE}/integrations/settings`).then(res => res.data),
  saveSettings: (settings) => axios.post(`${API_BASE}/integrations/settings`, settings).then(res => res.data),
};

// Test Run Services
export const testRunService = {
  addRun: (runData) => axios.post(`${API_BASE}/test-runs`, runData).then(res => res.data),
};
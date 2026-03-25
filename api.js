// Adaptify — API Client
const API_BASE = 'http://127.0.0.1:8000';

function getToken() {
  return localStorage.getItem('cognilearn_token');
}
function getUser() {
  const u = localStorage.getItem('cognilearn_user');
  return u ? JSON.parse(u) : null;
}
function setAuth(tokenData) {
  localStorage.setItem('cognilearn_token', tokenData.access_token);
  localStorage.setItem('cognilearn_user', JSON.stringify({
    id: tokenData.user_id,
    name: tokenData.name,
    role: tokenData.role
  }));
}
function clearAuth() {
  localStorage.removeItem('cognilearn_token');
  localStorage.removeItem('cognilearn_user');
}

async function apiCall(endpoint, method = 'GET', body = null, isFormData = false) {
  const token = getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isFormData && body) headers['Content-Type'] = 'application/json';

  const options = { method, headers };
  if (body) options.body = isFormData ? body : JSON.stringify(body);

  const res = await fetch(`${API_BASE}${endpoint}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

const API = {
  // Auth
  register: (data)   => apiCall('/auth/register', 'POST', data),
  login:    (data)   => apiCall('/auth/login', 'POST', data),
  getMe:    ()       => apiCall('/auth/me'),

  // Teacher
  uploadMaterial: (formData)    => apiCall('/teacher/upload-material', 'POST', formData, true),
  getMyMaterials: ()            => apiCall('/teacher/materials'),
  deleteMaterial: (id)          => apiCall(`/teacher/materials/${id}`, 'DELETE'),
  getAllStudents:  ()            => apiCall('/teacher/students'),
  deleteStudent:   (id)          => apiCall(`/teacher/students/${id}`, 'DELETE'),
  getStudentAnalytics: (id)     => apiCall(`/teacher/students/${id}/analytics`),
  getOverview:    ()            => apiCall('/teacher/analytics/overview'),

  // Student
  submitIQ:  (data) => apiCall('/student/submit-iq', 'POST', data),
  getProfile: ()    => apiCall('/student/profile'),
  chatWithAgent: (data) => apiCall('/student/chat', 'POST', data),
  getMyAssignments: () => apiCall('/student/assignments'),
  submitAssignment: (id, data) => apiCall(`/student/assignments/${id}/submit`, 'POST', data),

  // Assignments
  generateAssignment: (data) => apiCall('/assignments/generate', 'POST', data),
  getAssignment: (id)        => apiCall(`/assignments/${id}`),
  listAssignments: ()        => apiCall('/assignments/'),
  updateAssignment: (id, data) => apiCall(`/assignments/${id}`, 'PUT', data),
  deleteAssignment: (id)       => apiCall(`/assignments/${id}`, 'DELETE'),
};

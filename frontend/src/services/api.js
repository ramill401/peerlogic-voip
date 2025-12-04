import axios from 'axios'

// Use environment variable or fallback to localhost
// Use localhost (not 127.0.0.1) to match Django admin for cookie sharing
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Update with your connection ID (from setup_test_connection output)
const CONNECTION_ID = import.meta.env.VITE_CONNECTION_ID || '9199698e-b059-4b58-b8cc-051c884eca78'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // Send cookies for session authentication
})

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle 401 Unauthorized - redirect to login
      if (error.response.status === 401) {
        console.error('Authentication required. Please log in.')
        // For MVP: redirect to Django admin login
        // In production, redirect to Peerlogic login page
        const baseUrl = API_BASE.replace('/api', '')
        window.location.href = `${baseUrl}/admin/login/?next=${encodeURIComponent(window.location.href)}`
        return Promise.reject(error)
      }
      // Handle 403 Forbidden - redirect to login (might be unauthenticated)
      if (error.response.status === 403) {
        console.error('Access denied. Redirecting to login...')
        const baseUrl = API_BASE.replace('/api', '')
        window.location.href = `${baseUrl}/admin/login/?next=${encodeURIComponent(window.location.href)}`
        return Promise.reject(error)
      }
    } else if (error.request) {
      // Network error or CORS error - might be authentication issue
      console.error('Network error:', error.message)
      // Don't redirect on network errors - let the component handle it
    }
    return Promise.reject(error)
  }
)

export const connectionId = CONNECTION_ID

export const voipApi = {
  // Health
  health: () => api.get('/health/'),
  
  // Connections
  getConnections: () => api.get('/connections/'),

  // Users
  getUsers: (params = {}) => 
    api.get(`/connections/${CONNECTION_ID}/users/`, { params }),
  
  createUser: (userData) => 
    api.post(`/connections/${CONNECTION_ID}/users/create/`, userData),
  
  updateUser: (userId, userData) => 
    api.put(`/connections/${CONNECTION_ID}/users/${userId}/update/`, userData),
  
  deleteUser: (userId) => 
    api.delete(`/connections/${CONNECTION_ID}/users/${userId}/delete/`),

  // Devices
  getDevices: (params = {}) => 
    api.get(`/connections/${CONNECTION_ID}/devices/`, { params }),
  
  createDevice: (deviceData) => 
    api.post(`/connections/${CONNECTION_ID}/devices/create/`, deviceData),
  
  deleteDevice: (deviceId) => 
    api.delete(`/connections/${CONNECTION_ID}/devices/${deviceId}/delete/`),
}

export default voipApi


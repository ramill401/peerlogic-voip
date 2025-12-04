import axios from 'axios'

// Use environment variable or fallback to localhost
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

// Update with your Railway connection ID
const CONNECTION_ID = import.meta.env.VITE_CONNECTION_ID || '9199698e-b059-4b58-b8cc-051c884eca78'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

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


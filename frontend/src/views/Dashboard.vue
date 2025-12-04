<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-blue-100 text-blue-600">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Total Users</p>
            <p class="text-2xl font-semibold text-gray-900">{{ stats.users }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-green-100 text-green-600">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Devices Online</p>
            <p class="text-2xl font-semibold text-gray-900">{{ stats.devicesOnline }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-purple-100 text-purple-600">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Connection Status</p>
            <p class="text-2xl font-semibold text-green-600">Active</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div class="flex items-start">
        <svg class="w-5 h-5 text-red-600 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
          <h3 class="text-sm font-medium text-red-800">Connection Error</h3>
          <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          <p class="mt-2 text-xs text-red-600">
            To fix this, you need to configure NetSapiens credentials. Run:
            <code class="bg-red-100 px-1 rounded">python manage.py setup_test_connection --domain=hi.peerlogic.com --client-id=peerlogic-api-stage --client-secret=f9ded02d3a93db4675e07fc4d79d3ddc --username=YOUR_USERNAME --password=YOUR_PASSWORD</code>
          </p>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
      <div class="flex gap-4">
        <router-link to="/users" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Manage Users
        </router-link>
        <router-link to="/devices" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
          Manage Devices
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { voipApi } from '../services/api'

const stats = ref({
  users: 0,
  devicesOnline: 0,
})
const error = ref(null)

onMounted(async () => {
  try {
    const [usersRes, devicesRes] = await Promise.all([
      voipApi.getUsers(),
      voipApi.getDevices(),
    ])
    
    if (usersRes.data.error) {
      error.value = usersRes.data.error.message
    } else {
      stats.value.users = usersRes.data.total || 0
    }
    
    if (devicesRes.data.error) {
      error.value = error.value || devicesRes.data.error.message
    } else {
      const devices = devicesRes.data.items || []
      stats.value.devicesOnline = devices.filter(d => d.status === 'online').length
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
    error.value = err.response?.data?.error?.message || err.message || 'Failed to load dashboard data'
  }
})
</script>


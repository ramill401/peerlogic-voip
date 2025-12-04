<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Devices</h1>
      <button 
        @click="showCreateModal = true"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Add Device
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Devices Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="device in devices" :key="device.id" 
        class="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between">
          <div class="flex items-center">
            <div :class="[
              'p-3 rounded-full',
              device.status === 'online' ? 'bg-green-100' : 'bg-gray-100'
            ]">
              <svg class="w-6 h-6" :class="device.status === 'online' ? 'text-green-600' : 'text-gray-400'"
                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
              </svg>
            </div>
            <div class="ml-4">
              <h3 class="text-sm font-medium text-gray-900">{{ device.name }}</h3>
              <p class="text-sm text-gray-500">{{ device.manufacturer }} {{ device.model }}</p>
            </div>
          </div>
          <span :class="[
            'px-2 py-1 text-xs font-medium rounded-full',
            device.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          ]">
            {{ device.status }}
          </span>
        </div>
        
        <div class="mt-4 pt-4 border-t border-gray-100">
          <dl class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <dt class="text-gray-500">Type</dt>
              <dd class="text-gray-900">{{ formatDeviceType(device.device_type) }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">MAC</dt>
              <dd class="text-gray-900 font-mono text-xs">{{ device.mac_address || '-' }}</dd>
            </div>
          </dl>
        </div>
        
        <div class="mt-4 flex justify-end">
          <button @click="confirmDelete(device)" class="text-red-600 hover:text-red-900 text-sm">
            Delete
          </button>
        </div>
      </div>
    </div>

    <div v-if="!loading && devices.length === 0" class="text-center py-12 text-gray-500">
      No devices found
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-black opacity-30" @click="showCreateModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Add Device</h3>
          
          <form @submit.prevent="createDevice">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Device Name</label>
                <input v-model="formData.name" type="text" required
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg"/>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">MAC Address</label>
                <input v-model="formData.mac_address" type="text" required placeholder="AA:BB:CC:DD:EE:FF"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg"/>
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Manufacturer</label>
                  <input v-model="formData.manufacturer" type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"/>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Model</label>
                  <input v-model="formData.model" type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"/>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Device Type</label>
                <select v-model="formData.device_type"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="desk_phone">Desk Phone</option>
                  <option value="softphone">Softphone</option>
                  <option value="conference">Conference Phone</option>
                  <option value="mobile_app">Mobile App</option>
                </select>
              </div>
            </div>
            
            <div class="flex justify-end gap-3 mt-6">
              <button type="button" @click="showCreateModal = false"
                class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                Cancel
              </button>
              <button type="submit"
                class="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                Create
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Delete Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-black opacity-30" @click="showDeleteModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Delete Device</h3>
          <p class="text-gray-500 mb-6">Are you sure you want to delete {{ deviceToDelete?.name }}?</p>
          <div class="flex justify-end gap-3">
            <button @click="showDeleteModal = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg">Cancel</button>
            <button @click="deleteDevice"
              class="px-4 py-2 text-white bg-red-600 rounded-lg">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { voipApi } from '../services/api'

const devices = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const deviceToDelete = ref(null)
const formData = ref({
  name: '',
  mac_address: '',
  manufacturer: '',
  model: '',
  device_type: 'desk_phone',
})

const loadDevices = async () => {
  loading.value = true
  try {
    const res = await voipApi.getDevices()
    devices.value = res.data.items || []
  } catch (err) {
    console.error('Failed to load devices:', err)
  } finally {
    loading.value = false
  }
}

const formatDeviceType = (type) => {
  const types = {
    desk_phone: 'Desk Phone',
    softphone: 'Softphone',
    conference: 'Conference',
    mobile_app: 'Mobile App',
  }
  return types[type] || type
}

const createDevice = async () => {
  try {
    await voipApi.createDevice(formData.value)
    showCreateModal.value = false
    formData.value = { name: '', mac_address: '', manufacturer: '', model: '', device_type: 'desk_phone' }
    loadDevices()
  } catch (err) {
    console.error('Failed to create device:', err)
  }
}

const confirmDelete = (device) => {
  deviceToDelete.value = device
  showDeleteModal.value = true
}

const deleteDevice = async () => {
  try {
    await voipApi.deleteDevice(deviceToDelete.value.id)
    showDeleteModal.value = false
    loadDevices()
  } catch (err) {
    console.error('Failed to delete device:', err)
  }
}

onMounted(loadDevices)
</script>


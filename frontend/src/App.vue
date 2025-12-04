<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside class="fixed top-0 left-0 z-40 w-64 h-screen bg-white border-r border-gray-200">
      <div class="h-full px-3 py-4 overflow-y-auto">
        <a href="/" class="flex items-center mb-6 px-2">
          <span class="text-xl font-semibold text-gray-800">VoIP Admin</span>
        </a>
        <ul class="space-y-2">
          <li>
            <router-link 
              to="/" 
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              :class="{ 'bg-blue-50 text-blue-700': route.path === '/' }"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              <span class="ml-3">Dashboard</span>
            </router-link>
          </li>
          <li>
            <router-link 
              to="/users" 
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              :class="{ 'bg-blue-50 text-blue-700': route.path === '/users' }"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
              </svg>
              <span class="ml-3">Users</span>
            </router-link>
          </li>
          <li>
            <router-link 
              to="/devices" 
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              :class="{ 'bg-blue-50 text-blue-700': route.path === '/devices' }"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
              </svg>
              <span class="ml-3">Devices</span>
            </router-link>
          </li>
        </ul>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="ml-64 p-8">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

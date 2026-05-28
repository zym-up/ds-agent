import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const routes = [
  { path: '/', name: 'upload', component: () => import('./views/DataUpload.vue') },
  { path: '/analysis', name: 'analysis', component: () => import('./views/Analysis.vue') },
  { path: '/report', name: 'report', component: () => import('./views/Report.vue') },
  { path: '/settings', name: 'settings', component: () => import('./views/Settings.vue') },
  { path: '/history', name: 'history', component: () => import('./views/History.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')

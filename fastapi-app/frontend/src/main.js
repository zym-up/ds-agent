import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const routes = [
  { path: '/', name: 'new_project', component: () => import('./views/NewProject.vue') },
  { path: '/analysis', name: 'analysis', component: () => import('./views/Analysis.vue') },
  { path: '/settings', name: 'settings', component: () => import('./views/Settings.vue') },
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

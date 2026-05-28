<template>
  <div>
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px">
      <h2 style="margin: 0">📋 报告预览</h2>
      <div style="flex: 1" />
      <el-button @click="$emit('back')">← 返回分析</el-button>
      <el-button type="primary" @click="downloadReport">⬇ 下载 HTML</el-button>
    </div>
    <iframe v-if="blobUrl" :src="blobUrl" style="width: 100%; height: calc(100vh - 120px); border: 1px solid #eee; border-radius: 8px" />
    <div v-else style="text-align: center; color: #999; padding: 40px">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '../stores/project'

defineEmits(['back'])
const projectStore = useProjectStore()
const blobUrl = ref('')

onMounted(async () => {
  try {
    const res = await fetch(`/api/report/download/${projectStore.currentId}`)
    if (res.ok) {
      const html = await res.text()
      const blob = new Blob([html], { type: 'text/html' })
      blobUrl.value = URL.createObjectURL(blob)
    }
  } catch (e) { /* */ }
})

onUnmounted(() => {
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value)
  }
})

const downloadReport = () => {
  const a = document.createElement('a')
  a.href = `/api/report/download/${projectStore.currentId}`
  a.download = `${projectStore.currentName}_report.html`
  a.click()
}
</script>

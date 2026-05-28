<template>
  <div>
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px">
      <h2 style="margin: 0">📋 报告预览</h2>
      <div style="flex: 1" />
      <el-button @click="$emit('back')">← 返回分析</el-button>
      <el-button type="primary" @click="downloadReport">⬇ 下载 HTML</el-button>
    </div>
    <div v-if="reportHtml" v-html="reportHtml" style="border: 1px solid #eee; border-radius: 8px; padding: 20px; background: #fff; min-height: 500px" />
    <div v-else style="text-align: center; color: #999; padding: 40px">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useProjectStore } from '../stores/project'

defineEmits(['back'])
const projectStore = useProjectStore()
const reportHtml = ref('')

onMounted(async () => {
  try {
    const res = await fetch(`/api/report/download/${projectStore.currentId}`)
    if (res.ok) {
      reportHtml.value = await res.text()
    }
  } catch (e) { /* */ }
})

const downloadReport = () => {
  const a = document.createElement('a')
  a.href = `/api/report/download/${projectStore.currentId}`
  a.download = `${projectStore.currentName}_report.html`
  a.click()
}
</script>

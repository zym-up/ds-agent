<template>
  <div>
    <h2>📋 报告导出</h2>

    <div v-if="!projectStore.currentId">
      <el-empty description="请先创建分析项目" />
    </div>

    <div v-else>
      <el-input v-model="title" placeholder="报告标题" style="width: 400px; margin-bottom: 15px" />
      <el-input v-model="conclusion" type="textarea" :rows="5" placeholder="分析结论（可选）"
                style="margin-bottom: 15px" />

      <el-button type="primary" @click="genReport" :loading="generating">生成报告</el-button>

      <div v-if="reportPath" style="margin-top: 20px">
        <el-alert :title="'报告已生成: ' + reportPath" type="success" :closable="false" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { generateReport } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()
const title = ref(projectStore.currentName + ' — 分析报告')
const conclusion = ref('')
const reportPath = ref('')
const generating = ref(false)

const genReport = async () => {
  generating.value = true
  try {
    const res = await generateReport(projectStore.currentId, title.value, conclusion.value)
    reportPath.value = res.data.path
    ElMessage.success('报告已生成: ' + res.data.path)
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    generating.value = false
  }
}
</script>

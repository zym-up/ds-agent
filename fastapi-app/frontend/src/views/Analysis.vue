<template>
  <div>
    <h2>🔬 分析对话</h2>

    <div v-if="!projectStore.currentId">
      <el-empty description="请先上传数据并创建项目" />
    </div>

    <div v-else style="display: flex; gap: 20px; height: calc(100vh - 150px)">
      <div style="flex: 1; display: flex; flex-direction: column">
        <div style="flex: 1; overflow-y: auto; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 10px">
          <div v-for="(msg, i) in chatHistory" :key="i" style="margin-bottom: 15px">
            <div v-if="msg.role === 'user'" style="text-align: right">
              <el-tag>👤 你</el-tag>
              <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-top: 5px; display: inline-block; text-align: left; max-width: 80%">
                {{ msg.content }}
              </div>
            </div>
            <div v-else>
              <el-tag type="success">🤖 Agent</el-tag>
              <div style="background: #f5f5f5; padding: 10px; border-radius: 8px; margin-top: 5px; max-width: 80%">
                {{ msg.content }}
              </div>
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 10px">
          <el-input v-model="userInput" placeholder="描述你的分析需求..." @keyup.enter="sendMessage" />
          <el-button type="primary" @click="sendMessage" :loading="sending">发送</el-button>
        </div>
      </div>

      <div style="width: 250px; border: 1px solid #eee; border-radius: 8px; padding: 15px">
        <h3>📋 分析步骤</h3>
        <div v-if="!steps.length" style="color: #999; font-size: 13px; margin-top: 20px">
          在对话区描述需求，Agent 将自动规划步骤
        </div>
        <div v-for="(step, i) in steps" :key="i" style="margin: 10px 0; padding: 8px; background: #fafafa; border-radius: 4px">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>
              <span v-if="step.status === 'done'">✓</span>
              <span v-else-if="step.status === 'running'">⟳</span>
              <span v-else>○</span>
              步骤 {{ i + 1 }}
            </span>
            <el-button v-if="step.status === 'pending'" size="small" @click="runStep(i)">▶</el-button>
          </div>
          <div style="font-size: 12px; color: #666; margin-top: 4px">{{ step.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { planAnalysis, executeStep } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()
const userInput = ref('')
const sending = ref(false)
const chatHistory = ref([])
const steps = ref([])

const sendMessage = async () => {
  if (!userInput.value.trim()) return
  const msg = userInput.value
  userInput.value = ''
  chatHistory.value.push({ role: 'user', content: msg })

  sending.value = true
  try {
    const res = await planAnalysis(projectStore.currentId, msg)
    chatHistory.value.push({ role: 'assistant', content: res.data.explanation })
    steps.value = res.data.steps || []
  } catch (e) {
    ElMessage.error('请求失败: ' + e.message)
  } finally {
    sending.value = false
  }
}

const runStep = async (index) => {
  steps.value[index].status = 'running'
  try {
    const res = await executeStep(projectStore.currentId, index)
    steps.value[index].status = res.data.status
  } catch (e) {
    steps.value[index].status = 'error'
    ElMessage.error('执行失败: ' + e.message)
  }
}
</script>

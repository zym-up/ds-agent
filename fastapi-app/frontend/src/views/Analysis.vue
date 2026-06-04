<template>
  <div>
    <div v-if="projectStore.reportPreviewMode">
      <ReportPreview @back="projectStore.reportPreviewMode = false" />
    </div>

    <div v-else-if="!projectStore.currentId">
      <el-empty description="请先新建项目，或从侧边栏「📁 历史项目」中打开已有项目" />
    </div>

    <div v-else>
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px">
        <el-button @click="showProjectInfo = true; loadProjectInfo()" type="primary" plain>
          📊 {{ projectStore.currentName }}
        </el-button>
        <span style="color: #666; font-size: 13px">
          数据: {{ projectStore.selectedDataFiles.length }}/{{ projectStore.dataFiles.length }} 个文件 · {{ projectStore.totalRows.toLocaleString() }} 行
        </span>
        <div style="flex: 1" />
        <el-button @click="showUploadDialog = true">📤 上传新数据</el-button>
        <el-button type="primary" @click="openReportDialog">📋 导出报告</el-button>
      </div>

      <el-divider style="margin: 8px 0" />

      <div style="display: flex; gap: 12px; height: calc(100vh - 180px)">
        <!-- 左栏: 对话 + 轮次 (25%) -->
        <div style="width: 25%; display: flex; flex-direction: column; border: 1px solid #eee; border-radius: 8px">
          <div style="padding: 8px 12px; font-weight: 600; border-bottom: 1px solid #eee; font-size: 14px">💬 对话</div>
          <div style="flex: 1; overflow-y: auto; padding: 8px 12px" ref="chatListEl">
            <!-- 轮次列表 -->
            <div v-if="projectStore.rounds.length" style="margin-bottom: 8px">
              <div style="font-size: 11px; color: #999; margin-bottom: 4px; padding: 0 4px">对话轮次 (点击切换)</div>
              <div v-for="(rnd, ri) in projectStore.rounds" :key="ri"
                   @click="projectStore.setCurrentRound(ri)"
                   :style="{
                     padding: '8px 10px', margin: '4px 0', borderRadius: '6px', fontSize: '12px',
                     cursor: 'pointer', transition: 'all 0.15s',
                     border: ri === projectStore.currentRound ? '1px solid #1a73e8' : '1px solid #ddd',
                     background: ri === projectStore.currentRound ? '#e8f0fe' : '#f5f5f5'
                   }">
                <div style="font-weight: 600; margin-bottom: 3px; display: flex; align-items: center; gap: 4px">
                  <span>🔄 第{{ ri + 1 }}轮</span>
                  <span v-if="ri === projectStore.currentRound" style="font-size: 10px; color: #1a73e8">(当前)</span>
                </div>
                <div style="color: #666; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 2px">
                  {{ (rnd.user_input || '未命名').slice(0, 50) }}
                </div>
                <div style="color: #999; font-size: 11px">
                  {{ rnd.steps?.filter(s => s.status === 'done').length || 0 }}/{{ rnd.steps?.length || 0 }} 步骤完成
                </div>
              </div>
            </div>
            <el-divider v-if="projectStore.rounds.length" style="margin: 8px 0" />

            <div v-for="(msg, i) in projectStore.chatHistory" :key="i" style="margin-bottom: 10px">
              <div v-if="msg.role === 'user'" style="color: #1a73e8; font-size: 12px; margin-bottom: 2px">👤 你</div>
              <div v-else style="color: #34a853; font-size: 12px; margin-bottom: 2px">🤖 Agent</div>
              <div :style="{
                padding: '8px 10px', borderRadius: '6px', fontSize: '13px', lineHeight: '1.5',
                background: msg.role === 'user' ? '#e8f0fe' : '#f5f5f5'
              }">{{ msg.content }}</div>
            </div>
            <div v-if="streamingResponse" style="font-size: 13px; color: #666; white-space: pre-wrap">{{ streamingResponse }}</div>
          </div>
          <div style="padding: 8px; border-top: 1px solid #eee">
            <el-input v-model="userInput" placeholder="描述你的分析需求..." @keyup.enter="sendMessage" />
            <el-button type="primary" @click="sendMessage" :loading="sending" style="margin-top: 6px; width: 100%">
              发送
            </el-button>
          </div>
        </div>

        <!-- 中栏: 结果 (50%) -->
        <div style="width: 50%; border: 1px solid #eee; border-radius: 8px; display: flex; flex-direction: column">
          <div style="padding: 8px 12px; font-weight: 600; border-bottom: 1px solid #eee; font-size: 14px">
            📈 结果
            <span v-if="projectStore.currentRound >= 0" style="color: #999; font-size: 12px; margin-left: 8px">
              (第{{ projectStore.currentRound + 1 }}轮)
            </span>
          </div>
          <div style="flex: 1; overflow-y: auto; padding: 12px">
            <template v-if="projectStore.viewingStepIndex >= 0">
              <div v-if="viewingStep.llm_explanation" style="background: #e8f0fe; border-left: 3px solid #1a73e8; padding: 10px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 13px">
                🤖 <b>AI 解读:</b> {{ viewingStep.llm_explanation }}
              </div>
              <div v-if="viewingStep.last_text" v-html="renderMarkdown(viewingStep.last_text)" style="font-size: 13px"></div>
              <div v-for="c in (viewingStep.chart_count || 0)" :key="'h'+c"
                   style="margin-top: 10px; border: 1px solid #eee; border-radius: 4px; overflow: hidden">
                <iframe :src="chartUrl(viewingRoundIndex, projectStore.viewingStepIndex, c)" style="width: 100%; height: 400px; border: none" />
              </div>
            </template>
            <div v-else-if="currentResult">
              <div v-if="currentResult.llm_explanation" style="background: #e8f0fe; border-left: 3px solid #1a73e8; padding: 10px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 13px">
                🤖 <b>AI 解读:</b> {{ currentResult.llm_explanation }}
              </div>
              <div v-if="currentResult.text" v-html="renderMarkdown(currentResult.text)" style="font-size: 13px"></div>
              <div v-for="c in (currentResult.chart_count || 0)" :key="'c'+c"
                   style="margin-top: 10px; border: 1px solid #eee; border-radius: 4px; overflow: hidden">
                <iframe :src="chartUrl(currentExecutingRound, currentStepIndex, c)" style="width: 100%; height: 400px; border: none" />
              </div>
            </div>
            <div v-else style="color: #999; display: flex; align-items: center; justify-content: center; height: 100%">
              在对话区描述你的分析需求，Agent 将为你规划步骤
            </div>
          </div>
        </div>

        <!-- 右栏: 分析步骤 (25%) -->
        <div style="width: 25%; border: 1px solid #eee; border-radius: 8px; display: flex; flex-direction: column">
          <div style="padding: 8px 12px; font-weight: 600; border-bottom: 1px solid #eee; font-size: 14px">📋 分析步骤</div>
          <div style="flex: 1; overflow-y: auto; padding: 8px">
            <div v-if="!projectStore.steps.length" style="color: #999; text-align: center; margin-top: 20px; font-size: 13px">
              暂无分析步骤
            </div>
            <div v-for="(step, i) in projectStore.steps" :key="i"
                 :style="{
                   padding: '6px 8px', margin: '2px 0', borderRadius: '4px', fontSize: '13px',
                   borderLeft: i === projectStore.viewingStepIndex ? '3px solid #1a73e8' : '3px solid #e0e0e0',
                   background: i === projectStore.viewingStepIndex ? '#e8f0fe' : 'transparent'
                 }">
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span>
                  <span v-if="step.status === 'done'">✓</span>
                  <span v-else-if="step.status === 'running'">⟳</span>
                  <span v-else-if="step.status === 'error'">✗</span>
                  <span v-else>○</span>
                  <b>步骤 {{ i + 1 }}</b>: {{ (step.description || '').slice(0, 30) }}...
                </span>
              </div>
              <div v-if="step.status === 'pending' || step.status === 'done'" style="display: flex; gap: 4px; margin-top: 4px">
                <el-button v-if="step.status === 'pending'" size="small" @click="runStep(i)" :loading="executingIndex === i">
                  ▶ 执行
                </el-button>
                <el-button v-if="step.status === 'done'" size="small" @click="viewStep(i)">查看</el-button>
              </div>
            </div>
            <div v-if="projectStore.steps.length && projectStore.steps.every(s => s.status === 'done')"
                 style="margin-top: 12px">
              <el-alert title="当前轮次所有步骤已完成！" type="success" :closable="false" style="font-size: 12px" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 项目信息弹窗 -->
    <el-dialog v-model="showProjectInfo" title="📋 项目信息" width="400px">
      <el-descriptions v-if="projectInfo" :column="2" border size="small">
        <el-descriptions-item label="名称">{{ projectInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ (projectInfo.created_at || '').slice(0, 19) }}</el-descriptions-item>
        <el-descriptions-item label="数据文件">{{ projectInfo.data_files_count }} 个</el-descriptions-item>
        <el-descriptions-item label="总行数">{{ (projectInfo.total_rows || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="分析步骤">{{ projectInfo.steps_count }} 个</el-descriptions-item>
        <el-descriptions-item label="报告数">{{ projectInfo.reports_count }} 个</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 上传数据弹窗 -->
    <el-dialog v-model="showUploadDialog" title="📤 向当前项目追加数据" width="500px">
      <el-upload drag :auto-upload="false" :on-change="handleUploadFile" accept=".csv,.xlsx,.xls" :limit="1">
        <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
      </el-upload>
      <div v-if="uploading" style="text-align: center; margin-top: 10px">上传中...</div>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :disabled="!pendingUploadFile2" :loading="uploading">确认追加</el-button>
      </template>
    </el-dialog>

    <!-- 报告导出弹窗 -->
    <el-dialog v-model="showReportDialog" title="📋 导出分析报告" width="550px">
      <el-input v-model="reportTitle" placeholder="报告标题" style="margin-bottom: 16px" />

      <div style="margin-bottom: 12px; font-size: 13px; color: #666">
        包含内容 (所有轮次已完成步骤):
      </div>
      <el-checkbox-group v-model="reportSelectedSteps" style="display: flex; flex-direction: column; gap: 4px">
        <el-checkbox v-for="(s, i) in allDoneStepsFlat" :key="i" :value="i"
                     :label="(s.description || '').slice(0, 50)" style="font-size: 13px" />
      </el-checkbox-group>

      <el-checkbox v-model="reportIncludeConclusion" style="margin: 12px 0">AI 综合分析结论</el-checkbox>

      <el-input v-model="reportUserNotes" type="textarea" :rows="3" placeholder="工程师补充观点（可选）"
                style="margin-bottom: 16px" />

      <template #footer>
        <el-button @click="showReportDialog = false">取消</el-button>
        <el-button type="primary" @click="generateAndPreview" :loading="generatingReport" :disabled="!reportSelectedSteps.length">
          🤖 AI 结论并预览
        </el-button>
        <el-button type="success" @click="exportReport" :loading="generatingReport" :disabled="!reportSelectedSteps.length">
          ⬇ 导出 HTML
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  getProjectInfo, addDataFile, generateReport,
  streamPlan, streamExecute, streamConclude,
} from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'
import DOMPurify from 'dompurify'
import ReportPreview from './ReportPreview.vue'

const projectStore = useProjectStore()

const userInput = ref('')
const sending = ref(false)
const executingIndex = ref(-1)
const currentStepIndex = ref(-1)
const currentExecutingRound = ref(-1)
const viewingRoundIndex = ref(-1)
const streamingResponse = ref('')
const currentResult = ref(null)

const showProjectInfo = ref(false)
const projectInfo = ref(null)

const showUploadDialog = ref(false)
const pendingUploadFile2 = ref(null)
const uploading = ref(false)

const showReportDialog = ref(false)
const reportTitle = ref('')
const reportSelectedSteps = ref([])
const reportIncludeConclusion = ref(true)
const reportUserNotes = ref('')
const generatingReport = ref(false)

const viewingStep = computed(() => {
  const idx = projectStore.viewingStepIndex
  if (idx >= 0 && idx < projectStore.steps.length) {
    return projectStore.steps[idx]
  }
  return {}
})

watch(() => projectStore.currentRound, () => {
  viewingRoundIndex.value = -1
  currentExecutingRound.value = -1
  currentResult.value = null
  currentStepIndex.value = -1
})

const allDoneStepsFlat = computed(() => {
  const result = []
  for (const r of projectStore.rounds) {
    for (const s of (r.steps || [])) {
      if (s.status === 'done') {
        result.push({ ...s, round_user_input: r.user_input || '' })
      }
    }
  }
  return result
})

const chartUrl = (roundIdx, stepIdx, chartNum) =>
  `/api/projects/${projectStore.currentId}/charts/round${roundIdx}_step${stepIdx + 1}_chart${chartNum}.html`

const sendMessage = async () => {
  if (!userInput.value.trim()) return
  const msg = userInput.value.trim()
  userInput.value = ''
  projectStore.addChatMessage({ role: 'user', content: msg })

  sending.value = true
  streamingResponse.value = ''
  try {
    await streamPlan(
      projectStore.currentId, msg,
      (chunk) => { streamingResponse.value += chunk },
      (steps, roundIndex) => {
        if (!steps || !steps.length) {
          ElMessage.warning('AI 未能生成有效的分析计划，请尝试换一种描述方式')
        } else {
          projectStore.addRound(msg, streamingResponse.value, steps)
        }
        projectStore.addChatMessage({ role: 'assistant', content: streamingResponse.value })
        streamingResponse.value = ''
        projectStore.viewingStepIndex = -1
        viewingRoundIndex.value = -1
      }
    )
  } catch (e) {
    ElMessage.error('请求失败: ' + e.message)
  } finally {
    sending.value = false
  }
}

const runStep = async (index) => {
  projectStore.updateStep(index, { status: 'running' })
  executingIndex.value = index
  currentExecutingRound.value = projectStore.currentRound
  currentResult.value = null
  streamingResponse.value = ''

  try {
    await streamExecute(
      projectStore.currentId, index,
      (chunk) => { streamingResponse.value += chunk },
      (text, chartCount) => { currentResult.value = { text, chart_count: chartCount }; currentStepIndex.value = index },
      (error) => {
        if (error) {
          projectStore.updateStep(index, { status: 'error' })
          ElMessage.error('执行失败: ' + error)
        } else {
          projectStore.updateStep(index, {
            status: 'done',
            llm_explanation: streamingResponse.value,
            last_text: currentResult.value?.text || '',
            chart_count: currentResult.value?.chart_count || 0,
          })
          if (currentResult.value) {
            currentResult.value.llm_explanation = streamingResponse.value
          }
          streamingResponse.value = ''
        }
      }
    )
  } catch (e) {
    projectStore.updateStep(index, { status: 'error' })
    ElMessage.error('执行失败: ' + e.message)
  } finally {
    executingIndex.value = -1
  }
}

const viewStep = (index) => {
  projectStore.viewingStepIndex = index
  viewingRoundIndex.value = projectStore.currentRound
  currentResult.value = null
}

const loadProjectInfo = async () => {
  if (!projectStore.currentId) return
  try {
    const res = await getProjectInfo(projectStore.currentId)
    projectInfo.value = res.data
  } catch (e) {
    ElMessage.error('加载项目信息失败')
  }
}

const handleUploadFile = (file) => {
  pendingUploadFile2.value = file.raw
}

const confirmUpload = async () => {
  if (!pendingUploadFile2.value) return
  uploading.value = true
  try {
    const res = await addDataFile(projectStore.currentId, pendingUploadFile2.value)
    projectStore.dataFiles = res.data.data_files
    projectStore.selectedDataFiles = res.data.data_files.map(f => f.name)
    showUploadDialog.value = false
    pendingUploadFile2.value = null
    ElMessage.success('数据已追加，请重新描述分析需求以使用新数据')
  } catch (e) {
    ElMessage.error('追加失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

const openReportDialog = () => {
  reportTitle.value = `${projectStore.currentName} — 分析报告`
  reportSelectedSteps.value = allDoneStepsFlat.value.map((_, i) => i)
  reportIncludeConclusion.value = true
  reportUserNotes.value = ''
  showReportDialog.value = true
}

const generateAndPreview = async () => {
  const stepIndices = reportSelectedSteps.value
  generatingReport.value = true
  showReportDialog.value = false

  try {
    let conclusionText = ''
    if (reportIncludeConclusion.value) {
      try {
        await streamConclude(
          projectStore.currentId, stepIndices, reportUserNotes.value,
          (chunk) => { conclusionText += chunk },
          () => {}
        )
      } catch (e) {
        ElMessage.warning('AI 结论生成失败，将继续导出无结论的报告')
      }
    }

    await generateReport(
      projectStore.currentId, reportTitle.value,
      stepIndices, reportUserNotes.value, true, conclusionText,
    )
    projectStore.reportPreviewMode = true
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    generatingReport.value = false
  }
}

const exportReport = async () => {
  generatingReport.value = true
  try {
    const res = await generateReport(
      projectStore.currentId, reportTitle.value,
      reportSelectedSteps.value, reportUserNotes.value, false,
    )
    ElMessage.success('报告已保存: ' + res.data.path)
    showReportDialog.value = false
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    generatingReport.value = false
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
  let html = text
    .replace(/### (.+)/g, '<h4>$1</h4>')
    .replace(/## (.+)/g, '<h3>$1</h3>')
    .replace(/- (.+)/g, '<li>$1</li>')
    .replace(/```json\n?([\s\S]*?)```/g, '<pre style="background:#f5f5f5;padding:8px;border-radius:4px;font-size:12px">$1</pre>')
    .replace(/\n\n/g, '<br/><br/>')
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['h3', 'h4', 'li', 'pre', 'br', 'strong', 'em', 'code', 'b', 'i', 'ul', 'ol', 'p', 'span'],
    ALLOWED_ATTRS: ['style'],
  })
}
</script>

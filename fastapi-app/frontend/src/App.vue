<template>
  <el-container style="height: 100vh">
    <el-aside width="240px" style="background: #fafafa; border-right: 1px solid #eee; display: flex; flex-direction: column">
      <!-- 标题 -->
      <div style="padding: 20px 20px 10px; font-size: 18px; font-weight: bold; color: #1a73e8">
        📊 数据科学家 Agent
      </div>

      <!-- 主导航 (3 项) -->
      <el-menu :default-active="currentRoute" router style="border-right: none">
        <el-menu-item index="/">
          <span>🆕 新建项目</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <span>🔬 分析对话</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>⚙ 设置</span>
        </el-menu-item>
      </el-menu>

      <el-divider style="margin: 8px 0" />

      <!-- 当前项目 -->
      <div v-if="projectStore.currentName" style="padding: 4px 20px; color: #999; font-size: 12px">
        当前项目: {{ projectStore.currentName }}
      </div>

      <!-- 三个折叠面板 -->
      <div style="flex: 1; overflow-y: auto; padding: 0 8px">

        <!-- 📂 数据列表 -->
        <el-collapse v-model="activePanels" style="border: none">
          <el-collapse-item title="📂 数据列表" name="dataList">
            <div v-if="!projectStore.currentId" style="color: #999; font-size: 13px; padding: 4px 8px">
              请先选择或创建项目
            </div>
            <div v-else-if="!projectStore.dataFiles.length" style="color: #999; font-size: 13px; padding: 4px 8px">
              暂无数据，请上传
            </div>
            <div v-else style="padding: 0 4px">
              <div style="margin-bottom: 4px">
                <el-button size="small" @click="selectAll">全选</el-button>
                <el-button size="small" @click="selectNone">取消全选</el-button>
              </div>
              <el-checkbox-group v-model="projectStore.selectedDataFiles" style="display: flex; flex-direction: column">
                <el-checkbox v-for="f in projectStore.dataFiles" :key="f.name" :value="f.name" :label="f.name" style="margin-left: 4px">
                  {{ f.name }} ({{ f.rows.toLocaleString() }} 行)
                </el-checkbox>
              </el-checkbox-group>
              <div style="color: #999; font-size: 12px; margin-top: 4px">
                已选 {{ projectStore.selectedDataFiles.length }} 个文件，合计 {{ projectStore.totalRows.toLocaleString() }} 行
              </div>
              <el-button size="small" style="margin-top: 8px; width: 100%" @click="uploadDialogVisible = true">
                + 上传新数据
              </el-button>
            </div>
          </el-collapse-item>

          <!-- 📁 历史项目 -->
          <el-collapse-item title="📁 历史项目" name="historyProjects">
            <div v-if="!projects.length" style="color: #999; font-size: 13px; padding: 4px 8px">
              暂无项目
            </div>
            <div v-else style="max-height: 300px; overflow-y: auto">
              <div v-for="p in projects" :key="p.id"
                   @click="openProject(p)"
                   :style="{
                     padding: '8px 12px', cursor: 'pointer', borderRadius: '4px', marginBottom: '2px',
                     background: p.id === projectStore.currentId ? '#e8f0fe' : 'transparent',
                     borderLeft: p.id === projectStore.currentId ? '3px solid #1a73e8' : '3px solid transparent'
                   }">
                <div style="font-size: 13px; font-weight: 500">{{ p.name }}</div>
                <div style="font-size: 11px; color: #999">{{ p.created_at?.slice(0, 10) }}</div>
              </div>
            </div>
          </el-collapse-item>

          <!-- 📋 历史报告 -->
          <el-collapse-item title="📋 历史报告" name="historyReports">
            <div v-if="!projectStore.currentId" style="color: #999; font-size: 13px; padding: 4px 8px">
              请先选择或创建项目
            </div>
            <div v-else-if="!reports.length" style="color: #999; font-size: 13px; padding: 4px 8px">
              暂无报告
            </div>
            <div v-else style="max-height: 300px; overflow-y: auto">
              <div v-for="r in reports" :key="r.name" style="padding: 4px 8px; font-size: 13px">
                📄 {{ r.name }}
                <div style="font-size: 11px; color: #999">{{ r.created_at }}</div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-main style="overflow-y: auto">
      <router-view />
    </el-main>
  </el-container>

  <!-- 上传数据弹窗 -->
  <el-dialog v-model="uploadDialogVisible" title="📤 向当前项目追加数据" width="500px">
    <p style="color: #999; font-size: 13px">新数据将与已有数据按列名匹配、按行拼接</p>
    <el-upload
      drag
      :auto-upload="false"
      :on-change="handleUploadFile"
      accept=".csv,.xlsx,.xls"
      :limit="1"
      style="margin-top: 16px"
    >
      <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
    </el-upload>
    <div v-if="uploading" style="text-align: center; margin-top: 10px">
      <el-icon class="is-loading"><i class="el-icon-loading" /></el-icon> 上传中...
    </div>
    <template #footer>
      <el-button @click="uploadDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="confirmUpload" :disabled="!pendingUploadFile" :loading="uploading">
        确认追加
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from './stores/project'
import { listProjects, getProject, listDataFiles, addDataFile, mergeDataFiles, listReports } from './api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const currentRoute = computed(() => route.path)

const activePanels = ref([])
const projects = ref([])
const reports = ref([])

// 上传弹窗
const uploadDialogVisible = ref(false)
const pendingUploadFile = ref(null)
const uploading = ref(false)

onMounted(async () => {
  try {
    const res = await listProjects()
    projects.value = res.data
  } catch (e) { /* */ }
})

// 数据列表操作
const selectAll = () => {
  projectStore.selectedDataFiles = projectStore.dataFiles.map(f => f.name)
}
const selectNone = () => {
  projectStore.selectedDataFiles = []
}

// 数据文件选择变化时自动合并
watch(() => projectStore.selectedDataFiles, async (newVal) => {
  if (!newVal.length || !projectStore.currentId) return
  try {
    await mergeDataFiles(projectStore.currentId, newVal)
  } catch (e) {
    ElMessage.error('数据合并失败: ' + e.message)
  }
}, { deep: true })

// 打开历史项目
const openProject = async (p) => {
  if (p.id === projectStore.currentId) return
  try {
    const res = await getProject(p.id)
    projectStore.clearProject()
    projectStore.setProject(p.id, p.name)
    projectStore.setRounds(res.data.state?.rounds || [], res.data.state?.current_round ?? -1)
    projectStore.chatHistory = res.data.chat_history || []
    projectStore.dataFiles = res.data.data_files || []
    projectStore.selectedDataFiles = (res.data.data_files || []).map(f => f.name)

    const rRes = await listReports(p.id)
    reports.value = rRes.data

    router.push('/analysis')
    ElMessage.success(`已打开项目: ${p.name}`)
  } catch (e) {
    ElMessage.error('打开失败: ' + e.message)
  }
}

// 上传数据
const handleUploadFile = (file) => {
  pendingUploadFile.value = file.raw
}

const confirmUpload = async () => {
  if (!pendingUploadFile.value) return
  uploading.value = true
  try {
    const res = await addDataFile(projectStore.currentId, pendingUploadFile.value)
    projectStore.dataFiles = res.data.data_files
    projectStore.selectedDataFiles = res.data.data_files.map(f => f.name)
    uploadDialogVisible.value = false
    pendingUploadFile.value = null
    ElMessage.success('数据已追加')
  } catch (e) {
    ElMessage.error('追加失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}
</script>

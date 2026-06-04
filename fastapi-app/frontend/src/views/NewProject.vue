<template>
  <div>
    <h2>🆕 新建项目</h2>
    <div v-if="projectStore.currentName" style="margin-bottom: 15px">
      <el-tag type="info">当前项目: {{ projectStore.currentName }}</el-tag>
    </div>

    <el-input v-model="projectName" placeholder="输入项目名称..." style="width: 400px; margin-bottom: 16px" />

    <el-upload
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      accept=".csv,.xlsx,.xls,.json,.tsv"
      :limit="1"
    >
      <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
      <div class="el-upload__tip">支持 CSV、Excel、JSON 格式</div>
    </el-upload>

    <div v-if="uploadResult" style="margin-top: 20px">
      <h3>数据预览</h3>
      <el-table :data="uploadResult.preview" border stripe max-height="400" style="width: 100%">
        <el-table-column
          v-for="col in uploadResult.columns" :key="col" :prop="col" :label="col"
          min-width="120"
        />
      </el-table>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6">
          <el-statistic title="行数" :value="uploadResult.shape[0]" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="列数" :value="uploadResult.shape[1]" />
        </el-col>
      </el-row>

      <div style="margin-top: 20px">
        <el-button type="primary" @click="createProject" :loading="creating" :disabled="!projectName">
          创建并开始分析
        </el-button>
        <span v-if="!projectName" style="color: #999; margin-left: 10px; font-size: 13px">请先输入项目名称</span>
      </div>
    </div>

    <div v-if="!selectedFile" style="color: #999; margin-top: 10px; font-size: 13px">
      请先上传数据文件（必须上传数据才能创建项目）
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { uploadData, createProject as apiCreateProject } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()

const projectName = ref('')
const selectedFile = ref(null)
const uploadResult = ref(null)
const creating = ref(false)

const handleFileChange = async (file) => {
  selectedFile.value = file.raw
  try {
    const res = await uploadData(file.raw)
    uploadResult.value = res.data
    if (!projectName.value) {
      projectName.value = file.name.replace(/\.[^.]+$/, '')
    }
  } catch (e) {
    ElMessage.error('文件上传失败: ' + e.message)
  }
}

const createProject = async () => {
  if (!projectName.value || !selectedFile.value) return
  creating.value = true
  try {
    const res = await apiCreateProject(projectName.value, selectedFile.value)
    projectStore.clearProject()
    projectStore.setProject(res.data.project_id, projectName.value)
    projectStore.dataFiles = res.data.data_files || []
    projectStore.selectedDataFiles = (res.data.data_files || []).map(f => f.name)
    ElMessage.success('项目创建成功，正在进入分析对话...')
    router.push('/analysis')
  } catch (e) {
    ElMessage.error('创建失败: ' + e.message)
  } finally {
    creating.value = false
  }
}
</script>

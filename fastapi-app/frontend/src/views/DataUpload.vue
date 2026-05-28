<template>
  <div>
    <h2>📂 数据上传</h2>
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
        <el-input v-model="projectName" placeholder="项目名称" style="width: 300px" />
        <el-button type="primary" @click="createProject" style="margin-left: 10px"
                   :loading="creating">
          创建分析项目
        </el-button>
      </div>
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

const selectedFile = ref(null)
const uploadResult = ref(null)
const projectName = ref('')
const creating = ref(false)

const handleFileChange = async (file) => {
  selectedFile.value = file.raw
  const res = await uploadData(file.raw)
  uploadResult.value = res.data
  projectName.value = file.name.replace(/\.[^.]+$/, '')
}

const createProject = async () => {
  creating.value = true
  try {
    const res = await apiCreateProject(projectName.value, selectedFile.value)
    projectStore.setProject(res.data.project_id, projectName.value, uploadResult.value)
    ElMessage.success('项目创建成功')
    router.push('/analysis')
  } catch (e) {
    ElMessage.error('创建失败: ' + e.message)
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div>
    <h2>📁 历史项目</h2>
    <el-input v-model="search" placeholder="搜索项目..." style="width: 300px; margin-bottom: 20px" clearable />

    <div v-if="!filteredProjects.length" style="color: #999">暂无项目</div>

    <el-card v-for="p in filteredProjects" :key="p.id" style="margin-bottom: 15px">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <h3 style="margin: 0">📊 {{ p.name }}</h3>
          <div style="color: #999; font-size: 13px; margin-top: 5px">
            创建: {{ p.created_at?.slice(0, 10) }} | {{ p.steps_count }} 个步骤
            <span v-if="p.data_file"> | 数据: {{ p.data_file }}</span>
          </div>
        </div>
        <div>
          <el-button @click="openProject(p)">打开</el-button>
          <el-button type="danger" plain @click="removeProject(p.id)">删除</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, getProject, deleteProject } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()
const projects = ref([])
const search = ref('')

onMounted(async () => {
  const res = await listProjects()
  projects.value = res.data
})

const filteredProjects = computed(() =>
  search.value
    ? projects.value.filter(p => p.name.includes(search.value))
    : projects.value
)

const openProject = async (p) => {
  const res = await getProject(p.id)
  projectStore.setProject(p.id, p.name, res.data.data_info)
  router.push('/analysis')
}

const removeProject = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除此项目？', '确认', { type: 'warning' })
    await deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
    ElMessage.success('已删除')
  } catch (e) { /* cancelled */ }
}
</script>

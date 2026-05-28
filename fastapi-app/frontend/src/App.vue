<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #fafafa; border-right: 1px solid #eee">
      <div style="padding: 20px; font-size: 18px; font-weight: bold; color: #1a73e8">
        📊 数据科学家 Agent
      </div>
      <el-menu :default-active="currentRoute" router>
        <el-menu-item index="/">
          <span>📂 数据上传</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <span>🔬 分析对话</span>
        </el-menu-item>
        <el-menu-item index="/report">
          <span>📋 报告导出</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>⚙ 设置</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <span>📁 历史项目</span>
        </el-menu-item>
      </el-menu>
      <div style="padding: 10px 20px; color: #999; font-size: 12px; position: absolute; bottom: 10px">
        <span v-if="projectStore.currentName">当前: {{ projectStore.currentName }}</span>
      </div>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from './stores/project'

const route = useRoute()
const projectStore = useProjectStore()
const currentRoute = computed(() => route.path)
</script>

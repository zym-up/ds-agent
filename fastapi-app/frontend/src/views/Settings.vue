<template>
  <div>
    <h2>⚙ 设置</h2>
    <el-card style="max-width: 600px">
      <el-form :model="config" label-width="120px">
        <el-form-item label="预设模板">
          <el-select v-model="preset" @change="applyPreset">
            <el-option label="DeepSeek — deepseek-chat" value="deepseek" />
            <el-option label="Qwen — qwen-plus" value="qwen" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务名称">
          <el-input v-model="config.name" />
        </el-form-item>
        <el-form-item label="API 地址">
          <el-input v-model="config.base_url" placeholder="https://your-internal-api/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="config.api_key" type="password" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="config.model" />
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="config.temperature" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="最大 Token">
          <el-input-number v-model="config.max_tokens" :min="512" :max="16384" :step="512" />
        </el-form-item>
        <el-form-item>
          <el-button @click="testConnection">测试连接</el-button>
          <el-button type="primary" @click="saveSettings">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, saveConfig, testConnection as apiTest } from '../api'
import { ElMessage } from 'element-plus'

const config = ref({
  name: '', base_url: '', api_key: '', model: '',
  temperature: 0.3, max_tokens: 4096
})
const preset = ref('deepseek')

const presets = {
  deepseek: { name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  qwen: { name: 'Qwen', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  custom: { name: '自定义', base_url: '', model: '' },
}

onMounted(async () => {
  try {
    const res = await getConfig()
    Object.assign(config.value, res.data.llm)
  } catch (e) { /* use defaults */ }
})

const applyPreset = () => {
  Object.assign(config.value, presets[preset.value])
}

const testConnection = async () => {
  try {
    const res = await apiTest(config.value)
    if (res.data.success) ElMessage.success('连接成功: ' + res.data.message)
    else ElMessage.error('连接失败: ' + res.data.message)
  } catch (e) { ElMessage.error('连接失败: ' + e.message) }
}

const saveSettings = async () => {
  try {
    await saveConfig(config.value)
    ElMessage.success('配置已保存')
  } catch (e) { ElMessage.error('保存失败: ' + e.message) }
}
</script>

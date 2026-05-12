<template>
  <div class="recommendation-page">
    <!-- 输入区域 -->
    <el-card class="input-card" v-if="!taskId">
      <h2>输入学习需求</h2>
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="6"
        placeholder="例如：我想学习 Redis 缓存穿透、缓存击穿、缓存雪崩，还有布隆过滤器和分布式锁。"
      />
      <div class="config-options">
        <el-checkbox v-model="config.include_video">包含视频</el-checkbox>
        <el-checkbox v-model="config.include_articles">包含文章</el-checkbox>
        <el-checkbox v-model="config.include_official_docs">包含官方文档</el-checkbox>
        <el-checkbox v-model="config.include_github">包含 GitHub 项目</el-checkbox>
        <el-checkbox v-model="config.include_practice_tasks">生成练习任务</el-checkbox>
      </div>
      <el-button type="primary" size="large" @click="createTask" :loading="loading">
        生成资源推荐
      </el-button>
    </el-card>

    <!-- 任务状态 -->
    <el-card class="status-card" v-if="taskId && status !== 'COMPLETED'">
      <h2>正在生成资源推荐...</h2>
      <el-progress :percentage="progress" :status="status === 'FAILED' ? 'exception' : undefined" />
      <p class="current-step">{{ currentStep }}</p>
      <p class="error-message" v-if="errorMessage">{{ errorMessage }}</p>
      <el-button @click="reset">重新开始</el-button>
    </el-card>

    <!-- 推荐结果 -->
    <div v-if="status === 'COMPLETED' && result">
      <el-card class="result-header">
        <h2>学习资源推荐</h2>
        <el-button @click="reset">重新生成</el-button>
      </el-card>

      <!-- 学习主题 -->
      <el-card class="topics-card">
        <h3>识别出的学习主题</h3>
        <el-tag
          v-for="topic in result.topics"
          :key="topic.id"
          :type="getPriorityType(topic.priority)"
          size="large"
          class="topic-tag"
        >
          {{ topic.normalized_topic || topic.raw_text }}
        </el-tag>
      </el-card>

      <!-- 学习路径 -->
      <el-card class="learning-path-card" v-if="result.learning_path">
        <h3>学习路径</h3>
        <LearningPath :learning-path="result.learning_path" />
      </el-card>

      <!-- 推荐资源 -->
      <el-card class="resources-card">
        <h3>推荐资源 ({{ result.resources.length }})</h3>
        <div class="resources-grid">
          <ResourceCard
            v-for="resource in result.resources"
            :key="resource.id"
            :resource="resource"
          />
        </div>
      </el-card>

      <!-- 练习任务 -->
      <el-card class="practice-tasks-card" v-if="result.practice_tasks && result.practice_tasks.length > 0">
        <h3>练习任务</h3>
        <PracticeTask
          v-for="task in result.practice_tasks"
          :key="task.id"
          :task="task"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { recommendationApi } from '../api'
import ResourceCard from '../components/ResourceCard.vue'
import LearningPath from '../components/LearningPath.vue'
import PracticeTask from '../components/PracticeTask.vue'

const userInput = ref('')
const config = ref({
  include_video: true,
  include_articles: true,
  include_official_docs: true,
  include_github: true,
  include_practice_tasks: true,
})

const loading = ref(false)
const taskId = ref(null)
const status = ref('')
const currentStep = ref('')
const progress = ref(0)
const errorMessage = ref('')
const result = ref(null)

let pollTimer = null

const createTask = async () => {
  if (!userInput.value.trim()) {
    ElMessage.warning('请输入学习需求')
    return
  }

  loading.value = true
  try {
    const response = await recommendationApi.createTask({
      user_input: userInput.value,
      ...config.value,
    })

    if (response.data.code === 0) {
      taskId.value = response.data.data.task_id
      status.value = response.data.data.status
      startPolling()
      ElMessage.success('任务已创建，正在生成推荐...')
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    ElMessage.error('创建任务失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  pollTimer = setInterval(async () => {
    try {
      const response = await recommendationApi.getTaskStatus(taskId.value)
      if (response.data.code === 0) {
        const data = response.data.data
        status.value = data.status
        currentStep.value = data.current_step
        progress.value = data.progress
        errorMessage.value = data.error_message

        if (data.status === 'COMPLETED') {
          stopPolling()
          await loadResult()
        } else if (data.status === 'FAILED') {
          stopPolling()
          ElMessage.error('推荐失败')
        }
      }
    } catch (error) {
      console.error('轮询失败', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const loadResult = async () => {
  try {
    const response = await recommendationApi.getResult(taskId.value)
    if (response.data.code === 0) {
      result.value = response.data.data
      ElMessage.success('推荐完成！')
    }
  } catch (error) {
    ElMessage.error('加载结果失败')
    console.error(error)
  }
}

const reset = () => {
  stopPolling()
  taskId.value = null
  status.value = ''
  currentStep.value = ''
  progress.value = 0
  errorMessage.value = ''
  result.value = null
  userInput.value = ''
}

const getPriorityType = (priority) => {
  const map = {
    high: 'danger',
    medium: 'warning',
    low: 'info',
  }
  return map[priority] || 'info'
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.recommendation-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.input-card:hover {
  box-shadow: 0 12px 48px rgba(102, 126, 234, 0.2);
}

.input-card h2,
.status-card h2,
.result-header h2 {
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.config-options {
  margin: 24px 0;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7ff 0%, #f0f4ff 100%);
  border-radius: 12px;
}

.config-options :deep(.el-checkbox) {
  font-weight: 500;
  color: #555;
}

.input-card :deep(.el-button--primary) {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.input-card :deep(.el-button--primary):hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.input-card :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  font-size: 15px;
  line-height: 1.6;
  transition: all 0.3s ease;
}

.input-card :deep(.el-textarea__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.status-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.status-card :deep(.el-progress) {
  margin: 30px 0;
}

.current-step {
  margin-top: 20px;
  color: #666;
  font-size: 15px;
  font-weight: 500;
}

.error-message {
  margin-top: 16px;
  color: #f56c6c;
  font-weight: 500;
  padding: 12px;
  background: #fef0f0;
  border-radius: 8px;
}

.result-header {
  background: white;
  border-radius: 20px;
  padding: 30px 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
}

.topics-card,
.learning-path-card,
.resources-card,
.practice-tasks-card {
  background: white;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.topics-card h3,
.learning-path-card h3,
.resources-card h3,
.practice-tasks-card h3 {
  margin-bottom: 24px;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.topics-card h3::before {
  content: '🏷️';
  font-size: 24px;
}

.learning-path-card h3::before {
  content: '🗺️';
  font-size: 24px;
}

.resources-card h3::before {
  content: '📚';
  font-size: 24px;
}

.practice-tasks-card h3::before {
  content: '✍️';
  font-size: 24px;
}

.topic-tag {
  margin-right: 12px;
  margin-bottom: 12px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 20px;
  transition: all 0.2s ease;
}

.topic-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .input-card,
  .status-card,
  .result-header,
  .topics-card,
  .learning-path-card,
  .resources-card,
  .practice-tasks-card {
    padding: 24px;
    border-radius: 16px;
  }

  .resources-grid {
    grid-template-columns: 1fr;
  }

  .config-options {
    gap: 16px;
  }
}
</style>

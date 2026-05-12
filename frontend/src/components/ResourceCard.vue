<template>
  <div class="resource-card" @click="handleCardClick">
    <div class="card-inner">
      <div class="resource-header">
        <el-tag :type="getTypeColor(resource.resource_type)" size="small" effect="dark" class="type-tag">
          {{ getTypeLabel(resource.resource_type) }}
        </el-tag>
        <el-tag v-if="resource.difficulty" size="small" effect="plain" class="difficulty-tag">
          {{ getDifficultyLabel(resource.difficulty) }}
        </el-tag>
      </div>

      <h4 class="resource-title">
        <a :href="resource.url" target="_blank" @click.stop>{{ resource.title }}</a>
      </h4>

      <p class="resource-summary" v-if="resource.summary">{{ resource.summary }}</p>

      <div class="resource-reason" v-if="resource.reason">
        <el-icon class="reason-icon"><InfoFilled /></el-icon>
        <span>{{ resource.reason }}</span>
      </div>

      <div class="resource-footer">
        <div class="resource-meta">
          <span v-if="resource.estimated_minutes" class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ resource.estimated_minutes }} 分钟
          </span>
          <span v-if="resource.final_score" class="meta-item">
            <el-icon><Star /></el-icon>
            {{ resource.final_score.toFixed(1) }}
          </span>
        </div>

        <div class="resource-actions">
          <el-button
            :type="studied ? 'success' : 'default'"
            size="small"
            @click.stop="toggleStudied"
            class="action-btn"
          >
            <el-icon><Check /></el-icon>
            {{ studied ? '已学习' : '标记' }}
          </el-button>
          <el-button
            :type="favorite ? 'warning' : 'default'"
            size="small"
            @click.stop="toggleFavorite"
            class="action-btn"
          >
            <el-icon><Star /></el-icon>
            {{ favorite ? '已收藏' : '收藏' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { resourceApi } from '../api'

const props = defineProps({
  resource: {
    type: Object,
    required: true,
  },
})

const studied = ref(false)
const favorite = ref(false)

const handleCardClick = () => {
  // Card click handler for future enhancements
}

const getTypeColor = (type) => {
  const map = {
    video: 'danger',
    article: 'primary',
    official_doc: 'success',
    github: 'warning',
  }
  return map[type] || 'info'
}

const getTypeLabel = (type) => {
  const map = {
    video: '🎥 视频',
    article: '📄 文章',
    official_doc: '📚 官方文档',
    github: '💻 GitHub',
    doc: '📖 文档',
    course: '🎓 课程',
    qa: '💬 问答',
  }
  return map[type] || '📌 资源'
}

const getDifficultyLabel = (difficulty) => {
  const map = {
    basic: '⭐ 基础',
    medium: '⭐⭐ 中级',
    advanced: '⭐⭐⭐ 高级',
  }
  return map[difficulty] || difficulty
}

const toggleStudied = async () => {
  try {
    await resourceApi.markStudied(props.resource.id, !studied.value)
    studied.value = !studied.value
    ElMessage.success(studied.value ? '✅ 已标记为已学习' : '已取消标记')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const toggleFavorite = async () => {
  try {
    await resourceApi.favorite(props.resource.id, !favorite.value)
    favorite.value = !favorite.value
    ElMessage.success(favorite.value ? '⭐ 已收藏' : '已取消收藏')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.resource-card {
  height: 100%;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  position: relative;
}

.resource-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.resource-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.25);
}

.resource-card:hover::before {
  transform: scaleX(1);
}

.card-inner {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.resource-header {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.type-tag {
  font-weight: 600;
  border-radius: 8px;
  padding: 4px 12px;
}

.difficulty-tag {
  border-radius: 8px;
  padding: 4px 12px;
}

.resource-title {
  font-size: 18px;
  margin-bottom: 12px;
  line-height: 1.5;
  font-weight: 600;
  color: #1a1a1a;
}

.resource-title a {
  color: inherit;
  text-decoration: none;
  transition: color 0.2s ease;
}

.resource-title a:hover {
  color: #667eea;
}

.resource-summary {
  font-size: 14px;
  color: #666;
  margin-bottom: 16px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-grow: 1;
}

.resource-reason {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f5f7ff 0%, #f0f4ff 100%);
  border-radius: 12px;
  font-size: 13px;
  color: #555;
  margin-bottom: 16px;
  border-left: 3px solid #667eea;
  line-height: 1.6;
}

.reason-icon {
  color: #667eea;
  margin-top: 2px;
  flex-shrink: 0;
}

.resource-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.resource-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #888;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.resource-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: scale(1.05);
}

@media (max-width: 768px) {
  .card-inner {
    padding: 20px;
  }

  .resource-title {
    font-size: 16px;
  }
}
</style>

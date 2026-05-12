<template>
  <div class="practice-task">
    <div class="task-header">
      <el-tag :type="getDifficultyType(task.difficulty)" size="small" effect="dark" class="difficulty-tag">
        {{ getDifficultyLabel(task.difficulty) }}
      </el-tag>
      <el-tag size="small" effect="plain" class="type-tag">
        {{ getTaskTypeLabel(task.task_type) }}
      </el-tag>
    </div>

    <p class="task-text">{{ task.task_text }}</p>

    <el-collapse v-if="task.reference_answer" class="answer-collapse">
      <el-collapse-item name="1">
        <template #title>
          <span class="collapse-title">💡 查看参考答案</span>
        </template>
        <div class="reference-answer">{{ task.reference_answer }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
const props = defineProps({
  task: {
    type: Object,
    required: true,
  },
})

const getDifficultyType = (difficulty) => {
  const map = {
    basic: 'success',
    medium: 'warning',
    advanced: 'danger',
  }
  return map[difficulty] || 'info'
}

const getDifficultyLabel = (difficulty) => {
  const map = {
    basic: '⭐ 基础',
    medium: '⭐⭐ 中级',
    advanced: '⭐⭐⭐ 高级',
  }
  return map[difficulty] || difficulty
}

const getTaskTypeLabel = (type) => {
  const map = {
    concept_question: '💭 概念题',
    comparison_question: '⚖️ 对比题',
    scenario_question: '🎯 场景题',
    coding_task: '💻 代码练习',
    summary_task: '📝 总结任务',
    project_task: '🚀 项目任务',
    interview_question: '🎤 面试题',
  }
  return map[type] || '📌 练习'
}
</script>

<style scoped>
.practice-task {
  margin-bottom: 20px;
  padding: 24px;
  background: white;
  border-radius: 16px;
  border: 2px solid #f0f0f0;
  transition: all 0.3s ease;
}

.practice-task:hover {
  border-color: #667eea;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.task-header {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.difficulty-tag,
.type-tag {
  font-weight: 600;
  border-radius: 8px;
  padding: 6px 14px;
}

.task-text {
  font-size: 16px;
  color: #1a1a1a;
  line-height: 1.7;
  margin-bottom: 16px;
  font-weight: 500;
}

.answer-collapse {
  margin-top: 16px;
  border: none;
}

.answer-collapse :deep(.el-collapse-item__header) {
  background: linear-gradient(135deg, #f5f7ff 0%, #f0f4ff 100%);
  border-radius: 10px;
  padding: 12px 16px;
  border: none;
  font-weight: 600;
  transition: all 0.2s ease;
}

.answer-collapse :deep(.el-collapse-item__header:hover) {
  background: linear-gradient(135deg, #e8ecff 0%, #dce4ff 100%);
}

.answer-collapse :deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

.answer-collapse :deep(.el-collapse-item__content) {
  padding: 16px 0 0 0;
}

.collapse-title {
  color: #667eea;
  font-size: 14px;
}

.reference-answer {
  font-size: 14px;
  color: #555;
  line-height: 1.7;
  white-space: pre-wrap;
  padding: 16px;
  background: #fafafa;
  border-radius: 10px;
  border-left: 4px solid #667eea;
}
</style>

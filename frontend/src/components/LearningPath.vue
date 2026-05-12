<template>
  <div class="learning-path">
    <h4 class="path-title">{{ learningPath.title }}</h4>
    <p class="path-description" v-if="learningPath.description">{{ learningPath.description }}</p>

    <el-timeline>
      <el-timeline-item
        v-for="(stage, index) in stages"
        :key="index"
        :timestamp="stage.name"
        placement="top"
        :color="getStageColor(index)"
      >
        <div class="stage-card">
          <h5>{{ stage.goal }}</h5>
          <ul v-if="stage.tasks && stage.tasks.length > 0">
            <li v-for="(task, i) in stage.tasks" :key="i">
              <span class="task-bullet">✓</span>
              {{ task }}
            </li>
          </ul>
          <div class="expected-output" v-if="stage.expected_output">
            <div class="output-label">🎯 预期产出</div>
            <div class="output-content">{{ stage.expected_output }}</div>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  learningPath: {
    type: Object,
    required: true,
  },
})

const stages = computed(() => {
  if (Array.isArray(props.learningPath.stages)) {
    return props.learningPath.stages
  }
  return []
})

const getStageColor = (index) => {
  const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
  return colors[index % colors.length]
}
</script>

<style scoped>
.learning-path {
  padding: 10px 0;
}

.path-title {
  font-size: 20px;
  margin-bottom: 12px;
  color: #1a1a1a;
  font-weight: 700;
}

.path-description {
  font-size: 15px;
  color: #666;
  margin-bottom: 24px;
  line-height: 1.6;
}

.learning-path :deep(.el-timeline-item__timestamp) {
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 8px;
}

.stage-card {
  background: linear-gradient(135deg, #f5f7ff 0%, #ffffff 100%);
  padding: 24px;
  border-radius: 16px;
  border: 2px solid #f0f0f0;
  transition: all 0.3s ease;
}

.stage-card:hover {
  border-color: #667eea;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateX(4px);
}

.stage-card h5 {
  font-size: 17px;
  margin-bottom: 16px;
  color: #1a1a1a;
  font-weight: 600;
}

.stage-card ul {
  margin: 16px 0;
  padding-left: 0;
  list-style: none;
}

.stage-card li {
  margin: 10px 0;
  color: #555;
  font-size: 14px;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.task-bullet {
  color: #667eea;
  font-weight: bold;
  flex-shrink: 0;
  margin-top: 2px;
}

.expected-output {
  margin-top: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.output-label {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 8px;
}

.output-content {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}
</style>

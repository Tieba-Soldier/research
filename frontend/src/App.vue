<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="logo-section">
            <div class="logo-icon">🎓</div>
            <h1>智能学习资源推荐 Agent</h1>
          </div>
          <div class="header-subtitle">AI驱动的个性化学习路径规划</div>
        </div>
      </el-header>
      <el-main>
        <RecommendationPage />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import RecommendationPage from './pages/RecommendationPage.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
}

.app-container {
  min-height: 100vh;
}

.el-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px !important;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 32px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

.el-header h1 {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-subtitle {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  padding-left: 12px;
  border-left: 2px solid #e0e0e0;
}

.el-main {
  padding: 40px 20px;
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 8px;
  }

  .header-subtitle {
    border-left: none;
    padding-left: 0;
  }

  .el-header {
    height: auto !important;
    padding: 16px;
  }
}
</style>

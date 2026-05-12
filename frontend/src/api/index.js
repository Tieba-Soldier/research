import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const recommendationApi = {
  // 创建推荐任务
  createTask(data) {
    return api.post('/recommendations', data)
  },

  // 查询任务状态
  getTaskStatus(taskId) {
    return api.get(`/recommendations/tasks/${taskId}`)
  },

  // 获取推荐结果
  getResult(taskId) {
    return api.get(`/recommendations/tasks/${taskId}/result`)
  },
}

export const resourceApi = {
  // 标记已学习
  markStudied(resourceId, studied) {
    return api.post(`/resources/${resourceId}/mark-studied`, { studied })
  },

  // 收藏资源
  favorite(resourceId, favorite) {
    return api.post(`/resources/${resourceId}/favorite`, { favorite })
  },
}

export default api

# 资源搜索耗 Token 分析与优化建议

## 一句话结论

你这个项目里“搜索一次资源”之所以显得特别耗 token，根因不是单次搜索 API 本身，而是前端这次操作实际上触发了一个**完整推荐流水线**：

1. 分析用户需求
2. 提取主题
3. 标准化主题
4. 多 query 搜索
5. 对每条资源逐条做 LLM 评估
6. 生成学习路径
7. 生成练习任务

其中最贵的部分是 **“搜索后对每条资源逐条调用 LLM 评估”**。

---

## 1. 真实调用链

前端点击“生成资源推荐”后，会直接调用 `/api/recommendations`，并不是一个“纯搜索”接口：

- `frontend/src/pages/RecommendationPage.vue:112` 提交请求
- `frontend/src/api/index.js:10` 发送 `POST /recommendations`
- `backend/app/api/routes/recommendation.py:26` 只把 `request.user_input` 传给后端服务
- `backend/app/services/recommendation_service_v2.py:79` 开始完整推荐流程

也就是说，用户以为自己在“搜资源”，系统实际在跑一整条“搜索 + 理解 + 打分 + 生成内容”的 Agent 流程。

---

## 2. 一次请求会触发多少次 LLM 调用

### 固定调用

无论资源多少，都会有这些调用：

1. 用户需求分析：`UserNeedAnalyzer`
2. 主题提取：`TopicExtractor`
3. 主题标准化：`TopicNormalizer`
4. 学习路径生成：`LearningPathGenerator`
5. 练习任务生成：`PracticeTaskGenerator`

对应代码：

- `backend/app/services/recommendation_service_v2.py:113`
- `backend/app/services/recommendation_service_v2.py:153`
- `backend/app/services/recommendation_service_v2.py:170`

固定部分大约就是 **5 次 LLM 调用**。

### 最大头：资源逐条评估

资源评估这里是逐条并发调用：

- `backend/app/services/resource_evaluation_service.py:35`
- `backend/app/services/resource_evaluation_service.py:81`
- `backend/app/agents/nodes/resource_evaluator.py:21`

也就是：

> 搜到多少条资源，就调用多少次 LLM。

---

## 3. 为什么资源数量会膨胀

### 3.1 默认配置本身就偏大

默认值：

- `MAX_TOPICS_PER_REQUEST = 5`  
  `backend/app/core/config.py:47`
- `MAX_RESOURCES_PER_TOPIC = 5`  
  `backend/app/core/config.py:48`
- `MAX_SEARCH_QUERIES_PER_TOPIC = 5`  
  `backend/app/core/config.py:49`

### 3.2 每个主题会生成多个 query

搜索逻辑：

- `backend/app/services/search_service.py:82`
- `backend/app/services/search_service.py:85`
- `backend/app/services/search_service.py:147`
- `backend/app/services/search_service.py:163`

在 `global` 模式下，单主题通常会有：

- 1 个标准主题 query
- 最多 3 个关键词 query

也就是 **最多 4 个 query / topic**

在 `cn` 或 `hybrid` 模式下，还会追加中文导向 query，最多会顶到：

- **5 个 query / topic**

### 3.3 一个很容易被忽略的放大公式

粗略上限：

`raw_resources <= 主题数 × 每主题 query 数 × 每 query 返回结果数`

按当前默认值估算：

- `global`：`5 × 4 × 5 = 100`
- `cn/hybrid`：`5 × 5 × 5 = 125`

也就是说，一次请求在进入资源评估前，理论上可能已经累积 **100~125 条原始资源**。

而后面是：

> 100~125 条资源 = 100~125 次 LLM 评估调用

这就是账单突然变厚的真正原因。

---

## 4. 真正最耗 token 的地方

## 4.1 逐条资源评估是头号开销

`ResourceEvaluator` 每次只评估 1 条资源：

- `backend/app/agents/nodes/resource_evaluator.py:23`
- `backend/app/agents/nodes/resource_evaluator.py:33`

而它每次都要重新携带：

1. 一整份评估 prompt 模板
2. 用户上下文
3. 当前资源 JSON
4. JSON 输出约束模板

其中 prompt 文件本身就不短：

- `resource_evaluator.md` 约 `2412` 字符
- `llm_client.py` 每次又追加约 `332` 字符 JSON 约束

也就是说，**同一套指令被重复发送了几十次到上百次**。

### 4.2 prompt 里示例很多，而且每次都重复

几个主要 prompt 的体积：

- `user_need_analyzer.md`：约 `1166` 字符
- `topic_extractor.md`：约 `1810` 字符
- `topic_normalizer.md`：约 `2011` 字符
- `resource_evaluator.md`：约 `2412` 字符
- `learning_path_generator.md`：约 `1540` 字符
- `practice_task_generator.md`：约 `2015` 字符

真正的问题不是“某一个 prompt 太长”，而是：

> `resource_evaluator.md` 这份最长的 prompt，被按资源条数重复发送。

### 4.3 搜索结果没有在 LLM 前做足够强的裁剪

当前流程是：

1. 搜索
2. 仅按 URL 去重
3. 全量送去 LLM 评估

对应代码：

- `backend/app/services/search_service.py:57`
- `backend/app/services/search_service.py:58`
- `backend/app/services/recommendation_service_v2.py:147`

这里缺了一个关键步骤：

> 在进入 LLM 前，先做一次基于规则或分数的强裁剪。

比如“每主题先留前 2~3 条”“全局最多只评估 20 条”，现在都没有。

---

## 5. 还有哪些隐藏的放大器

## 5.1 JSON 修复重试会把一次调用变成两次

`LLMClient.generate_json()` 的逻辑是：

1. 先正常调用一次 LLM
2. JSON 解析失败或 Schema 校验失败
3. 再发一次“修复 JSON”的 LLM 请求

对应代码：

- `backend/app/tools/llm_client.py:80`
- `backend/app/tools/llm_client.py:110`
- `backend/app/tools/llm_client.py:123`
- `backend/app/tools/llm_client.py:141`

这意味着：

> 某些节点一旦输出不稳，token 成本会直接翻倍。

而且目前统计里的 `llm_calls` 并没有把这些 repair call 算进去，所以日志里看到的调用次数，**很可能低于真实账单**。

## 5.2 前端提供了“省钱开关”，但后端根本没用上

前端会把这些选项发出去：

- `include_video`
- `include_articles`
- `include_official_docs`
- `include_github`
- `include_practice_tasks`

对应：

- `frontend/src/pages/RecommendationPage.vue:94`
- `frontend/src/pages/RecommendationPage.vue:120`
- `backend/app/schemas/recommendation.py:8`

但后端真正创建任务时，只用了：

- `request.user_input`  
  `backend/app/api/routes/recommendation.py:26`

后续执行流程也始终读取全局 `settings`，没有使用请求里的：

- `max_topics`
- `max_resources_per_topic`
- `include_*`

这会带来两个问题：

1. 用户以为自己关闭了某些类型，实际上并没有省下 token
2. 用户以为自己传了更小的上限，实际上后端仍按默认大配额跑

## 5.3 主题缓存接口写了，但根本没接入

缓存服务里有：

- `get_topic_cache()`  
  `backend/app/services/cache_service.py:100`
- `set_topic_cache()`  
  `backend/app/services/cache_service.py:106`

但代码里没有实际调用。

结果是：

> 同样一句用户输入重复请求时，用户需求分析 / 主题提取 / 主题标准化 这 3 次 LLM 调用会每次重跑。

## 5.4 搜索调用统计本身就低估了真实量

推荐服务里对搜索调用次数的估算是：

- `backend/app/services/recommendation_service_v2.py:136`

它写的是：

`len(saved_topics) * min(3, settings.MAX_SEARCH_QUERIES_PER_TOPIC)`

但实际搜索逻辑允许：

- `search_queries[:settings.MAX_SEARCH_QUERIES_PER_TOPIC]`  
  `backend/app/services/search_service.py:85`

也就是说，真实 query 数可能是 `4` 或 `5`，但指标按 `3` 估算。  
这会让你误判“搜索已经不算多了”，实际上它已经放大很多了。

---

## 6. 当前最值得优先做的优化

下面按“收益 / 改造成本”排序。

## P0：把“搜索资源”和“生成学习路径/练习任务”拆开

现在一个按钮触发整套流程，这是最大结构性问题。

建议拆成：

1. `search_resources`
2. `generate_learning_path`
3. `generate_practice_tasks`

默认只做：

1. 主题分析
2. 搜索
3. 轻量排序
4. 返回资源

学习路径和练习任务改成用户点开时再生成。

### 预期收益

- 每次搜索至少少掉 `2` 次固定 LLM 调用
- 更重要的是，用户对“我只是搜资源”这件事会有正确预期

## P0：在 LLM 评估前做强裁剪

建议至少做两层裁剪：

1. **每主题先裁到 top 2~3**
2. **全局最多进入 LLM 的资源不超过 20**

裁剪依据可以先不用 LLM：

- 搜索引擎原始分数 `raw_score`
- 资源类型优先级
- 域名白名单
- 标题关键字命中
- URL 去重 + 域名去重

### 预期收益

如果把评估资源数从 `100` 压到 `20`：

- LLM 评估调用直接下降约 `80%`
- 整体 token 成本通常也会跟着下降约 `70%~85%`

## P0：批量评估资源，而不是 1 条资源 1 次 LLM

当前是：

- 1 条资源 -> 1 次 LLM

建议改成：

- 5~10 条资源 -> 1 次 LLM

这样一份 `resource_evaluator.md` prompt 只发一次，而不是重复 5~10 次。

### 预期收益

如果 20 条资源按 10 条一批：

- 从 `20` 次评估调用降到 `2` 次
- 重复 prompt 的输入 token 大幅下降

这是最直接、最实在的降本点。

## P1：真正使用请求里的限流参数

把这些字段打通：

- `max_topics`
- `max_resources_per_topic`
- `include_video`
- `include_articles`
- `include_official_docs`
- `include_github`
- `include_practice_tasks`

前端已经传了，Schema 也已经定义了，但执行链路没吃进去。

### 最少要做到

1. `create_task()` 存下用户选择
2. `execute_recommendation()` 使用任务上的参数，而不是一律走 `settings`
3. `include_practice_tasks = false` 时直接跳过练习题生成
4. `max_topics / max_resources_per_topic` 真正生效

## P1：缩短 prompt，去掉大段示例

现在很多 prompt 都带了较长示例。  
对于高频节点，特别是 `resource_evaluator.md`，建议：

1. 去掉冗长示例
2. 保留字段说明和一条最短示例
3. 统一压缩输出要求

因为现在 `llm_client.py` 已经会追加一段固定 JSON 要求了，prompt 文件里再写一遍，存在重复。

## P1：优先用结构化输出，减少 repair call

现在的 JSON 保证方式是：

1. 自由文本输出
2. 本地解析
3. 失败后再发修复请求

更好的方式是尽量使用模型侧的结构化输出能力，例如：

- OpenAI `response_format`
- 更明确的 JSON schema 输出

这样能减少 `_retry_with_fix()` 这类二次调用。

## P1：补上主题分析缓存

对以下阶段做缓存：

1. 用户需求分析
2. 主题提取
3. 主题标准化

缓存 key 可以用：

- `hash(user_input)`

对于同一句或高度相似的输入，能直接省掉前 3 次 LLM 调用。

---

## 7. 一个更合理的目标形态

我建议把一次“搜索资源”改造成下面这种结构：

### 搜索阶段

1. 用户输入
2. 提取 1~3 个主题
3. 每主题 2~3 个 query
4. 搜索结果去重
5. 规则裁剪到 10~20 条
6. 批量 LLM 评估
7. 返回资源列表

### 扩展阶段

用户点了再生成：

1. 学习路径
2. 练习任务

这样“搜索”这个动作的 token 成本会回到一个可控范围。

---

## 8. 建议的落地顺序

### 第一批，先立刻省钱

1. 把资源评估改成批量
2. 在评估前加 top-k 裁剪
3. 让 `max_topics` / `max_resources_per_topic` 真正生效
4. 关闭 `include_practice_tasks` 时跳过练习题生成

### 第二批，再做结构优化

1. 拆分“搜索资源”和“生成学习路径”
2. 接入主题缓存
3. 缩短 prompt
4. 改用结构化 JSON 输出

### 第三批，补监控

1. 统计真实 LLM 请求次数
2. 单独统计 repair call 次数
3. 统计每次请求进入评估的资源数
4. 统计 search query 实际数量，而不是估算值

---

## 9. 最终判断

如果只问一句“问题在哪”：

> 问题不在搜索 API，而在你把“搜索资源”设计成了“全链路推荐生成”，并且把搜索出来的大量资源逐条送进了 LLM 做重复评估。

如果只问一句“最该先优化什么”：

> 先把 **逐条资源评估** 改成 **先裁剪、后批量评估**，再把 **学习路径 / 练习题** 从默认搜索流程里拆出去。

这两步做完，token 成本通常就会明显下来。

  OpenMAIC 项目功能模块梳理  **主要功能是根据pdf和网络搜索的资料 生成一个带有沉浸式体验的课堂**

  一、核心功能模块

  1. 课堂生成系统 (Generation Pipeline)

  位置: lib/generation/

  两阶段生成流程:
  - 阶段1 - 大纲生成 (outline-generator.ts)
    - 输入：用户需求文本 + PDF文档（可选）
    - 输出：场景大纲列表 (SceneOutline[])
    - 功能：分析需求，推断课程语言、时长、难度，生成结构化大纲
  - 阶段2 - 场景内容生成 (scene-generator.ts)
    - 输入：场景大纲
    - 输出：完整场景（幻灯片/测验/交互/PBL）
    - 子流程：
        - 生成场景内容（文本、图表、公式）
      - 生成教学动作（语音、白板、特效）
      - 生成AI图片/视频（可选）

  支持的场景类型:
  - Slide: PPT式讲解，支持文本、图片、图表、公式、表格
  - Quiz: 单选/多选/简答题，AI自动评分
  - Interactive: HTML交互式模拟（物理实验、数学可视化等）
  - PBL: 项目式学习，多角色协作

  2. 多智能体编排系统 (Orchestration)

  位置: lib/orchestration/

  核心组件:
  - Director Graph (director-graph.ts): LangGraph状态机
    - 单智能体模式：纯代码逻辑，零LLM调用
    - 多智能体模式：LLM决策下一个发言者
  - Agent Generate Node: 执行单个智能体的生成
    - 流式输出文本和动作
    - 白板动作记录
    - 动作权限过滤

  智能体能力:
  - 语音讲解（TTS）
  - 白板绘图（画线、形状、文字、图表）
  - 幻灯片操作（聚光灯、激光笔）
  - 实时讨论

  3. 课堂播放引擎 (Playback)

  位置: lib/playback/

  状态机:
  - idle: 空闲
  - playing: 自动播放
  - live: 实时互动（讨论、问答）

  动作执行器 (lib/action/):
  支持28+种动作类型，包括：
  - speech: 语音播报
  - wb_draw_line/shape/text/chart: 白板绘制
  - spotlight/laser: 幻灯片特效
  - slide_next/prev: 幻灯片切换

  4. 幻灯片渲染系统 (Slide Renderer)

  位置: components/slide-renderer/

  Canvas渲染引擎:
  - 支持9种元素类型：Text, Image, Video, Shape, Line, Chart, Latex, Table, Code
  - 精确布局计算（文本高度查找表、对齐算法）
  - 实时编辑能力

  5. 文档解析系统 (PDF Parsing)

  位置: lib/pdf/

  支持的解析器:
  - unpdf: 内置，免费，基础文本+图片提取
  - MinerU: 高级解析，支持表格、公式（LaTeX）、OCR、布局保留

  解析流程:
  PDF → 解析器 → Markdown文本 + 图片数组 + 元数据
       → 图片映射 (img_1 → base64 URL)
       → 传递给生成流程

  6. 媒体生成系统 (Media Generation)

  位置: lib/media/

  支持的提供商:
  - 图片生成: OpenAI DALL-E, MiniMax, 自定义API
  - 视频生成: MiniMax, 自定义API
  - TTS: OpenAI, Azure, MiniMax, Edge TTS
  - ASR: OpenAI Whisper, 自定义API

  7. 导出系统 (Export)

  位置: lib/export/

  导出格式:
  - PPTX: 完整可编辑的PowerPoint文件（含图表、公式）
  - HTML: 自包含的交互式网页
  - ZIP: 完整课堂备份（课程结构+媒体文件）

  8. 存储系统 (Storage)

  位置: lib/storage/

  IndexedDB存储:
  - 课堂数据（场景、幻灯片、配置）
  - 媒体文件（图片、音频、视频）
  - 用户设置

  9. Web搜索增强 (Web Search)

  位置: lib/web-search/

  功能:
  - 实时联网搜索
  - 为课程内容提供最新信息
  - 支持自定义搜索API

  10. 国际化系统 (i18n)

  位置: lib/i18n/

  支持语言: 中文、英文、日语、俄语、阿拉伯语

---
  二、教学视频生成的资料来源

  主要数据来源:

  1. 用户输入的需求文本 (UserRequirements.requirement)

    - 自由文本描述（主题、时长、风格等）
    - 系统自动推断课程细节
  2. 上传的PDF文档 (ParsedPdfContent)
    {

    text: string,           // 提取的文本（MinerU为Markdown）
    images: string[],       // Base64图片数组
    tables: [...],          // 表格数据
    formulas: [...],        // LaTeX公式
    metadata: {
      imageMapping: {...},  // img_1 → base64 URL
      pdfImages: [...]      // 带页码的图片
    }
  }
  3. Web搜索结果 (可选)

    - 实时联网获取最新信息
    - 补充课程内容
  4. AI生成的媒体:

    - 图片: 根据prompt生成配图（gen_img_1, gen_img_2...）
    - 视频: 生成动画演示（gen_vid_1, gen_vid_2...）

  生成流程中的数据流:

  用户需求 + PDF文档 + Web搜索
           ↓
      [阶段1: 大纲生成]
      - LLM分析需求
      - 推断语言、时长、难度
      - 分配PDF图片到场景
      - 标记需要AI生成的媒体
           ↓
      场景大纲 (SceneOutline[])
      - 每个场景的标题、描述、关键点
      - suggestedImageIds: ["img_1", "img_3"]
      - mediaGenerations: [{ type: 'image', prompt: '...', elementId: 'gen_img_1' }]
           ↓
      [阶段2: 内容生成]
      - 为每个场景生成具体内容
      - Slide: 生成PPT元素（文本、图表、公式）
      - Quiz: 生成题目和答案
      - Interactive: 生成HTML代码
      - PBL: 生成项目配置
           ↓
      [阶段3: 动作生成]
      - 生成教学动作序列
      - speech: 语音讲解文本
      - wb_*: 白板绘制指令
      - spotlight/laser: 特效动作
           ↓
      [媒体生成]
      - 调用图片/视频生成API
      - 替换占位符ID为实际URL
           ↓
      [TTS生成]
      - 将speech动作的文本转为音频
      - 存储到IndexedDB
           ↓
      完整课堂 (Classroom)
      - 场景列表
      - 幻灯片内容
      - 动作序列
      - 媒体文件

  Prompt模板系统:

  位置: lib/generation/prompts/templates/

  关键模板：
  - requirements-to-outlines/: 需求→大纲
  - slide-content/: 大纲→幻灯片内容
  - slide-actions/: 内容→教学动作
  - quiz-content/: 大纲→测验题目
  - interactive-html/: 大纲→交互式HTML
  - pbl-actions/: 项目配置→协作流程

  每个模板包含：
  - system.md: 系统提示词（角色、规则、格式）
  - user.md: 用户提示词模板（插入实际数据）

  关键API端点:

  1. /api/parse-pdf: 解析PDF文档
  2. /api/generate/scene-outlines-stream: 生成场景大纲（流式）
  3. /api/generate/scene-content: 生成场景内容
  4. /api/generate/scene-actions: 生成教学动作
  5. /api/generate/image: 生成AI图片
  6. /api/generate/video: 生成AI视频
  7. /api/generate/tts: 文本转语音
  8. /api/chat: 多智能体讨论
  9. /api/generate-classroom: 异步生成完整课堂

---
  三、项目架构总结

  OpenMAIC/
  ├── 前端层 (Next.js App Router)
  │   ├── 课堂生成界面
  │   ├── 课堂播放界面
  │   └── 设置面板
  │
  ├── API层 (18个端点)
  │   ├── 生成相关 (大纲、内容、动作、媒体)
  │   ├── 解析相关 (PDF、转录)
  │   ├── 互动相关 (聊天、测验评分、PBL)
  │   └── 工具相关 (Web搜索、健康检查)
  │
  ├── 核心业务逻辑层
  │   ├── 生成流程 (两阶段pipeline)
  │   ├── 多智能体编排 (LangGraph)
  │   ├── 播放引擎 (状态机)
  │   ├── 动作执行器 (28+动作类型)
  │   └── 幻灯片渲染 (Canvas)
  │
  ├── 集成层
  │   ├── AI提供商 (OpenAI, Anthropic, Google, etc.)
  │   ├── TTS/ASR提供商
  │   ├── 图片/视频生成
  │   └── PDF解析器
  │
  └── 存储层
      ├── IndexedDB (课堂数据、媒体)
      └── 导出 (PPTX, HTML, ZIP)
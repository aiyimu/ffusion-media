# FFmpeg Web UI 项目全局规则
## 一、优先级说明
本规则为项目最高执行准则，所有代码开发、功能实现必须100%遵循，任何与本规则冲突的实现均视为无效，必须立即修正。

## 二、技术栈强制约定（固定不可变更）
### 系统
1. 操作系统: Windows11

### 后端技术栈
1.  核心框架：FastAPI 最新稳定版，必须使用异步原生支持
2.  异步任务队列：Celery 最新稳定版 + Redis 最新稳定版
3.  数据库：默认SQLite（开箱即用），必须兼容PostgreSQL
4.  ORM：SQLAlchemy 2.0 最新稳定版，禁止原生SQL拼接
5.  WebSocket：FastAPI原生WebSocket，禁止第三方WebSocket库
6.  FFmpeg调用：Python原生subprocess模块，**强制列表形式参数化调用，绝对禁止字符串拼接命令**，禁用ffmpeg-python等第三方封装库
7.  数据校验：Pydantic 2.0 最新稳定版，所有接口请求/响应必须全量校验
8.  环境管理：.env文件管理配置，禁止硬编码敏感信息和配置项

### 前端技术栈
1.  核心框架：Vue 3 + Vite 最新稳定版，必须使用Composition API + <script setup>语法
2.  UI组件库：Element Plus 最新稳定版，所有UI组件必须基于此库实现
3.  状态管理：Pinia 最新稳定版，禁止使用Vuex
4.  路由：Vue Router 4 最新稳定版
5.  HTTP请求：Axios 最新稳定版，必须封装统一的请求/响应拦截器
6.  代码规范：ESLint + Prettier，强制统一代码风格

## 三、编码规范强制要求
1.  命名规范：
    - Python：变量/函数蛇形命名（snake_case），类名大驼峰（PascalCase），常量全大写蛇形命名
    - 前端：变量/函数小驼峰（camelCase），组件名大驼峰，常量全大写蛇形命名
    - 所有命名必须有语义，禁止无意义单字符命名（循环变量i/j除外）
2.  模块化设计：严格单一职责原则，单个函数代码不超过50行，单个Vue组件代码不超过500行
3.  错误处理：
    - 所有异常场景必须完整捕获，禁止裸写业务逻辑
    - 所有接口必须有统一异常响应格式，前端必须有错误兜底和用户友好提示
    - FFmpeg执行必须加超时机制，禁止僵死进程占用服务器资源
4.  文档注释：
    - 所有Python函数必须带Google风格docstring，说明功能、参数、返回值、异常
    - 所有Vue组件必须注释核心功能，复杂逻辑必须加行内注释
    - 所有API接口必须自带FastAPI自动生成的文档说明

## 四、安全规范（零容忍，最高优先级）
1.  命令注入防护：
    - 绝对禁止用户输入直接拼接FFmpeg命令字符串，所有命令必须用列表形式参数化调用，subprocess.Popen的args必须是列表
    - 所有用户输入参数（编码、格式、时间、分辨率等）必须经过白名单校验，仅允许预设合法值
2.  文件安全：
    - 所有上传文件必须校验文件头（Magic Number），仅允许音视频、图片类合法文件，拦截可执行/恶意文件
    - 所有文件路径必须规范化校验，禁止../路径穿越字符，用户文件必须按用户ID隔离存储
    - 必须配置单文件大小上限，默认最大2GB，可在配置文件中调整
3.  权限隔离：
    - 必须实现基础JWT用户认证，每个用户只能操作自己的文件和任务，禁止跨用户越权访问
    - 必须限制Celery Worker并发数，默认最大同时处理4个任务，避免服务器过载，可配置调整
4.  输入校验：所有用户输入必须经过类型、范围、格式校验，禁止非法输入进入业务逻辑

## 五、项目结构强制约定
必须严格按照以下目录结构生成项目，禁止随意变更层级和命名：
ffmpeg-web-ui/├── backend/ # 后端项目根目录│ ├── app/ # 应用核心代码│ │ ├── init.py│ │ ├── main.py # FastAPI 入口启动文件│ │ ├── config.py # 全局配置文件│ │ ├── database.py # 数据库连接 & ORM 初始化│ │ ├── models/ # 数据库模型│ │ ├── api/ # API 路由（按业务模块拆分）│ │ ├── core/ # 核心业务逻辑│ │ ├── schemas/ # Pydantic 数据模型│ │ └── websocket/ # WebSocket 进度推送处理│ ├── requirements.txt # Python 依赖清单（精确到版本号）│ ├── celery_start.sh # Celery 启动脚本（Linux/macOS）│ ├── celery_start.bat # Celery 启动脚本（Windows）│ ├── start.sh # 后端一键启动脚本（Linux/macOS）│ ├── start.bat # 后端一键启动脚本（Windows）│ ├── .env.example # 环境变量示例文件│ └── README.md # 后端部署说明├── frontend/ # 前端项目根目录│ ├── src/│ │ ├── main.js # 入口文件│ │ ├── App.vue # 根组件│ │ ├── router/ # 路由配置│ │ ├── stores/ # Pinia 状态管理│ │ ├── components/ # 公共组件│ │ ├── views/ # 页面组件（按业务拆分）│ │ ├── api/ # API 请求封装│ │ ├── utils/ # 工具函数│ │ └── assets/ # 静态资源│ ├── package.json # 前端依赖清单（精确到版本号）│ ├── vite.config.js # Vite 配置 & 代理配置│ ├── .env.example # 环境变量示例文件│ ├── start.sh # 前端一键启动脚本（Linux/macOS）│ ├── start.bat # 前端一键启动脚本（Windows）│ └── README.md # 前端部署说明├── storage/ # 文件存储目录（自动生成）│ ├── uploads/ # 上传源文件│ ├── outputs/ # 处理后输出文件│ └── temp/ # 临时文件目录├── .gitignore # Git 忽略文件└── 项目总览 README.md # 全项目一键启动 & 部署说明

## 六、交付物强制约定
1.  所有代码必须完整可运行，无占位符、无缺失依赖、无语法错误
2.  必须提供全平台一键启动脚本，包含后端、Celery Worker、前端的完整启动命令
3.  必须提供详细的环境准备、部署步骤、常见问题排查文档
4.  核心功能模块必须有完整单元测试，测试覆盖率≥80%
5.  必须提供完整的API文档说明，包含FastAPI自动生成的/docs地址使用指南
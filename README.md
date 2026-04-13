# FFusion Media

基于 FFmpeg 与 Python 开发的跨平台本地媒体处理工具箱。

## 项目简介

FFusion Media 为 FFmpeg 命令行工具提供可视化、低门槛的 GUI 封装，支持视频剪切、格式转换、音频处理、图像转换等核心功能，预留插件化扩展能力，支持后续新增功能。

## 技术栈

- **开发语言**: Python 3.10+
- **核心引擎**: FFmpeg 6.0+ 静态编译版
- **GUI 框架**: PySide6 6.7.2+
- **打包工具**: PyInstaller 6.0+
- **配置管理**: pydantic-settings 2.0+

## 项目结构

```
FFusion-Media/
├── assets/                 # 静态资源目录
├── bin/                    # FFmpeg 静态二进制文件目录
├── src/                    # 项目核心源码目录
│   ├── core/               # 核心引擎层
│   ├── modules/            # 业务功能层（插件化）
│   ├── gui/                # GUI 界面层
│   └── utils/              # 通用工具类
├── tests/                  # 单元测试目录
├── docs/                   # 项目外部文档
├── build/                  # 打包配置目录
├── main.py                 # 程序入口文件
├── requirements.txt        # 项目依赖固定版本清单
├── .gitignore              # Git 忽略文件配置
├── README.md               # 项目首页说明文档
├── LICENSE                 # 开源协议文件
└── project_rule.md         # 项目开发规则手册
```

## 快速开始

### 环境要求

- Python 3.10 或更高版本

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（macOS/Linux）
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

## 开源协议

MIT License

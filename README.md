# 📽️ 文本转定格动画应用

这是一个基于Flask的Web应用，可以将用户输入的文本故事转换成AI生成的定格动画（GIF）。

## ✨ 功能特点

- 📝 输入文本故事，自动分解成多个场景
- 🎨 使用DALL-E API生成每个场景的图片
- 🎬 将图片合成为连贯的GIF动画
- ⚙️ 可自定义帧数和每帧持续时间
- 💾 支持下载生成的动画

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置API密钥

应用支持多种图片生成API：

#### 方式1：使用启动脚本（推荐）

最简单的方式是使用提供的启动脚本，API密钥已经配置好：

```bash
python run_with_api.py
```

#### 方式2：使用环境变量

**自定义API（已提供的密钥）:**
```powershell
$env:API_TYPE="custom"
$env:CUSTOM_API_KEY="2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9"
$env:CUSTOM_API_URL="https://your-api-endpoint.com/generate"  # 替换为实际API地址
```

**OpenAI DALL-E:**
```powershell
$env:API_TYPE="openai"
$env:OPENAI_API_KEY="your-openai-api-key"
```

**占位图片演示模式:**
```powershell
$env:API_TYPE="placeholder"
```

#### 方式3：编辑配置文件

修改 `config.py` 文件中的配置项。

### 3. 运行应用

**使用启动脚本（推荐）:**
```bash
python run_with_api.py
```

**或直接运行:**
```bash
python app.py
```

应用将在 http://localhost:5001 启动

## 📖 使用说明

1. **输入文本**: 在文本框中输入你的故事文本，可以是连贯的句子或段落
2. **设置参数**: 
   - 帧数：2-10帧（建议5帧）
   - 每帧时长：500-5000毫秒（建议1000毫秒）
3. **生成动画**: 点击"生成动画"按钮
4. **查看结果**: 等待生成完成后，可以查看动画并下载

## 🛠️ 技术栈

- **后端**: Flask (Python)
- **AI图片生成**: OpenAI DALL-E 3 API
- **图片处理**: Pillow (PIL)
- **前端**: HTML, CSS, JavaScript

## 📁 项目结构

```
flip_book/
├── app.py              # Flask应用主文件
├── requirements.txt    # Python依赖
├── README.md          # 项目说明文档
├── templates/         # HTML模板
│   └── index.html    # 主页面
├── static/           # 静态文件
│   └── style.css    # 样式文件
├── generated/        # 临时生成的图片
└── outputs/          # 输出的GIF动画
```

## 🎯 工作原理

1. **文本分析**: 将用户输入的文本按句子分割成多个场景
2. **图片生成**: 为每个场景调用DALL-E API生成图片
3. **动画合成**: 使用Pillow将所有图片合成为GIF动画
4. **结果展示**: 在网页上显示生成的动画并提供下载

## 💡 提示

- 文本越具体，生成的图片越准确
- 建议每个场景描述清晰，避免过于抽象
- 帧数越多，生成时间越长
- API调用可能需要消耗额度（取决于使用的API服务）
- 如果使用自定义API，请确保API端点URL正确

## ⚠️ 注意事项

- 默认已配置自定义API密钥，可直接运行
- 如果使用其他API服务，需要修改 `CUSTOM_API_URL` 为实际的API端点
- 图片生成速度取决于网络和API响应时间
- 生成的文件会保存在`outputs`文件夹中

## 🔧 更换图片生成API

如果你的API密钥对应的是特定服务（如Stable Diffusion、Replicate等），需要修改 `app.py` 中的 `generate_image_custom_api` 函数，调整请求格式以匹配你的API规范。

常见API服务的请求格式示例已包含在代码中，你只需要：
1. 修改 `CUSTOM_API_URL` 为实际的API端点
2. 根据API文档调整请求参数和响应处理

## 📝 示例文本

```
一只小猫在花园里玩耍。它追逐着蝴蝶。突然发现了一朵美丽的花。小猫闻了闻花香。最后满意地躺在草地上休息。
```

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可

MIT License

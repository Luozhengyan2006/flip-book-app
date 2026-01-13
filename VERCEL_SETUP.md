# Vercel 部署配置指南

## ✅ 已完成的修改

1. **创建了 `vercel.json`** - Vercel配置文件
2. **创建了 `api/index.py`** - 无服务器函数入口
3. **修改了前端代码** - 支持base64 GIF数据
4. **已推送到GitHub** ✓

## 🔧 在Vercel中配置环境变量

### 步骤1：打开Vercel项目设置
1. 访问你的Vercel项目：https://vercel.com/dashboard
2. 选择 `flip-book-app` 项目
3. 点击 **Settings（设置）** 标签
4. 左侧菜单选择 **Environment Variables（环境变量）**

### 步骤2：添加以下环境变量

| 名称 | 值 | 说明 |
|------|-----|------|
| `API_TYPE` | `custom` | API类型 |
| `CUSTOM_API_KEY` | `2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9` | 你的API密钥 |
| `CUSTOM_API_URL` | `https://api.deapi.ai/v1/images/generate` | API地址 |

**重要提示**：每个变量都要选择 **All Environments**（所有环境）

### 步骤3：重新部署

1. 点击 **Deployments（部署）** 标签
2. 找到最新的部署
3. 点击右侧的 **⋮** 菜单
4. 选择 **Redeploy（重新部署）**
5. 确认重新部署

## 🚀 验证部署

部署完成后：
1. 访问你的Vercel网址（类似 `https://flip-book-app.vercel.app`）
2. 应该能看到首页
3. 点击 "生成动画" 测试功能

## ⚠️ 注意事项

### 当前版本特性：
- ✅ 使用占位图片（多彩渐变背景）
- ✅ GIF在内存中生成，返回base64数据
- ✅ 无需文件存储
- ✅ 适配Vercel serverless架构

### 已知限制：
- **API调用可能失败**：deAPI端点返回404，所以目前使用占位图片
- **无文件持久化**：生成的GIF不会保存，每次生成新的
- **函数超时**：Vercel免费版函数最多执行10秒

### 如果需要真实图片：
1. 需要找到正确的deAPI端点URL
2. 或改用其他图片生成API（如OpenAI DALL-E）
3. 设置 `OPENAI_API_KEY` 环境变量

## 🐛 故障排除

### 如果仍然500错误：
1. 检查Vercel构建日志（Deployments → 点击部署 → Building标签）
2. 检查函数日志（Functions标签）
3. 确认环境变量已正确设置

### 如果前端加载但点击无响应：
1. 打开浏览器开发者工具（F12）
2. 查看Console标签的错误
3. 查看Network标签的请求状态

## 📝 本地测试

如果想在本地测试Vercel版本：
```bash
# 安装Vercel CLI
npm install -g vercel

# 在项目目录运行
cd "c:\Users\97746\OneDrive\Desktop\git\flip_book"
vercel dev
```

## 🔗 相关链接

- GitHub仓库：https://github.com/Luozhengyan2006/flip-book-app
- Vercel文档：https://vercel.com/docs
- Python Serverless函数：https://vercel.com/docs/functions/serverless-functions/runtimes/python

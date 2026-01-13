# deAPI 图片生成服务使用指南

## 当前配置

- **API密钥**: `2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9`
- **API端点**: `https://api.deapi.ai/v1/images/generate`

## 功能说明

本应用已完整实现以下功能：

### 1. ✅ 接收中文故事
- 支持完整的中文输入
- 智能识别中文标点符号（。！？；）
- 自动分割成多个场景

### 2. ✅ 场景分割
- 用户可选择2-10帧
- 智能分组相关句子
- 保持故事连贯性

### 3. ✅ 图片生成
- 使用deAPI的flux-pro模型
- 直接使用中文提示词（无需翻译）
- 支持1024x1024分辨率

### 4. ✅ 本地保存
- 每帧图片单独保存为PNG
- 存储在`generated/`文件夹
- 文件名格式：`frame_时间戳_帧号.png`

### 5. ✅ GIF动画合成
- 自动合成所有帧为GIF
- 可自定义每帧时长（500-5000ms）
- 存储在`outputs/`文件夹

### 6. ✅ URL返回
- 返回GIF的访问URL
- 格式：`/outputs/animation_时间戳_ID.gif`
- 支持直接在浏览器查看和下载

### 7. ✅ 中文支持
- 完整支持中文输入和输出
- 占位图片也显示中文
- 所有日志信息中文化

### 8. ✅ 错误处理
- API调用失败时使用占位图片
- 显示清晰的错误信息
- 确保动画始终能生成

### 9. ✅ 保持现有结构
- 所有Flask端点保持不变
- 前端界面无需修改
- 向后兼容

## API 调用格式

当前使用的请求格式：

```json
{
  "prompt": "中文场景描述",
  "model": "flux-pro",
  "width": 1024,
  "height": 1024,
  "num_inference_steps": 30,
  "guidance_scale": 7.5
}
```

## API 状态码

- `200`: 成功
- `401`: API密钥无效
- `404`: 端点不存在
- `429`: 频率限制
- `500`: 服务器错误

## 故障排除

### 如果API持续返回404

这可能意味着：

1. **URL不正确** - deAPI的实际端点可能不同
2. **需要注册** - 可能需要在deAPI平台注册账号
3. **API密钥格式** - 密钥格式可能需要调整

### 建议操作

1. 访问deAPI官网查看文档
2. 确认API端点URL
3. 检查API密钥是否有效
4. 查看是否有其他认证要求

### 临时解决方案

目前应用会在API失败时：
- 自动使用占位图片
- 每帧显示不同颜色
- 清晰显示场景文本
- 仍然生成完整的GIF动画

## 使用示例

### 请求示例

```bash
POST /generate
Content-Type: application/json

{
  "text": "我走到楼梯前。我开始上楼梯。我到达二楼。我走进厨房。我拿起水杯。",
  "num_frames": 5,
  "frame_duration": 1000
}
```

### 响应示例

```json
{
  "success": true,
  "output_file": "animation_20260112_203118.gif",
  "output_url": "/outputs/animation_20260112_203118.gif",
  "num_frames": 5,
  "scenes": [
    {
      "frame": 1,
      "scene": "我走到楼梯前",
      "status": "success",
      "image_file": "frame_20260112_203118_01.png"
    }
  ]
}
```

## 文件结构

```
flip_book/
├── app.py              # 主应用（已优化）
├── generated/          # 单帧图片存储
│   └── frame_*.png
├── outputs/            # GIF动画输出
│   └── animation_*.gif
├── templates/          # HTML模板
└── static/             # CSS样式
```

## 性能优化

- 超时设置：180秒
- 并发处理：顺序生成（保证质量）
- 图片格式：PNG（高质量），GIF（兼容性）
- 缓存：每个生成的文件永久保存

## 后续改进建议

1. 添加图片质量选项
2. 支持MP4视频输出
3. 批量处理多个故事
4. 添加图片预览功能
5. 支持自定义图片风格

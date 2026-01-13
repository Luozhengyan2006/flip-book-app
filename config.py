# API配置文件
# 在这里配置你的API密钥和设置

# API类型选择: 'openai', 'custom', 'placeholder'
API_TYPE = 'custom'

# 自定义API配置
CUSTOM_API_KEY = '2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9'
CUSTOM_API_URL = 'https://api.example.com/v1/generate'  # 替换为实际的API端点

# OpenAI配置（如果使用OpenAI）
OPENAI_API_KEY = ''  # 或者通过环境变量设置

# 图片生成参数
DEFAULT_IMAGE_SIZE = '1024x1024'
DEFAULT_STEPS = 30
DEFAULT_GUIDANCE_SCALE = 7.5

# 应用配置
FLASK_PORT = 5001
FLASK_DEBUG = True

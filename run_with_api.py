# 启动脚本 - 使用自定义API密钥

import os
import sys

# 设置API配置
os.environ['API_TYPE'] = 'custom'
os.environ['CUSTOM_API_KEY'] = '2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9'
os.environ['CUSTOM_API_URL'] = 'https://api.deapi.ai/v1/images/generate'

# 启动Flask应用
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("📽️  文本转定格动画应用")
    print("=" * 60)
    print(f"API类型: {os.environ.get('API_TYPE')}")
    print(f"API密钥: {os.environ.get('CUSTOM_API_KEY')[:20]}...")
    print(f"启动地址: http://localhost:5001")
    print("=" * 60)
    print()
    
    app.run(debug=True, port=5001)

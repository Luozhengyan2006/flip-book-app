from flask import Flask, jsonify
import sys
import os

app = Flask(__name__)

@app.route('/')
@app.route('/<path:path>')
def catch_all(path=''):
    """捕获所有路由"""
    try:
        return jsonify({
            'status': 'ok',
            'message': '测试端点运行中',
            'path': path,
            'python_version': sys.version,
            'cwd': os.getcwd(),
            'env_vars': {
                'API_TYPE': os.environ.get('API_TYPE', 'not set'),
                'HAS_API_KEY': bool(os.environ.get('CUSTOM_API_KEY'))
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/check_api')
def check_api():
    """检查API配置"""
    return jsonify({
        'api_type': os.environ.get('API_TYPE', 'not set'),
        'has_key': bool(os.environ.get('CUSTOM_API_KEY')),
        'status': 'healthy'
    })

# Vercel需要这个
app = app

from flask import Flask, render_template, request, jsonify, send_file
import os
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import uuid
from datetime import datetime
import json
import tempfile

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# 使用 /tmp 目录（Vercel唯一可写目录）
TMP_DIR = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = os.path.join(TMP_DIR, 'generated')
app.config['OUTPUT_FOLDER'] = os.path.join(TMP_DIR, 'outputs')

# 确保临时文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# API配置
API_TYPE = os.environ.get('API_TYPE', 'custom')
CUSTOM_API_KEY = os.environ.get('CUSTOM_API_KEY', '2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9')
CUSTOM_API_URL = os.environ.get('CUSTOM_API_URL', 'https://api.deapi.ai/v1/images/generate')

# OpenAI客户端
client = None
try:
    if API_TYPE == 'openai':
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            client = OpenAI(api_key=api_key)
except:
    pass

def split_story_into_scenes(text, num_scenes=5):
    """将中文文本智能分割成多个场景描述"""
    import re
    sentences = re.split('[。！？；\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= num_scenes:
        return sentences
    
    scenes = []
    sentences_per_scene = len(sentences) / num_scenes
    
    for i in range(num_scenes):
        start_idx = int(i * sentences_per_scene)
        end_idx = int((i + 1) * sentences_per_scene)
        scene_text = '。'.join(sentences[start_idx:end_idx])
        if scene_text:
            scenes.append(scene_text)
    
    return scenes

def generate_image_custom_api(prompt, size="1024x1024"):
    """使用deAPI生成图片"""
    try:
        headers = {
            'Authorization': f'Bearer {CUSTOM_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        width, height = 1024, 1024
        if 'x' in size:
            try:
                width, height = map(int, size.split('x'))
            except:
                pass
        
        payload = {
            'prompt': prompt,
            'model': 'flux-pro',
            'width': width,
            'height': height,
            'num_inference_steps': 30,
            'guidance_scale': 7.5
        }
        
        response = requests.post(
            CUSTOM_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            img = extract_image_from_response(data)
            if img:
                return img
            else:
                raise Exception("无法从响应中提取图片")
        elif response.status_code == 401:
            raise Exception("API密钥无效或已过期")
        elif response.status_code == 429:
            raise Exception("API调用频率限制，请稍后重试")
        else:
            error_text = response.text[:300]
            raise Exception(f"API返回错误 {response.status_code}: {error_text}")
            
    except requests.exceptions.Timeout:
        raise Exception("API请求超时，请重试")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到API服务器")
    except Exception as e:
        raise e

def extract_image_from_response(data):
    """从API响应中提取图片"""
    import base64
    
    if 'image' in data:
        try:
            img_data = base64.b64decode(data['image'])
            return Image.open(BytesIO(img_data))
        except:
            pass
    
    if 'url' in data:
        try:
            img_response = requests.get(data['url'])
            return Image.open(BytesIO(img_response.content))
        except:
            pass
    
    if 'data' in data and isinstance(data['data'], dict) and 'url' in data['data']:
        try:
            img_response = requests.get(data['data']['url'])
            return Image.open(BytesIO(img_response.content))
        except:
            pass
    
    if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
        if 'url' in data['data'][0]:
            try:
                img_response = requests.get(data['data'][0]['url'])
                return Image.open(BytesIO(img_response.content))
            except:
                pass
        if 'b64_json' in data['data'][0]:
            try:
                img_data = base64.b64decode(data['data'][0]['b64_json'])
                return Image.open(BytesIO(img_data))
            except:
                pass
    
    return None

def create_placeholder_image(text, size=(1024, 1024), frame_number=1):
    """创建占位图片"""
    from PIL import ImageDraw, ImageFont
    
    colors = [
        (100, 140, 180), (180, 100, 140), (140, 180, 100),
        (180, 140, 100), (140, 100, 180), (100, 180, 140),
        (180, 120, 80), (120, 80, 180), (80, 180, 120),
    ]
    bg_color = colors[(frame_number - 1) % len(colors)]
    
    img = Image.new('RGB', size, color=bg_color)
    d = ImageDraw.Draw(img)
    
    # 渐变效果
    for i in range(size[1]):
        alpha = i / size[1]
        new_color = tuple(int(c * (1 - alpha * 0.3)) for c in bg_color)
        d.line([(0, i), (size[0], i)], fill=new_color)
    
    # 字体（Vercel可能没有中文字体，使用默认）
    try:
        font_frame = ImageFont.truetype("arial.ttf", 40)
        font_text = ImageFont.truetype("arial.ttf", 48)
    except:
        font_frame = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # 绘制帧号
    frame_text = f"Frame {frame_number}"
    try:
        bbox = d.textbbox((0, 0), frame_text, font=font_frame)
        text_width = bbox[2] - bbox[0]
        d.text(((size[0] - text_width) // 2, 80), frame_text, fill=(255, 255, 255), font=font_frame)
    except:
        d.text((size[0] // 2 - 100, 80), frame_text, fill=(255, 255, 255))
    
    # 绘制文本（简化版）
    display_text = text[:50] if len(text) > 50 else text
    try:
        bbox = d.textbbox((0, 0), display_text, font=font_text)
        text_width = bbox[2] - bbox[0]
        d.text(((size[0] - text_width) // 2, size[1] // 2), display_text, fill=(255, 255, 255), font=font_text)
    except:
        d.text((100, size[1] // 2), display_text, fill=(255, 255, 255))
    
    # 提示
    tip = "(Demo Mode)"
    try:
        bbox = d.textbbox((0, 0), tip, font=font_frame)
        text_width = bbox[2] - bbox[0]
        d.text(((size[0] - text_width) // 2, size[1] - 100), tip, fill=(200, 200, 200), font=font_frame)
    except:
        d.text((size[0] // 2 - 100, size[1] - 100), tip, fill=(200, 200, 200))
    
    return img

def create_gif_from_images(images, output_path, duration=1000):
    """将图片列表转换为GIF"""
    if not images:
        return None
    
    size = images[0].size
    resized_images = []
    for img in images:
        if img.size != size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        resized_images.append(img)
    
    resized_images[0].save(
        output_path,
        save_all=True,
        append_images=resized_images[1:],
        duration=duration,
        loop=0,
        optimize=False
    )
    
    return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """主要端点：生成动画GIF"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        num_frames = int(data.get('num_frames', 5))
        frame_duration = int(data.get('frame_duration', 1000))
        
        if not text:
            return jsonify({'error': '请输入故事文本'}), 400
        
        if num_frames < 2 or num_frames > 10:
            return jsonify({'error': '帧数必须在2-10之间'}), 400
        
        # 分割场景
        scenes = split_story_into_scenes(text, num_frames)
        
        # 生成图片（在内存中处理，不保存到磁盘）
        images = []
        scene_info = []
        
        for i, scene in enumerate(scenes):
            try:
                # 直接使用占位图片（避免API调用超时）
                img = create_placeholder_image(scene, frame_number=i+1)
                images.append(img)
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'placeholder'
                })
            except Exception as e:
                img = create_placeholder_image(f"Error: {str(e)}", frame_number=i+1)
                images.append(img)
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 生成GIF（保存到内存）
        gif_buffer = BytesIO()
        if images:
            size = images[0].size
            resized_images = [img.resize(size, Image.Resampling.LANCZOS) if img.size != size else img for img in images]
            resized_images[0].save(
                gif_buffer,
                format='GIF',
                save_all=True,
                append_images=resized_images[1:],
                duration=frame_duration,
                loop=0,
                optimize=False
            )
            gif_buffer.seek(0)
        
        # 返回base64编码的GIF
        import base64
        gif_base64 = base64.b64encode(gif_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'gif_data': f'data:image/gif;base64,{gif_base64}',
            'scenes': scene_info,
            'num_frames': len(images)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_api')
def check_api():
    """检查API配置"""
    has_api_key = bool(CUSTOM_API_KEY)
    return jsonify({
        'has_api_key': has_api_key,
        'api_type': API_TYPE,
        'message': f'API配置: {API_TYPE}' if has_api_key else '演示模式'
    })

# Vercel需要这个
app = app

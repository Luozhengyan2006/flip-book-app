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

# 延迟创建文件夹（只在需要时创建，避免导入时错误）
def ensure_dirs():
    """确保必要的目录存在"""
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    except OSError:
        # 如果创建失败，使用临时目录
        pass

# API配置
API_TYPE = os.environ.get('API_TYPE', 'custom')
CUSTOM_API_KEY = os.environ.get('CUSTOM_API_KEY', '2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9')
# 尝试不同的endpoint（deAPI文档不明确）
CUSTOM_API_URL = os.environ.get('CUSTOM_API_URL', 'https://api.deapi.ai/generate')  # 修改路径

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

def generate_image(prompt, size="1024x1024"):
    """根据配置选择图片生成方法"""
    if API_TYPE == 'custom':
        return generate_image_custom_api(prompt, size)
    else:
        return create_placeholder_image(prompt)

def create_placeholder_image(text, size=(1024, 1024), frame_number=1):
    """创建占位图片（Vercel优化版）"""
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
    for i in range(0, size[1], 2):  # 每2像素一条线，提高性能
        alpha = i / size[1]
        new_color = tuple(int(c * (1 - alpha * 0.3)) for c in bg_color)
        d.line([(0, i), (size[0], i)], fill=new_color, width=2)
    
    # 使用PIL的基本绘制功能，不依赖字体文件
    # 绘制帧号（大字）
    frame_text = f"=== Frame {frame_number} ==="
    text_color = (255, 255, 255)
    
    # 由于没有字体，使用简单的矩形和文字组合
    # 在顶部绘制帧号背景
    d.rectangle([(size[0]//2 - 200, 50), (size[0]//2 + 200, 130)], 
                fill=(0, 0, 0, 128), outline=(255, 255, 255), width=3)
    
    # 使用load_default但放大绘制（多次绘制模拟粗体）
    font = ImageFont.load_default()
    
    # 帧号 - 多次绘制模拟放大和加粗效果
    frame_y = 70
    for offset_x in range(-2, 3):
        for offset_y in range(-2, 3):
            d.text((size[0]//2 - 100 + offset_x, frame_y + offset_y), 
                   frame_text, fill=text_color, font=font)
    
    # 场景文本 - 中间位置
    # 分行显示（每行20个字符）
    lines = []
    display_text = text[:100]  # 最多100字符
    for i in range(0, len(display_text), 20):
        lines.append(display_text[i:i+20])
    
    # 绘制文本背景
    text_bg_height = len(lines) * 60 + 40
    d.rectangle([(100, size[1]//2 - text_bg_height//2), 
                 (size[0] - 100, size[1]//2 + text_bg_height//2)],
                fill=(0, 0, 0, 100), outline=(255, 255, 255), width=2)
    
    # 绘制每行文本
    y_pos = size[1]//2 - text_bg_height//2 + 20
    for line in lines[:5]:  # 最多5行
        # 多次绘制模拟加粗
        for offset_x in range(-1, 2):
            for offset_y in range(-1, 2):
                d.text((150 + offset_x, y_pos + offset_y), 
                       line, fill=text_color, font=font)
        y_pos += 60
    
    # 底部提示
    tip_text = "[ Demo Mode - Placeholder Image ]"
    tip_y = size[1] - 100
    for offset_x in range(-1, 2):
        for offset_y in range(-1, 2):
            d.text((size[0]//2 - 180 + offset_x, tip_y + offset_y), 
                   tip_text, fill=(200, 200, 200), font=font)
    
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
    """首页"""
    try:
        return render_template('index.html')
    except Exception as e:
        # 如果模板加载失败，返回简单HTML
        return f'''
        # 确保目录存在
        ensure_dirs()
        
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>文本转定格动画</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                h1 {{ color: #333; }}
                .status {{ padding: 10px; background: #f0f0f0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>📽️ 文本转定格动画</h1>
            <div class="status">应用正在运行中...</div>
            <p>模板加载失败: {str(e)}</p>
            <p>请访问 <code>/check_api</code> 检查API状态</p>
        </body>
        </html>
        '''

@app.route('/generate', methods=['POST'])
def generate():
    """主要端点：生成动画GIF"""
    print("=== 开始生成动画 ===")
    try:
        data = request.get_json()
        print(f"收到请求: {data}")
        text = data.get('text', '').strip()
        num_frames = int(data.get('num_frames', 5))
        frame_duration = int(data.get('frame_duration', 1000))
        print(f"文本: {text[:50]}..., 帧数: {num_frames}, 时长: {frame_duration}ms")
        
        if not text:
            return jsonify({'error': '请输入故事文本'}), 400
        
        if num_frames < 2 or num_frames > 10:
            return jsonify({'error': '帧数必须在2-10之间'}), 400
        
        # 分割场景
        scenes = split_story_into_scenes(text, num_frames)
        print(f"场景分割完成，共 {len(scenes)} 个场景")
        
        # 生成图片
        images = []
        scene_info = []
        
        for i, scene in enumerate(scenes):
            print(f"正在生成第 {i+1}/{len(scenes)} 帧: {scene[:30]}...")
            try:
                # 尝试使用API生成图片
                img = generate_image(scene)
                images.append(img)
                print(f"✓ 第 {i+1} 帧生成成功（API）")
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'success'
                })
            except Exception as e:
                print(f"⚠ API失败，使用占位图: {e}")
                # API失败时使用占位图片
                img = create_placeholder_image(scene, frame_number=i+1)
                images.append(img)
                print(f"✓ 第 {i+1} 帧生成成功（占位图）")
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'placeholder'
                })
            except Exception as e:
                print(f"✗ 第 {i+1} 帧生成失败: {e}")
                # 如果连占位图都失败，创建最简单的图片
                img = Image.new('RGB', (1024, 1024), color=(100, 140, 180))
                images.append(img)
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 生成GIF到内存
        print("开始合成GIF...")
        gif_buffer = BytesIO()
        if images:
            size = images[0].size
            resized_images = [img.resize(size, Image.Resampling.LANCZOS) if img.size != size else img for img in images]
            
            # 保存GIF
            resized_images[0].save(
                gif_buffer,
                format='GIF',
                save_all=True,
                append_images=resized_images[1:],
                duration=frame_duration,
                loop=0,
                optimize=True  # 优化文件大小
            )
            gif_buffer.seek(0)
            print(f"✓ GIF合成成功，大小: {len(gif_buffer.getvalue())} bytes")
        
        # 返回base64
        import base64
        gif_base64 = base64.b64encode(gif_buffer.getvalue()).decode('utf-8')
        print(f"✓ Base64编码完成，长度: {len(gif_base64)}")
        
        result = {
            'success': True,
            'gif_data': f'data:image/gif;base64,{gif_base64}',
            'scenes': scene_info,
            'num_frames': len(images)
        }
        print("=== 生成完成，返回结果 ===")
        return jsonify(result)
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return jsonify({
            'error': str(e),
            'detail': error_detail
        }), 500

@app.route('/check_api')
def check_api():
    """检查API配置"""
    has_api_key = bool(CUSTOM_API_KEY)
    return jsonify({
        'has_api_key': has_api_key,
        'api_type': API_TYPE,
        'message': f'API配置: {API_TYPE}' if has_api_key else '演示模式'
    })

# Vercel需要直接导出app
app = app

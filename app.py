from flask import Flask, render_template, request, jsonify, send_file
import os
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import uuid
from datetime import datetime
import json

app = Flask(__name__)

# 获取当前脚本的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'generated')
app.config['OUTPUT_FOLDER'] = os.path.join(BASE_DIR, 'outputs')

# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# API配置
API_TYPE = os.environ.get('API_TYPE', 'custom')  # 'openai', 'custom', 'stability'
CUSTOM_API_KEY = os.environ.get('CUSTOM_API_KEY', '2182|TmECdKSqXp9UzkTYdxvVdfLoPrtzPsnmWt74yPU88f863ab9')
CUSTOM_API_URL = os.environ.get('CUSTOM_API_URL', 'https://api.deapi.ai/v1/images/generate')

# OpenAI客户端（如果使用OpenAI）
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
    # 支持多种中文标点符号分割
    import re
    
    # 按中文标点符号分割
    sentences = re.split('[。！？；\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= num_scenes:
        return sentences
    
    # 如果句子太多，智能分组
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
    """使用deAPI生成图片 - 支持中文提示词"""
    try:
        # deAPI标准格式
        headers = {
            'Authorization': f'Bearer {CUSTOM_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # 解析尺寸
        width, height = 1024, 1024
        if 'x' in size:
            try:
                width, height = map(int, size.split('x'))
            except:
                pass
        
        # deAPI标准请求格式
        payload = {
            'prompt': prompt,  # 支持中文
            'model': 'flux-pro',
            'width': width,
            'height': height,
            'num_inference_steps': 30,
            'guidance_scale': 7.5
        }
        
        print(f"调用deAPI: {CUSTOM_API_URL}")
        print(f"提示词: {prompt[:100]}...")
        
        response = requests.post(
            CUSTOM_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=180  # 增加超时时间
        )
        
        print(f"API响应: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"返回数据字段: {list(data.keys())}")
            
            # 提取并保存图片
            img = extract_image_from_response(data)
            if img:
                print(f"✓ 图片生成成功")
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
        print(f"deAPI调用失败: {e}")
        raise e

def extract_image_from_response(data):
    """从API响应中提取图片"""
    import base64
    
    # 尝试多种可能的响应格式
    # 方式1: 直接返回base64图片
    if 'image' in data:
        try:
            img_data = base64.b64decode(data['image'])
            img = Image.open(BytesIO(img_data))
            return img
        except:
            pass
    
    # 方式2: 返回图片URL
    if 'url' in data:
        try:
            img_response = requests.get(data['url'])
            img = Image.open(BytesIO(img_response.content))
            return img
        except:
            pass
    
    # 方式3: 返回data字段中的url
    if 'data' in data and isinstance(data['data'], dict):
        if 'url' in data['data']:
            try:
                img_response = requests.get(data['data']['url'])
                img = Image.open(BytesIO(img_response.content))
                return img
            except:
                pass
    
    # 方式4: 返回data数组中的url
    if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
        if 'url' in data['data'][0]:
            try:
                img_response = requests.get(data['data'][0]['url'])
                img = Image.open(BytesIO(img_response.content))
                return img
            except:
                pass
        if 'b64_json' in data['data'][0]:
            try:
                img_data = base64.b64decode(data['data'][0]['b64_json'])
                img = Image.open(BytesIO(img_data))
                return img
            except:
                pass
    
    return None

def generate_image_dalle(prompt, size="1024x1024"):
    """使用DALL-E API生成图片"""
    if not client:
        raise Exception("OpenAI API客户端未初始化，请设置OPENAI_API_KEY环境变量")
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # 下载图片
        img_response = requests.get(image_url)
        img = Image.open(BytesIO(img_response.content))
        
        return img
    except Exception as e:
        print(f"生成图片错误: {e}")
        # 返回占位图片
        return create_placeholder_image(prompt)

def generate_image(prompt, size="1024x1024"):
    """根据配置选择合适的图片生成方法"""
    if API_TYPE == 'openai':
        return generate_image_dalle(prompt, size)
    elif API_TYPE == 'custom':
        return generate_image_custom_api(prompt, size)
    else:
        # 默认使用占位图片
        return create_placeholder_image(prompt)

def create_placeholder_image(text, size=(1024, 1024), frame_number=1):
    """创建占位图片（当API不可用时）"""
    from PIL import ImageDraw, ImageFont
    import random
    
    # 根据帧数选择不同的背景色，使动画更连贯
    colors = [
        (100, 140, 180),  # 蓝色调
        (180, 100, 140),  # 粉红调
        (140, 180, 100),  # 绿色调
        (180, 140, 100),  # 橙色调
        (140, 100, 180),  # 紫色调
        (100, 180, 140),  # 青色调
        (180, 120, 80),   # 棕色调
        (120, 80, 180),   # 深紫调
        (80, 180, 120),   # 青绿调
    ]
    bg_color = colors[(frame_number - 1) % len(colors)]
    
    img = Image.new('RGB', size, color=bg_color)
    d = ImageDraw.Draw(img)
    
    # 添加渐变效果（简单版）
    for i in range(size[1]):
        alpha = i / size[1]
        new_color = tuple(int(c * (1 - alpha * 0.3)) for c in bg_color)
        d.line([(0, i), (size[0], i)], fill=new_color)
    
    # 使用字体
    try:
        font_title = ImageFont.truetype("msyh.ttc", 60)  # 微软雅黑
        font_frame = ImageFont.truetype("msyh.ttc", 40)
        font_text = ImageFont.truetype("msyh.ttc", 48)
    except:
        try:
            font_title = ImageFont.truetype("arial.ttf", 60)
            font_frame = ImageFont.truetype("arial.ttf", 40)
            font_text = ImageFont.truetype("arial.ttf", 48)
        except:
            font_title = ImageFont.load_default()
            font_frame = ImageFont.load_default()
            font_text = ImageFont.load_default()
    
    # 绘制帧号标记
    frame_text = f"第 {frame_number} 帧"
    try:
        bbox = d.textbbox((0, 0), frame_text, font=font_frame)
        text_width = bbox[2] - bbox[0]
        d.text(((size[0] - text_width) // 2, 80), frame_text, fill=(255, 255, 255), font=font_frame, stroke_width=2, stroke_fill=(0, 0, 0))
    except:
        d.text((size[0] // 2 - 100, 80), frame_text, fill=(255, 255, 255))
    
    # 提取主要内容（移除"Scene X of a story:"等前缀）
    display_text = text
    if ":" in text:
        parts = text.split(":", 1)
        if len(parts) > 1:
            display_text = parts[1].strip()
    
    # 移除英文提示词
    if "Consistent art style" in display_text:
        display_text = display_text.split(".")[0]
    
    # 智能换行 - 支持中文
    max_chars_per_line = 15  # 每行最多字符数
    lines = []
    current_line = ""
    
    for char in display_text:
        current_line += char
        # 中文字符或达到长度限制时换行
        if len(current_line) >= max_chars_per_line or char in '，。！？；':
            lines.append(current_line)
            current_line = ""
    if current_line:
        lines.append(current_line)
    
    # 绘制场景文本
    y_text = size[1] // 2 - (len(lines) * 35)
    for line in lines[:6]:  # 最多6行
        try:
            bbox = d.textbbox((0, 0), line.strip(), font=font_text)
            text_width = bbox[2] - bbox[0]
            position = ((size[0] - text_width) // 2, y_text)
            # 添加描边效果使文字更清晰
            d.text(position, line.strip(), fill=(255, 255, 255), font=font_text, stroke_width=3, stroke_fill=(0, 0, 0))
            y_text += 70
        except:
            d.text((100, y_text), line.strip(), fill=(255, 255, 255))
            y_text += 40
    
    # 底部添加提示
    tip = "（演示模式 - API调用失败）"
    try:
        bbox = d.textbbox((0, 0), tip, font=font_frame)
        text_width = bbox[2] - bbox[0]
        d.text(((size[0] - text_width) // 2, size[1] - 100), tip, fill=(200, 200, 200), font=font_frame)
    except:
        d.text((size[0] // 2 - 150, size[1] - 100), tip, fill=(200, 200, 200))
    
    return img

def create_gif_from_images(images, output_path, duration=1000):
    """将图片列表转换为GIF动画"""
    if not images:
        return None
    
    # 确保所有图片大小一致
    size = images[0].size
    resized_images = []
    for img in images:
        if img.size != size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        resized_images.append(img)
    
    # 保存为GIF
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
    """主要端点：接收中文故事，生成动画GIF"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        num_frames = int(data.get('num_frames', 5))
        frame_duration = int(data.get('frame_duration', 1000))
        
        # 验证输入
        if not text:
            return jsonify({'error': '请输入故事文本'}), 400
        
        if num_frames < 2 or num_frames > 10:
            return jsonify({'error': '帧数必须在2-10之间'}), 400
        
        print(f"\n{'='*60}")
        print(f"📽️  开始生成动画")
        print(f"故事文本: {text[:50]}...")
        print(f"帧数: {num_frames}")
        print(f"每帧时长: {frame_duration}ms")
        print(f"{'='*60}\n")
        
        # 将文本分割成场景
        scenes = split_story_into_scenes(text, num_frames)
        
        # 生成唯一的时间戳（用于文件命名）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # 为每个场景生成图片
        images = []
        scene_info = []
        
        for i, scene in enumerate(scenes):
            print(f"\n{'='*60}")
            print(f"正在生成第 {i+1}/{len(scenes)} 帧")
            print(f"场景: {scene}")
            print(f"{'='*60}\n")
            
            # 直接使用中文提示词，不添加额外的英文描述
            prompt = scene
            
            try:
                img = generate_image(prompt)
                
                # 保存单帧图片到本地
                frame_filename = f'frame_{timestamp}_{i+1:02d}.png'
                frame_path = os.path.join(app.config['UPLOAD_FOLDER'], frame_filename)
                img.save(frame_path, 'PNG')
                print(f"✓ 第{i+1}帧已保存: {frame_filename}")
                
                images.append(img)
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'success',
                    'image_file': frame_filename
                })
            except Exception as e:
                print(f"✗ 第 {i+1} 帧生成失败: {e}")
                # 使用占位图片
                img = create_placeholder_image(scene, frame_number=i+1)
                
                # 保存占位图片
                frame_filename = f'frame_{timestamp}_{i+1:02d}_placeholder.png'
                frame_path = os.path.join(app.config['UPLOAD_FOLDER'], frame_filename)
                img.save(frame_path, 'PNG')
                
                images.append(img)
                scene_info.append({
                    'frame': i + 1,
                    'scene': scene,
                    'status': 'placeholder',
                    'error': str(e),
                    'image_file': frame_filename
                })
        
        # 生成输出文件名
        output_filename = f'animation_{timestamp}_{unique_id}.gif'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        print(f"\n{'='*60}")
        print(f"正在合成GIF动画...")
        print(f"文件名: {output_filename}")
        print(f"{'='*60}\n")
        
        # 创建GIF动画
        create_gif_from_images(images, output_path, duration=frame_duration)
        
        print(f"✓ GIF动画生成成功!")
        print(f"文件路径: {output_path}")
        print(f"访问URL: /outputs/{output_filename}\n")
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'output_url': f'/outputs/{output_filename}',
            'scenes': scene_info,
            'num_frames': len(images),
            'gif_path': output_path
        })
        
    except Exception as e:
        print(f"错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/outputs/<filename>')
def serve_output(filename):
    """提供生成的动画文件"""
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/gif')
    return jsonify({'error': '文件不存在'}), 404

@app.route('/check_api')
def check_api():
    """检查API密钥是否设置"""
    if API_TYPE == 'openai':
        has_api_key = client is not None
        message = 'OpenAI API密钥已设置' if has_api_key else '未设置OPENAI_API_KEY环境变量'
    elif API_TYPE == 'custom':
        has_api_key = bool(CUSTOM_API_KEY)
        message = f'自定义API已配置 (密钥: {CUSTOM_API_KEY[:20]}...)' if has_api_key else '未设置CUSTOM_API_KEY'
    else:
        has_api_key = False
        message = '使用占位图片演示模式'
    
    return jsonify({
        'has_api_key': has_api_key,
        'api_type': API_TYPE,
        'message': message
    })

@app.route('/test_generate')
def test_generate():
    """测试生成一个简单的动画"""
    try:
        # 创建测试图片
        test_scenes = ["第一帧", "第二帧", "第三帧"]
        images = []
        
        for scene in test_scenes:
            img = create_placeholder_image(scene)
            images.append(img)
        
        # 生成GIF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'test_animation_{timestamp}.gif'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        create_gif_from_images(images, output_path, duration=1000)
        
        return jsonify({
            'success': True,
            'message': '测试动画生成成功',
            'url': f'/outputs/{output_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
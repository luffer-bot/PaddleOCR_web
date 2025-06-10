from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
import sys
import json
from werkzeug.utils import secure_filename
import logging
import shutil
import cv2
import numpy as np
import re
import ast

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')

# 配置上传文件夹和输出文件夹
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

# 确保必要的文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def draw_ocr_result(image_path, result):
    """在图片上绘制OCR结果"""
    try:
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"无法读取图片: {image_path}")
            return None

        # 获取识别结果
        if 'res' in result and 'rec_boxes' in result['res'] and 'rec_texts' in result['res']:
            boxes = result['res']['rec_boxes']
            texts = result['res']['rec_texts']
            
            # 绘制每个文本框
            for box, text in zip(boxes, texts):
                # 将坐标转换为整数
                box = box.astype(np.int32)
                # 绘制矩形框
                cv2.polylines(img, [box], True, (0, 255, 0), 2)
                # 添加文本
                cv2.putText(img, text, (box[0][0], box[0][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 保存结果图片
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], 
                                 f"{os.path.splitext(os.path.basename(image_path))[0]}_ocr_result.png")
        cv2.imwrite(output_path, img)
        return output_path
    except Exception as e:
        logger.error(f"绘制OCR结果时出错: {str(e)}")
        return None

def parse_ocr_output(output):
    """解析PaddleOCR的输出"""
    try:
        logger.debug("开始解析OCR输出")
        logger.debug(f"原始输出: {output}")
        
        # 尝试使用ast.literal_eval解析
        try:
            # 查找字典部分
            dict_match = re.search(r'\{.*\}', output, re.DOTALL)
            if dict_match:
                dict_str = dict_match.group()
                logger.debug(f"找到的字典字符串: {dict_str}")
                result = ast.literal_eval(dict_str)
                logger.debug(f"解析结果: {result}")
                return result
        except Exception as e:
            logger.error(f"使用ast.literal_eval解析失败: {str(e)}")
        
        # 如果ast.literal_eval失败，尝试使用json.loads
        try:
            # 替换单引号为双引号
            json_str = output.replace("'", '"')
            # 处理numpy数组
            json_str = re.sub(r'array\(\[(.*?)\], dtype=int\d+\)', r'[\1]', json_str)
            logger.debug(f"处理后的JSON字符串: {json_str}")
            result = json.loads(json_str)
            logger.debug(f"JSON解析结果: {result}")
            return result
        except Exception as e:
            logger.error(f"使用json.loads解析失败: {str(e)}")
        
        return None
    except Exception as e:
        logger.error(f"解析OCR输出时出错: {str(e)}")
        return None

def perform_ocr(image_path):
    """执行OCR识别并返回结果"""
    try:
        logger.debug(f"开始处理图片: {image_path}")
        
        # 构建输出文件路径
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # 执行OCR命令
        command = f'paddleocr ocr -i "{image_path}"'
        logger.debug(f"执行命令: {command}")
        
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # 执行命令并实时获取输出
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            startupinfo=startupinfo
        )

        # 实时读取输出
        stdout, stderr = process.communicate()
        
        logger.debug(f"命令执行完成，返回码: {process.returncode}")
        logger.debug(f"标准输出: {stdout}")
        if stderr:
            logger.debug(f"错误输出: {stderr}")

        # 复制原始图片到output目录
        original_output = os.path.join(app.config['OUTPUT_FOLDER'], os.path.basename(image_path))
        shutil.copy2(image_path, original_output)
        logger.debug(f"原始图片已复制到: {original_output}")

        # 检查是否有OCR结果图片生成
        result_image = None
        for file in os.listdir(os.path.dirname(image_path)):
            if file.startswith(base_name) and file.endswith(('.png', '.jpg', '.jpeg')):
                src_path = os.path.join(os.path.dirname(image_path), file)
                dst_path = os.path.join(app.config['OUTPUT_FOLDER'], file)
                shutil.move(src_path, dst_path)
                result_image = dst_path
                logger.debug(f"OCR结果图片已移动到: {dst_path}")

        output_files = {
            'original': original_output,
            'result_image': result_image
        }

        return {
            'success': True,
            'message': 'OCR处理完成',
            'output_files': output_files,
            'stdout': stdout,
            'stderr': stderr
        }

    except Exception as e:
        logger.error(f"处理过程中出现错误: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'处理过程中出现错误: {str(e)}',
            'output_files': None
        }

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件被上传'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.debug(f"文件已保存到: {filepath}")
        
        # 执行OCR处理
        result = perform_ocr(filepath)
        return jsonify(result)
    
    return jsonify({'success': False, 'message': '不支持的文件类型'})

@app.route('/output/<filename>')
def get_output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
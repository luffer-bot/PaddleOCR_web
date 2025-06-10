import os
from paddleocr import PaddleOCR
import tkinter as tk
from tkinter import filedialog, ttk
import time
import subprocess
import sys
import json

class OCRConfig:
    def __init__(self):
        self.config = {
            "use_doc_orientation_classify": True,
            "use_doc_unwarping": True,
            "use_textline_orientation": True,
            "save_path": "",
            "device": "cpu",
            "ocr_version": "PP-OCRv5",
            "text_det_limit_side_len": 64,
            "text_det_limit_type": "min",
            "text_det_thresh": 0.3,
            "text_det_box_thresh": 0.6,
            "text_det_unclip_ratio": 2.0,
            "text_rec_score_thresh": 0.0,
            "lang": "ch",
            "enable_hpi": False,
            "use_tensorrt": False,
            "min_subgraph_size": 3,
            "precision": "fp32",
            "enable_mkldnn": True,
            "cpu_threads": 8
        }
        
    def save_config(self, filename="ocr_config.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
            
    def load_config(self, filename="ocr_config.json"):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

def select_image():
    """打开文件选择对话框让用户选择图片"""
    print("正在打开文件选择对话框...")
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)  # 确保对话框显示在最前面
    file_path = filedialog.askopenfilename(
        title="选择图片文件",
        filetypes=[
            ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"),
            ("所有文件", "*.*")
        ]
    )
    root.destroy()  # 确保窗口被正确关闭
    return file_path

def select_save_path():
    """选择保存路径"""
    print("正在打开文件夹选择对话框...")
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(title="选择保存路径")
    root.destroy()
    return folder_path

def show_config_dialog(config):
    """显示配置对话框"""
    root = tk.Tk()
    root.title("OCR配置")
    root.geometry("600x800")
    
    # 创建滚动条
    canvas = tk.Canvas(root)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # 创建配置选项
    row = 0
    for key, value in config.config.items():
        ttk.Label(scrollable_frame, text=f"{key}:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            ttk.Checkbutton(scrollable_frame, variable=var).grid(row=row, column=1, padx=5, pady=5, sticky="w")
            config.config[key] = var
        elif isinstance(value, (int, float)):
            var = tk.StringVar(value=str(value))
            ttk.Entry(scrollable_frame, textvariable=var).grid(row=row, column=1, padx=5, pady=5, sticky="w")
            config.config[key] = var
        else:
            var = tk.StringVar(value=str(value))
            ttk.Entry(scrollable_frame, textvariable=var).grid(row=row, column=1, padx=5, pady=5, sticky="w")
            config.config[key] = var
        row += 1
    
    # 添加保存路径选择按钮
    ttk.Button(scrollable_frame, text="选择保存路径", 
               command=lambda: config.config["save_path"].set(select_save_path())
               ).grid(row=row, column=1, padx=5, pady=5, sticky="w")
    
    # 添加确定和取消按钮
    def on_ok():
        # 更新配置值
        for key in config.config:
            if isinstance(config.config[key], (tk.BooleanVar, tk.StringVar)):
                value = config.config[key].get()
                if isinstance(value, str):
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass
                config.config[key] = value
        root.destroy()
    
    ttk.Button(scrollable_frame, text="确定", command=on_ok).grid(row=row+1, column=0, padx=5, pady=5)
    ttk.Button(scrollable_frame, text="取消", command=root.destroy).grid(row=row+1, column=1, padx=5, pady=5)
    
    # 放置滚动条和画布
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    root.mainloop()

def perform_ocr(image_path, config):
    """执行OCR识别"""
    if not image_path:
        print("未选择文件，返回主菜单")
        return
    
    print(f"\n开始处理图片: {image_path}")
    print("正在执行OCR识别...")
    
    try:
        # 构建命令
        command = ['paddleocr', 'ocr', '-i', f'"{image_path}"']
        
        # 添加配置参数
        for key, value in config.config.items():
            if value is not None and value != "":
                if isinstance(value, bool):
                    command.extend([f'--{key}', str(value).lower()])
                else:
                    command.extend([f'--{key}', str(value)])
        
        command_str = ' '.join(command)
        print(f"执行命令: {command_str}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行命令并获取输出
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(
            command_str,
            shell=True,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=startupinfo
        )
        
        # 计算处理时间
        process_time = (time.time() - start_time) * 1000
        
        print(f"\n处理完成！耗时: {process_time:.2f}毫秒")
        print("\n识别结果:")
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("警告信息:")
            print(result.stderr)
            
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
    
    input("\n按回车键返回主菜单...")

def main():
    config = OCRConfig()
    config.load_config()  # 尝试加载已有配置
    
    while True:
        print("\n=== PaddleOCR 图片识别工具 v2.0 ===")
        print("1. 选择图片并识别")
        print("2. 配置参数")
        print("3. 保存当前配置")
        print("4. 退出程序")
        
        try:
            choice = input("\n请选择操作 (1-4): ")
            
            if choice == "1":
                image_path = select_image()
                if image_path:
                    perform_ocr(image_path, config)
            elif choice == "2":
                show_config_dialog(config)
            elif choice == "3":
                config.save_config()
                print("配置已保存")
            elif choice == "4":
                print("感谢使用，再见！")
                break
            else:
                print("无效的选择，请重试")
        except Exception as e:
            print(f"发生错误: {str(e)}")
            print("请重试...")

if __name__ == "__main__":
    main() 
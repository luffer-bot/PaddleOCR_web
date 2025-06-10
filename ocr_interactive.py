import os
from paddleocr import PaddleOCR
import tkinter as tk
from tkinter import filedialog
import time
import subprocess
import sys

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

def perform_ocr(image_path):
    """执行OCR识别"""
    if not image_path:
        print("未选择文件，返回主菜单")
        return
    
    print(f"\n开始处理图片: {image_path}")
    print("正在执行OCR识别...")
    
    try:
        # 使用命令行方式执行OCR
        command = f'paddleocr ocr -i "{image_path}"'
        print(f"执行命令: {command}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行命令并获取输出，使用UTF-8编码
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(
            command,
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
    while True:
        print("\n=== PaddleOCR 图片识别工具 ===")
        print("1. 选择图片并识别")
        print("2. 退出程序")
        
        try:
            choice = input("\n请选择操作 (1/2): ")
            
            if choice == "1":
                image_path = select_image()
                if image_path:
                    perform_ocr(image_path)
            elif choice == "2":
                print("感谢使用，再见！")
                break
            else:
                print("无效的选择，请重试")
        except Exception as e:
            print(f"发生错误: {str(e)}")
            print("请重试...")

if __name__ == "__main__":
    main() 
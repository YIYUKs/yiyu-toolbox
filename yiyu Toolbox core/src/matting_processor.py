import os
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from rembg import remove, new_session

class MattingThread(QThread):
    progress_signal = pyqtSignal(int, int, str) # item_val, total_val, msg
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, input_path, is_folder=False, strength="high"):
        super().__init__()
        self.input_path = input_path
        self.is_folder = is_folder
        self.strength = strength # low, medium, high, all
        # 锁定顶级 SOTA 引擎: birefnet-general
        self.model_name = "birefnet-general"

    def run(self):
        try:
            self.progress_signal.emit(0, 5, f"正在启动抠图引擎 ({self.model_name})...")
            session = new_session(self.model_name)
            
            if self.is_folder:
                self.process_folder(self.input_path, session)
            else:
                self.process_single_file(self.input_path, session)
        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def guided_filter(self, guide, src, radius, eps):
        guide = guide.astype(np.float32) / 255.0
        src = src.astype(np.float32) / 255.0

        mean_I = cv2.blur(guide, (radius, radius))
        mean_p = cv2.blur(src, (radius, radius))
        mean_II = cv2.blur(guide * guide, (radius, radius))
        mean_Ip = cv2.blur(guide * src, (radius, radius))

        var_I = mean_II - mean_I * mean_I
        cov_Ip = mean_Ip - mean_I * mean_p

        a = cov_Ip / (var_I + eps)
        b = mean_p - a * mean_I

        mean_a = cv2.blur(a, (radius, radius))
        mean_b = cv2.blur(b, (radius, radius))

        q = mean_a * guide + mean_b
        return (np.clip(q * 255, 0, 255)).astype(np.uint8)

    def refine_matte(self, img_bgr, mask_alpha, strength):
        """
        多级边缘处理：根据指定的强度参数进行精修
        """
        configs = {
            "high": [1, 8, 1e-3, 12],
            "medium": [0, 6, 1e-3, 6],
            "low": [0, 4, 2e-3, 1]
        }
        
        cfg = configs.get(strength, configs["high"])
        erosion_iters, radius, eps, sigmoid_factor = cfg

        mask_to_process = mask_alpha.copy()
        if erosion_iters > 0:
            kernel = np.ones((3, 3), np.uint8)
            mask_to_process = cv2.erode(mask_to_process, kernel, iterations=erosion_iters)
        
        guide = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        refined_mask = self.guided_filter(guide, mask_to_process, radius=radius, eps=eps)
        
        if sigmoid_factor > 1:
            refined_mask = refined_mask.astype(np.float32) / 255.0
            refined_mask = 1.0 / (1.0 + np.exp(-sigmoid_factor * (refined_mask - 0.5)))
            refined_mask = (np.clip(refined_mask * 255, 0, 255)).astype(np.uint8)
        
        return refined_mask

    def save_rgba(self, img_bgr, mask, output_path):
        b, g, r = cv2.split(img_bgr)
        rgba = cv2.merge([b, g, r, mask])
        _, buffer = cv2.imencode('.png', rgba)
        buffer.tofile(output_path)

    def process_single_file(self, img_path, session):
        self.progress_signal.emit(10, 10, "正在读取图片...")
        img_bgr = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img_bgr is None:
            self.finished_signal.emit(False, "无法读取图片")
            return

        self.progress_signal.emit(30, 30, "AI 正在执行核心识别 (仅运行一次)...")
        raw_mask = remove(img_bgr, session=session, only_mask=True)
        
        base_dir = os.path.dirname(img_path)
        out_dir = os.path.join(base_dir, "images_output_yiyu_box")
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        filename = os.path.basename(img_path)
        name, _ = os.path.splitext(filename)

        strengths = ["low", "medium", "high"] if self.strength == "all" else [self.strength]
        
        for i, s in enumerate(strengths):
            p_val = 50 + i * 15
            self.progress_signal.emit(p_val, p_val, f"生成结果 ({i+1}/{len(strengths)}): 强度-{s}")
            refined_mask = self.refine_matte(img_bgr, raw_mask, s)
            output_path = os.path.join(out_dir, f"{name}_{s}_refined.png")
            self.save_rgba(img_bgr, refined_mask, output_path)

        self.progress_signal.emit(100, 100, "处理完成")
        self.finished_signal.emit(True, f"已生成 {len(strengths)} 种强度的结果并保存至输出文件夹。")

    def process_folder(self, folder_path, session):
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not image_files:
            self.finished_signal.emit(False, "文件夹中没有图片")
            return

        total = len(image_files)
        base_out_dir = os.path.join(folder_path, "images_output_yiyu_box")
        if not os.path.exists(base_out_dir): os.makedirs(base_out_dir)

        strengths = ["low", "medium", "high"] if self.strength == "all" else [self.strength]

        for idx, filename in enumerate(image_files):
            img_path = os.path.join(folder_path, filename)
            total_prog = int(((idx + 1) / total) * 100)
            self.progress_signal.emit(0, total_prog, f"正在处理 ({idx+1}/{total}): {filename}")
            
            img_bgr = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img_bgr is not None:
                self.progress_signal.emit(30, total_prog, f"({idx+1}/{total}) AI 正在执行核心识别...")
                raw_mask = remove(img_bgr, session=session, only_mask=True)
                name, _ = os.path.splitext(filename)
                for s in strengths:
                    self.progress_signal.emit(70, total_prog, f"({idx+1}/{total}) 正在精修边缘...")
                    refined_mask = self.refine_matte(img_bgr, raw_mask, s)
                    output_path = os.path.join(base_out_dir, f"{name}_{s}_refined.png")
                    self.save_rgba(img_bgr, refined_mask, output_path)
                self.progress_signal.emit(100, total_prog, f"({idx+1}/{total}) 处理完成")

        self.progress_signal.emit(100, 100, "批量全模式处理完成")
        self.finished_signal.emit(True, f"已处理 {total} 张图片并保存至输出文件夹。")

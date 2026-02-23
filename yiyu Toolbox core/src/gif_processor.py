import os
import shutil
import subprocess
import urllib.request
import zipfile
from PyQt5.QtCore import QThread, pyqtSignal

class GifCompressThread(QThread):
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, target_path, compression_level=30, fuzz_pct=3, scale_pct=100, eliminate_colors=False):
        super().__init__()
        self.target_path = target_path
        self.compression_level = compression_level
        self.fuzz_pct = fuzz_pct
        self.scale_pct = scale_pct
        self.eliminate_colors = eliminate_colors
        self.is_running = True
        
        # Paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.resources_dir = os.path.join(base_dir, "resources")
        self.gifsicle_path = os.path.join(self.resources_dir, "gifsicle.exe")

    def run(self):
        try:
            self.progress_signal.emit(0, 0, "正在检查 gifsicle...")
            if not self.ensure_gifsicle():
                self.finished_signal.emit(False, "无法获取或下载 gifsicle 引擎")
                return

            if not os.path.exists(self.target_path):
                self.finished_signal.emit(False, "输入路径不存在")
                return

            if os.path.isfile(self.target_path):
                target_dir = os.path.dirname(self.target_path)
                output_dir = os.path.join(target_dir, "gif_output_yiyu_box")
                os.makedirs(output_dir, exist_ok=True)
                self.process_single_gif(self.target_path, output_dir, total_val=100)
                self.finished_signal.emit(True, "处理完成")
            else:
                self.process_folder(self.target_path)
                
        except Exception as e:
            self.finished_signal.emit(False, f"发生异常: {str(e)}")

    def stop(self):
        self.is_running = False

    def ensure_gifsicle(self):
        """Ensure gifsicle.exe exists, download if not."""
        if os.path.exists(self.gifsicle_path):
            return True

        os.makedirs(self.resources_dir, exist_ok=True)
        zip_path = os.path.join(self.resources_dir, "gifsicle.zip")
        # Reliable URL for windows gifsicle build (eternallybored.org / github mirror)
        # Using a direct link for a known working static build
        url = "https://eternallybored.org/misc/gifsicle/releases/gifsicle-1.95-win64.zip"

        try:
            self.progress_signal.emit(0, 0, "正在首次下载 gifsicle 引擎(约 1MB)...")
            
            def report_hook(count, block_size, total_size):
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    self.progress_signal.emit(percent, 0, f"下载引擎中: {percent}%")

            urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)

            self.progress_signal.emit(100, 0, "下载完成，正在解压...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find the exe inside the zip (it might be inside a subfolder)
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith("gifsicle.exe"):
                        file_info.filename = "gifsicle.exe" # extract flat
                        zip_ref.extract(file_info, self.resources_dir)
                        break
            
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
            return os.path.exists(self.gifsicle_path)
        except Exception as e:
            print(f"Failed to download gifsicle: {e}")
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            return False

    def process_folder(self, folder_path):
        output_dir = os.path.join(folder_path, "gif_output_yiyu_box")
        os.makedirs(output_dir, exist_ok=True)

        valid_exts = {'.gif'}
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and os.path.splitext(f)[1].lower() in valid_exts]

        total_files = len(files)
        if total_files == 0:
            self.finished_signal.emit(True, "目录中没有找到 GIF 文件")
            return

        for i, file_name in enumerate(files):
            if not self.is_running:
                self.finished_signal.emit(False, "用户中止操作")
                return

            file_path = os.path.join(folder_path, file_name)
            total_percent = int((i / total_files) * 100)
            self.progress_signal.emit(0, total_percent, f"准备处理: {file_name}")

            self.process_single_gif(file_path, output_dir, total_val=total_percent)

            # Update overall after finishing one
            completed_percent = int(((i + 1) / total_files) * 100)
            self.progress_signal.emit(100, completed_percent, f"完成: {file_name}")

        if self.is_running:
            self.progress_signal.emit(100, 100, "批量处理结束")
            self.finished_signal.emit(True, f"批量处理完成，共处理 {total_files} 个文件")


    def process_single_gif(self, file_path, output_dir, total_val=100):
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, f"opt_{filename}")

        self.progress_signal.emit(10, total_val, f"正在压缩 {filename}...")

        # Calculate colors based on Fuzz parameter
        # Ezgif Fuzz translates to fuzzy color bounding. Gifsicle doesn't have --fuzz natively.
        # We simulate it by reducing max color depth logarithmically.
        # 0% fuzz -> 256 colors
        # 100% fuzz -> ~2 colors
        import math
        colors = max(2, int(256 * math.pow(1 - (self.fuzz_pct / 100.0), 1.5)))

        cmd = [
            self.gifsicle_path,
            "-O3",
            f"--lossy={self.compression_level}",
            f"--colors={colors}" 
        ]
        if self.scale_pct > 0:
            # Scale_pct is now "Shrink percentage", so we keep (100 - X)% of the original.
            scale_factor = (100 - self.scale_pct) / 100.0
            cmd.append(f"--scale={scale_factor}")

        
        if self.eliminate_colors:
            cmd.append("--use-colormap=web")

        cmd.extend(["-o", output_path, file_path])

        try:
            # Run without showing cmd window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                cmd, 
                startupinfo=startupinfo,
                capture_output=True, 
                text=True, 
                errors="replace",
                check=False
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(100, total_val, f"压缩完成: {filename}")
            else:
                print(f"Gifsicle Error for {filename}: {result.stderr}")
                self.progress_signal.emit(100, total_val, f"压缩失败: {filename}")
                
        except Exception as e:
            print(f"Exception running gifsicle: {e}")
            self.progress_signal.emit(100, total_val, f"发生异常: {filename}")

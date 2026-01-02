import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image
import urllib.request

# --- Real-ESRGAN Architecture (Minimal RRDB Implementation) ---

def make_layer(block, n_layers):
    layers = []
    for _ in range(n_layers):
        layers.append(block())
    return nn.Sequential(*layers)

class ResidualDenseBlock_5C(nn.Module):
    def __init__(self, nf=64, gc=32, bias=True):
        super(ResidualDenseBlock_5C, self).__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1, bias=bias)
        self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1, bias=bias)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1, bias=bias)
        self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1, bias=bias)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1, bias=bias)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x

class RRDB(nn.Module):
    def __init__(self, nf, gc=32):
        super(RRDB, self).__init__()
        self.rdb1 = ResidualDenseBlock_5C(nf, gc)
        self.rdb2 = ResidualDenseBlock_5C(nf, gc)
        self.rdb3 = ResidualDenseBlock_5C(nf, gc)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x

class RRDBNet(nn.Module):
    def __init__(self, in_nc=3, out_nc=3, nf=64, nb=6, gc=32):
        super(RRDBNet, self).__init__()
        RRDB_block_f = lambda: RRDB(nf, gc)
        self.conv_first = nn.Conv2d(in_nc, nf, 3, 1, 1, bias=True)
        self.body = make_layer(RRDB_block_f, nb)
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1, bias=True)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1, bias=True)
        self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1, bias=True)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1, bias=True)
        self.conv_last = nn.Conv2d(nf, out_nc, 3, 1, 1, bias=True)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        fea = self.conv_first(x)
        trunk = self.conv_body(self.body(fea))
        fea = fea + trunk

        fea = self.lrelu(self.conv_up1(F.interpolate(fea, scale_factor=2, mode='nearest')))
        fea = self.lrelu(self.conv_up2(F.interpolate(fea, scale_factor=2, mode='nearest')))
        out = self.conv_last(self.lrelu(self.conv_hr(fea)))
        return out

# --- Worker Thread ---

class UpscaleThread(QThread):
    progress_signal = pyqtSignal(int, int, str) # item_val, total_val, msg
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, input_path, is_folder=False, scale=4, model_type="general"):
        super().__init__()
        self.input_path = input_path
        self.is_folder = is_folder
        self.scale = scale # 2, 4, 6
        self.model_type = model_type # general, anime
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Configure model parameters
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_root = os.path.join(base_dir, "model")
        
        if self.model_type == "general":
            self.model_path = os.path.join(model_root, "RealESRGAN_x4plus.pth")
            self.model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
            self.nb = 23
        else:
            self.model_path = os.path.join(model_root, "RealESRGAN_x4plus_anime.pth")
            self.model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
            self.nb = 6
            
        self.model = None

    def run(self):
        try:
            if not os.path.exists(self.model_path):
                self.download_model()
            
            self.load_model()
            
            if self.is_folder:
                self.process_folder(self.input_path)
            else:
                self.process_single_file(self.input_path)
        except Exception as e:
            self.finished_signal.emit(False, f"运行时出错: {str(e)}")

    def download_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        filename = os.path.basename(self.model_path)
        self.progress_signal.emit(0, 5, f"正在下载 {self.model_type} 模型权重 ({filename})...")
        
        def report_hook(count, block_size, total_size):
            if total_size > 0:
                progress = int(count * block_size * 100 / total_size)
                if progress % 5 == 0:
                    self.progress_signal.emit(progress, 5, f"下载模型进度: {progress}%")

        urllib.request.urlretrieve(self.model_url, self.model_path, report_hook)
        self.progress_signal.emit(100, 10, "模型下载完成！")

    def load_model(self):
        self.progress_signal.emit(0, 15, f"正在加载模型至 {self.device} (结构: {self.nb}层)...")
        self.model = RRDBNet(in_nc=3, out_nc=3, nf=64, nb=self.nb, gc=32)
        loadnet = torch.load(self.model_path, map_location=torch.device('cpu'))
        
        if 'params_ema' in loadnet:
            keyname = 'params_ema'
        elif 'params' in loadnet:
            keyname = 'params'
        else:
            keyname = None # direct state_dict
            
        if keyname:
            self.model.load_state_dict(loadnet[keyname], strict=True)
        else:
            self.model.load_state_dict(loadnet, strict=True)
            
        self.model.eval()
        self.model.to(self.device)
        self.progress_signal.emit(100, 20, "模型加载完毕")

    @torch.no_grad()
    def upscale_image(self, img_bgr):
        # Pre-process
        img = img_bgr.astype(np.float32) / 255.
        img = torch.from_numpy(np.transpose(img[:, :, [2, 1, 0]], (2, 0, 1))).float()
        img = img.unsqueeze(0).to(self.device)

        # Handle tiling to avoid OOM
        tile_size = 512
        tile_pad = 28 # Increase pad for better detail transition
        _, _, h, w = img.size()
        
        # Simple Tiling Logic
        output_h = h * 4
        output_w = w * 4
        output = torch.zeros((1, 3, output_h, output_w), device=self.device)

        total_tiles = ((h + tile_size - 1) // tile_size) * ((w + tile_size - 1) // tile_size)
        current_tile = 0

        for i in range(0, h, tile_size):
            for j in range(0, w, tile_size):
                current_tile += 1
                item_prog = int((current_tile / total_tiles) * 100)
                # total_prog is not easily accessible here without passing it down, 
                # but we can rely on current context if we wrap this or use a callback.
                # For now, let's just emit item progress with a dummy/placeholder total.
                # Or better: don't emit here, just do it in process_* loop.
                # Actually, the user wants to see "current task progress". Tiling is exactly that!
                # I'll use a hack: if total_prog is -1, UI keeps old total_prog.
                self.progress_signal.emit(item_prog, -1, f"AI 重建推理中 ({current_tile}/{total_tiles})...")
                
                # tile bound
                h_start, h_end = i, min(i + tile_size, h)
                w_start, w_end = j, min(j + tile_size, w)
                
                # with pad
                h_start_p = max(h_start - tile_pad, 0)
                h_end_p = min(h_end + tile_pad, h)
                w_start_p = max(w_start - tile_pad, 0)
                w_end_p = min(w_end + tile_pad, w)
                
                tile = img[:, :, h_start_p:h_end_p, w_start_p:w_end_p]
                
                # Inference
                out_tile = self.model(tile)
                
                # Cut pad
                h_cut_start = (h_start - h_start_p) * 4
                h_cut_end = (h_end - h_start_p) * 4
                w_cut_start = (w_start - w_start_p) * 4
                w_cut_end = (w_end - w_start_p) * 4
                
                out_tile = out_tile[:, :, h_cut_start:h_cut_end, w_cut_start:w_cut_end]
                
                output[:, :, h_start*4:h_end*4, w_start*4:w_end*4] = out_tile

        # Post-process
        output = output.data.squeeze().float().cpu().clamp_(0, 1).numpy()
        output = np.transpose(output[[2, 1, 0], :, :], (1, 2, 0))
        output = (output * 255.0).round().astype(np.uint8)

        # Scale Adjustment (Model is natively 4x)
        if self.scale != 4:
            new_w = int(img_bgr.shape[1] * self.scale)
            new_h = int(img_bgr.shape[0] * self.scale)
            output = cv2.resize(output, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
        return output

    def process_single_file(self, img_path):
        self.progress_signal.emit(10, 10, "正在读取图片...")
        img_bgr = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img_bgr is None:
            self.finished_signal.emit(False, "无法读取图片")
            return

        self.progress_signal.emit(20, 20, f"正在进行 {self.scale}x AI 重建处理...")
        # Since upscale_image emits its own internal progress now, we just call it.
        # But we need to make sure total_prog is correct.
        # I'll pass a context if needed, but for single file, total == item.
        result = self.upscale_image(img_bgr)
        
        base_dir = os.path.dirname(img_path)
        out_dir = os.path.join(base_dir, "upscale_output_yiyu_box")
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        
        filename = os.path.basename(img_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(out_dir, f"{name}_{self.scale}x_AI.png")
        
        _, buffer = cv2.imencode('.png', result)
        buffer.tofile(output_path)

        self.progress_signal.emit(100, 100, "处理完成")
        self.finished_signal.emit(True, f"图片已重建并保存至: {output_path}")

    def process_folder(self, folder_path):
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not image_files:
            self.finished_signal.emit(False, "文件夹中没有图片")
            return

        total = len(image_files)
        out_dir = os.path.join(folder_path, "upscale_output_yiyu_box")
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        for idx, filename in enumerate(image_files):
            img_path = os.path.join(folder_path, filename)
            total_prog = int(((idx + 1) / total) * 100)
            self.progress_signal.emit(0, total_prog, f"正在处理 ({idx+1}/{total}): {filename}")
            
            img_bgr = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img_bgr is not None:
                # Need to update upscale_image or its caller to handle signals correctly.
                # For now, I'll allow upscale_image to emit -1 for total_prog.
                result = self.upscale_image(img_bgr)
                name, _ = os.path.splitext(filename)
                output_path = os.path.join(out_dir, f"{name}_{self.scale}x_AI.png")
                _, buffer = cv2.imencode('.png', result)
                buffer.tofile(output_path)
            
            self.progress_signal.emit(100, total_prog, f"({idx+1}/{total}) 处理完成")

        self.progress_signal.emit(100, 100, "批量 AI 放大完成")
        self.finished_signal.emit(True, f"已处理 {total} 张图片并保存至输出文件夹。")

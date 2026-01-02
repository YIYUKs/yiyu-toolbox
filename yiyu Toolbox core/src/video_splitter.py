import os
import cv2
import shutil
import time
from PyQt5.QtCore import QThread, pyqtSignal
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

class VideoSplitterThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int) # item_val, total_val
    finished_signal = pyqtSignal(bool, str) # success, message

    def __init__(self, target_path, position='middle'):
        super().__init__()
        # target_path can be file or folder, but UI now sends folder
        self.target_path = target_path
        self.position = position
        self.is_running = True

    def run(self):
        try:
            if os.path.isdir(self.target_path):
                self._process_folder(self.target_path)
            elif os.path.isfile(self.target_path):
                 # Fallback support for single file
                self._process_single_video(self.target_path)
            else:
                self.finished_signal.emit(False, "Invalid path")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.log_signal.emit(f"Critical Error: {str(e)}\n{error_details}")
            self.finished_signal.emit(False, str(e))

    def stop(self):
        self.is_running = False

    def save_frame_safe(self, frame, output_path):
        """
        Use imencode to save image, supporting Chinese paths.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result, img_encode = cv2.imencode('.jpg', frame)
            if result:
                img_encode.tofile(output_path)
                return True
        except Exception as e:
            self.log_signal.emit(f"Error saving image [{output_path}]: {e}")
        return False

    def _process_folder(self, folder_path):
        # Scan for videos
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v')
        video_files = [f for f in os.listdir(folder_path) if f.lower().endswith(video_extensions)]
        
        if not video_files:
            self.finished_signal.emit(False, "No video files found in directory.")
            return

        total_videos = len(video_files)
        self.log_signal.emit(f"Found {total_videos} videos in folder.")
        
        success_count = 0
        error_count = 0
        
        for idx, filename in enumerate(video_files):
            if not self.is_running: break
            
            video_full_path = os.path.join(folder_path, filename)
            total_prog = int(((idx + 1) / total_videos) * 100)
            self.log_signal.emit(f"[{idx+1}/{total_videos}] Processing: {filename}")
            
            if self._process_single_video(video_full_path, total_val=total_prog, emit_finish=False):
                success_count += 1
            else:
                error_count += 1
                
            # Overall progress? The UI progress bar is currently used for EACH video inside _process_single_video
            # Maybe we should have two bars or use log for total.
            # For now, let's keep per-video progress in bar, and total in log.
        
        msg = f"Batch processing complete.\nSuccess: {success_count}\nFailed: {error_count}"
        self.finished_signal.emit(True, msg)


    def _process_single_video(self, video_path, total_val=100, emit_finish=True):
        if not os.path.exists(video_path):
            self.log_signal.emit(f"File not found: {video_path}")
            if emit_finish: self.finished_signal.emit(False, f"File not found: {video_path}")
            return False

        try:
            self.log_signal.emit(f"Analyzing mode: {self.position}")

            scene_list = []
            target_frames = []
            run_average_mode = (self.position == 'average')

            # 1. Scene Detection
            if not run_average_mode:
                # self.log_signal.emit("Running scene detection...") # Reduced verbosity
                video_stream = open_video(video_path)
                try:
                    scene_manager = SceneManager()
                    scene_manager.add_detector(ContentDetector(threshold=27.0))
                    scene_manager.detect_scenes(video=video_stream, show_progress=False)
                    scene_list = scene_manager.get_scene_list()
                finally:
                    if video_stream:
                        try:
                            if hasattr(video_stream, 'release'): video_stream.release()
                            elif hasattr(video_stream, 'close'): video_stream.close()
                        except: pass
                
                self.log_signal.emit(f"Detected {len(scene_list)} scenes.")

                if not scene_list:
                     self.log_signal.emit("No scenes detected. Switching to Average Mode.")
                     run_average_mode = True
                     # Temporarily force average logic but keep self.position for next video
                     # Actually we should use a local var for logic
                     pass

            # 2. Average Logic
            if run_average_mode:
                # self.log_signal.emit("Calculating 20 split points...")
                cap_temp = cv2.VideoCapture(video_path)
                if not cap_temp.isOpened():
                    self.log_signal.emit("Could not open video.")
                    return False
                
                total_frames = int(cap_temp.get(cv2.CAP_PROP_FRAME_COUNT))
                cap_temp.release()

                if total_frames > 0:
                    count = 20
                    if total_frames <= count:
                        target_frames = list(range(total_frames))
                    else:
                        step = total_frames / count
                        target_frames = sorted(list(set([int(i * step) for i in range(count)])))
                else:
                     self.log_signal.emit("Video frame count is 0.")
                     return False

            # 3. Calculate Targets from Scenes
            if not target_frames and scene_list:
                 for scene in scene_list:
                    start_frame = scene[0].get_frames()
                    end_frame = scene[1].get_frames()
                    
                    if self.position == 'middle':
                        tf = start_frame + (end_frame - start_frame) // 2
                    elif self.position == 'end':
                        tf = end_frame - 1
                    else: # start
                        tf = start_frame
                    
                    if tf < 0: tf = 0
                    target_frames.append(tf)

            # 4. Prepare Output
            video_dir = os.path.dirname(os.path.abspath(video_path))
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            
            mode_suffix_map = {'middle': '_middle', 'end': '_end', 'average': '_avg', 'start': ''}
            suffix = mode_suffix_map.get(self.position, "")
            if run_average_mode and self.position != 'average': suffix += "_auto_avg"
            
            # Standardized Output: <SourceDir>/videos_output_yiyu_box/<VideoName>_snapshots_<Mode>
            base_output_dir = os.path.join(video_dir, "videos_output_yiyu_box")
            output_dir = os.path.join(base_output_dir, f"{video_name}_snapshots{suffix}")
            
            os.makedirs(output_dir, exist_ok=True)

            # 5. Extract Frames
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                 self.log_signal.emit("OpenCV failed to open video.")
                 return False

            total_targets = len(target_frames)
            
            mode_cn_map = {'start': '开始', 'middle': '中间', 'end': '结尾', 'average': '均分'}
            mode_cn = mode_cn_map.get(self.position, self.position)

            for i, target_frame in enumerate(target_frames):
                if not self.is_running: break

                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    index_str = f"{i+1:05d}"
                    suffix_part = f"_{index_str}_{mode_cn}.jpg"
                    
                    current_path_len = len(output_dir) + 1 + len(suffix_part)
                    max_video_name_len = 250 - current_path_len
                    safe_video_name = video_name[:max_video_name_len] if max_video_name_len > 0 else "v"

                    file_path = os.path.join(output_dir, f"{safe_video_name}{suffix_part}")
                    self.save_frame_safe(frame, file_path)
                
                # Progress (Per Video)
                if total_targets > 0:
                    prog = int(((i + 1) / total_targets) * 100)
                    self.progress_signal.emit(prog, total_val)
            
            cap.release()

            # 6. Move Video File (Optional)
            # User requested "save all video processing results".
            # Usually this implies snapshots. Moving the source video might not be desired if it's "processing results".
            # BUT the original logic moved the video. 
            # If we move the video, it leaves the source folder. 
            # User said "save all video processing results" in a new folder. 
            # It's safer to COPY or Move. Original logic was MOVE. 
            # I will stick to MOVE to match original tool behavior, but into the new deep folder.
            try:
                 dst_path = os.path.join(output_dir, os.path.basename(video_path))
                 if os.path.exists(dst_path):
                      # self.log_signal.emit(f"Video file already in output.")
                      pass
                 else:
                      shutil.move(video_path, dst_path)
                      # self.log_signal.emit("Video moved.")
            except Exception as e:
                 self.log_signal.emit(f"Warning: Move failed: {e}")

            if emit_finish:
                self.finished_signal.emit(True, "Processing Complete.")
            
            return True

        except Exception as e:
            self.log_signal.emit(f"Error processing {video_path}: {e}")
            if emit_finish:
                self.finished_signal.emit(False, str(e))
            return False

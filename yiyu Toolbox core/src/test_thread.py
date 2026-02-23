import sys
import os
from PyQt5.QtWidgets import QApplication
from gif_processor import GifCompressThread

def main():
    app = QApplication(sys.argv)
    
    # Needs absolute path for test
    p = os.path.abspath('small.gif')
    print("Testing with file:", p)
    
    thread = GifCompressThread(p)
    
    def on_progress(val1, val2, msg):
        print(f"PROGRESS: {val1}% | {val2}% | {msg}")
        
    def on_finished(success, msg):
        print(f"FINISHED: {success} | {msg}")
        app.quit()
        
    thread.progress_signal.connect(on_progress)
    thread.finished_signal.connect(on_finished)
    
    thread.start()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

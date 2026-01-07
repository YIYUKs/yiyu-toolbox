import json
import os
import sys

class ConfigManager:
    @classmethod
    def get_config_path(cls):
        """
        Dynamically determines the config file path.
        - Frozen (PyInstaller): Next to the EXE.
        - Source (Main Core): In the parent directory of src/ (yiyu Toolbox core/).
        - Source (Generic): In the parent of current file.
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a temp folder and stores it in _MEIPASS
            # We want the config NEXT to the actual EXE launcher
            base_dir = os.path.dirname(sys.executable)
        else:
            # Source execution: parent of src/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(base_dir, "config.json")

    @classmethod
    def get_last_path(cls):
        """
        Retrieves the last used directory from config.json.
        Returns software root ('.') if config missing or path invalid.
        """
        try:
            config_path = cls.get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    path = config.get("last_path", ".")
                    if path and os.path.exists(path):
                        return path
        except Exception as e:
            print(f"Error loading config: {e}")
        return "."

    @classmethod
    def save_last_path(cls, path):
        """
        Saves the last used directory to config.json.
        If a file path is provided, it extracts the directory.
        """
        if not path:
            return
            
        try:
            # Normalize to directory if a file path was passed
            if os.path.isfile(path):
                directory = os.path.dirname(os.path.abspath(path))
            else:
                directory = os.path.abspath(path)
            
            config = {}
            config_path = cls.get_config_path()
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except:
                    pass
            
            config["last_path"] = directory
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace YiyuLauncher
{
    static class Program
    {
        [System.Runtime.InteropServices.DllImport("shell32.dll")]
        private static extern int SetCurrentProcessExplicitAppUserModelID([System.Runtime.InteropServices.MarshalAs(System.Runtime.InteropServices.UnmanagedType.LPWStr)] string AppID);

        [STAThread]
        static void Main()
        {
            try
            {
                // Synchronize AppID for Taskbar Grouping
                SetCurrentProcessExplicitAppUserModelID("Yiyu.Toolbox.V2");
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string pythonPath = Path.Combine(baseDir, "runtime", "Scripts", "pythonw.exe");
                string scriptPath = Path.Combine(baseDir, "src", "demo.py");

                if (!File.Exists(pythonPath) || !File.Exists(scriptPath))
                {
                    MessageBox.Show("错误：找不到启动组件。\n请确保在程序文件夹中运行。", "启动失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                // Setup Environment
                ProcessStartInfo startInfo = new ProcessStartInfo();
                startInfo.FileName = pythonPath;
                startInfo.Arguments = "\"" + scriptPath + "\"";
                startInfo.WorkingDirectory = baseDir;
                startInfo.UseShellExecute = false;
                startInfo.CreateNoWindow = true;

                // Sync Environment Variables
                startInfo.EnvironmentVariables["KMP_DUPLICATE_LIB_OK"] = "TRUE";
                
                // Auto-locate Qt
                string qtPath1 = Path.Combine(baseDir, "runtime", "Lib", "site-packages", "PyQt5", "Qt5", "plugins");
                string qtPath2 = Path.Combine(baseDir, "runtime", "Lib", "site-packages", "PyQt5", "Qt", "plugins");
                if (Directory.Exists(Path.Combine(qtPath1, "platforms")))
                    startInfo.EnvironmentVariables["QT_QPA_PLATFORM_PLUGIN_PATH"] = qtPath1;
                else if (Directory.Exists(Path.Combine(qtPath2, "platforms")))
                    startInfo.EnvironmentVariables["QT_QPA_PLATFORM_PLUGIN_PATH"] = qtPath2;

                Process.Start(startInfo);
            }
            catch (Exception ex)
            {
                MessageBox.Show("启动器发生未知错误：\n" + ex.Message, "系统错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}

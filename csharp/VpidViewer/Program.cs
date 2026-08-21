using System;
using System.Windows.Forms;
using VpidViewer.Gui;

namespace VpidViewer
{
    /// <summary>
    /// 应用入口。
    /// 对应 Python 版 main.py：配置日志、初始化 WinForms、异常兜底弹窗。
    /// </summary>
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            try
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);

                using (MainForm form = new MainForm())
                {
                    Application.Run(form);
                }
            }
            catch (Exception ex)
            {
                // 异常兜底：弹出致命错误对话框（对应 Python 版 messagebox.showerror）
                try
                {
                    MessageBox.Show(
                        "应用程序启动失败\n\n" + ex,
                        "Fatal Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                }
                catch
                {
                    Console.Error.WriteLine("Fatal error: " + ex);
                }
                // 失败码 1 退出，与 Python sys.exit(1) 对齐
                Environment.Exit(1);
            }
        }
    }
}
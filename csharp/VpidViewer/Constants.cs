using System.Drawing;

namespace VpidViewer
{
    /// <summary>
    /// 应用程序常量配置。对应 Python 版 src/constants.py。
    /// </summary>
    internal static class Constants
    {
        public const string AppName = "USB设备ID查看";
        public const string AppVersion = "2.0.0";
        public const string AppAuthor = "USB Manager";

        // 自动刷新间隔（毫秒）
        public const int AutoRefreshIntervalMs = 100;

        // 窗口尺寸
        public const int DefaultWindowWidth = 1280;
        public const int DefaultWindowHeight = 720;
        public const int MinWindowWidth = 960;
        public const int MinWindowHeight = 600;

        // 扫描超时保护（毫秒）
        public const int ScanTimeoutMs = 10000;

        public const string StatusConnected = "Connected";
        public const string StatusError = "Error";
        public const string StatusUnknown = "Unknown";

        // 注册表 USB 枚举路径
        public const string RegistryUsbBasePath = @"SYSTEM\CurrentControlSet\Enum\USB";

        // VID/PID 正则模式
        public const string VidPattern = @"VID_([0-9A-Fa-f]{4})";
        public const string PidPattern = @"PID_([0-9A-Fa-f]{4})";

        // ==================== 颜色 ====================
        public static readonly Color ColorPrimary = ColorFromHex("#2775b6");
        public static readonly Color ColorPrimaryHover = ColorFromHex("#3A8FD0");
        public static readonly Color ColorSuccess = ColorFromHex("#1ba784");
        public static readonly Color ColorSuccessBg = ColorFromHex("#E8F8F3");
        public static readonly Color ColorDanger = ColorFromHex("#ed3321");
        public static readonly Color ColorDangerBg = ColorFromHex("#FEF0F0");
        public static readonly Color ColorText = ColorFromHex("#303133");
        public static readonly Color ColorTextSecondary = ColorFromHex("#909399");
        public static readonly Color ColorBorder = ColorFromHex("#DCDFE6");
        public static readonly Color ColorBg = ColorFromHex("#F5F7FA");
        public static readonly Color ColorWhite = ColorFromHex("#FFFFFF");

        /// <summary>
        /// 将 "#RRGGBB" 十六进制颜色串转为 Color。
        /// </summary>
        public static Color ColorFromHex(string hex)
        {
            hex = hex.TrimStart('#');
            int r = int.Parse(hex.Substring(0, 2), System.Globalization.NumberStyles.HexNumber);
            int g = int.Parse(hex.Substring(2, 2), System.Globalization.NumberStyles.HexNumber);
            int b = int.Parse(hex.Substring(4, 2), System.Globalization.NumberStyles.HexNumber);
            return Color.FromArgb(r, g, b);
        }

        /// <summary>
        /// 将颜色变亮。factor 0.0~1.0，对应 Python 版 _lighten_color。
        /// </summary>
        public static Color Lighten(Color color, double factor)
        {
            int r = (int)System.Math.Min(255, color.R + (255 - color.R) * factor);
            int g = (int)System.Math.Min(255, color.G + (255 - color.G) * factor);
            int b = (int)System.Math.Min(255, color.B + (255 - color.B) * factor);
            return Color.FromArgb(r, g, b);
        }

        /// <summary>
        /// 等宽字体（用于 VID/PID 数据展示）。
        /// </summary>
        public const string MonospaceFontFamily = "Consolas";
    }
}
using System.Text.RegularExpressions;

namespace VpidViewer.Scanner
{
    /// <summary>
    /// USB 扫描器抽象基类。对应 Python 版 src/usb_scanner/base.py 的 BaseScanner。
    /// </summary>
    public abstract class BaseScanner
    {
        private static readonly Regex VidRe = new Regex(
            Constants.VidPattern, RegexOptions.IgnoreCase);
        private static readonly Regex PidRe = new Regex(
            Constants.PidPattern, RegexOptions.IgnoreCase);

        /// <summary>
        /// 扫描当前连接的 USB 设备。
        /// </summary>
        public abstract System.Collections.Generic.List<USBDevice> Scan();

        /// <summary>
        /// 从设备 ID 中提取 VID 和 PID。
        /// 例："USB\VID_8087&PID_0024\5&1234" → ("0x8087", "0x0024")。
        /// 匹配失败返回空字符串。
        /// </summary>
        public static void ExtractVidPid(string deviceId, out string vidOut, out string pidOut)
        {
            deviceId = deviceId ?? string.Empty;
            Match vidMatch = VidRe.Match(deviceId);
            Match pidMatch = PidRe.Match(deviceId);
            vidOut = vidMatch.Success ? "0x" + vidMatch.Groups[1].Value.ToUpperInvariant() : string.Empty;
            pidOut = pidMatch.Success ? "0x" + pidMatch.Groups[1].Value.ToUpperInvariant() : string.Empty;
        }

        /// <summary>
        /// 从设备 ID 中提取序列号（反斜杠分隔的第三段）。
        /// </summary>
        public static string ExtractSerialFromDeviceId(string deviceId)
        {
            if (string.IsNullOrEmpty(deviceId))
            {
                return string.Empty;
            }
            string[] parts = deviceId.Split('\\');
            return parts.Length >= 3 ? parts[2] : string.Empty;
        }
    }
}
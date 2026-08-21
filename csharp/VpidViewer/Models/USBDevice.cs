namespace VpidViewer.Models
{
    /// <summary>
    /// USB 设备信息类。对应 Python 版 src/device_info.py 的 USBDevice。
    ///
    /// 通过 (vid, pid, serial) 三元组唯一标识一个 USB 设备。
    /// vid/pid 内部存储格式为 "0xXXXX"（带 0x 前缀的大写十六进制）。
    /// </summary>
    public class USBDevice
    {
        public string Vid { get; set; }
        public string Pid { get; set; }
        public string Serial { get; set; }
        public string Name { get; set; }
        public string Manufacturer { get; set; }
        public string Location { get; set; }
        public string Driver { get; set; }
        public string DeviceId { get; set; }
        public string PnpDeviceId { get; set; }
        public string Status { get; set; }
        public string Path { get; set; }

        public USBDevice(
            string vid = "",
            string pid = "",
            string serial = "",
            string name = "",
            string manufacturer = "",
            string location = "",
            string driver = "",
            string deviceId = "",
            string pnpDeviceId = "",
            string status = "",
            string path = "")
        {
            Vid = vid;
            Pid = pid;
            Serial = serial;
            Name = name;
            Manufacturer = manufacturer;
            Location = location;
            Driver = driver;
            DeviceId = deviceId;
            PnpDeviceId = pnpDeviceId;
            Status = status;
            Path = path;
        }

        /// <summary>
        /// 去除 0x/0X 前缀并转大写。对应 Python 版 _strip_0x。
        /// </summary>
        private static string Strip0x(string hexStr)
        {
            if (string.IsNullOrEmpty(hexStr))
            {
                return hexStr;
            }
            if (hexStr.StartsWith("0x") || hexStr.StartsWith("0X"))
            {
                return hexStr.Substring(2).ToUpperInvariant();
            }
            return hexStr.ToUpperInvariant();
        }

        /// <summary>
        /// 获取设备显示名称，优先 name → manufacturer → 兜底。
        /// </summary>
        public string GetDisplayName()
        {
            if (!string.IsNullOrEmpty(Name))
            {
                return Name;
            }
            if (!string.IsNullOrEmpty(Manufacturer))
            {
                return Manufacturer + " Device";
            }
            return "Unknown USB Device";
        }

        /// <summary>
        /// 格式化 VID，去除 0x 前缀。如 '8087'。
        /// </summary>
        public string GetFormattedVid()
        {
            return (!string.IsNullOrEmpty(Vid)) ? Strip0x(Vid) : "N/A";
        }

        /// <summary>
        /// 格式化 PID，去除 0x 前缀。如 '0024'。
        /// </summary>
        public string GetFormattedPid()
        {
            return (!string.IsNullOrEmpty(Pid)) ? Strip0x(Pid) : "N/A";
        }

        /// <summary>
        /// 'VID:PID' 格式字符串，如 '8087:0024'。
        /// </summary>
        public string GetVidPidString()
        {
            return GetFormattedVid() + ":" + GetFormattedPid();
        }

        /// <summary>
        /// 获取设备唯一标识。对应 Python 版 get_unique_key()。
        /// </summary>
        public DeviceKey GetUniqueKey()
        {
            return new DeviceKey(Vid ?? "", Pid ?? "", Serial ?? "");
        }

        /// <summary>
        /// 转换为剪贴板文本（key: value 逐行）。
        /// </summary>
        public string ToClipboardText()
        {
            string name = (!string.IsNullOrEmpty(Name)) ? Name : "未知设备";
            string vid = GetFormattedVid();
            string pid = GetFormattedPid();
            string serial = (!string.IsNullOrEmpty(Serial)) ? Serial : "N/A";
            string manufacturer = (!string.IsNullOrEmpty(Manufacturer)) ? Manufacturer : "N/A";
            string location = (!string.IsNullOrEmpty(Location)) ? Location : "N/A";
            string path = (!string.IsNullOrEmpty(Path)) ? Path : "N/A";
            string driver = (!string.IsNullOrEmpty(Driver)) ? Driver : "N/A";
            string status = (!string.IsNullOrEmpty(Status)) ? Status : "N/A";

            return "名称: " + name + "\n" +
                   "VID: " + vid + "\n" +
                   "PID: " + pid + "\n" +
                   "序列号: " + serial + "\n" +
                   "制造商: " + manufacturer + "\n" +
                   "位置: " + location + "\n" +
                   "路径: " + path + "\n" +
                   "驱动: " + driver + "\n" +
                   "状态: " + status;
        }

        /// <summary>
        /// 用于日志/调试的简明表示。
        /// </summary>
        public override string ToString()
        {
            return "USBDevice(vid=" + (Vid ?? "") + ", pid=" + (Pid ?? "") +
                   ", serial=" + (Serial ?? "") + ", name=" + (Name ?? "") + ")";
        }
    }

    /// <summary>
    /// 设备唯一键 (vid, pid, serial)。net35 无 Tuple，故自定义值类型以支持去重/哈希。
    /// </summary>
    public struct DeviceKey : IEquatable<DeviceKey>
    {
        public readonly string Vid;
        public readonly string Pid;
        public readonly string Serial;

        public DeviceKey(string vid, string pid, string serial)
        {
            Vid = vid;
            Pid = pid;
            Serial = serial;
        }

        public bool Equals(DeviceKey other)
        {
            return string.Equals(Vid, other.Vid) &&
                   string.Equals(Pid, other.Pid) &&
                   string.Equals(Serial, other.Serial);
        }

        public override bool Equals(object obj)
        {
            if (obj is DeviceKey)
            {
                return Equals((DeviceKey)obj);
            }
            return false;
        }

        public override int GetHashCode()
        {
            int h = 17;
            h = h * 31 + (Vid != null ? Vid.GetHashCode() : 0);
            h = h * 31 + (Pid != null ? Pid.GetHashCode() : 0);
            h = h * 31 + (Serial != null ? Serial.GetHashCode() : 0);
            return h;
        }

        public override string ToString()
        {
            return "(" + (Vid ?? "") + ", " + (Pid ?? "") + ", " + (Serial ?? "") + ")";
        }
    }
}
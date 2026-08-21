using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32;

namespace VpidViewer.Scanner
{
    /// <summary>
    /// Windows USB 设备扫描器。
    /// 对应 Python 版 src/usb_scanner/windows.py 的 WindowsScanner。
    ///
    /// 扫描策略（与 Python 版一致）：
    /// 1. SetupAPI（DIGCF_PRESENT）——最可靠，返回真实连接的设备；
    /// 2. 注册表——兜底方案。
    /// 注：Python 版中 _scan_via_wmi 为从未被调用的死代码，此处不复刻。
    /// </summary>
    public class WindowsScanner : BaseScanner
    {
        #region SetupAPI 常量与结构
        private const uint DIGCF_PRESENT = 0x00000002;
        private const uint DIGCF_ALLCLASSES = 0x00000004;

        private const uint SPDRP_DEVICEDESC = 0x00000000;
        private const uint SPDRP_DRIVER = 0x00000009;
        private const uint SPDRP_FRIENDLYNAME = 0x0000000C;
        private const uint SPDRP_LOCATION_INFORMATION = 0x0000000D;
        private const uint SPDRP_MFG = 0x0000000F;

        private const int ERROR_INSUFFICIENT_BUFFER = 122;

        [StructLayout(LayoutKind.Sequential)]
        private struct SP_DEVINFO_DATA
        {
            public uint cbSize;
            public Guid ClassGuid;
            public uint DevInst;
            public IntPtr Reserved;
        }
        #endregion

        #region SetupAPI P/Invoke
        [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr SetupDiGetClassDevsW(
            IntPtr classGuid, string enumerator, IntPtr hwndParent, uint flags);

        [DllImport("setupapi.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool SetupDiEnumDeviceInfo(
            IntPtr devInfoSet, uint memberIndex, ref SP_DEVINFO_DATA devInfoData);

        [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool SetupDiGetDeviceInstanceIdW(
            IntPtr devInfoSet, ref SP_DEVINFO_DATA devInfoData,
            StringBuilder deviceInstanceId, uint deviceInstanceIdSize, out uint requiredSize);

        [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool SetupDiGetDeviceRegistryPropertyW(
            IntPtr devInfoSet, ref SP_DEVINFO_DATA devInfoData, uint property,
            out uint propertyRegDataType, IntPtr propertyBuffer,
            uint propertyBufferSize, out uint requiredSize);

        [DllImport("setupapi.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool SetupDiDestroyDeviceInfoList(IntPtr devInfoSet);
        #endregion

        /// <summary>
        /// 扫描当前真实连接的 USB 设备。
        /// </summary>
        public override List<USBDevice> Scan()
        {
            List<USBDevice> devices = ScanViaSetupApi();
            if (devices.Count > 0)
            {
                return devices;
            }

            List<USBDevice> regDevices = ScanViaRegistry();
            if (regDevices.Count > 0)
            {
                return regDevices;
            }

            return new List<USBDevice>();
        }

        // ============================================================
        // 扫描方法 1：SetupAPI（最可靠）
        // ============================================================

        private List<USBDevice> ScanViaSetupApi()
        {
            List<USBDevice> devices = new List<USBDevice>();
            IntPtr devInfoSet = IntPtr.Zero;

            try
            {
                devInfoSet = SetupDiGetClassDevsW(
                    IntPtr.Zero, null, IntPtr.Zero, DIGCF_PRESENT | DIGCF_ALLCLASSES);
                if (devInfoSet == IntPtr.Zero || devInfoSet == new IntPtr(-1))
                {
                    return devices;
                }

                Dictionary<DeviceKey, bool> seenKeys = new Dictionary<DeviceKey, bool>();
                uint index = 0;

                while (true)
                {
                    SP_DEVINFO_DATA devInfo = new SP_DEVINFO_DATA();
                    devInfo.cbSize = (uint)Marshal.SizeOf(typeof(SP_DEVINFO_DATA));

                    if (!SetupDiEnumDeviceInfo(devInfoSet, index, ref devInfo))
                    {
                        break;
                    }

                    StringBuilder instanceBuf = new StringBuilder(1024);
                    uint required = 0;
                    if (SetupDiGetDeviceInstanceIdW(
                            devInfoSet, ref devInfo, instanceBuf, (uint)instanceBuf.Capacity, out required))
                    {
                        string instanceId = instanceBuf.ToString();
                        string vid, pid;
                        ExtractVidPid(instanceId, out vid, out pid);
                        if (!string.IsNullOrEmpty(vid) && !string.IsNullOrEmpty(pid))
                        {
                            string serial = ExtractSerialFromDeviceId(instanceId);
                            DeviceKey key = new DeviceKey(vid, pid, serial);
                            if (!seenKeys.ContainsKey(key))
                            {
                                seenKeys[key] = true;

                                string name = GetRegistryProperty(devInfoSet, ref devInfo, SPDRP_FRIENDLYNAME);
                                if (string.IsNullOrEmpty(name))
                                {
                                    name = GetRegistryProperty(devInfoSet, ref devInfo, SPDRP_DEVICEDESC);
                                }
                                string manufacturer = GetRegistryProperty(devInfoSet, ref devInfo, SPDRP_MFG);
                                string driver = GetRegistryProperty(devInfoSet, ref devInfo, SPDRP_DRIVER);
                                string location = GetRegistryProperty(devInfoSet, ref devInfo, SPDRP_LOCATION_INFORMATION);

                                devices.Add(BuildDevice(
                                    vid, pid, serial, name, manufacturer,
                                    location, driver, instanceId, instanceId,
                                    Constants.StatusConnected, instanceId));
                            }
                        }
                    }

                    index++;
                }
            }
            catch (Exception)
            {
                // SetupAPI 失败则降级为注册表扫描；返回空列表触发 fallback
            }
            finally
            {
                if (devInfoSet != IntPtr.Zero && devInfoSet != new IntPtr(-1))
                {
                    SetupDiDestroyDeviceInfoList(devInfoSet);
                }
            }

            return devices;
        }

        private static string GetRegistryProperty(
            IntPtr devInfoSet, ref SP_DEVINFO_DATA devInfo, uint property)
        {
            uint dataType;
            uint required;
            bool result = SetupDiGetDeviceRegistryPropertyW(
                devInfoSet, ref devInfo, property, out dataType,
                IntPtr.Zero, 0, out required);

            if (!result)
            {
                // ERROR_INSUFFICIENT_BUFFER 属预期：required 已给出所需大小
                if (Marshal.GetLastWin32Error() != ERROR_INSUFFICIENT_BUFFER)
                {
                    return string.Empty;
                }
            }

            int size = (int)(required > 0 ? required : 512);
            IntPtr buffer = Marshal.AllocHGlobal(size);
            try
            {
                if (SetupDiGetDeviceRegistryPropertyW(
                        devInfoSet, ref devInfo, property, out dataType,
                        buffer, (uint)size, out required))
                {
                    return Marshal.PtrToStringUni(buffer);
                }
                return string.Empty;
            }
            finally
            {
                Marshal.FreeHGlobal(buffer);
            }
        }

        // ============================================================
        // 扫描方法 2：注册表（兜底）
        // ============================================================

        private List<USBDevice> ScanViaRegistry()
        {
            List<USBDevice> devices = new List<USBDevice>();
            try
            {
                using (RegistryKey baseKey = Registry.LocalMachine.OpenSubKey(Constants.RegistryUsbBasePath))
                {
                    if (baseKey == null)
                    {
                        return devices;
                    }

                    string[] vidPidKeyNames = baseKey.GetSubKeyNames();
                    foreach (string vidPidKeyName in vidPidKeyNames)
                    {
                        string vid, pid;
                        ExtractVidPid(vidPidKeyName, out vid, out pid);
                        if (!string.IsNullOrEmpty(vid) && !string.IsNullOrEmpty(pid))
                        {
                            string vidPidPath = Constants.RegistryUsbBasePath + "\\" + vidPidKeyName;
                            EnumerateRegistryInstances(vidPidPath, vid, pid, devices);
                        }
                    }
                }
            }
            catch (Exception)
            {
                // 注册表扫描失败，忽略
            }
            return devices;
        }

        private static void EnumerateRegistryInstances(
            string vidPidPath, string vid, string pid, List<USBDevice> devices)
        {
            try
            {
                using (RegistryKey vidPidKey = Registry.LocalMachine.OpenSubKey(vidPidPath))
                {
                    if (vidPidKey == null)
                    {
                        return;
                    }
                    string[] instanceNames = vidPidKey.GetSubKeyNames();
                    foreach (string instanceName in instanceNames)
                    {
                        string instancePath = vidPidPath + "\\" + instanceName;
                        USBDevice device = ParseRegistryDevice(instancePath, vid, pid, instanceName);
                        if (device != null)
                        {
                            devices.Add(device);
                        }
                    }
                }
            }
            catch (Exception)
            {
                // 单个 VID/PID 失败，忽略并继续
            }
        }

        private static USBDevice ParseRegistryDevice(
            string path, string vid, string pid, string serialPart)
        {
            string vidHex = vid.Replace("0x", "").Replace("0X", "");
            string pidHex = pid.Replace("0x", "").Replace("0X", "");
            string deviceId = "USB\\VID_" + vidHex + "&PID_" + pidHex + "\\" + serialPart;

            try
            {
                using (RegistryKey key = Registry.LocalMachine.OpenSubKey(path))
                {
                    if (key == null)
                    {
                        return null;
                    }

                    string errorCodeStr = GetRegistryValue(key, "ConfigManagerErrorCode");
                    if (!IsDeviceConnected(errorCodeStr))
                    {
                        return null;
                    }

                    string configFlagsStr = GetRegistryValue(key, "ConfigFlags");
                    if (configFlagsStr != null)
                    {
                        int configFlags;
                        if (int.TryParse(configFlagsStr, out configFlags))
                        {
                            if ((configFlags & 0x00000004) != 0)
                            {
                                return null;
                            }
                        }
                    }

                    string friendly = GetRegistryValue(key, "FriendlyName");
                    if (string.IsNullOrEmpty(friendly))
                    {
                        friendly = GetRegistryValue(key, "DeviceDesc");
                    }
                    string name = CleanRegistryString(friendly);
                    string manufacturer = CleanRegistryString(GetRegistryValue(key, "Mfg"));
                    string driver = GetRegistryValue(key, "Driver") ?? string.Empty;
                    string location = GetRegistryValue(key, "LocationInformation") ?? string.Empty;

                    return BuildDevice(
                        vid, pid, serialPart, name, manufacturer,
                        location, driver, deviceId, deviceId,
                        Constants.StatusConnected, deviceId);
                }
            }
            catch (Exception)
            {
                return null;
            }
        }

        // ============================================================
        // 工具方法
        // ============================================================

        private static USBDevice BuildDevice(
            string vid, string pid, string serial, string name, string manufacturer,
            string location, string driver, string deviceId, string pnpDeviceId,
            string status, string path)
        {
            if (string.IsNullOrEmpty(name))
            {
                name = "USB Device";
            }
            return new USBDevice(
                vid: vid, pid: pid, serial: serial, name: name,
                manufacturer: manufacturer, location: location, driver: driver,
                deviceId: deviceId, pnpDeviceId: pnpDeviceId, status: status, path: path);
        }

        private static bool IsDeviceConnected(string errorCode)
        {
            // ConfigManagerErrorCode：0 = 设备正常工作（已连接），其他值 = 有问题或已断开
            if (string.IsNullOrEmpty(errorCode))
            {
                return false;
            }
            int code;
            return int.TryParse(errorCode, out code) && code == 0;
        }

        private static string GetRegistryValue(RegistryKey key, string valueName)
        {
            try
            {
                object value = key.GetValue(valueName);
                if (value == null)
                {
                    return null;
                }
                string[] arr = value as string[];
                if (arr != null && arr.Length > 0)
                {
                    return arr[0];
                }
                return value.ToString();
            }
            catch (Exception)
            {
                return null;
            }
        }

        /// <summary>
        /// 清理注册表字符串值，提取反斜杠分隔的最后一段。
        /// </summary>
        private static string CleanRegistryString(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return string.Empty;
            }
            if (value.Contains("\\"))
            {
                string[] parts = value.Split('\\');
                return parts[parts.Length - 1];
            }
            return value;
        }
    }
}
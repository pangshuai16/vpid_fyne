using System.Collections.Generic;

namespace VpidViewer.Scanner
{
    /// <summary>
    /// 设备比对工具。对应 Python 版 src/usb_scanner/__init__.py 的 compare_devices。
    /// </summary>
    public static class DeviceComparer
    {
        /// <summary>
        /// 对比两个设备列表，找出新增和移除的设备。
        /// 基于 (vid, pid, serial) 唯一键。
        /// </summary>
        /// <returns>输出 (added, removed) 两个列表。</returns>
        public static void Compare(
            IList<USBDevice> oldDevices,
            IList<USBDevice> newDevices,
            out List<USBDevice> added,
            out List<USBDevice> removed)
        {
            HashSet<DeviceKey> oldKeys = new HashSet<DeviceKey>();
            if (oldDevices != null)
            {
                foreach (USBDevice d in oldDevices)
                {
                    oldKeys.Add(d.GetUniqueKey());
                }
            }

            HashSet<DeviceKey> newKeys = new HashSet<DeviceKey>();
            if (newDevices != null)
            {
                foreach (USBDevice d in newDevices)
                {
                    newKeys.Add(d.GetUniqueKey());
                }
            }

            added = new List<USBDevice>();
            removed = new List<USBDevice>();

            if (newDevices != null)
            {
                foreach (USBDevice d in newDevices)
                {
                    if (!oldKeys.Contains(d.GetUniqueKey()))
                    {
                        added.Add(d);
                    }
                }
            }

            if (oldDevices != null)
            {
                foreach (USBDevice d in oldDevices)
                {
                    if (!newKeys.Contains(d.GetUniqueKey()))
                    {
                        removed.Add(d);
                    }
                }
            }
        }

        /// <summary>
        /// 判断两个设备列表是否真正发生变化（唯一键集合是否一致）。
        /// </summary>
        public static bool HasChanged(IList<USBDevice> a, IList<USBDevice> b)
        {
            HashSet<DeviceKey> ka = KeysOf(a);
            HashSet<DeviceKey> kb = KeysOf(b);
            if (ka.Count != kb.Count)
            {
                return true;
            }
            foreach (DeviceKey k in ka)
            {
                if (!kb.Contains(k))
                {
                    return true;
                }
            }
            return false;
        }

        private static HashSet<DeviceKey> KeysOf(IList<USBDevice> devices)
        {
            HashSet<DeviceKey> keys = new HashSet<DeviceKey>();
            if (devices != null)
            {
                foreach (USBDevice d in devices)
                {
                    keys.Add(d.GetUniqueKey());
                }
            }
            return keys;
        }
    }
}
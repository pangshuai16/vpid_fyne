#include "core/linux_scanner.h"

#ifndef _WIN32

#include "common/constants.h"

#include <libusb.h>
#include <algorithm>
#include <cstdio>
#include <set>
#include <string>
#include <vector>

namespace vpid {

std::string LinuxScanner::getString(libusb_device* dev, uint8_t idx) {
    if (idx == 0) return std::string();
    libusb_device_handle* h = nullptr;
    if (libusb_open(dev, &h) != 0) return std::string();
    unsigned char buf[256] = {0};
    int len = libusb_get_string_descriptor_ascii(h, idx, buf, sizeof(buf));
    libusb_close(h);
    if (len < 0) return std::string();
    return std::string((const char*)buf, (size_t)len);
}

std::vector<USBDevice> LinuxScanner::scan() {
    std::vector<USBDevice> devices;
    libusb_context* ctx = nullptr;
    if (libusb_init(&ctx) != 0) return devices;

    libusb_device** list = nullptr;
    ssize_t count = libusb_get_device_list(ctx, &list);
    if (count < 0) { libusb_exit(ctx); return devices; }

    std::set<DeviceKey> seen;
    for (ssize_t i = 0; i < count; ++i) {
        libusb_device* dev = list[i];
        struct libusb_device_descriptor desc;
        if (libusb_get_device_descriptor(dev, &desc) != 0) continue;
        if (desc.idVendor == 0 && desc.idProduct == 0) continue;

        char vidhex[16], pidhex[16];
        snprintf(vidhex, sizeof(vidhex), "0x%04X", desc.idVendor);
        snprintf(pidhex, sizeof(pidhex), "0x%04X", desc.idProduct);
        std::string vid(vidhex), pid(pidhex);

        std::string serial = getString(dev, desc.iSerialNumber);
        std::string name = getString(dev, desc.iProduct);
        std::string manufacturer = getString(dev, desc.iManufacturer);

        DeviceKey key{vid, pid, serial};
        if (!seen.insert(key).second) continue;

        char didbuf[128];
        snprintf(didbuf, sizeof(didbuf), "USB\\VID_%04X&PID_%04X\\%s",
                 desc.idVendor, desc.idProduct, serial.c_str());
        std::string device_id(didbuf);

        char loc[64];
        snprintf(loc, sizeof(loc), "bus %u device %u",
                 libusb_get_bus_number(dev), libusb_get_device_address(dev));

        USBDevice d;
        d.vid = vid; d.pid = pid; d.serial = serial;
        d.name = name.empty() ? std::string("USB Device") : name;
        d.manufacturer = manufacturer;
        d.location = loc;
        d.driver.clear();
        d.device_id = device_id; d.pnp_device_id = device_id;
        d.status = kStatusConnected; d.path = device_id;
        devices.push_back(d);
    }

    libusb_free_device_list(list, 1);
    libusb_exit(ctx);
    return devices;
}

std::unique_ptr<Scanner> createScanner() { return std::make_unique<LinuxScanner>(); }

} // namespace vpid

#endif
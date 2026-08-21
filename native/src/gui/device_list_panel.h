#pragma once
#include <vector>
#include <wx/wx.h>
#include <wx/listctrl.h>
#include "core/device_info.h"

namespace vpid {

// 全部 USB 设备列表面板，对应 Python 版 DeviceListPanel
class DeviceListPanel : public wxPanel {
public:
    DeviceListPanel(wxWindow* parent);

    void updateDevices(const std::vector<USBDevice>& devices);
    const USBDevice* getSelectedDevice() const;
    void clearSelection();
    void clear();

    wxListCtrl* list() const { return m_list; }
    size_t deviceCount() const { return m_devices.size(); }

private:
    void buildUi();
    void populate();

    std::vector<USBDevice> m_devices;
    wxStaticText* m_title   = nullptr;
    wxStaticText* m_count   = nullptr;
    wxListCtrl*   m_list    = nullptr;
    long m_lastSelection    = -1; // 上一选中行，用于恢复
};

} // namespace vpid
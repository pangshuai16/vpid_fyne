#pragma once
#include <set>
#include <vector>
#include <wx/wx.h>
#include <wx/listctrl.h>
#include "core/device_info.h"

namespace vpid {

// 新增/移除设备面板（右上+右下），对应 Python 版 DeviceChangePanel
class DeviceChangePanel : public wxPanel {
public:
    DeviceChangePanel(wxWindow* parent);

    // 指向内部容器，主线程内使用；无选中返回 nullptr
    const USBDevice* getSelectedDevice() const;
    void clearSelection();

    void updateChanges(const std::vector<USBDevice>& added, const std::vector<USBDevice>& removed);
    void clear();

    bool addedContains(const DeviceKey& key) const { return m_addedKeys.count(key) != 0; }

    wxListCtrl* addedList() const;
    wxListCtrl* removedList() const;

private:
    struct Section;

    void buildUi();
    Section* createSection(wxWindow* parent, const wxString& title,
                           const wxColour& bg, const wxColour& fg,
                           wxBoxSizer* into);

    Section* m_added   = nullptr;
    Section* m_removed = nullptr;
    std::vector<USBDevice> m_addedDevices, m_removedDevices;
    std::set<DeviceKey> m_addedKeys;
};

} // namespace vpid
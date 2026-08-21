#include "gui/device_list_panel.h"
#include "common/constants.h"
#include <algorithm>

namespace vpid {

DeviceListPanel::DeviceListPanel(wxWindow* parent) : wxPanel(parent) { buildUi(); }

void DeviceListPanel::buildUi() {
    wxBoxSizer* root = new wxBoxSizer(wxVERTICAL);

    // 标题行
    wxPanel* header = new wxPanel(this);
    header->SetBackgroundColour(colWhite());
    wxBoxSizer* hs = new wxBoxSizer(wxHORIZONTAL);
    m_title = new wxStaticText(header, wxID_ANY, "全部 USB 设备",
                               wxDefaultPosition, wxDefaultSize, wxALIGN_LEFT);
    m_title->SetFont(m_title->GetFont().MakeBold());
    m_title->SetForegroundColour(colText());
    m_count = new wxStaticText(header, wxID_ANY, "0", wxDefaultPosition, wxDefaultSize, wxALIGN_RIGHT);
    m_count->SetFont(m_count->GetFont().MakeBold());
    m_count->SetForegroundColour(colPrimary());
    hs->Add(m_title, 1, wxALIGN_CENTER_VERTICAL);
    hs->Add(m_count, 0, wxALIGN_CENTER_VERTICAL);
    header->SetSizer(hs);

    // 列表
    m_list = new wxListCtrl(this, wxID_ANY, wxDefaultPosition, wxDefaultSize,
                            wxLC_REPORT | wxLC_SINGLE_SEL);
    m_list->AppendColumn("VID", wxLIST_FORMAT_CENTER, 70);
    m_list->AppendColumn("PID", wxLIST_FORMAT_CENTER, 70);
    m_list->AppendColumn("设备名称", wxLIST_FORMAT_LEFT, 200);
    m_list->AppendColumn("路径", wxLIST_FORMAT_LEFT, 340);

    root->Add(header, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 6);
    root->Add(m_list, 1, wxEXPAND | wxALL, 4);
    SetSizer(root);
}

void DeviceListPanel::updateDevices(const std::vector<USBDevice>& devices) {
    // 与 Python 版排序一致：pid, vid, name
    m_devices = devices;
    std::stable_sort(m_devices.begin(), m_devices.end(),
        [](const USBDevice& a, const USBDevice& b) {
            int c = a.getFormattedPid().compare(b.getFormattedPid());
            if (c != 0) return c < 0;
            c = a.getFormattedVid().compare(b.getFormattedVid());
            if (c != 0) return c < 0;
            return a.getDisplayName() < b.getDisplayName();
        });
    populate();
    m_count->SetLabel(std::to_string(m_devices.size()));
}

void DeviceListPanel::populate() {
    const USBDevice* sel = getSelectedDevice();
    m_list->DeleteAllItems();
    long selectedIndex = -1;
    for (size_t i = 0; i < m_devices.size(); ++i) {
        const USBDevice& d = m_devices[i];
        long idx = m_list->InsertItem((long)i, d.getFormattedVid());
        m_list->SetItem(idx, 1, d.getFormattedPid());
        m_list->SetItem(idx, 2, d.getDisplayName());
        m_list->SetItem(idx, 3, d.path.empty() ? std::string("-") : d.path);
        if (sel && sel->getUniqueKey() == d.getUniqueKey()) selectedIndex = idx;
    }
    if (selectedIndex >= 0) {
        m_list->SetItemState(selectedIndex, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
        m_list->EnsureVisible(selectedIndex);
    }
}

const USBDevice* DeviceListPanel::getSelectedDevice() const {
    long idx = m_list->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (idx < 0 || idx >= (long)m_devices.size()) return nullptr;
    return &m_devices[(size_t)idx];
}

void DeviceListPanel::clearSelection() {
    long idx = m_list->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    while (idx >= 0) {
        m_list->SetItemState(idx, 0, wxLIST_STATE_SELECTED);
        idx = m_list->GetNextItem(idx, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    }
}

void DeviceListPanel::clear() {
    m_list->DeleteAllItems();
    m_devices.clear();
    m_count->SetLabel("0");
}

} // namespace vpid
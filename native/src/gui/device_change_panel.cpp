#include "gui/device_change_panel.h"
#include "common/constants.h"
#include <wx/statline.h>

namespace vpid {

// 单个变化区域（新增或移除）
struct DeviceChangePanel::Section {
    wxStaticText* count = nullptr;
    wxListCtrl*   list  = nullptr;
    std::vector<USBDevice> devices;

    const USBDevice* selected() const {
        long idx = list->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
        if (idx < 0 || idx >= (long)devices.size()) return nullptr;
        return &devices[(size_t)idx];
    }
    void rebuild(const std::vector<USBDevice>& src) {
        devices = src;
        list->DeleteAllItems();
        for (size_t i = 0; i < devices.size(); ++i) {
            const USBDevice& d = devices[i];
            long idx = list->InsertItem((long)i, d.getFormattedVid());
            list->SetItem(idx, 1, d.getFormattedPid());
            list->SetItem(idx, 2, d.getDisplayName());
        }
        count->SetLabel(std::to_string(devices.size()));
    }
    void clearList() { list->DeleteAllItems(); devices.clear(); count->SetLabel("0"); }
};

DeviceChangePanel::DeviceChangePanel(wxWindow* parent) : wxPanel(parent) { buildUi(); }

DeviceChangePanel::Section* DeviceChangePanel::createSection(
        wxWindow* parent, const wxString& title, const wxColour& bg, const wxColour& fg,
        wxBoxSizer* into) {
    Section* s = new Section;

    wxPanel* box = new wxPanel(parent);
    box->SetBackgroundColour(colWhite());
    wxBoxSizer* v = new wxBoxSizer(wxVERTICAL);

    wxPanel* header = new wxPanel(box);
    header->SetBackgroundColour(bg);
    wxBoxSizer* hs = new wxBoxSizer(wxHORIZONTAL);
    wxStaticText* t = new wxStaticText(header, wxID_ANY, title);
    t->SetFont(t->GetFont().MakeBold());
    t->SetForegroundColour(fg);
    t->SetBackgroundColour(bg);
    s->count = new wxStaticText(header, wxID_ANY, "0", wxDefaultPosition, wxDefaultSize, wxALIGN_RIGHT);
    s->count->SetFont(s->count->GetFont().MakeBold());
    s->count->SetForegroundColour(fg);
    s->count->SetBackgroundColour(bg);
    hs->Add(t, 1, wxALIGN_CENTER_VERTICAL | wxLEFT, 6);
    hs->Add(s->count, 0, wxALIGN_CENTER_VERTICAL | wxRIGHT, 6);
    header->SetSizer(hs);

    s->list = new wxListCtrl(box, wxID_ANY, wxDefaultPosition, wxDefaultSize,
                             wxLC_REPORT | wxLC_SINGLE_SEL);
    s->list->AppendColumn("VID", wxLIST_FORMAT_CENTER, 80);
    s->list->AppendColumn("PID", wxLIST_FORMAT_CENTER, 80);
    s->list->AppendColumn("设备名称", wxLIST_FORMAT_LEFT, 220);

    v->Add(header, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 4);
    v->Add(s->list, 1, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, 4);
    box->SetSizer(v);

    into->Add(box, 1, wxEXPAND);
    return s;
}

void DeviceChangePanel::buildUi() {
    wxBoxSizer* root = new wxBoxSizer(wxVERTICAL);

    // 上：新增；分隔线；下：移除
    wxPanel* top = new wxPanel(this);
    top->SetBackgroundColour(colWhite());
    wxBoxSizer* topS = new wxBoxSizer(wxVERTICAL);
    m_added = createSection(top, "+ 新增设备", colSuccessBg(), colSuccess(), topS);
    top->SetSizer(topS);
    root->Add(top, 1, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 4);

    wxStaticLine* sep = new wxStaticLine(this);
    root->Add(sep, 0, wxEXPAND | wxLEFT | wxRIGHT, 8);

    wxPanel* bot = new wxPanel(this);
    bot->SetBackgroundColour(colWhite());
    wxBoxSizer* botS = new wxBoxSizer(wxVERTICAL);
    m_removed = createSection(bot, "- 移除设备", colDangerBg(), colDanger(), botS);
    bot->SetSizer(botS);
    root->Add(bot, 1, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, 4);

    SetSizer(root);
}

void DeviceChangePanel::updateChanges(const std::vector<USBDevice>& added,
                                      const std::vector<USBDevice>& removed) {
    m_addedDevices = added;
    m_removedDevices = removed;
    m_addedKeys.clear();
    for (const auto& d : added) m_addedKeys.insert(d.getUniqueKey());
    m_added->rebuild(added);
    m_removed->rebuild(removed);
}

const USBDevice* DeviceChangePanel::getSelectedDevice() const {
    if (const USBDevice* d = m_added->selected()) return d;
    return m_removed->selected();
}

void DeviceChangePanel::clearSelection() {
    auto clear = [](wxListCtrl* l) {
        long i = l->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
        while (i >= 0) { l->SetItemState(i, 0, wxLIST_STATE_SELECTED); i = l->GetNextItem(i, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED); }
    };
    clear(m_added->list);
    clear(m_removed->list);
}

void DeviceChangePanel::clear() {
    m_added->clearList();
    m_removed->clearList();
    m_addedDevices.clear();
    m_removedDevices.clear();
    m_addedKeys.clear();
}

wxListCtrl* DeviceChangePanel::addedList() const { return m_added ? m_added->list : nullptr; }
wxListCtrl* DeviceChangePanel::removedList() const { return m_removed ? m_removed->list : nullptr; }

} // namespace vpid
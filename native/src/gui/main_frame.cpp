#include "gui/main_frame.h"

#include "common/constants.h"
#include "core/device_scanner.h"
#include "core/device_comparer.h"

#include <wx/statline.h>
#include <wx/clipbrd.h>
#include <thread>

namespace vpid {

wxDEFINE_EVENT(wxEVT_SCAN_RESULT, ScanResultEvent);

namespace {
// 控件/定时器 ID
const int kBtnStopRefresh = 2001;
const int kBtnAutoRefresh = 2002;
const int kBtnManualRefresh = 2003;
const int kBtnBaseline = 2004;
const int kBtnCopy = 2005;
const int kTimerAuto = 2006;

// 按钮统一样式（扁平、自绘底色，曲线接近 Python Label 模拟按钮）
wxButton* makeButton(wxWindow* parent, int id, const wxString& text, const wxColour& bg) {
    wxButton* b = new wxButton(parent, id, text);
    b->SetBackgroundColour(bg);
    b->SetForegroundColour(colWhite());
    b->SetFont(b->GetFont().MakeBold());
    b->SetWindowStyleFlag(wxBU_EXACTFIT);
    return b;
}

} // namespace

MainFrame::MainFrame() : wxFrame(nullptr, wxID_ANY,
                                  wxString::FromUTF8(kAppName),
                                  wxDefaultPosition,
                                  wxSize(kDefaultWindowWidth, kDefaultWindowHeight)),
                          m_timer(this, kTimerAuto) {
    SetMinSize(wxSize(kMinWindowWidth, kMinWindowHeight));
    buildUi();

    // 事件绑定
    Bind(wxEVT_SCAN_RESULT, &MainFrame::onScanResult, this);
    Bind(wxEVT_TIMER, &MainFrame::onAutoRefreshTick, this, kTimerAuto);
    Bind(wxEVT_CLOSE_WINDOW, &MainFrame::onClose, this);

    Bind(wxEVT_BUTTON, &MainFrame::onStopRefresh, this, kBtnStopRefresh);
    Bind(wxEVT_BUTTON, &MainFrame::onStartAutoRefresh, this, kBtnAutoRefresh);
    Bind(wxEVT_BUTTON, &MainFrame::onManualRefresh, this, kBtnManualRefresh);
    Bind(wxEVT_BUTTON, &MainFrame::onSetBaseline, this, kBtnBaseline);
    Bind(wxEVT_BUTTON, &MainFrame::onCopy, this, kBtnCopy);

    m_list->list()->Bind(wxEVT_LIST_ITEM_SELECTED, &MainFrame::onLeftSelect, this);
    m_change->addedList()->Bind(wxEVT_LIST_ITEM_SELECTED, &MainFrame::onRightSelect, this);
    m_change->removedList()->Bind(wxEVT_LIST_ITEM_SELECTED, &MainFrame::onRightSelect, this);

    setupDeviceNotifier();

    // 启动：首次扫描 + 自动刷新
    startScan();
    if (m_autoRefresh) m_timer.Start(kAutoRefreshIntervalMs);
}

MainFrame::~MainFrame() {
    m_closing = true;
    m_timer.Stop();
#ifdef _WIN32
    if (m_hDevNotify) {
        UnregisterDeviceNotification((HDEVNOTIFY)m_hDevNotify);
        m_hDevNotify = nullptr;
    }
#endif
}

void MainFrame::buildUi() {
    // 顶部工具栏
    wxPanel* toolbar = new wxPanel(this);
    toolbar->SetBackgroundColour(colWhite());
    wxBoxSizer* tb = new wxBoxSizer(wxHORIZONTAL);
    m_deviceCount = new wxStaticText(toolbar, wxID_ANY, "0 个设备已连接");
    m_deviceCount->SetFont(m_deviceCount->GetFont().MakeBold());
    m_deviceCount->SetForegroundColour(colText());
    m_deviceCount->SetBackgroundColour(colWhite());
    tb->Add(m_deviceCount, 0, wxALIGN_CENTER_VERTICAL | wxRIGHT, 14);

    m_stopRefreshBtn = makeButton(toolbar, kBtnStopRefresh, wxT("停止刷新"), colDanger());
    m_autoRefreshBtn = makeButton(toolbar, kBtnAutoRefresh, wxT("自动刷新"), colSuccess());
    m_manualRefreshBtn = makeButton(toolbar, kBtnManualRefresh, wxT("手动刷新"), colPrimary());
    m_baselineBtn = makeButton(toolbar, kBtnBaseline, wxT("设为基准"), colSuccess());
    tb->Add(m_stopRefreshBtn, 0, wxRIGHT, 6);
    tb->Add(m_autoRefreshBtn, 0, wxRIGHT, 6);
    tb->Add(m_manualRefreshBtn, 0, wxRIGHT, 6);
    tb->Add(m_baselineBtn, 0, wxRIGHT, 6);

    tb->AddStretchSpacer(1);
    m_copyBtn = makeButton(toolbar, kBtnCopy, wxT("复制"), colPrimary());
    tb->Add(m_copyBtn, 0, wxRIGHT, 6);
    toolbar->SetSizer(tb);

    // 左右分栏内容
    wxSplitterWindow* split = new wxSplitterWindow(this);
    m_list = new DeviceListPanel(split);
    m_change = new DeviceChangePanel(split);
    split->SetMinimumPaneSize(120);
    split->SplitVertically(m_list, m_change, (int)(kDefaultWindowWidth * 0.6));

    // 状态栏
    m_statusBar = CreateStatusBar(2);
    const int widths[2] = {-2, -1};
    m_statusBar->SetStatusWidths(2, widths);

    // 总体布局
    wxBoxSizer* root = new wxBoxSizer(wxVERTICAL);
    root->Add(toolbar, 0, wxEXPAND);
    root->Add(new wxStaticLine(this), 0, wxEXPAND);
    root->Add(split, 1, wxEXPAND | wxALL, 4);
    SetSizer(root);

    refreshButtons();
}

void MainFrame::setupDeviceNotifier() {
#ifdef _WIN32
    // 监听 USB 设备接口插拔（RegisterDeviceNotification），跨 WM_DEVICECHANGE
    DEV_BROADCAST_DEVICEINTERFACE_W filter{};
    filter.dbcc_size = sizeof(filter);
    filter.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE;
    filter.dbcc_classguid = {0xA5DCBF10, 0x6530, 0x11D2,
                             {0x90, 0x1F, 0x00, 0xC0, 0x4F, 0xB9, 0x51, 0xED}};
    HDEVNOTIFY n = RegisterDeviceNotificationW(GetHandle(), &filter, DEVICE_NOTIFY_WINDOW_HANDLE);
    m_hDevNotify = (void*)n;
#endif
}

// ==================== 扫描控制 ====================

void MainFrame::startScan() {
    if (m_scanning.exchange(true)) return; // 防并发
    if (m_closing) { m_scanning = false; return; }

    std::thread t([this]() {
        auto result = std::make_shared<std::vector<USBDevice>>(scanUsbDevices());
        if (!m_closing) {
            ScanResultEvent* e = new ScanResultEvent(wxEVT_SCAN_RESULT);
            e->devices = result;
            wxQueueEvent(this, e); // 线程安全，投递到主线程
        }
    });
    t.detach();
}

void MainFrame::onScanResult(ScanResultEvent& evt) {
    m_scanning = false;
    if (m_closing) return;
    updateDeviceList(*evt.devices);
    if (m_eventPending > 0) {
        --m_eventPending;
        startScan();
    }
}

void MainFrame::onAutoRefreshTick(wxTimerEvent&) {
    if (!m_autoRefresh || m_closing) return;
    if (!m_scanning) startScan();
}

void MainFrame::triggerRescan() {
    if (m_scanning) { ++m_eventPending; return; }
    startScan();
}

void MainFrame::onClose(wxCloseEvent&) {
    m_closing = true;
    m_timer.Stop();
    Destroy();
}

// ==================== 核心逻辑 ====================

void MainFrame::updateDeviceList(const std::vector<USBDevice>& devices) {
    size_t prevCount = m_devices.size();

    // 首次扫描自动设为基准
    if (m_baseline.empty()) {
        m_baseline = devices;
        updateBaselineStatus();
    }

    std::vector<USBDevice> added, removed;
    DeviceComparer::compare(m_baseline, devices, added, removed);

    bool changed = DeviceComparer::hasChanged(m_devices, devices);
    m_devices = devices;

    if (changed) {
        m_list->updateDevices(devices);
        m_change->updateChanges(added, removed);

        wxString change;
        if (!added.empty()) change += wxString::Format(" (+%d)", (int)added.size());
        if (!removed.empty()) change += wxString::Format(" (-%d)", (int)removed.size());

        m_deviceCount->SetLabel(wxString::Format("%d 个设备已连接%s", (int)devices.size(), change));

        wxDateTime now = wxDateTime::Now();
        wxString ts = now.Format("%H:%M:%S");
        setStatus(wxString::Format("最后刷新: %s | 设备数: %d -> %d", ts, (int)prevCount, (int)devices.size()));
    }
}

// ==================== 用户操作 ====================

void MainFrame::onSetBaseline(wxCommandEvent&) {
    if (m_devices.empty()) {
        wxMessageBox("当前没有设备列表，请先刷新", "提示", wxOK | wxICON_INFORMATION, this);
        return;
    }
    m_baseline = m_devices;
    updateBaselineStatus();
    std::vector<USBDevice> added, removed;
    DeviceComparer::compare(m_baseline, m_devices, added, removed);
    m_change->updateChanges(added, removed);
    setStatus("已将当前设备列表设为基准");
    m_deviceCount->SetLabel(wxString::Format("%d 个设备已连接", (int)m_devices.size()));
}

void MainFrame::onCopy(wxCommandEvent&) {
    const USBDevice* d = getSelectedDevice();
    if (!d) {
        wxMessageBox("请先选择一个设备", "提示", wxOK | wxICON_INFORMATION, this);
        return;
    }
    wxString text = wxString::FromUTF8(d->toClipboardText());
    if (wxTheClipboard->Open()) {
        wxTheClipboard->SetData(new wxTextDataObject(text));
        wxTheClipboard->Close();
        setStatus("已复制: " + wxString::FromUTF8(d->getDisplayName()));
    }
}

void MainFrame::onManualRefresh(wxCommandEvent&) { startScan(); }

void MainFrame::onStopRefresh(wxCommandEvent&) {
    m_autoRefresh = false;
    m_timer.Stop();
    refreshButtons();
    setStatus("自动刷新已停止");
}

void MainFrame::onStartAutoRefresh(wxCommandEvent&) {
    if (m_autoRefresh) { refreshButtons(); return; }
    m_autoRefresh = true;
    m_timer.Start(kAutoRefreshIntervalMs);
    refreshButtons();
    setStatus(wxString::Format("自动刷新已开启（间隔 %d ms）", kAutoRefreshIntervalMs));
}

void MainFrame::refreshButtons() {
    m_stopRefreshBtn->Show(m_autoRefresh);
    m_autoRefreshBtn->Show(!m_autoRefresh);
    m_manualRefreshBtn->Show();
    m_baselineBtn->Show();
    m_copyBtn->Show();
    Layout();
}

// ==================== 列表选择互斥 ====================

void MainFrame::onLeftSelect(wxListEvent&) {
    const USBDevice* d = m_list->getSelectedDevice();
    if (!d) return;
    m_change->clearSelection();
    setStatus(deviceInfoText(*d));
}

void MainFrame::onRightSelect(wxListEvent&) {
    const USBDevice* d = m_change->getSelectedDevice();
    if (!d) return;
    m_list->clearSelection();
    const char* tag = m_change->addedContains(d->getUniqueKey()) ? "新增" : "移除";
    setStatus(wxString::Format("[%s] %s", wxString::FromUTF8(tag), deviceInfoText(*d)));
}

// ==================== Windows 设备插拔拦截 ====================

#ifdef _WIN32
WXLRESULT MainFrame::MSWWindowProc(WXUINT nMsg, WXWPARAM wParam, WXLPARAM lParam) {
    if (nMsg == WM_DEVICECHANGE) {
        DWORD e = (DWORD)wParam;
        if (e == DBT_DEVICEARRIVAL || e == DBT_DEVICEREMOVECOMPLETE) {
            triggerRescan();
            return 0;
        }
        if (e == DBT_DEVNODES_CHANGED) {
            triggerRescan();
            return 0;
        }
    }
    return wxFrame::MSWWindowProc(nMsg, wParam, lParam);
}
#endif

// ==================== 辅助 ====================

void MainFrame::setStatus(const wxString& msg) { m_statusBar->SetStatusText(msg, 0); }

void MainFrame::updateBaselineStatus() {
    if (m_baseline.empty()) return;
    wxDateTime now = wxDateTime::Now();
    wxString ts = now.Format("%H:%M:%S");
    m_statusBar->SetStatusText(wxString::Format("基准: %d 个设备 (%s)", (int)m_baseline.size(), ts), 1);
}

const USBDevice* MainFrame::getSelectedDevice() const {
    if (const USBDevice* d = m_list->getSelectedDevice()) return d;
    return m_change->getSelectedDevice();
}

wxString MainFrame::deviceInfoText(const USBDevice& d) {
    return wxString::Format("%s | VID: %s | PID: %s | 序列号: %s",
                            wxString::FromUTF8(d.getDisplayName()),
                            wxString::FromUTF8(d.getFormattedVid()),
                            wxString::FromUTF8(d.getFormattedPid()),
                            wxString::FromUTF8(d.serial.empty() ? std::string("N/A") : d.serial));
}

} // namespace vpid
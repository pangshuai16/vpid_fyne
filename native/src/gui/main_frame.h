#pragma once
#include <atomic>
#include <memory>
#include <mutex>
#include <vector>
#include <wx/wx.h>
#include <wx/splitter.h>
#include <wx/timer.h>
#include "core/device_info.h"
#include "gui/device_list_panel.h"
#include "gui/device_change_panel.h"

namespace vpid {

// 后台扫描结果事件（工作线程通过 wxQueueEvent 投递到主线程）
class ScanResultEvent : public wxEvent {
public:
    ScanResultEvent(wxEventType t) : wxEvent(0, t), devices(std::make_shared<std::vector<USBDevice>>()) {}
    ScanResultEvent(const ScanResultEvent& o) : wxEvent(o), devices(o.devices) {}
    wxEvent* Clone() const override { return new ScanResultEvent(*this); }
    std::shared_ptr<std::vector<USBDevice>> devices;
};

// 用 wxEventTypeTag 类型安全地声明自定义事件（在 main_frame.cpp 中 wxDEFINE_EVENT）
wxDECLARE_EVENT(wxEVT_SCAN_RESULT, ScanResultEvent);

// 主窗口，对应 Python 版 MainWindow
class MainFrame : public wxFrame {
public:
    MainFrame();
    ~MainFrame() override;

private:
    // 核心逻辑：基准比对
    void updateDeviceList(const std::vector<USBDevice>& devices);

    // 扫描控制
    void startScan();
    void onScanResult(ScanResultEvent& evt);
    void onAutoRefreshTick(wxTimerEvent&);
    void triggerRescan();   // 由设备插拔事件触发

    // 用户操作
    void onSetBaseline(wxCommandEvent&);
    void onCopy(wxCommandEvent&);
    void onManualRefresh(wxCommandEvent&);
    void onStopRefresh(wxCommandEvent&);
    void onStartAutoRefresh(wxCommandEvent&);
    void onLeftSelect(wxListEvent&);
    void onRightSelect(wxListEvent&);
    void onClose(wxCloseEvent&);

    void refreshButtons();
    void setStatus(const wxString& msg);
    void updateBaselineStatus();
    const USBDevice* getSelectedDevice() const;
    static wxString deviceInfoText(const USBDevice& d);

    void buildUi();
    void setupDeviceNotifier();

#ifdef _WIN32
    // 拦截 WM_DEVICECHANGE 实现热插拔即时刷新（wxFrame 虚函数）
    WXLRESULT MSWWindowProc(WXUINT nMsg, WXWPARAM wParam, WXLPARAM lParam) override;
#endif

    // 数据
    std::vector<USBDevice> m_devices;
    std::vector<USBDevice> m_baseline;
    std::atomic<bool> m_scanning{false};
    std::atomic<bool> m_closing{false};
    int m_eventPending = 0;
    bool m_autoRefresh = true;

    // 控件
    DeviceListPanel*   m_list    = nullptr;
    DeviceChangePanel* m_change  = nullptr;
    wxStaticText*      m_deviceCount = nullptr;
    wxButton* m_stopRefreshBtn = nullptr;
    wxButton* m_autoRefreshBtn = nullptr;
    wxButton* m_manualRefreshBtn = nullptr;
    wxButton* m_baselineBtn = nullptr;
    wxButton* m_copyBtn = nullptr;

    // 状态栏（字段0=状态，字段1=基准信息）
    wxStatusBar* m_statusBar = nullptr;

    // 定时器
    wxTimer m_timer; // 自动刷新（Linux 亦依赖其 100ms 轮询完成插拔检测）

    // Windows 设备通知句柄
    void* m_hDevNotify = nullptr;
};

} // namespace vpid
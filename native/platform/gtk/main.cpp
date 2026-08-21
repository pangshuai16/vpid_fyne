// Linux 原生 GTK3 版本（无 wxWidgets）
// 满足 glibc 2.28 环境（连同 GTK3 动态运行时一起分发）。
// 复用 core/（USB 枚举、比对、剪贴板文本生成）。

#include <gtk/gtk.h>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <algorithm>
#include <memory>
#include <cstdio>
#include <ctime>

#include "common/constants.h"
#include "core/device_scanner.h"
#include "core/device_comparer.h"

namespace vpid {

namespace theme {
static void rgba(GdkRGBA& c, const char* s){ gdk_rgba_parse(&c, s); }
static void primary(GdkRGBA& c){ rgba(c,"#2775b6"); }
static void success(GdkRGBA& c){ rgba(c,"#1ba784"); }
static void successBg(GdkRGBA& c){ rgba(c,"#E8F8F3"); }
static void danger(GdkRGBA& c){ rgba(c,"#ed3321"); }
static void dangerBg(GdkRGBA& c){ rgba(c,"#FEF0F0"); }
static void white(GdkRGBA& c){ rgba(c,"#FFFFFF"); }
}

struct App {
    GtkWidget* win = nullptr;

    GtkWidget* headerCount = nullptr;
    GtkWidget* btnStop = nullptr;
    GtkWidget* btnAuto = nullptr;
    GtkWidget* btnManual = nullptr;
    GtkWidget* btnBaseline = nullptr;
    GtkWidget* btnCopy = nullptr;

    GtkWidget* treeAll = nullptr;
    GtkListStore* storeAll = nullptr;
    GtkWidget* headerAdded = nullptr;
    GtkWidget* treeAdded = nullptr;
    GtkListStore* storeAdded = nullptr;
    GtkWidget* headerRemoved = nullptr;
    GtkWidget* treeRemoved = nullptr;
    GtkListStore* storeRemoved = nullptr;

    GtkWidget* statusA = nullptr;
    GtkWidget* statusB = nullptr;

    std::vector<USBDevice> allDev;
    std::vector<USBDevice> curDev;
    std::vector<USBDevice> addedDev, removedDev;
    std::vector<USBDevice> baseline;

    std::atomic<bool> scanning{false};
    std::atomic<bool> closing{false};
    bool autoRefresh = true;
    bool ignoreSel = false;
};

static App* g = nullptr;

static void sortByPidVidName(std::vector<USBDevice>& v) {
    std::stable_sort(v.begin(), v.end(),
        [](const USBDevice& a, const USBDevice& b) {
            int c = a.getFormattedPid().compare(b.getFormattedPid());
            if (c != 0) return c < 0;
            c = a.getFormattedVid().compare(b.getFormattedVid());
            if (c != 0) return c < 0;
            return a.getDisplayName() < b.getDisplayName();
        });
}

static std::string nowTime() {
    time_t t = time(nullptr);
    struct tm l;
    localtime_r(&t, &l);
    char b[32];
    snprintf(b, sizeof(b), "%02d:%02d:%02d", l.tm_hour, l.tm_min, l.tm_sec);
    return b;
}

static void setStatusA(const std::string& m) { gtk_label_set_text(GTK_LABEL(g->statusA), m.c_str()); }
static void setStatusB(const std::string& m) { gtk_label_set_text(GTK_LABEL(g->statusB), m.c_str()); }

static std::string deviceInfoText(const USBDevice& d) {
    std::string s = d.getDisplayName();
    s += " | VID: " + d.getFormattedVid();
    s += " | PID: " + d.getFormattedPid();
    s += " | 序列号: ";
    s += d.serial.empty() ? std::string("N/A") : d.serial;
    return s;
}

// ---- 列表控件 ----
static GtkWidget* makeList(const gchar* cols[], int n, GtkListStore** outStore) {
    GtkListStore* store = gtk_list_store_new(n, G_TYPE_STRING);
    GtkWidget* view = gtk_tree_view_new_with_model(GTK_TREE_MODEL(store));
    g_object_unref(store); // view 持有引用
    for (int i = 0; i < n; ++i) {
        GtkCellRenderer* r = gtk_cell_renderer_text_new();
        gtk_tree_view_insert_column_with_attributes(GTK_TREE_VIEW(view), -1,
            cols[i], r, "text", i, nullptr);
    }
    gtk_tree_view_set_headers_clickable(GTK_TREE_VIEW(view), FALSE);
    GtkTreeSelection* sel = gtk_tree_view_get_selection(GTK_TREE_VIEW(view));
    gtk_tree_selection_set_mode(sel, GTK_SELECTION_SINGLE);
    *outStore = store;
    return view;
}

static void repopulate(GtkListStore* store, const std::vector<USBDevice>& devs, bool withPath) {
    gtk_list_store_clear(store);
    for (const auto& d : devs) {
        GtkTreeIter it;
        gtk_list_store_append(store, &it);
        std::string v0 = d.getFormattedVid();
        std::string v1 = d.getFormattedPid();
        std::string v2 = d.getDisplayName();
        if (withPath) {
            std::string v3 = d.path.empty() ? std::string("-") : d.path;
            gtk_list_store_set(store, &it, 0, v0.c_str(), 1, v1.c_str(),
                               2, v2.c_str(), 3, v3.c_str(), -1);
        } else {
            gtk_list_store_set(store, &it, 0, v0.c_str(), 1, v1.c_str(),
                               2, v2.c_str(), -1);
        }
    }
}

static int selectedIndex(GtkWidget* view) {
    GtkTreeSelection* sel = gtk_tree_view_get_selection(GTK_TREE_VIEW(view));
    GtkTreeModel* model = nullptr;
    GtkTreeIter it;
    if (!gtk_tree_selection_get_selected(sel, &model, &it)) return -1;
    GtkTreePath* path = gtk_tree_model_get_path(model, &it);
    gint* idx = gtk_tree_path_get_indices(path);
    int r = (int)idx[0];
    gtk_tree_path_free(path);
    return r;
}

static const USBDevice* selFrom(const std::vector<USBDevice>& devs, GtkWidget* view) {
    int i = selectedIndex(view);
    if (i < 0 || (size_t)i >= devs.size()) return nullptr;
    return &devs[(size_t)i];
}

static void clearSelection(GtkWidget* view) {
    GtkTreeSelection* sel = gtk_tree_view_get_selection(GTK_TREE_VIEW(view));
    gtk_tree_selection_unselect_all(sel);
}

static void refreshViews() {
    repopulate(g->storeAll, g->allDev, true);
    repopulate(g->storeAdded, g->addedDev, false);
    repopulate(g->storeRemoved, g->removedDev, false);

    char buf[96];
    snprintf(buf, sizeof(buf), "%zu 个设备已连接", g->allDev.size());
    gtk_label_set_text(GTK_LABEL(g->headerCount), buf);
    snprintf(buf, sizeof(buf), "+ 新增设备  %zu", g->addedDev.size());
    gtk_label_set_text(GTK_LABEL(g->headerAdded), buf);
    snprintf(buf, sizeof(buf), "- 移除设备  %zu", g->removedDev.size());
    gtk_label_set_text(GTK_LABEL(g->headerRemoved), buf);
}

// ---- 后台扫描 ----
static void startScan();

static gboolean onScanIdle(gpointer user) {
    std::vector<USBDevice>* devs = static_cast<std::vector<USBDevice>*>(user);
    std::unique_ptr<std::vector<USBDevice>> ptr(devs);
    g->scanning = false;
    if (g->closing) return G_SOURCE_REMOVE;

    if (g->baseline.empty()) {
        g->baseline = *devs;
        setStatusB("基准: " + std::to_string(devs->size()) + " 个设备 (" + nowTime() + ")");
    }
    DeviceComparer::compare(g->baseline, *devs, g->addedDev, g->removedDev);
    bool changed = DeviceComparer::hasChanged(g->curDev, *devs);
    g->curDev = *devs;

    if (changed) {
        g->allDev = *devs;
        sortByPidVidName(g->allDev);
        refreshViews();
        char buf[128];
        snprintf(buf, sizeof(buf), "%zu 个设备已连接 (+%zu -%zu)",
                 devs->size(), g->addedDev.size(), g->removedDev.size());
        gtk_label_set_text(GTK_LABEL(g->headerCount), buf);
        setStatusA("最后刷新: " + nowTime() + " | 设备数: " +
                   std::to_string(g->curDev.size()) + " -> " + std::to_string(devs->size()));
    }
    return G_SOURCE_REMOVE;
}

static gpointer scanThread(gpointer) {
    auto* devs = new std::vector<USBDevice>(scanUsbDevices());
    if (g->closing) {
        delete devs;
        g->scanning = false;
        return nullptr;
    }
    g_idle_add(onScanIdle, devs);
    return nullptr;
}

static void startScan() {
    if (g->scanning.exchange(true)) return;
    if (g->closing) { g->scanning = false; return; }
    g_thread_new("scan", scanThread, nullptr);
}

// ---- 操作 ----
static void setBaseline() {
    if (g->curDev.empty()) {
        GtkWidget* dlg = gtk_message_dialog_new(GTK_WINDOW(g->win),
            GTK_DIALOG_MODAL, GTK_MESSAGE_INFO, GTK_BUTTONS_OK, "当前没有设备列表，请先刷新");
        gtk_dialog_run(GTK_DIALOG(dlg));
        gtk_widget_destroy(dlg);
        return;
    }
    g->baseline = g->curDev;
    g->addedDev.clear();
    g->removedDev.clear();
    setStatusA("已将当前设备列表设为基准");
    refreshViews();
    setStatusB("基准: " + std::to_string(g->baseline.size()) + " 个设备 (" + nowTime() + ")");
}

static void copySelected() {
    const USBDevice* d = selFrom(g->allDev, g->treeAll);
    if (!d) d = selFrom(g->addedDev, g->treeAdded);
    if (!d) d = selFrom(g->removedDev, g->treeRemoved);
    if (!d) {
        GtkWidget* dlg = gtk_message_dialog_new(GTK_WINDOW(g->win),
            GTK_DIALOG_MODAL, GTK_MESSAGE_INFO, GTK_BUTTONS_OK, "请先选择一个设备");
        gtk_dialog_run(GTK_DIALOG(dlg));
        gtk_widget_destroy(dlg);
        return;
    }
    GtkClipboard* cb = gtk_clipboard_get(GDK_SELECTION_CLIPBOARD);
    std::string text = d->toClipboardText();
    gtk_clipboard_set_text(cb, text.c_str(), -1);
    setStatusA("已复制: " + d->getDisplayName());
}

// ---- 信号 ----
static void onStopRefresh(GtkWidget*, gpointer) {
    g->autoRefresh = false;
    gtk_widget_hide(g->btnStop);
    gtk_widget_show(g->btnAuto);
    setStatusA("自动刷新已停止");
}
static void onAutoRefresh(GtkWidget*, gpointer) {
    if (!g->autoRefresh) {
        g->autoRefresh = true;
        gtk_widget_show(g->btnStop);
        gtk_widget_hide(g->btnAuto);
        setStatusA("自动刷新已开启（间隔 100 ms）");
    }
}
static void onManualRefresh(GtkWidget*, gpointer) {
    if (!g->scanning) startScan();
}
static void onBaseline(GtkWidget*, gpointer) { setBaseline(); }
static void onCopy(GtkWidget*, gpointer) { copySelected(); }

static void onSelChanged(GtkTreeSelection*, gpointer view) {
    if (g->ignoreSel) return;
    g->ignoreSel = true;
    // 左选中清右，右选中清左
    if (view == g->treeAll) { clearSelection(g->treeAdded); clearSelection(g->treeRemoved); }
    else { clearSelection(g->treeAll); }
    const USBDevice* d = nullptr;
    std::string tag;
    if (view == g->treeAll) d = selFrom(g->allDev, g->treeAll);
    else if (view == g->treeAdded) { d = selFrom(g->addedDev, g->treeAdded); tag = "新增  "; }
    else if (view == g->treeRemoved) { d = selFrom(g->removedDev, g->treeRemoved); tag = "移除  "; }
    if (d) setStatusA(tag + deviceInfoText(*d));
    g->ignoreSel = false;
}

static gboolean onTimer(gpointer) {
    if (g->closing) return G_SOURCE_REMOVE;
    if (g->autoRefresh && !g->scanning) startScan();
    return G_SOURCE_CONTINUE;
}

// ---- UI 构建 ----
static GtkWidget* makeButton(const char* text, void (*fn)(GtkWidget*, gpointer)) {
    GtkWidget* b = gtk_button_new_with_label(text);
    g_signal_connect(b, "clicked", G_CALLBACK(fn), nullptr);
    return b;
}

static void buildUi(App& a) {
    a.win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(a.win), kAppName);
    gtk_window_set_default_size(GTK_WINDOW(a.win), kDefaultWindowWidth, kDefaultWindowHeight);
    gtk_window_set_geometry_hints(GTK_WINDOW(a.win), GTK_WIDGET(a.win),
        nullptr, GDK_HINT_MIN_SIZE);
    gtk_widget_set_size_request(GTK_WIDGET(a.win), kMinWindowWidth, kMinWindowHeight);
    g_signal_connect(a.win, "destroy", G_CALLBACK(gtk_main_quit), nullptr);
    g_signal_connect(a.win, "delete-event", G_CALLBACK(+[](GtkWidget*, GdkEvent*,
                                                             gpointer) -> gboolean {
        g->closing = true;
        gtk_main_quit();
        return TRUE; // 阻止默认销毁，由我们主动退出主循环
    }), nullptr);
    g_signal_connect(a.win, "destroy", G_CALLBACK(+[](GtkWidget*, gpointer) {
        g->closing = true;
    }), nullptr);

    GtkWidget* root = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
    gtk_container_add(GTK_CONTAINER(a.win), root);

    // 顶栏
    GtkWidget* tb = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
    gtk_widget_set_margin_start(GTK_WIDGET(tb), 10);
    gtk_widget_set_margin_end(GTK_WIDGET(tb), 10);
    gtk_widget_set_margin_top(GTK_WIDGET(tb), 8);
    gtk_widget_set_margin_bottom(GTK_WIDGET(tb), 8);
    gtk_box_pack_start(GTK_BOX(root), tb, FALSE, FALSE, 0);

    a.headerCount = gtk_label_new("0 个设备已连接");
    gtk_box_pack_start(GTK_BOX(tb), a.headerCount, TRUE, TRUE, 0);

    a.btnStop = makeButton("停止刷新", onStopRefresh);
    a.btnAuto = makeButton("自动刷新", onAutoRefresh);
    a.btnManual = makeButton("手动刷新", onManualRefresh);
    a.btnBaseline = makeButton("设为基准", onBaseline);
    a.btnCopy = makeButton(" 复制 ", onCopy);

    GdkRGBA c;
    theme::danger(); gtk_widget_override_background_color(a.btnStop, GTK_STATE_FLAG_NORMAL, &c);
    theme::white();  gtk_widget_override_color(a.btnStop, GTK_STATE_FLAG_NORMAL, &c);
    theme::success();gtk_widget_override_background_color(a.btnAuto, GTK_STATE_FLAG_NORMAL, &c);
    theme::white();  gtk_widget_override_color(a.btnAuto, GTK_STATE_FLAG_NORMAL, &c);
    theme::primary();gtk_widget_override_background_color(a.btnManual, GTK_STATE_FLAG_NORMAL, &c);
    theme::white();  gtk_widget_override_color(a.btnManual, GTK_STATE_FLAG_NORMAL, &c);
    theme::success();gtk_widget_override_background_color(a.btnBaseline, GTK_STATE_FLAG_NORMAL, &c);
    theme::white();  gtk_widget_override_color(a.btnBaseline, GTK_STATE_FLAG_NORMAL, &c);
    theme::primary();gtk_widget_override_background_color(a.btnCopy, GTK_STATE_FLAG_NORMAL, &c);
    theme::white();  gtk_widget_override_color(a.btnCopy, GTK_STATE_FLAG_NORMAL, &c);

    gtk_box_pack_start(GTK_BOX(tb), a.btnStop, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(tb), a.btnAuto, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(tb), a.btnManual, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(tb), a.btnBaseline, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(tb), a.btnCopy, FALSE, FALSE, 0);

    // 主区分栏
    GtkWidget* paned = gtk_paned_new(GTK_ORIENTATION_HORIZONTAL);
    gtk_widget_set_hexpand(GTK_WIDGET(paned), TRUE);
    gtk_widget_set_vexpand(GTK_WIDGET(paned), TRUE);
    gtk_box_pack_start(GTK_BOX(root), paned, TRUE, TRUE, 4);

    // 左列表
    GtkWidget* left = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
    const gchar* colsAll[] = { "VID", "PID", "设备名称", "路径" };
    a.treeAll = makeList(colsAll, 4, &a.storeAll);
    GtkWidget* scAll = gtk_scrolled_window_new(nullptr, nullptr);
    gtk_container_add(GTK_CONTAINER(scAll), a.treeAll);
    gtk_box_pack_start(GTK_BOX(left), scAll, TRUE, TRUE, 0);
    gtk_paned_pack1(GTK_PANED(paned), left, TRUE, FALSE);

    // 右：新增 + 移除
    GtkWidget* right = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
    const gchar* colsChg[] = { "VID", "PID", "设备名称" };
    a.headerAdded = gtk_label_new("+ 新增设备  0");
    theme::successBg(); gtk_widget_override_background_color(a.headerAdded, GTK_STATE_FLAG_NORMAL, &c);
    theme::success();  gtk_widget_override_color(a.headerAdded, GTK_STATE_FLAG_NORMAL, &c);
    a.treeAdded = makeList(colsChg, 3, &a.storeAdded);
    GtkWidget* scAdded = gtk_scrolled_window_new(nullptr, nullptr);
    gtk_container_add(GTK_CONTAINER(scAdded), a.treeAdded);

    a.headerRemoved = gtk_label_new("- 移除设备  0");
    theme::dangerBg(); gtk_widget_override_background_color(a.headerRemoved, GTK_STATE_FLAG_NORMAL, &c);
    theme::danger();  gtk_widget_override_color(a.headerRemoved, GTK_STATE_FLAG_NORMAL, &c);
    a.treeRemoved = makeList(colsChg, 3, &a.storeRemoved);
    GtkWidget* scRemoved = gtk_scrolled_window_new(nullptr, nullptr);
    gtk_container_add(GTK_CONTAINER(scRemoved), a.treeRemoved);

    GtkWidget* rightTop = gtk_box_new(GTK_ORIENTATION_VERTICAL, 2);
    gtk_box_pack_start(GTK_BOX(rightTop), a.headerAdded, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(rightTop), scAdded, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(right), rightTop, TRUE, TRUE, 0);

    GtkWidget* rightBot = gtk_box_new(GTK_ORIENTATION_VERTICAL, 2);
    gtk_box_pack_start(GTK_BOX(rightBot), a.headerRemoved, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(rightBot), scRemoved, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(right), rightBot, TRUE, TRUE, 0);

    gtk_paned_pack2(GTK_PANED(paned), right, TRUE, FALSE);
    gtk_paned_set_position(GTK_PANED(paned), (int)(kDefaultWindowWidth * 0.6));

    // 底部状态
    GtkWidget* sb = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
    gtk_widget_set_margin_start(GTK_WIDGET(sb), 10);
    gtk_widget_set_margin_end(GTK_WIDGET(sb), 10);
    gtk_widget_set_margin_bottom(GTK_WIDGET(sb), 4);
    a.statusA = gtk_label_new("");
    a.statusB = gtk_label_new("");
    gtk_box_pack_start(GTK_BOX(sb), a.statusA, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(sb), a.statusB, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(root), sb, FALSE, FALSE, 0);

    // 选择互斥
    g_signal_connect(gtk_tree_view_get_selection(GTK_TREE_VIEW(a.treeAll)),
        "changed", G_CALLBACK(onSelChanged), a.treeAll);
    g_signal_connect(gtk_tree_view_get_selection(GTK_TREE_VIEW(a.treeAdded)),
        "changed", G_CALLBACK(onSelChanged), a.treeAdded);
    g_signal_connect(gtk_tree_view_get_selection(GTK_TREE_VIEW(a.treeRemoved)),
        "changed", G_CALLBACK(onSelChanged), a.treeRemoved);

    // 定时自动刷新（Linux 靠轮询检测插拔）
    g_timeout_add(kAutoRefreshIntervalMs, onTimer, nullptr);

    gtk_widget_show_all(a.win);
    startScan();
}

} // namespace vpid

int main(int argc, char** argv) {
    gtk_init(&argc, &argv);
    vpid::App app;
    vpid::g = &app;
    vpid::buildUi(app);
    gtk_main();
    return 0;
}
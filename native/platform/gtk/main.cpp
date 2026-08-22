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

// 全局 GTK3 CSS：Fluent Design —— 扁平、灰阶分层、Windows 蓝
static void applyCss() {
    static const char* css =
        "#vpid-main { background-color:#f3f3f3; }"
        /* ---- 顶栏标题 / 状态 ---- */
        "#vpid-main label.app-title { font-size:14pt; font-weight:600; color:#242424; }"
        "#vpid-main label.status  { color:#616161; font-size:9pt; }"
        /* ---- 按钮：Fluent 扁平，小圆角，无阴影 ---- */
        "#vpid-main button {"
        "  border:1px solid #8a8886; border-radius:4px; padding:4px 16px 3px; font-weight:600;"
        "  background-image:none; background-color:#f7f7f7; color:#242424;"
        "  text-shadow:none; min-height:28px; box-shadow:none; }"
        "#vpid-main button:hover  { background-color:#f0f0f0; border-color:#787674; }"
        "#vpid-main button:active { background-color:#e5e5e5; }"
        "#vpid-main button:disabled { opacity:0.4; }"
        "#vpid-main button.accent-blue, #vpid-main button.accent-green, #vpid-main button.accent-red {"
        "  border:none; color:#fff; }"
        "#vpid-main button.accent-blue  { background-color:#0078d4; }"
        "#vpid-main button.accent-blue:hover  { background-color:#106ebe; }"
        "#vpid-main button.accent-blue:active { background-color:#005a9e; }"
        "#vpid-main button.accent-green { background-color:#107c10; }"
        "#vpid-main button.accent-green:hover { background-color:#128212; }"
        "#vpid-main button.accent-green:active{ background-color:#0e6b0e; }"
        "#vpid-main button.accent-red   { background-color:#c42b1c; }"
        "#vpid-main button.accent-red:hover   { background-color:#b22416; }"
        "#vpid-main button.accent-red:active  { background-color:#982422; }"
        /* ---- 信息 chip：浅底 + 语义字色 ---- */
        "#vpid-main label.chip { padding:3px 12px; border-radius:4px; font-weight:600; font-size:9.5pt; }"
        "#vpid-main label.chip-green { background-color:#e6f4e7; color:#107c10; }"
        "#vpid-main label.chip-red   { background-color:#fbeae8; color:#c42b1c; }"
        /* ---- 列表：白底 + 细表头 + Fluent 选中蓝 ---- */
        "#vpid-main treeview, #vpid-main treeview.view { font-size:10pt; color:#242424; font-family:monospace; }"
        "#vpid-main treeview.view { background-color:#ffffff; }"
        "#vpid-main treeview.view:selected, #vpid-main treeview.view:selected:focus,"
        "#vpid-main treeview.view:selected:hover { background-color:#0078d4; color:#ffffff; }"
        "#vpid-main treeview.view:not(:selected):hover { background-color:#f3f7fc; }"
        "#vpid-main treeview header button { background-color:#f9f9f9; color:#616161; font-weight:600;"
        "  padding-top:5px; padding-bottom:5px; border:0; border-bottom:1px solid #e6e6e6; box-shadow:none; }"
        "#vpid-main treeview header button:not(:last-child) { border-right:1px solid #f0f0f0; }"
        "#vpid-main treeview header button:hover { background-color:#eef0f2; }"
        /* ---- 面板：圆角浅边，无重投影 ---- */
        "#vpid-main scrolledwindow { border:1px solid #e0e0e0; border-radius:6px;"
        "  background-color:#ffffff; box-shadow:0 1px 2px rgba(0,0,0,0.05); }"
        "#vpid-main paned > separator { background-color:#e0e0e0; min-width:1px; }"
        "#vpid-main scrolledwindow undershoot, #vpid-main scrolledwindow overshoot { background:none; }";
    GtkCssProvider* p = gtk_css_provider_new();
    gtk_css_provider_load_from_data(p, css, -1, nullptr);
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
        GTK_STYLE_PROVIDER(p), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    g_object_unref(p);
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
        gtk_cell_renderer_set_padding(r, 6, 4);
        bool isKey = (i <= 1); // VID / PID：固定 4 位 hex，等宽窄列居中
        if (isKey) gtk_cell_renderer_set_alignment(r, 0.5f, 0.5f);
        GtkTreeViewColumn* col = gtk_tree_view_column_new_with_attributes(cols[i], r, "text", i, nullptr);
        if (isKey) {
            gtk_tree_view_column_set_sizing(col, GTK_TREE_VIEW_COLUMN_FIXED);
            gtk_tree_view_column_set_fixed_width(col, 50);
            gtk_tree_view_column_set_alignment(col, 0.5f);
        } else {
            gtk_tree_view_column_set_expand(GTK_TREE_VIEW_COLUMN(col), TRUE);
        }
        gtk_tree_view_append_column(GTK_TREE_VIEW(view), col);
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
    // 刷新后清除选中，避免“默认全选中”观感
    gtk_tree_selection_unselect_all(gtk_tree_view_get_selection(GTK_TREE_VIEW(g->treeAll)));
    gtk_tree_selection_unselect_all(gtk_tree_view_get_selection(GTK_TREE_VIEW(g->treeAdded)));
    gtk_tree_selection_unselect_all(gtk_tree_view_get_selection(GTK_TREE_VIEW(g->treeRemoved)));

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
static GtkWidget* makeButton(const char* text, void (*fn)(GtkWidget*, gpointer), const char* cls) {
    GtkWidget* b = gtk_button_new_with_label(text);
    if (cls) gtk_style_context_add_class(gtk_widget_get_style_context(b), cls);
    g_signal_connect(b, "clicked", G_CALLBACK(fn), nullptr);
    return b;
}

static void addClass(GtkWidget* w, const char* cls) {
    gtk_style_context_add_class(gtk_widget_get_style_context(w), cls);
}

static void buildUi(App& a) {
    a.win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_widget_set_name(a.win, "vpid-main");
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
    addClass(a.headerCount, "app-title");
    gtk_box_pack_start(GTK_BOX(tb), a.headerCount, TRUE, TRUE, 0);

    a.btnStop = makeButton("停止刷新", onStopRefresh, "accent-red");
    a.btnAuto = makeButton("自动刷新", onAutoRefresh, "accent-green");
    a.btnManual = makeButton("手动刷新", onManualRefresh, "accent-blue");
    a.btnBaseline = makeButton("设为基准", onBaseline, "accent-green");
    a.btnCopy = makeButton(" 复制 ", onCopy, "accent-blue");

    // 按钮整体右对齐（与 Windows Fluent 工具栏一致）
    GtkWidget* btns = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
    gtk_box_pack_start(GTK_BOX(btns), a.btnStop, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(btns), a.btnAuto, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(btns), a.btnManual, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(btns), a.btnBaseline, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(btns), a.btnCopy, FALSE, FALSE, 0);
    gtk_box_pack_end(GTK_BOX(tb), btns, FALSE, FALSE, 0);

    // 主区分栏（左右留边对齐顶栏）
    GtkWidget* paned = gtk_paned_new(GTK_ORIENTATION_HORIZONTAL);
    gtk_widget_set_hexpand(GTK_WIDGET(paned), TRUE);
    gtk_widget_set_vexpand(GTK_WIDGET(paned), TRUE);
    gtk_widget_set_margin_start(GTK_WIDGET(paned), 10);
    gtk_widget_set_margin_end(GTK_WIDGET(paned), 10);
    gtk_widget_set_margin_top(GTK_WIDGET(paned), 2);
    gtk_widget_set_margin_bottom(GTK_WIDGET(paned), 6);
    gtk_box_pack_start(GTK_BOX(root), paned, TRUE, TRUE, 0);

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
    addClass(a.headerAdded, "chip");
    addClass(a.headerAdded, "chip-green");
    a.treeAdded = makeList(colsChg, 3, &a.storeAdded);
    GtkWidget* scAdded = gtk_scrolled_window_new(nullptr, nullptr);
    gtk_container_add(GTK_CONTAINER(scAdded), a.treeAdded);

    a.headerRemoved = gtk_label_new("- 移除设备  0");
    addClass(a.headerRemoved, "chip");
    addClass(a.headerRemoved, "chip-red");
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
    addClass(a.statusA, "status");
    addClass(a.statusB, "status");
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
    vpid::applyCss();
    vpid::App app;
    vpid::g = &app;
    vpid::buildUi(app);
    gtk_main();
    return 0;
}
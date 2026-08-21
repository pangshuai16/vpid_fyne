#include <wx/wx.h>
#include "common/constants.h"
#include "gui/main_frame.h"

namespace vpid {

// wxWidgets 应用入口，对应 Python 版 main.py
class VpidApp : public wxApp {
public:
    bool OnInit() override {
        MainFrame* frame = new MainFrame();
        frame->Show(true);
        return true;
    }
};

} // namespace vpid

wxIMPLEMENT_APP(vpid::VpidApp);
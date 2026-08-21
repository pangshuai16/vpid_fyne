cmake_minimum_required(VERSION 3.16)
project(vpid_viewer LANGUAGES CXX)

# 目标：
#   - Windows XP x86：MinGW-w64 (i686) 静态链接 wxWidgets+libusb，单文件自包含
#   - Linux x64/arm64 glibc2.28：Rocky8 容器内编译，静态/合并链接，单文件
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# 默认禁止编译期启用异常以外的东西，见机优化体积与启动
add_compile_options(-O2 -fno-rtti)

set(BASE_SOURCES
  src/main.cpp
  src/core/device_info.cpp
  src/core/device_scanner.cpp
  src/core/device_comparer.cpp
  src/gui/device_list_panel.cpp
  src/gui/device_change_panel.cpp
  src/gui/main_frame.cpp
)

add_executable(vpid_viewer WIN32 MACOSX_BUNDLE ${BASE_SOURCES}) # WIN32: GUI 子系统，抑制控制台窗口

if(WIN32)
  find_package(wxWidgets REQUIRED COMPONENTS core base)
  include(${wxWidgets_USE_FILE})
  # 自编译的 wxWidgets 是静态 monolithic 构建，安装布局为 <root>/lib/gcc_lib。
  # FindwxWidgets 经 wx-config 解析出的库列表只含辅助库（png/tiff/jpeg/zlib/
  # regex/expat），漏掉了 monolithic 主库 libwxmsw31u.a，导致 wxApp/wxFrame 等
  # 核心符号链接期 undefined。这里从 include dir 反推 gcc_lib 目录并补上主库。
  list(GET wxWidgets_INCLUDE_DIRS 0 _wxInc0)
  get_filename_component(_wxLibDir "${_wxInc0}" DIRECTORY)
  find_library(VPID_WX_MONO NAMES wxmsw31u libwxmsw31u HINTS "${_wxLibDir}")
  if(VPID_WX_MONO)
    set(wxWidgets_LIBRARIES ${VPID_WX_MONO} ${wxWidgets_LIBRARIES})
    message(STATUS ">>> linked monolithic wx core lib: ${VPID_WX_MONO}")
  else()
    message(FATAL_ERROR "Could not find monolithic libwxmsw31u in ${_wxLibDir}")
  endif()
  message(STATUS ">>> WIN32 wxWidgets_LIBRARIES: ${wxWidgets_LIBRARIES}")
  target_sources(vpid_viewer PRIVATE
    src/core/windows_scanner.cpp
  )
  target_include_directories(vpid_viewer PRIVATE src)
  # setupapi: USB 扫描；libusb: Linux/XP 也无需在此
  target_link_libraries(vpid_viewer PRIVATE ${wxWidgets_LIBRARIES} setupapi)
  # XP 兼容：定义 NT 5.1 API 集，避免链接 Vista+ 符号
  target_compile_definitions(vpid_viewer PRIVATE _WIN32_WINNT=0x0501 WINVER=0x0501)
else()
  find_package(wxWidgets REQUIRED COMPONENTS core base)
  include(${wxWidgets_USE_FILE})
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(LIBUSB REQUIRED libusb-1.0)
  target_sources(vpid_viewer PRIVATE
    src/core/linux_scanner.cpp
  )
  target_include_directories(vpid_viewer PRIVATE src ${LIBUSB_INCLUDE_DIRS})
  target_link_libraries(vpid_viewer PRIVATE ${wxWidgets_LIBRARIES} ${LIBUSB_LIBRARIES})
  target_compile_definitions(vpid_viewer PRIVATE WXUSINGDLL)
endif()
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
  # 静态 monolithic 安装把所有 .a 放在 <root>/lib/gcc_lib。FindwxWidgets 经
  # wx-config 只解析出辅助库（png/tiff/jpeg/zlib/regex/expat），漏掉核心库，
  # 导致 wxApp/wxFrame 等链接期 undefined。这里改为收集 gcc_lib 下的全部 .a
  # 并按名称排序（核心库如 libwxbase/libwxmsw 字母序在辅助库之前），既补上
  # 核心库又保证静态链接顺序正确。
  file(GLOB _wxStaticAll "${_wxLibDir}/*.a")
  if(NOT _wxStaticAll)
    message(FATAL_ERROR "No static .a libraries found in ${_wxLibDir}")
  endif()
  list(SORT _wxStaticAll)
  foreach(_l ${_wxStaticAll})
    message(STATUS ">>> wx static lib: ${_l}")
  endforeach()
  set(wxWidgets_LIBRARIES ${_wxStaticAll} ${wxWidgets_LIBRARIES})
  message(STATUS ">>> final WIN32 wxWidgets_LIBRARIES: ${wxWidgets_LIBRARIES}")
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
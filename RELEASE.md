# 自动发布指南

## GitHub Action 自动发布

本项目配置了 GitHub Action 用于自动编译和发布多平台可执行文件（C++ 原生实现）。

## 工作流配置

### build.yml (分支构建)
- **触发**: 所有分支推送（除 main 外）
- **构建平台**: Windows x86, Linux x64/arm64
- **目的**: 快速验证代码变更

### release.yml (发布构建)
- **触发**: main 分支推送
- **构建平台**: Windows x86, Linux x64/arm64
- **目的**: 创建完整 Release

## 使用步骤

### 自动发布（main 分支推送）

```bash
git add .
git commit -m "发布新版本"
git push origin main
```

推送后 GitHub Actions 将自动：
1. 构建全部平台矩阵
2. 创建新的 GitHub Release
3. 上传所有可执行文件

### 查看构建状态

- 打开 GitHub 仓库的 "Actions" 页面
- 查看对应工作流
- 等待构建完成

### 获取发布文件

构建完成后：
- 打开仓库的 "Releases" 页面
- 找到最新的版本发布（版本号为 `v${github.run_number}`）
- 下载对应平台的可执行文件

## 构建平台说明

| 平台 | 架构 | 文件名 | CI 环境 |
|------|------|--------|---------|
| Windows | x86 | `vpid_viewer_windows_x86.exe` | Windows 2022 + MSYS2 MINGW32 (mingw-w64-i686) |
| Linux | x64 | `vpid_viewer_linux_amd64` | Rocky Linux 8 (glibc 2.28) + gcc-c++ |
| Linux | arm64 | `vpid_viewer_linux_arm64` | Rocky Linux 8 + QEMU + gcc-c++ |

## 关键技术点

### Windows XP 兼容性

- MSYS2 MINGW32 (i686) 工具链（32 位 x86）
- 全静态链接（`-static -static-libgcc -static-libstdc++` + `-municode`），产物零 DLL 依赖
- 锁定 NT 5.1 API 集（`_WIN32_WINNT=0x0501` / `WINVER=0x0501` / `_WIN32_IE=0x0501`）
- 仅链接系统库（setupapi / advapi32 / comctl32 / user32 / gdi32）

### Linux glibc 兼容性

使用 Rocky Linux 8 容器构建，确保 glibc 2.28 兼容性，可在 CentOS 8、Ubuntu 20.04 及以上系统运行。构建依赖为 `gcc-c++ make cmake libusb1-devel gtk3-devel pkgconfig`。

### 多平台 USB 扫描

- **Windows**: SetupAPI 设备枚举，注册表兜底
- **Linux**: libusb-1.0

## Release 配置要点

1. **权限**: `permissions: contents: write` 允许创建 Release
2. **Artifact 下载**: 使用 `pattern: release-*` 和 `merge-multiple: true` 下载并合并所有 artifacts
3. **文件上传**: `files: artifacts/**/*` 上传所有下载的文件

## 本地构建测试

参考项目根目录 README.md 的「从源码构建」章节。
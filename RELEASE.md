# 自动发布指南

## GitHub Action 自动发布

本项目配置了 GitHub Action 用于自动编译和发布可执行文件。

## 工作流配置

工作流文件位于：`/.github/workflows/build-release.yml`

## 触发条件

1. **推送标签**: 当推送一个以 `v` 开头的标签时自动触发
2. **手动触发**: 通过 GitHub Actions 界面的 "Run workflow" 按钮手动触发

## 使用步骤

### 1. 准备发布

```bash
git add .
git commit -m "发布新版本"
```

### 2. 打标签

```bash
git tag -a v1.0.0 -m "版本 1.0.0 发布"
git push origin v1.0.0
```

### 3. 查看构建状态

- 打开 GitHub 仓库的 "Actions" 页面
- 查看 "Build and Release" 工作流
- 等待构建完成

### 4. 获取发布文件

构建完成后：
- 打开仓库的 "Releases" 页面
- 找到最新的版本发布
- 下载 `vpid_viewer.exe`

## 手动触发

1. 访问 GitHub 仓库的 Actions 页面
2. 选择 "Build and Release" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并运行

## 工作流说明

工作流执行步骤：

1. 检出代码
2. 设置社区补丁版 Python 3.8.20 x86 环境 (XP 兼容)
3. 安装依赖
4. 使用 PyInstaller 编译可执行文件
5. 自动创建 GitHub Release 并上传 exe

## 关于 Windows XP 兼容性

项目配置为使用社区补丁版 Python 3.8.20（来自 PythonVista 项目），支持 Windows XP 兼容性。

## XP 兼容性检查清单

- [x] 使用社区补丁版 Python 3.8.20
- [x] 使用 32 位 Python
- [x] 使用 PyInstaller 4.10
- [x] 避免使用 Vista+ API
- [ ] 在真实 XP 环境中测试

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
cd vpid_py
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
2. 设置 Python 3.8 x86 环境
3. 安装依赖
4. 使用 PyInstaller 编译可执行文件
5. 自动创建 GitHub Release 并上传 exe

## 关于 Windows XP 兼容性

重要提示：GitHub Actions 使用的标准 Python 3.8 不支持 Windows XP。

要获得真正的 XP 兼容性，需要：

### 方案 1: 使用 Python 3.5（推荐）

1. 在本地使用 Python 3.5 (最后官方支持 XP 的版本)
2. 安装依赖: `pip install -r requirements.txt`
3. 安装 PyInstaller 3.6: `pip install pyinstaller==3.6`
4. 构建: `pyinstaller vpid_viewer.spec`
5. 手动上传发布

### 方案 2: 使用社区 XP 补丁

使用社区提供的 Python 3.8 XP 补丁版本进行本地构建。

### 方案 3: 使用 Windows 7 构建

在 Windows 7 上使用 Python 3.5 构建，通常可以在 XP 上运行。

## XP 兼容性检查清单

- [ ] 使用 Python 3.5-3.8
- [ ] 使用 32 位 Python
- [ ] 使用 PyInstaller 3.6 或更低
- [ ] 避免使用 Python 3.6+ 语法
- [ ] 避免使用 Vista+ API
- [ ] 在真实 XP 环境中测试

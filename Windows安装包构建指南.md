# Windows 安装包构建指南

## 🎯 解决方案：GitHub Actions 自动构建

由于你没有 Windows 电脑，我们使用 **GitHub Actions** 在云端自动构建 Windows 安装包。

## ✅ 已完成配置

已创建 `.github/workflows/build-windows.yml`，它会在以下情况自动构建：
1. **推送版本标签时**（如 `v1.0.0`）
2. **手动触发**（在 GitHub Actions 页面点击 "Run workflow"）

## 📤 构建步骤

### 步骤 1: 推送代码和标签到 GitHub

在终端执行：

```bash
cd /Users/shibo/Documents/trae_projects/xinfudTools

# 添加 SSH 密钥
ssh-add
# 密码：mylove880117

# 推送代码和标签
git push github main --tags
```

### 步骤 2: 查看构建进度

1. 访问: https://github.com/Bob1817/xinfudTools/actions
2. 你会看到正在运行的 "Build Windows Installer" 工作流
3. 点击可以查看实时日志

### 步骤 3: 下载安装包

构建完成后（约 5-10 分钟）：

**方式一：从 Release 下载**
1. 访问: https://github.com/Bob1817/xinfudTools/releases
2. 找到 `v1.0.0` Release
3. 下载 `HR数据处理工具集-v1.0.0-windows.exe`

**方式二：从 Artifacts 下载**（保留 30 天）
1. 访问: https://github.com/Bob1817/xinfudTools/actions
2. 点击最近的一次构建
3. 在页面底部的 "Artifacts" 部分下载

## 🔧 工作流程说明

GitHub Actions 会自动执行：

1. ✅ 启动 Windows 虚拟机（windows-latest）
2. ✅ 安装 Python 3.11
3. ✅ 安装项目依赖（PyQt6, pandas, openpyxl 等）
4. ✅ 使用 PyInstaller 打包应用
5. ✅ 下载并安装 Inno Setup 6
6. ✅ 使用 Inno Setup 创建安装程序
7. ✅ 自动创建 GitHub Release 并上传安装包

## 📋 手动触发构建

如果你想重新构建（不需要创建新标签）：

1. 访问: https://github.com/Bob1817/xinfudTools/actions
2. 点击左侧 "Build Windows Installer"
3. 点击右上角 "Run workflow" 按钮
4. 选择分支（通常是 main）
5. 点击绿色 "Run workflow" 按钮

## 🐛 故障排除

### 构建失败

如果构建失败，可以：
1. 查看 Actions 日志了解错误详情
2. 检查 `requirements.txt` 是否包含所有依赖
3. 检查工作流文件是否有语法错误

### 常见问题

**Q: 构建需要多长时间？**
A: 首次构建约 5-10 分钟（需要下载依赖和 Inno Setup）

**Q: Artifacts 保留多久？**
A: 30 天。Release 中的文件永久保留。

**Q: 可以自定义安装包吗？**
A: 可以修改工作流中的 Inno Setup 脚本部分。

## 📦 生成的安装包

**文件名**: `HR数据处理工具集-v1.0.0-windows.exe`

**安装方式**:
1. 双击安装包
2. 选择安装路径（默认：`C:\Program Files\HR数据处理工具集`）
3. 选择是否创建桌面快捷方式
4. 完成安装

**安装后**:
- 开始菜单有快捷方式
- 桌面有快捷方式（如果选择）
- 可以从安装目录直接运行 `.exe` 文件

---

**提示**: 推送代码后，GitHub Actions 会自动运行，你只需等待 5-10 分钟即可下载 Windows 安装包！

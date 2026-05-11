# GitHub Actions 工作流

## 工作流说明

### build-release.yml
自动构建 Windows 安装包并创建 Release

#### 触发条件
- 推送标签 `v*` (如 v1.1.0)
- 手动触发 (workflow_dispatch)

#### 执行步骤
1. **检出代码** - 获取最新代码
2. **设置 Python** - 安装 Python 3.10
3. **安装依赖** - 安装 requirements.txt 和 PyInstaller
4. **构建可执行文件** - 使用 PyInstaller 打包
5. **打包安装程序** - 重命名并准备发布
6. **上传构建产物** - 保存安装包
7. **创建 GitHub Release** - 自动创建 Release 并上传安装包
8. **同步到 Gitee** - 推送代码到 Gitee 仓库

#### 需要的 Secrets

需要在 GitHub 仓库设置以下 Secrets：

1. **GITEE_TOKEN** (可选)
   - 用途：同步代码到 Gitee
   - 获取方式：Gitee 个人设置 -> 私人令牌

## 手动触发构建

1. 进入 GitHub 仓库
2. 点击 Actions 标签
3. 选择 "Build and Release" 工作流
4. 点击 "Run workflow"
5. 选择分支（通常是 main）
6. 点击 "Run workflow"

## 自动触发构建

推送标签时自动触发：

```bash
git tag -a v1.1.0 -m "v1.1.0 发布"
git push origin v1.1.0
```

## 查看构建状态

- GitHub Actions: https://github.com/Bob1817/xinfudTools/actions
- 构建完成后会自动创建 Release

## 发布流程

1. 本地开发完成并测试通过
2. 更新版本号（core/version.py 和 main.py）
3. 提交代码并推送
4. 创建 Git 标签并推送
5. GitHub Actions 自动构建
6. 构建完成后自动创建 Release
7. 用户收到更新提醒

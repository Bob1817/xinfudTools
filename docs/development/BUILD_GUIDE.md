# 构建发布指南

## 手动触发 GitHub Actions 构建

### 方法1：通过 GitHub 网站（推荐）

1. 访问 GitHub Actions 页面：
   https://github.com/Bob1817/xinfudTools/actions/workflows/build-windows.yml

2. 点击右侧的 "Run workflow" 按钮

3. 选择分支：`main`

4. 点击 "Run workflow"

5. 等待构建完成（约 5-10 分钟）

### 方法2：通过 GitHub CLI

```bash
# 安装 GitHub CLI
# macOS
brew install gh

# 登录
gh auth login

# 触发工作流
gh workflow run build-windows.yml --ref main
```

### 方法3：通过 API（需要 Token）

```bash
# 设置 GitHub Token
export GITHUB_TOKEN="your_github_token"

# 触发工作流
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/Bob1817/xinfudTools/actions/workflows/258550899/dispatches" \
  -d '{"ref":"main"}'
```

## 自动触发构建

推送标签时自动触发：

```bash
# 1. 确保代码已提交
git add .
git commit -m "Prepare for v1.1.0 release"

# 2. 创建标签
git tag -a v1.1.0 -m "v1.1.0 发布：优化数据匹配机制，新增输出路径设置"

# 3. 推送标签（自动触发构建）
git push origin v1.1.0
```

## 查看构建状态

- GitHub Actions: https://github.com/Bob1817/xinfudTools/actions
- 构建完成后会自动创建 Release

## 发布流程

### 1. 准备工作
- [ ] 代码已提交并推送
- [ ] 版本号已更新
- [ ] 所有测试通过
- [ ] 文档已更新

### 2. 创建标签
```bash
git tag -a v1.1.0 -m "v1.1.0 发布说明"
git push origin v1.1.0
```

### 3. 等待构建
- 自动触发 GitHub Actions
- 构建 Windows 安装包
- 创建 GitHub Release
- 同步到 Gitee

### 4. 验证发布
- [ ] GitHub Release 已创建
- [ ] 安装包已上传
- [ ] Gitee Release 已同步
- [ ] 自动更新功能正常

### 5. 通知用户
- 应用内显示更新提示
- 发送更新通知（如有邮件列表）

## 故障排查

### 构建失败

1. 查看 GitHub Actions 日志
2. 检查 requirements.txt 是否完整
3. 检查 PyInstaller 配置

### Gitee 同步失败

1. 检查 GITEE_TOKEN 是否设置
2. 检查 Gitee 仓库权限
3. 检查网络连接

### Release 创建失败

1. 检查 GITHUB_TOKEN 权限
2. 检查标签是否正确推送
3. 检查工作流配置

## 配置 Secrets

需要在 GitHub 仓库设置以下 Secrets：

### GITEE_TOKEN
1. 访问 https://gitee.com/profile/personal_access_tokens
2. 创建新的私人令牌
3. 权限：projects、pull_requests、hook
4. 复制 Token
5. 在 GitHub 仓库 Settings -> Secrets -> Actions 中添加

### GITHUB_TOKEN
- 自动提供，无需手动设置

## 相关链接

- GitHub Actions: https://github.com/Bob1817/xinfudTools/actions
- GitHub Releases: https://github.com/Bob1817/xinfudTools/releases
- Gitee Releases: https://gitee.com/shibo8817/xinfud-tools/releases

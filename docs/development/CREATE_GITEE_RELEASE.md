# 手动创建 Gitee Release v1.1.0

## 方法一：通过 Gitee 网站手动创建（推荐）

### 步骤

1. **访问 Gitee Release 页面**
   - 打开: https://gitee.com/shibo8817/xinfud-tools/releases

2. **点击 "创建发行版"**

3. **填写 Release 信息**

   **版本号**: `v1.1.0`
   
   **发行版标题**: `HR 数据处理工具集 v1.1.0`
   
   **发行版内容**:
   ```markdown
   ## v1.1.0 发布说明

   ### 核心功能
   - 数据合并器：支持同一身份证号多条数据自动合并
   - Sheet识别器：自动识别社保数据表中的Sheet，支持模糊匹配
   - 错误处理器：统一错误处理，提供友好的中文错误提示
   - 配置管理器：管理用户设置，支持输出路径持久化
   - Sheet选择弹窗：多Sheet场景下让用户选择具体的数据Sheet
   - 字段映射确认弹窗：字段不完全匹配时让用户确认字段映射关系
   - 输出路径选择弹窗：生成报表时选择输出位置

   ### 优化改进
   - 数据匹配机制优化：以身份证号为唯一识别ID，自动合并重复数据
   - 错误处理优化：未匹配字段默认为0.00，不报错中断流程
   - 错误提示优化：技术错误信息转换为中文可读信息
   - 输出位置设置：支持在设置页面配置默认输出路径

   ### 重构模块
   - social_security_loader.py：支持多Sheet识别和字段智能匹配
   - two_table_mapper.py：集成数据合并器，支持默认值处理
   - tax_merge_page.py：集成新的Sheet选择和字段映射流程
   - settings_page.py：添加输出路径设置功能

   ### 测试
   - 新增37个单元测试，测试通过率100%

   ### 下载
   请从 GitHub Release 下载 Windows 安装包：
   https://github.com/Bob1817/xinfudTools/releases/tag/v1.1.0

   ### 反馈与支持
   - GitHub: https://github.com/Bob1817/xinfudTools
   - Gitee: https://gitee.com/shibo8817/xinfud-tools
   ```

4. **选择标签**
   - 标签: `v1.1.0`（如果不存在，选择 "新建标签"）
   - 目标: `main`

5. **点击 "创建"**

---

## 方法二：通过 API 创建（需要 Token）

### 1. 获取 Gitee Token

1. 访问: https://gitee.com/profile/personal_access_tokens
2. 点击 "生成新令牌"
3. 权限选择: `projects`, `pull_requests`
4. 复制生成的 Token

### 2. 设置环境变量

```bash
export GITEE_TOKEN="your_token_here"
```

### 3. 运行创建脚本

```bash
python create_gitee_release.py
```

或者使用 curl:

```bash
curl -X POST \
  "https://gitee.com/api/v5/repos/shibo8817/xinfud-tools/releases" \
  -H "Content-Type: application/json" \
  -H "Authorization: token $GITEE_TOKEN" \
  -d '{
    "tag_name": "v1.1.0",
    "name": "HR 数据处理工具集 v1.1.0",
    "body": "v1.1.0 发布说明...",
    "prerelease": false,
    "target_commitish": "main"
  }'
```

---

## 方法三：通过 GitHub Actions 自动创建

### 配置步骤

1. **设置 GitHub Secret**
   - 访问: https://github.com/Bob1817/xinfudTools/settings/secrets/actions
   - 点击 "New repository secret"
   - Name: `GITEE_TOKEN`
   - Value: 你的 Gitee Token
   - 点击 "Add secret"

2. **触发自动构建**
   - 访问: https://github.com/Bob1817/xinfudTools/actions/workflows/build-windows.yml
   - 点击 "Run workflow"
   - 选择分支: `main`
   - 点击 "Run workflow"

3. **等待构建完成**
   - 构建完成后会自动创建 GitHub Release
   - 同时会自动同步到 Gitee 并创建 Gitee Release

---

## 验证 Release

创建完成后，访问以下链接验证:

- Gitee Release: https://gitee.com/shibo8817/xinfud-tools/releases/v1.1.0
- GitHub Release: https://github.com/Bob1817/xinfudTools/releases/tag/v1.1.0

---

## 注意事项

1. **Gitee 仓库大小限制**: 当前仓库大小为 1735MB，超过了 1024MB 的配额限制
   - 建议清理不必要的文件
   - 或者使用 GitHub 作为主要发布渠道

2. **GitHub Actions 自动同步**: 配置了自动同步到 Gitee，但需要设置 `GITEE_TOKEN`

3. **安装包下载**: 由于 Gitee 文件大小限制，建议用户从 GitHub Release 下载安装包

---

## 快速操作清单

- [ ] 获取 Gitee Token
- [ ] 访问 Gitee Release 页面
- [ ] 创建 v1.1.0 Release
- [ ] 填写发布说明
- [ ] 验证 Release 创建成功
- [ ] 测试自动更新功能

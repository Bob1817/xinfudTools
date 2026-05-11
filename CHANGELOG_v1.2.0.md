# v1.2.0 更新日志

## 🎯 版本信息
- **版本号**: v1.2.0
- **发布日期**: 2026-05-11
- **更新类型**: 功能增强

## ✨ 核心更新

### 社保数据表字段匹配逻辑重构

#### 问题修复
修复了 v1.1.0 版本中社保数据表字段映射错误的问题：
- ❌ 旧版本：字段匹配逻辑不严格，导致【基本养老保险费】等字段数据为空
- ✅ 新版本：严格按照用户要求实现字段匹配逻辑

#### 新匹配规则

**1. 完全匹配标准**
字段名必须完全等于：
- 【基本养老保险费】
- 【基本医疗保险费】
- 【失业保险费】
- 【住房公积金】

**2. 部分匹配标准**
字段名包含关键字：
- 【养老】
- 【医疗】
- 【失业】
- 【公积金】

**3. 处理流程**

| 场景 | 处理方式 |
|------|----------|
| 只有一个Sheet完全匹配 | 直接使用，无需弹窗 |
| 多个Sheet完全匹配 | 弹窗让用户选择具体Sheet |
| 只有一个Sheet部分匹配 | 弹窗让用户确认字段映射 |
| 多个Sheet部分匹配 | 弹窗让用户选择Sheet并确认字段映射 |

#### 技术实现

**新增模块**:
- `core/sheet_detector_v3.py` - Sheet检测器V3
- `core/social_security_loader_v3.py` - 社保数据加载器V3
- `ui/dialogs/sheet_selector_v3.py` - Sheet选择弹窗
- `ui/dialogs/field_mapper_v3.py` - 字段映射确认弹窗

**修改模块**:
- `ui/tools/tax_merge_page.py` - 更新为使用V3版本

## 🔧 其他改进

### 数据映射逻辑
- 严格扫描所有Sheet
- 智能识别包含社保关键字的Sheet
- 支持字段名模糊匹配
- 用户确认机制确保数据准确性

### 用户体验
- 清晰的匹配状态显示
- 直观的字段映射界面
- 详细的匹配结果摘要

## 📋 系统要求

- **Windows**: 10/11 (64位)
- **macOS**: 12.0+ (开发环境)
- **Python**: 3.10+

## 📥 下载地址

- **GitHub**: https://github.com/Bob1817/xinfudTools/releases/tag/v1.2.0
- **Gitee**: https://gitee.com/shibo8817/xinfud-tools/releases/v1.2.0

## 🐛 已知问题

暂无

## 📞 反馈与支持

- **GitHub Issues**: https://github.com/Bob1817/xinfudTools/issues
- **Gitee Issues**: https://gitee.com/shibo8817/xinfud-tools/issues

---

**发布日期**: 2026-05-11
**版本**: v1.2.0

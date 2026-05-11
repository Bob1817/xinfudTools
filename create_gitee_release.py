#!/usr/bin/env python3
"""
创建 Gitee Release v1.1.0
需要设置 GITEE_TOKEN 环境变量
"""

import os
import sys
import json
import urllib.request
import urllib.error


def create_gitee_release():
    """创建 Gitee Release"""
    
    # 获取 Token
    token = os.environ.get('GITEE_TOKEN')
    if not token:
        print("错误: 请设置 GITEE_TOKEN 环境变量")
        print("获取方式: https://gitee.com/profile/personal_access_tokens")
        sys.exit(1)
    
    repo = "shibo8817/xinfud-tools"
    tag = "v1.1.0"
    name = "HR 数据处理工具集 v1.1.0"
    
    body = """## v1.1.0 发布说明

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
- Gitee: https://gitee.com/shibo8817/xinfud-tools"""
    
    # 准备请求数据
    data = {
        "tag_name": tag,
        "name": name,
        "body": body,
        "prerelease": False,
        "target_commitish": "main"
    }
    
    # 发送请求
    url = f"https://gitee.com/api/v5/repos/{repo}/releases"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {token}"
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Gitee Release 创建成功！")
            print(f"   标签: {result['tag_name']}")
            print(f"   名称: {result['name']}")
            print(f"   链接: {result['html_url']}")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ 创建失败: HTTP {e.code}")
        print(f"   错误信息: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"❌ 创建失败: {str(e)}")
        return False


if __name__ == "__main__":
    create_gitee_release()

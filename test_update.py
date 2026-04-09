#!/usr/bin/env python3
"""
测试更新功能脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.version import get_version, get_version_tuple, compare_versions
from core.updater import UpdateManager


def test_version():
    """测试版本功能"""
    print("=" * 50)
    print("测试版本管理功能")
    print("=" * 50)
    
    # 获取当前版本
    version = get_version()
    print(f"✅ 当前版本: {version}")
    
    # 版本元组
    version_tuple = get_version_tuple()
    print(f"✅ 版本元组: {version_tuple}")
    
    # 版本比较
    print("\n版本比较测试:")
    print(f"  1.0.0 vs 1.0.0: {compare_versions('1.0.0', '1.0.0')} (期望: 0)")
    print(f"  1.1.0 vs 1.0.0: {compare_versions('1.1.0', '1.0.0')} (期望: 1)")
    print(f"  0.9.0 vs 1.0.0: {compare_versions('0.9.0', '1.0.0')} (期望: -1)")
    print(f"  2.0.0 vs 1.9.9: {compare_versions('2.0.0', '1.9.9')} (期望: 1)")


def test_update_manager():
    """测试更新管理器"""
    print("\n" + "=" * 50)
    print("测试更新管理器")
    print("=" * 50)
    
    # 获取应用路径
    app_path = UpdateManager.get_app_path()
    print(f"✅ 应用路径: {app_path}")
    
    # 是否打包
    is_frozen = UpdateManager.is_frozen()
    print(f"✅ 是否打包: {is_frozen}")
    
    # 更新源
    print(f"✅ Gitee 仓库: {UpdateManager.GITEE_REPO}")
    print(f"✅ GitHub 仓库: {UpdateManager.GITHUB_REPO}")


def test_update_checker():
    """测试更新检查器"""
    print("\n" + "=" * 50)
    print("测试更新检查器（需要网络连接）")
    print("=" * 50)
    
    from PyQt6.QtWidgets import QApplication
    from core.updater import UpdateChecker
    
    # 创建 QApplication（UpdateChecker 需要）
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建检查器
    checker = UpdateChecker(
        UpdateManager.GITEE_REPO,
        UpdateManager.GITHUB_REPO
    )
    
    # 连接信号
    def on_update_available(info):
        print(f"✅ 发现新版本: {info['version']}")
        print(f"   来源: {info['source']}")
        print(f"   更新说明: {info.get('description', '无')[:100]}...")
        app.quit()
    
    def on_no_update():
        print("✅ 当前已是最新版本")
        app.quit()
    
    def on_error(error):
        print(f"❌ 检查失败: {error}")
        app.quit()
    
    checker.update_available.connect(on_update_available)
    checker.no_update.connect(on_no_update)
    checker.error.connect(on_error)
    
    # 开始检查
    print("正在检查更新...")
    checker.start()
    
    # 等待结果
    sys.exit(app.exec())


if __name__ == "__main__":
    print("\n🚀 HR 数据处理工具集 - 更新功能测试\n")
    
    # 运行测试
    test_version()
    test_update_manager()
    
    # 询问是否测试网络功能
    print("\n是否测试网络连接和更新检查？(y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        test_update_checker()
    else:
        print("\n✅ 测试完成！")

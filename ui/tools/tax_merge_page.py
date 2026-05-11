"""
报税合并页面（优化版）
支持身份证号合并、多Sheet识别、输出路径选择
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFileDialog, QMessageBox, QSplitter, QTableWidgetItem,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    ComboBox, PushButton, ProgressBar, TextEdit,
    TableWidget, InfoBar, InfoBarPosition,
    FluentIcon, setFont, CardWidget, BodyLabel,
    StrongBodyLabel, CaptionLabel
)
from pathlib import Path
from core.data_loader import PayrollLoader
from core.social_security_loader import SocialSecurityLoader
from core.data_mapper import TaxReportMapper
from core.two_table_mapper import TwoTableMapper
from core.report_generator import ReportGenerator
from core.config_manager import get_config_manager
from core.error_handler import handle_error, get_friendly_error_message
from db.database import Database
from ui.dialogs.sheet_selector import SheetSelectorDialog
from ui.dialogs.field_mapper import FieldMapperDialog
from ui.dialogs.output_path_dialog import OutputPathDialog
import pandas as pd
import subprocess
import datetime


class FileListWidget(TableWidget):
    """文件列表组件"""

    files_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["文件名", "路径"])
        self.setColumnWidth(0, 250)
        self.setColumnWidth(1, 0)  # 隐藏路径列
        self.verticalHeader().hide()
        self.setBorderVisible(True)
        self.setBorderRadius(8)

    def add_files(self, file_paths: list):
        for path in file_paths:
            if path not in self.files:
                self.files.append(path)
                row = self.rowCount()
                self.insertRow(row)
                self.setItem(row, 0, QTableWidgetItem(f"📄 {Path(path).name}"))
                self.setItem(row, 1, QTableWidgetItem(path))

        self.files_changed.emit(self.files)

    def clear_files(self):
        self.files.clear()
        self.setRowCount(0)
        self.files_changed.emit([])

    def get_files(self) -> list:
        return self.files


class GenerateWorker(QThread):
    """后台生成线程（优化版）"""
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(
        self,
        payroll_paths: list,
        social_security_paths: list,
        period: str,
        output_dir: str,
        ss_sheet_mapping: dict = None  # 新增：社保表Sheet映射
    ):
        super().__init__()
        self.payroll_paths = payroll_paths
        self.social_security_paths = social_security_paths
        self.period = period
        self.output_dir = output_dir
        self.ss_sheet_mapping = ss_sheet_mapping or {}  # {文件路径: (sheet_name, field_mapping)}

    def run(self):
        import sys
        import traceback
        import datetime
        import os

        # 调试日志路径
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")
        log_file = os.path.join(desktop, "HR_Tools_Crash_Debug.txt")

        def log(msg):
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.datetime.now()}] {msg}\n")
            except: pass

        log("================ 任务开始 ================")

        try:
            log("Step 0: Ensuring output directory exists")
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)

            log(f"Step 1: Reading {len(self.payroll_paths)} payroll files")
            self.progress.emit(f"正在读取 {len(self.payroll_paths)} 个发薪表...")
            payroll_dfs = []
            for i, path in enumerate(self.payroll_paths):
                log(f"  Reading payroll file {i+1}: {path}")
                self.progress.emit(f"正在读取发薪表 {i+1}/{len(self.payroll_paths)}...")
                
                loader = PayrollLoader()
                log("  -> Calling loader.load()")
                df = loader.load(path)
                log(f"  -> Loaded {len(df)} rows")
                payroll_dfs.append(df)

            log("Step 2: Concatenating payroll data")
            merged_payroll = pd.concat(payroll_dfs, ignore_index=True)
            log(f"Merged rows: {len(merged_payroll)}")

            # 2. 读取社保表
            all_ss_dict = {}
            has_social_security = len(self.social_security_paths) > 0

            if has_social_security:
                log("Step 2b: Reading Social Security files")
                self.progress.emit(f"正在读取 {len(self.social_security_paths)} 个社保表...")
                ss_loader = SocialSecurityLoader()
                
                for i, path in enumerate(self.social_security_paths):
                    log(f"  Reading SS file {i+1}: {path}")
                    self.progress.emit(f"正在读取社保表 {i+1}/{len(self.social_security_paths)}...")
                    
                    # 使用指定的Sheet和字段映射
                    sheet_info = self.ss_sheet_mapping.get(path)
                    if sheet_info:
                        sheet_name, field_mapping = sheet_info
                        ss_loader.select_sheet(sheet_name, field_mapping)
                    
                    df = ss_loader.load(path)
                    ss_dict = ss_loader.get_social_security_data(df)
                    
                    # 合并社保数据（同一身份证号取第一条）
                    for id_card, data in ss_dict.items():
                        if id_card not in all_ss_dict:
                            all_ss_dict[id_card] = data

                log(f"Total SS records: {len(all_ss_dict)}")

            # 3. 合并数据
            log("Step 3: Mapping data")
            tax_df = None
            mode_text = ""
            
            if has_social_security:
                self.progress.emit(f"正在合并 {len(merged_payroll)} 条发薪数据...")
                log("  -> Using TwoTableMapper")
                mapper = TwoTableMapper()
                tax_df, merge_stats = mapper.merge_and_map(merged_payroll, all_ss_dict, self.period)
                mode_text = "双表合并模式"
                log(f"Mapping complete. Rows: {len(tax_df)}")
            else:
                self.progress.emit("正在映射数据到申报表格式...")
                log("  -> Using TaxReportMapper")
                mapper = TaxReportMapper()
                tax_df = mapper.map(merged_payroll, self.period)
                merge_stats = {'total_records': len(tax_df)}
                mode_text = "单表模式"

            # 4. 生成申报表
            log("Step 4: Generating Excel")
            self.progress.emit("正在生成申报表...")
            
            generator = ReportGenerator()
            output_path = generator.generate(tax_df, self.period, self.output_dir)
            log(f"Excel generated at: {output_path}")

            stats = {
                "total": int(len(tax_df)),
                "columns": int(len(tax_df.columns)),
                "output_path": str(output_path),
                "payroll_files": int(len(self.payroll_paths)),
                "social_security_files": int(len(self.social_security_paths)),
                "mode": str(mode_text),
                "merge_stats": merge_stats,
            }

            log("Emitting finished signal")
            self.finished.emit(str(output_path), stats)
            log("================ 任务完成 ================")

        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"发生异常: {e}\n\n{tb}"
            log(f"ERROR: {error_msg}")
            
            # 使用友好的错误信息
            friendly_msg = get_friendly_error_message(e)
            self.error.emit(friendly_msg)


class TaxMergePage(QWidget):
    """报税合并页面（优化版）"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setObjectName("taxMergePage")
        self.db = db
        
        # 获取配置管理器
        self.config = get_config_manager()
        
        # 使用配置的输出路径
        self.output_dir = self.config.get_output_path()
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 社保表Sheet映射缓存
        self.ss_sheet_mapping = {}  # {文件路径: (sheet_name, field_mapping)}
        
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = StrongBodyLabel("报税合并", self)
        layout.addWidget(title)

        # 说明
        desc = BodyLabel("上传发薪表（必填）和社保表（选填），按身份证号码合并后生成个税扣缴申报表", self)
        desc.setStyleSheet("color: #606266;")
        layout.addWidget(desc)

        # 文件选择区域（使用 Splitter）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 发薪表选择（必填）
        payroll_card = CardWidget()
        payroll_layout = QVBoxLayout(payroll_card)
        payroll_layout.setSpacing(12)

        payroll_title = StrongBodyLabel("📄 发薪数据表（必填）")
        payroll_layout.addWidget(payroll_title)

        self.payroll_file_list = FileListWidget()
        self.payroll_file_list.files_changed.connect(self._update_merge_preview)
        payroll_layout.addWidget(self.payroll_file_list)

        # 按钮行
        btn_layout = QHBoxLayout()
        add_payroll_btn = PushButton("添加文件", self, FluentIcon.ADD)
        add_payroll_btn.clicked.connect(self._add_payroll_files)
        btn_layout.addWidget(add_payroll_btn)

        clear_payroll_btn = PushButton("清空", self, FluentIcon.DELETE)
        clear_payroll_btn.clicked.connect(self.payroll_file_list.clear_files)
        btn_layout.addWidget(clear_payroll_btn)

        btn_layout.addStretch()
        payroll_layout.addLayout(btn_layout)

        # 社保表选择（选填）
        ss_card = CardWidget()
        ss_layout = QVBoxLayout(ss_card)
        ss_layout.setSpacing(12)

        ss_title = StrongBodyLabel("📊 社保数据表（选填）")
        ss_layout.addWidget(ss_title)

        self.ss_file_list = FileListWidget()
        self.ss_file_list.files_changed.connect(self._update_merge_preview)
        ss_layout.addWidget(self.ss_file_list)

        btn_layout2 = QHBoxLayout()
        add_ss_btn = PushButton("添加文件", self, FluentIcon.ADD)
        add_ss_btn.clicked.connect(self._add_social_security_files)
        btn_layout2.addWidget(add_ss_btn)

        clear_ss_btn = PushButton("清空", self, FluentIcon.DELETE)
        clear_ss_btn.clicked.connect(self.ss_file_list.clear_files)
        btn_layout2.addWidget(clear_ss_btn)

        btn_layout2.addStretch()
        ss_layout.addLayout(btn_layout2)

        splitter.addWidget(payroll_card)
        splitter.addWidget(ss_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        # 匹配预览
        self.merge_preview = TextEdit()
        self.merge_preview.setReadOnly(True)
        self.merge_preview.setMaximumHeight(120)
        layout.addWidget(self.merge_preview)

        # 所属期
        period_group = QGroupBox("所属期设置")
        period_layout = QHBoxLayout()

        # 年份下拉框
        self.year_combo = ComboBox()
        self.year_combo.setFixedWidth(120)
        current_year = datetime.datetime.now().year
        for year in range(current_year - 2, current_year + 3):
            self.year_combo.addItem(str(year), userData=year)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._update_period_value)
        period_layout.addWidget(self.year_combo)

        # 月份下拉框
        self.month_combo = ComboBox()
        self.month_combo.setFixedWidth(100)
        for month in range(1, 13):
            self.month_combo.addItem(f"{month}月", userData=month)
        current_month = datetime.datetime.now().month
        self.month_combo.setCurrentIndex(current_month - 1)
        self.month_combo.currentIndexChanged.connect(self._update_period_value)
        period_layout.addWidget(self.month_combo)

        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        self.period_value = ""
        self._update_period_value()

        # 生成按钮
        from PyQt6.QtWidgets import QPushButton as StdPushButton
        self.generate_btn = StdPushButton("生成个税申报表")
        self.generate_btn.setFixedHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: #0d6efd;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background: #0b5ed7; }
            QPushButton:disabled { background: #6c757d; }
        """)
        self.generate_btn.clicked.connect(self._start_generate)
        layout.addWidget(self.generate_btn)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
                border-radius: 3px;
            }
        """)
        self.progress_label = CaptionLabel("")
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def _update_period_value(self):
        """更新所属期值"""
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        if year and month:
            self.period_value = f"{year}-{month:02d}"

    def _add_social_security_files(self):
        """添加社保文件（优化版，支持Sheet选择）"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择社保数据表", "", "Excel 文件 (*.xlsx *.xls)"
        )
        
        if not paths:
            return
        
        # 检测每个文件的Sheet
        for path in paths:
            try:
                ss_loader = SocialSecurityLoader()
                need_select, results, summary = ss_loader.detect_sheets(path)
                
                if need_select:
                    # 需要用户选择Sheet
                    selected = SheetSelectorDialog.select_sheet(results, self)
                    
                    if selected:
                        # 检查是否需要字段映射确认
                        if not selected.is_perfect_match:
                            # 需要确认字段映射
                            field_mapping = FieldMapperDialog.confirm_mapping(
                                selected.sample_data.columns.tolist(),
                                selected.matched_fields,
                                self
                            )
                            
                            if field_mapping:
                                self.ss_sheet_mapping[path] = (selected.sheet_name, field_mapping)
                            else:
                                # 用户取消了字段映射，跳过此文件
                                continue
                        else:
                            self.ss_sheet_mapping[path] = (selected.sheet_name, selected.matched_fields)
                    else:
                        # 用户取消了Sheet选择，跳过此文件
                        continue
                else:
                    # 自动选择了Sheet
                    if results:
                        best = results[0]
                        self.ss_sheet_mapping[path] = (best.sheet_name, best.matched_fields)
                
                # 添加到列表
                self.ss_file_list.add_files([path])
                
            except Exception as e:
                error_info = handle_error(e, {'path': path})
                QMessageBox.warning(
                    self,
                    "文件检测失败",
                    f"无法检测文件：{Path(path).name}\n\n{error_info.message}"
                )

    def _add_payroll_files(self):
        """添加发薪文件"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择发薪数据表", "", "Excel 文件 (*.xlsx *.xls)"
        )
        if paths:
            self.payroll_file_list.add_files(list(paths))

    def _update_merge_preview(self):
        """更新合并预览"""
        payroll_files = self.payroll_file_list.get_files()
        ss_files = self.ss_file_list.get_files()

        if not payroll_files:
            self.merge_preview.setPlainText("")
            return

        try:
            payroll_ids = set()
            total_payroll_rows = 0
            for path in payroll_files:
                df = pd.read_excel(path, dtype={"身份证号": str})
                total_payroll_rows += len(df)
                for id_card in df["身份证号"]:
                    cleaned = str(id_card).strip().upper().replace(".0", "")
                    payroll_ids.add(cleaned)

            if ss_files:
                ss_loader = SocialSecurityLoader()
                all_ss_ids = set()
                total_ss_rows = 0

                for path in ss_files:
                    # 使用缓存的Sheet映射
                    sheet_info = self.ss_sheet_mapping.get(path)
                    if sheet_info:
                        sheet_name, _ = sheet_info
                        ss_loader.select_sheet(sheet_name)
                    
                    df = ss_loader.load(path)
                    total_ss_rows += len(df)
                    for id_card in df["身份证号"]:
                        cleaned = str(id_card).strip().upper().replace(".0", "")
                        all_ss_ids.add(cleaned)

                matched = len(all_ss_ids & payroll_ids)
                only_in_payroll = len(payroll_ids - all_ss_ids)
                only_in_ss = len(all_ss_ids - payroll_ids)
                match_rate = matched / len(payroll_ids) * 100 if payroll_ids else 0

                self.merge_preview.setPlainText(
                    f"✅ 发薪表：{len(payroll_files)} 个文件，{total_payroll_rows} 条数据\n"
                    f"✅ 社保表：{len(ss_files)} 个文件，{total_ss_rows} 条数据\n"
                    f"🔗 身份证号匹配：{matched} 条 ({match_rate:.1f}%)\n"
                    f"📌 仅在发薪表：{only_in_payroll} 条\n"
                    f"📌 仅在社保表：{only_in_ss} 条\n"
                    f"⚙️ 模式：双表合并（优先使用社保表数据）"
                )
            else:
                self.merge_preview.setPlainText(
                    f"✅ 发薪表：{len(payroll_files)} 个文件，{total_payroll_rows} 条数据\n"
                    f"📌 社保表：未上传（选填）\n"
                    f"⚙️ 模式：单表模式（使用发薪表中的个人社保数据）"
                )

        except Exception as e:
            error_info = handle_error(e)
            self.merge_preview.setPlainText(f"❌ 预览出错：{error_info.message}")

    def _start_generate(self):
        """开始生成（优化版，支持输出路径选择）"""
        payroll_files = self.payroll_file_list.get_files()
        ss_files = self.ss_file_list.get_files()

        if not payroll_files:
            InfoBar.error(
                title="提示",
                content="请先选择发薪数据表（必填）",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not self.period_value:
            InfoBar.error(
                title="提示",
                content="请选择所属期",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 选择输出路径
        output_path, remember, auto_open = OutputPathDialog.select_output_path(
            self.output_dir, 
            self
        )
        
        if not output_path:
            # 用户取消了
            return
        
        # 更新输出路径
        self.output_dir = output_path
        
        # 更新配置
        if remember:
            self.config.set_output_path(output_path)
        self.config.set_auto_open_folder(auto_open)

        self.generate_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_label.setText("处理中...")

        self.worker = GenerateWorker(
            payroll_files,
            ss_files,
            self.period_value,
            self.output_dir,
            self.ss_sheet_mapping
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, msg):
        self.progress_label.setText(msg)

    def _on_finished(self, output_path, stats):
        try:
            self.progress_bar.setRange(0, 100)
            self.progress_label.setText("")
            self.generate_btn.setEnabled(True)

            source_desc = f"[发薪]{' + '.join(Path(f).name for f in self.payroll_file_list.get_files())}"
            if self.ss_file_list.get_files():
                source_desc += f" + [社保]{' + '.join(Path(f).name for f in self.ss_file_list.get_files())}"

            try:
                self.db.save_record({
                    "period": self.period_value,
                    "source_file": source_desc,
                    "output_file": output_path,
                    "total_records": stats["total"],
                    "note": f"{stats['mode']}，发薪表{stats['payroll_files']}个，社保表{stats['social_security_files']}个",
                })
            except Exception as db_err:
                print(f"Database save error (non-fatal): {db_err}")

            # 延迟打开文件夹
            if self.config.get_auto_open_folder():
                QTimer.singleShot(500, lambda: self._open_folder(output_path))

            # 显示成功信息
            success_msg = f"个税申报表已生成：{stats['total']} 条数据"
            if 'merge_stats' in stats:
                merge_stats = stats['merge_stats']
                if merge_stats.get('merged_payroll_records', 0) > 0:
                    success_msg += f"\n合并了 {merge_stats['merged_payroll_records']} 条重复记录"

            InfoBar.success(
                title="生成成功",
                content=success_msg,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        except Exception as e:
            import traceback
            print(f"Error in _on_finished: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"生成成功但后续处理失败：{e}")

    def _on_error(self, err_msg):
        self.progress_bar.setRange(0, 100)
        self.progress_label.setText("")
        self.generate_btn.setEnabled(True)

        InfoBar.error(
            title="生成失败",
            content="处理过程中发生错误，请查看详细错误信息",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=10000,
            parent=self
        )
        
        # 显示详细错误对话框
        QMessageBox.critical(self, "生成失败", err_msg)

    @staticmethod
    def _open_folder(file_path):
        """打开文件所在文件夹"""
        folder = str(Path(file_path).parent)
        if Path(file_path).root == '/':
            subprocess.run(['open', folder])
        else:
            subprocess.Popen(f'explorer "{folder}"', shell=True)

    def receive_dropped_files(self, files: list):
        """接收拖放的文件"""
        ss_files = []
        payroll_files = []

        for path in files:
            name = Path(path).name.lower()
            if "社保" in name or "social" in name:
                ss_files.append(path)
            else:
                payroll_files.append(path)

        if ss_files:
            self.ss_file_list.add_files(ss_files)
        if payroll_files:
            self.payroll_file_list.add_files(payroll_files)

        if ss_files or payroll_files:
            self._update_merge_preview()

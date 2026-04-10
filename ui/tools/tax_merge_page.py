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
from db.database import Database
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
    """后台生成线程"""
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(
        self,
        payroll_paths: list,
        social_security_paths: list,
        period: str,
        output_dir: str
    ):
        super().__init__()
        self.payroll_paths = payroll_paths
        self.social_security_paths = social_security_paths
        self.period = period
        self.output_dir = output_dir

    def run(self):
        import sys
        import traceback
        print("[Worker] Starting GenerateWorker", flush=True)
        print(f"[Worker] payroll_paths: {self.payroll_paths}", flush=True)
        print(f"[Worker] social_security_paths: {self.social_security_paths}", flush=True)
        print(f"[Worker] period: {self.period}", flush=True)
        print(f"[Worker] output_dir: {self.output_dir}", flush=True)
        
        try:
            # 1. 读取所有发薪表（必填）
            print("[Worker] Step 1: Reading payroll files...", flush=True)
            self.progress.emit(f"正在读取 {len(self.payroll_paths)} 个发薪表...")
            payroll_dfs = []
            for i, path in enumerate(self.payroll_paths):
                print(f"[Worker]   Reading payroll file {i+1}: {path}", flush=True)
                self.progress.emit(f"正在读取发薪表 {i+1}/{len(self.payroll_paths)}...")
                loader = PayrollLoader()
                df = loader.load(path)
                print(f"[Worker]   Loaded {len(df)} rows from {path}", flush=True)
                payroll_dfs.append(df)

            print("[Worker] Concatenating payroll data...", flush=True)
            merged_payroll = pd.concat(payroll_dfs, ignore_index=True)
            print(f"[Worker] Merged payroll: {len(merged_payroll)} rows", flush=True)

            # 2. 读取社保表（选填）
            all_ss_dict = {}
            has_social_security = len(self.social_security_paths) > 0
            print(f"[Worker] Step 2: has_social_security={has_social_security}", flush=True)

            if has_social_security:
                self.progress.emit(f"正在读取 {len(self.social_security_paths)} 个社保表...")
                ss_loader = SocialSecurityLoader()

                for i, path in enumerate(self.social_security_paths):
                    print(f"[Worker]   Reading social security file {i+1}: {path}", flush=True)
                    self.progress.emit(f"正在读取社保表 {i+1}/{len(self.social_security_paths)}...")
                    df = ss_loader.load(path)
                    ss_dict = ss_loader.get_social_security_data(df)
                    for id_card, data in ss_dict.items():
                        if id_card not in all_ss_dict:
                            all_ss_dict[id_card] = data

            # 3. 合并数据并生成申报表
            print("[Worker] Step 3: Mapping data...", flush=True)
            tax_df = None
            mode_text = ""
            
            if has_social_security:
                self.progress.emit(f"正在合并 {len(merged_payroll)} 条发薪数据...")
                mapper = TwoTableMapper()
                print("[Worker]   Using TwoTableMapper.merge_and_map...", flush=True)
                tax_df = mapper.merge_and_map(merged_payroll, all_ss_dict, self.period)
                mode_text = "双表合并模式"
            else:
                self.progress.emit("正在映射数据到申报表格式...")
                mapper = TaxReportMapper()
                print("[Worker]   Using TaxReportMapper.map...", flush=True)
                print(f"[Worker]   merged_payroll shape: {merged_payroll.shape}", flush=True)
                print(f"[Worker]   merged_payroll columns: {list(merged_payroll.columns)[:15]}...", flush=True)
                tax_df = mapper.map(merged_payroll, self.period)
                mode_text = "单表模式"
            
            print(f"[Worker] Mapped to {len(tax_df)} rows, {len(tax_df.columns)} cols", flush=True)
            print(f"[Worker] tax_df dtypes:\n{tax_df.dtypes.to_string()}", flush=True)

            # 4. 生成申报表
            print("[Worker] Step 4: Generating Excel...", flush=True)
            self.progress.emit("正在生成申报表...")
            generator = ReportGenerator()
            output_path = generator.generate(tax_df, self.period, self.output_dir)
            print(f"[Worker] Excel generated: {output_path}", flush=True)

            stats = {
                "total": int(len(tax_df)),
                "columns": int(len(tax_df.columns)),
                "output_path": str(output_path),
                "payroll_files": int(len(self.payroll_paths)),
                "social_security_files": int(len(self.social_security_paths)),
                "mode": str(mode_text),
            }

            print("[Worker] Emitting finished signal...", flush=True)
            # Convert to simple tuple to avoid PyQt signal serialization issues
            self.finished.emit(str(output_path), stats)
            print("[Worker] Done!", flush=True)

        except Exception as e:
            tb = traceback.format_exc()
            print(f"[Worker] ERROR: {e}\n{tb}", flush=True)
            sys.stdout.flush()
            self.error.emit(f"{e}\n\n{tb}")


class TaxMergePage(QWidget):
    """报税合并页面"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setObjectName("taxMergePage")
        self.db = db
        self.output_dir = str(Path.home() / "Desktop")
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
        print(f"[UI] Connecting generate_btn to _start_generate", flush=True)
        self.generate_btn.clicked.connect(self._start_generate)
        print(f"[UI] generate_btn connected", flush=True)
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
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择社保数据表", "", "Excel 文件 (*.xlsx *.xls)"
        )
        if paths:
            self.ss_file_list.add_files(list(paths))

    def _add_payroll_files(self):
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
            self.merge_preview.setPlainText(f"❌ 预览出错：{e}")

    def _start_generate(self):
        import sys
        print("[UI] _start_generate called", flush=True)
        sys.stdout.flush()
        
        payroll_files = self.payroll_file_list.get_files()
        ss_files = self.ss_file_list.get_files()
        
        print(f"[UI] payroll_files: {payroll_files}", flush=True)
        print(f"[UI] ss_files: {ss_files}", flush=True)
        print(f"[UI] period_value: {self.period_value}", flush=True)
        sys.stdout.flush()

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

        self.generate_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_label.setText("处理中...")

        self.worker = GenerateWorker(
            payroll_files,
            ss_files,
            self.period_value,
            self.output_dir
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

            # 延迟打开文件夹，避免阻塞 UI 线程
            QTimer.singleShot(500, lambda: self._open_folder(output_path))

            InfoBar.success(
                title="生成成功",
                content=f"个税申报表已生成：{stats['total']} 条数据\n已自动打开文件所在文件夹。",
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
            content=err_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=10000,
            parent=self
        )

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

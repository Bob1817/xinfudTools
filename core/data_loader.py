import pandas as pd
from pathlib import Path


class PayrollLoader:
    """发薪表读取器"""

    # 发薪表列位置（0-based index）
    # 前11列: 发薪月份, 完成时间, 姓名, 身份证号, 手机号码, 项目名称,
    #         客户公司, 银行名称, 银行卡号, 应发金额, 个税
    # 企业部分(7列): 社保公积金总计, 养老, 失业, 工伤, 医疗, 公积金, 总计
    # 个人部分(6列): 养老, 失业, 工伤, 医疗, 公积金, 总计

    # 基础字段列名
    COL_NAME = "姓名"
    COL_ID = "身份证号"
    COL_PHONE = "手机号码"
    COL_CLIENT = "客户公司"
    COL_SERVICE = "服务主体"
    COL_GROSS_PAY = "应发金额"
    COL_TAX = "个税"
    COL_NET_PAY = "实发金额"
    COL_COMM_FEE = "通讯费"
    COL_REMARK = "备注"

    # 企业部分列位置（从第11列开始，索引10）
    COMPANY_START = 10
    # 个人部分列位置（从第18列开始，索引17）
    PERSONAL_START = 17

    def load(self, file_path: str) -> pd.DataFrame:
        """读取发薪表"""
        df = pd.read_excel(
            file_path,
            dtype={"身份证号": str, "手机号码": str, "银行卡号": str},
        )

        # 身份证号清洗
        df[self.COL_ID] = df[self.COL_ID].astype(str).str.strip().str.upper()
        # 去掉可能的 .0（Excel数字格式问题）
        df[self.COL_ID] = df[self.COL_ID].str.replace(r"\.0$", "", regex=True)

        self._validate(df)
        return df

    def _validate(self, df: pd.DataFrame):
        """校验必要列"""
        required = [self.COL_NAME, self.COL_ID, self.COL_GROSS_PAY]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"发薪表缺少必要列：{missing}")

        if len(df.columns) < 24:
            raise ValueError(
                f"发薪表列数不足（当前{len(df.columns)}列，预期至少24列），"
                f"请确认企业部分和个人部分的社保公积金列完整"
            )

    def get_company_columns(self, df: pd.DataFrame) -> list[str]:
        """获取企业部分列名"""
        return list(df.columns[self.COMPANY_START : self.COMPANY_START + 7])

    def get_personal_columns(self, df: pd.DataFrame) -> list[str]:
        """获取个人部分列名（按名称查找，支持灵活列顺序）"""
        # 按名称查找个人部分列
        all_cols = list(df.columns)
        personal_names = []
        target_names = ["养老", "失业", "工伤", "医疗", "公积金", "总计"]

        for target in target_names:
            for col in all_cols:
                if target in col and col not in personal_names:
                    personal_names.append(col)
                    break

        # 如果按名称没找到，尝试按位置获取
        if len(personal_names) < 5 and len(all_cols) >= self.PERSONAL_START + 6:
            personal_names = all_cols[self.PERSONAL_START:self.PERSONAL_START + 6]

        return personal_names

    def get_column_info(self, df: pd.DataFrame) -> dict:
        """获取列位置信息（用于调试）"""
        all_cols = list(df.columns)
        return {
            "total_columns": len(all_cols),
            "columns": all_cols,
            "company_range": f"索引 {self.COMPANY_START}-{self.COMPANY_START + 6}",
            "company_names": self.get_company_columns(df),
            "personal_range": f"索引 {self.PERSONAL_START}-{self.PERSONAL_START + 5}",
            "personal_names": self.get_personal_columns(df),
        }

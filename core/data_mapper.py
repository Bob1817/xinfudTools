import pandas as pd
from core.data_loader import PayrollLoader


class TaxReportMapper:
    """将发薪表数据映射为个税申报表格式"""

    # 申报表模板列名（按顺序）
    TAX_COLUMNS = [
        "*工号",
        "*姓名",
        "*证件类型",
        "*证件号码",
        "本期收入",
        "本期免税收入",
        "基本养老保险费",
        "基本医疗保险费",
        "失业保险费",
        "住房公积金",
        "累计子女教育",
        "累计继续教育",
        "累计住房贷款利息",
        "累计住房租金",
        "累计赡养老人",
        "累计3岁以下婴幼儿照护",
        "累计个人养老金",
        "企业(职业)年金",
        "商业健康保险",
        "税延养老保险",
        "公务交通费用",
        "通讯费用",
        "律师办案费用",
        "西藏附加减除费用",
        "其他",
        "准予扣除的捐赠额",
        "减免税额",
        "备注",
    ]

    def __init__(self):
        self.loader = PayrollLoader()

    def map(self, payroll_df: pd.DataFrame, period: str = "") -> pd.DataFrame:
        """执行映射"""
        df = payroll_df.copy()
        l = self.loader
        personal_cols = l.get_personal_columns(df)

        # 个人部分列名（按申报表顺序：养老、医疗、失业、公积金）
        # 注意：发薪表个人部分顺序是 养老, 失业, 工伤, 医疗, 公积金, 总计
        # 需要重新映射
        col_pension = personal_cols[0]      # 养老
        col_unemploy = personal_cols[1]     # 失业
        col_work_injury = personal_cols[2]  # 工伤（申报表不需要）
        col_medical = personal_cols[3]      # 医疗
        col_housing = personal_cols[4]      # 公积金

        # 构建申报表
        result = pd.DataFrame()

        result["*工号"] = range(1, len(df) + 1)
        result["*姓名"] = df[l.COL_NAME]
        result["*证件类型"] = "居民身份证"
        result["*证件号码"] = df[l.COL_ID]
        result["本期收入"] = df[l.COL_GROSS_PAY]
        result["本期免税收入"] = 0
        result["基本养老保险费"] = df[col_pension].fillna(0)
        result["基本医疗保险费"] = df[col_medical].fillna(0)
        result["失业保险费"] = df[col_unemploy].fillna(0)
        result["住房公积金"] = df[col_housing].fillna(0)
        result["累计子女教育"] = 0
        result["累计继续教育"] = 0
        result["累计住房贷款利息"] = 0
        result["累计住房租金"] = 0
        result["累计赡养老人"] = 0
        result["累计3岁以下婴幼儿照护"] = 0
        result["累计个人养老金"] = 0
        result["企业(职业)年金"] = 0
        result["商业健康保险"] = 0
        result["税延养老保险"] = 0
        result["公务交通费用"] = 0
        result["通讯费用"] = df[l.COL_COMM_FEE].fillna(0) if l.COL_COMM_FEE in df.columns else 0
        result["律师办案费用"] = 0
        result["西藏附加减除费用"] = 0
        result["其他"] = 0
        result["准予扣除的捐赠额"] = 0
        result["减免税额"] = 0
        result["备注"] = df[l.COL_REMARK].fillna("") if l.COL_REMARK in df.columns else ""

        # 确保数值列是数值类型，避免 openpyxl 报错
        for col in ["本期收入", "基本养老保险费", "基本医疗保险费", "失业保险费", "住房公积金", "通讯费用"]:
            result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)

        result["*证件号码"] = result["*证件号码"].astype(str)
        result["*姓名"] = result["*姓名"].astype(str)
        result["备注"] = result["备注"].fillna("").astype(str)

        return result

    def validate_mapping(self, payroll_df: pd.DataFrame) -> dict:
        """验证映射关系，返回检测结果"""
        info = self.loader.get_column_info(payroll_df)

        personal_cols = info["personal_names"]
        company_cols = info["company_names"]

        return {
            "total_rows": len(payroll_df),
            "total_columns": info["total_columns"],
            "company_columns": company_cols,
            "personal_columns": personal_cols,
            "sample_personal": {
                col: payroll_df[col].head(3).tolist()
                for col in personal_cols
            },
        }

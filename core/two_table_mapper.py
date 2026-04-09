import pandas as pd
from core.data_loader import PayrollLoader
from core.social_security_loader import SocialSecurityLoader


class TwoTableMapper:
    """双表合并映射器：社保数据表 + 发薪表 → 个税申报表"""

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
        "累计 3 岁以下婴幼儿照护",
        "累计个人养老金",
        "企业 (职业)年金",
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
        self.payroll_loader = PayrollLoader()
        self.ss_loader = SocialSecurityLoader()

    def merge_and_map(
        self,
        payroll_df: pd.DataFrame,
        social_security_dict: dict,
        period: str = ""
    ) -> pd.DataFrame:
        """
        合并社保数据和发薪表数据，生成申报表格式

        Args:
            payroll_df: 发薪表数据
            social_security_dict: 社保数据字典（以身份证号为 key）
            period: 所属期

        Returns:
            申报表格式的 DataFrame
        """
        l = self.payroll_loader
        personal_cols = l.get_personal_columns(payroll_df)

        # 发薪表个人部分列名映射
        # 发薪表个人部分顺序：养老 [0], 失业 [1], 工伤 [2], 医疗 [3], 公积金 [4], 总计 [5]
        col_pension = personal_cols[0]      # 养老
        col_unemploy = personal_cols[1]     # 失业
        col_work_injury = personal_cols[2]  # 工伤（申报表不需要）
        col_medical = personal_cols[3]      # 医疗
        col_housing = personal_cols[4]      # 公积金

        # 构建申报表
        result = pd.DataFrame()

        # 遍历发薪表数据
        for _, row in payroll_df.iterrows():
            id_card = str(row[l.COL_ID]).strip()

            # 获取社保数据（如果有）
            ss_data = social_security_dict.get(id_card, {})

            # 构建一行申报表数据
            tax_row = {}
            tax_row["*工号"] = len(result) + 1
            tax_row["*姓名"] = row[l.COL_NAME]
            tax_row["*证件类型"] = "居民身份证"
            tax_row["*证件号码"] = id_card

            # 本期收入（发薪表的应发金额）
            tax_row["本期收入"] = row[l.COL_GROSS_PAY] if pd.notna(row[l.COL_GROSS_PAY]) else 0
            tax_row["本期免税收入"] = 0

            # 社保公积金 - 优先使用社保表数据，没有则用发薪表个人部分数据
            # 社保表：个人养老、个人医疗、个人失业、个人公积金
            if ss_data:
                tax_row["基本养老保险费"] = ss_data.get(self.ss_loader.COL_PENSION, 0) or 0
                tax_row["基本医疗保险费"] = ss_data.get(self.ss_loader.COL_MEDICAL, 0) or 0
                tax_row["失业保险费"] = ss_data.get(self.ss_loader.COL_UNEMPLOYMENT, 0) or 0
                tax_row["住房公积金"] = ss_data.get(self.ss_loader.COL_HOUSING, 0) or 0
            else:
                # 使用发薪表个人部分数据
                tax_row["基本养老保险费"] = row[col_pension] if pd.notna(row[col_pension]) else 0
                tax_row["基本医疗保险费"] = row[col_medical] if pd.notna(row[col_medical]) else 0
                tax_row["失业保险费"] = row[col_unemploy] if pd.notna(row[col_unemploy]) else 0
                tax_row["住房公积金"] = row[col_housing] if pd.notna(row[col_housing]) else 0

            # 专项附加扣除等全部为 0
            tax_row["累计子女教育"] = 0
            tax_row["累计继续教育"] = 0
            tax_row["累计住房贷款利息"] = 0
            tax_row["累计住房租金"] = 0
            tax_row["累计赡养老人"] = 0
            tax_row["累计 3 岁以下婴幼儿照护"] = 0
            tax_row["累计个人养老金"] = 0
            tax_row["企业 (职业) 年金"] = 0
            tax_row["商业健康保险"] = 0
            tax_row["税延养老保险"] = 0
            tax_row["公务交通费用"] = 0

            # 通讯费用
            if l.COL_COMM_FEE in row.index:
                tax_row["通讯费用"] = row[l.COL_COMM_FEE] if pd.notna(row[l.COL_COMM_FEE]) else 0
            else:
                tax_row["通讯费用"] = 0

            tax_row["律师办案费用"] = 0
            tax_row["西藏附加减除费用"] = 0
            tax_row["其他"] = 0
            tax_row["准予扣除的捐赠额"] = 0
            tax_row["减免税额"] = 0

            # 备注
            if l.COL_REMARK in row.index:
                tax_row["备注"] = row[l.COL_REMARK] if pd.notna(row[l.COL_REMARK]) else ""
            else:
                tax_row["备注"] = ""

            result = pd.concat([result, pd.DataFrame([tax_row])], ignore_index=True)

        return result

    def validate_merge(
        self,
        payroll_df: pd.DataFrame,
        social_security_df: pd.DataFrame
    ) -> dict:
        """验证合并结果，返回检测结果"""
        # 发薪表数据
        payroll_ids = set(str(id_card).strip().upper() for id_card in payroll_df[self.payroll_loader.COL_ID])
        ss_ids = set(str(id_card).strip().upper() for id_card in social_security_df[self.ss_loader.COL_ID])

        # 匹配情况
        matched_ids = payroll_ids & ss_ids
        only_in_payroll = payroll_ids - ss_ids
        only_in_ss = ss_ids - payroll_ids

        return {
            "payroll_total": len(payroll_df),
            "social_security_total": len(social_security_df),
            "matched_count": len(matched_ids),
            "only_in_payroll_count": len(only_in_payroll),
            "only_in_ss_count": len(only_in_ss),
            "match_rate": len(matched_ids) / len(payroll_ids) * 100 if payroll_ids else 0,
        }

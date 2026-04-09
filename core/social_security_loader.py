import pandas as pd
from pathlib import Path


class SocialSecurityLoader:
    """社保数据表读取器"""

    # 本月发薪明细 sheet 中的列
    COL_NAME = "姓名"
    COL_ID = "身份证号"
    COL_PENSION = "个人养老"
    COL_MEDICAL = "个人医疗"
    COL_UNEMPLOYMENT = "个人失业"
    COL_HOUSING = "个人公积金"

    # 需要提取的列（按申报表顺序）
    TARGET_COLUMNS = [COL_ID, COL_NAME, COL_PENSION, COL_MEDICAL, COL_UNEMPLOYMENT, COL_HOUSING]

    def load(self, file_path: str) -> pd.DataFrame:
        """读取社保数据表中的【本月发薪明细】sheet"""
        df = pd.read_excel(
            file_path,
            sheet_name="本月发薪明细",
            dtype={
                "身份证号": str,
                "手机号码": str,
                "银行卡号": str,
            },
        )

        # 身份证号清洗
        df[self.COL_ID] = df[self.COL_ID].astype(str).str.strip().str.upper()
        # 去掉可能的 .0（Excel 数字格式问题）
        df[self.COL_ID] = df[self.COL_ID].str.replace(r"\.0$", "", regex=True)
        # 去掉可能的 'NAN' 空值
        df[self.COL_ID] = df[self.COL_ID].replace("NAN", "")

        # 只保留需要的列
        result = df[self.TARGET_COLUMNS].copy()

        # 删除空行
        result = result.dropna(subset=[self.COL_ID])

        self._validate(result)
        return result

    def _validate(self, df: pd.DataFrame):
        """校验必要列"""
        if len(df) == 0:
            raise ValueError("【本月发薪明细】sheet 中没有有效数据")

        missing = [c for c in [self.COL_ID, self.COL_NAME] if c not in df.columns]
        if missing:
            raise ValueError(f"社保数据表缺少必要列：{missing}")

    def get_social_security_data(self, df: pd.DataFrame) -> dict:
        """
        将数据转换为以身份证号为 key 的字典，方便后续合并
        返回格式：{
            "身份证号": {
                "姓名": "...",
                "个人养老": ...,
                "个人医疗": ...,
                "个人失业": ...,
                "个人公积金": ...
            },
            ...
        }
        """
        return df.set_index(self.COL_ID).to_dict(orient="index")

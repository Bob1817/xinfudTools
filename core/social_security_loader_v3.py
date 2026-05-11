"""
社保数据表读取器 V3（最终修复版）
严格按照用户要求实现字段匹配逻辑
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from core.sheet_detector_v3 import SheetDetectorV3, SheetMatchResult, detect_social_security_sheets_v3
from core.error_handler import handle_error


class SocialSecurityLoaderV3:
    """社保数据表读取器 V3（最终修复版）"""

    # 标准列名（用于数据读取后的统一处理）
    COL_NAME = "姓名"
    COL_ID = "身份证号"
    COL_PENSION = "个人养老"
    COL_MEDICAL = "个人医疗"
    COL_UNEMPLOYMENT = "个人失业"
    COL_HOUSING = "个人公积金"

    # 需要提取的列（按申报表顺序）
    TARGET_COLUMNS = [COL_ID, COL_NAME, COL_PENSION, COL_MEDICAL, COL_UNEMPLOYMENT, COL_HOUSING]

    def __init__(self):
        self.sheet_detector = SheetDetectorV3()
        self.current_field_mapping: Dict[str, str] = {}
        self.current_sheet_name: Optional[str] = None
        self.current_match_type: Optional[str] = None  # 'perfect' 或 'partial'

    def detect_sheets(self, file_path: str) -> Tuple[str, List[SheetMatchResult], str]:
        """
        检测文件中的社保数据Sheet
        
        Returns:
            (处理模式, 匹配结果列表, 摘要信息)
        """
        try:
            return detect_social_security_sheets_v3(file_path)
        except Exception as e:
            error_info = handle_error(e, {'path': file_path})
            raise ValueError(f"检测Sheet失败: {error_info.message}")

    def select_sheet(self, sheet_name: str, field_mapping: Dict[str, str], match_type: str):
        """
        选择要使用的Sheet和字段映射
        
        Args:
            sheet_name: Sheet名称
            field_mapping: 字段映射（必须包含养老、医疗、失业、公积金四个字段）
            match_type: 匹配类型 ('perfect' 或 'partial')
        """
        required_fields = ['养老', '医疗', '失业', '公积金']
        missing = [f for f in required_fields if f not in field_mapping]
        
        if missing:
            raise ValueError(f"字段映射缺少必要字段: {missing}")
        
        self.current_sheet_name = sheet_name
        self.current_field_mapping = field_mapping
        self.current_match_type = match_type

    def load(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """读取社保数据表"""
        try:
            use_sheet = sheet_name or self.current_sheet_name
            
            if not use_sheet:
                mode, results, summary = self.detect_sheets(file_path)
                
                if mode == 'none':
                    raise ValueError("未找到包含完整社保数据（养老、医疗、失业、公积金）的Sheet")
                
                # 自动处理的情况
                if mode in ['auto_perfect', 'auto_partial']:
                    best = results[0]
                    use_sheet = best.sheet_name
                    self.current_field_mapping = best.matched_fields
                    self.current_match_type = best.match_type
                else:
                    # 需要用户选择的情况
                    raise ValueError(f"发现多个社保数据Sheet，需要用户选择")
            
            # 读取数据
            df = pd.read_excel(
                file_path,
                sheet_name=use_sheet,
                dtype={"身份证号": str, "手机号码": str, "银行卡号": str},
            )

            # 重命名列
            df = self._rename_columns(df)

            # 身份证号清洗
            df[self.COL_ID] = df[self.COL_ID].astype(str).str.strip().str.upper()
            df[self.COL_ID] = df[self.COL_ID].str.replace(r"\.0$", "", regex=True)
            df[self.COL_ID] = df[self.COL_ID].replace("NAN", "")

            # 只保留需要的列
            available_columns = [c for c in self.TARGET_COLUMNS if c in df.columns]
            result = df[available_columns].copy()

            # 删除空行
            result = result.dropna(subset=[self.COL_ID])
            
            # 填充缺失的数值列为0
            numeric_columns = [self.COL_PENSION, self.COL_MEDICAL, self.COL_UNEMPLOYMENT, self.COL_HOUSING]
            for col in numeric_columns:
                if col in result.columns:
                    result[col] = result[col].fillna(0)

            self._validate(result)
            return result

        except Exception as e:
            error_info = handle_error(e, {'path': file_path})
            raise ValueError(f"读取社保数据表失败: {error_info.message}")

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """根据字段映射重命名列"""
        rename_map = {}
        
        standard_names = {
            '养老': self.COL_PENSION,
            '医疗': self.COL_MEDICAL,
            '失业': self.COL_UNEMPLOYMENT,
            '公积金': self.COL_HOUSING,
        }
        
        for target_name, actual_name in self.current_field_mapping.items():
            if actual_name and actual_name in df.columns:
                standard_name = standard_names.get(target_name)
                if standard_name:
                    rename_map[actual_name] = standard_name
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        return df

    def _validate(self, df: pd.DataFrame):
        """校验必要列"""
        if len(df) == 0:
            raise ValueError("社保数据表中没有有效数据")

        required = [self.COL_ID, self.COL_NAME]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"社保数据表缺少必要列：{missing}")

    def get_social_security_data(self, df: pd.DataFrame) -> Dict:
        """将数据转换为以身份证号为 key 的字典"""
        numeric_columns = [self.COL_PENSION, self.COL_MEDICAL, self.COL_UNEMPLOYMENT, self.COL_HOUSING]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df.set_index(self.COL_ID).to_dict(orient="index")


# 便捷函数
def load_social_security_v3(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """便捷函数：读取社保数据表 V3"""
    loader = SocialSecurityLoaderV3()
    return loader.load(file_path, sheet_name)

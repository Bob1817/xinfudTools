"""
社保数据表读取器（优化版）
支持多Sheet自动识别和字段智能匹配
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from core.sheet_detector import SheetDetector, SheetMatchResult, FieldMapper
from core.error_handler import handle_error, ErrorInfo


class SocialSecurityLoader:
    """社保数据表读取器（优化版）"""

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
        self.sheet_detector = SheetDetector()
        self.field_mapper = FieldMapper()
        self.current_field_mapping: Dict[str, str] = {}
        self.current_sheet_name: Optional[str] = None

    def detect_sheets(self, file_path: str) -> Tuple[bool, List[SheetMatchResult], str]:
        """
        检测文件中的社保数据Sheet
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            (是否需要用户选择, 匹配结果列表, 摘要信息)
        """
        try:
            results = self.sheet_detector.detect_social_security_sheets(file_path)
            
            if not results:
                return False, [], "未找到包含社保数据的Sheet"
            
            # 检查是否需要用户选择
            perfect_matches = [r for r in results if r.is_perfect_match]
            
            if len(perfect_matches) == 1:
                # 只有一个完全匹配，自动选择
                self.current_sheet_name = perfect_matches[0].sheet_name
                self.current_field_mapping = perfect_matches[0].matched_fields
                return False, results, self.sheet_detector.get_match_summary()
            
            # 需要用户选择
            return True, results, self.sheet_detector.get_match_summary()
            
        except Exception as e:
            error_info = handle_error(e, {'path': file_path})
            raise ValueError(f"检测Sheet失败: {error_info.message}")

    def select_sheet(self, sheet_name: str, field_mapping: Optional[Dict[str, str]] = None):
        """
        选择要使用的Sheet和字段映射
        
        Args:
            sheet_name: Sheet名称
            field_mapping: 字段映射（如果不提供则使用自动检测的映射）
        """
        self.current_sheet_name = sheet_name
        
        if field_mapping:
            self.current_field_mapping = field_mapping
        else:
            # 从检测结果中查找映射
            for result in self.sheet_detector.match_results:
                if result.sheet_name == sheet_name:
                    self.current_field_mapping = result.matched_fields
                    break

    def load(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        读取社保数据表
        
        Args:
            file_path: Excel文件路径
            sheet_name: Sheet名称，None则使用当前选中的Sheet
            
        Returns:
            DataFrame
            
        Raises:
            ValueError: 读取失败
        """
        try:
            # 确定使用的Sheet
            use_sheet = sheet_name or self.current_sheet_name
            
            if not use_sheet:
                # 自动检测Sheet
                need_select, results, summary = self.detect_sheets(file_path)
                
                if need_select:
                    raise ValueError(
                        f"发现多个社保数据Sheet，需要用户选择:\n{summary}"
                    )
                
                if not results:
                    raise ValueError("未找到包含社保数据的Sheet")
                
                # 自动选择第一个（应该是完全匹配的）
                use_sheet = results[0].sheet_name
                self.current_field_mapping = results[0].matched_fields
            
            # 读取数据
            df = pd.read_excel(
                file_path,
                sheet_name=use_sheet,
                dtype={
                    "身份证号": str,
                    "手机号码": str,
                    "银行卡号": str,
                },
            )

            # 如果没有字段映射，尝试自动检测
            if not self.current_field_mapping:
                suggestions = self.field_mapper.suggest_field_mapping(df.columns.tolist())
                is_valid, missing = self.field_mapper.validate_mapping(suggestions)
                
                if not is_valid:
                    raise ValueError(
                        f"无法自动识别以下字段: {', '.join(missing)}\n"
                        f"请手动指定字段映射。"
                    )
                
                self.current_field_mapping = suggestions

            # 重命名列（使用标准列名）
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
        """
        根据字段映射重命名列
        
        Args:
            df: 原始DataFrame
            
        Returns:
            重命名后的DataFrame
        """
        rename_map = {}
        
        for standard_name, actual_name in self.current_field_mapping.items():
            if actual_name and actual_name in df.columns:
                rename_map[actual_name] = standard_name
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        return df

    def _validate(self, df: pd.DataFrame):
        """校验必要列"""
        if len(df) == 0:
            raise ValueError("社保数据表中没有有效数据")

        # 检查必要列（至少要有身份证号和姓名）
        required = [self.COL_ID, self.COL_NAME]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"社保数据表缺少必要列：{missing}")

    def get_social_security_data(self, df: pd.DataFrame) -> Dict:
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
        # 确保数值列为数值类型
        numeric_columns = [self.COL_PENSION, self.COL_MEDICAL, self.COL_UNEMPLOYMENT, self.COL_HOUSING]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df.set_index(self.COL_ID).to_dict(orient="index")

    def get_sheet_info(self, file_path: str) -> Dict:
        """
        获取文件中的Sheet信息
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Sheet信息字典
        """
        try:
            xl_file = pd.ExcelFile(file_path)
            return {
                'file_name': Path(file_path).name,
                'sheet_count': len(xl_file.sheet_names),
                'sheet_names': xl_file.sheet_names,
                'file_path': file_path
            }
        except Exception as e:
            error_info = handle_error(e, {'path': file_path})
            raise ValueError(f"无法读取文件: {error_info.message}")

    def validate_field_mapping(self, mapping: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        验证字段映射
        
        Args:
            mapping: 字段映射字典
            
        Returns:
            (是否有效, 缺失字段列表)
        """
        return self.field_mapper.validate_mapping(mapping)

    def suggest_field_mapping(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """
        建议字段映射
        
        Args:
            columns: 列名列表
            
        Returns:
            建议的字段映射
        """
        return self.field_mapper.suggest_field_mapping(columns)


# 便捷函数
def load_social_security(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    便捷函数：读取社保数据表
    
    Args:
        file_path: Excel文件路径
        sheet_name: Sheet名称
        
    Returns:
        DataFrame
    """
    loader = SocialSecurityLoader()
    return loader.load(file_path, sheet_name)


def detect_social_security_sheets(file_path: str) -> Tuple[bool, List[SheetMatchResult], str]:
    """
    便捷函数：检测社保数据Sheet
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        (是否需要用户选择, 匹配结果列表, 摘要信息)
    """
    loader = SocialSecurityLoader()
    return loader.detect_sheets(file_path)

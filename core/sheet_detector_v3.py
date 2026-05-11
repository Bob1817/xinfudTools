"""
Sheet识别器模块 V3
根据用户要求实现精确的字段匹配逻辑

匹配规则：
1. 完全匹配：字段名完全等于【基本养老保险费】【基本医疗保险费】【失业保险费】【住房公积金】
2. 部分匹配：包含【养老】【医疗】【失业】【公积金】关键字
3. 必须四个字段都存在
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class SheetMatchResult:
    """Sheet匹配结果"""
    sheet_name: str
    match_type: str  # 'perfect' 完全匹配, 'partial' 部分匹配
    match_score: float
    matched_fields: Dict[str, str]  # 目标字段 -> 实际字段名
    row_count: int
    sample_data: pd.DataFrame


class SheetDetectorV3:
    """Sheet识别器 V3"""
    
    # 完全匹配字段名
    PERFECT_MATCH_FIELDS = {
        '养老': ['基本养老保险费'],
        '医疗': ['基本医疗保险费'],
        '失业': ['失业保险费'],
        '公积金': ['住房公积金'],
    }
    
    # 部分匹配关键字
    PARTIAL_MATCH_KEYWORDS = {
        '养老': ['养老'],
        '医疗': ['医疗'],
        '失业': ['失业'],
        '公积金': ['公积金'],
    }
    
    def __init__(self):
        self.match_results: List[SheetMatchResult] = []
    
    def detect_social_security_sheets(self, file_path: str) -> List[SheetMatchResult]:
        """
        检测Excel文件中所有Sheet
        
        规则：
        1. 先检查是否完全匹配（字段名完全等于标准名）
        2. 再检查是否部分匹配（包含关键字）
        3. 必须四个字段都存在
        """
        self.match_results = []
        
        try:
            xl_file = pd.ExcelFile(file_path)
            sheet_names = xl_file.sheet_names
            
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
                    
                    if df.empty:
                        continue
                    
                    # 先尝试完全匹配
                    result = self._check_perfect_match(sheet_name, df)
                    
                    if result:
                        self.match_results.append(result)
                    else:
                        # 尝试部分匹配
                        result = self._check_partial_match(sheet_name, df)
                        if result:
                            self.match_results.append(result)
                        
                except Exception as e:
                    continue
            
            # 按匹配类型和匹配度排序（完全匹配优先）
            self.match_results.sort(key=lambda x: (0 if x.match_type == 'perfect' else 1, -x.match_score))
            
            return self.match_results
            
        except Exception as e:
            raise ValueError(f"无法读取文件 {file_path}: {str(e)}")
    
    def _check_perfect_match(self, sheet_name: str, df: pd.DataFrame) -> Optional[SheetMatchResult]:
        """
        检查是否完全匹配
        
        完全匹配标准：
        - 字段名完全等于【基本养老保险费】【基本医疗保险费】【失业保险费】【住房公积金】
        """
        columns = [str(col).strip() for col in df.columns.tolist()]
        
        matched_fields = {}
        
        for field_key, perfect_names in self.PERFECT_MATCH_FIELDS.items():
            found = False
            for col in columns:
                if col in perfect_names:
                    matched_fields[field_key] = col
                    found = True
                    break
            
            if not found:
                # 缺少必要字段，不是完全匹配
                return None
        
        # 四个字段都完全匹配
        return SheetMatchResult(
            sheet_name=sheet_name,
            match_type='perfect',
            match_score=1.0,
            matched_fields=matched_fields,
            row_count=len(df),
            sample_data=df.head(5)
        )
    
    def _check_partial_match(self, sheet_name: str, df: pd.DataFrame) -> Optional[SheetMatchResult]:
        """
        检查是否部分匹配
        
        部分匹配标准：
        - 字段名包含【养老】【医疗】【失业】【公积金】关键字
        """
        columns = [str(col).strip() for col in df.columns.tolist()]
        
        matched_fields = {}
        
        for field_key, keywords in self.PARTIAL_MATCH_KEYWORDS.items():
            found = False
            for col in columns:
                for keyword in keywords:
                    if keyword in col:
                        matched_fields[field_key] = col
                        found = True
                        break
                if found:
                    break
            
            if not found:
                # 缺少必要字段
                return None
        
        # 计算匹配度
        score = len(matched_fields) / 4.0
        
        return SheetMatchResult(
            sheet_name=sheet_name,
            match_type='partial',
            match_score=score,
            matched_fields=matched_fields,
            row_count=len(df),
            sample_data=df.head(5)
        )
    
    def get_match_summary(self) -> str:
        """获取匹配摘要信息"""
        if not self.match_results:
            return "未找到包含社保数据（养老、医疗、失业、公积金）的Sheet"
        
        lines = [
            f"📊 社保数据Sheet识别结果",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"找到 {len(self.match_results)} 个候选Sheet：",
            f""
        ]
        
        for i, result in enumerate(self.match_results, 1):
            if result.match_type == 'perfect':
                status = "✅ 完全匹配"
            else:
                status = "⚠️ 部分匹配"
            
            lines.append(f"{i}. {status} {result.sheet_name}")
            lines.append(f"   匹配度: {result.match_score:.0%}")
            lines.append(f"   字段映射:")
            
            for target, actual in result.matched_fields.items():
                lines.append(f"     {target} → {actual}")
            
            lines.append(f"")
        
        return '\n'.join(lines)


# 便捷函数
def detect_social_security_sheets_v3(file_path: str) -> Tuple[str, List[SheetMatchResult], str]:
    """
    检测社保数据Sheet V3
    
    Returns:
        (处理模式, 匹配结果列表, 摘要信息)
        处理模式: 'auto_perfect' 自动完全匹配, 
                'select_perfect' 选择完全匹配,
                'auto_partial' 自动部分匹配,
                'select_partial' 选择部分匹配,
                'none' 未找到
    """
    detector = SheetDetectorV3()
    results = detector.detect_social_security_sheets(file_path)
    
    if not results:
        return 'none', [], "未找到包含社保数据（养老、医疗、失业、公积金）的Sheet"
    
    # 分离完全匹配和部分匹配
    perfect_matches = [r for r in results if r.match_type == 'perfect']
    partial_matches = [r for r in results if r.match_type == 'partial']
    
    # 判断处理模式
    if len(perfect_matches) == 1:
        return 'auto_perfect', results, detector.get_match_summary()
    elif len(perfect_matches) > 1:
        return 'select_perfect', results, detector.get_match_summary()
    elif len(partial_matches) == 1:
        return 'auto_partial', results, detector.get_match_summary()
    elif len(partial_matches) > 1:
        return 'select_partial', results, detector.get_match_summary()
    else:
        return 'none', [], detector.get_match_summary()

"""
Sheet识别器模块 V2
修复版：正确处理社保数据表字段匹配逻辑

关键规则：
1. 必须包含【养老】【医疗】【失业】【公积金】四个字段
2. 支持模糊匹配：养老、养老保险、个人养老、养老保险费等
3. 完全匹配：四个字段都存在且匹配度高
4. 部分匹配：四个字段都存在但匹配度不够高
5. 不匹配：缺少任一字段
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class SheetMatchResult:
    """Sheet匹配结果"""
    sheet_name: str
    match_score: float  # 0-1的匹配度
    matched_fields: Dict[str, str]  # 目标字段 -> 实际字段名
    missing_fields: List[str]  # 缺失的目标字段
    unmatched_fields: List[str]  # 存在但不完全匹配的字段
    is_perfect_match: bool  # 是否完全匹配（四个字段都存在且匹配度高）
    is_partial_match: bool  # 是否部分匹配（四个字段都存在但匹配度不够）
    row_count: int
    sample_data: pd.DataFrame  # 前5行数据用于预览


class SheetDetectorV2:
    """Sheet识别器 V2：修复字段匹配逻辑"""
    
    # 目标字段（必须四个都存在）
    TARGET_FIELDS = {
        '养老': ['养老', '养老保险', '养老保险费', '基本养老', '基本养老保险', '个人养老', '个人养老保险', '个人养老保险费'],
        '医疗': ['医疗', '医疗保险', '医疗保险费', '基本医疗', '基本医疗保险', '个人医疗', '个人医疗保险', '个人医疗保险费'],
        '失业': ['失业', '失业保险', '失业保险费', '个人失业', '个人失业保险', '个人失业保险费'],
        '公积金': ['公积金', '住房公积金', '个人公积金', '个人住房公积金', '公积金费', '住房公积金费'],
    }
    
    # 完全匹配阈值（所有字段匹配度都超过此值）
    PERFECT_MATCH_THRESHOLD = 0.8
    
    def __init__(self):
        self.match_results: List[SheetMatchResult] = []
    
    def detect_social_security_sheets(self, file_path: str) -> List[SheetMatchResult]:
        """
        检测Excel文件中所有Sheet，返回包含社保数据的Sheet列表
        
        规则：
        1. 必须包含【养老】【医疗】【失业】【公积金】四个字段
        2. 四个字段都存在 → 完全匹配或部分匹配
        3. 缺少任一字段 → 不匹配
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Sheet匹配结果列表（按匹配度降序排列）
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
                    
                    result = self._analyze_sheet(sheet_name, df)
                    
                    # 只保留四个字段都存在的Sheet
                    if len(result.matched_fields) == 4:
                        self.match_results.append(result)
                        
                except Exception as e:
                    continue
            
            # 按匹配度降序排列
            self.match_results.sort(key=lambda x: x.match_score, reverse=True)
            
            return self.match_results
            
        except Exception as e:
            raise ValueError(f"无法读取文件 {file_path}: {str(e)}")
    
    def _analyze_sheet(self, sheet_name: str, df: pd.DataFrame) -> SheetMatchResult:
        """
        分析单个Sheet
        
        Args:
            sheet_name: Sheet名称
            df: Sheet数据
            
        Returns:
            Sheet匹配结果
        """
        columns = df.columns.tolist()
        column_strs = [str(col).strip() for col in columns]
        
        matched_fields = {}  # 成功匹配的字段
        unmatched_fields = []  # 存在但匹配度不高的字段
        
        # 检查每个目标字段
        for field_key, field_variants in self.TARGET_FIELDS.items():
            best_match = None
            best_score = 0.0
            
            for column in column_strs:
                for variant in field_variants:
                    score = self._calculate_similarity(column, variant)
                    if score > best_score:
                        best_score = score
                        best_match = column
            
            if best_match and best_score > 0.6:  # 匹配度阈值
                matched_fields[field_key] = best_match
                if best_score < self.PERFECT_MATCH_THRESHOLD:
                    unmatched_fields.append(field_key)
        
        # 计算整体匹配度
        if len(matched_fields) == 4:
            # 四个字段都匹配，计算平均匹配度
            total_score = 0.0
            for field_key, matched_col in matched_fields.items():
                # 重新计算每个字段的匹配度
                best_score = 0.0
                for variant in self.TARGET_FIELDS[field_key]:
                    score = self._calculate_similarity(matched_col, variant)
                    if score > best_score:
                        best_score = score
                total_score += best_score
            
            match_score = total_score / 4
        else:
            match_score = 0.0
        
        # 判断是否完全匹配
        is_perfect_match = (
            len(matched_fields) == 4 and 
            len(unmatched_fields) == 0 and
            match_score >= self.PERFECT_MATCH_THRESHOLD
        )
        
        # 判断是否部分匹配
        is_partial_match = (
            len(matched_fields) == 4 and 
            len(unmatched_fields) > 0
        )
        
        return SheetMatchResult(
            sheet_name=sheet_name,
            match_score=match_score,
            matched_fields=matched_fields,
            missing_fields=[],  # 四个字段都存在，没有缺失
            unmatched_fields=unmatched_fields,
            is_perfect_match=is_perfect_match,
            is_partial_match=is_partial_match,
            row_count=len(df),
            sample_data=df.head(5)
        )
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度"""
        s1 = s1.lower().replace(' ', '').replace('_', '').replace('-', '')
        s2 = s2.lower().replace(' ', '').replace('_', '').replace('-', '')
        
        # 完全包含
        if s2 in s1 or s1 in s2:
            return 1.0
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def get_match_summary(self) -> str:
        """获取匹配摘要信息"""
        if not self.match_results:
            return "未找到包含完整社保数据（养老、医疗、失业、公积金）的Sheet"
        
        lines = [
            f"📊 社保数据Sheet识别结果",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"找到 {len(self.match_results)} 个候选Sheet（都包含四个必要字段）：",
            f""
        ]
        
        for i, result in enumerate(self.match_results, 1):
            if result.is_perfect_match:
                status = "✅ 完全匹配"
            elif result.is_partial_match:
                status = "⚠️ 部分匹配"
            else:
                status = "❓ 匹配度低"
            
            lines.append(f"{i}. {status} {result.sheet_name}")
            lines.append(f"   匹配度: {result.match_score:.1%}")
            lines.append(f"   字段映射:")
            
            for target, actual in result.matched_fields.items():
                if target in result.unmatched_fields:
                    lines.append(f"     ⚠️ {target} → {actual} (不完全匹配)")
                else:
                    lines.append(f"     ✅ {target} → {actual}")
            
            lines.append(f"")
        
        return '\n'.join(lines)


class FieldMapperV2:
    """字段映射器 V2"""
    
    TARGET_FIELDS = SheetDetectorV2.TARGET_FIELDS
    
    def suggest_field_mapping(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """建议字段映射"""
        suggestions = {}
        
        for target_key, variants in self.TARGET_FIELDS.items():
            best_match = None
            best_score = 0.0
            
            for column in columns:
                column_str = str(column).strip()
                for variant in variants:
                    score = self._calculate_similarity(column_str, variant)
                    if score > best_score and score > 0.6:
                        best_score = score
                        best_match = column_str
            
            suggestions[target_key] = best_match
        
        return suggestions
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度"""
        s1 = s1.lower().replace(' ', '').replace('_', '').replace('-', '')
        s2 = s2.lower().replace(' ', '').replace('_', '').replace('-', '')
        
        if s2 in s1 or s1 in s2:
            return 1.0
        
        return SequenceMatcher(None, s1, s2).ratio()


# 便捷函数
def detect_social_security_sheets_v2(file_path: str) -> Tuple[bool, List[SheetMatchResult], str]:
    """
    检测社保数据Sheet V2
    
    Returns:
        (是否需要用户选择, 匹配结果列表, 摘要信息)
    """
    detector = SheetDetectorV2()
    results = detector.detect_social_security_sheets(file_path)
    
    if not results:
        return False, [], "未找到包含完整社保数据（养老、医疗、失业、公积金）的Sheet"
    
    # 检查是否需要用户选择
    perfect_matches = [r for r in results if r.is_perfect_match]
    
    if len(perfect_matches) == 1:
        # 只有一个完全匹配，不需要选择
        return False, results, detector.get_match_summary()
    
    # 需要用户选择
    return True, results, detector.get_match_summary()

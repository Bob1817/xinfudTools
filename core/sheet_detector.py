"""
Sheet识别器模块
自动识别Excel文件中包含社保数据的Sheet
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import re


@dataclass
class SheetMatchResult:
    """Sheet匹配结果"""
    sheet_name: str
    match_score: float  # 0-1的匹配度
    matched_fields: Dict[str, str]  # 目标字段 -> 实际字段名
    missing_fields: List[str]  # 缺失的目标字段
    is_perfect_match: bool
    row_count: int
    sample_data: pd.DataFrame  # 前5行数据用于预览


class SheetDetector:
    """Sheet识别器：自动识别包含社保数据的Sheet"""
    
    # 目标字段（用于识别社保表）
    TARGET_FIELDS = {
        '养老': ['养老', '养老保险', '养老保险费', '基本养老', '基本养老保险', '个人养老'],
        '医疗': ['医疗', '医疗保险', '医疗保险费', '基本医疗', '基本医疗保险', '个人医疗'],
        '失业': ['失业', '失业保险', '失业保险费', '个人失业'],
        '公积金': ['公积金', '住房公积金', '个人公积金', '公积金费'],
    }
    
    # 关键字段（必须至少有一个）
    KEY_FIELDS = ['养老', '医疗', '失业', '公积金']
    
    # 完全匹配的阈值
    PERFECT_MATCH_THRESHOLD = 0.9
    
    def __init__(self):
        self.match_results: List[SheetMatchResult] = []
    
    def detect_social_security_sheets(self, file_path: str) -> List[SheetMatchResult]:
        """
        检测Excel文件中所有Sheet，返回包含社保数据的Sheet列表
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Sheet匹配结果列表（按匹配度降序排列）
        """
        self.match_results = []
        
        try:
            # 获取所有Sheet名称
            xl_file = pd.ExcelFile(file_path)
            sheet_names = xl_file.sheet_names
            
            for sheet_name in sheet_names:
                try:
                    # 读取Sheet（最多读取10行用于检测）
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
                    
                    if df.empty:
                        continue
                    
                    # 分析Sheet
                    result = self._analyze_sheet(sheet_name, df)
                    
                    # 只保留包含关键字段的Sheet
                    if result.match_score > 0:
                        self.match_results.append(result)
                        
                except Exception as e:
                    # 读取失败，跳过
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
        
        matched_fields = {}
        missing_fields = []
        total_score = 0.0
        
        # 检查每个目标字段
        for field_key, field_variants in self.TARGET_FIELDS.items():
            best_match = None
            best_score = 0.0
            
            for column in column_strs:
                for variant in field_variants:
                    score = self._calculate_similarity(column, variant)
                    if score > best_score and score > 0.6:  # 相似度阈值
                        best_score = score
                        best_match = column
            
            if best_match:
                matched_fields[field_key] = best_match
                total_score += best_score
            else:
                missing_fields.append(field_key)
        
        # 计算整体匹配度
        if len(self.TARGET_FIELDS) > 0:
            match_score = total_score / len(self.TARGET_FIELDS)
        else:
            match_score = 0.0
        
        # 如果没有匹配到任何关键字段，匹配度设为0
        if not matched_fields:
            match_score = 0.0
        
        # 是否完全匹配（所有关键字段都存在且相似度高）
        is_perfect_match = (
            len(matched_fields) == len(self.TARGET_FIELDS) and
            match_score >= self.PERFECT_MATCH_THRESHOLD
        )
        
        return SheetMatchResult(
            sheet_name=sheet_name,
            match_score=match_score,
            matched_fields=matched_fields,
            missing_fields=missing_fields,
            is_perfect_match=is_perfect_match,
            row_count=len(df),
            sample_data=df.head(5)
        )
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            s1: 字符串1
            s2: 字符串2
            
        Returns:
            相似度 (0-1)
        """
        # 预处理
        s1 = s1.lower().replace(' ', '').replace('_', '').replace('-', '')
        s2 = s2.lower().replace(' ', '').replace('_', '').replace('-', '')
        
        # 完全包含
        if s2 in s1 or s1 in s2:
            return 1.0
        
        # 使用SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()
    
    def get_best_sheet(self) -> Optional[SheetMatchResult]:
        """
        获取最佳匹配的Sheet
        
        Returns:
            最佳匹配的Sheet，如果没有则返回None
        """
        if not self.match_results:
            return None
        return self.match_results[0]
    
    def has_perfect_match(self) -> bool:
        """
        检查是否有完全匹配的Sheet
        
        Returns:
            是否有完全匹配的Sheet
        """
        return any(r.is_perfect_match for r in self.match_results)
    
    def get_perfect_matches(self) -> List[SheetMatchResult]:
        """
        获取所有完全匹配的Sheet
        
        Returns:
            完全匹配的Sheet列表
        """
        return [r for r in self.match_results if r.is_perfect_match]
    
    def get_match_summary(self) -> str:
        """
        获取匹配摘要信息
        
        Returns:
            摘要文本
        """
        if not self.match_results:
            return "未找到包含社保数据的Sheet"
        
        lines = [
            f"📊 社保数据Sheet识别结果",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"找到 {len(self.match_results)} 个候选Sheet：",
            f""
        ]
        
        for i, result in enumerate(self.match_results, 1):
            status = "✅" if result.is_perfect_match else "⚠️"
            lines.append(f"{i}. {status} {result.sheet_name}")
            lines.append(f"   匹配度: {result.match_score:.1%}")
            lines.append(f"   匹配字段: {len(result.matched_fields)}/4")
            
            if result.matched_fields:
                field_str = ", ".join([f"{k}→{v}" for k, v in result.matched_fields.items()])
                lines.append(f"   字段映射: {field_str}")
            
            if result.missing_fields:
                lines.append(f"   缺失字段: {', '.join(result.missing_fields)}")
            
            lines.append(f"")
        
        return '\n'.join(lines)
    
    def get_sheet_for_user_selection(self) -> List[Dict]:
        """
        获取用于用户选择的Sheet列表
        
        Returns:
            包含详细信息的字典列表
        """
        result = []
        for match in self.match_results:
            result.append({
                'sheet_name': match.sheet_name,
                'match_score': match.match_score,
                'is_perfect_match': match.is_perfect_match,
                'matched_fields': match.matched_fields,
                'missing_fields': match.missing_fields,
                'row_count': match.row_count,
                'display_text': f"{match.sheet_name} (匹配度: {match.match_score:.0%})"
            })
        return result


class FieldMapper:
    """字段映射器：处理字段名不完全匹配的情况"""
    
    def __init__(self, target_fields: Dict[str, List[str]] = None):
        self.target_fields = target_fields or SheetDetector.TARGET_FIELDS
    
    def suggest_field_mapping(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """
        建议字段映射
        
        Args:
            columns: 实际列名列表
            
        Returns:
            目标字段 -> 建议的实际字段名（None表示未找到）
        """
        suggestions = {}
        
        for target_key, variants in self.target_fields.items():
            best_match = None
            best_score = 0.0
            
            for column in columns:
                column_str = str(column).strip()
                for variant in variants:
                    score = self._calculate_similarity(column_str, variant)
                    if score > best_score and score > 0.5:
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
    
    def validate_mapping(self, mapping: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        验证字段映射
        
        Args:
            mapping: 字段映射字典
            
        Returns:
            (是否有效, 缺失字段列表)
        """
        missing = []
        for key in self.target_fields.keys():
            if not mapping.get(key):
                missing.append(key)
        
        return len(missing) == 0, missing


# 便捷函数
def detect_social_security_sheets(file_path: str) -> List[SheetMatchResult]:
    """
    便捷函数：检测社保数据Sheet
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        Sheet匹配结果列表
    """
    detector = SheetDetector()
    return detector.detect_social_security_sheets(file_path)


def get_sheet_selection_info(file_path: str) -> Tuple[bool, List[SheetMatchResult], str]:
    """
    获取Sheet选择信息
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        (是否需要用户选择, 匹配结果列表, 摘要信息)
    """
    detector = SheetDetector()
    results = detector.detect_social_security_sheets(file_path)
    
    if not results:
        return False, [], "未找到包含社保数据的Sheet"
    
    # 检查是否需要用户选择
    perfect_matches = detector.get_perfect_matches()
    
    if len(perfect_matches) == 1:
        # 只有一个完全匹配，不需要选择
        return False, results, detector.get_match_summary()
    elif len(perfect_matches) > 1:
        # 多个完全匹配，需要用户选择
        return True, results, detector.get_match_summary()
    else:
        # 没有完全匹配，需要用户确认
        return True, results, detector.get_match_summary()

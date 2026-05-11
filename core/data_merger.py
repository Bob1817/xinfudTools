"""
数据合并器模块
处理同一身份证号的多条数据合并逻辑
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class MergeWarning:
    """合并警告信息"""
    id_card: str
    field: str
    values: List[str]
    message: str


class DataMerger:
    """数据合并器：处理同一身份证号的多条数据合并"""
    
    # 数值型字段（需要累加）- 支持多种可能的字段名
    NUMERIC_FIELDS = [
        '应发金额', '个税', '个人养老', '个人医疗', '个人失业', 
        '个人公积金', '通讯费', '实发金额',
        '养老', '医疗', '失业', '公积金',  # 简化字段名
        '基本养老保险费', '基本医疗保险费', '失业保险费', '住房公积金'  # 申报表字段名
    ]
    
    # 文本型字段（取第一条）
    TEXT_FIELDS = [
        '姓名', '手机号码', '银行卡号', '银行名称', '备注'
    ]
    
    def __init__(self):
        self.warnings: List[MergeWarning] = []
    
    def merge_by_id_card(self, df: pd.DataFrame, id_card_col: str = '身份证号') -> Tuple[pd.DataFrame, List[MergeWarning]]:
        """
        按身份证号合并数据
        
        Args:
            df: 输入DataFrame
            id_card_col: 身份证号列名
            
        Returns:
            (合并后的DataFrame, 警告信息列表)
        """
        self.warnings = []
        
        if df.empty:
            return df.copy(), []
        
        # 清洗身份证号
        df = df.copy()
        df[id_card_col] = df[id_card_col].astype(str).str.strip().str.upper()
        df[id_card_col] = df[id_card_col].str.replace(r'\.0$', '', regex=True)
        
        # 按身份证号分组
        grouped = df.groupby(id_card_col, sort=False)
        
        # 存储合并后的数据
        merged_rows = []
        
        for id_card, group in grouped:
            if len(group) == 1:
                # 只有一条数据，直接保留
                merged_rows.append(group.iloc[0].to_dict())
            else:
                # 多条数据，需要合并
                merged_row = self._merge_group(group, id_card)
                merged_rows.append(merged_row)
        
        # 创建新的DataFrame
        result = pd.DataFrame(merged_rows)
        
        # 保持原始列顺序
        result = result[df.columns]
        
        return result, self.warnings
    
    def _merge_group(self, group: pd.DataFrame, id_card: str) -> Dict:
        """
        合并同一身份证号的多条数据
        
        Args:
            group: 同一身份证号的数据组
            id_card: 身份证号
            
        Returns:
            合并后的行数据
        """
        merged = {}
        
        for column in group.columns:
            values = group[column].tolist()
            
            # 检查数据一致性
            self._check_consistency(id_card, column, values)
            
            if column in self.NUMERIC_FIELDS:
                # 数值型字段：累加
                merged[column] = self._sum_numeric(values)
            elif column in self.TEXT_FIELDS:
                # 文本型字段：取第一条非空值
                merged[column] = self._get_first_non_empty(values)
            else:
                # 其他字段：取第一条
                merged[column] = values[0]
        
        return merged
    
    def _sum_numeric(self, values: List) -> float:
        """
        累加数值，处理空值和非数值
        
        Args:
            values: 数值列表
            
        Returns:
            累加结果
        """
        total = 0.0
        for v in values:
            if pd.notna(v) and v != '' and v is not None:
                try:
                    total += float(v)
                except (ValueError, TypeError):
                    pass
        return total
    
    def _get_first_non_empty(self, values: List) -> str:
        """
        获取第一个非空值
        
        Args:
            values: 值列表
            
        Returns:
            第一个非空值，如果没有则返回空字符串
        """
        for v in values:
            if pd.notna(v) and str(v).strip() and str(v).upper() != 'NAN':
                return str(v).strip()
        return ''
    
    def _check_consistency(self, id_card: str, field: str, values: List):
        """
        检查数据一致性，记录警告
        
        Args:
            id_card: 身份证号
            field: 字段名
            values: 值列表
        """
        if len(values) <= 1:
            return
        
        # 检查文本字段的一致性
        if field in self.TEXT_FIELDS:
            non_empty_values = []
            for v in values:
                if pd.notna(v) and str(v).strip() and str(v).upper() != 'NAN':
                    non_empty_values.append(str(v).strip())
            
            # 如果有多个不同的非空值
            unique_values = list(set(non_empty_values))
            if len(unique_values) > 1:
                warning = MergeWarning(
                    id_card=id_card,
                    field=field,
                    values=unique_values,
                    message=f"身份证号 {id_card} 的 '{field}' 字段存在多个不同值: {unique_values}，已使用第一个值: {unique_values[0]}"
                )
                self.warnings.append(warning)
    
    def validate_data_consistency(self, df: pd.DataFrame, id_card_col: str = '身份证号') -> Dict:
        """
        验证数据一致性，返回统计信息
        
        Args:
            df: 输入DataFrame
            id_card_col: 身份证号列名
            
        Returns:
            统计信息字典
        """
        if df.empty:
            return {
                'total_rows': 0,
                'unique_ids': 0,
                'duplicate_ids': 0,
                'max_duplicates': 0,
                'warnings': []
            }
        
        # 清洗身份证号
        df_clean = df.copy()
        df_clean[id_card_col] = df_clean[id_card_col].astype(str).str.strip().str.upper()
        
        # 统计
        total_rows = len(df_clean)
        id_counts = df_clean[id_card_col].value_counts()
        unique_ids = len(id_counts)
        duplicate_ids = len(id_counts[id_counts > 1])
        max_duplicates = id_counts.max() if len(id_counts) > 0 else 0
        
        # 生成警告
        warnings = []
        for id_card, count in id_counts[id_counts > 1].items():
            group = df_clean[df_clean[id_card_col] == id_card]
            
            # 检查每个文本字段
            for field in self.TEXT_FIELDS:
                if field in group.columns:
                    values = group[field].dropna().astype(str).tolist()
                    unique_vals = list(set([v.strip() for v in values if v.strip() and v.upper() != 'NAN']))
                    
                    if len(unique_vals) > 1:
                        warnings.append({
                            'id_card': id_card,
                            'field': field,
                            'values': unique_vals,
                            'count': count
                        })
        
        return {
            'total_rows': total_rows,
            'unique_ids': unique_ids,
            'duplicate_ids': duplicate_ids,
            'max_duplicates': int(max_duplicates),
            'warnings': warnings
        }
    
    def get_merge_preview(self, df: pd.DataFrame, id_card_col: str = '身份证号') -> str:
        """
        获取合并预览信息
        
        Args:
            df: 输入DataFrame
            id_card_col: 身份证号列名
            
        Returns:
            预览文本
        """
        stats = self.validate_data_consistency(df, id_card_col)
        
        lines = [
            f"📊 数据合并预览",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"总数据条数: {stats['total_rows']}",
            f"唯一身份证号: {stats['unique_ids']}",
            f"重复身份证号: {stats['duplicate_ids']}",
        ]
        
        if stats['duplicate_ids'] > 0:
            lines.append(f"最大重复数: {stats['max_duplicates']} 条")
            lines.append(f"")
            lines.append(f"⚠️ 发现 {len(stats['warnings'])} 处数据不一致:")
            
            for i, warning in enumerate(stats['warnings'][:5], 1):  # 最多显示5条
                lines.append(f"  {i}. 身份证号 {warning['id_card']}: {warning['field']} 字段有 {len(warning['values'])} 个不同值")
            
            if len(stats['warnings']) > 5:
                lines.append(f"  ... 还有 {len(stats['warnings']) - 5} 处")
        
        lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"✅ 合并后将生成 {stats['unique_ids']} 条记录")
        
        return '\n'.join(lines)


# 便捷函数
def merge_payroll_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[MergeWarning]]:
    """
    便捷函数：合并发薪表数据
    
    Args:
        df: 发薪表DataFrame
        
    Returns:
        (合并后的DataFrame, 警告信息列表)
    """
    merger = DataMerger()
    return merger.merge_by_id_card(df, id_card_col='身份证号')


def merge_social_security_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[MergeWarning]]:
    """
    便捷函数：合并社保表数据
    
    Args:
        df: 社保表DataFrame
        
    Returns:
        (合并后的DataFrame, 警告信息列表)
    """
    merger = DataMerger()
    return merger.merge_by_id_card(df, id_card_col='身份证号')

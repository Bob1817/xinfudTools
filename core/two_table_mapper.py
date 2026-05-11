"""
双表合并映射器（优化版）
社保数据表 + 发薪表 → 个税申报表
支持身份证号合并和默认值处理
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from core.data_loader import PayrollLoader
from core.social_security_loader import SocialSecurityLoader
from core.data_merger import DataMerger, MergeWarning
from core.error_handler import handle_error, ErrorInfo


class TwoTableMapper:
    """双表合并映射器：社保数据表 + 发薪表 → 个税申报表（优化版）"""

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
        "企业 (职业) 年金",
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
        self.data_merger = DataMerger()
        self.warnings: List[MergeWarning] = []
        self.merge_stats: Dict = {}

    def merge_and_map(
        self,
        payroll_df: pd.DataFrame,
        social_security_dict: Dict,
        period: str = ""
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        合并社保数据和发薪表数据，生成申报表格式
        
        Args:
            payroll_df: 发薪表数据
            social_security_dict: 社保数据字典（以身份证号为 key）
            period: 所属期
            
        Returns:
            (申报表格式的 DataFrame, 合并统计信息)
        """
        self.warnings = []
        
        try:
            # 步骤1：合并发薪表中同一身份证号的数据
            payroll_merged, payroll_warnings = self.data_merger.merge_by_id_card(
                payroll_df, 
                id_card_col='身份证号'
            )
            self.warnings.extend(payroll_warnings)
            
            # 获取发薪表个人部分列名
            personal_cols = self.payroll_loader.get_personal_columns(payroll_merged)
            
            # 发薪表个人部分列名映射
            col_pension = personal_cols[0]      # 养老
            col_unemploy = personal_cols[1]     # 失业
            col_medical = personal_cols[3]      # 医疗
            col_housing = personal_cols[4]      # 公积金

            # 构建申报表
            result = pd.DataFrame()
            
            # 统计信息
            stats = {
                'total_records': 0,
                'with_ss_data': 0,
                'without_ss_data': 0,
                'ss_fields_used': 0,
                'payroll_fields_used': 0,
                'default_values': 0,
                'merged_payroll_records': len(payroll_df) - len(payroll_merged),
                'warnings': []
            }

            # 遍历发薪表数据
            for idx, row in payroll_merged.iterrows():
                try:
                    id_card = str(row[self.payroll_loader.COL_ID]).strip()
                    
                    # 跳过空身份证号
                    if not id_card or id_card.upper() == 'NAN':
                        continue

                    # 获取社保数据（如果有）
                    ss_data = social_security_dict.get(id_card, {})
                    has_ss_data = bool(ss_data)
                    
                    if has_ss_data:
                        stats['with_ss_data'] += 1
                    else:
                        stats['without_ss_data'] += 1

                    # 构建一行申报表数据
                    tax_row = {}
                    tax_row["*工号"] = len(result) + 1
                    tax_row["*姓名"] = row[self.payroll_loader.COL_NAME]
                    tax_row["*证件类型"] = "居民身份证"
                    tax_row["*证件号码"] = id_card

                    # 本期收入（发薪表的应发金额）
                    tax_row["本期收入"] = self._get_safe_value(
                        row, self.payroll_loader.COL_GROSS_PAY, 0
                    )
                    tax_row["本期免税收入"] = 0

                    # 社保公积金 - 优先使用社保表数据，没有则用发薪表个人部分数据，都没有则默认为0
                    # 基本养老保险费
                    if ss_data and self.ss_loader.COL_PENSION in ss_data:
                        tax_row["基本养老保险费"] = self._safe_float(ss_data.get(self.ss_loader.COL_PENSION, 0))
                        stats['ss_fields_used'] += 1
                    else:
                        tax_row["基本养老保险费"] = self._get_safe_value(row, col_pension, 0)
                        if tax_row["基本养老保险费"] > 0:
                            stats['payroll_fields_used'] += 1
                        else:
                            stats['default_values'] += 1

                    # 基本医疗保险费
                    if ss_data and self.ss_loader.COL_MEDICAL in ss_data:
                        tax_row["基本医疗保险费"] = self._safe_float(ss_data.get(self.ss_loader.COL_MEDICAL, 0))
                        stats['ss_fields_used'] += 1
                    else:
                        tax_row["基本医疗保险费"] = self._get_safe_value(row, col_medical, 0)
                        if tax_row["基本医疗保险费"] > 0:
                            stats['payroll_fields_used'] += 1
                        else:
                            stats['default_values'] += 1

                    # 失业保险费
                    if ss_data and self.ss_loader.COL_UNEMPLOYMENT in ss_data:
                        tax_row["失业保险费"] = self._safe_float(ss_data.get(self.ss_loader.COL_UNEMPLOYMENT, 0))
                        stats['ss_fields_used'] += 1
                    else:
                        tax_row["失业保险费"] = self._get_safe_value(row, col_unemploy, 0)
                        if tax_row["失业保险费"] > 0:
                            stats['payroll_fields_used'] += 1
                        else:
                            stats['default_values'] += 1

                    # 住房公积金
                    if ss_data and self.ss_loader.COL_HOUSING in ss_data:
                        tax_row["住房公积金"] = self._safe_float(ss_data.get(self.ss_loader.COL_HOUSING, 0))
                        stats['ss_fields_used'] += 1
                    else:
                        tax_row["住房公积金"] = self._get_safe_value(row, col_housing, 0)
                        if tax_row["住房公积金"] > 0:
                            stats['payroll_fields_used'] += 1
                        else:
                            stats['default_values'] += 1

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
                    if hasattr(self.payroll_loader, 'COL_COMM_FEE') and self.payroll_loader.COL_COMM_FEE in row.index:
                        tax_row["通讯费用"] = self._get_safe_value(row, self.payroll_loader.COL_COMM_FEE, 0)
                    else:
                        tax_row["通讯费用"] = 0

                    tax_row["律师办案费用"] = 0
                    tax_row["西藏附加减除费用"] = 0
                    tax_row["其他"] = 0
                    tax_row["准予扣除的捐赠额"] = 0
                    tax_row["减免税额"] = 0

                    # 备注
                    if hasattr(self.payroll_loader, 'COL_REMARK') and self.payroll_loader.COL_REMARK in row.index:
                        tax_row["备注"] = str(row[self.payroll_loader.COL_REMARK]) if pd.notna(row[self.payroll_loader.COL_REMARK]) else ""
                    else:
                        tax_row["备注"] = ""

                    result = pd.concat([result, pd.DataFrame([tax_row])], ignore_index=True)
                    stats['total_records'] += 1
                    
                except Exception as e:
                    # 记录错误但继续处理其他记录
                    error_info = handle_error(e, {'row': idx, 'id_card': id_card})
                    stats['warnings'].append(f"处理第{idx+1}行数据时出错: {error_info.message}")
                    continue

            # 确保数据类型正确
            for col in ["本期收入", "基本养老保险费", "基本医疗保险费", "失业保险费", "住房公积金", "通讯费用"]:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)

            result["*证件号码"] = result["*证件号码"].astype(str)
            result["*姓名"] = result["*姓名"].astype(str)
            result["备注"] = result["备注"].fillna("").astype(str)
            
            # 保存统计信息
            self.merge_stats = stats
            
            return result, stats
            
        except Exception as e:
            error_info = handle_error(e)
            raise ValueError(f"合并数据失败: {error_info.message}")

    def _get_safe_value(self, row, column, default=0):
        """
        安全获取值，如果列不存在或值为空则返回默认值
        
        Args:
            row: 数据行
            column: 列名
            default: 默认值
            
        Returns:
            值或默认值
        """
        try:
            if column not in row.index:
                return default
            
            value = row[column]
            
            if pd.isna(value) or value == '' or value is None:
                return default
            
            # 尝试转换为数值
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
                
        except Exception:
            return default

    def _safe_float(self, value, default=0.0):
        """
        安全转换为浮点数
        
        Args:
            value: 值
            default: 默认值
            
        Returns:
            浮点数或默认值
        """
        try:
            if pd.isna(value) or value == '' or value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def validate_merge(
        self,
        payroll_df: pd.DataFrame,
        social_security_df: pd.DataFrame
    ) -> Dict:
        """
        验证合并结果，返回检测结果
        
        Args:
            payroll_df: 发薪表数据
            social_security_df: 社保表数据
            
        Returns:
            检测结果字典
        """
        try:
            # 合并发薪表数据（用于统计）
            payroll_merged, _ = self.data_merger.merge_by_id_card(
                payroll_df, 
                id_card_col='身份证号'
            )
            
            # 发薪表数据
            payroll_ids = set(str(id_card).strip().upper() for id_card in payroll_merged['身份证号'] if pd.notna(id_card))
            ss_ids = set(str(id_card).strip().upper() for id_card in social_security_df['身份证号'] if pd.notna(id_card))

            # 匹配情况
            matched_ids = payroll_ids & ss_ids
            only_in_payroll = payroll_ids - ss_ids
            only_in_ss = ss_ids - payroll_ids

            return {
                "payroll_total": len(payroll_df),
                "payroll_unique": len(payroll_merged),
                "payroll_merged": len(payroll_df) - len(payroll_merged),
                "social_security_total": len(social_security_df),
                "matched_count": len(matched_ids),
                "only_in_payroll_count": len(only_in_payroll),
                "only_in_ss_count": len(only_in_ss),
                "match_rate": len(matched_ids) / len(payroll_ids) * 100 if payroll_ids else 0,
            }
        except Exception as e:
            error_info = handle_error(e)
            raise ValueError(f"验证合并失败: {error_info.message}")

    def get_merge_summary(self) -> str:
        """
        获取合并摘要信息
        
        Returns:
            摘要文本
        """
        if not self.merge_stats:
            return "暂无合并数据"
        
        lines = [
            f"📊 数据合并统计",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"总记录数: {self.merge_stats.get('total_records', 0)}",
            f"",
            f"数据来源:",
            f"  • 使用社保表数据: {self.merge_stats.get('with_ss_data', 0)} 条",
            f"  • 使用发薪表数据: {self.merge_stats.get('without_ss_data', 0)} 条",
            f"",
            f"字段来源:",
            f"  • 社保表字段: {self.merge_stats.get('ss_fields_used', 0)} 次",
            f"  • 发薪表字段: {self.merge_stats.get('payroll_fields_used', 0)} 次",
            f"  • 默认值(0.00): {self.merge_stats.get('default_values', 0)} 次",
        ]
        
        if self.merge_stats.get('merged_payroll_records', 0) > 0:
            lines.append(f"")
            lines.append(f"⚠️ 合并了 {self.merge_stats['merged_payroll_records']} 条重复身份证号记录")
        
        if self.warnings:
            lines.append(f"")
            lines.append(f"⚠️ 发现 {len(self.warnings)} 处数据不一致:")
            for warning in self.warnings[:3]:
                lines.append(f"  • {warning.message}")
            if len(self.warnings) > 3:
                lines.append(f"  ... 还有 {len(self.warnings) - 3} 处")
        
        lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return '\n'.join(lines)

    def get_warnings(self) -> List[MergeWarning]:
        """
        获取合并警告
        
        Returns:
            警告列表
        """
        return self.warnings.copy()


# 便捷函数
def merge_tables(
    payroll_df: pd.DataFrame,
    social_security_dict: Dict,
    period: str = ""
) -> Tuple[pd.DataFrame, Dict]:
    """
    便捷函数：合并发薪表和社保表
    
    Args:
        payroll_df: 发薪表数据
        social_security_dict: 社保数据字典
        period: 所属期
        
    Returns:
        (申报表DataFrame, 统计信息)
    """
    mapper = TwoTableMapper()
    return mapper.merge_and_map(payroll_df, social_security_dict, period)

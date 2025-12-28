"""
Data Analysis Module - CMMS Data Import & Metrics Calculation
Automated analysis of CMMS exports for evidence-based scoring
"""
from sqlalchemy.orm import Session
from models import DataAnalysis, Evidence, EvidenceType
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime
import os
from scoring_engine import (
    calculate_reactive_ratio,
    calculate_pm_compliance,
    calculate_data_graveyard_index
)


class CMMSDataAnalyzer:
    """
    Analyzes CMMS data exports to calculate key reliability metrics
    Supports multiple CMMS formats with configurable column mappings
    """
    
    # Default column mappings (can be overridden per CMMS system)
    DEFAULT_WO_COLUMNS = {
        "work_order_number": ["WO Number", "Work Order ID", "WO#"],
        "work_order_type": ["Type", "WO Type", "Work Type", "Order Type"],
        "priority": ["Priority", "Priority Level"],
        "status": ["Status", "WO Status"],
        "created_date": ["Created", "Date Created", "Entry Date"],
        "completed_date": ["Completed", "Date Completed", "Finish Date"],
        "closure_notes": ["Notes", "Resolution", "Closure Notes", "Comments"]
    }
    
    DEFAULT_PM_COLUMNS = {
        "pm_number": ["PM Number", "PM ID"],
        "due_date": ["Due Date", "Scheduled Date"],
        "completed_date": ["Completed Date", "Actual Date"],
        "status": ["Status"]
    }
    
    def __init__(self, db: Session, upload_dir: str = "./uploads/cmms_data"):
        self.db = db
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def import_work_orders(
        self,
        file_path: str,
        column_mapping: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Import work order data from CSV or Excel
        
        Args:
            file_path: Path to CMMS export file
            column_mapping: Optional custom column mapping
        
        Returns:
            Cleaned DataFrame with standardized column names
        """
        # Read file based on extension
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")
        
        # Apply column mapping
        mapping = column_mapping or self.DEFAULT_WO_COLUMNS
        standardized_df = self._apply_column_mapping(df, mapping)
        
        return standardized_df
    
    def import_pm_data(
        self,
        file_path: str,
        column_mapping: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Import PM data with standardized column names"""
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        mapping = column_mapping or self.DEFAULT_PM_COLUMNS
        standardized_df = self._apply_column_mapping(df, mapping)
        
        return standardized_df
    
    def _apply_column_mapping(self, df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
        """Find and rename columns based on mapping"""
        new_df = df.copy()
        rename_dict = {}
        
        for standard_name, possible_names in mapping.items():
            for col in df.columns:
                if col in possible_names:
                    rename_dict[col] = standard_name
                    break
        
        new_df = new_df.rename(columns=rename_dict)
        return new_df
    
    def analyze_work_orders(
        self,
        assessment_id: int,
        analyzer_id: int,
        file_path: str,
        save_to_db: bool = True
    ) -> Dict:
        """
        Complete work order analysis pipeline
        Calculates: Reactive Ratio, Data Quality, Work Type Distribution
        """
        # Import data
        df = self.import_work_orders(file_path)
        
        # Calculate reactive ratio
        reactive_metrics = calculate_reactive_ratio(df)
        
        # Calculate data quality
        data_quality_metrics = calculate_data_graveyard_index(df)
        
        # Additional metrics
        work_type_distribution = self._calculate_work_type_distribution(df)
        
        # Combine all metrics
        combined_metrics = {
            "reactive_ratio": reactive_metrics,
            "data_quality": data_quality_metrics,
            "work_type_distribution": work_type_distribution,
            "total_records_analyzed": len(df),
            "analysis_date": datetime.utcnow().isoformat()
        }
        
        # Save to database
        if save_to_db:
            self._save_analysis_results(
                assessment_id=assessment_id,
                analyzer_id=analyzer_id,
                analysis_type="Work Order Analysis",
                metrics=combined_metrics,
                data_source=os.path.basename(file_path)
            )
        
        return combined_metrics
    
    def analyze_pm_compliance(
        self,
        assessment_id: int,
        analyzer_id: int,
        file_path: str,
        save_to_db: bool = True
    ) -> Dict:
        """
        PM compliance analysis pipeline
        Calculates: On-time completion %, Average delay, Compliance trend
        """
        # Import PM data
        df = self.import_pm_data(file_path)
        
        # Calculate compliance
        pm_metrics = calculate_pm_compliance(df)
        
        # Save to database
        if save_to_db:
            self._save_analysis_results(
                assessment_id=assessment_id,
                analyzer_id=analyzer_id,
                analysis_type="PM Compliance Analysis",
                metrics=pm_metrics,
                data_source=os.path.basename(file_path)
            )
        
        return pm_metrics
    
    def _calculate_work_type_distribution(self, df: pd.DataFrame) -> Dict:
        """Calculate distribution of work types"""
        if 'work_order_type' not in df.columns:
            return {"error": "work_order_type column not found"}
        
        distribution = df['work_order_type'].value_counts().to_dict()
        total = len(df)
        
        return {
            "distribution": distribution,
            "percentages": {
                wtype: round(count / total * 100, 1)
                for wtype, count in distribution.items()
            }
        }
    
    def _save_analysis_results(
        self,
        assessment_id: int,
        analyzer_id: int,
        analysis_type: str,
        metrics: Dict,
        data_source: str
    ):
        """Save analysis results to database"""
        analysis = DataAnalysis(
            assessment_id=assessment_id,
            analyzed_by=analyzer_id,
            analysis_type=analysis_type,
            data_source=data_source,
            metrics=metrics,
            sample_size=metrics.get('total_records_analyzed'),
            actual_value=metrics.get('reactive_ratio', {}).get('reactive_ratio'),
            passed=metrics.get('reactive_ratio', {}).get('score', 0) >= 3
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    def random_sample_audit(
        self,
        df: pd.DataFrame,
        sample_size: int = 50,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Perform random sampling for detailed audit
        Used for closure code quality checks
        """
        if len(df) < sample_size:
            return df  # Return all if less than sample size
        
        return df.sample(n=sample_size, random_state=seed)
    
    def get_analysis_summary(self, assessment_id: int) -> Dict:
        """Get summary of all data analyses for an assessment"""
        analyses = self.db.query(DataAnalysis).filter(
            DataAnalysis.assessment_id == assessment_id
        ).all()
        
        summary = {
            "total_analyses": len(analyses),
            "analyses": []
        }
        
        for analysis in analyses:
            summary["analyses"].append({
                "type": analysis.analysis_type,
                "data_source": analysis.data_source,
                "analyzed_at": analysis.analyzed_at.isoformat(),
                "passed": analysis.passed,
                "key_metrics": analysis.metrics
            })
        
        return summary
    
    def detect_bad_actors(
        self,
        df: pd.DataFrame,
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        Identify top failing assets (Bad Actors)
        Requires 'asset_id' or 'equipment' column
        """
        asset_col = None
        for col in ['asset_id', 'equipment', 'equipment_id', 'asset']:
            if col in df.columns:
                asset_col = col
                break
        
        if not asset_col:
            raise ValueError("No asset identifier column found")
        
        # Count failures per asset
        failure_types = ['corrective', 'emergency', 'breakdown']
        
        if 'work_order_type' in df.columns:
            failures = df[
                df['work_order_type'].str.lower().isin(failure_types)
            ]
        else:
            failures = df  # Use all WOs if type not available
        
        bad_actors = failures.groupby(asset_col).size().sort_values(ascending=False).head(top_n)
        
        return bad_actors.to_frame(name='failure_count')

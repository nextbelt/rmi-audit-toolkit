"""
Observation & Shadowing Module
Real-time field observation capture with evidence management
"""
from sqlalchemy.orm import Session
from models import Observation, Evidence, EvidenceType, PillarType
from typing import List, Optional, Dict
from datetime import datetime
import os
import shutil


class ObservationManager:
    """
    Manages field observations during job shadowing
    Tablet-friendly interface for capturing real-time evidence
    """
    
    def __init__(self, db: Session, upload_dir: str = "./uploads"):
        self.db = db
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def create_observation(
        self,
        assessment_id: int,
        observer_id: int,
        observation_data: Dict
    ) -> Observation:
        """
        Create a new field observation
        
        Args:
            assessment_id: ID of the assessment
            observer_id: ID of the auditor making the observation
            observation_data: Dict containing observation details
        """
        observation = Observation(
            assessment_id=assessment_id,
            observer_id=observer_id,
            observation_title=observation_data['title'],
            observation_type=observation_data.get('type', 'General'),
            pillar=PillarType(observation_data['pillar']),
            subcategory=observation_data.get('subcategory'),
            observation_notes=observation_data['notes'],
            pass_fail_result=observation_data.get('pass_fail'),
            severity=observation_data.get('severity'),
            observed_role=observation_data.get('observed_role'),
            location=observation_data.get('location'),
            observed_at=observation_data.get('observed_at', datetime.utcnow())
        )
        
        self.db.add(observation)
        self.db.commit()
        self.db.refresh(observation)
        
        return observation
    
    def attach_evidence(
        self,
        observation_id: int,
        uploader_id: int,
        file_path: str,
        evidence_type: EvidenceType,
        description: Optional[str] = None
    ) -> Evidence:
        """
        Attach evidence file to an observation
        
        Args:
            observation_id: ID of the observation
            uploader_id: ID of user uploading evidence
            file_path: Path to the evidence file
            evidence_type: Type of evidence (photo, document, etc.)
            description: Optional description of the evidence
        """
        # Copy file to uploads directory
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create subdirectory for this observation
        obs_dir = os.path.join(self.upload_dir, f"observation_{observation_id}")
        os.makedirs(obs_dir, exist_ok=True)
        
        dest_path = os.path.join(obs_dir, file_name)
        shutil.copy2(file_path, dest_path)
        
        # Create evidence record
        evidence = Evidence(
            observation_id=observation_id,
            evidence_type=evidence_type,
            file_path=dest_path,
            file_name=file_name,
            file_size_bytes=file_size,
            description=description,
            uploaded_by=uploader_id
        )
        
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        
        return evidence
    
    def get_observations_by_assessment(
        self,
        assessment_id: int,
        pillar: Optional[PillarType] = None
    ) -> List[Observation]:
        """Get all observations for an assessment, optionally filtered by pillar"""
        query = self.db.query(Observation).filter(
            Observation.assessment_id == assessment_id
        )
        
        if pillar:
            query = query.filter(Observation.pillar == pillar)
        
        return query.order_by(Observation.observed_at.desc()).all()
    
    def get_observation_with_evidence(self, observation_id: int) -> Dict:
        """Get observation with all attached evidence"""
        observation = self.db.query(Observation).filter(
            Observation.id == observation_id
        ).first()
        
        if not observation:
            raise ValueError(f"Observation {observation_id} not found")
        
        evidence_files = self.db.query(Evidence).filter(
            Evidence.observation_id == observation_id
        ).all()
        
        return {
            "observation": observation,
            "evidence": evidence_files,
            "evidence_count": len(evidence_files)
        }
    
    def get_critical_failures(self, assessment_id: int) -> List[Observation]:
        """Get all observations marked as critical failures"""
        return self.db.query(Observation).filter(
            Observation.assessment_id == assessment_id,
            Observation.severity == "Critical",
            Observation.pass_fail_result == False
        ).all()
    
    def create_checklist_observation(
        self,
        assessment_id: int,
        observer_id: int,
        checklist_items: List[Dict]
    ) -> List[Observation]:
        """
        Create multiple observations from a checklist
        Useful for structured audits (e.g., LOTO compliance, SOP usage)
        
        Args:
            checklist_items: List of dicts, each containing observation data
        """
        observations = []
        
        for item in checklist_items:
            obs = self.create_observation(
                assessment_id=assessment_id,
                observer_id=observer_id,
                observation_data=item
            )
            observations.append(obs)
        
        return observations


# Pre-defined observation checklists for common scenarios

WORK_EXECUTION_CHECKLIST = [
    {
        "title": "Spare Parts Availability",
        "type": "Work Execution",
        "pillar": "process",
        "subcategory": "Planning & Kitting",
        "severity": "Major",
        "notes": "Template - Update with actual findings"
    },
    {
        "title": "SOP Reference & Usage",
        "type": "Work Execution",
        "pillar": "process",
        "subcategory": "SOP Compliance",
        "severity": "Major",
        "notes": "Template - Update with actual findings"
    },
    {
        "title": "Tools & Equipment Ready",
        "type": "Work Execution",
        "pillar": "process",
        "subcategory": "Job Preparation",
        "severity": "Minor",
        "notes": "Template - Update with actual findings"
    }
]

SAFETY_CHECKLIST = [
    {
        "title": "LOTO Procedure Applied",
        "type": "Safety Compliance",
        "pillar": "process",
        "subcategory": "Safety",
        "severity": "Critical",
        "notes": "Template - Update with actual findings"
    },
    {
        "title": "PPE Compliance",
        "type": "Safety Compliance",
        "pillar": "people",
        "subcategory": "Safety Culture",
        "severity": "Critical",
        "notes": "Template - Update with actual findings"
    },
    {
        "title": "Permit-to-Work Obtained",
        "type": "Safety Compliance",
        "pillar": "process",
        "subcategory": "Safety",
        "severity": "Critical",
        "notes": "Template - Update with actual findings"
    }
]

CMMS_USAGE_CHECKLIST = [
    {
        "title": "Technician Accesses Work Order on Mobile",
        "type": "CMMS Usage",
        "pillar": "technology",
        "subcategory": "System Adoption",
        "severity": "Minor",
        "notes": "Template - Update with actual findings"
    },
    {
        "title": "Work Order Updates in Real-Time",
        "type": "CMMS Usage",
        "pillar": "technology",
        "subcategory": "Data Timeliness",
        "severity": "Minor",
        "notes": "Template - Update with actual findings"
    },
    {
        "title": "Photo Attached to Work Order",
        "type": "CMMS Usage",
        "pillar": "technology",
        "subcategory": "Documentation Quality",
        "severity": "Minor",
        "notes": "Template - Update with actual findings"
    }
]

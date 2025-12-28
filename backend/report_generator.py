"""
Executive Report Generator
Professional, board-ready reports with charts and roadmaps
"""
from sqlalchemy.orm import Session
from models import Assessment, Score, PillarType, Report
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import io
from datetime import datetime
from typing import Dict, List
import json
import os


class ReportGenerator:
    """
    Generates executive-grade audit reports
    - Executive Summary
    - Pillar Breakdown
    - Radar Charts
    - 30/60/90 Day Roadmap
    - PDF Export
    """
    
    def __init__(self, db: Session, output_dir: str = "./reports"):
        self.db = db
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_executive_report(
        self,
        assessment_id: int,
        generated_by: int
    ) -> str:
        """
        Generate complete executive report
        Returns: Path to generated PDF
        """
        # Get assessment data
        assessment = self.db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Get scores
        scores = self.db.query(Score).filter(
            Score.assessment_id == assessment_id
        ).all()
        
        # Create PDF
        filename = f"RMI_Audit_Report_{assessment.client_name}_{assessment.site_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title Page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("Reliability Maturity Index", title_style))
        story.append(Paragraph("Audit Report", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Client info
        client_info = f"""
        <b>Client:</b> {assessment.client_name}<br/>
        <b>Site:</b> {assessment.site_name}<br/>
        <b>Industry:</b> {assessment.industry or 'N/A'}<br/>
        <b>Assessment Date:</b> {assessment.assessment_date.strftime('%B %d, %Y')}<br/>
        <b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y')}
        """
        story.append(Paragraph(client_info, styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        overall_score = next((s for s in scores if s.pillar is None), None)
        if overall_score:
            maturity_level = self._get_maturity_description(overall_score.final_score)
            
            summary_text = f"""
            <b>Overall RMI Score: {overall_score.final_score:.2f} / 5.00</b><br/>
            <b>Maturity Level:</b> {maturity_level}<br/><br/>
            
            This assessment evaluated {assessment.site_name}'s maintenance and reliability practices 
            across three critical pillars: People, Process, and Technology. The assessment included 
            structured interviews, field observations, and data analysis of CMMS records.
            """
            story.append(Paragraph(summary_text, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Pillar Scores Table
        story.append(Paragraph("Pillar Breakdown", heading_style))
        
        pillar_scores = [s for s in scores if s.pillar is not None]
        table_data = [['Pillar', 'Score', 'Maturity Level', 'Confidence']]
        
        for score in pillar_scores:
            table_data.append([
                score.pillar.value.title(),
                f"{score.final_score:.2f}",
                self._get_maturity_description(score.final_score),
                score.confidence_level
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        # Generate and add radar chart
        chart_image = self._generate_radar_chart(pillar_scores)
        if chart_image:
            story.append(Paragraph("Maturity Profile", heading_style))
            story.append(Image(chart_image, width=5*inch, height=4*inch))
            story.append(Spacer(1, 0.3*inch))
        
        story.append(PageBreak())
        
        # Key Findings
        story.append(Paragraph("Key Findings", heading_style))
        findings = self._generate_findings(assessment_id, pillar_scores)
        for finding in findings:
            story.append(Paragraph(f"• {finding}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Roadmap
        story.append(PageBreak())
        story.append(Paragraph("Recommended Roadmap", heading_style))
        roadmap = self._generate_roadmap(pillar_scores)
        
        for phase, actions in roadmap.items():
            story.append(Paragraph(f"<b>{phase}</b>", styles['Heading3']))
            for action in actions:
                story.append(Paragraph(f"• {action}", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        
        # Save report record to database
        self._save_report_record(
            assessment_id=assessment_id,
            generated_by=generated_by,
            report_type="Executive Summary",
            file_path=filepath
        )
        
        return filepath
    
    def _generate_radar_chart(self, pillar_scores: List[Score]) -> str:
        """Generate radar chart for pillar scores"""
        if not pillar_scores:
            return None
        
        categories = []
        values = []
        
        for score in pillar_scores:
            categories.append(score.pillar.value.title())
            values.append(score.final_score)
        
        # Create radar chart
        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(projection='polar'))
        
        # Number of variables
        num_vars = len(categories)
        angles = [n / float(num_vars) * 2 * 3.14159 for n in range(num_vars)]
        values += values[:1]  # Complete the circle
        angles += angles[:1]
        
        ax.plot(angles, values, 'o-', linewidth=2, color='#3498db')
        ax.fill(angles, values, alpha=0.25, color='#3498db')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=12)
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(['1', '2', '3', '4', '5'])
        ax.grid(True)
        
        plt.title('RMI Maturity Profile', size=16, weight='bold', pad=20)
        
        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Save temporarily
        temp_path = os.path.join(self.output_dir, "temp_radar.png")
        with open(temp_path, 'wb') as f:
            f.write(img_buffer.getvalue())
        
        return temp_path
    
    def _get_maturity_description(self, score: float) -> str:
        """Convert score to maturity description"""
        if score < 2.0:
            return "Reactive"
        elif score < 3.0:
            return "Emerging Preventive"
        elif score < 4.0:
            return "Preventive"
        elif score < 4.5:
            return "Predictive"
        else:
            return "Prescriptive"
    
    def _generate_findings(self, assessment_id: int, pillar_scores: List[Score]) -> List[str]:
        """Generate key findings based on scores"""
        findings = []
        
        for score in pillar_scores:
            pillar_name = score.pillar.value.title()
            
            if score.final_score < 2.5:
                findings.append(
                    f"<b>{pillar_name}:</b> CRITICAL - Significant gaps identified. "
                    f"Immediate intervention required to prevent reliability degradation."
                )
            elif score.final_score < 3.5:
                findings.append(
                    f"<b>{pillar_name}:</b> Improvement opportunities exist. "
                    f"Focus on standardization and capability building."
                )
            elif score.final_score < 4.5:
                findings.append(
                    f"<b>{pillar_name}:</b> Solid foundation in place. "
                    f"Ready for predictive maintenance initiatives."
                )
            else:
                findings.append(
                    f"<b>{pillar_name}:</b> EXCELLENT - World-class practices observed. "
                    f"Focus on sustainability and continuous improvement."
                )
        
        # Add specific findings based on critical failures
        from scoring_engine import ScoringEngine
        engine = ScoringEngine(self.db)
        violations = engine.validate_evidence_requirements(assessment_id)
        
        if violations:
            findings.append(
                f"<b>Evidence Gap:</b> {len(violations)} high scores require additional "
                f"evidence documentation for defensibility."
            )
        
        return findings
    
    def _generate_roadmap(self, pillar_scores: List[Score]) -> Dict[str, List[str]]:
        """Generate 30/60/90 day roadmap based on scores"""
        roadmap = {
            "30-Day Quick Wins": [],
            "60-Day Capability Building": [],
            "90-Day Strategic Initiatives": []
        }
        
        # Identify weakest pillar
        weakest = min(pillar_scores, key=lambda x: x.final_score)
        strongest = max(pillar_scores, key=lambda x: x.final_score)
        
        # 30-Day actions (quick wins)
        if weakest.pillar == PillarType.PEOPLE:
            roadmap["30-Day Quick Wins"].extend([
                "Conduct skill gap assessment for critical technicians",
                "Establish weekly toolbox talks on reliability topics",
                "Create mentorship pairings between senior and junior technicians"
            ])
        elif weakest.pillar == PillarType.PROCESS:
            roadmap["30-Day Quick Wins"].extend([
                "Audit 100 recent work orders for planning quality",
                "Create standard job plans for top 20 PM tasks",
                "Implement daily production-maintenance coordination meetings"
            ])
        elif weakest.pillar == PillarType.TECHNOLOGY:
            roadmap["30-Day Quick Wins"].extend([
                "Audit CMMS data quality (closure codes, failure modes)",
                "Create dashboard for reactive vs. preventive work",
                "Establish data quality KPIs and weekly monitoring"
            ])
        
        # 60-Day actions (capability building)
        roadmap["60-Day Capability Building"].extend([
            "Develop formal training curriculum for maintenance roles",
            "Implement work order planning checklist and approval process",
            "Redesign CMMS failure code structure per ISO 14224",
            "Launch pilot predictive maintenance program on critical assets"
        ])
        
        # 90-Day actions (strategic)
        roadmap["90-Day Strategic Initiatives"].extend([
            "Establish Reliability Center of Excellence (COE)",
            "Implement Reliability-Centered Maintenance (RCM) for critical systems",
            "Deploy mobile CMMS with offline capability",
            "Create asset criticality matrix and risk-based PM strategy",
            "Develop key reliability metrics dashboard for leadership"
        ])
        
        return roadmap
    
    def _save_report_record(
        self,
        assessment_id: int,
        generated_by: int,
        report_type: str,
        file_path: str
    ):
        """Save report metadata to database"""
        report = Report(
            assessment_id=assessment_id,
            generated_by=generated_by,
            report_type=report_type,
            title=f"RMI Audit Report - {report_type}",
            file_path=file_path
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    def generate_technical_detail_report(
        self,
        assessment_id: int,
        generated_by: int
    ) -> str:
        """Generate detailed technical report with all questions and responses"""
        # Implementation similar to executive report but with full question details
        pass
    
    def export_to_powerpoint(self, assessment_id: int) -> str:
        """Export key findings to PowerPoint format"""
        # Use python-pptx library for PowerPoint generation
        pass

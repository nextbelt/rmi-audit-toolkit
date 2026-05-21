"""
Executive Report Generator - Consulting-Grade Deliverable
MBB/Accenture Style: Visual Narrative with Professional Branding
"""
from sqlalchemy.orm import Session
from models import Assessment, Score, PillarType, Report, QuestionResponse, QuestionBank, Observation, DataAnalysis
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
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
import numpy as np


class ConsultingTheme:
    """
    Professional Neutral Color Palette
    Clean, corporate styling without brand-specific colors
    """
    # Primary Brand Colors - Professional Navy & Slate
    PRIMARY = colors.HexColor('#1A4D8F')      # Professional Navy Blue
    SECONDARY = colors.HexColor('#2C3E50')    # Dark Slate
    ACCENT = colors.HexColor('#3498DB')       # Bright Blue accent
    
    # Maturity Level Colors
    CRITICAL = colors.HexColor('#E74C3C')     # Red
    WARNING = colors.HexColor('#E67E22')      # Orange
    CAUTION = colors.HexColor('#F39C12')      # Amber
    GOOD = colors.HexColor('#27AE60')         # Green
    EXCELLENT = colors.HexColor('#16A085')    # Teal
    
    # Neutral Palette
    DARK_GREY = colors.HexColor('#2C3E50')
    MID_GREY = colors.HexColor('#7F8C8D')
    LIGHT_GREY = colors.HexColor('#BDC3C7')
    BG_GREY = colors.HexColor('#ECF0F1')
    WHITE = colors.white
    
    @staticmethod
    def get_maturity_color(score: float) -> colors.Color:
        """Return color based on maturity score"""
        if score < 2.0:
            return ConsultingTheme.CRITICAL
        elif score < 3.0:
            return ConsultingTheme.WARNING
        elif score < 4.0:
            return ConsultingTheme.CAUTION
        elif score < 4.5:
            return ConsultingTheme.GOOD
        else:
            return ConsultingTheme.EXCELLENT


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
        
        # Get CMMS data analyses
        cmms_analyses = self.db.query(DataAnalysis).filter(
            DataAnalysis.assessment_id == assessment_id
        ).all()
        
        # Create PDF
        filename = f"RMI_Audit_Report_{assessment.client_name}_{assessment.site_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Consulting-Grade Custom Styles
        title_style = ParagraphStyle(
            'ConsultingTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=ConsultingTheme.PRIMARY,
            spaceAfter=0.3*inch,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=34
        )
        
        heading_style = ParagraphStyle(
            'ConsultingHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=ConsultingTheme.SECONDARY,
            spaceAfter=0.2*inch,
            spaceBefore=0.3*inch,
            fontName='Helvetica-Bold'
        )
        
        insight_style = ParagraphStyle(
            'InsightBox',
            parent=styles['Normal'],
            fontSize=11,
            textColor=ConsultingTheme.DARK_GREY,
            backColor=ConsultingTheme.BG_GREY,
            borderWidth=1,
            borderColor=ConsultingTheme.ACCENT,
            borderPadding=12,
            spaceAfter=0.2*inch,
            leftIndent=10,
            rightIndent=10
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
            # Get audit statistics
            response_count = self.db.query(QuestionResponse).filter(
                QuestionResponse.assessment_id == assessment_id,
                QuestionResponse.is_draft == False,
                QuestionResponse.is_na == False
            ).count()
            
            observation_count = self.db.query(Observation).filter(
                Observation.assessment_id == assessment_id
            ).count()
            
            # Get unique respondents count (simplified - count unique respondent_ids)
            unique_respondents = self.db.query(QuestionResponse.respondent_id).filter(
                QuestionResponse.assessment_id == assessment_id,
                QuestionResponse.is_draft == False,
                QuestionResponse.respondent_id.isnot(None)
            ).distinct().count()
            
            # If no respondent_ids, just say "multiple respondents"
            if unique_respondents == 0:
                unique_respondents = "multiple"
            
            maturity_level = self._get_maturity_description(overall_score.final_score)
            
            # Get CMMS metrics for summary
            cmms_summary = ""
            if cmms_analyses:
                latest_analysis = cmms_analyses[0]
                metrics = latest_analysis.metrics or {}
                reactive_ratio = metrics.get('reactive_ratio', {}).get('reactive_ratio', 'N/A')
                data_quality = metrics.get('data_quality', {}).get('graveyard_percentage', 'N/A')
                total_records = metrics.get('total_records_analyzed', 0)
                
                if total_records > 0:
                    cmms_summary = f"• <b>{total_records} work order records analyzed</b> from CMMS export (Reactive Ratio: {reactive_ratio}%, Data Quality: {100 - data_quality if isinstance(data_quality, (int, float)) else 'N/A'}%)<br/>"
                else:
                    cmms_summary = "• Data analysis of CMMS records and work order history<br/>"
            else:
                cmms_summary = "• Data analysis of CMMS records and work order history<br/>"
            
            summary_text = f"""
            <b>Overall RMI Score: {overall_score.final_score:.2f} / 5.00</b><br/>
            <b>Maturity Level:</b> {maturity_level}<br/><br/>
            
            This assessment evaluated {assessment.site_name}'s maintenance and reliability practices 
            across three critical pillars: People, Process, and Technology. The assessment included:<br/>
            • <b>{response_count} interview responses</b> from {unique_respondents} different role categories<br/>
            • <b>{observation_count} field observations</b> during job shadowing and facility walkthrough<br/>
            {cmms_summary}<br/>
            
            The audit was conducted over {(datetime.now() - assessment.assessment_date).days} days 
            from {assessment.assessment_date.strftime('%B %d, %Y')} to {datetime.now().strftime('%B %d, %Y')}.
            """
            story.append(Paragraph(summary_text, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Pillar Scores Table - Keep together on same page
        pillar_section = []
        pillar_section.append(Paragraph("Pillar Breakdown", heading_style))
        
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
        # Consulting-Style Table: No vertical lines, clean horizontal separators
        table.setStyle(TableStyle([
            # Header Styling
            ('LINEABOVE', (0, 0), (-1, 0), 2, ConsultingTheme.PRIMARY),  # Thick top line
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, ConsultingTheme.SECONDARY),  # Header separator
            ('BACKGROUND', (0, 0), (-1, 0), ConsultingTheme.BG_GREY),
            ('TEXTCOLOR', (0, 0), (-1, 0), ConsultingTheme.SECONDARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body Styling
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, ConsultingTheme.LIGHT_GREY),  # Thin row separators
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Left-align for cleaner look
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        pillar_section.append(table)
        
        # Keep the pillar table with its heading
        story.append(KeepTogether(pillar_section))
        story.append(Spacer(1, 0.5*inch))
        
        # Generate and add radar chart - Keep together on same page
        chart_image = self._generate_radar_chart(pillar_scores)
        if chart_image:
            chart_section = []
            chart_section.append(Paragraph("Maturity Profile", heading_style))
            chart_section.append(Image(chart_image, width=5*inch, height=4*inch))
            story.append(KeepTogether(chart_section))
            story.append(Spacer(1, 0.3*inch))
        
        story.append(PageBreak())
        
        # Key Findings - Keep together on same page
        findings_section = []
        findings_section.append(Paragraph("Key Findings", heading_style))
        findings = self._generate_findings(assessment_id, pillar_scores)
        for finding in findings:
            findings_section.append(Paragraph(f"• {finding}", styles['Normal']))
            findings_section.append(Spacer(1, 0.1*inch))
        
        story.append(KeepTogether(findings_section))
        story.append(Spacer(1, 0.3*inch))
        
        # CMMS Data Analysis Section (if available)
        if cmms_analyses:
            story.append(PageBreak())
            story.append(Paragraph("CMMS Data Analysis", heading_style))
            self._add_cmms_section(story, cmms_analyses, styles, insight_style)
        
        # Critical Observations from Field Work
        story.append(PageBreak())
        story.append(Paragraph("Critical Field Observations", heading_style))
        self._add_observations_section(story, assessment_id, styles)
        
        # Detailed Interview Responses by Pillar
        story.append(PageBreak())
        story.append(Paragraph("Interview Response Details", heading_style))
        self._add_detailed_responses_section(story, assessment_id, styles, heading_style)
        
        # Roadmap - Visual Timeline with Insight Box
        story.append(PageBreak())
        story.append(Paragraph("Strategic Roadmap", heading_style))
        
        # Sort pillars to identify priority areas
        sorted_pillars = sorted(pillar_scores, key=lambda x: x.final_score)
        weakest_pillar = sorted_pillars[0].pillar.value.title()
        
        # Add dynamic insight based on weakest pillar
        priority_focus = {
            "People": "talent development and knowledge transfer",
            "Process": "planning discipline and work management rigor",
            "Technology": "data quality and system utilization"
        }
        focus_area = priority_focus.get(weakest_pillar, "foundational capabilities")
        
        insight_text = f"<b>Strategic Priority:</b> Primary focus on <b>{weakest_pillar}</b> pillar improvements ({focus_area}). Execute quick wins in first 30 days while building organizational capability for sustainable transformation."
        story.append(Paragraph(insight_text, insight_style))
        story.append(Spacer(1, 0.15*inch))
        
        roadmap = self._generate_roadmap(pillar_scores)
        
        for phase, actions in roadmap.items():
            # Create colored phase header with timeline indicator
            phase_color = ConsultingTheme.PRIMARY if '30-Day' in phase else ConsultingTheme.ACCENT if '60-Day' in phase else ConsultingTheme.MID_GREY
            phase_style = ParagraphStyle(
                'PhaseHeader',
                parent=styles['Heading3'],
                textColor=phase_color,
                fontSize=13,
                fontName='Helvetica-Bold',
                spaceAfter=6
            )
            
            # Keep each phase together on same page
            phase_section = []
            
            # Phase header with count
            phase_header = f"{phase} — {len(actions)} Actions"
            phase_section.append(Paragraph(phase_header, phase_style))
            
            # Action items with improved formatting
            action_style = ParagraphStyle(
                'ActionItem',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=15,
                bulletIndent=5,
                spaceAfter=4
            )
            
            for i, action in enumerate(actions, 1):
                action_text = f"<b>{i}.</b> {action}"
                phase_section.append(Paragraph(action_text, action_style))
            
            story.append(KeepTogether(phase_section))
            story.append(Spacer(1, 0.25*inch))
        
        # Add implementation note
        note_style = ParagraphStyle(
            'ImplementationNote',
            parent=styles['Normal'],
            fontSize=9,
            textColor=ConsultingTheme.MID_GREY,
            leftIndent=10,
            rightIndent=10,
            borderPadding=8
        )
        implementation_note = (
            "<i>Note: Roadmap prioritizes actions based on current maturity assessment. "
            "Assign executive sponsors to each phase, establish weekly progress reviews, "
            "and adjust timeline based on resource availability and organizational readiness.</i>"
        )
        story.append(Paragraph(implementation_note, note_style))
        
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
        """Generate consulting-grade radar chart with benchmark"""
        if not pillar_scores:
            return None
        
        categories = []
        values = []
        
        for score in pillar_scores:
            categories.append(score.pillar.value.title())
            values.append(score.final_score)
        
        # Create professional radar chart
        fig, ax = plt.subplots(figsize=(7, 6), subplot_kw=dict(projection='polar'))
        
        # Remove chart junk
        ax.set_facecolor('#FAFAFA')
        ax.spines['polar'].set_visible(False)
        
        # Number of variables
        num_vars = len(categories)
        angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
        values_plot = values + values[:1]  # Complete the circle
        angles_plot = angles + angles[:1]
        
        # Industry Benchmark (3.0 average across all pillars)
        benchmark_values = [3.0] * num_vars  # Industry average baseline
        benchmark_plot = benchmark_values + benchmark_values[:1]
        
        # Plot benchmark first (background)
        ax.plot(angles_plot, benchmark_plot, linestyle='--', linewidth=1.5, 
                color='#95A5A6', label='Industry Avg (3.0)', zorder=1)
        ax.fill(angles_plot, benchmark_plot, alpha=0.1, color='#95A5A6', zorder=1)
        
        # Plot actual values (foreground) - using actual RMI scores
        ax.plot(angles_plot, values_plot, 'o-', linewidth=2.5, 
                color='#1A4D8F', markerfacecolor='white', markersize=8, 
                markeredgewidth=2, markeredgecolor='#1A4D8F', zorder=2)
        ax.fill(angles_plot, values_plot, alpha=0.3, color='#3498DB', zorder=2)
        
        # Styling
        ax.set_xticks(angles)
        ax.set_xticklabels(categories, size=11, weight='bold')
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(['1', '2', '3', '4', '5'], size=9, color='#666666')
        ax.grid(color='#E0E0E0', linestyle='--', linewidth=0.5)
        
        # Legend
        plt.legend(loc='upper right', frameon=False, fontsize=9, bbox_to_anchor=(1.15, 1.1))
        
        plt.title('RMI Maturity Profile', size=14, weight='bold', pad=15, color='#2A2A2A')
        
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
        """Generate key findings based on scores and actual responses"""
        findings = []
        
        # Get actual low-scoring responses for context
        critical_responses = self.db.query(QuestionResponse, QuestionBank).join(
            QuestionBank, QuestionResponse.question_id == QuestionBank.id
        ).filter(
            QuestionResponse.assessment_id == assessment_id,
            QuestionResponse.is_draft == False,
            QuestionResponse.is_na == False,
            QuestionResponse.numeric_score <= 2.5
        ).all()
        
        # Get high severity observations count
        high_severity_obs = self.db.query(Observation).filter(
            Observation.assessment_id == assessment_id,
            Observation.severity.ilike('%high%')
        ).count()
        
        # Count critical responses per pillar
        pillar_issue_counts = {}
        pillar_specific_issues = {}
        
        for response, question in critical_responses:
            pillar = question.pillar
            if pillar not in pillar_issue_counts:
                pillar_issue_counts[pillar] = 0
                pillar_specific_issues[pillar] = []
            pillar_issue_counts[pillar] += 1
            if len(pillar_specific_issues[pillar]) < 3:  # Store top 3 specific issues
                pillar_specific_issues[pillar].append({
                    'code': question.question_code,
                    'score': response.numeric_score,
                    'evidence': response.evidence_notes
                })
        
        # Add pillar-level findings with meaningful context
        for score in pillar_scores:
            pillar_name = score.pillar.value.title()
            critical_count = pillar_issue_counts.get(score.pillar, 0)
            
            if score.final_score < 2.5:
                finding = f"<b>{pillar_name} Pillar (Score: {score.final_score:.2f}):</b> CRITICAL - Significant gaps identified with {critical_count} critical deficiencies. "
                
                # Add pillar-specific insights
                if score.pillar == PillarType.PEOPLE:
                    finding += "Key concerns include: inadequate training programs, unclear safety authority, limited technician development pathways, and insufficient cross-training. "
                elif score.pillar == PillarType.PROCESS:
                    finding += "Key concerns include: inconsistent LOTO procedures, poor work order planning quality, lack of standardized job procedures, and weak preventive maintenance scheduling. "
                elif score.pillar == PillarType.TECHNOLOGY:
                    finding += "Key concerns include: non-compliant failure taxonomy (ISO 14224), poor CMMS data quality, inadequate reliability metrics, and limited use of predictive technologies. "
                
                finding += "Immediate intervention required to prevent reliability degradation."
                findings.append(finding)
                
            elif score.final_score < 3.5:
                finding = f"<b>{pillar_name} Pillar (Score: {score.final_score:.2f}):</b> Emerging practices with improvement opportunities. "
                
                if critical_count > 0:
                    finding += f"{critical_count} areas require attention. "
                
                if score.pillar == PillarType.PEOPLE:
                    finding += "Focus on formalizing training programs, establishing competency frameworks, and building leadership capability."
                elif score.pillar == PillarType.PROCESS:
                    finding += "Focus on standardizing procedures, improving planning & scheduling maturity, and implementing work management best practices."
                elif score.pillar == PillarType.TECHNOLOGY:
                    finding += "Focus on improving data quality, implementing failure code taxonomy, and establishing baseline reliability metrics."
                
                findings.append(finding)
                
            elif score.final_score < 4.5:
                findings.append(
                    f"<b>{pillar_name} Pillar (Score: {score.final_score:.2f}):</b> Solid preventive foundation in place. "
                    f"Ready to advance toward predictive maintenance and reliability-centered strategies. "
                    f"Continue building on current strengths while addressing remaining gaps."
                )
            else:
                findings.append(
                    f"<b>{pillar_name} Pillar (Score: {score.final_score:.2f}):</b> EXCELLENT - World-class practices observed. "
                    f"Prescriptive maintenance capabilities in place. Focus on sustainability, knowledge transfer, and continuous improvement."
                )
        
        # Add observation-based findings
        if high_severity_obs > 0:
            findings.append(
                f"<b>Field Observations:</b> {high_severity_obs} high-severity issues identified "
                f"during job shadowing and facility walkthrough. Immediate attention required. "
                f"See 'Critical Field Observations' section for detailed findings."
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
        
        # Add specific technical findings if Technology pillar is weak
        tech_score = next((s for s in pillar_scores if s.pillar == PillarType.TECHNOLOGY), None)
        if tech_score and tech_score.final_score < 3.0:
            findings.append(
                "<b>Data Quality:</b> CMMS data quality issues detected. "
                "Generic closure codes and lack of failure taxonomy prevent effective "
                "root cause analysis and reliability improvement initiatives."
            )
        
        return findings
    
    def _generate_roadmap(self, pillar_scores: List[Score]) -> Dict[str, List[str]]:
        """Generate prioritized 30/60/90 day roadmap based on actual scores and gaps"""
        roadmap = {
            "30-Day Quick Wins (Foundation)": [],
            "60-Day Capability Building (Implementation)": [],
            "90-Day Strategic Initiatives (Transformation)": []
        }
        
        # Sort pillars by score to prioritize weakest areas
        sorted_pillars = sorted(pillar_scores, key=lambda x: x.final_score)
        weakest = sorted_pillars[0]
        second_weakest = sorted_pillars[1] if len(sorted_pillars) > 1 else None
        
        # Define pillar-specific actions by maturity level
        people_actions = {
            "quick_wins": [
                "Conduct skills matrix assessment for all maintenance technicians",
                "Launch weekly 15-minute reliability toolbox talks",
                "Establish knowledge transfer sessions (senior to junior tech pairing)"
            ],
            "capability": [
                "Develop competency-based training program with certification paths",
                "Create succession planning framework for critical maintenance roles",
                "Implement formal mentorship program with quarterly reviews"
            ],
            "strategic": [
                "Launch Reliability Technician certification program (in-house or external)",
                "Establish career development pathways with skills-based advancement",
                "Create cross-functional reliability working groups (operations + maintenance)"
            ]
        }
        
        process_actions = {
            "quick_wins": [
                "Audit 100 most recent work orders for planning/execution quality",
                "Create standardized job plans for top 20 critical PM tasks",
                "Implement daily 5-minute production-maintenance coordination standup"
            ],
            "capability": [
                "Deploy work order planning checklist with mandatory planner approval",
                "Establish PM optimization reviews using RCM/PMO methodology",
                "Implement backlog management process with priority ranking system"
            ],
            "strategic": [
                "Transition to Reliability-Centered Maintenance (RCM) for critical assets",
                "Deploy formal Planning & Scheduling discipline (2-week forward schedule)",
                "Implement shutdown/turnaround planning process with critical path analysis"
            ]
        }
        
        technology_actions = {
            "quick_wins": [
                "Audit CMMS data quality: closure codes, failure modes, cause codes",
                "Create 'Bad Actor' dashboard (Top 10 failing assets by downtime)",
                "Establish weekly CMMS data quality scorecard and review"
            ],
            "capability": [
                "Redesign CMMS failure taxonomy aligned with ISO 14224 standards",
                "Implement mobile CMMS access for field technicians (real-time updates)",
                "Deploy work order data completeness enforcement (mandatory fields)"
            ],
            "strategic": [
                "Launch predictive maintenance pilot program (vibration/thermography)",
                "Implement asset criticality analysis and risk-based maintenance strategy",
                "Deploy automated reliability metrics dashboard for leadership visibility"
            ]
        }
        
        pillar_action_map = {
            PillarType.PEOPLE: people_actions,
            PillarType.PROCESS: process_actions,
            PillarType.TECHNOLOGY: technology_actions
        }
        
        # Prioritize actions based on weakest pillars
        # 30-Day: Focus heavily on weakest pillar + one action from second weakest
        if weakest.pillar in pillar_action_map:
            roadmap["30-Day Quick Wins (Foundation)"].extend(pillar_action_map[weakest.pillar]["quick_wins"])
        if second_weakest and second_weakest.pillar in pillar_action_map:
            roadmap["30-Day Quick Wins (Foundation)"].append(pillar_action_map[second_weakest.pillar]["quick_wins"][0])
        
        # 60-Day: Build capability across weak pillars
        for pillar_score in sorted_pillars[:2]:  # Focus on two weakest
            if pillar_score.pillar in pillar_action_map:
                roadmap["60-Day Capability Building (Implementation)"].extend(
                    pillar_action_map[pillar_score.pillar]["capability"][:2]  # Top 2 capability actions
                )
        
        # 90-Day: Strategic initiatives across all pillars with emphasis on integration
        for pillar_score in sorted_pillars:
            if pillar_score.pillar in pillar_action_map:
                roadmap["90-Day Strategic Initiatives (Transformation)"].append(
                    pillar_action_map[pillar_score.pillar]["strategic"][0]  # Top strategic action per pillar
                )
        
        # Add integration/culture actions for 90-day (cross-pillar)
        roadmap["90-Day Strategic Initiatives (Transformation)"].extend([
            "Establish Reliability Center of Excellence (RCM experts, data analysts, trainers)",
            "Implement executive reliability scorecard with leading/lagging KPIs"
        ])
        
        return roadmap
    
    def _add_cmms_section(self, story: list, cmms_analyses, styles, insight_style):
        """Add CMMS data analysis section to report"""
        if not cmms_analyses:
            return
        
        # Get latest analysis (most recent upload)
        latest = cmms_analyses[0]
        metrics = latest.metrics or {}
        
        # Extract key metrics
        reactive_ratio_data = metrics.get('reactive_ratio', {})
        reactive_ratio = reactive_ratio_data.get('reactive_ratio', 0)
        reactive_count = reactive_ratio_data.get('reactive_work_orders', 0)
        preventive_count = reactive_ratio_data.get('preventive_work_orders', 0)
        total_wos = reactive_ratio_data.get('total_work_orders', 0)
        severity = reactive_ratio_data.get('severity', 'Unknown')
        
        data_quality_data = metrics.get('data_quality', {})
        graveyard_pct = data_quality_data.get('graveyard_percentage', 0)
        data_quality = 100 - graveyard_pct if isinstance(graveyard_pct, (int, float)) else 0
        poor_closures = data_quality_data.get('poor_quality_closures', 0)
        
        work_dist = metrics.get('work_type_distribution', {}).get('distribution', {})
        
        # Summary paragraph
        summary = f"""
        <b>Work Order Analysis:</b> {total_wos} work orders analyzed from CMMS export 
        ({latest.data_source or 'uploaded file'}). Analysis completed on 
        {latest.analyzed_at.strftime('%B %d, %Y') if latest.analyzed_at else 'N/A'}.<br/><br/>
        
        <b>Key Performance Indicators:</b><br/>
        • <b>Reactive Ratio: {reactive_ratio}%</b> - {severity}<br/>
        • <b>Data Quality: {data_quality:.1f}%</b> ({poor_closures} work orders with generic/missing closure codes)<br/>
        • <b>Work Mix:</b> {preventive_count} preventive vs {reactive_count} reactive work orders<br/>
        """
        story.append(Paragraph(summary, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Work Type Distribution Table
        if work_dist:
            story.append(Paragraph("Work Type Distribution", styles['Heading3']))
            table_data = [['Work Type', 'Count', 'Percentage']]
            
            work_pcts = metrics.get('work_type_distribution', {}).get('percentages', {})
            for work_type, count in work_dist.items():
                pct = work_pcts.get(work_type, 0)
                table_data.append([work_type, str(count), f"{pct:.1f}%"])
            
            table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 2, ConsultingTheme.PRIMARY),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, ConsultingTheme.SECONDARY),
                ('BACKGROUND', (0, 0), (-1, 0), ConsultingTheme.BG_GREY),
                ('TEXTCOLOR', (0, 0), (-1, 0), ConsultingTheme.SECONDARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, ConsultingTheme.LIGHT_GREY),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2*inch))
        
        # Insights and Recommendations
        insights = []
        if reactive_ratio > 40:
            insights.append("⚠️ <b>HIGH REACTIVE MAINTENANCE:</b> Over 40% of work is reactive. Prioritize PM program improvements and failure analysis to reduce emergency work.")
        elif reactive_ratio > 25:
            insights.append("⚠️ <b>MODERATE REACTIVE LOAD:</b> 25-40% reactive work detected. Strengthen preventive maintenance scheduling and equipment monitoring.")
        else:
            insights.append("✓ <b>GOOD REACTIVE CONTROL:</b> Reactive ratio under 25% indicates effective preventive maintenance practices.")
        
        if data_quality < 60:
            insights.append("⚠️ <b>POOR DATA QUALITY:</b> Over 40% of work orders have generic closure codes. Implement data quality standards and CMMS training for technicians.")
        elif data_quality < 75:
            insights.append("⚠️ <b>DATA QUALITY CONCERNS:</b> 25-40% of closures lack detail. Improve work order completion processes and enforce closure code requirements.")
        else:
            insights.append("✓ <b>ACCEPTABLE DATA QUALITY:</b> Most work orders contain detailed closure information supporting reliability analysis.")
        
        if insights:
            story.append(Paragraph("CMMS Performance Insights", styles['Heading3']))
            for insight in insights:
                story.append(Paragraph(insight, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        # Impact on Technology Score
        tech_impact = f"""
        <b>Technology Pillar Impact:</b> CMMS data contributes 20% to the Technology pillar score 
        (60% interviews + 20% observations + 20% CMMS). The reactive ratio and data quality metrics 
        are scored on a 1-5 scale and averaged. Low CMMS scores (<2.0) can cap the overall Technology 
        pillar at 3.5 due to weakest-link logic.
        """
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(tech_impact, insight_style))
    
    def _add_observations_section(self, story: list, assessment_id: int, styles):
        """Add detailed field observations to report"""
        observations = self.db.query(Observation).filter(
            Observation.assessment_id == assessment_id
        ).order_by(Observation.severity.desc(), Observation.observed_at).all()
        
        if not observations:
            story.append(Paragraph("No field observations recorded for this assessment.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            return
        
        # Group by severity
        critical_obs = [o for o in observations if o.severity and 'high' in o.severity.lower()]
        major_obs = [o for o in observations if o.severity and 'medium' in o.severity.lower()]
        minor_obs = [o for o in observations if o.severity and 'low' in o.severity.lower()]
        
        severity_style = ParagraphStyle(
            'Severity',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#c0392b'),
            spaceAfter=8
        )
        
        # Critical/High Observations
        if critical_obs:
            story.append(Paragraph(f"<b>HIGH SEVERITY ({len(critical_obs)} findings)</b>", severity_style))
            for obs in critical_obs:
                obs_section = []
                obs_text = f"""
                <b>{obs.observation_title}</b><br/>
                <i>Pillar: {obs.pillar.value.title() if obs.pillar else 'N/A'} | 
                Type: {obs.observation_type or 'General'} | 
                Location: {obs.location or 'Not specified'}</i><br/>
                <b>Finding:</b> {obs.observation_notes}<br/>
                <i>Observed: {obs.observed_at.strftime('%B %d, %Y at %I:%M %p') if obs.observed_at else 'Date not recorded'}</i>
                """
                obs_section.append(Paragraph(obs_text, styles['Normal']))
                obs_section.append(Spacer(1, 0.15*inch))
                story.append(KeepTogether(obs_section))
        
        # Medium/Major Observations
        if major_obs:
            story.append(Paragraph(f"<b>MEDIUM SEVERITY ({len(major_obs)} findings)</b>", severity_style))
            for obs in major_obs[:5]:  # Limit to top 5 for report brevity
                obs_section = []
                obs_text = f"""
                <b>{obs.observation_title}</b><br/>
                <i>Pillar: {obs.pillar.value.title() if obs.pillar else 'N/A'}</i><br/>
                {obs.observation_notes[:300]}{'...' if len(obs.observation_notes) > 300 else ''}
                """
                obs_section.append(Paragraph(obs_text, styles['Normal']))
                obs_section.append(Spacer(1, 0.1*inch))
                story.append(KeepTogether(obs_section))
            if len(major_obs) > 5:
                story.append(Paragraph(f"<i>...and {len(major_obs) - 5} additional medium severity findings</i>", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        # Low/Minor Observations
        if minor_obs:
            story.append(Paragraph(f"<b>LOW SEVERITY ({len(minor_obs)} findings)</b>", styles['Normal']))
            story.append(Paragraph(f"<i>{len(minor_obs)} minor observations documented - see full technical report for details</i>", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_detailed_responses_section(self, story: list, assessment_id: int, styles, heading_style):
        """Add detailed interview responses organized by pillar"""
        
        # Get all responses with question details (include drafts as they represent actual interview data)
        responses = self.db.query(QuestionResponse, QuestionBank).join(
            QuestionBank, QuestionResponse.question_id == QuestionBank.id
        ).filter(
            QuestionResponse.assessment_id == assessment_id,
            QuestionResponse.is_na == False  # Exclude N/A, but INCLUDE drafts
        ).order_by(QuestionBank.pillar, QuestionBank.question_code).all()
        
        if not responses:
            story.append(Paragraph("No interview responses recorded for this assessment.", styles['Normal']))
            return
        
        # Group by pillar
        pillar_responses = {}
        for response, question in responses:
            pillar = question.pillar.value.lower() if question.pillar else 'other'
            if pillar not in pillar_responses:
                pillar_responses[pillar] = []
            pillar_responses[pillar].append((response, question))
        
        # Create sections for each pillar
        for pillar in ['people', 'process', 'technology']:
            if pillar not in pillar_responses:
                continue
            
            pillar_title = pillar.title()
            story.append(Paragraph(f"{pillar_title} Pillar Responses", heading_style))
            
            for response, question in pillar_responses[pillar]:
                # Keep each Q&A together on same page
                qa_section = []
                
                # Question header
                question_header = f"""
                <b>[{question.question_code}] {question.question_text}</b><br/>
                <i>Target Role: {question.target_role.value if question.target_role else 'N/A'} | 
                Weight: {question.weight} | 
                Evidence Required: {'Yes' if question.evidence_required else 'No'}</i>
                """
                qa_section.append(Paragraph(question_header, styles['Normal']))
                qa_section.append(Spacer(1, 0.05*inch))
                
                # Response details
                response_text = f"""
                <b>Response:</b> {response.response_value or 'No response provided'}<br/>
                """
                
                if response.numeric_score is not None:
                    response_text += f"<b>Score:</b> {response.numeric_score} / 5<br/>"
                
                if response.evidence_notes:
                    response_text += f"<b>Evidence/Notes:</b> {response.evidence_notes}<br/>"
                
                # Note: respondent_role is stored via target_role in QuestionBank, not in QuestionResponse
                # if response.respondent_id:
                #     response_text += f"<i>Respondent ID: {response.respondent_id}</i><br/>"
                
                if response.answered_at:
                    response_text += f"<i>Answered: {response.answered_at.strftime('%B %d, %Y')}</i>"
                
                qa_section.append(Paragraph(response_text, styles['Normal']))
                qa_section.append(Spacer(1, 0.15*inch))
                
                story.append(KeepTogether(qa_section))
            
            story.append(Spacer(1, 0.2*inch))
    
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

"""
v2 Executive Report Generator.

Reads from AssessmentV2 + SubdomainScore + Domain/Subdomain, and produces an
executive PDF using reportlab. Mirrors the v1 ReportGenerator's structure
without depending on v1 tables.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session  # noqa: E402

from models import Report  # noqa: E402  -- reused for the report registry row
from models_v2 import (  # noqa: E402
    AssessmentV2,
    Domain,
    ResponseV2,
    Subdomain,
    SubdomainScore,
)

logger = logging.getLogger(__name__)


_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(name: str) -> str:
    return _FILENAME_RE.sub("_", name or "").strip("._-") or "unknown"


def _maturity_color(score: float):
    if score < 2.0:
        return colors.HexColor("#E74C3C")
    if score < 3.0:
        return colors.HexColor("#E67E22")
    if score < 4.0:
        return colors.HexColor("#F39C12")
    if score < 4.5:
        return colors.HexColor("#27AE60")
    return colors.HexColor("#16A085")


def _maturity_label(score: float) -> str:
    if score < 2.0:
        return "Level 1 - Reactive"
    if score < 3.0:
        return "Level 2 - Emerging Preventive"
    if score < 4.0:
        return "Level 3 - Preventive"
    if score < 4.5:
        return "Level 4 - Predictive"
    return "Level 5 - Prescriptive"


class ReportGeneratorV2:
    PRIMARY = colors.HexColor("#1A4D8F")
    DARK = colors.HexColor("#2C3E50")
    MID = colors.HexColor("#7F8C8D")
    BG = colors.HexColor("#ECF0F1")

    def __init__(self, db: Session, output_dir: str = "./reports") -> None:
        self.db = db
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate(self, *, assessment_id: int, generated_by: int) -> str:
        a = self.db.query(AssessmentV2).filter(AssessmentV2.id == assessment_id).first()
        if not a:
            raise ValueError(f"Assessment {assessment_id} not found")

        subdomain_scores = (
            self.db.query(SubdomainScore, Subdomain, Domain)
            .join(Subdomain, SubdomainScore.subdomain_id == Subdomain.id)
            .join(Domain, Subdomain.domain_id == Domain.id)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .order_by(Domain.display_order, Subdomain.display_order)
            .all()
        )

        domain_rollup = self._rollup_domains(subdomain_scores)
        overall = a.overall_rmi if a.overall_rmi is not None else (
            sum(d["score"] for d in domain_rollup.values()) / max(len(domain_rollup), 1)
        )

        filename = (
            f"RMI_Audit_Report_{_slug(a.client_name)}_{_slug(a.site_name)}_"
            f"{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        )
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=self.PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=0.3 * inch,
        )
        h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=self.DARK, spaceAfter=0.1 * inch)
        body = ParagraphStyle("Body", parent=styles["BodyText"], textColor=self.DARK, fontSize=10, leading=14)
        small = ParagraphStyle("Small", parent=body, fontSize=8, textColor=self.MID)

        story = []
        story.extend(self._cover(a, overall, title_style, body, small))
        story.append(PageBreak())
        story.extend(self._domain_table(domain_rollup, h2, body))
        story.extend(self._radar(domain_rollup))
        story.append(PageBreak())
        story.extend(self._subdomain_breakdown(subdomain_scores, h2, body, small))
        story.append(PageBreak())
        story.extend(self._evidence_summary(assessment_id, h2, body, small))

        doc.build(story)

        # Register in the existing reports table so /report/download keeps working
        registry = Report(
            assessment_id=assessment_id,
            report_type="executive_v2",
            title=f"Executive RMI Report — {a.client_name} {a.site_name}",
            content=json.dumps({
                "overall_rmi": overall,
                "domains": domain_rollup,
            }),
            file_path=filepath,
            generated_by=generated_by,
        )
        self.db.add(registry)
        self.db.commit()
        return filepath

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _rollup_domains(self, scored_rows) -> Dict[str, dict]:
        result: Dict[str, dict] = {}
        per_domain: Dict[str, List[float]] = {}
        for sc, sd, dom in scored_rows:
            per_domain.setdefault(dom.code, []).append(float(sc.final_score or 0))
            result.setdefault(dom.code, {"name": dom.name, "score": 0.0, "subdomains": []})
            result[dom.code]["subdomains"].append({
                "code": sd.code,
                "name": sd.name,
                "score": float(sc.final_score or 0),
                "cap_applied": bool(getattr(sc, "cap_applied", False)),
                "cap_reason": getattr(sc, "cap_reason", None),
            })
        for code, scores in per_domain.items():
            result[code]["score"] = sum(scores) / max(len(scores), 1)
        return result

    def _cover(self, a: AssessmentV2, overall: float, title_style, body, small) -> list:
        story = []
        story.append(Paragraph("RMI Executive Report", title_style))
        story.append(Spacer(1, 0.3 * inch))
        meta = [
            ["Client", a.client_name or ""],
            ["Site", a.site_name or ""],
            ["Assessment Mode", a.assessment_mode.value if a.assessment_mode else ""],
            ["Industry Module", a.industry_module.value if a.industry_module else "—"],
            ["Assessment Date", a.assessment_date.isoformat() if a.assessment_date else ""],
            ["Status", a.status or ""],
            ["Overall RMI", f"{overall:.2f} / 5.00"],
            ["Maturity Level", _maturity_label(overall)],
        ]
        t = Table(meta, colWidths=[2.2 * inch, 4.0 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), self.BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), self.DARK),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4 * inch))
        story.append(Paragraph(
            "Scoring policy, evidence rules, and cap definitions are documented "
            "in SCORING_POLICY.md.",
            small,
        ))
        return story

    def _domain_table(self, rollup: Dict[str, dict], h2, body) -> list:
        story = [Paragraph("Domain Scores", h2)]
        rows = [["Domain", "Score (1-5)", "Maturity"]]
        for code, data in rollup.items():
            score = data["score"]
            rows.append([
                f"{code} — {data['name']}",
                f"{score:.2f}",
                _maturity_label(score),
            ])
        t = Table(rows, colWidths=[3.5 * inch, 1.2 * inch, 2.0 * inch])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        for i, (_, data) in enumerate(rollup.items(), start=1):
            style.append(("TEXTCOLOR", (1, i), (1, i), _maturity_color(data["score"])))
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))
        return story

    def _radar(self, rollup: Dict[str, dict]) -> list:
        if not rollup:
            return []
        labels = list(rollup.keys())
        scores = [rollup[k]["score"] for k in labels]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        scores_closed = scores + scores[:1]
        angles_closed = angles + angles[:1]

        fig = plt.figure(figsize=(6, 6))
        ax = plt.subplot(111, polar=True)
        ax.plot(angles_closed, scores_closed, color="#1A4D8F", linewidth=2)
        ax.fill(angles_closed, scores_closed, color="#1A4D8F", alpha=0.15)
        ax.set_xticks(angles)
        ax.set_xticklabels(labels)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_ylim(0, 5)
        ax.set_title("Domain Maturity", pad=18)
        buf = io.BytesIO()
        plt.savefig(buf, format="PNG", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return [Image(buf, width=4.5 * inch, height=4.5 * inch)]

    def _subdomain_breakdown(self, scored_rows, h2, body, small) -> list:
        story = [Paragraph("Subdomain Detail", h2)]
        rows = [["Code", "Subdomain", "Score", "Cap"]]
        for sc, sd, dom in scored_rows:
            cap_note = "—"
            if getattr(sc, "cap_applied", False):
                cap_note = (getattr(sc, "cap_reason", None) or "applied")[:60]
            rows.append([sd.code, f"{dom.code} · {sd.name}", f"{float(sc.final_score or 0):.2f}", cap_note])
        t = Table(rows, colWidths=[0.8 * inch, 3.5 * inch, 0.8 * inch, 1.6 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(t)
        return story

    def _evidence_summary(self, assessment_id: int, h2, body, small) -> list:
        from models_v2 import EvidenceStatus

        rows = self.db.query(ResponseV2).filter(ResponseV2.assessment_id == assessment_id).all()
        story = [Paragraph("Evidence Summary", h2)]
        if not rows:
            story.append(Paragraph("No responses recorded.", body))
            return story
        buckets: Dict[str, int] = {}
        for r in rows:
            key = r.evidence_status.value if r.evidence_status else "unknown"
            buckets[key] = buckets.get(key, 0) + 1

        table_rows = [["Evidence Status", "Count"]]
        for k in [
            EvidenceStatus.NOT_REQUIRED.value,
            EvidenceStatus.PENDING_EVIDENCE.value,
            EvidenceStatus.PENDING_VERIFICATION.value,
            EvidenceStatus.ACCEPTED.value,
            EvidenceStatus.REJECTED.value,
        ]:
            table_rows.append([k, str(buckets.get(k, 0))])

        t = Table(table_rows, colWidths=[3.0 * inch, 1.0 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(
            "Per scoring policy: only ACCEPTED evidence lifts the evidence cap for "
            "questions where evidence is required. PENDING/REJECTED items are capped at 3.",
            small,
        ))
        return story

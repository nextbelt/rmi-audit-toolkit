"""
v2 Executive Report Generator — client-grade deliverable.

Self-contained: reads only v2 tables (AssessmentV2 / SubdomainScore / Domain /
Subdomain / CMMSUploadV2) and the live v2 engines. Produces a branded executive
PDF with both the 3-pillar (People / Process / Technology) rollup AND the native
5-domain view, an executive summary, data-driven findings, a CMMS data section,
cultural blind spots, ISO 55001 readiness, a 30/60/90-day roadmap, and an
evidence summary — with firm branding (logo, colors, footer, page numbers)
driven entirely by config so the report can be rebranded without code changes.
"""
from __future__ import annotations

import io
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
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session  # noqa: E402

from config import settings  # noqa: E402
from models import Report  # noqa: E402  -- report registry row (reused for /report/download)
from models_v2 import (  # noqa: E402
    AssessmentV2,
    CMMSUploadV2,
    Domain,
    ResponseV2,
    Subdomain,
    SubdomainScore,
)
from scoring_engine_v2 import ScoringEngineV2  # noqa: E402

logger = logging.getLogger(__name__)

_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

# 5 domains → 3 client-facing pillars
PILLAR_MAP: Dict[str, List[str]] = {
    "People": ["WC", "LC"],       # Workforce Capability + Leadership & Culture
    "Process": ["WM", "SG"],      # Work Management + Strategy & Governance
    "Technology": ["AI"],         # Asset Information
}
INDUSTRY_NAMES = {
    "MFG": "Manufacturing (General)", "FNB": "Food & Beverage", "ONG": "Oil & Gas",
    "MNM": "Mining & Minerals", "UTL": "Utilities", "PHA": "Pharmaceuticals",
}
PILLAR_FOCUS = {
    "People": "workforce competency, leadership commitment, and reliability culture",
    "Process": "planning & scheduling discipline, work execution, and governance",
    "Technology": "CMMS effectiveness, data quality, and analytics-driven decisions",
}

# Curated 30/60/90 actions per domain (used when a weakest-link area is found)
DOMAIN_ROADMAP: Dict[str, Dict[str, List[str]]] = {
    "WC": {
        "30": ["Run a skills-matrix gap analysis for all maintenance roles",
               "Launch weekly reliability toolbox talks"],
        "60": ["Stand up a competency-based training program with certification paths",
               "Formalize knowledge-transfer pairing (senior to junior technicians)"],
        "90": ["Establish a Reliability Technician certification track and career ladder"],
    },
    "LC": {
        "30": ["Publish and brief stop-work authority and safety expectations",
               "Hold a leadership reliability alignment session"],
        "60": ["Define reliability KPIs reviewed by leadership on a fixed cadence",
               "Clarify maintenance org structure and accountability (RACI)"],
        "90": ["Embed a proactive reliability culture program with frontline ownership"],
    },
    "WM": {
        "30": ["Audit the last 100 work orders for planning/execution quality",
               "Create standardized job plans for the top 20 critical PM tasks"],
        "60": ["Deploy a planner-approved work-order planning checklist",
               "Run PM optimization (RCM/PMO) on critical assets; manage backlog by priority"],
        "90": ["Institute a 2-week forward schedule with schedule-compliance KPIs"],
    },
    "AI": {
        "30": ["Audit CMMS data quality (closure codes, failure modes, completeness)",
               "Stand up a Top-10 bad-actor dashboard by downtime"],
        "60": ["Align failure taxonomy to ISO 14224; enforce mandatory WO fields",
               "Enable mobile CMMS capture for field technicians"],
        "90": ["Launch a predictive-maintenance pilot and a leadership reliability dashboard"],
    },
    "SG": {
        "30": ["Draft/ratify a written asset-management policy and objectives",
               "Define the reliability metric set (leading + lagging)"],
        "60": ["Stand up monthly performance reviews against AM objectives",
               "Establish a continuous-improvement (RCA to action) loop"],
        "90": ["Mature toward ISO 55001 alignment with an audited management system"],
    },
}


def _slug(name: str) -> str:
    return _FILENAME_RE.sub("_", name or "").strip("._-") or "unknown"


def _hex(value: str):
    try:
        return colors.HexColor(value)
    except Exception:
        return colors.HexColor("#0E6E62")


def _maturity_label(score: Optional[float]) -> str:
    if score is None:
        return "Not scored"
    if score < 2.0:
        return "Level 1 — Reactive"
    if score < 3.0:
        return "Level 2 — Emerging"
    if score < 3.6:
        return "Level 3 — Systematic"
    if score < 4.3:
        return "Level 4 — Proactive"
    return "Level 5 — Prescriptive"


def _score_color(score: Optional[float]):
    if score is None:
        return colors.HexColor("#9AA5A1")
    if score < 2.0:
        return colors.HexColor("#C0392B")
    if score < 3.0:
        return colors.HexColor("#E67E22")
    if score < 3.6:
        return colors.HexColor("#B8860B")
    if score < 4.3:
        return colors.HexColor("#2F8A6B")
    return colors.HexColor("#16745F")


class ReportGeneratorV2:
    """Branded executive report for a vNext (v2) assessment."""

    def __init__(self, db: Session, output_dir: Optional[str] = None) -> None:
        self.db = db
        self.output_dir = output_dir or settings.REPORT_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.PRIMARY = _hex(settings.BRAND_PRIMARY_HEX)
        self.DARK = _hex(settings.BRAND_DARK_HEX)
        self.ACCENT = _hex(settings.BRAND_ACCENT_HEX)
        self.MID = colors.HexColor("#6B7670")
        self.BG = colors.HexColor("#F1F5F3")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate(self, *, assessment_id: int, generated_by: int) -> str:
        a = self.db.query(AssessmentV2).filter(AssessmentV2.id == assessment_id).first()
        if not a:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Compute the rich scoring view WITHOUT persisting — generating a report
        # must never mutate the assessment's official scores. domain_rollup below
        # reads the persisted SubdomainScores (the scores that were signed off).
        engine = ScoringEngineV2(self.db)
        try:
            scoring = engine.calculate(assessment_id, persist=False)
        except Exception as exc:  # scoring should not hard-fail report generation
            logger.warning("Scoring during report generation failed: %s", exc)
            scoring = {}

        domain_rollup = self._domain_rollup(assessment_id)
        pillar_rollup = self._pillar_rollup(domain_rollup)
        overall = a.overall_rmi
        if overall is None and domain_rollup:
            vals = [d["score"] for d in domain_rollup.values() if d["score"] is not None]
            overall = round(sum(vals) / len(vals), 2) if vals else None

        benchmark = self._safe_benchmark(assessment_id)
        cmms_uploads = (
            self.db.query(CMMSUploadV2)
            .filter(CMMSUploadV2.assessment_id == assessment_id,
                    CMMSUploadV2.status == "processed")
            .order_by(CMMSUploadV2.uploaded_at.desc())
            .all()
        )

        styles = self._styles()
        filename = (
            f"RMI_Audit_Report_{_slug(a.client_name)}_{_slug(a.site_name)}_"
            f"{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        )
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath, pagesize=letter,
            topMargin=0.9 * inch, bottomMargin=0.8 * inch,
            leftMargin=0.85 * inch, rightMargin=0.85 * inch,
            title=f"RMI Executive Report — {a.client_name} {a.site_name}",
            author=settings.FIRM_NAME,
        )

        story: list = []
        story += self._cover(a, overall, styles)
        story.append(PageBreak())
        story += self._exec_summary(a, overall, scoring, cmms_uploads, styles)
        story += self._pillar_section(pillar_rollup, styles)
        story.append(PageBreak())
        story += self._domain_section(domain_rollup, benchmark, styles)
        story += self._subdomain_section(assessment_id, styles)
        story.append(PageBreak())
        story += self._findings_section(domain_rollup, scoring, styles)
        if cmms_uploads:
            story += self._cmms_section(cmms_uploads, styles)
        story += self._blind_spot_section(scoring, styles)
        story += self._roadmap_section(domain_rollup, styles)
        story += self._evidence_section(assessment_id, scoring, styles)

        doc.build(story, onFirstPage=self._page_furniture, onLaterPages=self._page_furniture)

        registry = Report(
            assessment_id=assessment_id,
            report_type="executive_v2",
            title=f"Executive RMI Report — {a.client_name} {a.site_name}",
            content={
                "overall_rmi": overall,
                "domains": {k: v["score"] for k, v in domain_rollup.items()},
                "pillars": {k: v["score"] for k, v in pillar_rollup.items()},
            },
            file_path=filepath,
            generated_by=generated_by,
        )
        self.db.add(registry)
        self.db.commit()
        return filepath

    # ------------------------------------------------------------------
    # Page furniture (header + footer + page numbers)
    # ------------------------------------------------------------------

    def _page_furniture(self, canvas, doc) -> None:
        canvas.saveState()
        w, h = letter
        # Header rule + firm name
        canvas.setStrokeColor(self.PRIMARY)
        canvas.setLineWidth(0.75)
        canvas.line(0.85 * inch, h - 0.6 * inch, w - 0.85 * inch, h - 0.6 * inch)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(self.PRIMARY)
        canvas.drawString(0.85 * inch, h - 0.52 * inch, settings.FIRM_NAME.upper())
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(self.MID)
        canvas.drawRightString(w - 0.85 * inch, h - 0.52 * inch,
                               "Reliability Maturity Index — Executive Audit")
        # Footer
        canvas.setStrokeColor(colors.HexColor("#D8E0DC"))
        canvas.setLineWidth(0.5)
        canvas.line(0.85 * inch, 0.62 * inch, w - 0.85 * inch, 0.62 * inch)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(self.MID)
        canvas.drawString(0.85 * inch, 0.46 * inch, settings.REPORT_CONFIDENTIAL_LABEL)
        canvas.drawCentredString(w / 2.0, 0.46 * inch, settings.FIRM_WEBSITE)
        canvas.drawRightString(w - 0.85 * inch, 0.46 * inch, f"Page {doc.page}")
        canvas.restoreState()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _styles(self) -> dict:
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle("Title", parent=base["Heading1"], fontSize=26,
                                    textColor=self.PRIMARY, alignment=TA_CENTER, leading=30,
                                    spaceAfter=6),
            "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontSize=13,
                                       textColor=self.DARK, alignment=TA_CENTER, leading=18),
            "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=15,
                                 textColor=self.PRIMARY, spaceBefore=14, spaceAfter=6),
            "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=11.5,
                                 textColor=self.DARK, spaceBefore=8, spaceAfter=4),
            "body": ParagraphStyle("Body", parent=base["BodyText"], fontSize=9.5,
                                   textColor=self.DARK, leading=14, alignment=TA_LEFT),
            "small": ParagraphStyle("Small", parent=base["BodyText"], fontSize=8,
                                    textColor=self.MID, leading=11),
            "callout": ParagraphStyle("Callout", parent=base["BodyText"], fontSize=10,
                                      textColor=self.DARK, leading=15, backColor=self.BG,
                                      borderColor=self.ACCENT, borderWidth=0, borderPadding=10,
                                      leftIndent=6, rightIndent=6, spaceAfter=8),
        }

    # ------------------------------------------------------------------
    # Rollups
    # ------------------------------------------------------------------

    def _domain_rollup(self, assessment_id: int) -> Dict[str, dict]:
        rows = (
            self.db.query(SubdomainScore, Subdomain, Domain)
            .join(Subdomain, SubdomainScore.subdomain_id == Subdomain.id)
            .join(Domain, Subdomain.domain_id == Domain.id)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .order_by(Domain.display_order, Subdomain.display_order)
            .all()
        )
        result: Dict[str, dict] = {}
        per_domain: Dict[str, List[float]] = {}
        for sc, sd, dom in rows:
            result.setdefault(dom.code, {"name": dom.name, "score": None, "subdomains": []})
            if sc.final_score is not None:
                per_domain.setdefault(dom.code, []).append(float(sc.final_score))
            result[dom.code]["subdomains"].append({
                "code": sd.code, "name": sd.name,
                "score": float(sc.final_score) if sc.final_score is not None else None,
                "cap_applied": bool(getattr(sc, "cap_applied", False)),
                "cap_reason": getattr(sc, "cap_reason", None),
            })
        for code, vals in per_domain.items():
            result[code]["score"] = round(sum(vals) / len(vals), 2) if vals else None
        return result

    def _pillar_rollup(self, domain_rollup: Dict[str, dict]) -> Dict[str, dict]:
        out: Dict[str, dict] = {}
        for pillar, codes in PILLAR_MAP.items():
            vals = [domain_rollup[c]["score"] for c in codes
                    if c in domain_rollup and domain_rollup[c]["score"] is not None]
            out[pillar] = {
                "score": round(sum(vals) / len(vals), 2) if vals else None,
                "domains": codes,
            }
        return out

    def _safe_benchmark(self, assessment_id: int) -> Optional[dict]:
        try:
            from benchmarking_engine import BenchmarkingEngine
            result = BenchmarkingEngine(self.db).benchmark_assessment(assessment_id)
            return result if result.get("status") == "benchmarked" else None
        except Exception as exc:
            logger.info("Benchmark unavailable for report: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _cover(self, a: AssessmentV2, overall: Optional[float], st: dict) -> list:
        story: list = [Spacer(1, 0.4 * inch)]
        if settings.LOGO_PATH and os.path.isfile(settings.LOGO_PATH):
            try:
                story.append(Image(settings.LOGO_PATH, width=2.2 * inch, height=0.9 * inch,
                                   kind="proportional"))
                story.append(Spacer(1, 0.3 * inch))
            except Exception as exc:
                logger.warning("Logo failed to load: %s", exc)
        story.append(Spacer(1, 1.0 * inch))
        story.append(Paragraph("Reliability Maturity Index", st["title"]))
        story.append(Paragraph("Executive Audit Report", st["subtitle"]))
        story.append(Spacer(1, 0.5 * inch))

        score_txt = f"{overall:.2f} / 5.00" if overall is not None else "Pending"
        story.append(Paragraph(
            f"<b>{a.client_name}</b> — {a.site_name}", st["subtitle"]))
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            f"Overall RMI <b>{score_txt}</b> &nbsp;·&nbsp; {_maturity_label(overall)}",
            st["subtitle"]))
        story.append(Spacer(1, 0.6 * inch))

        meta = [
            ["Prepared by", settings.FIRM_NAME],
            ["Prepared for", a.client_name or ""],
            ["Site", a.site_name or ""],
            ["Region", a.region or "—"],
            ["Assessment mode", a.assessment_mode.value.title() if a.assessment_mode else "—"],
            ["Industry module",
             INDUSTRY_NAMES.get(a.industry_module.value, a.industry_module.value)
             if a.industry_module else "—"],
            ["Lead assessor", a.lead_assessor or "—"],
            ["Assessment date", a.assessment_date.strftime("%B %d, %Y") if a.assessment_date else "—"],
            ["Report generated", datetime.utcnow().strftime("%B %d, %Y")],
        ]
        t = Table(meta, colWidths=[2.0 * inch, 4.0 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), self.BG),
            ("TEXTCOLOR", (0, 0), (0, -1), self.PRIMARY),
            ("TEXTCOLOR", (1, 0), (1, -1), self.DARK),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8E0DC")),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(settings.REPORT_CONFIDENTIAL_LABEL, st["small"]))
        return story

    def _exec_summary(self, a, overall, scoring, cmms_uploads, st) -> list:
        responses = self.db.query(ResponseV2).filter(
            ResponseV2.assessment_id == a.id,
            ResponseV2.is_draft == False,  # noqa: E712
            ResponseV2.is_na == False,  # noqa: E712
        ).count()
        confidence = scoring.get("confidence")
        band = scoring.get("confidence_band") or [None, None]
        velocity = scoring.get("velocity") or {}
        iso = scoring.get("iso_55001_readiness")

        days = 0
        if a.assessment_date:
            ad = a.assessment_date.date() if hasattr(a.assessment_date, "date") else a.assessment_date
            days = max(0, (datetime.utcnow().date() - ad).days)
        band_txt = (f" (confidence band {band[0]:.2f}–{band[1]:.2f})"
                    if band and band[0] is not None else "")
        conf_txt = f"{confidence*100:.0f}%" if confidence is not None else "—"

        story = [Paragraph("Executive Summary", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        summary = (
            f"<b>{a.site_name}</b> achieved an overall Reliability Maturity Index of "
            f"<b>{(f'{overall:.2f}' if overall is not None else 'N/A')} / 5.00</b> "
            f"(<b>{_maturity_label(overall)}</b>){band_txt}. "
            f"This assessment evaluated reliability and maintenance practices across the "
            f"three pillars of <b>People</b>, <b>Process</b>, and <b>Technology</b>, mapped "
            f"to five maturity domains and fifteen subdomains. "
            f"It is based on <b>{responses}</b> scored interview responses"
            f"{f' and {len(cmms_uploads)} CMMS data snapshot(s)' if cmms_uploads else ''}, "
            f"with an overall scoring confidence of <b>{conf_txt}</b>."
        )
        story.append(Paragraph(summary, st["body"]))
        story.append(Spacer(1, 6))
        extras = []
        if velocity.get("status") == "calculated":
            extras.append(
                f"<b>Maturity velocity:</b> {velocity.get('delta'):+.2f} RMI vs. the prior "
                f"assessment ({velocity.get('interpretation')}).")
        if iso is not None:
            extras.append(f"<b>ISO 55001 readiness:</b> {iso*100:.0f}% of subdomains at or above "
                          f"the Systematic (3.0) floor.")
        if days:
            extras.append(f"<b>Reporting window:</b> {days} day(s) since fieldwork commenced.")
        if extras:
            story.append(Paragraph("&nbsp;&nbsp;•&nbsp; " +
                                   "<br/>&nbsp;&nbsp;•&nbsp; ".join(extras), st["callout"]))
        return story

    def _pillar_section(self, pillar_rollup, st) -> list:
        story = [Paragraph("Maturity by Pillar (People · Process · Technology)", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        rows = [["Pillar", "Score", "Maturity Level", "Constituent Domains"]]
        for pillar, data in pillar_rollup.items():
            score = data["score"]
            rows.append([
                pillar,
                f"{score:.2f}" if score is not None else "—",
                _maturity_label(score),
                ", ".join(data["domains"]),
            ])
        t = Table(rows, colWidths=[1.4 * inch, 0.8 * inch, 2.0 * inch, 1.9 * inch])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#D8E0DC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.BG]),
        ]
        for i, (_, data) in enumerate(pillar_rollup.items(), start=1):
            style.append(("TEXTCOLOR", (1, i), (1, i), _score_color(data["score"])))
            style.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
        t.setStyle(TableStyle(style))
        story.append(t)
        radar = self._radar(
            list(pillar_rollup.keys()),
            [pillar_rollup[k]["score"] or 0 for k in pillar_rollup],
            title="Pillar Maturity Profile",
        )
        if radar:
            story.append(Spacer(1, 8))
            story.append(KeepTogether([radar]))
        return story

    def _domain_section(self, domain_rollup, benchmark, st) -> list:
        story = [Paragraph("Maturity by Domain (5-Domain Framework)", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        has_bench = bool(benchmark and benchmark.get("domain_benchmarks"))
        header = ["Domain", "Score", "Maturity Level"]
        if has_bench:
            header.append("Percentile")
        rows = [header]
        for code, data in domain_rollup.items():
            score = data["score"]
            row = [f"{code} — {data['name']}",
                   f"{score:.2f}" if score is not None else "—",
                   _maturity_label(score)]
            if has_bench:
                p = (benchmark["domain_benchmarks"].get(code) or {}).get("percentile")
                row.append(f"{p}th" if p is not None else "—")
            rows.append(row)
        widths = [2.6 * inch, 0.8 * inch, 1.9 * inch] + ([0.9 * inch] if has_bench else [])
        t = Table(rows, colWidths=widths)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.BG]),
        ]
        for i, (_, data) in enumerate(domain_rollup.items(), start=1):
            style.append(("TEXTCOLOR", (1, i), (1, i), _score_color(data["score"])))
            style.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
        t.setStyle(TableStyle(style))
        story.append(t)

        # Benchmark overlay: real peer mean when we have a peer group, otherwise
        # an explicitly-labelled target baseline (never a fabricated peer line).
        peer_mean = ((benchmark or {}).get("peer_stats") or {}).get("mean")
        if peer_mean is not None:
            bench_vals = [peer_mean] * len(domain_rollup)
            bench_label = f"Peer mean ({peer_mean:.1f}, n={benchmark['peer_stats']['count']})"
        else:
            bench_vals = [3.0] * len(domain_rollup)
            bench_label = "Target baseline (3.0)"

        radar = self._radar(
            list(domain_rollup.keys()),
            [domain_rollup[k]["score"] or 0 for k in domain_rollup],
            benchmark_values=bench_vals, benchmark_label=bench_label,
            title="Domain Maturity Profile",
        )
        if radar:
            story.append(Spacer(1, 8))
            story.append(KeepTogether([radar]))
        return story

    def _subdomain_section(self, assessment_id: int, st) -> list:
        rows_q = (
            self.db.query(SubdomainScore, Subdomain, Domain)
            .join(Subdomain, SubdomainScore.subdomain_id == Subdomain.id)
            .join(Domain, Subdomain.domain_id == Domain.id)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .order_by(Domain.display_order, Subdomain.display_order)
            .all()
        )
        story = [Paragraph("Subdomain Detail", st["h3"])]
        rows = [["Code", "Subdomain", "Score", "Notes"]]
        for sc, sd, dom in rows_q:
            note = "—"
            if getattr(sc, "cap_applied", False):
                note = (getattr(sc, "cap_reason", None) or "Capped")[:54]
            rows.append([sd.code, f"{sd.name}",
                         f"{(sc.final_score or 0):.2f}", note])
        t = Table(rows, colWidths=[0.7 * inch, 2.5 * inch, 0.7 * inch, 2.4 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.BG]),
        ]))
        story.append(t)
        return story

    def _findings_section(self, domain_rollup, scoring, st) -> list:
        story = [Paragraph("Key Findings", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        findings: List[str] = []
        ordered = sorted(
            [(c, d) for c, d in domain_rollup.items() if d["score"] is not None],
            key=lambda x: x[1]["score"])
        for code, data in ordered:
            s = data["score"]
            if s < 2.5:
                findings.append(f"<b>{code} — {data['name']} ({s:.2f}):</b> Critical gap. "
                                f"Foundational practices are absent or inconsistent; immediate "
                                f"intervention is required to arrest reliability risk.")
            elif s < 3.5:
                findings.append(f"<b>{code} — {data['name']} ({s:.2f}):</b> Emerging. Practices "
                                f"exist but are not yet systematic; targeted improvement will "
                                f"move this domain to a proactive footing.")
            elif s < 4.3:
                findings.append(f"<b>{code} — {data['name']} ({s:.2f}):</b> Solid proactive "
                                f"foundation; well positioned to advance toward predictive and "
                                f"prescriptive practice.")
            else:
                findings.append(f"<b>{code} — {data['name']} ({s:.2f}):</b> Best-in-class. Focus "
                                f"on sustainment, knowledge transfer, and continuous improvement.")
        caps = scoring.get("caps_applied") or []
        cap_labels = sorted({c.get("label") for c in caps if c.get("label")})
        for label in cap_labels[:6]:
            findings.append(f"<b>Weakest-link constraint:</b> {label}. This evidence-based cap "
                            f"limits the affected score until the gap is closed.")
        for f in findings:
            story.append(Paragraph(f"•&nbsp; {f}", st["body"]))
            story.append(Spacer(1, 4))
        return story

    def _cmms_section(self, cmms_uploads, st) -> list:
        story = [PageBreak(), Paragraph("CMMS Data Analysis", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        for u in cmms_uploads:
            m = u.metrics or {}
            story.append(Paragraph(
                f"<b>{(u.kind or '').replace('_', ' ').title()}</b> — "
                f"{u.original_filename or 'snapshot'} · {u.record_count or 0} records", st["h3"]))
            kpis = []
            rr = (m.get("reactive_ratio") or {}).get("reactive_ratio")
            if isinstance(rr, (int, float)):
                sev = (m.get("reactive_ratio") or {}).get("severity", "")
                kpis.append(["Reactive ratio", f"{rr*100:.1f}%", sev])
            dq = (m.get("data_quality") or {})
            if dq.get("actionability_index") is not None:
                kpis.append(["Data quality (actionability)",
                             f"{dq.get('actionability_index'):.1f}/100",
                             dq.get("severity", "")])
            pmc = m.get("pm_compliance_rate", m.get("compliance_rate"))
            if isinstance(pmc, (int, float)):
                kpis.append(["PM compliance", f"{pmc*100:.1f}%", m.get("severity", "")])
            if isinstance(m.get("total_records_analyzed"), int):
                kpis.append(["Records analyzed", str(m.get("total_records_analyzed")), ""])
            if kpis:
                rows = [["Metric", "Value", "Assessment"]] + kpis
                t = Table(rows, colWidths=[2.2 * inch, 1.2 * inch, 2.9 * inch])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), self.DARK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.BG]),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
            if u.bad_actors:
                top = ", ".join(f"{k} ({v})" for k, v in (u.bad_actors or [])[:5])
                if top:
                    story.append(Paragraph(f"<b>Top bad actors:</b> {top}", st["small"]))
                    story.append(Spacer(1, 6))
        return story

    def _blind_spot_section(self, scoring, st) -> list:
        spots = scoring.get("blind_spots") or []
        if not spots:
            return []
        story = [Paragraph("Cultural Blind Spots", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8),
                 Paragraph("Subdomains where role perceptions diverge significantly — a signal of "
                           "misalignment between frontline and leadership views.", st["body"]),
                 Spacer(1, 6)]
        rows = [["Subdomain", "Role spread", "Severity"]]
        for bs in spots:
            rows.append([bs.get("subdomain", ""), f"{bs.get('variance', 0):.2f}",
                         (bs.get("severity") or "").title()])
        t = Table(rows, colWidths=[2.0 * inch, 1.5 * inch, 2.8 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.BG]),
        ]))
        story.append(t)
        return story

    def _roadmap_section(self, domain_rollup, st) -> list:
        story = [PageBreak(), Paragraph("Strategic Roadmap (30 / 60 / 90 Day)", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        ordered = sorted(
            [(c, d) for c, d in domain_rollup.items() if d["score"] is not None],
            key=lambda x: x[1]["score"])
        weakest = [c for c, _ in ordered[:3]] or list(DOMAIN_ROADMAP.keys())[:3]
        if ordered:
            story.append(Paragraph(
                f"<b>Strategic priority:</b> concentrate first on "
                f"{', '.join(weakest)} — the lowest-scoring domains — while sustaining strengths.",
                st["callout"]))
        phases = [("First 30 Days — Quick Wins", "30"),
                  ("Days 31–60 — Capability Building", "60"),
                  ("Days 61–90 — Strategic Initiatives", "90")]
        for title, key in phases:
            actions: List[str] = []
            for code in weakest:
                actions.extend(DOMAIN_ROADMAP.get(code, {}).get(key, []))
            if not actions:
                continue
            story.append(Paragraph(f"{title} — {len(actions)} actions", st["h3"]))
            for i, act in enumerate(actions, 1):
                story.append(Paragraph(f"<b>{i}.</b> {act}", st["body"]))
            story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Assign an executive sponsor per phase, establish a weekly cadence, and re-baseline "
            "the RMI at 90 days to measure velocity.", st["small"]))
        return story

    def _evidence_section(self, assessment_id, scoring, st) -> list:
        from models_v2 import EvidenceStatus
        rows = self.db.query(ResponseV2).filter(
            ResponseV2.assessment_id == assessment_id).all()
        if not rows:
            return []
        buckets: Dict[str, int] = {}
        for r in rows:
            key = r.evidence_status.value if r.evidence_status else "unknown"
            buckets[key] = buckets.get(key, 0) + 1
        order = [
            (EvidenceStatus.ACCEPTED.value, "Verified (Accepted)"),
            (EvidenceStatus.PENDING_VERIFICATION.value, "Submitted, pending verification"),
            (EvidenceStatus.PENDING_EVIDENCE.value, "Awaiting evidence"),
            (EvidenceStatus.REJECTED.value, "Rejected"),
            (EvidenceStatus.NOT_REQUIRED.value, "Evidence not required"),
        ]
        story = [Paragraph("Evidence & Assurance Summary", st["h2"]),
                 HRFlowable(width="100%", thickness=0.5, color=self.PRIMARY, spaceAfter=8)]
        table_rows = [["Evidence Status", "Responses"]]
        for key, label in order:
            table_rows.append([label, str(buckets.get(key, 0))])
        t = Table(table_rows, colWidths=[3.6 * inch, 1.2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.BG]),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Scores of 4 or above on evidence-required questions are credited only where "
            "supporting evidence has been verified; unverified claims are conservatively "
            "moderated. This preserves the defensibility of the maturity rating.", st["small"]))
        return story

    # ------------------------------------------------------------------
    # Radar chart (in-memory, no temp file)
    # ------------------------------------------------------------------

    def _radar(self, labels: List[str], values: List[float],
               benchmark_values: Optional[List[float]] = None,
               benchmark_label: str = "Benchmark",
               title: str = "Maturity Profile") -> Optional[Image]:
        if not labels:
            return None
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        vals = list(values) + values[:1]
        ang = angles + angles[:1]
        primary = settings.BRAND_PRIMARY_HEX

        fig = plt.figure(figsize=(6, 5.2))
        ax = plt.subplot(111, polar=True)
        ax.set_facecolor("#FBFCFB")
        if benchmark_values:
            bvals = list(benchmark_values) + benchmark_values[:1]
            ax.plot(ang, bvals, linestyle="--", linewidth=1.3, color="#9AA5A1",
                    label=benchmark_label, zorder=1)
            ax.fill(ang, bvals, color="#9AA5A1", alpha=0.08, zorder=1)
        ax.plot(ang, vals, "o-", linewidth=2.3, color=primary, markersize=6,
                markerfacecolor="white", markeredgecolor=primary, markeredgewidth=1.6,
                label="This site", zorder=2)
        ax.fill(ang, vals, color=primary, alpha=0.18, zorder=2)
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, size=10, weight="bold")
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(["1", "2", "3", "4", "5"], size=8, color="#6B7670")
        ax.set_ylim(0, 5)
        ax.grid(color="#E0E6E3", linestyle="--", linewidth=0.5)
        ax.set_title(title, size=12, weight="bold", pad=18, color="#14302B")
        ax.legend(loc="upper right", bbox_to_anchor=(1.18, 1.12), frameon=False, fontsize=8)
        buf = io.BytesIO()
        plt.savefig(buf, format="PNG", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return Image(buf, width=4.8 * inch, height=4.2 * inch)

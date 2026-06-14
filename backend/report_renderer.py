"""
Premium HTML→PDF executive report renderer (Playwright / headless Chromium).

Produces a SOC 2-grade, branded NextBelt audit report. Gathers the same v2 data
as report_generator_v2 but renders it through an HTML/CSS template with embedded
Inter fonts, brand palette, the NextBelt logo, and Python-computed SVG charts —
then prints a full-bleed cover + paginated body and merges them with pypdf.

Falls back to the ReportLab generator if Chromium is unavailable, so report
download never hard-fails.
"""
from __future__ import annotations

import base64
import logging
import math
import os
import re
import tempfile
from datetime import datetime
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from config import settings
from models import Report
from models_v2 import (
    AssessmentV2, CMMSUploadV2, Domain, Practice, QuestionV2, ResponseV2,
    Subdomain, SubdomainScore, EvidenceStatus,
)
from scoring_engine_v2 import ScoringEngineV2

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_TPL_DIR = os.path.join(_HERE, "report_templates")
_ASSET_DIR = os.path.join(_HERE, "report_assets")
_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

# ── Brand palette (NextBelt) ──
NAVY = "#061A31"
BLUE = "#0B4F93"
ACCENT = "#1C78B5"
SILVER = "#BCC1C3"
GRAPHITE = "#25282B"

PILLAR_MAP: Dict[str, List[str]] = {
    "People": ["WC", "LC"],
    "Process": ["WM", "SG"],
    "Technology": ["AI"],
}
INDUSTRY_NAMES = {
    "MFG": "Manufacturing (General)", "FNB": "Food & Beverage", "ONG": "Oil & Gas",
    "MNM": "Mining & Minerals", "UTL": "Utilities", "PHA": "Pharmaceuticals",
}
DOMAIN_ROADMAP = {
    "WC": {"30": ["Run a skills-matrix gap analysis for all maintenance roles",
                  "Launch weekly reliability toolbox talks"],
           "60": ["Stand up a competency-based training program with certification paths",
                  "Formalize knowledge-transfer pairing (senior to junior technicians)"],
           "90": ["Establish a Reliability Technician certification track and career ladder"]},
    "LC": {"30": ["Publish and brief stop-work authority and safety expectations",
                  "Hold a leadership reliability alignment session"],
           "60": ["Define reliability KPIs reviewed by leadership on a fixed cadence",
                  "Clarify maintenance org structure and accountability (RACI)"],
           "90": ["Embed a proactive reliability culture program with frontline ownership"]},
    "WM": {"30": ["Audit the last 100 work orders for planning/execution quality",
                  "Create standardized job plans for the top 20 critical PM tasks"],
           "60": ["Deploy a planner-approved work-order planning checklist",
                  "Run PM optimization (RCM/PMO) on critical assets; manage backlog by priority"],
           "90": ["Institute a 2-week forward schedule with schedule-compliance KPIs"]},
    "AI": {"30": ["Audit CMMS data quality (closure codes, failure modes, completeness)",
                  "Stand up a Top-10 bad-actor dashboard by downtime"],
           "60": ["Align failure taxonomy to ISO 14224; enforce mandatory WO fields",
                  "Enable mobile CMMS capture for field technicians"],
           "90": ["Launch a predictive-maintenance pilot and a leadership reliability dashboard"]},
    "SG": {"30": ["Draft/ratify a written asset-management policy and objectives",
                  "Define the reliability metric set (leading + lagging)"],
           "60": ["Stand up monthly performance reviews against AM objectives",
                  "Establish a continuous-improvement (RCA to action) loop"],
           "90": ["Mature toward ISO 55001 alignment with an audited management system"]},
}


def _slug(name: str) -> str:
    return _FILENAME_RE.sub("_", name or "").strip("._-") or "unknown"


def _level(score: Optional[float]) -> dict:
    if score is None:
        return {"n": 0, "label": "Not scored", "color": SILVER}
    if score < 2.0:
        return {"n": 1, "label": "Reactive", "color": "#C0392B"}
    if score < 3.0:
        return {"n": 2, "label": "Emerging", "color": "#D9822B"}
    if score < 3.6:
        return {"n": 3, "label": "Systematic", "color": ACCENT}
    if score < 4.3:
        return {"n": 4, "label": "Proactive", "color": "#2E8C6A"}
    return {"n": 5, "label": "Prescriptive", "color": "#1E7A52"}


def _data_uri(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return ""


class HTMLReportRenderer:
    def __init__(self, db: Session, output_dir: Optional[str] = None) -> None:
        self.db = db
        self.output_dir = output_dir or settings.REPORT_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(_TPL_DIR),
            autoescape=select_autoescape(["html"]),
        )

    # ── public ──
    def generate(self, *, assessment_id: int, generated_by: int) -> str:
        a = self.db.query(AssessmentV2).filter(AssessmentV2.id == assessment_id).first()
        if not a:
            raise ValueError(f"Assessment {assessment_id} not found")

        ctx = self._build_context(a)
        fonts_css = self._read(os.path.join(_TPL_DIR, "_fonts.css"))
        serif_css = self._read(os.path.join(_TPL_DIR, "_serif.css"))

        cover_html = self.env.get_template("cover.html.j2").render(
            fonts_css=fonts_css, serif_css=serif_css, **ctx)
        body_html = self.env.get_template("report.html.j2").render(
            fonts_css=fonts_css, serif_css=serif_css, **ctx)

        filename = (
            f"RMI_Audit_Report_{_slug(a.client_name)}_{_slug(a.site_name)}_"
            f"{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        )
        filepath = os.path.join(self.output_dir, filename)
        self._render_pdf(cover_html, body_html, filepath, ctx)

        registry = Report(
            assessment_id=assessment_id, report_type="executive_v2_html",
            title=f"Executive RMI Report — {a.client_name} {a.site_name}",
            content={"overall_rmi": ctx["overall"], "engine": "html"},
            file_path=filepath, generated_by=generated_by,
        )
        self.db.add(registry)
        self.db.commit()
        return filepath

    # ── PDF rendering (Playwright + merge) ──
    def _render_pdf(self, cover_html: str, body_html: str, filepath: str, ctx: dict) -> None:
        from playwright.sync_api import sync_playwright

        footer = self._footer_template(ctx)
        header = self._header_template(ctx)
        tmp_cover = filepath + ".cover.pdf"
        tmp_body = filepath + ".body.pdf"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"]
                )
                ctx_b = browser.new_context()
                # Cover: full bleed
                pc = ctx_b.new_page()
                pc.set_content(cover_html, wait_until="load")
                pc.pdf(path=tmp_cover, format="Letter", print_background=True,
                       margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
                pc.close()
                # Body: margins + running header/footer + page numbers
                pb = ctx_b.new_page()
                pb.set_content(body_html, wait_until="load")
                pb.pdf(path=tmp_body, format="Letter", print_background=True,
                       display_header_footer=True, header_template=header, footer_template=footer,
                       margin={"top": "0.7in", "bottom": "0.62in", "left": "0.7in", "right": "0.7in"})
                pb.close()
                browser.close()

            from pypdf import PdfReader, PdfWriter
            writer = PdfWriter()
            for part in (tmp_cover, tmp_body):
                for page in PdfReader(part).pages:
                    writer.add_page(page)
            with open(filepath, "wb") as f:
                writer.write(f)
        finally:
            for t in (tmp_cover, tmp_body):
                try:
                    os.remove(t)
                except OSError:
                    pass

    def _header_template(self, ctx: dict) -> str:
        # No running header — the McKinsey-style layout keeps the top of each
        # page clean. (Playwright requires a template when header/footer is on.)
        return '<div style="height:0;"></div>'

    def _footer_template(self, ctx: dict) -> str:
        client = (ctx.get("client") or "").replace("&", "&amp;")
        return (
            f'<div style="width:100%;font-family:Georgia,\'Times New Roman\',serif;font-size:7.5px;'
            f'color:#8A929A;padding:0 0.7in;display:flex;justify-content:space-between;align-items:baseline;">'
            f'<span style="font-style:italic;">Reliability Maturity Index &nbsp;·&nbsp; {client}</span>'
            f'<span class="pageNumber" style="font-variant-numeric:tabular-nums;"></span></div>'
        )

    # ── data ──
    def _read(self, path: str) -> str:
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _build_context(self, a: AssessmentV2) -> dict:
        engine = ScoringEngineV2(self.db)
        try:
            scoring = engine.calculate(a.id, persist=False)
        except Exception as exc:
            logger.warning("scoring during report failed: %s", exc)
            scoring = {}

        domain_rollup = self._domain_rollup(a.id)
        overall = a.overall_rmi
        if overall is None and domain_rollup:
            vals = [d["score"] for d in domain_rollup if d["score"] is not None]
            overall = round(sum(vals) / len(vals), 2) if vals else None

        pillars = self._pillars(domain_rollup)
        benchmark = self._benchmark(a.id)
        peer_mean = (benchmark or {}).get("peer_stats", {}).get("mean") if benchmark else None

        responses = self.db.query(ResponseV2).filter(
            ResponseV2.assessment_id == a.id,
            ResponseV2.is_draft == False, ResponseV2.is_na == False,  # noqa: E712
        ).count()

        ctx = {
            "firm": {"name": settings.FIRM_NAME, "tagline": settings.FIRM_TAGLINE,
                     "website": settings.FIRM_WEBSITE, "email": settings.FIRM_EMAIL},
            "confidential": settings.REPORT_CONFIDENTIAL_LABEL,
            "logo": _data_uri(os.path.join(_ASSET_DIR, "nextbelt_logo.png")),
            "navy": NAVY, "blue": BLUE, "accent": ACCENT, "silver": SILVER, "graphite": GRAPHITE,
            "client": a.client_name, "site": a.site_name,
            "region": a.region or "—",
            "industry": INDUSTRY_NAMES.get(a.industry_module.value, a.industry_module.value) if a.industry_module else (a.industry or "—"),
            "mode": a.assessment_mode.value.title() if a.assessment_mode else "—",
            "lead_assessor": a.lead_assessor or "—",
            "assessment_date": a.assessment_date.strftime("%B %d, %Y") if a.assessment_date else "—",
            "report_date": datetime.utcnow().strftime("%B %d, %Y"),
            "overall": round(overall, 2) if overall is not None else None,
            "overall_level": _level(overall),
            "confidence": round((scoring.get("confidence") or 0) * 100) if scoring.get("confidence") is not None else None,
            "confidence_band": scoring.get("confidence_band") or [None, None],
            "iso_readiness": round((scoring.get("iso_55001_readiness") or 0) * 100) if scoring.get("iso_55001_readiness") is not None else None,
            "responses": responses,
            "domains": domain_rollup,
            "pillars": pillars,
            "findings": self._findings(domain_rollup, scoring),
            "priority_fixes": self._priority_fixes(a.id),
            "cmms": self._cmms(a.id),
            "blind_spots": scoring.get("blind_spots") or [],
            "velocity": scoring.get("velocity") or {},
            "roadmap": self._roadmap(domain_rollup),
            "evidence": self._evidence(a.id),
            "benchmark": benchmark,
            "peer_mean": peer_mean,
            "pillar_radar": self._radar_svg([p["name"] for p in pillars], [p["score"] or 0 for p in pillars]),
            "domain_radar": self._radar_svg(
                [d["code"] for d in domain_rollup], [d["score"] or 0 for d in domain_rollup],
                benchmark=[peer_mean] * len(domain_rollup) if peer_mean else [3.0] * len(domain_rollup),
                benchmark_label=(f"Peer mean {peer_mean:.1f}" if peer_mean else "Target 3.0"),
            ),
        }
        return ctx

    def _domain_rollup(self, assessment_id: int) -> List[dict]:
        rows = (
            self.db.query(SubdomainScore, Subdomain, Domain)
            .join(Subdomain, SubdomainScore.subdomain_id == Subdomain.id)
            .join(Domain, Subdomain.domain_id == Domain.id)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .order_by(Domain.display_order, Subdomain.display_order)
            .all()
        )
        agg: Dict[str, dict] = {}
        for sc, sd, dom in rows:
            d = agg.setdefault(dom.code, {"code": dom.code, "name": dom.name, "scores": [], "subdomains": []})
            fs = float(sc.final_score) if sc.final_score is not None else None
            if fs is not None:
                d["scores"].append(fs)
            d["subdomains"].append({
                "code": sd.code, "name": sd.name, "score": fs, "level": _level(fs),
                "cap_applied": bool(getattr(sc, "cap_applied", False)),
                "cap_reason": getattr(sc, "cap_reason", None),
            })
        out = []
        for d in agg.values():
            score = round(sum(d["scores"]) / len(d["scores"]), 2) if d["scores"] else None
            out.append({"code": d["code"], "name": d["name"], "score": score,
                        "level": _level(score), "subdomains": d["subdomains"]})
        return out

    def _pillars(self, domain_rollup: List[dict]) -> List[dict]:
        by_code = {d["code"]: d for d in domain_rollup}
        out = []
        for name, codes in PILLAR_MAP.items():
            vals = [by_code[c]["score"] for c in codes if c in by_code and by_code[c]["score"] is not None]
            score = round(sum(vals) / len(vals), 2) if vals else None
            out.append({"name": name, "codes": codes, "score": score, "level": _level(score)})
        return out

    def _benchmark(self, assessment_id: int) -> Optional[dict]:
        try:
            from benchmarking_engine import BenchmarkingEngine
            r = BenchmarkingEngine(self.db).benchmark_assessment(assessment_id)
            return r if r.get("status") == "benchmarked" else None
        except Exception:
            return None

    def _findings(self, domain_rollup, scoring) -> List[str]:
        out = []
        for d in sorted([x for x in domain_rollup if x["score"] is not None], key=lambda x: x["score"]):
            s = d["score"]
            if s < 2.5:
                out.append(f"<b>{d['code']} — {d['name']} ({s:.2f}):</b> Critical gap. Foundational "
                           f"practices are absent or inconsistent; immediate intervention is required.")
            elif s < 3.5:
                out.append(f"<b>{d['code']} — {d['name']} ({s:.2f}):</b> Emerging. Practices exist but "
                           f"are not yet systematic; targeted improvement moves this to a proactive footing.")
            elif s < 4.3:
                out.append(f"<b>{d['code']} — {d['name']} ({s:.2f}):</b> Solid proactive foundation; well "
                           f"positioned to advance toward predictive and prescriptive practice.")
            else:
                out.append(f"<b>{d['code']} — {d['name']} ({s:.2f}):</b> Best-in-class. Focus on sustainment, "
                           f"knowledge transfer, and continuous improvement.")
        for label in sorted({c.get("label") for c in (scoring.get("caps_applied") or []) if c.get("label")})[:5]:
            out.append(f"<b>Weakest-link constraint:</b> {label}.")
        return out

    def _priority_fixes(self, assessment_id: int) -> List[dict]:
        rows = (
            self.db.query(ResponseV2.numeric_score, QuestionV2.question_code, QuestionV2.question_text,
                          QuestionV2.practice_link, Subdomain.id, Subdomain.name, Domain.code, Domain.name,
                          Domain.display_order)
            .join(QuestionV2, ResponseV2.question_id == QuestionV2.id)
            .join(Subdomain, QuestionV2.subdomain_id == Subdomain.id)
            .join(Domain, Subdomain.domain_id == Domain.id)
            .filter(ResponseV2.assessment_id == assessment_id,
                    ResponseV2.numeric_score.isnot(None),
                    ResponseV2.is_na == False, ResponseV2.is_draft == False)  # noqa: E712
            .all()
        )
        if not rows:
            return []
        plinks = {r[3] for r in rows if r[3]}
        ptitle: Dict[str, str] = {}
        if plinks:
            for p in self.db.query(Practice).filter(
                (Practice.practice_id.in_(plinks)) | (Practice.practice_code.in_(plinks))
            ).all():
                if p.practice_id:
                    ptitle[p.practice_id] = p.title
                if p.practice_code:
                    ptitle[p.practice_code] = p.title
        sub_practice: Dict[int, str] = {}
        for p in self.db.query(Practice).order_by(Practice.from_level, Practice.priority_rank).all():
            sub_practice.setdefault(p.subdomain_id, p.title)

        groups: Dict[str, dict] = {}
        for score, qcode, qtext, plink, sdid, sdname, dcode, dname, order in rows:
            g = groups.setdefault(dcode, {"code": dcode, "name": dname, "order": order, "rows": []})
            fix = ptitle.get(plink) or sub_practice.get(sdid) or f"Strengthen {sdname}"
            g["rows"].append({"score": float(score), "code": qcode,
                               "text": (qtext or "")[:120], "level": _level(float(score)), "fix": fix})
        out = []
        for g in sorted(groups.values(), key=lambda x: x["order"]):
            weak = [w for w in sorted(g["rows"], key=lambda x: x["score"]) if w["score"] < 3.0][:4]
            if weak:
                out.append({"code": g["code"], "name": g["name"], "rows": weak})
        return out

    def _cmms(self, assessment_id: int) -> List[dict]:
        rows = (self.db.query(CMMSUploadV2)
                .filter(CMMSUploadV2.assessment_id == assessment_id, CMMSUploadV2.status == "processed")
                .order_by(CMMSUploadV2.uploaded_at.desc()).all())
        out = []
        for u in rows:
            m = u.metrics or {}
            kpis = []
            rr = (m.get("reactive_ratio") or {}).get("reactive_ratio")
            if isinstance(rr, (int, float)):
                kpis.append(("Reactive ratio", f"{rr*100:.1f}%", (m.get("reactive_ratio") or {}).get("severity", "")))
            dq = m.get("data_quality") or {}
            if dq.get("actionability_index") is not None:
                kpis.append(("Data quality (actionability)", f"{dq.get('actionability_index'):.1f}/100", dq.get("severity", "")))
            pmc = m.get("pm_compliance_rate", m.get("compliance_rate"))
            if isinstance(pmc, (int, float)):
                kpis.append(("PM compliance", f"{pmc*100:.1f}%", m.get("severity", "")))
            out.append({"kind": (u.kind or "").replace("_", " ").title(),
                        "filename": u.original_filename or "snapshot",
                        "records": u.record_count or 0, "kpis": kpis,
                        "bad_actors": (u.bad_actors or [])[:5]})
        return out

    def _roadmap(self, domain_rollup) -> dict:
        ordered = sorted([d for d in domain_rollup if d["score"] is not None], key=lambda x: x["score"])
        weakest = [d["code"] for d in ordered[:3]] or list(DOMAIN_ROADMAP)[:3]
        phases = {}
        for key, title in (("30", "First 30 Days — Quick Wins"),
                           ("60", "Days 31–60 — Capability Building"),
                           ("90", "Days 61–90 — Strategic Initiatives")):
            acts = []
            for c in weakest:
                acts.extend(DOMAIN_ROADMAP.get(c, {}).get(key, []))
            phases[key] = {"title": title, "actions": acts}
        return {"weakest": weakest, "phases": phases}

    def _evidence(self, assessment_id: int) -> List[dict]:
        rows = self.db.query(ResponseV2).filter(ResponseV2.assessment_id == assessment_id).all()
        buckets: Dict[str, int] = {}
        for r in rows:
            k = r.evidence_status.value if r.evidence_status else "unknown"
            buckets[k] = buckets.get(k, 0) + 1
        order = [(EvidenceStatus.ACCEPTED.value, "Verified (Accepted)"),
                 (EvidenceStatus.PENDING_VERIFICATION.value, "Submitted, pending verification"),
                 (EvidenceStatus.PENDING_EVIDENCE.value, "Awaiting evidence"),
                 (EvidenceStatus.REJECTED.value, "Rejected"),
                 (EvidenceStatus.NOT_REQUIRED.value, "Evidence not required")]
        return [{"label": label, "count": buckets.get(k, 0)} for k, label in order]

    # ── SVG radar chart ──
    def _radar_svg(self, labels: List[str], values: List[float], *,
                   benchmark: Optional[List[float]] = None, benchmark_label: str = "",
                   size: int = 460) -> str:
        n = len(labels)
        if n < 3:
            return ""
        cx = cy = size / 2
        r = size * 0.33
        def pt(i, val):
            ang = -math.pi / 2 + i * 2 * math.pi / n
            rr = max(0.0, min(val, 5.0)) / 5.0 * r
            return cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        parts = [f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
                 f'font-family="Inter,Arial,sans-serif">']
        # rings
        for ring in range(1, 6):
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, ring) for i in range(n)))
            parts.append(f'<polygon points="{pts}" fill="none" stroke="#E3E8EE" stroke-width="1"/>')
        # axes + labels
        for i, lab in enumerate(labels):
            x, y = pt(i, 5)
            parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#E3E8EE" stroke-width="1"/>')
            lx, ly = pt(i, 5.85)
            anchor = "middle" if abs(lx - cx) < 8 else ("start" if lx > cx else "end")
            parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                         f'dominant-baseline="middle" font-size="15" font-weight="700" fill="{NAVY}">{lab}</text>')
        # benchmark polygon
        if benchmark:
            bpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, benchmark[i]) for i in range(n)))
            parts.append(f'<polygon points="{bpts}" fill="none" stroke="{SILVER}" '
                         f'stroke-width="1.5" stroke-dasharray="4 3"/>')
        # data polygon
        dpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, values[i]) for i in range(n)))
        parts.append(f'<polygon points="{dpts}" fill="{ACCENT}" fill-opacity="0.18" '
                     f'stroke="{BLUE}" stroke-width="2.5"/>')
        for i in range(n):
            x, y = pt(i, values[i])
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fff" stroke="{BLUE}" stroke-width="2"/>')
        parts.append("</svg>")
        return "".join(parts)

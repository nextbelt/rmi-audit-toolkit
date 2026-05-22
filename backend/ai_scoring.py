"""
AI-Assisted Scoring Module
Uses OpenAI to evaluate text responses, analyze evidence files (images/PDFs),
and assign numeric maturity scores.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict, Optional

import openai

from config import settings

logger = logging.getLogger(__name__)


IMAGE_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}
PDF_MIME_TYPES = {"application/pdf"}


class AIScoringEngine:
    """
    Evaluates narrative text responses using OpenAI API
    Returns 1-5 scores with rationale based on RMI maturity criteria
    """
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        openai.api_key = settings.OPENAI_API_KEY
    
    def score_text_response(
        self, 
        question_text: str, 
        response_text: str,
        question_type: str = "LIKERT"
    ) -> Dict[str, any]:
        """
        Score a text response using AI
        
        Args:
            question_text: The assessment question
            response_text: The user's narrative answer
            question_type: Type of question (LIKERT, BINARY, etc.)
        
        Returns:
            {
                "numeric_score": float (1-5),
                "rationale": str,
                "confidence": str (HIGH, MEDIUM, LOW),
                "key_findings": list[str]
            }
        """
        if question_type == "BINARY":
            # Binary questions get simple yes/no scoring
            return self._score_binary(response_text)
        
        # LIKERT questions use full maturity assessment
        return self._score_likert(question_text, response_text)
    
    def _score_binary(self, response_text: str) -> Dict:
        """Simple binary scoring - look for yes/no indicators"""
        response_lower = response_text.lower()
        
        # Check for positive indicators
        positive_words = ["yes", "implemented", "exists", "established", "in place", "documented"]
        negative_words = ["no", "not implemented", "does not exist", "lacking", "absent", "informal"]
        
        positive_count = sum(1 for word in positive_words if word in response_lower)
        negative_count = sum(1 for word in negative_words if word in response_lower)
        
        if positive_count > negative_count:
            return {
                "numeric_score": 5.0,
                "rationale": "Response indicates positive/yes answer",
                "confidence": "HIGH",
                "key_findings": ["Positive indicators found in response"]
            }
        else:
            return {
                "numeric_score": 1.0,
                "rationale": "Response indicates negative/no answer",
                "confidence": "HIGH",
                "key_findings": ["Negative indicators found in response"]
            }
    
    def _score_likert(self, question_text: str, response_text: str) -> Dict:
        """
        Use OpenAI to score narrative response on 1-5 maturity scale
        """
        
        prompt = f"""You are an expert RMI (Reliability, Maintainability, Inspectability) auditor. 
Evaluate the following response and assign a maturity score from 1 to 5 based on these criteria:

**Maturity Scale:**
1 = Ad Hoc / Non-existent: No formal processes, reactive only, no documentation
2 = Initial / Developing: Some informal processes, inconsistent application, minimal documentation
3 = Defined / Managed: Documented processes, somewhat standardized, moderate consistency
4 = Optimized / Proactive: Well-documented, standardized, data-driven, continuous improvement
5 = World Class / Excellence: Best-in-class, fully integrated, predictive, benchmark performance

**Question:** {question_text}

**Response:** {response_text}

Analyze this response and provide:
1. A numeric score (1-5, use decimals like 2.5 or 3.5 for nuanced assessment)
2. A brief rationale (2-3 sentences)
3. Confidence level (HIGH, MEDIUM, or LOW)
4. 2-3 key findings or evidence points from the response

Format your response EXACTLY as JSON:
{{
    "numeric_score": <number>,
    "rationale": "<string>",
    "confidence": "<HIGH|MEDIUM|LOW>",
    "key_findings": ["<finding1>", "<finding2>", "<finding3>"]
}}
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert RMI auditor. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=500,
                response_format={"type": "json_object"}  # Ensures JSON output
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Validate and normalize score
            score = float(result.get("numeric_score", 3.0))
            score = max(1.0, min(5.0, score))  # Clamp to 1-5 range
            
            return {
                "numeric_score": round(score, 1),
                "rationale": result.get("rationale", "AI evaluation completed"),
                "confidence": result.get("confidence", "MEDIUM").upper(),
                "key_findings": result.get("key_findings", [])
            }
            
        except Exception as e:
            # Fallback: return neutral score if AI fails
            print(f"AI scoring error: {str(e)}")
            return {
                "numeric_score": 3.0,
                "rationale": f"AI scoring unavailable - manual review recommended. Error: {str(e)[:100]}",
                "confidence": "LOW",
                "key_findings": ["AI evaluation failed - requires manual assessment"]
            }
    
    def analyze_evidence(
        self,
        question_text: str,
        question_code: str,
        scoring_rubric: Optional[Dict] = None,
        file_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        filename: Optional[str] = None,
        existing_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze an uploaded evidence file against an RMI question.

        - Images: sent to GPT-4o vision.
        - PDFs: best-effort text extraction (pypdf if available), then scored
          as text. If text extraction fails, returns a manual-review flag.
        - Anything else: manual review.

        Returns:
            {
                "numeric_score": float (1-5) | None,
                "observations": str,
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "key_findings": [str, ...],
                "analyzed_kind": "image" | "pdf" | "unsupported",
            }
        """
        if not file_bytes or not mime_type:
            return {
                "numeric_score": None,
                "observations": "No evidence file provided.",
                "confidence": "LOW",
                "key_findings": [],
                "analyzed_kind": "unsupported",
            }

        mime = mime_type.lower()
        rubric_block = self._format_rubric(scoring_rubric)
        notes_block = f"\n\n**Auditor notes:** {existing_notes}" if existing_notes else ""

        if mime in IMAGE_MIME_TYPES:
            return self._analyze_image_evidence(
                question_text=question_text,
                question_code=question_code,
                rubric_block=rubric_block,
                notes_block=notes_block,
                file_bytes=file_bytes,
                mime=mime,
            )

        if mime in PDF_MIME_TYPES:
            extracted = self._extract_pdf_text(file_bytes)
            if not extracted:
                return {
                    "numeric_score": None,
                    "observations": (
                        f"Uploaded PDF '{filename or 'evidence.pdf'}' could not be parsed. "
                        "Manual review required."
                    ),
                    "confidence": "LOW",
                    "key_findings": [],
                    "analyzed_kind": "pdf",
                }
            return self._analyze_text_evidence(
                question_text=question_text,
                question_code=question_code,
                rubric_block=rubric_block,
                notes_block=notes_block,
                extracted_text=extracted,
                analyzed_kind="pdf",
            )

        return {
            "numeric_score": None,
            "observations": (
                f"Evidence type {mime} is not supported by AI analysis yet. "
                "Manual review required."
            ),
            "confidence": "LOW",
            "key_findings": [],
            "analyzed_kind": "unsupported",
        }

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    @staticmethod
    def _format_rubric(rubric: Optional[Dict]) -> str:
        if not rubric:
            return ""
        try:
            items = sorted(rubric.items(), key=lambda kv: float(kv[0]))
        except Exception:
            items = list(rubric.items())
        lines = [f"{level}: {desc}" for level, desc in items]
        return "\n**Scoring rubric:**\n" + "\n".join(lines)

    @staticmethod
    def _extract_pdf_text(file_bytes: bytes, max_chars: int = 8000) -> Optional[str]:
        """Best-effort PDF text extraction. Returns None if no extractor is installed."""
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except Exception:
                logger.info("No PDF text extractor (pypdf / PyPDF2) installed.")
                return None

        import io
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            chunks = []
            for page in reader.pages[:20]:  # cap at 20 pages
                try:
                    chunks.append(page.extract_text() or "")
                except Exception:
                    continue
            text = "\n\n".join(c.strip() for c in chunks if c and c.strip())
            return text[:max_chars] if text else None
        except Exception as exc:
            logger.warning("PDF extraction failed: %s", exc)
            return None

    def _analyze_image_evidence(
        self,
        *,
        question_text: str,
        question_code: str,
        rubric_block: str,
        notes_block: str,
        file_bytes: bytes,
        mime: str,
    ) -> Dict[str, Any]:
        b64 = base64.b64encode(file_bytes).decode("ascii")
        data_url = f"data:{mime};base64,{b64}"

        user_prompt = (
            f"You are an RMI (Reliability Maturity) auditor. Inspect this evidence image "
            f"submitted in response to a maturity question.\n\n"
            f"**Question ({question_code}):** {question_text}{rubric_block}{notes_block}\n\n"
            "Decide:\n"
            "1. A suggested maturity score 1-5 (decimals OK) based ONLY on what the image shows.\n"
            "2. 2-4 concrete observations from the image (what you can see — equipment, "
            "boards, screenshots, logs, etc.).\n"
            "3. Confidence (HIGH / MEDIUM / LOW). LOW if the image is ambiguous or unrelated.\n\n"
            "Respond as JSON: "
            '{"numeric_score": <number|null>, "observations": "<string>", '
            '"confidence": "<HIGH|MEDIUM|LOW>", "key_findings": ["<finding>", ...]}'
        )

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert RMI auditor analyzing photo/screenshot "
                            "evidence. Respond ONLY with valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            payload = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.warning("AI image evidence analysis failed: %s", exc)
            return {
                "numeric_score": None,
                "observations": f"AI analysis failed: {str(exc)[:160]}",
                "confidence": "LOW",
                "key_findings": [],
                "analyzed_kind": "image",
            }

        return self._normalize_payload(payload, "image")

    def _analyze_text_evidence(
        self,
        *,
        question_text: str,
        question_code: str,
        rubric_block: str,
        notes_block: str,
        extracted_text: str,
        analyzed_kind: str,
    ) -> Dict[str, Any]:
        prompt = (
            f"You are an RMI (Reliability Maturity) auditor. Analyze the extracted text "
            f"from an evidence document in response to a maturity question.\n\n"
            f"**Question ({question_code}):** {question_text}{rubric_block}{notes_block}\n\n"
            f"**Extracted text:**\n{extracted_text}\n\n"
            "Provide a suggested maturity score (1-5, decimals OK), 2-4 concrete observations, "
            "and a confidence level. If the document doesn't clearly relate to the question, "
            "return numeric_score=null and confidence=LOW.\n\n"
            "Respond as JSON: "
            '{"numeric_score": <number|null>, "observations": "<string>", '
            '"confidence": "<HIGH|MEDIUM|LOW>", "key_findings": ["<finding>", ...]}'
        )

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert RMI auditor analyzing document evidence. "
                            "Respond ONLY with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            payload = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.warning("AI text evidence analysis failed: %s", exc)
            return {
                "numeric_score": None,
                "observations": f"AI analysis failed: {str(exc)[:160]}",
                "confidence": "LOW",
                "key_findings": [],
                "analyzed_kind": analyzed_kind,
            }

        return self._normalize_payload(payload, analyzed_kind)

    @staticmethod
    def _normalize_payload(payload: Dict[str, Any], kind: str) -> Dict[str, Any]:
        raw_score = payload.get("numeric_score")
        score: Optional[float]
        if raw_score is None:
            score = None
        else:
            try:
                score = max(1.0, min(5.0, float(raw_score)))
                score = round(score, 1)
            except (TypeError, ValueError):
                score = None

        confidence = str(payload.get("confidence", "MEDIUM")).upper()
        if confidence not in {"HIGH", "MEDIUM", "LOW"}:
            confidence = "MEDIUM"

        findings = payload.get("key_findings") or []
        if not isinstance(findings, list):
            findings = [str(findings)]

        return {
            "numeric_score": score,
            "observations": str(payload.get("observations") or ""),
            "confidence": confidence,
            "key_findings": [str(f) for f in findings],
            "analyzed_kind": kind,
        }

    def analyze_all_responses(self, responses: list[Dict]) -> Dict:
        """
        Analyze multiple responses for a pillar/assessment
        Returns summary insights and patterns
        """
        if not responses:
            return {"summary": "No responses to analyze"}
        
        response_texts = [r.get("response_value", "") for r in responses if r.get("response_value")]
        
        if not response_texts:
            return {"summary": "No text responses found"}
        
        combined_text = "\n\n".join([f"Response {i+1}: {txt[:500]}" for i, txt in enumerate(response_texts)])
        
        prompt = f"""Analyze these RMI audit responses and provide:
1. Overall maturity trend (improving, stable, declining)
2. Top 3 strengths identified
3. Top 3 gaps or weaknesses
4. Key recommendation for improvement

Responses:
{combined_text}

Provide a concise executive summary (max 200 words)."""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an RMI audit expert providing executive insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            return {
                "summary": response.choices[0].message.content,
                "response_count": len(response_texts)
            }
            
        except Exception as e:
            return {
                "summary": f"AI analysis unavailable: {str(e)}",
                "response_count": len(response_texts)
            }

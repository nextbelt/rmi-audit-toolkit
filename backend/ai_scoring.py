"""
AI-Assisted Scoring Module
Uses OpenAI to evaluate text responses and assign numeric scores
"""
from typing import Optional, Dict
import openai
from config import settings


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

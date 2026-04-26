import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .config import AgentConfig
from .ollama_client import OllamaClient
from .pattern_analyzer import ErrorCluster

logger = logging.getLogger(__name__)

@dataclass
class Evidence:
    question_id: int
    question_url: str
    answer_id: int
    answer_score: int
    is_accepted: bool
    excerpt_summary: str

@dataclass
class VerifiedSuggestion:
    cluster_id: str
    tag: str
    title: str
    summary: str
    status: str  # "VERIFIED" | "UNVERIFIED" | "LOW_CONFIDENCE"
    confidence_score: float
    evidence: List[Evidence]
    reasoning: str
    warning: Optional[str]

class SolutionVerifier:
    def __init__(self, config: AgentConfig, llm: OllamaClient):
        self.config = config
        self.llm = llm

    def verify_cluster(self, cluster: ErrorCluster, answers: List[Dict]) -> VerifiedSuggestion:
        cluster_answers = [a for a in answers if a.get("question_id") in cluster.question_ids]
        supporting_answers = cluster_answers

        if len(supporting_answers) < 3:
            return self._create_unverified(cluster, "Insufficient supporting answers (< 3)")

        if not any(a.get("is_accepted", False) for a in supporting_answers):
            return self._create_unverified(cluster, "No accepted answers in supporting set")

        total_score = sum(a.get("score", 0) for a in supporting_answers)
        if total_score < 10:
            return self._create_unverified(cluster, f"Total answer score too low ({total_score} < 10)")

        verification_result = self._llm_verify_answers(cluster, supporting_answers[:5])
        if not verification_result.get("solution_found", False):
            return self._create_unverified(cluster, "LLM found no consistent solution")

        top_evidence = sorted(
            supporting_answers,
            key=lambda answer: (
                0 if answer.get("is_accepted", False) else 1,
                -(answer.get("score", 0)),
            ),
        )[:5]

        evidence_list: List[Evidence] = []
        for answer in top_evidence:
            summary = self._summarize_answer_excerpt(answer.get("body", ""))
            evidence_list.append(Evidence(
                question_id=answer.get("question_id", 0),
                question_url=answer.get("link") or f"https://stackoverflow.com/questions/{answer.get('question_id')}",
                answer_id=answer.get("answer_id", 0),
                answer_score=answer.get("score", 0),
                is_accepted=answer.get("is_accepted", False),
                excerpt_summary=summary,
            ))

        confidence_score = self._calculate_confidence(supporting_answers)
        low_confidence_reasons: List[str] = []

        if confidence_score < self.config.confidence_threshold:
            low_confidence_reasons.append(
                f"Confidence score {confidence_score:.2f} below threshold {self.config.confidence_threshold}"
            )

        if len(cluster.question_ids) < 10:
            low_confidence_reasons.append("Insufficient sample size (< 10 questions)")

        status = "VERIFIED"
        warning = None
        if low_confidence_reasons:
            status = "LOW_CONFIDENCE"
            warning = "; ".join(low_confidence_reasons)

        title = verification_result.get("solution_summary") or cluster.label
        summary = verification_result.get("solution_summary") or ""
        reasoning = verification_result.get("confidence_reason") or "Verified solution appears in the provided answers."

        return VerifiedSuggestion(
            cluster_id=cluster.cluster_id,
            tag=cluster.cluster_id.split("_")[0] if "_" in cluster.cluster_id else "",
            title=title,
            summary=summary,
            status=status,
            confidence_score=confidence_score,
            evidence=evidence_list,
            reasoning=reasoning,
            warning=warning,
        )

    def _create_unverified(self, cluster: ErrorCluster, reason: str) -> VerifiedSuggestion:
        return VerifiedSuggestion(
            cluster_id=cluster.cluster_id,
            tag=cluster.cluster_id.split("_")[0] if "_" in cluster.cluster_id else "",
            title=cluster.label,
            summary="",
            status="UNVERIFIED",
            confidence_score=0.0,
            evidence=[],
            reasoning=reason,
            warning=None,
        )

    def _llm_verify_answers(self, cluster: ErrorCluster, answers: List[Dict]) -> Dict[str, Optional[str]]:
        body_snippets: List[str] = []
        total_chars = 0
        for answer in answers:
            body = answer.get("body", "") or ""
            truncated_body = body[:500] + " [truncated]" if len(body) > 500 else body
            if total_chars + len(truncated_body) > 2000:
                break
            body_snippets.append(truncated_body)
            total_chars += len(truncated_body)

        answer_text = "\n".join(
            f"Answer {i + 1}: {snippet}"
            for i, snippet in enumerate(body_snippets)
        )

        prompt = (
            f"Read these StackOverflow answers about {cluster.label}:\n"
            f"{answer_text}\n"
            "Does a consistent solution or fix appear across these answers?\n"
            "Respond with JSON: {\n"
            "  \"solution_found\": true/false,\n"
            "  \"solution_summary\": \"one sentence if found, else null\",\n"
            "  \"confidence_reason\": \"one sentence explanation\"\n"
            "}\n"
            "Only reference content from the answers provided above."
        )
        schema_hint = json.dumps({
            "solution_found": "true/false",
            "solution_summary": "one sentence if found, else null",
            "confidence_reason": "one sentence explanation",
        })

        try:
            result = self.llm.generate_json(prompt, schema_hint)
            if not isinstance(result, dict):
                raise ValueError("LLM returned invalid JSON for verification")
            return {
                "solution_found": bool(result.get("solution_found", False)),
                "solution_summary": result.get("solution_summary") if result.get("solution_summary") else None,
                "confidence_reason": str(result.get("confidence_reason", "")),
            }
        except Exception as exc:
            logger.warning("LLM answer verification failed for cluster %s: %s", cluster.cluster_id, exc)
            return {
                "solution_found": False,
                "solution_summary": None,
                "confidence_reason": "LLM verification error",
            }

    def _summarize_answer_excerpt(self, body: str) -> str:
        answer_body = body[:500] + " [truncated]" if len(body) > 500 else body
        prompt = (
            "Summarize the solution or fix described in this StackOverflow answer in no more than two sentences. "
            "Only reference the answer content provided.\n\n"
            f"{answer_body}\n\n"
            "Response:"
        )
        try:
            summary = self.llm.generate(prompt)
            return " ".join(summary.split())[:280]
        except Exception as exc:
            logger.warning("LLM evidence summarization failed: %s", exc)
            return answer_body[:280]

    def _calculate_confidence(self, supporting_answers: List[Dict]) -> float:
        verified_ratio = min(len(supporting_answers) / 10, 1.0) * 0.35
        avg_score = sum(a.get("score", 0) for a in supporting_answers) / len(supporting_answers) if supporting_answers else 0
        score_ratio = min(avg_score / 50, 1.0) * 0.25
        accepted_count = sum(1 for a in supporting_answers if a.get("is_accepted", False))
        total_answers = len(supporting_answers)
        accepted_ratio = (accepted_count / total_answers) * 0.25 if total_answers > 0 else 0
        now = datetime.now()
        has_recent = any(
            (now - datetime.fromtimestamp(a.get("creation_date", 0))).days < 30
            for a in supporting_answers
            if a.get("creation_date") is not None
        )
        recency_weight = (1.0 if has_recent else 0.5) * 0.15
        confidence = verified_ratio + score_ratio + accepted_ratio + recency_weight
        return min(confidence, 1.0)
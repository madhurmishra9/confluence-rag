import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .cache_manager import CacheManager
from .config import AgentConfig
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

@dataclass
class ErrorCluster:
    cluster_id: str
    label: str
    question_count: int
    question_ids: List[int]
    question_urls: List[str]
    top_error_string: str
    first_seen_date: str
    last_seen_date: str
    trend_direction: str
    is_emerging: bool
    avg_score: float
    has_accepted_answers: bool

@dataclass
class TagAnalysis:
    tag: str
    total_questions: int
    answered_count: int
    unanswered_count: int
    unanswered_7d_plus: List[Dict]
    avg_time_to_answer_hours: Optional[float]
    question_velocity_7d: int
    trend_direction: str
    clusters: List[ErrorCluster]
    analysis_timestamp: str

class PatternAnalyzer:
    def __init__(self, config: AgentConfig, llm: OllamaClient, cache: CacheManager):
        self.config = config
        self.llm = llm
        self.cache = cache

    def analyze(self, questions: List[Dict], answers: List[Dict], tag: str) -> TagAnalysis:
        now = datetime.now()
        analysis_timestamp = now.isoformat()

        total_questions = len(questions)
        answered_questions = [q for q in questions if q.get("is_answered", False)]
        answered_count = len(answered_questions)
        unanswered_count = total_questions - answered_count

        unanswered_7d_plus = []
        for q in questions:
            if not q.get("is_answered", False):
                created_at = q.get("creation_date")
                if created_at is None:
                    continue
                created_dt = datetime.fromtimestamp(created_at)
                if now - created_dt >= timedelta(days=7):
                    unanswered_7d_plus.append(q)

        avg_time_to_answer_hours = self._compute_avg_time_to_answer_hours(answered_questions, answers)

        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        question_velocity_7d = sum(
            1 for q in questions
            if q.get("creation_date") is not None and datetime.fromtimestamp(q["creation_date"]) >= week_ago
        )

        last_7d_count = sum(
            1 for q in questions
            if q.get("creation_date") is not None and datetime.fromtimestamp(q["creation_date"]) >= week_ago
        )
        prior_7d_count = sum(
            1 for q in questions
            if q.get("creation_date") is not None and two_weeks_ago <= datetime.fromtimestamp(q["creation_date"]) < week_ago
        )

        if prior_7d_count == 0:
            trend_direction = "STABLE"
        else:
            ratio = last_7d_count / prior_7d_count
            if ratio > 1.3:
                trend_direction = "INCREASING"
            elif ratio < 0.7:
                trend_direction = "DECREASING"
            else:
                trend_direction = "STABLE"

        clusters = self._cluster_questions(questions, answers, tag)

        return TagAnalysis(
            tag=tag,
            total_questions=total_questions,
            answered_count=answered_count,
            unanswered_count=unanswered_count,
            unanswered_7d_plus=unanswered_7d_plus,
            avg_time_to_answer_hours=avg_time_to_answer_hours,
            question_velocity_7d=question_velocity_7d,
            trend_direction=trend_direction,
            clusters=clusters,
            analysis_timestamp=analysis_timestamp,
        )

    def _compute_avg_time_to_answer_hours(self, answered_questions: List[Dict], answers: List[Dict]) -> Optional[float]:
        answers_by_question = {}
        for answer in answers:
            qid = answer.get("question_id")
            if qid is None:
                continue
            answers_by_question.setdefault(qid, []).append(answer)

        answer_hours = []
        for question in answered_questions:
            qid = question.get("question_id")
            if qid is None or qid not in answers_by_question:
                continue
            first_answer = min(
                answers_by_question[qid],
                key=lambda answer: answer.get("creation_date", float("inf"))
            )
            if first_answer.get("creation_date") is None or question.get("creation_date") is None:
                continue
            q_time = datetime.fromtimestamp(question["creation_date"])
            a_time = datetime.fromtimestamp(first_answer["creation_date"])
            answer_hours.append((a_time - q_time).total_seconds() / 3600)

        return sum(answer_hours) / len(answer_hours) if answer_hours else None

    def _cluster_questions(self, questions: List[Dict], answers: List[Dict], tag: str) -> List[ErrorCluster]:
        keyword_groups: Dict[str, List[Dict]] = {}
        for question in questions:
            title = question.get("title", "")
            keywords = self._extract_keywords(title)
            if not keywords:
                continue
            selected_keyword = self._select_keyword(keywords)
            if not selected_keyword:
                continue
            keyword_groups.setdefault(selected_keyword, []).append(question)

        valid_clusters = {k: v for k, v in keyword_groups.items() if len(v) >= 3}
        if not valid_clusters:
            return []

        answers_by_question: Dict[int, List[Dict]] = {}
        for answer in answers:
            qid = answer.get("question_id")
            if qid is None:
                continue
            answers_by_question.setdefault(qid, []).append(answer)

        clusters: List[ErrorCluster] = []
        cluster_index = 0
        for keyword, cluster_questions in sorted(valid_clusters.items(), key=lambda item: len(item[1]), reverse=True):
            cluster_index += 1
            question_ids = [q["question_id"] for q in cluster_questions if q.get("question_id") is not None]
            question_urls = [
                q.get("link") or f"https://stackoverflow.com/questions/{q['question_id']}"
                for q in cluster_questions
                if q.get("question_id") is not None
            ]
            scores = [q.get("score", 0) for q in cluster_questions if isinstance(q.get("score"), (int, float))]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            dates = [datetime.fromtimestamp(q["creation_date"]) for q in cluster_questions if q.get("creation_date") is not None]
            first_seen_date = min(dates).isoformat() if dates else ""
            last_seen_date = max(dates).isoformat() if dates else ""
            is_emerging = (datetime.now() - min(dates)).days < 7 if dates else False
            recent_dates = [d for d in dates if d >= datetime.now() - timedelta(days=7)]
            prior_dates = [d for d in dates if datetime.now() - timedelta(days=14) <= d < datetime.now() - timedelta(days=7)]
            if len(prior_dates) == 0:
                trend_direction = "STABLE"
            else:
                ratio = len(recent_dates) / len(prior_dates)
                if ratio > 1.3:
                    trend_direction = "INCREASING"
                elif ratio < 0.7:
                    trend_direction = "DECREASING"
                else:
                    trend_direction = "STABLE"

            has_accepted_answers = any(
                answer.get("is_accepted", False)
                for qid in question_ids
                for answer in answers_by_question.get(qid, [])
            )

            label, top_error_string = self._llm_label_cluster(cluster_questions[:10], tag, keyword)

            clusters.append(ErrorCluster(
                cluster_id=f"{tag}_{cluster_index}",
                label=label,
                question_count=len(cluster_questions),
                question_ids=question_ids,
                question_urls=question_urls,
                top_error_string=top_error_string,
                first_seen_date=first_seen_date,
                last_seen_date=last_seen_date,
                trend_direction=trend_direction,
                is_emerging=is_emerging,
                avg_score=avg_score,
                has_accepted_answers=has_accepted_answers,
            ))

        return clusters

    def _extract_keywords(self, title: str) -> List[str]:
        keywords: List[str] = []
        if not title:
            return keywords

        keywords.extend(re.findall(r"\b[A-Z][a-zA-Z]+Error\b", title))
        keywords.extend(re.findall(r"\b[45]\d{2}\b", title))
        keywords.extend(re.findall(r"\bSTATUS_[A-Z_]+\b", title))
        keywords.extend(re.findall(
            r"\b[A-Za-z_][A-Za-z0-9_]*\(\)\b|\b(?:[A-Za-z_][A-Za-z0-9_]*\.)+[A-Za-z_][A-Za-z0-9_]*\b",
            title,
        ))

        return [kw for kw in keywords if kw]

    def _select_keyword(self, keywords: List[str]) -> Optional[str]:
        priority_patterns = [
            r"^[A-Z][a-zA-Z]+Error$",
            r"^[45]\d{2}$",
            r"^STATUS_[A-Z_]+$",
        ]
        for pattern in priority_patterns:
            for keyword in keywords:
                if re.match(pattern, keyword):
                    return keyword
        return max(set(keywords), key=keywords.count) if keywords else None

    def _llm_label_cluster(self, questions: List[Dict], tag: str, fallback_keyword: str) -> Tuple[str, str]:
        titles = [q.get("title", "") for q in questions]
        prompt = (
            f"Given these StackOverflow question titles about {tag}:\n"
            + "\n".join(f"- {title}" for title in titles)
            + "\nIdentify the common error pattern.\n"
            + "Respond with JSON: {\n  \"label\": \"short label max 8 words\",\n  \"top_error_string\": \"exact error or pattern\",\n  \"root_cause_hypothesis\": \"one sentence, factual only\"\n}\n"
            + "Base your answer ONLY on the titles provided."
        )
        schema_hint = json.dumps({
            "label": "short label max 8 words",
            "top_error_string": "exact error or pattern",
            "root_cause_hypothesis": "one sentence, factual only",
        })

        try:
            result = self.llm.generate_json(prompt, schema_hint)
            if not isinstance(result, dict):
                raise ValueError("LLM returned invalid JSON for cluster label")
            label = str(result.get("label", "")).strip()
            top_error_string = str(result.get("top_error_string", "")).strip()
            if not label or "UNCERTAIN" in label.upper():
                return fallback_keyword, fallback_keyword
            if not top_error_string:
                top_error_string = fallback_keyword
            return label, top_error_string
        except Exception as exc:
            logger.warning("LLM cluster labeling failed for tag %s: %s", tag, exc)
            return fallback_keyword, fallback_keyword
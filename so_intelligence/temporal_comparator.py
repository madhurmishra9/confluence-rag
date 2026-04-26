import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .config import AgentConfig
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class PeriodMetrics:
    """Metrics for a time period (before or after intervention)."""
    period_label: str  # "PRE" or "POST"
    question_count: int
    unanswered_rate: float
    avg_time_to_answer_hours: Optional[float]
    avg_answer_score: float
    unique_error_clusters: int
    date_range: Tuple[str, str]  # (start_iso, end_iso)


@dataclass
class MetricDelta:
    """Change in a metric between periods."""
    metric_name: str
    pre_value: float
    post_value: float
    delta: float  # post - pre
    delta_pct: float  # (post - pre) / pre * 100
    trend: str  # "↑" | "↓" | "→"
    significance: str  # "SIGNIFICANT" | "MARGINAL" | "INSUFFICIENT_DATA"


@dataclass
class ComparisonResult:
    """Result of temporal comparison before/after intervention."""
    tag: str
    intervention_date: str
    pre_period: PeriodMetrics
    post_period: PeriodMetrics
    deltas: Dict[str, MetricDelta] = field(default_factory=dict)
    verdict: str = "NEUTRAL"  # "IMPROVED" | "NEUTRAL" | "WORSENED" | "INSUFFICIENT_DATA"
    regressions: List[str] = field(default_factory=list)  # clusters in POST but not PRE
    resolutions: List[str] = field(default_factory=list)  # clusters in PRE but not POST
    insufficient_data_warning: Optional[str] = None


class TemporalComparator:
    """Analyzes before/after metrics around an intervention date."""

    def __init__(self, config: AgentConfig, cache: CacheManager):
        self.config = config
        self.cache = cache

    def compare(
        self,
        tag: str,
        intervention_date: str,
        questions: List[Dict],
        answers: List[Dict],
    ) -> ComparisonResult:
        """
        Compare metrics before and after an intervention date.

        Args:
            tag: Stack Overflow tag
            intervention_date: ISO 8601 date string (YYYY-MM-DD)
            questions: List of question dicts with creation_date (Unix timestamp)
            answers: List of answer dicts

        Returns:
            ComparisonResult with computed deltas and verdict
        """
        # Parse intervention date
        intervention_dt = datetime.fromisoformat(intervention_date)
        intervention_ts = int(intervention_dt.timestamp())

        # Split questions into pre/post periods
        pre_questions = [
            q for q in questions
            if q.get("creation_date") is not None and q["creation_date"] < intervention_ts
        ]
        post_questions = [
            q for q in questions
            if q.get("creation_date") is not None and q["creation_date"] >= intervention_ts
        ]

        # Compute metrics for each period
        pre_metrics = self._compute_period_metrics(
            pre_questions, answers, "PRE", tag
        )
        post_metrics = self._compute_period_metrics(
            post_questions, answers, "POST", tag
        )

        # Compute deltas
        deltas = self._compute_deltas(pre_metrics, post_metrics)

        # Determine verdict
        verdict, insufficient_warning = self._determine_verdict(
            pre_metrics, post_metrics, deltas
        )

        # Find regressions and resolutions
        pre_clusters = self._extract_cluster_labels(pre_questions)
        post_clusters = self._extract_cluster_labels(post_questions)
        regressions = [c for c in post_clusters if c not in pre_clusters]
        resolutions = [c for c in pre_clusters if c not in post_clusters]

        return ComparisonResult(
            tag=tag,
            intervention_date=intervention_date,
            pre_period=pre_metrics,
            post_period=post_metrics,
            deltas=deltas,
            verdict=verdict,
            regressions=regressions,
            resolutions=resolutions,
            insufficient_data_warning=insufficient_warning,
        )

    def _compute_period_metrics(
        self,
        questions: List[Dict],
        answers: List[Dict],
        period_label: str,
        tag: str,
    ) -> PeriodMetrics:
        """Compute all metrics for a period."""
        question_count = len(questions)

        # Unanswered rate
        unanswered = sum(
            1 for q in questions if not q.get("is_answered", False)
        )
        unanswered_rate = unanswered / question_count if question_count > 0 else 0.0

        # Average time to answer
        avg_time_to_answer_hours = self._compute_avg_time_to_answer(
            questions, answers
        )

        # Average answer score
        answered_questions = [
            q for q in questions if q.get("is_answered", False)
        ]
        if answered_questions:
            question_ids = [
                q["question_id"] for q in answered_questions
                if q.get("question_id") is not None
            ]
            period_answers = [
                a for a in answers
                if a.get("question_id") in question_ids
            ]
            avg_answer_score = (
                sum(a.get("score", 0) for a in period_answers) / len(period_answers)
                if period_answers
                else 0.0
            )
        else:
            avg_answer_score = 0.0

        # Unique error clusters (approximated by unique error patterns in titles)
        unique_clusters = len(self._extract_cluster_labels(questions))

        # Date range
        if questions:
            dates = sorted([
                datetime.fromtimestamp(q["creation_date"])
                for q in questions
                if q.get("creation_date") is not None
            ])
            date_range = (dates[0].isoformat(), dates[-1].isoformat())
        else:
            date_range = ("", "")

        return PeriodMetrics(
            period_label=period_label,
            question_count=question_count,
            unanswered_rate=unanswered_rate,
            avg_time_to_answer_hours=avg_time_to_answer_hours,
            avg_answer_score=avg_answer_score,
            unique_error_clusters=unique_clusters,
            date_range=date_range,
        )

    def _compute_avg_time_to_answer(
        self, questions: List[Dict], answers: List[Dict]
    ) -> Optional[float]:
        """Compute average time from question to first answer in hours."""
        answers_by_question = {}
        for answer in answers:
            qid = answer.get("question_id")
            if qid is None:
                continue
            answers_by_question.setdefault(qid, []).append(answer)

        times_hours = []
        for question in questions:
            if not question.get("is_answered", False):
                continue
            qid = question.get("question_id")
            if qid is None or qid not in answers_by_question:
                continue
            q_time = question.get("creation_date")
            if q_time is None:
                continue
            first_answer = min(
                answers_by_question[qid],
                key=lambda a: a.get("creation_date", float("inf")),
            )
            a_time = first_answer.get("creation_date")
            if a_time is None:
                continue
            hours = (a_time - q_time) / 3600.0
            times_hours.append(hours)

        return sum(times_hours) / len(times_hours) if times_hours else None

    def _extract_cluster_labels(self, questions: List[Dict]) -> List[str]:
        """Extract unique error pattern labels from questions."""
        import re
        clusters = set()
        for q in questions:
            title = q.get("title", "")
            # Extract error names and status codes
            errors = re.findall(r"\b[A-Z][a-zA-Z]+Error\b", title)
            codes = re.findall(r"\b[45]\d{2}\b", title)
            clusters.update(errors)
            clusters.update(codes)
        return list(clusters)

    def _compute_deltas(
        self, pre_metrics: PeriodMetrics, post_metrics: PeriodMetrics
    ) -> Dict[str, MetricDelta]:
        """Compute metric deltas between periods."""
        deltas = {}

        # Unanswered rate delta
        if pre_metrics.unanswered_rate > 0:
            delta_pct = (
                (post_metrics.unanswered_rate - pre_metrics.unanswered_rate)
                / pre_metrics.unanswered_rate
                * 100
            )
        else:
            delta_pct = 0.0

        trend = "↓" if post_metrics.unanswered_rate < pre_metrics.unanswered_rate else (
            "↑" if post_metrics.unanswered_rate > pre_metrics.unanswered_rate else "→"
        )
        significance = self._assess_significance(
            post_metrics.unanswered_rate, pre_metrics.unanswered_rate
        )

        deltas["unanswered_rate"] = MetricDelta(
            metric_name="unanswered_rate",
            pre_value=pre_metrics.unanswered_rate,
            post_value=post_metrics.unanswered_rate,
            delta=post_metrics.unanswered_rate - pre_metrics.unanswered_rate,
            delta_pct=delta_pct,
            trend=trend,
            significance=significance,
        )

        # Time to answer delta
        if (
            pre_metrics.avg_time_to_answer_hours is not None
            and post_metrics.avg_time_to_answer_hours is not None
        ):
            pre_val = pre_metrics.avg_time_to_answer_hours
            post_val = post_metrics.avg_time_to_answer_hours
            delta_pct = (post_val - pre_val) / pre_val * 100 if pre_val > 0 else 0.0
            trend = "↓" if post_val < pre_val else (
                "↑" if post_val > pre_val else "→"
            )
            significance = self._assess_significance(post_val, pre_val)

            deltas["avg_time_to_answer"] = MetricDelta(
                metric_name="avg_time_to_answer_hours",
                pre_value=pre_val,
                post_value=post_val,
                delta=post_val - pre_val,
                delta_pct=delta_pct,
                trend=trend,
                significance=significance,
            )

        # Question count delta
        pre_count = pre_metrics.question_count
        post_count = post_metrics.question_count
        if pre_count > 0:
            delta_pct = (post_count - pre_count) / pre_count * 100
        else:
            delta_pct = 0.0

        trend = "↓" if post_count < pre_count else (
            "↑" if post_count > pre_count else "→"
        )

        deltas["question_count"] = MetricDelta(
            metric_name="question_count",
            pre_value=float(pre_count),
            post_value=float(post_count),
            delta=float(post_count - pre_count),
            delta_pct=delta_pct,
            trend=trend,
            significance="MARGINAL",
        )

        # Answer score delta
        if pre_metrics.avg_answer_score > 0:
            delta_pct = (
                (post_metrics.avg_answer_score - pre_metrics.avg_answer_score)
                / pre_metrics.avg_answer_score
                * 100
            )
        else:
            delta_pct = 0.0

        trend = "↑" if post_metrics.avg_answer_score > pre_metrics.avg_answer_score else (
            "↓" if post_metrics.avg_answer_score < pre_metrics.avg_answer_score else "→"
        )
        significance = self._assess_significance(
            post_metrics.avg_answer_score, pre_metrics.avg_answer_score
        )

        deltas["avg_answer_score"] = MetricDelta(
            metric_name="avg_answer_score",
            pre_value=pre_metrics.avg_answer_score,
            post_value=post_metrics.avg_answer_score,
            delta=post_metrics.avg_answer_score - pre_metrics.avg_answer_score,
            delta_pct=delta_pct,
            trend=trend,
            significance=significance,
        )

        return deltas

    def _assess_significance(self, post_val: float, pre_val: float) -> str:
        """Assess whether a change is significant, marginal, or insufficient."""
        if pre_val == 0:
            return "INSUFFICIENT_DATA"
        delta_pct = abs((post_val - pre_val) / pre_val * 100)
        if delta_pct > 15:
            return "SIGNIFICANT"
        elif delta_pct > 5:
            return "MARGINAL"
        else:
            return "INSUFFICIENT_DATA"

    def _determine_verdict(
        self,
        pre_metrics: PeriodMetrics,
        post_metrics: PeriodMetrics,
        deltas: Dict[str, MetricDelta],
    ) -> Tuple[str, Optional[str]]:
        """Determine overall verdict based on metrics."""
        insufficient_warning = None

        # Check for insufficient data
        if post_metrics.question_count < 30:
            insufficient_warning = (
                f"POST-intervention period has only {post_metrics.question_count} "
                "questions (< 30 threshold for statistical confidence)"
            )
            return "INSUFFICIENT_DATA", insufficient_warning

        # Compute average delta for key metrics
        key_metrics = ["unanswered_rate", "avg_time_to_answer"]
        relevant_deltas = [
            deltas[m] for m in key_metrics if m in deltas
        ]

        if not relevant_deltas:
            return "NEUTRAL", None

        avg_delta_pct = sum(d.delta_pct for d in relevant_deltas) / len(relevant_deltas)

        # IMPROVED: key metrics decreased and question count stable or decreased
        question_delta_pct = deltas["question_count"].delta_pct
        if avg_delta_pct < -10 and question_delta_pct < 0:
            return "IMPROVED", None

        # WORSENED: any key metric increased > 15%
        if any(d.delta_pct > 15 for d in relevant_deltas):
            return "WORSENED", None

        # Otherwise neutral
        return "NEUTRAL", None

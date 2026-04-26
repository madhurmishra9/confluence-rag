import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

from .config import AgentConfig
from .cache_manager import CacheManager
from .ollama_client import OllamaClient, OllamaConnectionError
from .so_fetcher import StackOverflowFetcher, AuthenticationError, APIUnavailableError
from .data_validator import DataValidator, ValidationHaltError
from .pattern_analyzer import PatternAnalyzer, TagAnalysis
from .solution_verifier import SolutionVerifier, VerifiedSuggestion
from .temporal_comparator import TemporalComparator, ComparisonResult

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class TagAnalysisResult:
    """Result of analyzing a single tag."""
    tag: str
    status: str  # "SUCCESS" | "FAILED"
    analysis: Optional[TagAnalysis] = None
    suggestions: List[VerifiedSuggestion] = field(default_factory=list)
    comparison: Optional[ComparisonResult] = None
    error: Optional[str] = None


@dataclass
class RunResult:
    """Result of a full orchestrator run."""
    run_id: str
    status: str  # "SUCCESS" | "PARTIAL" | "FAILED"
    tags_analyzed: List[str]
    tag_analyses: Dict[str, TagAnalysisResult] = field(default_factory=dict)
    suggestions: Dict[str, List[VerifiedSuggestion]] = field(default_factory=dict)
    comparisons: Optional[Dict[str, ComparisonResult]] = None
    report_paths: Dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class OrchestratorFailureError(Exception):
    """Raised when the orchestrator encounters a critical failure."""
    pass


class SOIntelligenceOrchestrator:
    """Main orchestrator for Stack Overflow intelligence pipeline."""

    def __init__(self, config: AgentConfig):
        """
        Initialize orchestrator and all components.

        Args:
            config: AgentConfig instance

        Raises:
            OllamaConnectionError: If Ollama is not responding
            AuthenticationError: If SO token is invalid
        """
        self.config = config
        self.run_id = str(uuid.uuid4())

        # Initialize components
        self.cache = CacheManager(config)
        self.llm = OllamaClient(config)
        self.fetcher = StackOverflowFetcher(config)
        self.validator = DataValidator()
        self.analyzer = PatternAnalyzer(config, self.llm, self.cache)
        self.verifier = SolutionVerifier(config, self.llm)
        self.temporal_comparator = TemporalComparator(config, self.cache)

        # Validate startup
        self._validate_startup()

    def _validate_startup(self) -> None:
        """Validate Ollama connection and SO token."""
        logger.info("Validating startup configuration...")

        # Check Ollama
        if not self.llm.ping():
            error_msg = f"Ollama is not responding at {self.config.ollama_base_url}"
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg)
        logger.info("✓ Ollama connection verified")

        # Check SO token
        if not self.config.so_api_token:
            error_msg = "SO_API_TOKEN environment variable not set"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)
        logger.info("✓ SO API token configured")

        # Log startup summary
        logger.info(
            "Orchestrator initialized: run_id=%s, model=%s, tags=%d",
            self.run_id,
            self.config.ollama_model,
            len(self.config.default_tags),
        )

    def run(
        self,
        tags: Optional[List[str]] = None,
        date_range_days: Optional[int] = None,
        intervention_date: Optional[str] = None,
        force_refresh: bool = False,
    ) -> RunResult:
        """
        Execute the full intelligence pipeline.

        Args:
            tags: List of SO tags to analyze (default: config.default_tags)
            date_range_days: Days of history to fetch (default: config.date_range_days)
            intervention_date: ISO 8601 date for temporal comparison (optional)
            force_refresh: Skip cache and fetch fresh data

        Returns:
            RunResult with analysis results and any errors
        """
        start_time = datetime.now()
        tags = tags or self.config.default_tags
        date_range_days = date_range_days or self.config.date_range_days

        result = RunResult(
            run_id=self.run_id,
            status="SUCCESS",
            tags_analyzed=tags,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Initialize
            task = progress.add_task("Initializing pipeline...", total=None)
            try:
                self._step_initialize()
                progress.update(task, description="✓ Pipeline initialized")
            except Exception as e:
                error_msg = f"Initialization failed: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.status = "FAILED"
                result.duration_seconds = (
                    datetime.now() - start_time
                ).total_seconds()
                return result

            # Step 2: Fetch
            task = progress.add_task("Fetching data for all tags...", total=len(tags))
            fetch_results = {}
            for tag in tags:
                try:
                    fetch_results[tag] = self._step_fetch(
                        tag, date_range_days, force_refresh
                    )
                    progress.advance(task)
                except Exception as e:
                    error_msg = f"Fetch failed for tag '{tag}': {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    progress.advance(task)

            # Check if ALL tags failed
            if len(fetch_results) == 0:
                error_msg = (
                    "All tags failed to fetch. Pipeline cannot continue."
                )
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.status = "FAILED"
                result.duration_seconds = (
                    datetime.now() - start_time
                ).total_seconds()
                raise OrchestratorFailureError(error_msg)

            logger.info(
                "Fetched data for %d/%d tags",
                len(fetch_results),
                len(tags),
            )

            # Step 3: Analyze
            task = progress.add_task("Analyzing patterns...", total=len(fetch_results))
            for tag, (questions, answers) in fetch_results.items():
                try:
                    analysis = self._step_analyze(tag, questions, answers)
                    tag_result = TagAnalysisResult(
                        tag=tag,
                        status="SUCCESS",
                        analysis=analysis,
                    )
                    result.tag_analyses[tag] = tag_result
                    progress.advance(task)
                except Exception as e:
                    error_msg = f"Analysis failed for tag '{tag}': {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    tag_result = TagAnalysisResult(
                        tag=tag,
                        status="FAILED",
                        error=error_msg,
                    )
                    result.tag_analyses[tag] = tag_result
                    progress.advance(task)

            # Step 4: Verify
            task = progress.add_task("Verifying solutions...", total=len(result.tag_analyses))
            for tag, tag_result in result.tag_analyses.items():
                if tag_result.analysis is None:
                    progress.advance(task)
                    continue

                try:
                    suggestions = self._step_verify(
                        tag_result.analysis,
                        fetch_results[tag][1],  # answers
                    )
                    tag_result.suggestions = suggestions
                    result.suggestions[tag] = suggestions
                    progress.advance(task)
                except Exception as e:
                    error_msg = f"Verification failed for tag '{tag}': {e}"
                    logger.error(error_msg)
                    result.warnings.append(error_msg)
                    progress.advance(task)

            # Step 5: Compare (optional)
            if intervention_date:
                task = progress.add_task("Computing temporal comparisons...", total=len(fetch_results))
                result.comparisons = {}
                for tag, (questions, answers) in fetch_results.items():
                    try:
                        comparison = self._step_compare(
                            tag,
                            intervention_date,
                            questions,
                            answers,
                        )
                        result.comparisons[tag] = comparison
                        if tag in result.tag_analyses:
                            result.tag_analyses[tag].comparison = comparison
                        progress.advance(task)
                    except Exception as e:
                        error_msg = f"Comparison failed for tag '{tag}': {e}"
                        logger.error(error_msg)
                        result.warnings.append(error_msg)
                        progress.advance(task)

        # Check overall status
        successful_tags = sum(
            1 for tr in result.tag_analyses.values()
            if tr.status == "SUCCESS"
        )
        if successful_tags < len(tags):
            result.status = "PARTIAL"

        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Pipeline completed: status=%s, duration=%.1fs, "
            "successful_tags=%d/%d, errors=%d",
            result.status,
            result.duration_seconds,
            successful_tags,
            len(tags),
            len(result.errors),
        )

        return result

    def _step_initialize(self) -> None:
        """Initialize and validate all components."""
        logger.info("Step INITIALIZE: Validating configuration")
        # Components are already validated in __init__
        logger.debug("All components initialized and validated")

    def _step_fetch(
        self,
        tag: str,
        date_range_days: int,
        force_refresh: bool,
    ) -> tuple:
        """
        Fetch questions and answers for a tag.

        Returns:
            (questions, answers) tuple
        """
        logger.info("Step FETCH: Fetching data for tag '%s'", tag)

        # Check cache freshness unless force_refresh
        if not force_refresh and self.cache.is_fresh(tag):
            logger.info("  → Using cached data for tag '%s'", tag)
            to_ts = int(datetime.now().timestamp())
            from_ts = to_ts - (date_range_days * 86400)
            questions = self.cache.get_questions(tag, from_ts, to_ts)
            answers = self.cache.get_answers(
                [q["question_id"] for q in questions if q.get("question_id")]
            )
            return (questions, answers)

        # Fetch from API
        try:
            logger.info("  → Fetching from Stack Overflow API for tag '%s'", tag)
            to_ts = int(datetime.now().timestamp())
            from_ts = to_ts - (date_range_days * 86400)

            questions = self.fetcher.fetch_questions(tag, from_ts, to_ts)
            logger.info(
                "  → Fetched %d questions for tag '%s'",
                len(questions),
                tag,
            )

            answers = self.fetcher.fetch_answers(
                [q["question_id"] for q in questions if q.get("question_id")]
            )
            logger.info(
                "  → Fetched %d answers for tag '%s'",
                len(answers),
                tag,
            )

            # Save to cache
            self.cache.save_questions(questions, tag)
            self.cache.save_answers(answers)

            return (questions, answers)

        except APIUnavailableError as e:
            logger.warning("  → API unavailable: %s. Trying cache fallback.", e)
            # Try to load from cache with STALE warning
            try:
                to_ts = int(datetime.now().timestamp())
                from_ts = to_ts - (date_range_days * 86400)
                questions = self.cache.get_questions(tag, from_ts, to_ts)
                answers = self.cache.get_answers(
                    [q["question_id"] for q in questions if q.get("question_id")]
                )
                if questions:
                    warning = f"Data for tag '{tag}' is stale (API unavailable)"
                    logger.warning("  → %s", warning)
                    # Don't add to result.warnings here; let caller decide
                    return (questions, answers)
            except Exception as cache_err:
                logger.error("  → Cache fallback also failed: %s", cache_err)
                raise APIUnavailableError(
                    f"API unavailable and no cached data: {e}"
                ) from e

            raise

    def _step_analyze(
        self,
        tag: str,
        questions: List[Dict],
        answers: List[Dict],
    ) -> TagAnalysis:
        """Analyze patterns in questions and answers."""
        logger.info("Step ANALYZE: Analyzing tag '%s'", tag)

        # Validate data
        try:
            q_validation = self.validator.validate_questions(questions)
            a_validation = self.validator.validate_answers(answers)

            logger.info(
                "  → Validation: %d/%d questions valid, %d/%d answers valid",
                len(q_validation.passed),
                len(questions),
                len(a_validation.passed),
                len(answers),
            )

            questions = q_validation.passed
            answers = a_validation.passed

        except ValidationHaltError as e:
            logger.error("  → Validation failed: %s", e)
            raise

        # Analyze patterns
        analysis = self.analyzer.analyze(questions, answers, tag)
        logger.info(
            "  → Found %d clusters in tag '%s'",
            len(analysis.clusters),
            tag,
        )

        return analysis

    def _step_verify(
        self,
        analysis: TagAnalysis,
        answers: List[Dict],
    ) -> List[VerifiedSuggestion]:
        """Verify solutions for each cluster."""
        logger.info(
            "Step VERIFY: Verifying %d clusters for tag '%s'",
            len(analysis.clusters),
            analysis.tag,
        )

        suggestions = []
        verified_count = 0
        unverified_count = 0
        low_confidence_count = 0

        for cluster in analysis.clusters:
            suggestion = self.verifier.verify_cluster(cluster, answers)
            suggestions.append(suggestion)

            if suggestion.status == "VERIFIED":
                verified_count += 1
            elif suggestion.status == "UNVERIFIED":
                unverified_count += 1
            else:
                low_confidence_count += 1

        logger.info(
            "  → Verified: %d, Unverified: %d, Low confidence: %d",
            verified_count,
            unverified_count,
            low_confidence_count,
        )

        return suggestions

    def _step_compare(
        self,
        tag: str,
        intervention_date: str,
        questions: List[Dict],
        answers: List[Dict],
    ) -> ComparisonResult:
        """Compare metrics before/after intervention."""
        logger.info(
            "Step COMPARE: Computing temporal comparison for tag '%s' "
            "around intervention date '%s'",
            tag,
            intervention_date,
        )

        comparison = self.temporal_comparator.compare(
            tag,
            intervention_date,
            questions,
            answers,
        )

        logger.info(
            "  → Verdict: %s (PRE: %d qs, POST: %d qs)",
            comparison.verdict,
            comparison.pre_period.question_count,
            comparison.post_period.question_count,
        )

        return comparison

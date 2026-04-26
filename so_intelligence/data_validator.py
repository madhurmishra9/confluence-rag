import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    passed: List[Dict]
    failed: List[Dict]
    quarantined: List[Dict]
    pass_rate: float
    failure_reasons: List[str]
    halt_required: bool

class ValidationHaltError(Exception):
    def __init__(self, error_log_path: str):
        self.error_log_path = error_log_path
        super().__init__(f"Validation failed, see {error_log_path}")

class DataValidator:
    REQUIRED_QUESTION_FIELDS = {
        "question_id": int,
        "title": str,
        "tags": list,
        "creation_date": int,
        "view_count": int,
        "answer_count": int,
        "score": int,
        "is_answered": bool
    }

    REQUIRED_ANSWER_FIELDS = {
        "answer_id": int,
        "question_id": int,
        "creation_date": int,
        "score": int,
        "is_accepted": bool,
        "body": str
    }

    def validate_questions(self, records: List[Dict]) -> ValidationResult:
        return self._validate(records, self.REQUIRED_QUESTION_FIELDS, "questions")

    def validate_answers(self, records: List[Dict]) -> ValidationResult:
        return self._validate(records, self.REQUIRED_ANSWER_FIELDS, "answers")

    def _validate(self, records: List[Dict], required_fields: Dict, record_type: str) -> ValidationResult:
        passed = []
        failed = []
        quarantined = []
        failure_reasons = []

        now = int(datetime.now().timestamp()) + 86400  # now + 1 day

        for record in records:
            reasons = self._check_record(record, required_fields, now, record_type)
            if not reasons:
                passed.append(record)
            else:
                failed.append(record)
                failure_reasons.extend(reasons)

        # Deduplicate by question_id if questions
        if record_type == "questions":
            seen = set()
            deduped_passed = []
            for q in passed:
                qid = q.get("question_id")
                if qid not in seen:
                    seen.add(qid)
                    deduped_passed.append(q)
                else:
                    logger.info(f"Duplicate question_id {qid} removed")
            passed = deduped_passed

        total = len(passed) + len(failed)
        pass_rate = len(passed) / total if total > 0 else 0.0
        halt_required = pass_rate < 0.80

        if halt_required:
            timestamp = int(datetime.now().timestamp())
            error_log_path = f"validation_errors_{timestamp}.json"
            error_data = {
                "timestamp": timestamp,
                "record_type": record_type,
                "total_records": total,
                "passed": len(passed),
                "failed": len(failed),
                "pass_rate": pass_rate,
                "failure_reasons": failure_reasons,
                "failed_records": failed
            }
            with open(error_log_path, "w") as f:
                json.dump(error_data, f, indent=2)
            raise ValidationHaltError(error_log_path)

        return ValidationResult(
            passed=passed,
            failed=failed,
            quarantined=quarantined,
            pass_rate=pass_rate,
            failure_reasons=failure_reasons,
            halt_required=halt_required
        )

    def _check_record(self, record: Dict, required_fields: Dict, now: int, record_type: str) -> List[str]:
        reasons = []

        for field, expected_type in required_fields.items():
            if field not in record:
                reasons.append(f"Missing field: {field}")
                continue

            value = record[field]
            if not isinstance(value, expected_type):
                reasons.append(f"Invalid type for {field}: expected {expected_type.__name__}, got {type(value).__name__}")
                continue

            if field == "creation_date":
                if not (0 < value < now):
                    reasons.append(f"Invalid creation_date: {value}")
            elif field == "tags" and record_type == "questions":
                if not value:
                    reasons.append("Empty tags list")
            elif field == "is_answered" and record_type == "questions":
                if value and record.get("answer_count", 0) == 0:
                    reasons.append("is_answered=True but answer_count=0")
            elif field == "is_accepted" and record_type == "answers":
                if value and not record.get("body", "").strip():
                    reasons.append("is_accepted=True but empty body")
            elif field == "body" and record_type == "answers":
                if len(value.strip()) < 10:
                    reasons.append("Body too short (<10 chars)")
            elif field == "score":
                if not isinstance(value, int):
                    reasons.append(f"Score not integer: {value}")

        return reasons
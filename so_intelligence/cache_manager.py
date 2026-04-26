import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite_utils

from .config import AgentConfig

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.db = sqlite_utils.Database(config.db_path)

        # Ensure tables exist
        self._create_tables()

    def _create_tables(self):
        # raw_questions
        self.db["raw_questions"].create({
            "question_id": int,
            "tag": str,
            "fetched_at": int,
            "payload": str
        }, pk="question_id", if_not_exists=True)

        # raw_answers
        self.db["raw_answers"].create({
            "answer_id": int,
            "question_id": int,
            "fetched_at": int,
            "payload": str
        }, pk="answer_id", if_not_exists=True)

        # analysis_runs
        self.db["analysis_runs"].create({
            "run_id": str,
            "tags": str,  # JSON
            "date_range": str,  # JSON
            "created_at": int,
            "results": str,  # JSON
            "status": str
        }, pk="run_id", if_not_exists=True)

        # api_call_log
        self.db["api_call_log"].create({
            "id": int,
            "endpoint": str,
            "tag": str,
            "page": int,
            "quota_remaining": int,
            "duration_ms": int,
            "called_at": int
        }, pk="id", if_not_exists=True)

        # fetch_meta
        self.db["fetch_meta"].create({
            "tag": str,
            "last_fetched_at": int,
            "question_count": int,
            "is_stale": bool
        }, pk="tag", if_not_exists=True)

    def save_questions(self, questions: List[Dict], tag: str) -> int:
        fetched_at = int(datetime.now().timestamp())
        count = 0
        for q in questions:
            qid = q["question_id"]
            payload = json.dumps(q)
            self.db["raw_questions"].insert({
                "question_id": qid,
                "tag": tag,
                "fetched_at": fetched_at,
                "payload": payload
            }, replace=True)
            count += 1
        return count

    def save_answers(self, answers: List[Dict]) -> int:
        fetched_at = int(datetime.now().timestamp())
        count = 0
        for a in answers:
            aid = a["answer_id"]
            qid = a["question_id"]
            payload = json.dumps(a)
            self.db["raw_answers"].insert({
                "answer_id": aid,
                "question_id": qid,
                "fetched_at": fetched_at,
                "payload": payload
            }, replace=True)
            count += 1
        return count

    def get_questions(self, tag: str, from_date: int, to_date: int) -> List[Dict]:
        rows = self.db["raw_questions"].rows_where(
            "tag = ? AND fetched_at >= ? AND fetched_at <= ?",
            [tag, from_date, to_date]
        )
        return [json.loads(row["payload"]) for row in rows]

    def get_answers(self, question_ids: List[int]) -> List[Dict]:
        if not question_ids:
            return []
        placeholders = ",".join("?" for _ in question_ids)
        rows = self.db["raw_answers"].rows_where(
            f"question_id IN ({placeholders})",
            question_ids
        )
        return [json.loads(row["payload"]) for row in rows]

    def is_fresh(self, tag: str, ttl_hours: int = 6) -> bool:
        row = self.db["fetch_meta"].get(tag)
        if not row:
            return False
        last_fetched = row["last_fetched_at"]
        ttl_seconds = ttl_hours * 3600
        return (int(datetime.now().timestamp()) - last_fetched) < ttl_seconds

    def mark_stale(self, tag: str) -> None:
        self.db["fetch_meta"].insert({
            "tag": tag,
            "last_fetched_at": 0,
            "question_count": 0,
            "is_stale": True
        }, replace=True)

    def log_api_call(self, endpoint: str, tag: str, page: int, quota_remaining: int, duration_ms: int) -> None:
        called_at = int(datetime.now().timestamp())
        self.db["api_call_log"].insert({
            "endpoint": endpoint,
            "tag": tag,
            "page": page,
            "quota_remaining": quota_remaining,
            "duration_ms": duration_ms,
            "called_at": called_at
        })

    def save_run(self, run_id: str, tags: List[str], date_range: Dict, results: Dict, status: str) -> None:
        created_at = int(datetime.now().timestamp())
        self.db["analysis_runs"].insert({
            "run_id": run_id,
            "tags": json.dumps(tags),
            "date_range": json.dumps(date_range),
            "created_at": created_at,
            "results": json.dumps(results),
            "status": status
        }, replace=True)

    def get_last_run(self, tags: List[str]) -> Optional[Dict]:
        # Find runs that include all specified tags
        rows = list(self.db["analysis_runs"].rows_where("status = 'completed'", order_by="created_at DESC"))
        for row in rows:
            run_tags = json.loads(row["tags"])
            if all(tag in run_tags for tag in tags):
                return {
                    "run_id": row["run_id"],
                    "tags": run_tags,
                    "date_range": json.loads(row["date_range"]),
                    "created_at": row["created_at"],
                    "results": json.loads(row["results"]),
                    "status": row["status"]
                }
        return None

    def archive_old_records(self, older_than_days: int = 90) -> int:
        cutoff = int((datetime.now() - timedelta(days=older_than_days)).timestamp())
        count = 0

        # Archive old questions
        old_questions = list(self.db["raw_questions"].rows_where("fetched_at < ?", [cutoff]))
        count += len(old_questions)
        for row in old_questions:
            self.db["raw_questions"].delete(row["question_id"])

        # Archive old answers
        old_answers = list(self.db["raw_answers"].rows_where("fetched_at < ?", [cutoff]))
        count += len(old_answers)
        for row in old_answers:
            self.db["raw_answers"].delete(row["answer_id"])

        # Archive old api calls
        old_calls = list(self.db["api_call_log"].rows_where("called_at < ?", [cutoff]))
        count += len(old_calls)
        for row in old_calls:
            self.db["api_call_log"].delete(row["id"])

        return count

    def get_db_stats(self) -> Dict:
        stats = {}
        for table in ["raw_questions", "raw_answers", "analysis_runs", "api_call_log", "fetch_meta"]:
            stats[table] = self.db[table].count
        # db size - approximate
        import os
        stats["db_size_bytes"] = os.path.getsize(self.config.db_path) if os.path.exists(self.config.db_path) else 0
        return stats
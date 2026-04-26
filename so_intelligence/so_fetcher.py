import logging
import time
from typing import Dict, List, Tuple
import requests

from .config import AgentConfig

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    pass

class InvalidTagError(Exception):
    pass

class APIUnavailableError(Exception):
    pass

class FetchTimeoutError(Exception):
    pass

class NetworkError(Exception):
    pass

class StackOverflowFetcher:
    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self, config: AgentConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "StackOverflowIntelligence/1.0"
        })
        if config.so_api_token:
            self.session.params = {"key": config.so_api_token}
        self.quota_remaining = None

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["site"] = "stackoverflow"

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                self._update_quota(response)

                if response.status_code == 200:
                    data = response.json()
                    backoff = data.get("backoff")
                    if backoff:
                        logger.info(f"API requested backoff: {backoff}s")
                        time.sleep(backoff)
                    return data

                elif response.status_code == 401:
                    raise AuthenticationError("SO_API_TOKEN invalid or expired")

                elif response.status_code == 429:
                    backoff = response.headers.get("backoff", 60)
                    wait_time = int(backoff) * 2
                    logger.warning(f"Rate limited, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                elif response.status_code == 400:
                    raise InvalidTagError("Invalid tag or parameters")

                elif response.status_code in (500, 503):
                    raise APIUnavailableError(f"Stack Overflow API unavailable: {response.status_code}")

                else:
                    response.raise_for_status()

            except requests.Timeout:
                if attempt < 2:
                    delays = [10, 20, 30]
                    time.sleep(delays[attempt])
                    continue
                raise FetchTimeoutError("Request timed out after retries")

            except requests.RequestException as e:
                if attempt < 2:
                    time.sleep(5)
                    continue
                raise NetworkError(f"Network error: {e}")

        raise Exception("Max retries exceeded")

    def _update_quota(self, response):
        quota = response.headers.get("X-RateLimit-Remaining")
        if quota:
            self.quota_remaining = int(quota)
            if self.quota_remaining < 100:
                logger.warning(f"Low API quota remaining: {self.quota_remaining}")

    def fetch_questions(self, tag: str, from_date: int, to_date: int) -> List[Dict]:
        all_questions = []
        page = 1
        has_more = True

        while has_more:
            params = {
                "tagged": tag,
                "fromdate": from_date,
                "todate": to_date,
                "filter": "withbody",
                "sort": "creation",
                "order": "desc",
                "page": page,
                "pagesize": 100
            }

            data = self._make_request("/questions", params)
            questions = data.get("items", [])
            all_questions.extend(questions)

            has_more = data.get("has_more", False)
            page += 1

            backoff = data.get("backoff")
            if backoff:
                time.sleep(backoff)

        return all_questions

    def fetch_answers(self, question_ids: List[int]) -> List[Dict]:
        all_answers = []
        batch_size = 100

        for i in range(0, len(question_ids), batch_size):
            batch = question_ids[i:i+batch_size]
            ids_str = ";".join(str(qid) for qid in batch)

            params = {
                "filter": "withbody",
                "sort": "votes"
            }

            data = self._make_request(f"/questions/{ids_str}/answers", params)
            answers = data.get("items", [])
            all_answers.extend(answers)

        return all_answers

    def validate_tag(self, tag: str) -> Tuple[bool, str]:
        params = {"inname": tag}
        data = self._make_request("/tags", params)
        items = data.get("items", [])

        if items and items[0]["name"] == tag:
            return True, tag

        closest = items[0]["name"] if items else ""
        return False, closest

    def get_tag_info(self, tag: str) -> Dict:
        data = self._make_request(f"/tags/{tag}/info")
        item = data.get("items", [{}])[0]
        return {
            "count": item.get("count", 0),
            "has_synonyms": item.get("has_synonyms", False),
            "is_moderator_only": item.get("is_moderator_only", False)
        }
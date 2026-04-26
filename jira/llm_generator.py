"""
LLM Generator Module - Uses Ollama to generate structured Jira ticket JSON
"""

import json
import os
import requests
from typing import Dict, Any


def validate_story_points(points: int) -> bool:
    """Validate that story points follow Fibonacci scale: 1, 2, 3, 5, 8, 13"""
    valid_points = {1, 2, 3, 5, 8, 13}
    return points in valid_points


def generate_ticket_json(user_description: str) -> Dict[str, Any]:
    """
    Generate structured Jira ticket JSON from user description using Ollama.
    
    Args:
        user_description: Plain English description of the work needed
        
    Returns:
        Parsed JSON dictionary containing ticket structure
        
    Raises:
        ValueError: If Ollama is not running or JSON parsing fails
        KeyError: If required environment variables are missing
    """
    
    # Get Ollama configuration from environment
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
    
    # Structured prompt for LLM
    system_prompt = """You are a Jira ticket generation expert. Your job is to take a user's description 
and generate a well-structured Jira Epic/Story with subtasks and acceptance criteria.

IMPORTANT: You MUST respond with ONLY valid JSON, no markdown, no preamble, no explanation.

The JSON must follow this exact schema:
{
  "summary": "Short ticket title (5-10 words max)",
  "description": "Detailed description of the work to be done",
  "story_points": 5,
  "acceptance_criteria": [
    "Criterion 1 - Something testable",
    "Criterion 2 - Something testable"
  ],
  "tasks": [
    {
      "summary": "Subtask title",
      "description": "Details about what this subtask covers",
      "story_points": 2,
      "acceptance_criteria": [
        "Subtask acceptance criterion"
      ]
    }
  ]
}

RULES:
1. Story points MUST be Fibonacci scale only: 1, 2, 3, 5, 8, 13
2. Summary must be concise (max 10 words)
3. Description should be detailed but not excessive (2-3 sentences)
4. Break down the work into 2-4 realistic subtasks
5. Each task should have 1-2 acceptance criteria
6. Each acceptance criterion should be testable/measurable
7. Subtask story points should sum to less than or equal to parent story points
8. Return ONLY the JSON object, nothing else"""

    user_prompt = f"Create a Jira ticket for the following: {user_description}"
    
    # Call Ollama API
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": ollama_model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "temperature": 0.3,  # Lower temperature for more deterministic JSON
            },
            timeout=120
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ValueError(
            "❌ Cannot connect to Ollama. Please make sure Ollama is running:\n"
            "   ollama serve"
        )
    except requests.exceptions.Timeout:
        raise ValueError(
            "❌ Ollama request timed out. Please check that Ollama is responding."
        )
    except requests.exceptions.RequestException as e:
        raise ValueError(f"❌ Ollama API error: {str(e)}")
    
    # Extract response
    response_data = response.json()
    llm_output = response_data.get("response", "").strip()
    
    if not llm_output:
        raise ValueError("❌ Ollama returned an empty response")
    
    # Try to parse JSON
    ticket_data = _parse_and_validate_json(llm_output, ollama_url, ollama_model, user_prompt, system_prompt)
    
    return ticket_data


def _parse_and_validate_json(
    json_string: str, 
    ollama_url: str, 
    ollama_model: str, 
    user_prompt: str, 
    system_prompt: str,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Parse and validate JSON response from LLM. Retry once if parsing fails.
    
    Args:
        json_string: Raw JSON string to parse
        ollama_url: Ollama API URL
        ollama_model: Model name for retry
        user_prompt: User prompt for retry
        system_prompt: System prompt for retry
        retry_count: Current retry attempt (0 or 1)
        
    Returns:
        Validated ticket JSON dictionary
        
    Raises:
        ValueError: If JSON is invalid or validation fails
    """
    # Try to clean up the JSON if it contains markdown code blocks
    if "```json" in json_string:
        json_string = json_string.split("```json")[1].split("```")[0].strip()
    elif "```" in json_string:
        json_string = json_string.split("```")[1].split("```")[0].strip()
    
    try:
        ticket_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        if retry_count < 1:
            print("⚠️  JSON parsing failed, retrying with refined prompt...")
            retry_prompt = f"{user_prompt}\n\nPREVIOUS ATTEMPT HAD INVALID JSON. Return ONLY valid JSON in the specified format, nothing else."
            try:
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": ollama_model,
                        "prompt": retry_prompt,
                        "system": system_prompt,
                        "stream": False,
                        "temperature": 0.2,
                    },
                    timeout=120
                )
                response.raise_for_status()
                llm_output = response.json().get("response", "").strip()
                return _parse_and_validate_json(llm_output, ollama_url, ollama_model, user_prompt, system_prompt, retry_count + 1)
            except Exception as retry_error:
                raise ValueError(f"❌ JSON parsing failed and retry failed: {str(retry_error)}")
        else:
            raise ValueError(
                f"❌ LLM returned invalid JSON (even after retry):\n\n{json_string[:500]}\n\n"
                f"JSON Error: {str(e)}"
            )
    
    # Validate schema and structure
    _validate_ticket_schema(ticket_data)
    
    return ticket_data


def _validate_ticket_schema(ticket_data: Dict[str, Any]) -> None:
    """
    Validate that ticket data matches required schema.
    
    Args:
        ticket_data: Dictionary to validate
        
    Raises:
        ValueError: If schema is invalid
    """
    # Check required fields
    required_fields = ["summary", "description", "story_points", "acceptance_criteria", "tasks"]
    missing_fields = [f for f in required_fields if f not in ticket_data]
    if missing_fields:
        raise ValueError(f"❌ Missing required fields: {', '.join(missing_fields)}")
    
    # Validate summary
    if not isinstance(ticket_data["summary"], str) or len(ticket_data["summary"]) == 0:
        raise ValueError("❌ Summary must be a non-empty string")
    
    # Validate description
    if not isinstance(ticket_data["description"], str) or len(ticket_data["description"]) == 0:
        raise ValueError("❌ Description must be a non-empty string")
    
    # Validate story points
    if not isinstance(ticket_data["story_points"], int):
        raise ValueError("❌ Story points must be an integer")
    if not validate_story_points(ticket_data["story_points"]):
        raise ValueError(f"❌ Story points {ticket_data['story_points']} not in Fibonacci scale (1, 2, 3, 5, 8, 13)")
    
    # Validate acceptance criteria
    if not isinstance(ticket_data["acceptance_criteria"], list):
        raise ValueError("❌ Acceptance criteria must be a list")
    if len(ticket_data["acceptance_criteria"]) == 0:
        raise ValueError("❌ At least one acceptance criterion is required")
    for i, ac in enumerate(ticket_data["acceptance_criteria"]):
        if not isinstance(ac, str) or len(ac) == 0:
            raise ValueError(f"❌ Acceptance criterion {i} must be a non-empty string")
    
    # Validate tasks
    if not isinstance(ticket_data["tasks"], list):
        raise ValueError("❌ Tasks must be a list")
    if len(ticket_data["tasks"]) == 0:
        raise ValueError("❌ At least one task is required")
    
    total_subtask_points = 0
    for i, task in enumerate(ticket_data["tasks"]):
        if not isinstance(task, dict):
            raise ValueError(f"❌ Task {i} must be a dictionary")
        
        task_required = ["summary", "description", "story_points", "acceptance_criteria"]
        task_missing = [f for f in task_required if f not in task]
        if task_missing:
            raise ValueError(f"❌ Task {i} missing fields: {', '.join(task_missing)}")
        
        if not isinstance(task["summary"], str) or len(task["summary"]) == 0:
            raise ValueError(f"❌ Task {i} summary must be a non-empty string")
        
        if not isinstance(task["story_points"], int):
            raise ValueError(f"❌ Task {i} story points must be an integer")
        if not validate_story_points(task["story_points"]):
            raise ValueError(f"❌ Task {i} story points {task['story_points']} not in Fibonacci scale")
        
        total_subtask_points += task["story_points"]
        
        if not isinstance(task["acceptance_criteria"], list):
            raise ValueError(f"❌ Task {i} acceptance criteria must be a list")
        if len(task["acceptance_criteria"]) == 0:
            raise ValueError(f"❌ Task {i} requires at least one acceptance criterion")
        for j, ac in enumerate(task["acceptance_criteria"]):
            if not isinstance(ac, str) or len(ac) == 0:
                raise ValueError(f"❌ Task {i} criterion {j} must be a non-empty string")
    
    if total_subtask_points > ticket_data["story_points"]:
        print(f"⚠️  Warning: Total subtask points ({total_subtask_points}) exceeds parent story points ({ticket_data['story_points']})")

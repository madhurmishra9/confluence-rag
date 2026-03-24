"""
Jira Client Module - Handles all Jira REST API v3 calls
"""

import os
import requests
from typing import Dict, Any, List, Optional
from requests.auth import HTTPBasicAuth


class JiraClient:
    """Client for interacting with Jira REST API v3"""
    
    def __init__(self):
        """Initialize Jira client with credentials from environment"""
        self.jira_url = os.getenv("JIRA_URL", "").rstrip("/")
        self.jira_email = os.getenv("JIRA_EMAIL", "")
        self.jira_api_token = os.getenv("JIRA_API_TOKEN", "")
        self.jira_project_key = os.getenv("JIRA_PROJECT_KEY", "")
        self.jira_team_name = os.getenv("JIRA_TEAM_NAME", "")
        
        # Validate required environment variables
        self._validate_config()
        
        # Setup authentication
        self.auth = HTTPBasicAuth(self.jira_email, self.jira_api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _validate_config(self) -> None:
        """Validate that all required Jira config is present"""
        required_keys = {
            "JIRA_URL": self.jira_url,
            "JIRA_EMAIL": self.jira_email,
            "JIRA_API_TOKEN": self.jira_api_token,
            "JIRA_PROJECT_KEY": self.jira_project_key,
            "JIRA_TEAM_NAME": self.jira_team_name,
        }
        
        missing_keys = [key for key, value in required_keys.items() if not value]
        if missing_keys:
            raise ValueError(
                f"❌ Missing required Jira configuration keys in .env:\n"
                f"   {', '.join(missing_keys)}\n\n"
                f"Please add these keys to your .env file."
            )
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Jira API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            ValueError: If API returns an error
        """
        url = f"{self.jira_url}/rest/api/3{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            
            # Check for errors
            if response.status_code >= 400:
                error_detail = self._extract_error_message(response)
                raise ValueError(
                    f"❌ Jira API Error ({response.status_code}):\n{error_detail}"
                )
            
            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise ValueError("❌ Jira API request timed out")
        except requests.exceptions.ConnectionError:
            raise ValueError(
                f"❌ Cannot connect to Jira at {self.jira_url}\n"
                f"Please verify JIRA_URL in .env is correct"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"❌ Jira API request failed: {str(e)}")
    
    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from Jira error response"""
        try:
            error_data = response.json()
            if "errorMessages" in error_data and error_data["errorMessages"]:
                return error_data["errorMessages"][0]
            if "errors" in error_data and error_data["errors"]:
                errors_dict = error_data["errors"]
                return "; ".join([f"{k}: {v}" for k, v in errors_dict.items()])
            return response.text or "Unknown error"
        except:
            return response.text or "Unknown error"
    
    def create_story(self, ticket_data: Dict[str, Any]) -> str:
        """
        Create a Jira Story with the given data.
        
        Args:
            ticket_data: Dictionary with keys:
                - summary: Story title
                - description: Story description
                - story_points: Story points (custom field)
                - acceptance_criteria: List of acceptance criteria
                
        Returns:
            Created issue key (e.g., "PROJ-123")
            
        Raises:
            ValueError: If creation fails
        """
        # Format acceptance criteria
        ac_text = "\n".join([f"• {ac}" for ac in ticket_data["acceptance_criteria"]])
        full_description = (
            f"{ticket_data['description']}\n\n"
            f"*Acceptance Criteria:*\n{ac_text}"
        )
        
        # Prepare issue creation payload
        issue_payload = {
            "fields": {
                "project": {
                    "key": self.jira_project_key
                },
                "summary": ticket_data["summary"],
                "description": {
                    "version": 3,
                    "type": "doc",
                    "content": self._convert_text_to_adf(full_description)
                },
                "issuetype": {
                    "name": "Story"
                },
                "labels": [self.jira_team_name],
                # Story points is custom field - adjust field ID if needed
                "customfield_10016": ticket_data["story_points"]
            }
        }
        
        response = self._make_request("POST", "/issues", data=issue_payload)
        
        if "id" not in response or "key" not in response:
            raise ValueError(f"❌ Unexpected Jira response: {response}")
        
        issue_key = response["key"]
        print(f"✓ Created Story: {issue_key}")
        return issue_key
    
    def create_subtask(self, parent_key: str, task_data: Dict[str, Any]) -> str:
        """
        Create a subtask linked to a parent Story.
        
        Args:
            parent_key: Parent issue key (e.g., "PROJ-123")
            task_data: Dictionary with keys:
                - summary: Subtask title
                - description: Subtask description
                - story_points: Subtask story points
                - acceptance_criteria: List of acceptance criteria
                
        Returns:
            Created subtask issue key
            
        Raises:
            ValueError: If creation fails
        """
        # Format acceptance criteria
        ac_text = "\n".join([f"• {ac}" for ac in task_data["acceptance_criteria"]])
        full_description = (
            f"{task_data['description']}\n\n"
            f"*Acceptance Criteria:*\n{ac_text}"
        )
        
        # Prepare subtask payload
        subtask_payload = {
            "fields": {
                "project": {
                    "key": self.jira_project_key
                },
                "parent": {
                    "key": parent_key
                },
                "summary": task_data["summary"],
                "description": {
                    "version": 3,
                    "type": "doc",
                    "content": self._convert_text_to_adf(full_description)
                },
                "issuetype": {
                    "name": "Subtask"
                },
                # Story points custom field
                "customfield_10016": task_data["story_points"]
            }
        }
        
        response = self._make_request("POST", "/issues", data=subtask_payload)
        
        if "id" not in response or "key" not in response:
            raise ValueError(f"❌ Unexpected Jira response: {response}")
        
        subtask_key = response["key"]
        print(f"  └─ Created Subtask: {subtask_key}")
        return subtask_key
    
    def _convert_text_to_adf(self, text: str) -> List[Dict[str, Any]]:
        """
        Convert plain text to Atlassian Document Format (ADF).
        This is a simple conversion for basic text with bullet points.
        
        Args:
            text: Plain text to convert
            
        Returns:
            ADF content array
        """
        content = []
        
        for line in text.split("\n"):
            line = line.rstrip()
            if not line:
                # Empty line - add paragraph
                content.append({
                    "type": "paragraph",
                    "content": []
                })
            elif line.startswith("*") and line.endswith("*"):
                # Bold title
                title = line.strip("*").strip()
                content.append({
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": title,
                        "marks": [{"type": "strong"}]
                    }]
                })
            elif line.startswith("• "):
                # Bullet point
                bullet_text = line[2:].strip()
                content.append({
                    "type": "bulletList",
                    "content": [{
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": bullet_text
                            }]
                        }]
                    }]
                })
            else:
                # Regular paragraph
                if line:
                    content.append({
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": line
                        }]
                    })
        
        # Ensure at least one paragraph
        if not content:
            content.append({
                "type": "paragraph",
                "content": []
            })
        
        return content
    
    def get_issue_url(self, issue_key: str) -> str:
        """Get the browse URL for an issue"""
        return f"{self.jira_url}/browse/{issue_key}"

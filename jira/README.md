# 🎟️ Jira Ticket Creator CLI

A standalone Python CLI tool that automatically generates well-structured Jira Epic/Stories with subtasks, acceptance criteria, and story points using a local Ollama LLM (llama3.1:8b).

## ✨ Features

- **AI-Powered Ticket Generation**: Uses Ollama's llama3.1:8b model to intelligently generate ticket structure
- **Structured Output**: Creates Stories with:
  - Concise, descriptive summaries
  - Detailed descriptions
  - Fibonacci-scaled story points (1, 2, 3, 5, 8, 13)
  - Testable acceptance criteria
  - Intelligent subtask breakdown (2-4 tasks)
- **Jira Integration**: Direct REST API v3 integration with Atlassian Cloud
- **Preview & Confirmation**: Shows generated ticket before creation in Jira
- **Error Handling**: Graceful error messages for missing configs, network issues, and malformed LLM responses
- **Flexible Input**: Accept descriptions via CLI argument or interactive prompt
- **Standalone**: Completely independent from the existing confluence-rag code

## 📋 Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Architecture](#architecture)
5. [API Reference](#api-reference)
6. [Error Handling](#error-handling)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

---

## 🚀 Installation

### Prerequisites

- **Python 3.8+**
- **Ollama** running with llama3.1:8b model (`ollama serve`)
- **Jira Cloud** account with API token access

### Step 1: Install Dependencies

```bash
pip install requests python-dotenv
```

These are the only external packages required:
- **requests**: HTTP client for Jira REST API calls
- **python-dotenv**: Environment variable management from .env file

All other imports are from Python's standard library.

### Step 2: Verify File Structure

Ensure the jira module is in your project root:

```
confluence-rag/
├── jira/
│   ├── __init__.py
│   ├── create_ticket.py        # CLI entry point
│   ├── llm_generator.py        # Ollama integration
│   ├── jira_client.py          # Jira API client
│   └── README.md               # This file
├── .env                        # Configuration (updated)
└── [other project files]
```

---

## ⚙️ Configuration

### Update .env File

Add/update these keys in your existing `.env` file:

```env
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=PROJ
JIRA_TEAM_NAME=your_team_name
```

### Configuration Guide

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `JIRA_URL` | Yes | Your Jira Cloud instance URL | `https://acme.atlassian.net` |
| `JIRA_EMAIL` | Yes | Your Atlassian account email | `user@example.com` |
| `JIRA_API_TOKEN` | Yes | API token for authentication | Get from https://id.atlassian.com/manage-profile/security/api-tokens |
| `JIRA_PROJECT_KEY` | Yes | Project key prefix | If tickets are `PROJ-123`, use `PROJ` |
| `JIRA_TEAM_NAME` | Yes | Team identifier (added as label) | `backend-team`, `platform`, etc. |

### Getting Your Jira Credentials

1. **JIRA_URL**: Copy from your browser URL bar (https://your-domain.atlassian.net)
2. **JIRA_EMAIL**: Your Atlassian account email
3. **JIRA_API_TOKEN**: 
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy and paste into .env
4. **JIRA_PROJECT_KEY**: Visit your Jira project and note the key (e.g., PROJ-123 → PROJ)
5. **JIRA_TEAM_NAME**: Any identifier for your team (e.g., "backend", "frontend")

---

## 📖 Usage

### Basic Command Line

```bash
# With description as argument
python jira/create_ticket.py "Create a user authentication system with OAuth2"

# Interactive mode (prompts for description)
python jira/create_ticket.py
```

### Interactive Mode

If no argument is provided, the tool enters interactive mode:

```
======================================================================
🎯 JIRA TICKET CREATOR - Interactive Mode
======================================================================

Enter a description of the work to be done.
(Press Enter twice to submit)

Build a real-time notification system
```

### Full Workflow

1. **Input**: Provide description (CLI arg or interactive)
2. **Generate**: LLM creates structured ticket JSON
3. **Preview**: Review generated summary, points, tasks, criteria
4. **Confirm**: User approves before creation
5. **Create**: Tickets created in Jira with proper linking
6. **Output**: URLs to created Story and Subtasks

---

## 🏗️ Architecture

### Module Overview

```
jira/
├── create_ticket.py       │  CLI entry point & user interaction
├── llm_generator.py       │  Ollama integration & JSON validation
└── jira_client.py         │  Jira REST API v3 wrapper
```

### Data Flow

```
User Input
    ↓
create_ticket.py (CLI handling)
    ↓
generate_ticket_json() (Ollama call)
    ↓
LLM Response → Validate JSON Schema
    ↓
display_ticket_preview() (User review)
    ↓
JiraClient (API auth & creation)
    ↓
create_story() → create_subtask() for each task
    ↓
Display Jira URLs
```

### Generated Ticket Schema

The LLM generates tickets following this JSON schema:

```json
{
  "summary": "Short ticket title",
  "description": "Detailed description of the work",
  "story_points": 5,
  "acceptance_criteria": [
    "Criterion 1",
    "Criterion 2"
  ],
  "tasks": [
    {
      "summary": "Subtask title",
      "description": "Subtask detail",
      "story_points": 2,
      "acceptance_criteria": [
        "Subtask criterion"
      ]
    }
  ]
}
```

**Validation Rules:**
- Story points: Fibonacci scale (1, 2, 3, 5, 8, 13) only
- Summary: Non-empty string
- Tasks: At least 1 task required
- Acceptance Criteria: At least 1 per task
- Subtask points should sum to ≤ parent story points

---

## 📚 API Reference

### llm_generator.py

#### `generate_ticket_json(user_description: str) -> Dict[str, Any]`

Generate structured Jira ticket from user description using Ollama.

**Parameters:**
- `user_description` (str): Plain English description of work needed

**Returns:**
- Dictionary with keys: summary, description, story_points, acceptance_criteria, tasks

**Raises:**
- `ValueError`: If Ollama is not running or JSON parsing fails
- `KeyError`: If required environment variables are missing

**Example:**
```python
from jira.llm_generator import generate_ticket_json

ticket = generate_ticket_json("Build user authentication system")
print(ticket['summary'])  # "User Authentication System"
print(ticket['story_points'])  # 5, 8, 13, etc.
```

#### `validate_story_points(points: int) -> bool`

Check if story points follow Fibonacci scale.

**Parameters:**
- `points` (int): Number to validate

**Returns:**
- True if valid (1, 2, 3, 5, 8, 13), False otherwise

---

### jira_client.py

#### `JiraClient` Class

Initialize the Jira API client with credentials from environment.

```python
from jira.jira_client import JiraClient

client = JiraClient()  # Reads JIRA_* from .env
```

**Raises:**
- `ValueError`: If required .env keys are missing

#### `create_story(ticket_data: Dict[str, Any]) -> str`

Create a Jira Story with acceptance criteria.

**Parameters:**
- `ticket_data`: Dict with keys:
  - `summary` (str): Story title
  - `description` (str): Story description
  - `story_points` (int): Story points
  - `acceptance_criteria` (list): List of acceptance criteria strings

**Returns:**
- Issue key (e.g., "PROJ-123")

**Example:**
```python
story_key = client.create_story({
    "summary": "Build API",
    "description": "Create REST API endpoints",
    "story_points": 5,
    "acceptance_criteria": ["API responds in < 200ms", "Tests pass"]
})
# Returns: "PROJ-456"
```

#### `create_subtask(parent_key: str, task_data: Dict[str, Any]) -> str`

Create a subtask linked to a parent Story.

**Parameters:**
- `parent_key` (str): Parent story key (e.g., "PROJ-123")
- `task_data`: Dict with same structure as story_data

**Returns:**
- Subtask issue key (e.g., "PROJ-457")

#### `get_issue_url(issue_key: str) -> str`

Get the browse URL for an issue.

**Parameters:**
- `issue_key` (str): Issue key (e.g., "PROJ-123")

**Returns:**
- Full URL (e.g., "https://domain.atlassian.net/browse/PROJ-123")

---

### create_ticket.py

#### `main()`

CLI entry point. Handles user input, generates ticket, and creates in Jira.

**Command Line Usage:**
```bash
python jira/create_ticket.py "description"
python jira/create_ticket.py  # Interactive mode
```

#### `display_ticket_preview(ticket_data: dict) -> None`

Display formatted preview of generated ticket to user.

#### `get_user_confirmation() -> bool`

Prompt user for yes/no confirmation. Loops until valid input.

---

## ⚠️ Error Handling

### Ollama Errors

**Issue**: "Cannot connect to Ollama"
```
❌ Cannot connect to Ollama. Please make sure Ollama is running:
   ollama serve
```

**Solution**: 
- Ensure Ollama is installed: https://ollama.ai
- Run `ollama serve` in a separate terminal
- Verify `OLLAMA_BASE_URL=http://localhost:11434` in .env

### JSON Parsing Errors

**Issue**: LLM returns invalid JSON
```
⚠️  JSON parsing failed, retrying with refined prompt...
```

The tool automatically retries with a clearer prompt. If it fails twice:
```
❌ LLM returned invalid JSON (even after retry):

{invalid json here}

JSON Error: ...
```

**Solution**:
- Reduce model temperature in llm_generator.py (already set to 0.3)
- Ensure Ollama model is properly loaded: `ollama pull llama3.1:8b`

### Jira API Errors

**Issue**: Authentication failed
```
❌ Jira API Error (401):
   Unauthorized
```

**Solution**:
- Verify JIRA_EMAIL and JIRA_API_TOKEN are correct
- Generate new API token: https://id.atlassian.com/manage-profile/security/api-tokens
- Ensure token doesn't have special characters (copy-paste carefully)

**Issue**: Project not found
```
❌ Jira API Error (400):
   project key is required
```

**Solution**:
- Verify JIRA_PROJECT_KEY in .env matches your project
- Check project key in Jira (visible in issue URLs)

### Configuration Errors

**Issue**: Missing environment variables
```
❌ Missing required Jira configuration keys in .env:
   JIRA_URL, JIRA_API_TOKEN
```

**Solution**:
- Add all `JIRA_*` keys to .env file
- Ensure no typos in key names
- Restart your terminal after updating .env

---

## 🔧 Troubleshooting

### "Connection refused" on Windows

If you're using Windows and get connection errors:

**For Windows 10/11 with WSL2:**
- Ollama must be running in WSL2 or on Host
- Check Ollama is accessible at `http://localhost:11434`

**For Windows with Docker:**
- If Ollama runs in Docker, use: `OLLAMA_BASE_URL=http://host.docker.internal:11434`

### Slow ticket generation

**Issue**: Takes > 60 seconds to generate ticket

**Causes**:
- Ollama model too large or needs time to load
- Server under heavy load
- Network latency

**Solutions**:
- Increase timeout in llm_generator.py (currently 120s):
  ```python
  timeout=180  # Increase to 180 seconds
  ```
- Use lighter model: `ollama pull mistral:7b`
- Check Ollama logs: Look for errors causing slowness

### Story points mismatch

**Issue**: Subtasks points don't match parent

The tool warns but allows it:
```
⚠️  Warning: Total subtask points (10) exceeds parent story points (8)
```

**Why**: Sometimes breaking work into subtasks requires different estimates

**Solution**: 
- Manually adjust in Jira, or
- Re-run with different description to get smaller subtasks

### Jira custom field errors

**Issue**: Story points not saved
```
❌ Jira API Error (400):
   field [customfield_10016] cannot be set
```

**Cause**: Custom field ID doesn't match your Jira instance

**Solution**:
1. Log into Jira → Project Settings → Fields
2. Find "Story Points" field ID (e.g., customfield_10020)
3. Update in jira_client.py line where `customfield_10016` appears:
   ```python
   "customfield_XXXXX": ticket_data["story_points"]  # Replace XXXXX
   ```

---

## 📝 Examples

### Example 1: Auth System (CLI Argument)

```bash
python jira/create_ticket.py "Implement OAuth2 authentication with Google, GitHub, and Microsoft providers. Must support single sign-on and token refresh."
```

**Generated Ticket:**
```
Summary: Implement Multi-Provider OAuth2 Auth
Points: 8

Description: Implement a comprehensive OAuth2 authentication system 
supporting Google, GitHub, and Microsoft providers with proper token 
management and single sign-on capabilities.

Acceptance Criteria:
• OAuth2 flow is implemented for all three providers
• Tokens are securely stored and refreshed
• SSO session management works correctly
• Logout clears all authentication state

Subtasks:
1. OAuth2 Provider Integration (3 pts)
   - Set up OAuth2 flows for Google, GitHub, Microsoft
   
2. Token Management & Security (3 pts)
   - Secure token storage and encryption
   - Implement refresh token logic
   
3. Session & SSO Management (2 pts)
   - Session management across providers
   - SSO functionality
```

### Example 2: API Rate Limiting (Interactive)

```bash
python jira/create_ticket.py
```

```
Enter description:
Implement API rate limiting with token bucket and sliding window 
strategies. Must be configurable per endpoint.
```

**Result**: PROJ-460 created with 2-3 subtasks

### Example 3: Handling Errors

```bash
python jira/create_ticket.py "test"
```

If Ollama is down:
```
❌ Cannot connect to Ollama. Please make sure Ollama is running:
   ollama serve
```

If .env is missing JIRA_PROJECT_KEY:
```
❌ Missing required Jira configuration keys in .env:
   JIRA_PROJECT_KEY

Please add these keys to your .env file.
```

---

## 🔐 Security Notes

### Credentials Management

- **All credentials come from .env**, never hardcoded
- **API Token**: Better than password-based auth, more granular permissions
- **.env in .gitignore**: Ensure .env is never committed to version control
- **Token rotation**: Periodically rotate your Jira API token

### Best Practices

1. **Use environment variables** for all secrets
2. **Create API token** with minimal required permissions
3. **Don't share .env** with team members
4. **Audit logs**: Check Jira for token usage
5. **Rotate tokens** if compromised

---

## 📦 Dependency Information

### Why These Packages?

| Package | Use | Size |
|---------|-----|------|
| `requests` | HTTP calls to Jira API & Ollama | ~60 KB |
| `python-dotenv` | .env file loading | ~12 KB |

Both are lightweight, widely-used packages with excellent maintenance.

### Alternative: Manual .env Parsing

If you can't install python-dotenv, the tool falls back to manual parsing:
```python
# create_ticket.py has fallback logic for .env parsing
```

---

## 🎯 Workflow Summary

**Quick Reference:**

```bash
# 1. Install
pip install requests python-dotenv

# 2. Configure
# Edit .env with JIRA_* keys

# 3. Start Ollama
ollama serve

# 4. Create ticket
python jira/create_ticket.py "Your description"

# 5. Confirm
# (yes/no prompt)

# 6. View in Jira
# Click link in output
```

---

## 📞 Support

### Common Issues

| Issue | Solution |
|-------|----------|
| Ollama not responding | `ollama serve` in separate terminal |
| Wrong story points schema | Fibonacci only: 1,2,3,5,8,13 |
| Jira connection fails | Check JIRA_URL, JIRA_EMAIL, token |
| JSON parsing errors | Auto-retries; check Ollama model |
| Missing .env keys | Add all JIRA_* variables |

### Debug Mode

To see detailed API requests, add logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📄 License

This tool is part of the confluence-rag project.

---

## 🚀 Next Steps

1. Install dependencies: `pip install requests python-dotenv`
2. Configure .env with Jira credentials
3. Test with: `python jira/create_ticket.py "test ticket"`
4. Check output in your Jira project
5. Integrate into your workflow!

Happy ticket creating! 🎉

#!/usr/bin/env python3
"""
Jira Ticket Creator CLI - Main entry point for creating Jira tickets
Usage:
    python jira/create_ticket.py "Your description here"
    python jira/create_ticket.py  # Interactive mode
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira.llm_generator import generate_ticket_json
from jira.jira_client import JiraClient


def display_ticket_preview(ticket_data: dict) -> None:
    """Display a formatted preview of the generated ticket"""
    print("\n" + "=" * 70)
    print("📋 GENERATED TICKET PREVIEW")
    print("=" * 70)
    
    print(f"\n📌 Summary: {ticket_data['summary']}")
    print(f"   Points: {ticket_data['story_points']}")
    
    print(f"\n📝 Description:\n   {ticket_data['description']}")
    
    print(f"\n✅ Acceptance Criteria:")
    for ac in ticket_data['acceptance_criteria']:
        print(f"   • {ac}")
    
    print(f"\n📋 Subtasks ({len(ticket_data['tasks'])} total):")
    for i, task in enumerate(ticket_data['tasks'], 1):
        print(f"\n   {i}. {task['summary']} ({task['story_points']} pts)")
        print(f"      {task['description']}")
        print(f"      Criteria:")
        for ac in task['acceptance_criteria']:
            print(f"        • {ac}")
    
    print("\n" + "=" * 70)


def get_user_confirmation() -> bool:
    """Ask user to confirm ticket creation"""
    while True:
        response = input("\n🚀 Create this ticket in Jira? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        print("   Please enter 'yes' or 'no'")


def create_tickets_in_jira(ticket_data: dict, jira_client: JiraClient) -> None:
    """Create the story and all subtasks in Jira"""
    try:
        print("\n🔄 Creating tickets in Jira...")
        
        # Create the parent Story
        story_key = jira_client.create_story(ticket_data)
        
        # Create subtasks
        for task in ticket_data['tasks']:
            jira_client.create_subtask(story_key, task)
        
        # Display success message with URLs
        story_url = jira_client.get_issue_url(story_key)
        
        print("\n" + "=" * 70)
        print("✨ TICKETS CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📋 Parent Story: {story_key}")
        print(f"   🔗 {story_url}")
        print(f"\n   ✓ {len(ticket_data['tasks'])} subtasks created and linked")
        print("\n" + "=" * 70)
        
    except ValueError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


def load_env_file() -> None:
    """Load .env file from project root"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
    else:
        print(f"⚠️  Warning: .env file not found at {env_path}")


def main():
    """Main CLI entry point"""
    # Load environment variables
    try:
        load_env_file()
    except ImportError:
        print("⚠️  python-dotenv not installed. Make sure to run:")
        print("   pip install python-dotenv")
        print("\nAttempting to read .env without python-dotenv...")
        # Try manual .env parsing if dotenv isn't available
        try:
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Could not load .env: {e}")
    
    # Get user description
    if len(sys.argv) > 1:
        # Description provided as command line argument
        user_description = " ".join(sys.argv[1:])
        print(f"📝 Description: {user_description}\n")
    else:
        # Interactive mode
        print("=" * 70)
        print("🎯 JIRA TICKET CREATOR - Interactive Mode")
        print("=" * 70)
        print("\nEnter a description of the work to be done.")
        print("(Press Enter twice to submit)\n")
        
        lines = []
        empty_line_count = 0
        while True:
            try:
                line = input()
                if line == "":
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_line_count = 0
                    lines.append(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n\n❌ Cancelled by user")
                sys.exit(0)
        
        user_description = "\n".join(lines).strip()
        
        if not user_description:
            print("❌ No description provided")
            sys.exit(1)
    
    # Generate ticket structure
    print("⏳ Generating ticket structure with Ollama...")
    try:
        ticket_data = generate_ticket_json(user_description)
    except ValueError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
    
    # Display preview
    display_ticket_preview(ticket_data)
    
    # Get confirmation
    if not get_user_confirmation():
        print("\n❌ Ticket creation cancelled")
        sys.exit(0)
    
    # Initialize Jira client and create tickets
    try:
        jira_client = JiraClient()
    except ValueError as e:
        print(f"\n{e}")
        sys.exit(1)
    
    create_tickets_in_jira(ticket_data, jira_client)


if __name__ == "__main__":
    main()

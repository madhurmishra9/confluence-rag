#!/usr/bin/env python3
"""
SO Intelligence CLI Entrypoint

Provides subcommands for:
  - run: Execute the analysis pipeline
  - serve: Start API + dashboard server
  - status: Show last run summary and cache stats
  - validate-config: Verify all dependencies and configuration
"""

import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json
import subprocess

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Setup console and logger
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import from local modules
from .config import AgentConfig
from .orchestrator import SOIntelligenceOrchestrator, OrchestratorFailureError
from .ollama_client import OllamaClient, OllamaConnectionError
from .so_fetcher import StackOverflowFetcher, AuthenticationError
from .cache_manager import CacheManager
from .report_generator import ReportGenerator
from .solution_verifier import SolutionVerifier


def print_header(title: str) -> None:
    """Print a formatted header."""
    console.print(f"\n[bold cyan]>>> {title}[/bold cyan]\n")


def check_health() -> bool:
    """
    Run all startup health checks.
    
    Returns:
        True if all checks pass, False otherwise.
    """
    print_header("[*] Running Health Checks")
    
    checks_passed = True
    checks_results = []
    
    # Check 1: Ollama running
    console.print("[cyan]Checking Ollama connection...[/cyan]", end=" ")
    try:
        config = AgentConfig()
        llm = OllamaClient(config)
        if llm.ping():
            console.print("[green]PASS[/green]")
            checks_results.append(("Ollama Running", "PASS", "green"))
        else:
            console.print("[red]FAIL[/red]")
            checks_results.append(("Ollama Running", "FAIL", "red"))
            checks_passed = False
    except Exception as e:
        console.print("[red]✗[/red]")
        checks_results.append(("Ollama Running", f"✗ {e}", "red"))
        checks_passed = False
    
    # Check 2: SO API Token
    console.print("[cyan]Checking Stack Overflow API token...[/cyan]", end=" ")
    try:
        config = AgentConfig()
        if config.so_api_token:
            console.print("[green]PASS[/green]")
            checks_results.append(("SO API Token", "PASS", "green"))
        else:
            console.print("[red]FAIL[/red]")
            checks_results.append(("SO API Token", "FAIL Not set", "red"))
            checks_passed = False
    except Exception as e:
        console.print("[red]✗[/red]")
        checks_results.append(("SO API Token", f"✗ {e}", "red"))
        checks_passed = False
    
    # Check 3: Required packages
    console.print("[cyan]Checking required packages...[/cyan]", end=" ")
    required_packages = [
        "ollama", "langchain_ollama", "chromadb", "pydantic_settings",
        "python_dotenv", "sqlite_utils", "requests", "reportlab",
        "python_docx", "pandas", "fastapi", "uvicorn", "rich"
    ]
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_").replace("python_", ""))
        except ImportError:
            missing_packages.append(pkg)
    
    if not missing_packages:
        console.print("[green]PASS[/green]")
        checks_results.append(("Required Packages", "PASS", "green"))
    else:
        console.print("[red]FAIL[/red]")
        pkg_list = ", ".join(missing_packages)
        checks_results.append(("Required Packages", f"FAIL Missing: {pkg_list}", "red"))
        checks_passed = False
    
    # Check 4: Models available in Ollama
    console.print("[cyan]Checking Ollama models...[/cyan]", end=" ")
    try:
        config = AgentConfig()
        llm = OllamaClient(config)
        # Check if Ollama is responding by trying to list models via ping
        if llm.ping():
            console.print("[green]PASS[/green]")
            checks_results.append(("Ollama Models", "PASS", "green"))
        else:
            console.print("[yellow]WARN[/yellow]")
            msg = f"WARN Could not verify models"
            checks_results.append(("Ollama Models", msg, "yellow"))
    except Exception as e:
        console.print("[yellow]WARN[/yellow]")
        checks_results.append(("Ollama Models", f"WARN {str(e)[:50]}", "yellow"))
    
    # Print results table
    table = Table(title="Health Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="white")
    
    for check_name, result, color in checks_results:
        table.add_row(check_name, f"[{color}]{result}[/{color}]")
    
    console.print(table)
    
    if not checks_passed:
        console.print("\n[red][FAIL] Some critical checks failed. Please fix them before proceeding.[/red]")
        console.print("[yellow][INFO] Make sure Ollama is running:[/yellow]")
        console.print("  $ ollama serve")
        console.print("[yellow][INFO] Or set SO_API_TOKEN:[/yellow]")
        console.print("  $ export SO_API_TOKEN=your_token_here")
        return False
    
    console.print("\n[green][PASS] All checks passed![/green]")
    return True


def cmd_validate_config(args) -> int:
    """Validate configuration and dependencies."""
    logger.info("Starting validate-config...")
    if not check_health():
        return 1
    return 0


def cmd_run(args) -> int:
    """Execute the analysis pipeline."""
    print_header("[START] Analysis Pipeline")
    
    # Run health checks first
    if not check_health():
        return 1
    
    try:
        # Load config
        config = AgentConfig()
        
        # Parse arguments
        tags = args.tags if args.tags else config.default_tags
        days = args.days or config.date_range_days
        intervention_date = args.intervention
        force_refresh = args.force_refresh
        skip_report = args.no_report
        
        logger.info(f"Running with tags: {tags}, days: {days}")
        logger.info(f"Force refresh: {force_refresh}, Skip report: {skip_report}")
        
        # Initialize orchestrator
        console.print("[cyan]Initializing orchestrator...[/cyan]")
        orchestrator = SOIntelligenceOrchestrator(config)
        
        # Run pipeline
        console.print("[cyan]Executing pipeline...[/cyan]")
        result = orchestrator.run(
            tags=tags,
            date_range_days=days,
            intervention_date=intervention_date,
            force_refresh=force_refresh,
        )
        
        # Print results
        print_header("[RESULTS] Pipeline Results")
        
        result_table = Table(title="Run Summary")
        result_table.add_column("Metric", style="cyan")
        result_table.add_column("Value", style="white")
        
        result_table.add_row("Run ID", result.run_id)
        status_display = f"[green]{result.status}[/green]" if result.status == "SUCCESS" else f"[red]{result.status}[/red]"
        result_table.add_row("Status", status_display)
        result_table.add_row("Tags Analyzed", str(len(result.tags_analyzed)))
        result_table.add_row("Duration", f"{result.duration_seconds:.2f}s")
        
        if result.errors:
            result_table.add_row("Errors", str(len(result.errors)))
        if result.warnings:
            result_table.add_row("Warnings", str(len(result.warnings)))
        
        console.print(result_table)
        
        # Print errors and warnings
        if result.errors:
            console.print("\n[red]Errors:[/red]")
            for error in result.errors:
                console.print(f"  - {error}")
        
        if result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  - {warning}")
        
        # Generate report if requested
        if not skip_report and result.status in ["SUCCESS", "PARTIAL"]:
            console.print("\n[cyan]Generating report...[/cyan]")
            try:
                report_gen = ReportGenerator(config)
                report_paths = report_gen.generate(result)
                console.print("[green][OK] Report generated:[/green]")
                for format_type, path in report_paths.items():
                    console.print(f"  - {format_type}: {path}")
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                console.print(f"[yellow]⚠ Report generation failed: {e}[/yellow]")
        
        return 0 if result.status == "SUCCESS" else 1
        
    except OrchestratorFailureError as e:
        logger.error(f"Orchestrator failed: {e}")
        console.print(f"[red][FAIL] Pipeline failed: {e}[/red]")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red][FAIL] Unexpected error: {e}[/red]")
        return 1


def cmd_serve(args) -> int:
    """Start API + dashboard server."""
    print_header("[SERVER] API + Dashboard Server")
    
    # Run health checks first
    if not check_health():
        return 1
    
    try:
        port = args.port or 8000
        
        # Check if api_server module exists
        try:
            from api_server import app
        except ImportError:
            logger.error("api_server module not found")
            console.print("[red][FAIL] API server module not found[/red]")
            return 1
        
        # Check if port is available
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                console.print(f"[red][FAIL] Port {port} is already in use[/red]")
                return 1
        except Exception as e:
            logger.warning(f"Could not check port availability: {e}")
        
        console.print(f"[cyan]Starting server on port {port}...[/cyan]")
        console.print(f"[green][OK] Dashboard available at:[/green] http://localhost:{port}")
        console.print(f"[green][OK] API docs at:[/green] http://localhost:{port}/docs")
        
        if args.open:
            console.print("[cyan]Opening browser...[/cyan]")
            import webbrowser
            webbrowser.open(f"http://localhost:{port}")
        
        # Start server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
        return 0
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        console.print(f"[red][FAIL] Server startup failed: {e}[/red]")
        return 1


def cmd_status(args) -> int:
    """Show last run summary and cache stats."""
    print_header("[STATUS] System Report")
    
    try:
        config = AgentConfig()
        cache = CacheManager(config)
        
        # Get cache stats
        stats_table = Table(title="System Status")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")
        
        # Database file size
        db_path = Path(config.db_path)
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            stats_table.add_row("Database Size", f"{size_mb:.2f} MB")
        
        # Cache TTL
        stats_table.add_row("Cache TTL", f"{config.cache_ttl_days} days")
        
        # Config values
        stats_table.add_row("Ollama Model", config.ollama_model)
        stats_table.add_row("Embedding Model", config.ollama_embed_model)
        stats_table.add_row("Default Tags", str(len(config.default_tags)))
        stats_table.add_row("API Token", "[green]Set[/green]" if config.so_api_token else "[red]Not Set[/red]")
        
        console.print(stats_table)
        
        # Try to get last run info
        try:
            db = cache.db
            runs = list(db["analysis_runs"].rows_where(order_by="-created_at", limit=1))
            if runs:
                run = runs[0]
                last_run_table = Table(title="Last Run")
                last_run_table.add_column("Metric", style="cyan")
                last_run_table.add_column("Value", style="white")
                
                from datetime import datetime
                timestamp = datetime.fromtimestamp(run["created_at"])
                last_run_table.add_row("Timestamp", timestamp.isoformat())
                last_run_table.add_row("Run ID", run["run_id"])
                last_run_table.add_row("Status", run["status"])
                
                console.print(last_run_table)
            else:
                console.print("[yellow][INFO] No previous runs found[/yellow]")
        except Exception as e:
            logger.debug(f"Could not retrieve last run info: {e}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Status command failed: {e}", exc_info=True)
        console.print(f"[red][FAIL] Status command failed: {e}[/red]")
        return 1


def main() -> int:
    """Main entrypoint."""
    parser = argparse.ArgumentParser(
        description="SO Intelligence - Stack Overflow Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m so_intelligence run --tags cloudspanner alloydb --days 30
  python -m so_intelligence serve --port 8000 --open
  python -m so_intelligence status
  python -m so_intelligence validate-config
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Execute analysis pipeline")
    run_parser.add_argument(
        "--tags",
        nargs="+",
        default=None,
        help="Tags to analyze (default: config defaults)"
    )
    run_parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Date range in days (default: 30)"
    )
    run_parser.add_argument(
        "--intervention",
        type=str,
        default=None,
        help="ISO 8601 intervention date for temporal comparison (e.g., 2024-01-15)"
    )
    run_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Skip cache and fetch fresh data"
    )
    run_parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation"
    )
    run_parser.set_defaults(func=cmd_run)
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start API + dashboard server")
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    serve_parser.add_argument(
        "--open",
        action="store_true",
        help="Open browser automatically"
    )
    serve_parser.set_defaults(func=cmd_serve)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show system status and last run info")
    status_parser.set_defaults(func=cmd_status)
    
    # validate-config command
    validate_parser = subparsers.add_parser("validate-config", help="Validate configuration and dependencies")
    validate_parser.set_defaults(func=cmd_validate_config)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        console.print("\n[yellow][INFO] Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red][FAIL] Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())

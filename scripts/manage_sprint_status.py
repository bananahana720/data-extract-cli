#!/usr/bin/env python3
"""
Sprint Status Manager

Interactive sprint status management with display of current status,
story state updates, sprint report generation, and velocity metrics.

Usage:
    python scripts/manage_sprint_status.py --status      # Display current sprint status
    python scripts/manage_sprint_status.py --update      # Interactive story state updates
    python scripts/manage_sprint_status.py --report      # Generate sprint report
    python scripts/manage_sprint_status.py --velocity    # Calculate velocity metrics
"""

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog  # type: ignore[import-not-found]
from rich import box  # type: ignore[import-not-found]
from rich.console import Console  # type: ignore[import-not-found]
from rich.panel import Panel  # type: ignore[import-not-found]
from rich.prompt import Confirm, Prompt  # type: ignore[import-not-found]
from rich.table import Table  # type: ignore[import-not-found]

# Try to import optional dependencies
try:
    from ruamel.yaml import YAML  # type: ignore[import-not-found]

    HAS_RUAMEL = True
except ImportError:
    import yaml  # type: ignore[import-untyped]

    HAS_RUAMEL = False

try:
    import plotly.graph_objects as go  # type: ignore[import-not-found]

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from jinja2 import Template  # type: ignore[import-not-found]

    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

# Configure structured logging
logger = structlog.get_logger()
console = Console()

# Constants
SPRINT_STATUS_FILE = Path(__file__).parent.parent / "docs" / "sprint-status.yaml"
STORIES_DIR = Path(__file__).parent.parent / "docs" / "stories"
REPORTS_DIR = Path(__file__).parent.parent / "docs" / "reports"
VELOCITY_HISTORY_FILE = REPORTS_DIR / "velocity-history.json"

# Status transitions
VALID_STATUS_TRANSITIONS = {
    "backlog": ["drafted"],
    "drafted": ["ready-for-dev", "backlog"],
    "ready-for-dev": ["in-progress", "drafted"],
    "in-progress": ["review", "ready-for-dev"],
    "review": ["done", "in-progress"],
    "done": [],  # Terminal state
}

# Story point estimates (defaults)
DEFAULT_STORY_POINTS = {"small": 2, "medium": 5, "large": 8, "epic": 13}


class SprintStatusManager:
    """Manages sprint status tracking and reporting."""

    def __init__(self, status_file: Path = SPRINT_STATUS_FILE):
        """Initialize the sprint status manager."""
        self.status_file = status_file
        self.data: Dict[str, Any] = {}
        self.yaml = None

        # Setup YAML handler with comment preservation
        if HAS_RUAMEL:
            self.yaml = YAML()
            self.yaml.preserve_quotes = True
            self.yaml.width = 200
            self.yaml.indent(mapping=2, sequence=2, offset=0)

        # Load notification configuration from environment variables
        self.slack_webhook = os.environ.get("SPRINT_SLACK_WEBHOOK")
        self.teams_webhook = os.environ.get("SPRINT_TEAMS_WEBHOOK")
        self.notification_enabled = bool(self.slack_webhook or self.teams_webhook)

        logger.info(
            "initialized_sprint_manager",
            status_file=str(status_file),
            notifications_enabled=self.notification_enabled,
        )

    def load_status(self) -> Dict[str, Any]:
        """Load sprint status from YAML file."""
        if not self.status_file.exists():
            logger.error("status_file_not_found", path=str(self.status_file))
            raise FileNotFoundError(f"Sprint status file not found: {self.status_file}")

        try:
            if HAS_RUAMEL and self.yaml:
                with open(self.status_file, "r") as f:
                    self.data = self.yaml.load(f)
            else:
                with open(self.status_file, "r") as f:
                    self.data = yaml.safe_load(f)

            logger.info(
                "loaded_sprint_status", stories=len(self.data.get("development_status", {}))
            )
            return self.data
        except Exception as e:
            logger.error("failed_to_load_status", error=str(e))
            raise

    def save_status(self) -> None:
        """Save sprint status to YAML file, preserving comments."""
        try:
            if HAS_RUAMEL and self.yaml:
                # Preserve comments and formatting
                with open(self.status_file, "w") as f:
                    self.yaml.dump(self.data, f)
            else:
                # Fallback to standard YAML (loses comments)
                with open(self.status_file, "w") as f:
                    yaml.dump(
                        self.data, f, default_flow_style=False, sort_keys=False, allow_unicode=True
                    )

            logger.info("saved_sprint_status")
        except Exception as e:
            logger.error("failed_to_save_status", error=str(e))
            raise

    def display_status(self, verbose: bool = False) -> None:
        """Display current sprint status with breakdown."""
        self.load_status()
        dev_status = self.data.get("development_status", {})

        # Count statuses
        status_counts: Counter[str] = Counter()
        epic_status = {}

        for key, status in dev_status.items():
            if key.startswith("epic-") and not key.endswith("-retrospective"):
                epic_status[key] = status
            elif not key.endswith("-retrospective"):
                status_counts[status] += 1

        # Calculate completion percentage
        total_stories = sum(status_counts.values())
        done_stories = status_counts.get("done", 0)
        completion_pct = (done_stories / total_stories * 100) if total_stories > 0 else 0

        # Create summary panel
        summary = f"""[bold cyan]Sprint Status Summary[/bold cyan]

Total Stories: [bold]{total_stories}[/bold]
Completion: [bold green]{completion_pct:.1f}%[/bold green] ({done_stories}/{total_stories})

Status Breakdown:
  • Done: [green]{status_counts.get('done', 0)}[/green]
  • In Review: [yellow]{status_counts.get('review', 0)}[/yellow]
  • In Progress: [blue]{status_counts.get('in-progress', 0)}[/blue]
  • Ready for Dev: [cyan]{status_counts.get('ready-for-dev', 0)}[/cyan]
  • Drafted: [magenta]{status_counts.get('drafted', 0)}[/magenta]
  • Backlog: [dim]{status_counts.get('backlog', 0)}[/dim]"""

        console.print(Panel(summary, title="📊 Sprint Overview", border_style="cyan"))

        # Show epic breakdown if verbose
        if verbose:
            self._display_epic_breakdown(dev_status, epic_status)

        # Identify blockers
        blockers = self._identify_blockers(dev_status)
        if blockers:
            console.print("\n[bold red]⚠️  Potential Blockers:[/bold red]")
            for blocker in blockers:
                console.print(f"  • {blocker}")

    def _display_epic_breakdown(
        self, dev_status: Dict[str, str], epic_status: Dict[str, str]
    ) -> None:
        """Display breakdown by epic."""
        epic_stories = defaultdict(list)

        # Group stories by epic
        for key, status in dev_status.items():
            if "-" in key and not key.startswith("epic-"):
                epic_num = key.split("-")[0]
                epic_stories[f"epic-{epic_num}"].append((key, status))

        # Create epic table
        table = Table(title="Epic Breakdown", box=box.ROUNDED)
        table.add_column("Epic", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Stories", style="white")
        table.add_column("Progress", style="green")

        for epic_key in sorted(epic_stories.keys()):
            epic_stat = epic_status.get(epic_key, "backlog")
            stories = epic_stories[epic_key]
            done = sum(1 for _, s in stories if s == "done")
            total = len(stories)
            progress = f"{done}/{total} ({done/total*100:.0f}%)" if total > 0 else "0/0"

            table.add_row(epic_key, epic_stat, str(total), progress)

        console.print("\n")
        console.print(table)

    def _identify_blockers(self, dev_status: Dict[str, str]) -> List[str]:
        """Identify potential blockers in the sprint."""
        blockers = []

        # Check for stuck stories (in-progress for too long)
        in_progress = [
            k for k, v in dev_status.items() if v == "in-progress" and not k.startswith("epic-")
        ]
        if len(in_progress) > 3:
            blockers.append(f"{len(in_progress)} stories in progress (consider WIP limits)")

        # Check for review queue
        in_review = [
            k for k, v in dev_status.items() if v == "review" and not k.startswith("epic-")
        ]
        if len(in_review) > 2:
            blockers.append(f"{len(in_review)} stories awaiting review")

        # Check for uncontexted epics with drafted stories
        for key, status in dev_status.items():
            if key.startswith("epic-") and status == "backlog":
                epic_num = key.replace("epic-", "")
                has_stories = any(k.startswith(f"{epic_num}-") for k in dev_status.keys())
                if has_stories:
                    blockers.append(
                        f"Epic {epic_num} needs tech context before stories can progress"
                    )

        return blockers

    def update_story_status(self, story_key: str, new_status: str) -> bool:
        """Update the status of a specific story."""
        self.load_status()
        dev_status = self.data.get("development_status", {})

        if story_key not in dev_status:
            logger.error("story_not_found", story=story_key)
            return False

        current_status = dev_status[story_key]

        # Validate transition
        valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in valid_transitions and new_status != current_status:
            logger.error(
                "invalid_transition",
                story=story_key,
                current=current_status,
                new=new_status,
                valid=valid_transitions,
            )
            return False

        # Update status
        dev_status[story_key] = new_status
        self.save_status()

        logger.info(
            "updated_story_status",
            story=story_key,
            old_status=current_status,
            new_status=new_status,
        )

        # Send notification for status change
        self.send_notification(
            "Story Status Updated",
            f"**{story_key}**: {current_status} → {new_status}",
            "info",
        )

        return True

    def interactive_update(self) -> None:
        """Interactive CLI for updating story statuses."""
        self.load_status()
        dev_status = self.data.get("development_status", {})

        # Filter out epics and retrospectives for story list
        stories = {
            k: v
            for k, v in dev_status.items()
            if not k.startswith("epic-") and not k.endswith("-retrospective")
        }

        if not stories:
            console.print("[yellow]No stories found in sprint status[/yellow]")
            return

        console.print("[bold cyan]Interactive Story Status Update[/bold cyan]\n")

        # Display current stories
        table = Table(title="Current Stories", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Story Key", style="cyan")
        table.add_column("Status", style="yellow")

        story_list = list(stories.items())
        for idx, (key, status) in enumerate(story_list, 1):
            table.add_row(str(idx), key, status)

        console.print(table)

        # Select story to update
        try:
            choice = Prompt.ask("\nEnter story number to update (or 'q' to quit)")
            if choice.lower() == "q":
                return

            idx = int(choice) - 1
            if 0 <= idx < len(story_list):
                story_key, current_status = story_list[idx]

                # Show valid transitions
                valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
                if not valid_transitions:
                    console.print(
                        f"[yellow]Story '{story_key}' is in terminal state '{current_status}'[/yellow]"
                    )
                    return

                console.print(f"\n[cyan]Current status:[/cyan] {current_status}")
                console.print(f"[cyan]Valid transitions:[/cyan] {', '.join(valid_transitions)}")

                new_status = Prompt.ask("Enter new status", choices=valid_transitions)

                if self.update_story_status(story_key, new_status):
                    console.print(
                        f"[green]✓ Updated {story_key}: {current_status} → {new_status}[/green]"
                    )
                else:
                    console.print(f"[red]✗ Failed to update {story_key}[/red]")
            else:
                console.print("[red]Invalid story number[/red]")
        except (ValueError, KeyboardInterrupt):
            console.print("\n[yellow]Update cancelled[/yellow]")

    def generate_report(
        self, output_format: str = "markdown", output_file: Optional[Path] = None
    ) -> str:
        """Generate sprint report with metrics and charts."""
        self.load_status()
        dev_status = self.data.get("development_status", {})

        # Gather metrics
        metrics = self._calculate_metrics(dev_status)

        # Generate report content
        if output_format == "markdown":
            report = self._generate_markdown_report(metrics)
        elif output_format == "html" and HAS_JINJA2:
            report = self._generate_html_report(metrics)
        else:
            report = self._generate_text_report(metrics)

        # Save report
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report)
            logger.info("saved_sprint_report", file=str(output_file))
            console.print(f"[green]Report saved to: {output_file}[/green]")

        return report

    def _calculate_metrics(self, dev_status: Dict[str, str]) -> Dict[str, Any]:
        """Calculate sprint metrics."""
        stories = {
            k: v
            for k, v in dev_status.items()
            if not k.startswith("epic-") and not k.endswith("-retrospective")
        }

        # Status counts
        status_counts = Counter(stories.values())

        # Epic metrics
        epic_metrics: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "done": 0})
        for key, status in stories.items():
            if "-" in key:
                epic_num = key.split("-")[0]
                epic_metrics[f"epic-{epic_num}"]["total"] += 1
                if status == "done":
                    epic_metrics[f"epic-{epic_num}"]["done"] += 1

        # Calculate dates (mock for now - would read from git or config)
        today = datetime.now()
        sprint_start = today - timedelta(days=7)
        sprint_end = today + timedelta(days=7)

        return {
            "sprint_number": "Current",
            "start_date": sprint_start.strftime("%Y-%m-%d"),
            "end_date": sprint_end.strftime("%Y-%m-%d"),
            "total_stories": len(stories),
            "status_counts": dict(status_counts),
            "epic_metrics": dict(epic_metrics),
            "completion_pct": (status_counts.get("done", 0) / len(stories) * 100) if stories else 0,
            "velocity": status_counts.get("done", 0) * DEFAULT_STORY_POINTS["medium"],
        }

    def _generate_markdown_report(self, metrics: Dict[str, Any]) -> str:
        """Generate markdown format report."""
        report = f"""# Sprint Report - Sprint {metrics['sprint_number']}

## Summary
- **Start Date**: {metrics['start_date']}
- **End Date**: {metrics['end_date']}
- **Velocity**: {metrics['velocity']} points
- **Completion**: {metrics['completion_pct']:.1f}%

## Stories
| Status | Count |
|--------|-------|
| Done | {metrics['status_counts'].get('done', 0)} |
| In Review | {metrics['status_counts'].get('review', 0)} |
| In Progress | {metrics['status_counts'].get('in-progress', 0)} |
| Ready for Dev | {metrics['status_counts'].get('ready-for-dev', 0)} |
| Drafted | {metrics['status_counts'].get('drafted', 0)} |
| Backlog | {metrics['status_counts'].get('backlog', 0)} |

## Epic Progress
| Epic | Completed | Total | Progress |
|------|-----------|-------|----------|
"""

        for epic, data in sorted(metrics["epic_metrics"].items()):
            progress = (data["done"] / data["total"] * 100) if data["total"] > 0 else 0
            report += f"| {epic} | {data['done']} | {data['total']} | {progress:.0f}% |\n"

        report += f"""

## Metrics
- **Total Stories**: {metrics['total_stories']}
- **Completed**: {metrics['status_counts'].get('done', 0)}
- **In Progress**: {metrics['status_counts'].get('in-progress', 0)}
- **Blocked**: {metrics['status_counts'].get('blocked', 0)}

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def _generate_html_report(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML format report with charts."""
        if not HAS_JINJA2:
            return self._generate_markdown_report(metrics)

        # Create burndown chart if plotly available
        chart_html = ""
        if HAS_PLOTLY:
            chart_html = self._generate_burndown_chart(metrics)

        template = Template(
            """
<!DOCTYPE html>
<html>
<head>
    <title>Sprint Report - Sprint {{ sprint_number }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #3498db; color: white; }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
    </style>
</head>
<body>
    <h1>Sprint Report - Sprint {{ sprint_number }}</h1>

    <div class="metrics">
        <div class="metric">
            <div>Velocity</div>
            <div class="metric-value">{{ velocity }} points</div>
        </div>
        <div class="metric">
            <div>Completion</div>
            <div class="metric-value">{{ "%.1f"|format(completion_pct) }}%</div>
        </div>
    </div>

    <h2>Story Status</h2>
    <table>
        <tr><th>Status</th><th>Count</th></tr>
        {% for status, count in status_counts.items() %}
        <tr><td>{{ status }}</td><td>{{ count }}</td></tr>
        {% endfor %}
    </table>

    {{ chart_html|safe }}

    <p><small>Generated: {{ generated_at }}</small></p>
</body>
</html>
        """
        )

        return str(
            template.render(
                **metrics,
                chart_html=chart_html,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

    def _generate_text_report(self, metrics: Dict[str, Any]) -> str:
        """Generate plain text report."""
        return self._generate_markdown_report(metrics).replace("#", "").replace("|", " ")

    def _generate_burndown_chart(self, metrics: Dict[str, Any]) -> str:
        """Generate burndown chart HTML using plotly."""
        if not HAS_PLOTLY:
            return ""

        # Mock data for burndown (would calculate from history)
        days = list(range(14))
        ideal = [metrics["total_stories"] - (i * metrics["total_stories"] / 14) for i in days]
        actual = [
            metrics["total_stories"] - (i * metrics["status_counts"].get("done", 0) / 7)
            for i in range(8)
        ] + [None] * 6

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=days, y=ideal, mode="lines", name="Ideal", line=dict(dash="dash"))
        )
        fig.add_trace(go.Scatter(x=days[:8], y=actual[:8], mode="lines+markers", name="Actual"))

        fig.update_layout(
            title="Sprint Burndown Chart",
            xaxis_title="Days",
            yaxis_title="Stories Remaining",
            height=400,
        )

        return str(fig.to_html(include_plotlyjs="cdn", div_id="burndown-chart"))

    def calculate_velocity(self, sprints: int = 3) -> Dict[str, Any]:
        """Calculate team velocity over recent sprints."""
        # Load historical velocity data
        history = self._load_velocity_history()

        # Add current sprint data
        self.load_status()
        dev_status = self.data.get("development_status", {})
        done_count = sum(
            1 for k, v in dev_status.items() if v == "done" and not k.startswith("epic-")
        )

        current_velocity = done_count * DEFAULT_STORY_POINTS["medium"]

        # Update history
        sprint_key = f"sprint_{datetime.now().strftime('%Y%m%d')}"
        history[sprint_key] = {
            "date": datetime.now().isoformat(),
            "velocity": current_velocity,
            "stories_completed": done_count,
        }

        # Calculate metrics
        recent_sprints = list(history.values())[-sprints:]
        velocities = [s["velocity"] for s in recent_sprints]

        metrics = {
            "current_velocity": current_velocity,
            "average_velocity": sum(velocities) / len(velocities) if velocities else 0,
            "min_velocity": min(velocities) if velocities else 0,
            "max_velocity": max(velocities) if velocities else 0,
            "sprint_count": len(recent_sprints),
            "history": recent_sprints,
        }

        # Save updated history
        self._save_velocity_history(history)

        return metrics

    def _load_velocity_history(self) -> Dict[str, Any]:
        """Load velocity history from file."""
        if VELOCITY_HISTORY_FILE.exists():
            try:
                with open(VELOCITY_HISTORY_FILE, "r") as f:
                    data: Dict[str, Any] = json.load(f)
                    return data
            except Exception as e:
                logger.warning("failed_to_load_velocity_history", error=str(e))
        return {}

    def _save_velocity_history(self, history: Dict[str, Any]) -> None:
        """Save velocity history to file."""
        VELOCITY_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(VELOCITY_HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=2)
            logger.info("saved_velocity_history")
        except Exception as e:
            logger.error("failed_to_save_velocity_history", error=str(e))

    def display_velocity(self) -> None:
        """Display velocity metrics."""
        metrics = self.calculate_velocity()

        panel_content = f"""[bold cyan]Velocity Metrics[/bold cyan]

Current Sprint: [bold]{metrics['current_velocity']}[/bold] points
Average (last {metrics['sprint_count']} sprints): [bold]{metrics['average_velocity']:.1f}[/bold] points
Range: {metrics['min_velocity']} - {metrics['max_velocity']} points

Recent Sprint Performance:"""

        for sprint in metrics["history"][-5:]:
            date = datetime.fromisoformat(sprint["date"]).strftime("%Y-%m-%d")
            panel_content += (
                f"\n  • {date}: {sprint['velocity']} points ({sprint['stories_completed']} stories)"
            )

        console.print(Panel(panel_content, title="📈 Velocity Tracking", border_style="green"))

    def send_notification(
        self, title: str, message: str, notification_type: str = "info", retries: int = 3
    ) -> bool:
        """
        Send notification to configured webhooks (Slack/Teams).

        Args:
            title: Notification title
            message: Notification message body
            notification_type: Type of notification (info, warning, error, success)
            retries: Number of retry attempts for failed requests

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.notification_enabled:
            return False

        # Import requests here to avoid dependency if not using notifications
        try:
            import requests  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("requests_not_installed", message="Install requests for notifications")
            return False

        success = False

        # Color mapping for notification types
        color_map = {
            "info": "#36a64f",  # Green
            "warning": "#ff9900",  # Orange
            "error": "#ff0000",  # Red
            "success": "#00ff00",  # Bright green
        }
        color = color_map.get(notification_type, "#808080")

        # Send to Slack
        if self.slack_webhook:
            slack_payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "Sprint Status Manager",
                        "ts": int(datetime.now().timestamp()),
                    }
                ]
            }

            for attempt in range(retries):
                try:
                    response = requests.post(self.slack_webhook, json=slack_payload, timeout=5)
                    if response.status_code == 200:
                        logger.info("slack_notification_sent", title=title)
                        success = True
                        break
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        "slack_notification_failed",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    if attempt < retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff

        # Send to Microsoft Teams
        if self.teams_webhook:
            teams_payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color.replace("#", ""),
                "summary": title,
                "sections": [
                    {
                        "activityTitle": title,
                        "text": message,
                        "markdown": True,
                    }
                ],
            }

            for attempt in range(retries):
                try:
                    response = requests.post(self.teams_webhook, json=teams_payload, timeout=5)
                    if response.status_code == 200:
                        logger.info("teams_notification_sent", title=title)
                        success = True
                        break
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        "teams_notification_failed",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    if attempt < retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff

        return success

    def check_and_notify_blockers(self) -> None:
        """Check for blockers and send notifications if found."""
        self.load_status()
        dev_status = self.data.get("development_status", {})
        blockers = self._identify_blockers(dev_status)

        if blockers:
            message = "**Sprint Blockers Detected:**\n"
            for blocker in blockers:
                message += f"• {blocker}\n"

            self.send_notification(
                "⚠️ Sprint Blockers",
                message,
                "warning",
            )

    def notify_sprint_completion(self) -> None:
        """Send notification when sprint is completed."""
        self.load_status()
        dev_status = self.data.get("development_status", {})
        metrics = self._calculate_metrics(dev_status)

        if metrics["completion_pct"] >= 100:
            message = (
                f"**Sprint Completed!**\n\n"
                f"• Completed Stories: {metrics['completed']}\n"
                f"• Total Points: {metrics.get('total_points', 'N/A')}\n"
                f"• Duration: {metrics.get('sprint_days', 14)} days"
            )

            self.send_notification(
                "🎉 Sprint Completed",
                message,
                "success",
            )


def main() -> None:
    """Main entry point for the sprint status manager."""
    parser = argparse.ArgumentParser(description="Sprint Status Manager")
    parser.add_argument("--status", action="store_true", help="Display current sprint status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed breakdown")
    parser.add_argument("--update", action="store_true", help="Interactive story status update")
    parser.add_argument("--report", action="store_true", help="Generate sprint report")
    parser.add_argument(
        "--format", choices=["markdown", "html", "text"], default="markdown", help="Report format"
    )
    parser.add_argument("--output", type=Path, help="Output file for report")
    parser.add_argument(
        "--velocity", action="store_true", help="Calculate and display velocity metrics"
    )
    parser.add_argument("--story", help="Update specific story status")
    parser.add_argument("--set-status", help="New status for story")

    args = parser.parse_args()

    manager = SprintStatusManager()

    try:
        if args.status or (not any([args.update, args.report, args.velocity, args.story])):
            manager.display_status(verbose=args.verbose)

        elif args.update:
            if not HAS_RUAMEL:
                console.print(
                    "[yellow]Warning: ruamel.yaml not installed. "
                    "Comments in sprint-status.yaml will be lost.[/yellow]"
                )
                if not Confirm.ask("Continue anyway?"):
                    return
            manager.interactive_update()

        elif args.report:
            if not HAS_JINJA2 and args.format == "html":
                console.print(
                    "[yellow]Warning: jinja2 not installed. "
                    "Using markdown format instead.[/yellow]"
                )
                args.format = "markdown"

            output_file = args.output
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = "html" if args.format == "html" else "md"
                output_file = REPORTS_DIR / f"sprint_report_{timestamp}.{ext}"

            report = manager.generate_report(args.format, output_file)
            if not args.output:
                console.print(report)

        elif args.velocity:
            if not HAS_PLOTLY:
                console.print("[yellow]Note: Install plotly for burndown charts[/yellow]")
            manager.display_velocity()

        elif args.story and args.set_status:
            if manager.update_story_status(args.story, args.set_status):
                console.print(f"[green]✓ Updated {args.story} to {args.set_status}[/green]")
            else:
                console.print(f"[red]✗ Failed to update {args.story}[/red]")
                sys.exit(1)

        else:
            parser.print_help()

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("unexpected_error")
        sys.exit(1)


if __name__ == "__main__":
    main()

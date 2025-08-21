#!/usr/bin/env python
"""
CLI demo: prompt+budget → plan→run→print summary
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Optional

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from plugah.boardroom import BoardRoom

console = Console()


def print_prd(prd: dict):
    """Pretty print PRD"""

    table = Table(title="Product Requirements Document", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Title", prd.get("title", ""))
    table.add_row("Problem", prd.get("problem_statement", ""))
    table.add_row("Budget", f"${prd.get('budget', 0):,.2f}")
    table.add_row("Domain", prd.get("domain", ""))
    table.add_row("Users", prd.get("users", ""))

    if prd.get("success_criteria"):
        criteria = "\n".join(f"• {c}" for c in prd["success_criteria"])
        table.add_row("Success Criteria", criteria)

    if prd.get("objectives"):
        objectives = "\n".join(f"• {o['title']}" for o in prd["objectives"])
        table.add_row("Objectives", objectives)

    console.print(table)


def print_oag(oag: dict):
    """Pretty print OAG structure"""

    # Create org tree
    tree = Tree("📊 Organization Structure")

    # Board room
    board = tree.add("🏛️ Board Room")

    # Add agents by level
    agents = oag.get("nodes", {})

    # Group by level
    by_level = {}
    for _, agent in agents.items():
        if agent.get("node_type") == "agent":
            level = agent.get("level", "IC")
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(agent)

    # Add C-Suite
    if "C_SUITE" in by_level:
        for agent in by_level["C_SUITE"]:
            board.add(f"👔 {agent['role']} ({agent['id']})")

    # Add VPs
    if "VP" in by_level:
        vp_branch = tree.add("🎯 Vice Presidents")
        for agent in by_level["VP"]:
            vp_branch.add(f"📋 {agent['role']} ({agent['id']})")

    # Add Directors
    if "DIRECTOR" in by_level:
        dir_branch = tree.add("📁 Directors")
        for agent in by_level["DIRECTOR"]:
            dir_branch.add(f"📂 {agent['role']} ({agent['id']})")

    # Add Managers
    if "MANAGER" in by_level:
        mgr_branch = tree.add("👥 Managers")
        for agent in by_level["MANAGER"]:
            mgr_branch.add(f"👤 {agent['role']} ({agent['id']})")

    # Add ICs
    if "IC" in by_level:
        ic_branch = tree.add("⚡ Individual Contributors")
        for agent in by_level["IC"]:
            spec = agent.get('specialization', agent['role'])
            ic_branch.add(f"🔧 {spec} ({agent['id']})")

    console.print(tree)

    # Print task summary
    tasks = [n for n in agents.values() if n.get("node_type") == "task"]
    if tasks:
        task_table = Table(title=f"📝 Tasks ({len(tasks)} total)")
        task_table.add_column("Task ID", style="cyan")
        task_table.add_column("Description", style="white")
        task_table.add_column("Status", style="yellow")
        task_table.add_column("Agent", style="green")

        for task in tasks[:10]:  # Show first 10
            task_table.add_row(
                task.get("id", ""),
                task.get("description", "")[:50],
                task.get("status", "planned"),
                task.get("agent_id", "")
            )

        if len(tasks) > 10:
            task_table.add_row("...", f"and {len(tasks) - 10} more", "", "")

        console.print(task_table)

    # Print budget info
    budget = oag.get("budget", {})
    budget_panel = Panel(
        f"[green]Policy:[/green] {budget.get('policy', 'balanced')}\n"
        f"[yellow]Soft Cap:[/yellow] ${budget.get('caps', {}).get('soft_cap_usd', 0):,.2f}\n"
        f"[red]Hard Cap:[/red] ${budget.get('caps', {}).get('hard_cap_usd', 0):,.2f}\n"
        f"[cyan]Forecast:[/cyan] ${budget.get('forecast_cost_usd', 0):,.2f}",
        title="💰 Budget",
        expand=False
    )
    console.print(budget_panel)


def print_execution_summary(results: dict):
    """Print execution summary"""

    metrics = results.get("metrics", {})

    # Health scores
    health = metrics.get("health", {})
    health_table = Table(title="🏥 Health Scores")
    health_table.add_column("Metric", style="cyan")
    health_table.add_column("Score", style="white")
    health_table.add_column("Status", style="green")

    for key, value in health.items():
        status = "🟢" if value > 80 else "🟡" if value > 50 else "🔴"
        health_table.add_row(key.replace("_", " ").title(), f"{value:.1f}%", status)

    console.print(health_table)

    # Final costs
    cost_panel = Panel(
        f"[green]Total Spent:[/green] ${results.get('total_cost', 0):,.2f}\n"
        f"[yellow]Budget Remaining:[/yellow] ${results.get('budget_remaining', 0):,.2f}",
        title="💵 Final Costs",
        expand=False
    )
    console.print(cost_panel)

    # Task results
    task_results = results.get("results", {})
    if task_results:
        completed = sum(1 for r in task_results.values() if r.status.value == "done")
        failed = sum(1 for r in task_results.values() if r.status.value == "failed")

        rprint(f"\n[bold]Task Results:[/bold] {completed} completed, {failed} failed")


async def run_demo(
    prompt: str,
    budget: float,
    questions: Optional[list] = None,
    verbose: bool = False
):
    """Run the full demo flow"""

    console.print(Panel(f"[bold cyan]Plugah.ai Demo[/bold cyan]\n\nProject: {prompt}\nBudget: ${budget:,.2f}", expand=False))

    # Initialize board room
    boardroom = BoardRoom()

    # Add callback for verbose output
    if verbose:
        def print_event(event, data):
            console.print(f"[dim]Event: {event}[/dim]")
        boardroom.add_callback(print_event)

    # Phase 1: Startup Discovery
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running startup discovery...", total=None)

        discovery = await boardroom.startup_phase(prompt, budget)

        progress.update(task, completed=1)

    # Show questions (in real app, user would answer)
    console.print("\n[bold]Discovery Questions:[/bold]")
    for i, q in enumerate(discovery["questions"], 1):
        console.print(f"  {i}. {q}")

    # Simulate answers or use provided ones
    if not questions:
        questions = [
            "Developers and data scientists",
            "Accurate summarization, Fast processing, Easy integration",
            "Must handle rate limits, Secure API keys, Scalable architecture",
            "2 weeks",
            "Slack API"
        ]

    console.print("\n[dim]Using simulated answers...[/dim]\n")

    # Process answers
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating PRD...", total=None)

        prd = await boardroom.process_discovery(questions, prompt, budget)

        progress.update(task, completed=1)

    print_prd(prd)

    # Phase 2: Planning
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Planning organization...", total=None)

        oag = await boardroom.plan_organization(prd, budget)

        progress.update(task, completed=1)

    console.print("\n[bold]Planned OAG:[/bold]")
    print_oag(oag.model_dump())

    # Save OAG to file
    oag_path = Path(f".runs/{boardroom.project_id}/oag.json")
    oag_path.parent.mkdir(parents=True, exist_ok=True)
    with open(oag_path, 'w') as f:
        json.dump(oag.model_dump(), f, indent=2, default=str)

    console.print(f"\n[green]✓[/green] OAG saved to: {oag_path}")

    # Phase 3: Execution
    console.print("\n[bold]Starting execution...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Executing tasks...", total=len(oag.get_tasks()))

        # Add progress callback
        def update_progress(event, data):
            if event == "task_complete":
                progress.advance(task)

        boardroom.add_callback(update_progress)

        results = await boardroom.execute()

        progress.update(task, completed=len(oag.get_tasks()))

    # Print summary
    console.print("\n[bold]Execution Summary:[/bold]")
    print_execution_summary(results)

    # Save patches log
    patches_path = Path(f".runs/{boardroom.project_id}/patches.log")
    if boardroom.patch_manager:
        boardroom.patch_manager.export_patches(str(patches_path))
        console.print(f"[green]✓[/green] Patches saved to: {patches_path}")

    # Generate audit report
    boardroom.audit_logger.generate_summary_report()
    console.print(f"[green]✓[/green] Audit report saved to: .runs/{boardroom.project_id}/artifacts/summary_report.json")

    return boardroom.project_id


def main():
    """CLI entry point"""

    parser = argparse.ArgumentParser(description="Plugah.ai Demo CLI")
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Project prompt/description"
    )
    parser.add_argument(
        "--budget",
        type=float,
        required=True,
        help="Budget in USD"
    )
    parser.add_argument(
        "--answers",
        type=str,
        nargs="+",
        help="Discovery question answers (optional)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output"
    )

    args = parser.parse_args()

    # Run the demo
    project_id = asyncio.run(
        run_demo(
            prompt=args.prompt,
            budget=args.budget,
            questions=args.answers,
            verbose=args.verbose
        )
    )

    console.print(f"\n[bold green]Demo complete![/bold green] Project ID: {project_id}")


if __name__ == "__main__":
    main()

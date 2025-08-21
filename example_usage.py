#!/usr/bin/env python3
"""
Example usage of Plugah API for Seren integration
"""

import asyncio
import os


async def main():
    """Example end-to-end usage"""
    
    # Enable mock mode for demo (remove for real execution)
    os.environ["PLUGAH_MODE"] = "mock"
    
    # Import the required components
    from plugah import BoardRoom, BudgetPolicy
    
    # Initialize BoardRoom
    br = BoardRoom()
    
    # Phase 1: Generate discovery questions
    print("Phase 1: Startup Discovery")
    print("-" * 40)
    questions = await br.startup_phase(
        problem="Build a Slack bot that summarizes conversations",
        budget_usd=100.0,
        model_hint="gpt-3.5-turbo",
        policy=BudgetPolicy.BALANCED
    )
    
    print(f"Generated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    
    # Phase 2: Process answers into PRD
    print("\nPhase 2: Process Discovery")
    print("-" * 40)
    answers = [
        "Engineering teams and project managers",
        "1. Accurate summaries, 2. Real-time processing, 3. Easy setup",
        "Must respect Slack rate limits, secure credential storage",
        "2 weeks",
        "Slack API, OpenAI API"
    ]
    
    prd = await br.process_discovery(
        answers=answers,
        problem="Build a Slack bot that summarizes conversations",
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED
    )
    
    print(f"PRD created with {len(prd.objectives)} objectives")
    for obj in prd.objectives:
        print(f"  - {obj['title']}")
    
    # Phase 3: Plan organization
    print("\nPhase 3: Organization Planning")
    print("-" * 40)
    oag = await br.plan_organization(
        prd=prd,
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED
    )
    
    print(f"Created organization with:")
    print(f"  - {len(oag.get_agents())} agents")
    print(f"  - {len(oag.get_tasks())} tasks")
    print(f"  - Budget policy: {oag.budget.policy.value}")
    print(f"  - Forecast cost: ${oag.budget.forecast_cost_usd:.2f}")
    
    # Optional: Save state for later resumption
    br.save_state("project_state.json")
    print("\nState saved to project_state.json")
    
    # Phase 4: Execute
    print("\nPhase 4: Execution")
    print("-" * 40)
    
    # Optional: Add event handler
    async def handle_event(event, data):
        print(f"  Event: {event.value} - {data.get('message', '')}")
    
    result = await br.execute(on_event=handle_event)
    
    print(f"\n✅ Execution complete!")
    print(f"  - Total cost: ${result.total_cost}")
    print(f"  - Artifacts: {len(result.artifacts)} items")
    print(f"  - Metrics: {result.metrics}")
    
    # Demonstrate state restoration
    print("\n" + "=" * 40)
    print("Demonstrating state restoration...")
    br2 = BoardRoom()
    br2.load_state("project_state.json")
    print(f"Restored BoardRoom with project_id: {br2.project_id}")
    
    # Clean up
    os.remove("project_state.json")


async def example_with_materialize():
    """Example showing how to access materialization"""
    
    os.environ["PLUGAH_MODE"] = "mock"
    
    from plugah import BoardRoom, BudgetPolicy
    from plugah.materialize import Materializer
    
    # Create and execute through planning
    br = BoardRoom()
    
    questions = await br.startup_phase(
        "Create a data pipeline",
        budget_usd=50.0,
        policy=BudgetPolicy.CONSERVATIVE
    )
    
    prd = await br.process_discovery(
        ["Data team"] * len(questions),
        "Create a data pipeline",
        50.0
    )
    
    oag = await br.plan_organization(prd, 50.0)
    
    # Access materialization directly
    print("\nMaterialization Example")
    print("-" * 40)
    materializer = Materializer()
    agents, tasks, id_map = materializer.materialize(oag)
    
    print(f"Materialized {len(agents)} agents:")
    for agent_id, agent in agents.items():
        print(f"  - {agent_id}: {agent.role}")
    
    print(f"\nMaterialized {len(tasks)} tasks:")
    for task_id, task in tasks.items():
        print(f"  - {task_id}: {task.description[:50]}...")


if __name__ == "__main__":
    print("Plugah API Usage Examples")
    print("=" * 40)
    
    # Run main example
    asyncio.run(main())
    
    print("\n" + "=" * 40)
    
    # Run materialization example
    asyncio.run(example_with_materialize())
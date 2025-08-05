"""
Workflow Module for Orion AI Agent System

This module provides the main workflow function that now uses the agent-based architecture.
"""

import os
from typing import Optional

from .agents import WorkflowOrchestratorAgent


def run(
    repo_url: str,
    user_prompt: str,
    workdir: Optional[str] = None,
    enable_testing: bool = True,
    create_venv: bool = True,
    strict_testing: bool = False,
    commit_changes: bool = False,
    create_pr: bool = False,
) -> Optional[dict]:
    """
    Main workflow for the agent using the new agent-based architecture.

    Args:
        repo_url: GitHub repository URL
        user_prompt: Task description for the AI
        workdir: Working directory for cloning
        enable_testing: Whether to test the generated code
        create_venv: Whether to create a virtual environment
        strict_testing: Whether to abort on test failures
        commit_changes: Whether to commit the changes
        create_pr: Whether to create a pull request

    Returns:
        Optional[dict]: Workflow result with status, pr_url, and other data
    """
    # Determine debug mode from environment
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    # Initialize the workflow orchestrator agent
    orchestrator = WorkflowOrchestratorAgent(debug=debug_mode)

    # Run the complete workflow using the agent
    result = orchestrator.run_complete_workflow(
        repo_url=repo_url,
        user_prompt=user_prompt,
        workdir=workdir,
        enable_testing=enable_testing,
        create_venv=create_venv,
        strict_testing=strict_testing,
        commit_changes=commit_changes,
        create_pr=create_pr,
    )

    # Print workflow summary
    if result:
        print("\n" + "=" * 60)
        print("📊 WORKFLOW SUMMARY")
        print("=" * 60)

        status = result.get("status", "unknown")
        if status == "completed":
            print("✅ Status: Completed Successfully")
        elif status == "failed":
            print("❌ Status: Failed")
            error = result.get("error", "Unknown error")
            print(f"❌ Error: {error}")
        else:
            print(f"⚠️ Status: {status}")

        # Print phase information
        phases = result.get("phases", {})
        for phase_name, phase_info in phases.items():
            phase_status = phase_info.get("status", "unknown")
            if phase_status == "completed":
                print(f"✅ {phase_name.replace('_', ' ').title()}: Completed")
            else:
                print(f"❌ {phase_name.replace('_', ' ').title()}: {phase_status}")

        # Print created files
        created_files = result.get("created_files", [])
        if created_files:
            print(f"📁 Created Files: {', '.join(created_files)}")

        # Print duration if available
        duration = result.get("duration")
        if duration:
            print(f"⏱️ Duration: {duration:.2f} seconds")

        # Print PR URL if available
        pr_url = result.get("pr_url")
        if pr_url:
            print(f"🔗 Pull Request: {pr_url}")

        print("=" * 60)

        # Print agent summary if debug mode
        if debug_mode:
            print("\n🔧 AGENT EXECUTION SUMMARY")
            print("=" * 60)
            summary = orchestrator.get_workflow_summary()
            agents_summary = summary.get("agents_summary", {})

            for agent_name, agent_stats in agents_summary.items():
                success_rate = agent_stats.get("success_rate", 0)
                total_actions = agent_stats.get("total_actions", 0)
                print(f"🤖 {agent_name.replace('_', ' ').title()}:")
                print(f"   Actions: {total_actions}, Success Rate: {success_rate:.1f}%")
            print("=" * 60)

    else:
        print("❌ Workflow failed to complete - no result returned")

    return result

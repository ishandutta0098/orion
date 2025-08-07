"""
Workflow Module for Orion AI Agent System

This module provides the main workflow function using LangGraph for intelligent
agent coordination, parallel processing, and enhanced error recovery capabilities.
"""

import os
from typing import Optional

from .agents.langgraph_orchestrator_agent import LangGraphOrchestratorAgent


def run_intelligent_workflow(
    repo_url: str,
    user_prompt: str,
    workdir: Optional[str] = None,
    enable_testing: bool = True,
    create_venv: bool = True,
    conda_env: str = "ml",
    strict_testing: bool = False,
    commit_changes: bool = False,
    create_pr: bool = False,
    branch: Optional[str] = None,
) -> Optional[dict]:
    """
    Main workflow for the agent using LangGraph for intelligent coordination.

    This workflow provides significant enhancements over traditional approaches:

    ✨ Key Features:
    - 🧠 Intelligent workflow routing based on repository analysis
    - ⚡ Parallel agent execution for independent tasks
    - 🔄 Smart error recovery with multiple retry strategies
    - 📊 State-based decision making throughout the workflow
    - 🎯 Conditional workflow paths based on context
    - 💾 Built-in state persistence and checkpointing

    Args:
        repo_url: GitHub repository URL
        user_prompt: Task description for the AI
        workdir: Working directory for cloning
        enable_testing: Whether to test the generated code
        create_venv: Whether to create a virtual environment
        conda_env: Conda environment to use for running code
        strict_testing: Whether to abort on test failures
        commit_changes: Whether to commit the changes
        create_pr: Whether to create a pull request
        branch: Target branch to clone and work on

    Returns:
        Optional[dict]: Enhanced workflow result with detailed state tracking
    """
    # Determine debug mode from environment
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    # Initialize the LangGraph orchestrator
    orchestrator = LangGraphOrchestratorAgent(debug=debug_mode)

    if debug_mode:
        print("🚀 Starting Enhanced AI Workflow with LangGraph")
        print("=" * 60)
        print("🔥 FEATURES ENABLED:")
        print("  🧠 Intelligent workflow routing")
        print("  ⚡ Parallel agent processing")
        print("  🔄 Smart error recovery")
        print("  📊 Advanced state management")
        print("  🎯 Context-aware decisions")
        print("=" * 60)

    # Run the intelligent workflow
    result = orchestrator.run_intelligent_workflow(
        repo_url=repo_url,
        user_prompt=user_prompt,
        workdir=workdir,
        enable_testing=enable_testing,
        create_venv=create_venv,
        conda_env=conda_env,
        strict_testing=strict_testing,
        commit_changes=commit_changes,
        create_pr=create_pr,
        branch=branch,
    )

    # Enhanced result processing and display
    if result:
        print("\n" + "=" * 60)
        print("📊 LANGGRAPH WORKFLOW SUMMARY")
        print("=" * 60)

        status = result.get("status", "unknown")
        session_id = result.get("session_id", "unknown")

        if debug_mode:
            print(f"🆔 Session ID: {session_id}")

        if status == "completed":
            print("✅ Status: Completed Successfully")
        elif status == "failed":
            print("❌ Status: Failed")
            error = result.get("error", "Unknown error")
            print(f"❌ Error: {error}")

            # Show retry information
            retry_count = result.get("retry_count", 0)
            if retry_count > 0:
                print(f"🔄 Retry attempts: {retry_count}")
        else:
            print(f"⚠️ Status: {status}")

        # Show completed phases
        completed_phases = result.get("completed_phases", [])
        if completed_phases:
            print("✅ Completed Phases:")
            for phase in completed_phases:
                print(f"   ✓ {phase.replace('_', ' ').title()}")

        # Show failed phases (if any)
        failed_phases = result.get("failed_phases", [])
        if failed_phases:
            print("❌ Failed Phases:")
            for phase in failed_phases:
                print(f"   ✗ {phase.replace('_', ' ').title()}")

        # Show created files
        created_files = result.get("created_files", [])
        if created_files:
            print(f"📁 Created Files: {', '.join(created_files)}")

        # Show current phase
        current_phase = result.get("current_phase")
        if current_phase and debug_mode:
            print(f"📍 Last Phase: {current_phase.replace('_', ' ').title()}")

        # Show PR URL if available
        pr_url = result.get("pr_url")
        if pr_url:
            print(f"🔗 Pull Request: {pr_url}")
        elif result.get("create_pr"):
            # If PR creation was requested but no URL found, show debug info
            pr_info = result.get("pr_info")
            if pr_info:
                print(f"🔧 PR Info Available: {pr_info}")
            else:
                print("⚠️ PR creation was requested but no PR info found in result")

        # Show intelligent workflow benefits
        if debug_mode:
            print("\n🎯 LANGGRAPH ADVANTAGES UTILIZED:")

            parallel_tasks = result.get("parallel_tasks", [])
            if parallel_tasks:
                print(f"  ⚡ Parallel processing: {', '.join(parallel_tasks)}")

            if failed_phases and status != "failed":
                print("  🔄 Smart error recovery: Continued despite failures")

            if len(completed_phases) > 0:
                print(f"  📊 State management: Tracked {len(completed_phases)} phases")

        # Show duration if available
        duration = result.get("duration")
        if duration:
            print(f"⏱️ Duration: {duration:.2f} seconds")

        print("=" * 60)

        # Enhanced debug information
        if debug_mode:
            print("\n🔧 LANGGRAPH DEBUG INFORMATION")
            print("=" * 60)

            # Show state transitions
            messages = result.get("messages", [])
            if messages:
                print(f"💬 Message history: {len(messages)} state transitions")

            # Show retry information
            retry_count = result.get("retry_count", 0)
            print(f"🔄 Retry count: {retry_count}")

            # Show next agent if workflow was interrupted
            next_agent = result.get("next_agent")
            if next_agent:
                print(f"➡️  Next planned agent: {next_agent}")

            print("=" * 60)

    else:
        print("❌ LangGraph workflow failed to complete - no result returned")

    return result


# Keep the old function name for backwards compatibility
def run(
    repo_url: str,
    user_prompt: str,
    workdir: Optional[str] = None,
    enable_testing: bool = True,
    create_venv: bool = True,
    strict_testing: bool = False,
    commit_changes: bool = False,
    create_pr: bool = False,
    branch: Optional[str] = None,
) -> Optional[dict]:
    """
    Backwards compatibility wrapper for the intelligent workflow.

    This function maintains API compatibility while using LangGraph underneath.
    """
    return run_intelligent_workflow(
        repo_url=repo_url,
        user_prompt=user_prompt,
        workdir=workdir,
        enable_testing=enable_testing,
        create_venv=create_venv,
        strict_testing=strict_testing,
        commit_changes=commit_changes,
        create_pr=create_pr,
        branch=branch,
    )

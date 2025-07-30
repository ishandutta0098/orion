"""
Agents Package for Orion AI Agent System

This package contains all the specialized agents that work together to provide
AI-powered code generation and repository management capabilities.
"""

from .ai_generator_agent import AIGeneratorAgent
from .code_tester_agent import CodeTesterAgent
from .environment_manager_agent import EnvironmentManagerAgent
from .git_operations_agent import GitOperationsAgent
from .github_integration_agent import GitHubIntegrationAgent
from .workflow_orchestrator_agent import WorkflowOrchestratorAgent

__all__ = [
    "AIGeneratorAgent",
    "CodeTesterAgent",
    "EnvironmentManagerAgent",
    "GitOperationsAgent",
    "GitHubIntegrationAgent",
    "WorkflowOrchestratorAgent",
]

__version__ = "1.0.0"

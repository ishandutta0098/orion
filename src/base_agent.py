"""
Base Agent Class for Orion AI Agent System

This module provides the base agent functionality that all specific agents inherit from.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAgent(ABC):
    """
    Base class for all agents in the Orion AI Agent system.

    Provides common functionality like logging, state management, and error handling.
    """

    def __init__(self, name: str, debug: bool = False):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            debug: Whether to enable debug mode
        """
        self.name = name
        self.debug = debug
        self.state = {}
        self.execution_history = []

        # Setup logging
        self.logger = logging.getLogger(f"orion.{name}")
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # Create console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(f"🤖 [{name}] %(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log(self, message: str, level: str = "info") -> None:
        """
        Log a message with the specified level.

        Args:
            message: Message to log
            level: Log level (info, debug, warning, error)
        """
        getattr(self.logger, level.lower())(message)

    def update_state(self, key: str, value: Any) -> None:
        """
        Update the agent's state.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
        self.log(f"State updated: {key} = {value}", "debug")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the agent's state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self.state.get(key, default)

    def record_execution(self, action: str, result: Any, duration: float) -> None:
        """
        Record an execution in the agent's history.

        Args:
            action: Action performed
            result: Result of the action
            duration: Time taken to execute
        """
        execution_record = {
            "timestamp": time.time(),
            "action": action,
            "result": result,
            "duration": duration,
            "success": result is not None and not isinstance(result, Exception),
        }
        self.execution_history.append(execution_record)
        self.log(f"Recorded execution: {action} (took {duration:.2f}s)", "debug")

    def execute_with_tracking(self, action_name: str, func, *args, **kwargs) -> Any:
        """
        Execute a function with automatic tracking and error handling.

        Args:
            action_name: Name of the action being performed
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or None if error occurred
        """
        self.log(f"Starting action: {action_name}")
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            self.record_execution(action_name, result, duration)
            self.log(f"Completed action: {action_name} ✅")
            return result

        except Exception as e:
            duration = time.time() - start_time
            self.record_execution(action_name, e, duration)
            self.log(f"Failed action: {action_name} ❌ Error: {e}", "error")
            return None

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the agent's execution history.

        Returns:
            Dictionary containing execution statistics
        """
        if not self.execution_history:
            return {"total_actions": 0, "success_rate": 0, "total_time": 0}

        successful = sum(1 for record in self.execution_history if record["success"])
        total_time = sum(record["duration"] for record in self.execution_history)

        return {
            "total_actions": len(self.execution_history),
            "successful_actions": successful,
            "failed_actions": len(self.execution_history) - successful,
            "success_rate": successful / len(self.execution_history) * 100,
            "total_time": total_time,
            "average_time": total_time / len(self.execution_history),
        }

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Main execution method that each agent must implement.

        Args:
            *args: Variable arguments
            **kwargs: Keyword arguments

        Returns:
            Execution result
        """
        pass

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}', state={self.state})"

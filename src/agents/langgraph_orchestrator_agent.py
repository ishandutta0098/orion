"""
LangGraph Workflow Orchestrator Agent for Orion AI Agent System

This agent uses LangGraph to provide intelligent workflow orchestration with
dynamic routing, parallel processing, and enhanced error recovery capabilities.
"""

import os
import sys
from operator import add
from typing import Annotated, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent

from .ai_generator_agent import AIGeneratorAgent
from .code_tester_agent import CodeTesterAgent
from .environment_manager_agent import EnvironmentManagerAgent
from .git_operations_agent import GitOperationsAgent
from .github_integration_agent import GitHubIntegrationAgent
from .repository_scanner_agent import RepositoryScannerAgent
from .task_classifier_agent import TaskClassifierAgent


class WorkflowState(TypedDict):
    """
    State structure for the LangGraph workflow.

    This maintains the complete state of the workflow as it progresses
    through different phases and agents.
    """

    # Input parameters
    repo_url: str
    user_prompt: str
    workdir: Optional[str]
    target_branch: Optional[str]
    enable_testing: bool
    create_venv: bool
    conda_env: str
    strict_testing: bool
    commit_changes: bool
    create_pr: bool

    # Workflow state
    session_id: str
    current_phase: str
    messages: Annotated[List[BaseMessage], add]
    start_time: Optional[float]

    # Results from each phase
    repo_path: Optional[str]
    branch_name: Optional[str]
    generated_code: Optional[str]
    created_files: List[str]
    modified_files: List[str]
    repository_scan: Optional[Dict]
    task_classification: Optional[Dict]
    test_results: Optional[Dict]
    venv_path: Optional[str]
    commit_info: Optional[Dict]
    pr_info: Optional[Dict]
    pr_url: Optional[str]

    # Status tracking
    status: str
    error: Optional[str]
    completed_phases: List[str]
    failed_phases: List[str]

    # Agent coordination
    next_agent: Optional[str]
    parallel_tasks: List[str]
    retry_count: int

    # Timing information
    end_time: Optional[float]
    duration: Optional[float]


class LangGraphOrchestratorAgent(BaseAgent):
    """
    Advanced workflow orchestrator using LangGraph for intelligent agent coordination.

    Capabilities:
    - Dynamic workflow routing based on context
    - Parallel agent execution for independent tasks
    - Intelligent error recovery and retry mechanisms
    - State-based decision making
    - Conditional workflow paths
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the LangGraph Orchestrator Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("LangGraphOrchestrator", debug)

        # Initialize all sub-agents
        self.git_agent = GitOperationsAgent(debug=debug)
        self.ai_agent = AIGeneratorAgent(debug=debug)
        self.github_agent = GitHubIntegrationAgent(debug=debug)
        self.env_agent = EnvironmentManagerAgent(debug=debug)
        self.test_agent = CodeTesterAgent(debug=debug)
        self.scanner_agent = RepositoryScannerAgent(debug=debug)
        self.classifier_agent = TaskClassifierAgent(debug=debug)

        # Initialize LangGraph components
        self.memory = MemorySaver()
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.memory)

        self.log(
            "🚀 LangGraph Orchestrator Agent initialized with intelligent workflow routing"
        )

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with intelligent routing and parallel processing.

        Returns:
            StateGraph: The compiled workflow graph
        """
        workflow = StateGraph(WorkflowState)

        # Add all workflow nodes
        workflow.add_node("analyze_repository", self._analyze_repository)
        workflow.add_node("classify_task", self._classify_task_node)
        workflow.add_node("scan_repository", self._scan_repository_node)
        workflow.add_node("setup_repository", self._setup_repository_node)
        workflow.add_node("generate_code", self._generate_code_node)
        workflow.add_node("setup_environment", self._setup_environment_node)
        workflow.add_node("run_tests", self._run_tests_node)
        workflow.add_node("commit_changes", self._commit_changes_node)
        workflow.add_node("create_pull_request", self._create_pr_node)
        workflow.add_node("error_recovery", self._error_recovery_node)
        workflow.add_node("parallel_coordinator", self._parallel_coordinator)

        # Define the workflow entry point
        workflow.set_entry_point("analyze_repository")

        # Add conditional edges for intelligent routing
        workflow.add_conditional_edges(
            "analyze_repository",
            self._route_after_analysis,
            {
                "classify_task": "classify_task",
                "error": "error_recovery",
            },
        )

        workflow.add_conditional_edges(
            "classify_task",
            self._route_after_classification,
            {
                "scan_repository": "scan_repository",
                "setup_repository": "setup_repository",
                "error": "error_recovery",
            },
        )

        workflow.add_conditional_edges(
            "scan_repository",
            self._route_after_scan,
            {
                "setup_repository": "setup_repository",
                "error": "error_recovery",
            },
        )

        workflow.add_conditional_edges(
            "setup_repository",
            self._route_after_repo_setup,
            {
                "scan_repository": "scan_repository",
                "generate_code": "generate_code",
                "parallel_setup": "parallel_coordinator",
                "error": "error_recovery",
            },
        )

        workflow.add_conditional_edges(
            "generate_code",
            self._route_after_code_generation,
            {
                "test_code": "setup_environment",
                "commit_direct": "commit_changes",
                "parallel_test_commit": "parallel_coordinator",
                "error": "error_recovery",
            },
        )

        workflow.add_conditional_edges(
            "parallel_coordinator",
            self._route_parallel_completion,
            {
                "setup_environment": "setup_environment",
                "run_tests": "run_tests",
                "commit_changes": "commit_changes",
                "create_pr": "create_pull_request",
                "complete": END,
                "error": "error_recovery",
            },
        )

        # Add linear edges for standard flow
        workflow.add_edge("setup_environment", "run_tests")

        workflow.add_conditional_edges(
            "run_tests",
            self._route_after_testing,
            {
                "commit": "commit_changes",
                "retry_generation": "generate_code",
                "error": "error_recovery",
                "complete": END,
            },
        )

        workflow.add_conditional_edges(
            "commit_changes",
            self._route_after_commit,
            {
                "create_pr": "create_pull_request",
                "complete": END,
                "error": "error_recovery",
            },
        )

        workflow.add_edge("create_pull_request", END)

        workflow.add_conditional_edges(
            "error_recovery",
            self._route_error_recovery,
            {
                "retry": "analyze_repository",
                "retry_generation": "generate_code",
                "retry_testing": "setup_environment",
                "retry_commit": "commit_changes",
                "abort": END,
            },
        )

        return workflow

    def _analyze_repository(self, state: WorkflowState) -> WorkflowState:
        """
        Analyze the repository to determine the optimal workflow path.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        self.log("🔍 Analyzing repository and planning workflow...")

        try:
            # Add analysis message
            state["messages"].append(
                SystemMessage(
                    content=f"Analyzing repository {state['repo_url']} for task: {state['user_prompt']}"
                )
            )

            # Perform repository analysis
            state["current_phase"] = "analysis"
            state["status"] = "analyzing"

            # This is where we could add intelligent analysis
            # For now, we'll determine the workflow based on the prompt
            prompt_lower = state["user_prompt"].lower()

            # Determine if this is a complex task requiring parallel processing
            if any(
                keyword in prompt_lower
                for keyword in ["complex", "multiple", "parallel", "concurrent"]
            ):
                state["parallel_tasks"] = ["environment_setup", "code_analysis"]
                self.log("📊 Detected complex task - will use parallel processing")

            state["completed_phases"].append("analysis")
            state["status"] = "planning_complete"

        except Exception as e:
            state["error"] = f"Repository analysis failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("analysis")

        return state

    def _classify_task_node(self, state: WorkflowState) -> WorkflowState:
        """
        Classify the user task to determine approach.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        self.log("🔍 Classifying task...")

        try:
            state["current_phase"] = "task_classification"

            # Classify the task
            classification = self.classifier_agent.classify_task(state["user_prompt"])

            state["task_classification"] = classification
            state["completed_phases"].append("task_classification")
            state["status"] = "task_classified"

            primary_action = classification.get("primary_action", "create")
            task_type = classification.get("task_type", "general")
            confidence = classification.get("confidence", 0.5)

            self.log(
                f"✅ Task classified: {primary_action} ({task_type}) - confidence: {confidence:.2f}"
            )

        except Exception as e:
            state["error"] = f"Task classification failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("task_classification")

        return state

    def _scan_repository_node(self, state: WorkflowState) -> WorkflowState:
        """
        Scan the repository to understand its structure.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        self.log("🔍 Scanning repository...")

        try:
            state["current_phase"] = "repository_scan"

            if not state.get("repo_path"):
                raise Exception("Repository path not available")

            # Scan the repository
            scan_result = self.scanner_agent.scan_repository(state["repo_path"])

            state["repository_scan"] = scan_result

            # Validate mentioned files against repository
            task_classification = state.get("task_classification", {})
            if task_classification:
                mentioned_files = task_classification.get("mentioned_files", [])
                if mentioned_files:
                    validated_files = self.classifier_agent.validate_and_find_files(
                        mentioned_files, scan_result
                    )
                    # Update task classification with validated files
                    task_classification["target_files"] = validated_files
                    task_classification["validated_files"] = validated_files
                    state["task_classification"] = task_classification
                    self.log(f"💡 Validated files: {validated_files}")

            state["completed_phases"].append("repository_scan")
            state["status"] = "repository_scanned"

            total_files = scan_result.get("total_files", 0)
            python_files = len(scan_result.get("python_files", []))

            self.log(
                f"✅ Repository scanned: {total_files} files ({python_files} Python files)"
            )

        except Exception as e:
            state["error"] = f"Repository scan failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("repository_scan")

        return state

    def _route_after_analysis(self, state: WorkflowState) -> str:
        """Route after repository analysis."""
        if state["status"] == "error":
            return "error"
        return "classify_task"

    def _route_after_classification(self, state: WorkflowState) -> str:
        """Route after task classification."""
        if state["status"] == "error":
            return "error"

        # Always setup repository first, then optionally scan
        return "setup_repository"

    def _route_after_scan(self, state: WorkflowState) -> str:
        """Route after repository scan."""
        if state["status"] == "error":
            return "error"
        return "setup_repository"

    def _setup_repository_node(self, state: WorkflowState) -> WorkflowState:
        """Repository setup node for LangGraph workflow."""
        self.log("🔄 Setting up repository...")

        try:
            state["current_phase"] = "repository_setup"

            # Use the existing git agent functionality
            workdir = state["workdir"] or "/Users/ishandutta/Documents/code"
            repo_name = state["repo_url"].split("/")[-1].replace(".git", "")
            repo_path = os.path.join(workdir, repo_name)

            # Clone repository
            clone_success = self.git_agent.clone_repository(
                state["repo_url"], repo_path, target_branch=state.get("target_branch")
            )
            if not clone_success:
                raise Exception("Failed to clone repository")

            # Create branch for AI changes
            import time

            base_branch_name = f"ai-update-{repo_name}-{int(time.time())}"
            branch_name = self.git_agent.create_unique_branch(
                base_branch_name, repo_path
            )

            if not branch_name:
                raise Exception("Failed to create branch")

            branch_created = self.git_agent.create_and_switch_branch(
                branch_name, repo_path
            )
            if not branch_created:
                raise Exception("Failed to switch to new branch")

            state["repo_path"] = repo_path
            state["branch_name"] = branch_name
            state["completed_phases"].append("repository_setup")
            state["status"] = "repo_ready"

            self.log(f"✅ Repository setup complete: {repo_path}")

        except Exception as e:
            state["error"] = f"Repository setup failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("repository_setup")

        return state

    def _generate_code_node(self, state: WorkflowState) -> WorkflowState:
        """Enhanced code generation node with context awareness."""
        self.log("🤖 Generating code with enhanced context...")

        try:
            state["current_phase"] = "code_generation"

            # Get context from previous phases
            repository_context = state.get("repository_scan")
            task_classification = state.get("task_classification")

            # Generate code using enhanced AI agent
            if repository_context or task_classification:
                generated_code = self.ai_agent.generate_code_with_context(
                    state["user_prompt"],
                    state["repo_path"],
                    repository_context,
                    task_classification,
                )
            else:
                # Fallback to basic generation
                generated_code = self.ai_agent.generate_code_changes(
                    state["user_prompt"], state["repo_path"]
                )

            if not generated_code:
                raise Exception("Code generation failed")

            # Apply code changes using the available method
            success = self.ai_agent.make_code_changes(
                generated_code, state["repo_path"]
            )

            if success:
                # Get the lists of created and modified files from the agent state
                state["created_files"] = self.ai_agent.get_created_files()
                state["modified_files"] = self.ai_agent.get_modified_files()
            else:
                self.log("⚠️ Code application failed", "warning")
                state["created_files"] = []
                state["modified_files"] = []

            state["generated_code"] = generated_code
            state["completed_phases"].append("code_generation")
            state["status"] = "code_generated"

            total_changes = len(state["created_files"]) + len(state["modified_files"])
            self.log(
                f"✅ Code generation complete. Created {len(state['created_files'])} files, "
                f"modified {len(state['modified_files'])} files (total: {total_changes} changes)"
            )

        except Exception as e:
            state["error"] = f"Code generation failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("code_generation")

        return state

    def _setup_environment_node(self, state: WorkflowState) -> WorkflowState:
        """Environment setup node for LangGraph workflow."""
        self.log("🧪 Setting up environment...")

        try:
            state["current_phase"] = "environment_setup"

            if state["create_venv"]:
                # Legacy: Create virtual environment
                self.log("⚠️ Using legacy virtual environment creation")
                venv_path = self.env_agent.create_virtual_environment(
                    state["repo_path"]
                )
                if venv_path:
                    state["venv_path"] = venv_path
                    venv_python = self.env_agent.get_venv_python(venv_path)

                    # Install dependencies
                    deps_installed = self.env_agent.install_dependencies(
                        state["repo_path"], venv_python
                    )
                    if deps_installed:
                        self.env_agent.create_requirements_file(
                            state["repo_path"], venv_python
                        )
            else:
                # Use conda environment (preferred)
                conda_env = state.get("conda_env", "ml")
                self.log(f"🐍 Using conda environment: {conda_env}")

                # Set the conda environment for testing
                state["venv_path"] = f"conda:{conda_env}"
                self.log(f"✅ Conda environment configured: {conda_env}")

            state["completed_phases"].append("environment_setup")
            state["status"] = "environment_ready"

            self.log("✅ Environment setup complete")

        except Exception as e:
            state["error"] = f"Environment setup failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("environment_setup")

        return state

    def _run_tests_node(self, state: WorkflowState) -> WorkflowState:
        """Testing node for LangGraph workflow."""
        self.log("🧪 Running tests...")

        try:
            state["current_phase"] = "testing"

            if state["enable_testing"] and (
                state["created_files"] or state["modified_files"]
            ):
                # Determine execution environment
                if state.get("venv_path", "").startswith("conda:"):
                    # Use conda environment
                    conda_env = state["venv_path"].replace("conda:", "")
                    venv_python = f"conda run -n {conda_env} python"
                else:
                    # Use virtual environment (legacy)
                    venv_python = (
                        self.env_agent.get_venv_python(state["venv_path"])
                        if state["venv_path"]
                        else None
                    )

                # Combine created and modified files for testing
                test_files = state["created_files"] + state.get("modified_files", [])

                test_passed = self.test_agent.test_generated_code(
                    state["repo_path"], venv_python, test_files
                )

                test_results = self.test_agent.get_test_results(state["repo_path"])
                state["test_results"] = test_results

                if not test_passed and state["strict_testing"]:
                    raise Exception("Tests failed in strict mode")

                state["completed_phases"].append("testing")
                state["status"] = "tests_complete"

                if test_passed:
                    self.log("✅ All tests passed")
                else:
                    self.log("⚠️ Some tests failed, but continuing...")
            else:
                state["status"] = "tests_skipped"
                self.log("⚠️ Testing skipped")

        except Exception as e:
            state["error"] = f"Testing failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("testing")

        return state

    def _commit_changes_node(self, state: WorkflowState) -> WorkflowState:
        """Commit changes node for LangGraph workflow."""
        self.log("📝 Committing changes...")

        try:
            state["current_phase"] = "commit"

            if state["commit_changes"]:
                # Create commit message
                commit_message = f":robot: [orion] {state['user_prompt']}"

                commit_success = self.git_agent.commit_changes(
                    commit_message, state["repo_path"]
                )

                if not commit_success:
                    raise Exception("Failed to commit changes")

                state["commit_info"] = {
                    "message": commit_message,
                    "branch": state["branch_name"],
                    "success": True,
                }

                state["completed_phases"].append("commit")
                state["status"] = "committed"

                self.log("✅ Changes committed successfully")
            else:
                state["status"] = "commit_skipped"
                self.log("⚠️ Commit skipped")

        except Exception as e:
            state["error"] = f"Commit failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("commit")

        return state

    def _create_pr_node(self, state: WorkflowState) -> WorkflowState:
        """Create pull request node for LangGraph workflow."""
        self.log("🚀 Creating pull request...")

        try:
            state["current_phase"] = "pull_request"

            if state["create_pr"]:
                # Push branch first
                push_success = self.git_agent.push_branch(
                    state["branch_name"], state["repo_path"]
                )

                if push_success:
                    # Create PR
                    pr_title = f":robot: [orion] {state['user_prompt']}"
                    pr_body = f"This PR contains AI-generated changes for: {state['user_prompt']}\n\nGenerated by Orion AI Agent"

                    pr_result = self.github_agent.create_pull_request(
                        state["repo_url"], pr_title, pr_body, state["branch_name"]
                    )

                    if pr_result:
                        state["pr_info"] = pr_result
                        state["pr_url"] = pr_result.get("pr_url")
                        state["completed_phases"].append("pull_request")
                        state["status"] = "completed"

                        self.log(f"✅ Pull request created: {state['pr_url']}")
                    else:
                        raise Exception("Failed to create pull request")
                else:
                    raise Exception("Failed to push branch")
            else:
                state["status"] = "completed"
                self.log("⚠️ Pull request creation skipped")

        except Exception as e:
            state["error"] = f"PR creation failed: {str(e)}"
            state["status"] = "error"
            state["failed_phases"].append("pull_request")

        return state

    def _parallel_coordinator(self, state: WorkflowState) -> WorkflowState:
        """Coordinate parallel task execution."""
        self.log("🔄 Coordinating parallel tasks...")

        # This is a placeholder for parallel task coordination
        # In a full implementation, this would manage concurrent execution
        state["status"] = "parallel_coordination"

        return state

    def _error_recovery_node(self, state: WorkflowState) -> WorkflowState:
        """Handle error recovery and retry logic."""
        self.log(
            f"🔧 Handling error recovery for: {state.get('error', 'Unknown error')}"
        )

        # Increment retry count
        state["retry_count"] = state.get("retry_count", 0) + 1

        # Determine recovery strategy based on failed phase
        if state["retry_count"] < 3:
            last_failed = state["failed_phases"][-1] if state["failed_phases"] else None

            if last_failed == "code_generation":
                state["next_agent"] = "retry_generation"
                self.log("🔄 Will retry code generation with modified prompt")
            elif last_failed == "testing":
                state["next_agent"] = "retry_testing"
                self.log("🔄 Will retry testing with relaxed constraints")
            else:
                state["next_agent"] = "retry"
                self.log("🔄 Will retry from the beginning")
        else:
            state["next_agent"] = "abort"
            state["status"] = "failed"
            self.log("❌ Maximum retries exceeded, aborting workflow")

        return state

    # Routing functions for conditional edges
    def _route_after_analysis(self, state: WorkflowState) -> str:
        """Route after repository analysis."""
        if state["status"] == "error":
            return "error"
        return "classify_task"

    def _route_after_repo_setup(self, state: WorkflowState) -> str:
        """Route after repository setup."""
        if state["status"] == "error":
            return "error"

        # Check if repository scan is needed
        classification = state.get("task_classification", {})
        requires_scan = classification.get("requires_repository_scan", False)

        if requires_scan and not state.get("repository_scan"):
            return "scan_repository"

        # Check if we should use parallel processing
        if state.get("parallel_tasks"):
            return "parallel_setup"

        return "generate_code"

    def _route_after_code_generation(self, state: WorkflowState) -> str:
        """Route after code generation."""
        if state["status"] == "error":
            return "error"

        # Decide based on configuration
        if not state["enable_testing"]:
            return "commit_direct"

        # Check if we can run testing and commit in parallel
        if state.get("parallel_tasks") and "parallel" in state["user_prompt"].lower():
            return "parallel_test_commit"

        return "test_code"

    def _route_after_testing(self, state: WorkflowState) -> str:
        """Route after testing."""
        if state["status"] == "error":
            if state["strict_testing"]:
                return "error"
            else:
                # Continue despite test failures
                return "commit"

        if not state["commit_changes"]:
            return "complete"

        return "commit"

    def _route_after_commit(self, state: WorkflowState) -> str:
        """Route after commit."""
        if state["status"] == "error":
            return "error"

        if state["create_pr"]:
            return "create_pr"

        return "complete"

    def _route_parallel_completion(self, state: WorkflowState) -> str:
        """Route parallel task completion."""
        # This would contain logic for managing parallel task completion
        return "complete"

    def _route_error_recovery(self, state: WorkflowState) -> str:
        """Route error recovery."""
        return state.get("next_agent", "abort")

    def run_intelligent_workflow(
        self,
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
    ) -> Dict[str, any]:
        """
        Run the intelligent workflow using LangGraph.

        Args:
            repo_url: GitHub repository URL
            user_prompt: Task description for the AI
            workdir: Working directory for cloning
            enable_testing: Whether to test the generated code
            create_venv: Whether to create a virtual environment
            strict_testing: Whether to abort on test failures
            commit_changes: Whether to commit the changes
            create_pr: Whether to create a pull request
            branch: Target branch to clone and work on

        Returns:
            Dict: Workflow results and summary
        """

        def _workflow_operation():
            import time

            # Initialize state
            start_time = time.time()
            initial_state = WorkflowState(
                repo_url=repo_url,
                user_prompt=user_prompt,
                workdir=workdir,
                target_branch=branch,
                enable_testing=enable_testing,
                create_venv=create_venv,
                conda_env=conda_env,
                strict_testing=strict_testing,
                commit_changes=commit_changes,
                create_pr=create_pr,
                session_id=f"langgraph_workflow_{int(start_time)}",
                current_phase="initialization",
                messages=[HumanMessage(content=f"Task: {user_prompt}")],
                repo_path=None,
                branch_name=None,
                generated_code=None,
                created_files=[],
                modified_files=[],
                repository_scan=None,
                task_classification=None,
                test_results=None,
                venv_path=None,
                commit_info=None,
                pr_info=None,
                pr_url=None,
                status="initializing",
                error=None,
                completed_phases=[],
                failed_phases=[],
                next_agent=None,
                parallel_tasks=[],
                retry_count=0,
                start_time=start_time,
                end_time=None,
                duration=None,
            )

            self.log("🚀 Starting LangGraph intelligent workflow...")

            try:
                # Create a thread configuration for state persistence
                config = {"configurable": {"thread_id": initial_state["session_id"]}}

                # Run the workflow
                final_state = initial_state
                for chunk in self.app.stream(initial_state, config):
                    # Each chunk contains the state updates from different nodes
                    if isinstance(chunk, dict):
                        for node_name, node_state in chunk.items():
                            if isinstance(node_state, dict):
                                # Update final_state with the latest node state
                                final_state.update(node_state)

                                # Log current state
                                current_phase = node_state.get(
                                    "current_phase", "unknown"
                                )
                                status = node_state.get("status", "unknown")
                                self.log(f"📊 Phase: {current_phase}, Status: {status}")

                # Ensure we have a final status and duration
                if final_state.get("status") in [
                    "completed",
                    "failed",
                ] and not final_state.get("duration"):
                    import time

                    final_state["end_time"] = time.time()
                    # Only calculate duration if start_time exists
                    start_time = final_state.get("start_time")
                    if start_time:
                        final_state["duration"] = final_state["end_time"] - start_time
                    else:
                        # If no start_time, we can't calculate duration
                        final_state["duration"] = None

                return final_state

            except Exception as e:
                self.log(f"❌ Workflow execution failed: {e}", "error")
                initial_state["status"] = "failed"
                initial_state["error"] = str(e)
                return initial_state

        return (
            self.execute_with_tracking("run_intelligent_workflow", _workflow_operation)
            or {}
        )

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the LangGraph Orchestrator Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "run": self.run_intelligent_workflow,
            "status": self.get_execution_summary,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None

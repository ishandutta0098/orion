# Orion AI Agent System

## Overview

Orion is an advanced AI agent system inspired by OpenAI's Codex approach to software engineering automation. Like Codex, Orion provides intelligent AI agents that can understand natural language prompts and execute complex software development tasks including code generation, testing, environment management, and GitHub integration.

The system uses **LangGraph** for intelligent workflow orchestration, enabling dynamic routing, parallel processing, and sophisticated error recovery - making it a powerful tool for automating software development workflows.

## Architecture

The Orion system is built around a collection of specialized agents that work together through intelligent orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                 LangGraph Orchestrator                      │
│           (Intelligent Workflow Coordination)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼───┐    ┌────▼───┐    ┌────▼───┐
   │   AI   │    │  Git   │    │GitHub  │
   │Generator│    │ Ops    │    │Integr. │
   └────────┘    └────────┘    └────────┘
        │             │             │
   ┌────▼───┐    ┌────▼───┐         │
   │  Code  │    │  Env   │         │
   │ Tester │    │Manager │         │
   └────────┘    └────────┘         │
        │             │             │
        └─────────────┼─────────────┘
                      │
              ┌───────▼────────┐
              │  Base Agent    │
              │ (Common Core)  │
              └────────────────┘
```

## Core Agents

### 1. LangGraph Orchestrator Agent (`LangGraphOrchestratorAgent`)

**Purpose**: Intelligent workflow orchestration using LangGraph for advanced agent coordination.

**Capabilities**:
- Dynamic workflow routing based on context analysis
- Parallel agent execution for independent tasks  
- Intelligent error recovery and retry mechanisms
- State-based decision making throughout workflows
- Built-in checkpointing and state persistence
- Conditional workflow paths based on repository analysis

**Key Features**:
- **Smart Routing**: Analyzes repository context to determine optimal workflow paths
- **Parallel Processing**: Executes independent tasks simultaneously for improved performance
- **Error Recovery**: Multiple retry strategies with intelligent fallback mechanisms
- **State Management**: Maintains complete workflow state across all phases
- **Checkpointing**: Persistent state storage for workflow resumption

**Usage**:
```python
orchestrator = LangGraphOrchestratorAgent(debug=True)
result = orchestrator.run_workflow(
    repo_url="https://github.com/user/repo",
    user_prompt="Add authentication system",
    enable_testing=True,
    create_pr=True
)
```

---

### 2. AI Generator Agent (`AIGeneratorAgent`)

**Purpose**: AI-powered code generation using LangChain and OpenAI models.

**Capabilities**:
- Generate code based on natural language prompts
- Extract and process AI responses intelligently
- Manage code generation state and history
- Create fallback implementations for edge cases
- Analyze generated code quality

**Key Methods**:
- `generate_code_changes()`: Generate code modifications based on prompts
- `make_code_changes()`: Apply generated changes to repository files
- `extract_python_code_from_text()`: Parse AI responses for code blocks
- `analyze_code_quality()`: Evaluate generated code for best practices

**Configuration**:
- **Model**: Configurable OpenAI model (default: `gpt-4o-mini`)
- **Temperature**: Control randomness in generation (default: `0.1`)
- **Context**: Repository analysis for informed code generation

**Example**:
```python
ai_agent = AIGeneratorAgent(model="gpt-4o-mini", temperature=0.1)
result = ai_agent.generate_code_changes(
    prompt="Create a REST API endpoint for user authentication",
    repo_path="/path/to/repo",
    context={"framework": "FastAPI", "database": "PostgreSQL"}
)
```

---

### 3. Git Operations Agent (`GitOperationsAgent`)

**Purpose**: Comprehensive git repository management and version control operations.

**Capabilities**:
- Clone repositories with branch-specific targeting
- Create and manage branches intelligently
- Handle git state and operation history
- Commit changes with descriptive messages
- Push branches with conflict resolution

**Key Methods**:
- `clone_repository()`: Clone repos with optional branch targeting
- `create_unique_branch()`: Generate unique branch names with collision avoidance
- `commit_changes()`: Commit modifications with automated staging
- `push_branch()`: Push changes with upstream configuration
- `get_repository_status()`: Comprehensive git status analysis

**Smart Features**:
- **Branch Management**: Automatic unique branch name generation
- **Conflict Resolution**: Intelligent handling of existing repositories
- **Status Tracking**: Detailed git state monitoring
- **Error Recovery**: Robust error handling for git operations

---

### 4. GitHub Integration Agent (`GitHubIntegrationAgent`)

**Purpose**: GitHub API integration using Composio for seamless repository operations.

**Capabilities**:
- Authenticate with GitHub using secure token management
- List and filter user repositories
- Create pull requests with rich descriptions
- Format GitHub API responses for human readability
- Manage GitHub-specific workflows

**Key Methods**:
- `check_authentication()`: Verify GitHub API access
- `list_repositories()`: Retrieve user repositories with filtering
- `create_pull_request()`: Create PRs with automated descriptions
- `extract_pr_url()`: Parse PR URLs from API responses
- `get_authentication_status()`: Detailed auth status reporting

**Integration Features**:
- **Composio Integration**: Leverages Composio for robust GitHub API access
- **Token Management**: Secure handling of authentication tokens
- **Rich Formatting**: Human-readable output formatting
- **Error Handling**: Comprehensive API error management

---

### 5. Code Tester Agent (`CodeTesterAgent`)

**Purpose**: Comprehensive code testing and validation with intelligent error handling.

**Capabilities**:
- Test generated code in isolated environments
- Create intelligent test wrappers for validation
- Syntax validation and error detection
- Generate detailed test reports
- Mock external dependencies automatically

**Key Methods**:
- `test_generated_code()`: Execute comprehensive code testing
- `_check_syntax()`: Validate Python syntax before execution
- `_create_and_run_test_wrapper()`: Generate and execute test environments
- `get_test_results()`: Retrieve detailed testing outcomes
- `get_test_summary()`: Generate testing summary reports

**Testing Features**:
- **Isolated Execution**: Safe code execution in virtual environments
- **Smart Mocking**: Automatic mocking of user inputs and external dependencies
- **Comprehensive Reporting**: Detailed test results with error analysis
- **Fallback Strategies**: Multiple testing approaches for different code types

---

### 6. Environment Manager Agent (`EnvironmentManagerAgent`)

**Purpose**: Python environment and dependency management with cross-platform support.

**Capabilities**:
- Create and manage virtual environments
- Install dependencies with version management
- Generate requirements files automatically
- Cross-platform environment handling
- Environment cleanup and maintenance

**Key Methods**:
- `create_virtual_environment()`: Set up isolated Python environments
- `install_dependencies()`: Smart dependency installation
- `create_requirements_file()`: Generate requirements.txt files
- `get_environment_info()`: Comprehensive environment analysis
- `cleanup_environment()`: Safe environment cleanup

**Management Features**:
- **Cross-Platform**: Windows, macOS, and Linux support
- **Version Management**: Intelligent dependency version handling
- **Resource Tracking**: Monitor environment resource usage
- **Cleanup Automation**: Automatic environment maintenance

---

## Base Agent Architecture

All agents inherit from the `BaseAgent` class, which provides:

### Core Functionality
- **Logging System**: Structured logging with agent-specific formatting
- **State Management**: Persistent state tracking across operations
- **Execution Tracking**: Detailed operation history and performance metrics
- **Error Handling**: Standardized error management and recovery
- **Debug Support**: Comprehensive debugging capabilities

### Common Methods
- `log()`: Structured logging with multiple levels
- `update_state()` / `get_state()`: State management
- `record_execution()`: Track operation performance
- `execute_with_tracking()`: Wrapped execution with metrics
- `get_execution_summary()`: Performance and operation summaries

## Workflow Orchestration

The LangGraph orchestrator provides sophisticated workflow management:

### Workflow Phases
1. **Repository Analysis**: Intelligent codebase analysis and context extraction
2. **Repository Setup**: Git operations and branch management
3. **Code Generation**: AI-powered code creation based on analysis
4. **Environment Setup**: Virtual environment and dependency management
5. **Testing**: Comprehensive code validation and testing
6. **Integration**: GitHub PR creation and workflow completion

### Advanced Features
- **Dynamic Routing**: Context-aware workflow path selection
- **Parallel Execution**: Concurrent processing of independent tasks
- **Error Recovery**: Multi-level error handling with intelligent retry
- **State Persistence**: Workflow state preservation across interruptions
- **Conditional Logic**: Smart decision making based on repository characteristics

## Usage Examples

### Basic Workflow Execution
```python
from src.workflow import run_intelligent_workflow

result = run_intelligent_workflow(
    repo_url="https://github.com/user/repo",
    user_prompt="Add user authentication with JWT tokens",
    workdir="./workspace",
    enable_testing=True,
    create_pr=True,
    debug=True
)
```

### Individual Agent Usage
```python
from src.agents import AIGeneratorAgent, CodeTesterAgent

# Generate code
ai_agent = AIGeneratorAgent()
code = ai_agent.generate_code_changes(
    prompt="Create a FastAPI endpoint for user login",
    repo_path="./repo"
)

# Test the generated code
test_agent = CodeTesterAgent()
test_results = test_agent.test_generated_code(
    repo_path="./repo",
    venv_python="./repo/.venv/bin/python",
    created_files=["app/auth.py"]
)
```

### Advanced Orchestration
```python
from src.agents import LangGraphOrchestratorAgent

orchestrator = LangGraphOrchestratorAgent(debug=True)
result = orchestrator.run_workflow(
    repo_url="https://github.com/user/complex-project",
    user_prompt="Refactor authentication system to use OAuth2",
    target_branch="feature/oauth2-migration",
    enable_testing=True,
    strict_testing=True,
    create_venv=True,
    commit_changes=True,
    create_pr=True
)
```

## Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# GitHub Integration (via Composio)
COMPOSIO_API_KEY=your_composio_api_key

# Optional: Custom model configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
```

### Agent Configuration
Each agent supports debug mode and custom configuration:
```python
# Enable debug mode for detailed logging
agent = AIGeneratorAgent(debug=True)

# Custom model configuration
ai_agent = AIGeneratorAgent(
    model="gpt-4o",
    temperature=0.2,
    debug=True
)
```

## Integration with External Tools

### Composio Integration
The GitHub agent leverages Composio for robust GitHub API integration:
- Secure authentication management
- Rich API response formatting
- Error handling and retry logic
- Rate limiting and quota management

### LangChain Integration
The AI generator uses LangChain for:
- Structured prompt templates
- Output parsing and validation
- Chain-of-thought reasoning
- Context-aware generation

### LangGraph Orchestration
Advanced workflow management through:
- State-based graph execution
- Conditional workflow routing
- Parallel task execution
- Checkpointing and recovery

## Error Handling and Recovery

The system implements multi-level error handling:

### Agent-Level Recovery
- Individual agent error handling
- Automatic retry mechanisms
- Fallback strategies for common failures
- State preservation during errors

### Orchestrator-Level Recovery
- Workflow-level error detection
- Intelligent retry with backoff
- Alternative workflow paths
- Graceful degradation strategies

### System-Level Monitoring
- Comprehensive logging and metrics
- Performance tracking and optimization
- Resource usage monitoring
- Error pattern analysis

## Performance and Scalability

### Optimization Features
- **Parallel Processing**: Independent tasks execute simultaneously
- **Intelligent Caching**: State and result caching for improved performance
- **Resource Management**: Efficient memory and CPU usage
- **Batch Operations**: Grouped operations for better throughput

### Monitoring and Metrics
- Execution time tracking
- Resource usage monitoring  
- Success/failure rate analysis
- Performance trend analysis

## Future Enhancements

The Orion system is designed for extensibility:

### Planned Features
- Additional AI model support (Anthropic Claude, Google Gemini)
- Extended programming language support
- Advanced testing strategies
- Enhanced error recovery mechanisms
- Integration with additional development tools

### Architecture Extensions
- Plugin system for custom agents
- Workflow template library
- Advanced analytics and reporting
- Cloud deployment capabilities

---

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run Basic Workflow**:
   ```bash
   python main.py --repo https://github.com/user/repo --prompt "Add user authentication"
   ```

4. **Enable Debug Mode**:
   ```bash
   python main.py --repo https://github.com/user/repo --prompt "Your task" --debug
   ```

For more detailed usage instructions, see the main README.md file.

---

*Orion AI Agent System - Bringing the power of AI-driven software engineering to your development workflow.* 
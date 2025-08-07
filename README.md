# 🚀 Orion AI Agent

A smart multi-agent system powered by **LangGraph** that turns prompts into GitHub PRs with intelligent workflow orchestration, parallel processing, and advanced error recovery.

## ✨ Key Features

- 🧠 **Intelligent Workflow Routing**: Dynamic decision-making based on repository analysis
- ⚡ **Parallel Agent Execution**: Multiple agents working simultaneously for better performance
- 🔄 **Smart Error Recovery**: Multiple retry strategies and alternative workflow paths
- 📊 **Advanced State Management**: Sophisticated state tracking with built-in persistence
- 🎯 **Context-Aware Decisions**: Adaptive workflow based on task complexity and requirements

## 🚀 Quick Start

### Installation

```bash
git clone <repository-url>
cd orion
pip install -r requirements.txt
```

### Setup Authentication

```bash
python main.py --setup-auth
```

### Basic Usage

```bash
# Basic code generation
python main.py --prompt "Add logging functionality to the project"

# With commit and PR creation
python main.py --prompt "Build REST API with comprehensive tests" --commit --create-pr

# Enable debug mode for detailed workflow information
python main.py --prompt "Refactor database layer" --debug

# List available repositories
python main.py --list-repos

# Discord bot integration
python main.py --discord-bot

# Explain repository structure with an OpenAI summary (no changes made)
python main.py --prompt "Explain" --repo-url <repository-url> --branch <branch>
```

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `--prompt "text"` | Instruction for the AI agent |
| `--repo-url URL` | GitHub repository URL to work with |
| `--branch BRANCH` | Name of the branch to work on |
| `--commit` | Commit the generated changes |
| `--create-pr` | Create a pull request (auto-enables --commit) |
| `--debug` | Enable detailed LangGraph workflow information |
| `--strict-testing` | Abort commit if tests fail |
| `--no-testing` | Disable code testing |
| `--no-venv` | Disable virtual environment creation |
| `--list-repos` | List repositories from your GitHub account |
| `--setup-auth` | Run authentication setup |
| `--discord-bot` | Start Discord bot for interactive prompts |
| `--prompt "Explain"` | Use OpenAI to describe the repository and ignore commit/PR flags |

## 🎯 LangGraph Architecture

Orion uses **LangGraph** for production-grade workflow orchestration:

- **Intelligent Routing**: Analyzes repository structure to choose optimal workflow paths
- **Parallel Processing**: Runs independent tasks simultaneously (30-50% faster execution)
- **Error Recovery**: Smart retry strategies with context-aware fallbacks
- **State Persistence**: Resume interrupted workflows from any checkpoint
- **Adaptive Workflows**: Dynamic execution based on task complexity

### Workflow Phases

1. **Repository Analysis** → Intelligent context gathering
2. **Code Generation** → AI-powered implementation
3. **Environment Setup** → Automated dependency management
4. **Testing & Validation** → Quality assurance with smart recovery
5. **Git Operations** → Commit and PR creation

# Contributing to Plugah

Thank you for your interest in contributing to Plugah! We welcome contributions from the community and are grateful for any help you can provide.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your changes
4. **Make your changes** and commit them
5. **Push to your fork** and submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ (for web interface)
- uv (Python package manager)
- Git

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/plugah.git
cd plugah

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
uv pip install -e ".[dev,demo]"

# Install pre-commit hooks (optional but recommended)
pre-commit install

# For web development
cd web/frontend
npm install
cd ../..
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=plugah --cov-report=term-missing

# Run specific test file
pytest tests/test_planner.py

# Run linting
ruff check plugah

# Run type checking
mypy plugah

# Format code
ruff format plugah
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, please use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml) and include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Feature suggestions are welcome! Please use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml) and include:

- A clear problem statement
- Your proposed solution
- Alternatives you've considered
- Use cases and expected impact

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Simple issues good for beginners
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

### Development Workflow

1. **Find or create an issue** for what you want to work on
2. **Comment on the issue** to let others know you're working on it
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following our coding standards
5. **Write or update tests** for your changes
6. **Update documentation** if needed
7. **Run tests and linting** to ensure everything passes
8. **Commit your changes** using semantic commit messages:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug in executor"
   git commit -m "docs: update README"
   ```

## Pull Request Process

1. **Update the CHANGELOG.md** with your changes (if significant)
2. **Ensure all tests pass** and coverage doesn't decrease significantly
3. **Update documentation** including docstrings and README if needed
4. **Fill out the PR template** completely
5. **Link the related issue** in your PR description
6. **Request review** from maintainers
7. **Address review feedback** promptly
8. **Squash commits** if requested before merging

### PR Title Format

Use semantic prefixes:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or corrections
- `chore:` Maintenance tasks

## Coding Standards

### Python Code Style

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use ruff for linting and formatting
- Docstrings for all public functions (Google style)

Example:
```python
def calculate_budget(
    total: float,
    policy: BudgetPolicy = BudgetPolicy.BALANCED
) -> BudgetModel:
    """
    Calculate budget allocation based on policy.
    
    Args:
        total: Total budget in USD
        policy: Budget policy to apply
        
    Returns:
        BudgetModel with calculated caps
    """
    # Implementation
```

### TypeScript/React Code Style

- Use TypeScript for all new code
- Functional components with hooks
- Tailwind CSS for styling
- ESLint and Prettier for formatting

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
```bash
feat(executor): add checkpoint support for long-running tasks
fix(budget): correct soft cap calculation in CFO
docs(api): add examples for BoardRoom methods
```

## Testing

- Write tests for all new features
- Maintain or improve test coverage
- Use pytest for Python tests
- Mock external dependencies
- Test edge cases and error conditions

### Test Structure

```python
def test_feature_normal_case():
    """Test normal operation of feature"""
    # Arrange
    # Act
    # Assert

def test_feature_edge_case():
    """Test edge cases and boundaries"""
    pass

def test_feature_error_handling():
    """Test error conditions"""
    with pytest.raises(ExpectedError):
        # Code that should raise
```

## Documentation

- Update docstrings for any modified functions
- Update README.md for new features
- Update CLAUDE.md for development workflow changes
- Add examples for complex features
- Keep documentation in sync with code

## Community

- **Discussions**: [GitHub Discussions](https://github.com/cheesejaguar/plugah/discussions)
- **Issues**: [GitHub Issues](https://github.com/cheesejaguar/plugah/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/cheesejaguar/plugah/pulls)

## Recognition

Contributors will be recognized in:
- The CHANGELOG.md file
- GitHub's contributor graph
- Special mentions for significant contributions

## Questions?

Feel free to:
- Open a [discussion](https://github.com/cheesejaguar/plugah/discussions)
- Comment on relevant issues
- Reach out to maintainers

Thank you for contributing to Plugah! 🎉
# Contributing to Guestbook API

Thank you for your interest in contributing to the Guestbook API project! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)

---

## Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please be respectful and constructive in all interactions.

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of Flask and REST APIs
- Familiarity with pytest for testing

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/TestApiSkills.git
   cd TestApiSkills
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/TestApiSkills.git
   ```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
nano .env  # or use your preferred editor
```

### 4. Initialize Database

```bash
cd src
python app.py  # Database will be created automatically
```

### 5. Verify Setup

```bash
# Run tests to ensure everything works
pytest tests/ -v

# Start the server
cd src && python app.py
```

---

## Making Changes

### 1. Create a Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - for new features
- `fix/` - for bug fixes
- `docs/` - for documentation changes
- `test/` - for test improvements
- `refactor/` - for code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### 3. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add rate limiting to webhook endpoints"
```

Good commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

Example:
```
feat: Add rate limiting to webhook endpoints

Implement rate limiting for webhook registration and dispatch
endpoints to prevent abuse. Limits set to 10 requests per minute
for registration and 50 per minute for dispatch.

Closes #123
```

---

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rate_limiting.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test class
pytest tests/test_rate_limiting.py::TestRateLimitingAuth -v
```

### Write Tests

- Add tests for all new features
- Ensure existing tests still pass
- Aim for high test coverage
- Test edge cases and error conditions

Test file naming:
- `test_*.py` for pytest files
- Place in `tests/` directory
- Mirror the source structure

Example test structure:
```python
import pytest

class TestYourFeature:
    """Test suite for your feature"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_edge_case(self):
        """Test edge case"""
        pass
    
    def test_error_handling(self):
        """Test error handling"""
        pass
```

---

## Submitting Changes

### 1. Update Your Branch

Before submitting, update your branch with the latest changes:

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to GitHub and open a Pull Request
2. Fill in the PR template:
   - Clear title describing the change
   - Description of what was changed and why
   - Reference any related issues
   - Screenshots if applicable
   - Checklist of completed items

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Related Issues
Closes #(issue number)
```

---

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Keep functions small and focused
- Maximum line length: 88 characters (Black formatter)
- Use type hints where appropriate

### Code Formatting

We use Black for code formatting:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

We use flake8 for linting:

```bash
# Run linter
flake8 src/ tests/

# With specific config
flake8 --max-line-length=88 src/
```

### Import Organization

Use isort for import sorting:

```bash
# Sort imports
isort src/ tests/

# Check sorting
isort --check-only src/ tests/
```

### Pre-commit Hooks

Pre-commit hooks automatically run formatting and linting:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Documentation

### Code Documentation

- Add docstrings to all functions and classes
- Use Google-style docstrings
- Document parameters, return values, and exceptions

Example:
```python
def create_entry(name: str, email: str, comment: str) -> dict:
    """
    Create a new guestbook entry.
    
    Args:
        name: The name of the person creating the entry
        email: Email address of the person
        comment: The comment text
        
    Returns:
        Dictionary containing the created entry data
        
    Raises:
        ValueError: If name or email is empty
        DatabaseError: If database operation fails
        
    Example:
        >>> entry = create_entry("John", "john@example.com", "Hello!")
        >>> print(entry['name'])
        'John'
    """
    pass
```

### API Documentation

- Update Swagger documentation for API changes
- Add examples to endpoint docstrings
- Document request/response schemas

### README and Guides

- Update README.md if adding major features
- Add guides in `docs/` for new features
- Keep documentation up to date with code changes

---

## Specific Guidelines

### Rate Limiting Changes

If modifying rate limiting:
1. Update limits in `src/rate_limiter.py`
2. Update tests in `tests/test_rate_limiting.py`
3. Update documentation in `docs/RATE_LIMITING_GUIDE.md`
4. Run rate limiting tests: `pytest tests/test_rate_limiting.py -v`

### Adding New Endpoints

1. Add route to appropriate blueprint in `src/blueprints/v1/`
2. Add Swagger documentation with docstring
3. Add tests in `tests/`
4. Apply rate limiting in `src/app.py`
5. Update API documentation

### Security Changes

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Review security implications
- Add tests for security features
- Document security considerations

---

## Questions?

If you have questions:

1. Check existing documentation
2. Search existing issues
3. Open a new issue with the `question` label
4. Join our discussion forum (if available)

---

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- Release notes

Thank you for contributing! 🙏

---

*Last updated: March 2024*

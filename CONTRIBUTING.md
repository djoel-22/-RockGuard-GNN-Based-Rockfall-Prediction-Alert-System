# Contributing to RockGuard

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `config.example.env` to `config.env` and fill in your credentials
4. Run the app: `python main.py`

## Code Style

- Follow [PEP 8](https://pep8.org/)
- Use descriptive variable names — this is safety-critical software
- Add docstrings to all public classes and methods
- Keep each module focused on a single responsibility

## Submitting Changes

1. Create a branch: `git checkout -b feature/your-feature-name`
2. Make your changes and commit with clear messages
3. Push and open a Pull Request against `main`
4. Describe what changed and why in the PR description

## Reporting Bugs

Open an issue with:
- Your OS and Python version
- Steps to reproduce the bug
- Expected vs. actual behavior
- Relevant error messages or screenshots

## Areas That Need Help

- Unit tests (currently none — this is a priority!)
- IoT sensor ingestion (MQTT)
- GNN model retraining pipeline
- PDF report export
- Multi-platform testing (macOS, Linux)

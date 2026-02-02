# Contributing to SwarmGrid

Thanks for taking the time to contribute. This guide explains how to report issues, request features, and submit code changes.

## Code of Conduct

This project is governed by the Code of Conduct. By participating, you agree to uphold it.
See `CODE_OF_CONDUCT.md`.

## Ways to Contribute

- Report bugs
- Suggest features
- Improve documentation
- Submit pull requests

### Reporting Bugs

Before creating a bug report, search existing issues to avoid duplicates. A good report includes:

- A clear, descriptive title
- Steps to reproduce the problem
- Expected behavior vs actual behavior
- Logs, config snippets, or screenshots when relevant
- Environment details (OS, Docker version, component)

### Suggesting Features

Feature requests are tracked as GitHub issues. Please include:

- The problem you are trying to solve
- The proposed solution
- Alternatives you considered
- Any relevant constraints

## Development Workflow

1. Fork the repository
2. Create a branch from `main`
3. Make your changes
4. Run tests
5. Update documentation if needed
6. Open a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- .NET 8 SDK
- Node.js 20+
- Docker and Docker Compose

### Quick Start

For a full local stack:

```bash
docker-compose up -d
```

For component-specific setup, see:
- `edge-agent/README.md`
- `core-backend/README.md`
- `dashboard/README.md`

## Coding Standards

### Python (Edge Agent)

- Follow PEP 8
- Use type hints where practical
- Add docstrings for public functions

### C# (Core Backend)

- Follow Microsoft C# coding conventions
- Keep methods small and focused
- Add XML docs for public APIs

### TypeScript/React (Dashboard)

- Prefer strict typing (avoid `any`)
- Use PascalCase for component files
- Use functional components and hooks

## Testing

- Edge Agent: `pytest`
- Core Backend: `dotnet test`
- Dashboard: `npm test` (if configured)

## Commit Messages

We follow Conventional Commits:

```
<type>(<scope>): <description>
```

Types:
- feat
- fix
- docs
- style
- refactor
- test
- chore

Examples:
```
feat(edge-agent): add flow entropy smoothing
fix(dashboard): correct heatmap color scale
```

## Versioning

Releases will follow SemVer once versioned releases begin. Until then, expect breaking changes on `main`.

## Need Help?

- Review `docs/`
- Open a GitHub discussion
- File an issue

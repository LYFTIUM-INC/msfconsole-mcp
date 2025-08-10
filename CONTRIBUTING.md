# Contributing

## Setup

- Python 3.10+
- Install dependencies:
  - `make setup`
- Install pre-commit (optional):
  - `pip install pre-commit && make pre-commit`

## Commands

- Lint: `make lint`
- Format: `make format`
- Test: `make test`
- Coverage: `make cov`

## Branching and PRs

- Use feature branches (`feature/...`)
- Write tests for new code
- Keep coverage at 100% for changed modules
- Update `README.md` when changing public APIs
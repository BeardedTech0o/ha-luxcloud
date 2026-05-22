# Contributing to LuxCloud

Thank you for taking the time to contribute! This guide explains how to get set up and what to expect when submitting changes.

---

## Table of contents

- [Reporting bugs](#reporting-bugs)
- [Requesting features](#requesting-features)
- [Development setup](#development-setup)
- [Running tests](#running-tests)
- [Submitting a pull request](#submitting-a-pull-request)
- [Code style](#code-style)

---

## Reporting bugs

Before opening a bug report, please:

1. Check the [troubleshooting section](README.md#troubleshooting) in the README
2. Search [existing issues](https://github.com/BeardedTech0o/ha-luxcloud/issues) to avoid duplicates
3. Collect your HA logs: **Settings → System → Logs** — filter by `luxcloud`

Then open a [Bug Report](https://github.com/BeardedTech0o/ha-luxcloud/issues/new?template=bug_report.yml) and fill in the template.

---

## Requesting features

Open a [Feature Request](https://github.com/BeardedTech0o/ha-luxcloud/issues/new?template=feature_request.yml) describing the use case and what you'd like to see.

---

## Development setup

### Prerequisites

- Python 3.12+
- A LuxPower inverter and cloud account (or willingness to mock the API)

### Getting started

```bash
# Clone the repo
git clone https://github.com/BeardedTech0o/ha-luxcloud.git
cd ha-luxcloud

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install test dependencies
pip install -r requirements_test.txt
```

### Folder structure

```
custom_components/luxcloud/   ← integration source
tests/                        ← pytest test suite
.github/                      ← CI workflows and issue templates
```

---

## Running tests

```bash
pytest tests/ -v
```

To run with coverage:

```bash
pytest tests/ --cov=custom_components/luxcloud --cov-report=term-missing
```

### Validators

```bash
# hassfest — checks manifest, strings, and HA conventions
docker run --rm -v "$(pwd)":/github/workspace homeassistant/hassfest

# HACS — checks repo structure for HACS compatibility
docker run --rm -v "$(pwd)":/github/workspace ghcr.io/hacs/action
```

---

## Submitting a pull request

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Make your changes** — keep commits focused and atomic

3. **Add or update tests** for any changed behaviour

4. **Run the full test suite** and both validators before pushing

5. **Update [CHANGELOG.md](CHANGELOG.md)** under `[Unreleased]`

6. **Open a PR** against the `main` branch and fill in the pull request template

PRs that break existing tests, fail the validators, or lack a changelog entry will not be merged until those are resolved.

---

## Code style

- Follow existing patterns in the codebase
- Use `from __future__ import annotations` in all Python files
- Keep functions small and focused
- Add a comment only when the **why** is non-obvious — avoid restating what the code already says
- Entity descriptions should include `translation_key` so names are translatable
- All new entities need a corresponding entry in `strings.json`, `translations/en.json`, and `icons.json`

---

## Questions?

Open a [Discussion](https://github.com/BeardedTech0o/ha-luxcloud/discussions) for anything that doesn't fit a bug report or feature request.

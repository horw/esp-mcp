---
alwaysApply: false
name: run-esp-idf-pytest
description: The skill to run a pytest. Always follow this rule when you need to execute a pytest written for ESP-IDF applications.
---

# How to Run ESP-IDF pytest with run_pytest

This document describes how to use the `run_pytest` tool to run pytest tests for ESP-IDF projects.

## Typical Usage Scenarios

### 1. Run All Tests for a Specific Target

```python
run_pytest(
    project_path="/path/to/project",
    pytest_args="--target=esp32"
)
```

**Note**: The application needs to be built into separate `build_{target}_{config}` directories.

### 2. Run Tests for a Specific Target and Configuration

```python
run_pytest(
    project_path="/path/to/project",
    pytest_args="--target=esp32 --sdkconfig=release"
)
```

**Note**:
- `--sdkconfig` directly specifies the configuration name (e.g., "release" maps to `sdkconfig.ci.release`)

## Parameter Description

Refer to the MCP tool documentation for detailed parameter information.

## Important Notes

1. **Build Directory**: Ensure the test application is correctly built into the corresponding directory
    - When running tests for a single config, the `build_{target}_{config}` directory takes precedence over `build`. If tests are compiled into the `build` directory, ensure the `build_{target}_{config}` directory does not exist.
    - When running tests for multiple configs of the same target, provide different `build_{target}_{config}` directories.

2. **ESP-IDF Environment**: The tool automatically loads the ESP-IDF environment, no manual export required. Install of ESP-IDF may be required for once after switched to a new version.

3. **Single Target Limitation**: Only one target chip can be specified per test run

4. **Single Configuration Limitation**: Only one sdkconfig configuration can be specified per test run, or it can be omitted to run all tests for that target chip.


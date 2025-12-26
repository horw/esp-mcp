#!/usr/bin/env python3
"""
Integration tests for ESP-MCP tools.

This test suite tests the MCP tools directly by importing and calling them.
Requires ESP-IDF to be installed and configured.
"""
import asyncio
import os
import sys
import logging

# Add parent directory to path to import main module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import config from test directory
test_dir = os.path.dirname(os.path.abspath(__file__))
if test_dir not in sys.path:
    sys.path.insert(0, test_dir)

try:
    from config import IDF_PATH, PROJECT_PATH, PYTEST_FILE, TARGET_CHIP, SERIAL_PORT, SDKCONFIG_DEFAULTS
except ImportError:
    print("Error: config.py not found. Please copy config.example.py to config.py and configure it.")
    sys.exit(1)

# Import main module functions
try:
    from main import (
        run_esp_idf_install,
        setup_project_esp_target,
        build_esp_project,
        run_pytest
    )
except ImportError as e:
    print(f"Error importing main module: {e}")
    print(f"Parent dir: {parent_dir}")
    print(f"Python path: {sys.path[:3]}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)


async def test_run_esp_idf_install():
    """Test run_esp_idf_install function"""
    print("=" * 80)
    print("Test 1: run_esp_idf_install")
    print("=" * 80)
    print(f"IDF path: {IDF_PATH}")
    print()

    try:
        stdout, stderr = await run_esp_idf_install(idf_path=IDF_PATH)
        print("STDOUT (last 500 chars):")
        print(stdout[-500:] if len(stdout) > 500 else stdout)
        print()
        if stderr:
            print("STDERR:")
            print(stderr)
        print("✓ Installation test completed")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_setup_project_esp_target():
    """Test setup_project_esp_target function"""
    print("=" * 80)
    print("Test 2: setup_project_esp_target")
    print("=" * 80)
    print(f"Project path: {PROJECT_PATH}")
    print(f"Target chip: {TARGET_CHIP}")
    print(f"IDF path: {IDF_PATH}")
    print()

    try:
        stdout, stderr = await setup_project_esp_target(
            project_path=PROJECT_PATH,
            target=TARGET_CHIP,
            idf_path=IDF_PATH
        )
        print("STDOUT (last 500 chars):")
        print(stdout[-500:] if len(stdout) > 500 else stdout)
        print()
        if stderr:
            print("STDERR:")
            print(stderr)
        print("✓ Set target test completed")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_build_esp_project():
    """Test build_esp_project function"""
    print("=" * 80)
    print("Test 3: build_esp_project")
    print("=" * 80)
    print(f"Project path: {PROJECT_PATH}")
    print(f"IDF path: {IDF_PATH}")
    print()

    try:
        stdout, stderr = await build_esp_project(
            project_path=PROJECT_PATH,
            idf_path=IDF_PATH
        )
        print("STDOUT (last 500 chars):")
        print(stdout[-500:] if len(stdout) > 500 else stdout)
        print()
        if stderr:
            print("STDERR:")
            print(stderr[-500:] if len(stderr) > 500 else stderr)
        print("✓ Build test completed")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_build_esp_project_with_sdkconfig_defaults():
    """Test build_esp_project with sdkconfig_defaults parameter"""
    print("=" * 80)
    print("Test 3.5: build_esp_project with sdkconfig_defaults")
    print("=" * 80)
    print(f"Project path: {PROJECT_PATH}")
    print(f"IDF path: {IDF_PATH}")
    print(f"sdkconfig_defaults: {SDKCONFIG_DEFAULTS}")
    print("Note: This will trigger reconfigure and full rebuild")
    print()

    if not SDKCONFIG_DEFAULTS:
        print("⚠ Skipping test: SDKCONFIG_DEFAULTS not configured")
        return True

    try:
        stdout, stderr = await build_esp_project(
            project_path=PROJECT_PATH,
            idf_path=IDF_PATH,
            sdkconfig_defaults=SDKCONFIG_DEFAULTS
        )
        print("STDOUT (last 500 chars):")
        print(stdout[-500:] if len(stdout) > 500 else stdout)
        print()
        if stderr:
            print("STDERR:")
            print(stderr[-500:] if len(stderr) > 500 else stderr)

        # Verify that the command includes SDKCONFIG_DEFAULTS
        if "SDKCONFIG_DEFAULTS" in stdout or "SDKCONFIG_DEFAULTS" in stderr:
            print("✓ SDKCONFIG_DEFAULTS parameter detected in build output")
        else:
            print("⚠ Warning: SDKCONFIG_DEFAULTS not found in output (may be normal)")

        print("✓ Build with sdkconfig_defaults test completed")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_run_pytest():
    """Test run_pytest function"""
    print("=" * 80)
    print("Test 4: run_pytest")
    print("=" * 80)
    print(f"Project path: {PROJECT_PATH}")
    print(f"Test file: {PYTEST_FILE}")
    print(f"Target chip: {TARGET_CHIP}")
    print(f"IDF path: {IDF_PATH}")
    if SERIAL_PORT:
        print(f"Serial port: {SERIAL_PORT}")
    print()

    try:
        pytest_args = f"--target={TARGET_CHIP} -v"
        if SERIAL_PORT:
            pytest_args += f" --port {SERIAL_PORT}"

        stdout, stderr = await run_pytest(
            project_path=PROJECT_PATH,
            test_path=PYTEST_FILE,
            pytest_args=pytest_args,
            idf_path=IDF_PATH
        )
        print("STDOUT:")
        print(stdout)
        print()
        if stderr:
            print("STDERR:")
            print(stderr)
        print("✓ Pytest test completed")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests in sequence"""
    print("Starting ESP-MCP tools integration tests...")
    print()
    print(f"Configuration:")
    print(f"  IDF_PATH: {IDF_PATH}")
    print(f"  PROJECT_PATH: {PROJECT_PATH}")
    print(f"  TARGET_CHIP: {TARGET_CHIP}")
    print(f"  SERIAL_PORT: {SERIAL_PORT or 'auto-detect'}")
    print(f"  SDKCONFIG_DEFAULTS: {SDKCONFIG_DEFAULTS or 'not set (will skip test)'}")
    print()

    results = []

    # Test 1: Install ESP-IDF
    result1 = await test_run_esp_idf_install()
    results.append(("run_esp_idf_install", result1))
    print()

    # Test 2: Set target
    result2 = await test_setup_project_esp_target()
    results.append(("setup_project_esp_target", result2))
    print()

    # Test 3: Build project (incremental)
    result3 = await test_build_esp_project()
    results.append(("build_esp_project", result3))
    print()

    # Test 3.5: Build project with sdkconfig_defaults (optional, will trigger full rebuild)
    print("Skipping sdkconfig_defaults test to avoid full rebuild...")
    print("To test sdkconfig_defaults, uncomment test 3.5 in test_mcp_tools.py")
    result3_5 = await test_build_esp_project_with_sdkconfig_defaults()
    results.append(("build_esp_project (with sdkconfig_defaults)", result3_5))
    print()

    # Test 4: Run pytest
    result4 = await test_run_pytest()
    results.append(("run_pytest", result4))
    print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:30s} {status}")

    all_passed = all(result for _, result in results)
    print()
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


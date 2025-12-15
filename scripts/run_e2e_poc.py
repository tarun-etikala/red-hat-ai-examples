#!/usr/bin/env python3
"""Run E2E POC tests on RHOAI cluster.

This script helps run the POC tests with proper setup and verification.

Usage:
    # Interactive mode (will prompt for credentials if not set)
    python scripts/run_e2e_poc.py

    # With credentials already set
    export RHOAI_API_URL="https://api.your-cluster.example.com:6443"
    export RHOAI_TOKEN="your-token"
    python scripts/run_e2e_poc.py --run-tests

    # Quick verification only
    python scripts/run_e2e_poc.py --verify-only

    # Run specific strategy tests
    python scripts/run_e2e_poc.py --strategy local
    python scripts/run_e2e_poc.py --strategy kubernetes
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


def check_credentials() -> bool:
    """Check if RHOAI credentials are configured."""
    api_url = os.environ.get("RHOAI_API_URL")
    token = os.environ.get("RHOAI_TOKEN")

    if not api_url or not token:
        print("❌ RHOAI credentials not configured.")
        print("\nPlease set the following environment variables:")
        print("  export RHOAI_API_URL='https://api.your-cluster.example.com:6443'")
        print("  export RHOAI_TOKEN='your-token-here'")
        print("\nYou can get these values with:")
        print("  RHOAI_API_URL: oc whoami --show-server")
        print("  RHOAI_TOKEN: oc whoami -t")
        return False

    print(f"✓ API URL: {api_url}")
    print(f"✓ Token: {token[:20]}...")
    return True


def verify_connection() -> bool:
    """Verify connection to the RHOAI cluster."""
    print("\n" + "=" * 60)
    print("Verifying RHOAI cluster connection...")
    print("=" * 60)

    try:
        # Add project root to path
        repo_root = get_repo_root()
        sys.path.insert(0, str(repo_root))

        from infrastructure.rhoai import ClusterConfig, RHOAIClient

        config = ClusterConfig(
            api_url=os.environ.get("RHOAI_API_URL", ""),
            token=os.environ.get("RHOAI_TOKEN", ""),
            namespace=os.environ.get("RHOAI_NAMESPACE", "default"),
            verify_ssl=os.environ.get("RHOAI_VERIFY_SSL", "false").lower() == "true",
        )

        client = RHOAIClient(config)
        client.connect()

        info = client.get_cluster_info()
        print("\n✓ Connection successful!")
        print(f"  Kubernetes: {info['kubernetes_version']}")
        print(f"  Platform: {info.get('platform', 'N/A')}")

        namespaces = client.list_namespaces()
        print(f"  Accessible namespaces: {len(namespaces)}")

        client.close()
        return True

    except ImportError as e:
        print(f"\n❌ Missing dependencies: {e}")
        print("Install with: pip install kubernetes openshift-client")
        return False
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False


def run_pytest(test_path: str, extra_args: list = None) -> int:
    """Run pytest with the specified test path."""
    repo_root = get_repo_root()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / test_path),
        "-v",
        "-s",
        "--tb=short",
    ]

    if extra_args:
        cmd.extend(extra_args)

    print("\n" + "=" * 60)
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60 + "\n")

    return subprocess.run(cmd, cwd=repo_root).returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run E2E POC tests on RHOAI cluster",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check credentials and verify connection
    python scripts/run_e2e_poc.py --verify-only

    # Run all POC tests
    python scripts/run_e2e_poc.py --run-tests

    # Run quick verification test
    python scripts/run_e2e_poc.py --quick

    # Run connectivity tests only
    python scripts/run_e2e_poc.py --strategy connectivity

    # Run local strategy tests (no cluster needed)
    python scripts/run_e2e_poc.py --strategy local
        """,
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify connection, don't run tests",
    )

    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run all POC tests",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick verification test only",
    )

    parser.add_argument(
        "--strategy",
        choices=["connectivity", "local", "kubernetes", "all"],
        default="all",
        help="Which strategy tests to run",
    )

    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip connection verification before tests",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("RHOAI E2E POC Test Runner")
    print("=" * 60)

    # Check credentials
    if not check_credentials():
        if args.strategy == "local":
            print("\n⚠ Running local tests without cluster credentials...")
        else:
            sys.exit(1)

    # Verify connection (unless skipped or local-only)
    if args.strategy != "local" and not args.skip_verify:
        if not verify_connection():
            if not args.verify_only:
                print("\n⚠ Connection verification failed.")
                print("You can still run local tests with: --strategy local")
            sys.exit(1)

    if args.verify_only:
        print("\n✓ Verification complete!")
        sys.exit(0)

    # Run tests
    if args.quick:
        return run_pytest("tests/e2e/test_poc_strategies.py::test_poc_quick_verify")

    if args.strategy == "connectivity":
        return run_pytest("tests/e2e/test_poc_strategies.py::TestClusterConnectivity")

    if args.strategy == "local":
        return run_pytest(
            "tests/e2e/test_poc_strategies.py::TestExecutionStrategies",
            extra_args=["-k", "local"],
        )

    if args.strategy == "kubernetes":
        return run_pytest(
            "tests/e2e/test_poc_strategies.py::TestExecutionStrategies",
            extra_args=["-k", "kubernetes", "-m", "e2e"],
        )

    if args.run_tests or args.strategy == "all":
        return run_pytest(
            "tests/e2e/test_poc_strategies.py",
            extra_args=["-m", "e2e or not e2e"],  # Run all tests
        )

    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

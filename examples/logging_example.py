"""
Example demonstrating the logging framework usage.

This script shows how to use the logging framework with:
- Basic logging
- JSON structured logging
- Performance timing
- Correlation tracking
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure import correlation_context, get_logger, timed, timer


def main():
    """Demonstrate logging framework features."""

    print("=" * 70)
    print("Logging Framework Demo")
    print("=" * 70)

    # 1. Basic Logger
    print("\n1. Basic Logger (console output)")
    print("-" * 70)

    logger = get_logger("demo", json_format=False, console=True)  # Human-readable for demo

    logger.debug("Debug message - detailed diagnostics")
    logger.info("Info message - general information")
    logger.warning("Warning message - recoverable issue")
    logger.error("Error message - something failed")

    # 2. Structured Logging
    print("\n2. Structured Logging (with extra fields)")
    print("-" * 70)

    logger.info(
        "Processing file", extra={"file_path": "document.docx", "file_size": 1024, "format": "docx"}
    )

    # 3. Performance Timing - Decorator
    print("\n3. Performance Timing - Decorator")
    print("-" * 70)

    @timed(logger)
    def process_document(doc_name: str) -> int:
        """Simulate document processing."""
        print(f"   Processing {doc_name}...")
        time.sleep(0.1)  # Simulate work
        return 42

    result = process_document("example.docx")
    print(f"   Result: {result}")

    # 4. Performance Timing - Context Manager
    print("\n4. Performance Timing - Context Manager")
    print("-" * 70)

    with timer(logger, "batch_processing"):
        print("   Processing batch of 3 files...")
        for i in range(3):
            time.sleep(0.05)  # Simulate work
            print(f"   - Processed file {i + 1}")

    # 5. Correlation Tracking
    print("\n5. Correlation Tracking")
    print("-" * 70)

    def process_request(request_id: str, file_name: str):
        """Process a request with correlation tracking."""
        with correlation_context(request_id):
            logger.info("Request started", extra={"file": file_name})

            # Simulate processing steps
            time.sleep(0.05)
            logger.info("Extraction complete", extra={"blocks": 25})

            time.sleep(0.05)
            logger.info("Processing complete", extra={"nodes": 30})

            logger.info("Request completed", extra={"success": True})

    process_request("req-001", "document1.docx")

    # 6. JSON Logging to File
    print("\n6. JSON Logging to File")
    print("-" * 70)

    log_file = Path("logs/demo.log")
    log_file.parent.mkdir(exist_ok=True)

    json_logger = get_logger("json_demo", json_format=True, file_path=log_file)

    json_logger.info("Starting extraction", extra={"file": "test.docx"})
    json_logger.info("Extraction complete", extra={"blocks": 10, "duration": 1.23})

    print(f"   Logs written to: {log_file}")
    print("   Log file contents:")

    if log_file.exists():
        with open(log_file, "r") as f:
            for line in f:
                print(f"   {line.rstrip()}")

    # 7. Multi-Sink (Console + File)
    print("\n7. Multi-Sink Logging (Console + File)")
    print("-" * 70)

    multi_logger = get_logger(
        "multi_sink", json_format=False, file_path=Path("logs/multi.log"), console=True
    )

    multi_logger.info("This appears in both console and file")

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nCheck the following files:")
    print(f"  - {log_file}")
    print("  - logs/multi.log")
    print("\nFor more details, see: docs/LOGGING_GUIDE.md")


if __name__ == "__main__":
    main()

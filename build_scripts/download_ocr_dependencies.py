#!/usr/bin/env python3
"""Download Tesseract and Poppler Windows binaries for packaging.

This script downloads the required OCR dependencies for Windows builds:
- Tesseract OCR: Windows portable ZIP version
- Poppler: Windows binaries for PDF processing

The downloaded files are extracted to build_scripts/vendor/ for bundling
with PyInstaller or other packaging tools.
"""

import argparse
import hashlib
import logging
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional

import requests  # type: ignore[import-untyped]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Download URLs and versions
TESSERACT_VERSION = "5.3.3"
TESSERACT_URL = f"https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-{TESSERACT_VERSION}.20231005.zip"

DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_MS = 500
POPPLER_DEFAULT_VERSION = "24.02.0"
POPPLER_GITHUB_API_TEMPLATE = (
    "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/tags/{tag}"
)

# Known SHA256 checksums for OCR dependencies.
# Values can be injected via environment variables in CI/CD:
# - DATA_EXTRACT_TESSERACT_SHA256
# - DATA_EXTRACT_POPPLER_SHA256
CHECKSUMS = {
    "tesseract-5.3.3": os.environ.get("DATA_EXTRACT_TESSERACT_SHA256", "").strip(),
    f"poppler-{POPPLER_DEFAULT_VERSION}": os.environ.get("DATA_EXTRACT_POPPLER_SHA256", "").strip(),
}

# Required files for verification
TESSERACT_REQUIRED_FILES = [
    "tesseract.exe",
    "tessdata/eng.traineddata",
]

POPPLER_REQUIRED_FILES = [
    "Library/bin/pdftoppm.exe",
    "Library/bin/pdfinfo.exe",
]

POPPLER_CHECKSUM_ENV_VAR = "DATA_EXTRACT_POPPLER_SHA256"


def parse_non_negative_int(raw_value: str) -> int:
    """Parse CLI integer values that must be >= 0."""
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected integer value, got: {raw_value}") from exc

    if value < 0:
        raise argparse.ArgumentTypeError(f"Expected value >= 0, got: {raw_value}")
    return value


def normalize_poppler_version(raw_version: str) -> str:
    """Normalize user-supplied Poppler version to MAJOR.MINOR.PATCH format."""
    normalized = raw_version.strip()
    if normalized.startswith("v"):
        normalized = normalized[1:]
    if normalized.endswith("-0"):
        normalized = normalized[:-2]

    parts = normalized.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise argparse.ArgumentTypeError(
            f"Invalid Poppler version '{raw_version}'. Expected format like 24.02.0"
        )
    return normalized


def build_poppler_release_api_url(poppler_version: str) -> str:
    """Build GitHub release API URL for the provided Poppler version."""
    release_tag = f"v{poppler_version}-0"
    return POPPLER_GITHUB_API_TEMPLATE.format(tag=release_tag)


def resolve_poppler_checksum(poppler_version: str) -> str:
    """Resolve expected Poppler checksum from versioned config key or env fallback."""
    checksum_key = f"poppler-{poppler_version}"
    configured_checksum = CHECKSUMS.get(checksum_key, "").strip()
    if configured_checksum:
        return configured_checksum
    return os.environ.get(POPPLER_CHECKSUM_ENV_VAR, "").strip()


def request_with_retry(
    url: str,
    *,
    timeout: int,
    stream: bool = False,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_ms: int = DEFAULT_BACKOFF_MS,
) -> Optional[requests.Response]:
    """Perform HTTP GET with retry and exponential backoff."""
    total_attempts = max_retries + 1

    for attempt in range(1, total_attempts + 1):
        try:
            response = requests.get(url, stream=stream, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            if attempt == total_attempts:
                logger.error(f"Request failed after {total_attempts} attempt(s): {url} ({exc})")
                return None

            backoff_seconds = (backoff_ms / 1000.0) * (2 ** (attempt - 1))
            logger.warning(
                "Request attempt %s/%s failed for %s: %s. Retrying in %.2fs",
                attempt,
                total_attempts,
                url,
                exc,
                backoff_seconds,
            )
            if backoff_seconds > 0:
                time.sleep(backoff_seconds)

    return None


def verify_checksum(file_path: Path, expected_sha256: str) -> bool:
    """Verify file integrity with SHA256 checksum.

    Args:
        file_path: Path to file to verify
        expected_sha256: Expected SHA256 hash (with or without 'sha256:' prefix)

    Returns:
        True if checksum matches, False otherwise
    """
    try:
        logger.info(f"Verifying checksum for {file_path.name}")

        # Remove 'sha256:' prefix if present
        expected = expected_sha256.replace("sha256:", "").strip().lower()

        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)

        actual = sha256_hash.hexdigest().lower()

        if actual == expected:
            logger.info(f"Checksum verified: {actual}")
            return True
        else:
            logger.error("Checksum mismatch!")
            logger.error(f"  Expected: {expected}")
            logger.error(f"  Actual:   {actual}")
            return False

    except OSError as e:
        logger.error(f"Checksum verification failed: {e}")
        return False


def download_file(
    url: str,
    output_path: Path,
    chunk_size: int = 8192,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_ms: int = DEFAULT_BACKOFF_MS,
) -> bool:
    """Download a file with progress indication.

    Args:
        url: URL to download from
        output_path: Local path to save file
        chunk_size: Download chunk size in bytes

    Returns:
        True if download successful, False otherwise
    """
    try:
        logger.info(f"Downloading from {url}")
        response = request_with_retry(
            url,
            stream=True,
            timeout=60,
            max_retries=max_retries,
            backoff_ms=backoff_ms,
        )
        if response is None:
            logger.error(f"Download failed after retries: {url}")
            return False

        with response:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.info(
                                f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)"
                            )

        logger.info(f"Downloaded to {output_path}")
        return True

    except (requests.RequestException, OSError) as e:
        logger.error(f"Download failed: {e}")
        return False


def get_github_release_asset(
    api_url: str,
    pattern: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_ms: int = DEFAULT_BACKOFF_MS,
) -> Optional[str]:
    """Get download URL for a GitHub release asset matching pattern.

    Args:
        api_url: GitHub API URL for releases
        pattern: Pattern to match in asset names

    Returns:
        Download URL if found, None otherwise
    """
    try:
        logger.info(f"Fetching release info from {api_url}")
        response = request_with_retry(
            api_url,
            timeout=30,
            max_retries=max_retries,
            backoff_ms=backoff_ms,
        )
        if response is None:
            logger.error(f"Failed to fetch release info after retries: {api_url}")
            return None
        with response:
            data = response.json()

        for asset in data.get("assets", []):
            asset_name = str(asset.get("name", ""))
            if pattern.lower() in asset_name.lower():
                return str(asset.get("browser_download_url", ""))

        logger.error(f"No asset matching '{pattern}' found in release metadata")
        return None

    except (requests.RequestException, ValueError) as e:
        logger.error(f"Failed to fetch release info: {e}")
        return None


def extract_zip(zip_path: Path, output_dir: Path) -> bool:
    """Extract ZIP file to output directory.

    Args:
        zip_path: Path to ZIP file
        output_dir: Directory to extract to

    Returns:
        True if extraction successful, False otherwise
    """
    try:
        logger.info(f"Extracting {zip_path} to {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)

        logger.info("Extraction complete")
        return True

    except (zipfile.BadZipFile, OSError) as e:
        logger.error(f"Extraction failed: {e}")
        return False


def verify_files(base_dir: Path, required_files: list[str]) -> bool:
    """Verify that required files exist in the extracted directory.

    Args:
        base_dir: Base directory to check
        required_files: List of required file paths (relative to base_dir)

    Returns:
        True if all files exist, False otherwise
    """
    missing_files = []

    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
            logger.warning(f"Missing required file: {file_path}")

    if missing_files:
        logger.error(f"Verification failed: {len(missing_files)} required files missing")
        return False

    logger.info("All required files verified")
    return True


def download_tesseract(
    output_dir: Path,
    force: bool = False,
    skip_verify: bool = False,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_ms: int = DEFAULT_BACKOFF_MS,
) -> bool:
    """Download and extract Tesseract OCR portable version.

    Args:
        output_dir: Directory to extract Tesseract to
        force: Re-download even if exists
        skip_verify: Skip checksum verification (for development only)
        max_retries: Number of network retries after initial failure
        backoff_ms: Initial network retry backoff in milliseconds

    Returns:
        True if successful, False otherwise
    """
    tesseract_dir = output_dir / "tesseract"

    # Check if already exists
    if tesseract_dir.exists() and not force:
        logger.info(f"Tesseract already exists at {tesseract_dir}")
        if verify_files(tesseract_dir, TESSERACT_REQUIRED_FILES):
            logger.info("Skipping Tesseract download")
            return True
        else:
            logger.warning("Existing Tesseract installation incomplete, re-downloading")

    # Download Tesseract portable ZIP
    download_path = output_dir / f"tesseract-{TESSERACT_VERSION}.zip"

    if not download_file(
        TESSERACT_URL,
        download_path,
        max_retries=max_retries,
        backoff_ms=backoff_ms,
    ):
        logger.error("Failed to download Tesseract")
        return False

    # Verify checksum
    if not skip_verify:
        checksum_key = f"tesseract-{TESSERACT_VERSION}"
        if checksum_key in CHECKSUMS:
            expected_checksum = CHECKSUMS[checksum_key]

            if not expected_checksum:
                logger.error(f"Checksum missing for {checksum_key}")
                logger.error(
                    "Set DATA_EXTRACT_TESSERACT_SHA256 or use --skip-verify only in trusted environments."
                )
                download_path.unlink(missing_ok=True)
                return False
            if not verify_checksum(download_path, expected_checksum):
                logger.error("Checksum verification failed for Tesseract")
                download_path.unlink(missing_ok=True)
                return False
        else:
            logger.error(f"No checksum defined for {checksum_key}")
            logger.error(
                "Set DATA_EXTRACT_TESSERACT_SHA256 or use --skip-verify only in trusted environments."
            )
            download_path.unlink(missing_ok=True)
            return False
    else:
        logger.warning(
            "Checksum verification was explicitly disabled via --skip-verify. "
            "Proceed only in trusted development environments."
        )

    # Extract ZIP
    if not extract_zip(download_path, tesseract_dir):
        logger.error("Failed to extract Tesseract ZIP")
        return False

    # Verify installation
    if not verify_files(tesseract_dir, TESSERACT_REQUIRED_FILES):
        logger.error("Tesseract verification failed")
        return False

    # Clean up ZIP
    download_path.unlink(missing_ok=True)
    logger.info(f"Tesseract installed successfully to {tesseract_dir}")
    return True


def download_poppler(
    output_dir: Path,
    force: bool = False,
    skip_verify: bool = False,
    poppler_version: str = POPPLER_DEFAULT_VERSION,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_ms: int = DEFAULT_BACKOFF_MS,
) -> bool:
    """Download and extract Poppler Windows binaries.

    Args:
        output_dir: Directory to extract Poppler to
        force: Re-download even if exists
        skip_verify: Skip checksum verification (for development only)
        poppler_version: Poppler version in MAJOR.MINOR.PATCH format
        max_retries: Number of network retries after initial failure
        backoff_ms: Initial network retry backoff in milliseconds

    Returns:
        True if successful, False otherwise
    """
    try:
        poppler_version = normalize_poppler_version(poppler_version)
    except argparse.ArgumentTypeError as exc:
        logger.error(str(exc))
        return False

    poppler_dir = output_dir / "poppler"

    # Check if already exists
    if poppler_dir.exists() and not force:
        logger.info(f"Poppler already exists at {poppler_dir}")
        if verify_files(poppler_dir, POPPLER_REQUIRED_FILES):
            logger.info("Skipping Poppler download")
            return True
        else:
            logger.warning("Existing Poppler installation incomplete, re-downloading")

    # Resolve version-specific Poppler release (pinned by default).
    release_api_url = build_poppler_release_api_url(poppler_version)
    asset_pattern = f"Release-{poppler_version}-"
    download_url = get_github_release_asset(
        release_api_url,
        asset_pattern,
        max_retries=max_retries,
        backoff_ms=backoff_ms,
    )

    if not download_url:
        logger.error(f"Failed to find Poppler release for version {poppler_version}")
        return False

    # Download Poppler ZIP
    download_path = output_dir / "poppler-windows.zip"

    if not download_file(
        download_url,
        download_path,
        max_retries=max_retries,
        backoff_ms=backoff_ms,
    ):
        logger.error("Failed to download Poppler")
        return False

    # Verify checksum
    if not skip_verify:
        checksum_key = f"poppler-{poppler_version}"
        expected_checksum = resolve_poppler_checksum(poppler_version)

        if not expected_checksum:
            if checksum_key in CHECKSUMS:
                logger.error(f"Checksum missing for {checksum_key}")
            else:
                logger.error(f"No checksum defined for {checksum_key}")
            logger.error(
                "Set DATA_EXTRACT_POPPLER_SHA256 or use --skip-verify only in trusted environments."
            )
            download_path.unlink(missing_ok=True)
            return False
        if not verify_checksum(download_path, expected_checksum):
            logger.error("Checksum verification failed for Poppler")
            download_path.unlink(missing_ok=True)
            return False
    else:
        logger.warning(
            "Checksum verification was explicitly disabled via --skip-verify. "
            "Proceed only in trusted development environments."
        )

    # Extract ZIP
    if not extract_zip(download_path, poppler_dir):
        logger.error("Failed to extract Poppler")
        return False

    # Verify installation
    if not verify_files(poppler_dir, POPPLER_REQUIRED_FILES):
        logger.error("Poppler verification failed")
        return False

    # Clean up ZIP
    download_path.unlink(missing_ok=True)
    logger.info(f"Poppler {poppler_version} installed successfully to {poppler_dir}")
    return True


def print_summary(output_dir: Path) -> None:
    """Print summary of downloaded dependencies.

    Args:
        output_dir: Directory containing downloaded dependencies
    """
    logger.info("\n" + "=" * 60)
    logger.info("Download Summary")
    logger.info("=" * 60)

    tesseract_dir = output_dir / "tesseract"
    poppler_dir = output_dir / "poppler"

    if tesseract_dir.exists():
        logger.info(f"\nTesseract: {tesseract_dir}")
        for file_path in TESSERACT_REQUIRED_FILES:
            full_path = tesseract_dir / file_path
            status = "✓" if full_path.exists() else "✗"
            logger.info(f"  {status} {file_path}")

    if poppler_dir.exists():
        logger.info(f"\nPoppler: {poppler_dir}")
        for file_path in POPPLER_REQUIRED_FILES:
            full_path = poppler_dir / file_path
            status = "✓" if full_path.exists() else "✗"
            logger.info(f"  {status} {file_path}")

    logger.info("\n" + "=" * 60)


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Download Tesseract and Poppler Windows binaries for packaging"
    )
    parser.add_argument(
        "--tesseract-only",
        action="store_true",
        help="Download only Tesseract",
    )
    parser.add_argument(
        "--poppler-only",
        action="store_true",
        help="Download only Poppler",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if files exist",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Explicitly skip checksum verification (unsafe; trusted dev/test environments only)",
    )
    parser.add_argument(
        "--max-retries",
        type=parse_non_negative_int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Network retries per request after first failure (default: {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument(
        "--backoff-ms",
        type=parse_non_negative_int,
        default=DEFAULT_BACKOFF_MS,
        help=f"Initial retry backoff in milliseconds (default: {DEFAULT_BACKOFF_MS})",
    )
    parser.add_argument(
        "--poppler-version",
        type=normalize_poppler_version,
        default=POPPLER_DEFAULT_VERSION,
        help=f"Pinned Poppler version to download (default: {POPPLER_DEFAULT_VERSION})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build_scripts/vendor"),
        help="Custom output directory (default: build_scripts/vendor/)",
    )

    args = parser.parse_args()

    # Determine what to download
    download_tesseract_flag = not args.poppler_only
    download_poppler_flag = not args.tesseract_only

    success = True

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {args.output_dir.absolute()}")
    logger.info(
        "Network retry policy: max_retries=%s, backoff_ms=%s",
        args.max_retries,
        args.backoff_ms,
    )
    logger.info("Pinned Poppler version: %s", args.poppler_version)

    if args.skip_verify:
        logger.warning("\n" + "!" * 60)
        logger.warning("SECURITY WARNING: Checksum verification is DISABLED via --skip-verify")
        logger.warning("No integrity checks will run for downloaded archives")
        logger.warning("Use this only in trusted development/testing environments")
        logger.warning("!" * 60 + "\n")

    # Download dependencies
    if download_tesseract_flag:
        logger.info("\n" + "=" * 60)
        logger.info("Downloading Tesseract OCR")
        logger.info("=" * 60)
        if not download_tesseract(
            args.output_dir,
            args.force,
            args.skip_verify,
            max_retries=args.max_retries,
            backoff_ms=args.backoff_ms,
        ):
            success = False
            logger.error("Tesseract download failed")

    if download_poppler_flag:
        logger.info("\n" + "=" * 60)
        logger.info("Downloading Poppler")
        logger.info("=" * 60)
        if not download_poppler(
            args.output_dir,
            args.force,
            args.skip_verify,
            poppler_version=args.poppler_version,
            max_retries=args.max_retries,
            backoff_ms=args.backoff_ms,
        ):
            success = False
            logger.error("Poppler download failed")

    # Print summary
    print_summary(args.output_dir)

    if success:
        logger.info("\n✓ All dependencies downloaded successfully")
        return 0
    else:
        logger.error("\n✗ Some dependencies failed to download")
        return 1


if __name__ == "__main__":
    sys.exit(main())

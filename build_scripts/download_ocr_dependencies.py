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
TESSERACT_GITHUB_API = "https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest"

POPPLER_GITHUB_API = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"

# Known SHA256 checksums for OCR dependencies.
# Values can be injected via environment variables in CI/CD:
# - DATA_EXTRACT_TESSERACT_SHA256
# - DATA_EXTRACT_POPPLER_SHA256
CHECKSUMS = {
    "tesseract-5.3.3": os.environ.get("DATA_EXTRACT_TESSERACT_SHA256", "").strip(),
    "poppler-24.02.0": os.environ.get("DATA_EXTRACT_POPPLER_SHA256", "").strip(),
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


def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
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
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

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
                        logger.info(f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")

        logger.info(f"Downloaded to {output_path}")
        return True

    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False


def get_latest_github_release_asset(api_url: str, pattern: str) -> Optional[str]:
    """Get download URL for latest GitHub release matching pattern.

    Args:
        api_url: GitHub API URL for releases
        pattern: Pattern to match in asset names

    Returns:
        Download URL if found, None otherwise
    """
    try:
        logger.info(f"Fetching latest release info from {api_url}")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        for asset in data.get("assets", []):
            if pattern.lower() in asset["name"].lower():
                return str(asset["browser_download_url"])

        logger.error(f"No asset matching '{pattern}' found in latest release")
        return None

    except requests.RequestException as e:
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


def download_tesseract(output_dir: Path, force: bool = False, skip_verify: bool = False) -> bool:
    """Download and extract Tesseract OCR portable version.

    Args:
        output_dir: Directory to extract Tesseract to
        force: Re-download even if exists
        skip_verify: Skip checksum verification (for development only)

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

    if not download_file(TESSERACT_URL, download_path):
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
        logger.warning("Checksum verification SKIPPED (--skip-verify flag)")

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


def download_poppler(output_dir: Path, force: bool = False, skip_verify: bool = False) -> bool:
    """Download and extract Poppler Windows binaries.

    Args:
        output_dir: Directory to extract Poppler to
        force: Re-download even if exists
        skip_verify: Skip checksum verification (for development only)

    Returns:
        True if successful, False otherwise
    """
    poppler_dir = output_dir / "poppler"

    # Check if already exists
    if poppler_dir.exists() and not force:
        logger.info(f"Poppler already exists at {poppler_dir}")
        if verify_files(poppler_dir, POPPLER_REQUIRED_FILES):
            logger.info("Skipping Poppler download")
            return True
        else:
            logger.warning("Existing Poppler installation incomplete, re-downloading")

    # Get latest Poppler release
    download_url = get_latest_github_release_asset(POPPLER_GITHUB_API, "Release-")

    if not download_url:
        logger.error("Failed to find Poppler release")
        return False

    # Download Poppler ZIP
    download_path = output_dir / "poppler-windows.zip"

    if not download_file(download_url, download_path):
        logger.error("Failed to download Poppler")
        return False

    # Verify checksum
    if not skip_verify:
        # Extract version from URL if possible for checksum lookup
        # For now, use a generic key since we fetch latest dynamically
        checksum_key = "poppler-24.02.0"
        if checksum_key in CHECKSUMS:
            expected_checksum = CHECKSUMS[checksum_key]

            if not expected_checksum:
                logger.error(f"Checksum missing for {checksum_key}")
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
            logger.error(f"No checksum defined for {checksum_key}")
            logger.error(
                "Set DATA_EXTRACT_POPPLER_SHA256 or use --skip-verify only in trusted environments."
            )
            download_path.unlink(missing_ok=True)
            return False
    else:
        logger.warning("Checksum verification SKIPPED (--skip-verify flag)")

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
    logger.info(f"Poppler installed successfully to {poppler_dir}")
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
        help="Skip checksum verification (for development only)",
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

    if args.skip_verify:
        logger.warning("\n" + "!" * 60)
        logger.warning("SECURITY WARNING: Checksum verification is DISABLED")
        logger.warning("This should only be used for development/testing")
        logger.warning("!" * 60 + "\n")

    # Download dependencies
    if download_tesseract_flag:
        logger.info("\n" + "=" * 60)
        logger.info("Downloading Tesseract OCR")
        logger.info("=" * 60)
        if not download_tesseract(args.output_dir, args.force, args.skip_verify):
            success = False
            logger.error("Tesseract download failed")

    if download_poppler_flag:
        logger.info("\n" + "=" * 60)
        logger.info("Downloading Poppler")
        logger.info("=" * 60)
        if not download_poppler(args.output_dir, args.force, args.skip_verify):
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

"""Unit tests for download_ocr_dependencies.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "build_scripts"))

import download_ocr_dependencies as downloader  # noqa: E402


class TestNetworkRetry:
    """Retry/backoff behavior for outbound HTTP requests."""

    @pytest.mark.unit
    def test_request_with_retry_succeeds_after_transient_failures(self):
        """Retries requests and applies exponential backoff between attempts."""
        success_response = MagicMock()
        success_response.raise_for_status.return_value = None

        with (
            patch.object(
                downloader.requests,
                "get",
                side_effect=[
                    downloader.requests.RequestException("first failure"),
                    downloader.requests.RequestException("second failure"),
                    success_response,
                ],
            ) as mock_get,
            patch.object(downloader.time, "sleep") as mock_sleep,
        ):
            response = downloader.request_with_retry(
                "https://example.test/file.zip",
                timeout=15,
                max_retries=3,
                backoff_ms=250,
            )

        assert response is success_response
        assert mock_get.call_count == 3
        mock_sleep.assert_has_calls([call(0.25), call(0.5)])

    @pytest.mark.unit
    def test_request_with_retry_returns_none_after_exhausting_retries(self):
        """Stops after max retries and returns None when all attempts fail."""
        with (
            patch.object(
                downloader.requests,
                "get",
                side_effect=[
                    downloader.requests.RequestException("network down"),
                    downloader.requests.RequestException("network down"),
                    downloader.requests.RequestException("network down"),
                ],
            ) as mock_get,
            patch.object(downloader.time, "sleep") as mock_sleep,
        ):
            response = downloader.request_with_retry(
                "https://example.test/file.zip",
                timeout=15,
                max_retries=2,
                backoff_ms=100,
            )

        assert response is None
        assert mock_get.call_count == 3
        mock_sleep.assert_has_calls([call(0.1), call(0.2)])


class TestPopplerVersionAndChecksum:
    """Version pinning and checksum selection for Poppler downloads."""

    @pytest.mark.unit
    def test_resolve_poppler_checksum_prefers_versioned_checksum_over_env(self):
        """Version-specific checksum config takes precedence over shared env fallback."""
        selected_version = "24.08.0"
        version_checksum = "sha256:from-config"
        env_checksum = "sha256:from-env"

        with (
            patch.dict(
                downloader.CHECKSUMS,
                {f"poppler-{selected_version}": version_checksum},
                clear=True,
            ),
            patch.dict(
                downloader.os.environ,
                {downloader.POPPLER_CHECKSUM_ENV_VAR: env_checksum},
                clear=True,
            ),
        ):
            resolved = downloader.resolve_poppler_checksum(selected_version)

        assert resolved == version_checksum

    @pytest.mark.unit
    def test_download_poppler_uses_selected_version_for_release_and_checksum(self, tmp_path):
        """Poppler version drives both release lookup and checksum key selection."""
        selected_version = "24.08.0"
        expected_checksum = "sha256:abc123"

        with (
            patch.object(
                downloader,
                "get_github_release_asset",
                return_value="https://example.test/poppler.zip",
            ) as mock_release_lookup,
            patch.object(downloader, "download_file", return_value=True) as mock_download_file,
            patch.object(downloader, "verify_checksum", return_value=True) as mock_verify_checksum,
            patch.object(downloader, "extract_zip", return_value=True),
            patch.object(downloader, "verify_files", return_value=True),
            patch.dict(
                downloader.CHECKSUMS,
                {f"poppler-{selected_version}": expected_checksum},
                clear=True,
            ),
        ):
            ok = downloader.download_poppler(
                tmp_path,
                poppler_version=selected_version,
                max_retries=4,
                backoff_ms=300,
            )

        assert ok is True
        mock_release_lookup.assert_called_once_with(
            downloader.build_poppler_release_api_url(selected_version),
            f"Release-{selected_version}-",
            max_retries=4,
            backoff_ms=300,
        )
        mock_download_file.assert_called_once_with(
            "https://example.test/poppler.zip",
            tmp_path / "poppler-windows.zip",
            max_retries=4,
            backoff_ms=300,
        )
        mock_verify_checksum.assert_called_once_with(tmp_path / "poppler-windows.zip", expected_checksum)

    @pytest.mark.unit
    def test_download_poppler_uses_env_checksum_for_selected_version(self, tmp_path):
        """Non-default Poppler versions may use shared env checksum when version key is unset."""
        selected_version = "24.08.0"
        expected_checksum = "sha256:env-supplied"

        with (
            patch.object(
                downloader,
                "get_github_release_asset",
                return_value="https://example.test/poppler.zip",
            ),
            patch.object(downloader, "download_file", return_value=True),
            patch.object(downloader, "verify_checksum", return_value=True) as mock_verify_checksum,
            patch.object(downloader, "extract_zip", return_value=True),
            patch.object(downloader, "verify_files", return_value=True),
            patch.dict(downloader.CHECKSUMS, {}, clear=True),
            patch.dict(
                downloader.os.environ,
                {downloader.POPPLER_CHECKSUM_ENV_VAR: expected_checksum},
                clear=True,
            ),
        ):
            ok = downloader.download_poppler(
                tmp_path,
                poppler_version=selected_version,
            )

        assert ok is True
        mock_verify_checksum.assert_called_once_with(tmp_path / "poppler-windows.zip", expected_checksum)

    @pytest.mark.unit
    def test_download_poppler_fails_when_checksum_missing_for_selected_version(self, tmp_path):
        """Fails safely when selected Poppler version has no configured checksum."""
        with (
            patch.object(
                downloader,
                "get_github_release_asset",
                return_value="https://example.test/poppler.zip",
            ),
            patch.object(downloader, "download_file", return_value=True),
            patch.object(downloader, "verify_checksum") as mock_verify_checksum,
            patch.object(downloader, "extract_zip") as mock_extract_zip,
            patch.object(downloader, "verify_files") as mock_verify_files,
            patch.dict(downloader.CHECKSUMS, {}, clear=True),
        ):
            ok = downloader.download_poppler(tmp_path, poppler_version="24.08.0")

        assert ok is False
        mock_verify_checksum.assert_not_called()
        mock_extract_zip.assert_not_called()
        mock_verify_files.assert_not_called()

    @pytest.mark.unit
    def test_download_poppler_skip_verify_bypasses_missing_checksum(self, tmp_path):
        """Explicit --skip-verify semantics: no checksum lookup is required."""
        with (
            patch.object(
                downloader,
                "get_github_release_asset",
                return_value="https://example.test/poppler.zip",
            ),
            patch.object(downloader, "download_file", return_value=True),
            patch.object(downloader, "verify_checksum") as mock_verify_checksum,
            patch.object(downloader, "extract_zip", return_value=True),
            patch.object(downloader, "verify_files", return_value=True),
            patch.dict(downloader.CHECKSUMS, {}, clear=True),
        ):
            ok = downloader.download_poppler(
                tmp_path,
                poppler_version="24.08.0",
                skip_verify=True,
            )

        assert ok is True
        mock_verify_checksum.assert_not_called()


class TestCliFlags:
    """CLI wiring for retry/poppler-version flags."""

    @pytest.mark.unit
    def test_main_forwards_retry_and_poppler_version_flags(self, tmp_path):
        """CLI values are propagated to dependency download functions."""
        with (
            patch.object(
                sys,
                "argv",
                [
                    "download_ocr_dependencies.py",
                    "--output-dir",
                    str(tmp_path),
                    "--max-retries",
                    "5",
                    "--backoff-ms",
                    "1200",
                    "--poppler-version",
                    "v24.08.0-0",
                ],
            ),
            patch.object(downloader, "download_tesseract", return_value=True) as mock_tesseract,
            patch.object(downloader, "download_poppler", return_value=True) as mock_poppler,
            patch.object(downloader, "print_summary"),
        ):
            exit_code = downloader.main()

        assert exit_code == 0
        mock_tesseract.assert_called_once_with(
            tmp_path,
            False,
            False,
            max_retries=5,
            backoff_ms=1200,
        )
        mock_poppler.assert_called_once_with(
            tmp_path,
            False,
            False,
            poppler_version="24.08.0",
            max_retries=5,
            backoff_ms=1200,
        )

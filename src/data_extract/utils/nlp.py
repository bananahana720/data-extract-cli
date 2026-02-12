"""NLP utilities for text processing using spaCy.

This module provides sentence boundary detection and other NLP utilities
for the data extraction pipeline. Used by Epic 3 chunking stage.

Supports both development and frozen executable modes (PyInstaller).
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Optional

import structlog
from spacy.language import Language

# Module-level cache for lazy loading (load once, reuse pattern from Story 2.5.1.1)
_nlp_model: Optional[Language] = None
_using_fallback_model = False

logger = structlog.get_logger(__name__)


def _validate_override_path(path_str: str, expected_type: str = "file") -> Optional[Path]:
    """Validate override path is safe and exists.

    Args:
        path_str: Path string from environment variable
        expected_type: "file" or "directory"

    Returns:
        Validated Path or None if invalid
    """
    try:
        path = Path(path_str).resolve()

        # Must be absolute after resolution
        if not path.is_absolute():
            logger.warning("override_path_not_absolute", path=path_str)
            return None

        # Check existence based on type
        if expected_type == "file" and not path.is_file():
            logger.warning("override_path_not_file", path=path_str)
            return None
        elif expected_type == "directory" and not path.is_dir():
            logger.warning("override_path_not_directory", path=path_str)
            return None

        return path
    except (OSError, RuntimeError, ValueError) as e:
        logger.warning("override_path_invalid", path=path_str, error=str(e))
        return None


def _get_frozen_base_path() -> Optional[Path]:
    """Get base path for PyInstaller frozen executable.

    Returns:
        Path to temporary extraction directory if frozen, None otherwise.

    Example:
        In frozen mode: Path("C:/Users/.../AppData/Local/Temp/_MEI12345")
        In dev mode: None
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return None


def _find_spacy_model_path() -> Optional[Path]:
    """Locate spaCy model in frozen executable or environment override.

    Checks in order:
    1. SPACY_MODEL_PATH_OVERRIDE environment variable
    2. Frozen bundle path (PyInstaller _MEIPASS)
    3. Returns None to fall back to standard spacy.load()

    Returns:
        Path to spaCy model directory if found, None for standard loading.

    Environment Variables:
        SPACY_MODEL_PATH_OVERRIDE: Override path to en_core_web_md model

    Example:
        # In frozen executable
        path = _find_spacy_model_path()
        # Returns: Path("C:/Users/.../Temp/_MEI12345/en_core_web_md/en_core_web_md")

        # With override
        os.environ["SPACY_MODEL_PATH_OVERRIDE"] = "C:/models/en_core_web_md"
        path = _find_spacy_model_path()
        # Returns: Path("C:/models/en_core_web_md")
    """
    # Check environment variable override
    override = os.environ.get("SPACY_MODEL_PATH_OVERRIDE")
    if override:
        override_path = _validate_override_path(override, expected_type="directory")
        if override_path:
            logger.info("Using spaCy model from environment override", path=str(override_path))
            return override_path

    # Check frozen bundle path
    frozen_base = _get_frozen_base_path()
    if frozen_base:
        # PyInstaller bundles model at: _MEIPASS/en_core_web_md/en_core_web_md
        model_path = frozen_base / "en_core_web_md" / "en_core_web_md"
        if model_path.exists():
            logger.info("Using bundled spaCy model from frozen executable", path=str(model_path))
            return model_path
        else:
            logger.warning(
                "Running in frozen mode but bundled model not found",
                expected_path=str(model_path),
            )

    return None


def _build_fallback_nlp() -> Language:
    """Build lightweight English sentence segmenter for offline/dev fallback."""
    import spacy

    fallback_nlp = spacy.blank("en")
    if "sentencizer" not in fallback_nlp.pipe_names:
        fallback_nlp.add_pipe("sentencizer")
    return fallback_nlp


def _heuristic_sentence_boundaries(text: str) -> List[int]:
    """Calculate sentence boundaries when statistical spaCy model is unavailable."""
    boundaries: List[int] = []
    non_terminal_abbreviations = {
        "dr.",
        "mr.",
        "mrs.",
        "ms.",
        "prof.",
        "inc.",
        "ltd.",
        "corp.",
        "co.",
        "vs.",
        "e.g.",
        "i.e.",
    }

    for idx, char in enumerate(text):
        if char not in ".!?":
            continue

        # Ignore punctuation used inside tokens (domains, acronyms, decimals).
        if idx + 1 < len(text) and not text[idx + 1].isspace():
            continue

        next_idx = idx + 1
        while next_idx < len(text) and text[next_idx].isspace():
            next_idx += 1

        if next_idx >= len(text):
            boundaries.append(len(text))
            continue

        next_char = text[next_idx]
        if char == ".":
            token_start = idx
            while token_start > 0 and not text[token_start - 1].isspace():
                token_start -= 1
            prev_token = text[token_start : idx + 1]
            prev_token_lower = prev_token.lower()

            if prev_token_lower in non_terminal_abbreviations:
                continue

            is_acronym = bool(re.fullmatch(r"(?:[A-Za-z]\.){2,}", prev_token))
            if is_acronym and not next_char.isupper():
                continue

            if not (next_char.isalpha() or next_char in "\"'([{"):
                continue

        boundaries.append(idx + 1)

    if not boundaries:
        return [len(text)]
    if boundaries[-1] != len(text):
        boundaries.append(len(text))
    return boundaries


def get_sentence_boundaries(text: str, nlp: Optional[Language] = None) -> List[int]:
    """Extract sentence boundary positions from text using spaCy.

    Returns character offsets (zero-indexed) where each sentence ends.
    Lazy loads en_core_web_md model if nlp parameter is None.

    Args:
        text: Input text to segment into sentences. Must be non-empty.
        nlp: Optional pre-loaded spaCy Language model. If None, lazy loads
            en_core_web_md and caches for subsequent calls.

    Returns:
        List of character positions (zero-indexed) where sentences end.
        For example, "Hello. World." returns [6, 13].

    Raises:
        ValueError: If text is empty or whitespace-only.
        OSError: If required spaCy resources are unavailable in frozen mode.

    Example:
        >>> boundaries = get_sentence_boundaries("Dr. Smith visited. This is sentence two.")
        >>> print(boundaries)
        [18, 42]

        >>> # With pre-loaded model
        >>> import spacy
        >>> nlp = spacy.load("en_core_web_md")
        >>> boundaries = get_sentence_boundaries("Hello. World.", nlp=nlp)
        >>> print(boundaries)
        [6, 13]

    NFR Compliance:
        - NFR-P3: Model load <5s, segmentation <100ms per 1000 words
        - NFR-O4: Logs model version on first load
        - NFR-R3: Clear error messages for missing model or invalid input
    """
    global _nlp_model, _using_fallback_model

    # Input validation (NFR-R3)
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty or whitespace-only")

    # Lazy load model if not provided
    if nlp is None:
        if _nlp_model is None:
            try:
                import spacy

                # Check for frozen executable or environment override
                model_path = _find_spacy_model_path()

                if model_path:
                    # Load from bundled or override path
                    _nlp_model = spacy.load(str(model_path))
                    _using_fallback_model = False
                    logger.info(
                        "spaCy model loaded from custom path",
                        model_name="en_core_web_md",
                        path=str(model_path),
                        version=_nlp_model.meta["version"],
                    )
                else:
                    # Standard load from site-packages
                    _nlp_model = spacy.load("en_core_web_md")
                    _using_fallback_model = False
                    logger.info(
                        "spaCy model loaded",
                        model_name="en_core_web_md",
                        version=_nlp_model.meta["version"],
                        language=_nlp_model.meta["lang"],
                        vocab_size=len(_nlp_model.vocab),
                    )
            except OSError as e:
                # Clear error message with actionable resolution (NFR-R3)
                frozen_base = _get_frozen_base_path()
                if frozen_base:
                    # In frozen mode, don't suggest download command
                    error_msg = (
                        "spaCy model 'en_core_web_md' not found in frozen executable bundle. "
                        "The model may not have been included during build, or the bundle is corrupted. "
                        "Set SPACY_MODEL_PATH_OVERRIDE environment variable to specify model location."
                    )
                    logger.error("spaCy model load failed", error=str(e), resolution=error_msg)
                    raise OSError(error_msg) from e

                error_msg = (
                    "spaCy model 'en_core_web_md' not found. "
                    "Falling back to lightweight sentence segmentation; "
                    "install with: python -m spacy download en_core_web_md"
                )
                logger.warning(
                    "spaCy model load failed, using fallback", error=str(e), resolution=error_msg
                )
                _nlp_model = _build_fallback_nlp()
                _using_fallback_model = True
                logger.info(
                    "spaCy fallback model loaded",
                    model_name="blank_en_sentencizer",
                    language=_nlp_model.meta.get("lang"),
                )

        nlp = _nlp_model

    # Process text and extract sentence boundaries
    assert nlp is not None
    if nlp is _nlp_model and _using_fallback_model:
        return _heuristic_sentence_boundaries(text)

    doc = nlp(text)
    boundaries = [sent.end_char for sent in doc.sents]

    return boundaries

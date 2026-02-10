"""Sentence segmentation wrapper for chunking engine.

Wraps the spaCy-based sentence boundary detection utility for dependency injection.
"""

from typing import List

from ..utils.nlp import get_sentence_boundaries


class SentenceSegmenter:
    """Sentence segmentation using spaCy for semantic chunking.

    Wraps get_sentence_boundaries() utility to provide a clean interface
    for dependency injection in ChunkingEngine.

    Example:
        >>> segmenter = SentenceSegmenter()
        >>> sentences = segmenter.segment("First sentence. Second sentence.")
        >>> print(sentences)
        ['First sentence.', 'Second sentence.']
    """

    def segment(self, text: str) -> List[str]:
        """Segment text into sentences using spaCy.

        Args:
            text: Input text to segment

        Returns:
            List of sentence strings

        Raises:
            ValueError: If text is empty or whitespace-only
            OSError: If en_core_web_md model is not installed
        """
        if not text or not text.strip():
            return []

        # Get sentence boundary positions
        boundaries = get_sentence_boundaries(text)

        # Extract sentence texts
        sentences: List[str] = []
        start = 0
        for end in boundaries:
            sentence = text[start:end].strip()
            if sentence:  # Skip empty sentences
                sentences.append(sentence)
            start = end

        return sentences

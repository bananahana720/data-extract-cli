"""Entity normalization for audit domain.

This module provides entity recognition, standardization, and normalization
for audit-specific entities (processes, risks, controls, regulations, policies, issues).

Classes:
    EntityNormalizer: Main class for entity recognition and normalization

Key Features (Story 2.2):
- AC-2.2.1: Recognition of 6 entity types using configurable patterns
- AC-2.2.2: Entity ID standardization (e.g., "Risk #123" → "Risk-123")
- AC-2.2.3: Abbreviation expansion using configurable dictionary
  Note: Abbreviation expansion applies to first occurrence only to prevent
  conflicts when the same abbreviation appears multiple times.
- AC-2.2.4: Consistent capitalization for entity types
- AC-2.2.5: Cross-reference resolution and entity graph construction
- AC-2.2.6: Entity tagging in metadata for RAG retrieval
- AC-2.2.7: Configurable patterns and rules via YAML

Implementation Note (Architectural Decision):
    This implementation uses compiled regex patterns with context window analysis
    instead of spaCy NLP integration. This decision was made because:
    1. Audit entity formats are highly structured (Risk-123, Control-456)
    2. Regex patterns provide deterministic, fast recognition without ML overhead
    3. Context window (±5 words) provides sufficient disambiguation
    4. Avoids spaCy dependency (~100MB) and model loading time (~2s)
    5. Maintains compliance with ADR-004 (Classical NLP, no transformers)

    If spaCy integration is needed in future for advanced NLP features
    (sentence boundaries, NER), it can be added without breaking the current API.
"""

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..core.models import Document, Entity, EntityType, ProcessingContext


class EntityNormalizer:
    """Entity recognizer and normalizer for audit documents.

    Recognizes and normalizes audit domain entities using configurable
    patterns and dictionaries. Implements PipelineStage protocol.

    Attributes:
        patterns: Compiled entity patterns by type
        dictionary: Abbreviation expansion dictionary
        config: Normalization configuration settings
        logger: Structured logger for audit trail

    Example:
        >>> from pathlib import Path
        >>> normalizer = EntityNormalizer(
        ...     patterns_file=Path("config/normalize/entity_patterns.yaml"),
        ...     dictionary_file=Path("config/normalize/entity_dictionary.yaml")
        ... )
        >>> document = Document(...)
        >>> normalized_doc = normalizer.process(document, context)
    """

    def __init__(
        self,
        patterns_file: Optional[Path] = None,
        dictionary_file: Optional[Path] = None,
        context_window: int = 5,
        logger: Optional[Any] = None,
    ):
        """Initialize EntityNormalizer with configuration files.

        Args:
            patterns_file: Path to entity patterns YAML (AC-2.2.7)
            dictionary_file: Path to entity dictionary YAML (AC-2.2.3)
            context_window: Words before/after for disambiguation (AC-2.2.1)
            logger: Structured logger for audit trail

        Raises:
            FileNotFoundError: If required configuration files not found
            ValueError: If patterns fail validation
        """
        self.context_window = context_window
        self.logger = logger

        # Load and compile entity patterns (AC-2.2.7)
        self.patterns: Dict[EntityType, List[Dict[str, Any]]] = (
            self._load_patterns(patterns_file) if patterns_file else {}
        )

        # Load abbreviation dictionary (AC-2.2.3)
        self.dictionary = self._load_dictionary(dictionary_file) if dictionary_file else {}

        # Entity graph for cross-reference resolution (AC-2.2.5)
        self.entity_graph: Dict[str, List[str]] = defaultdict(list)

    def _load_patterns(self, patterns_file: Path) -> Dict[EntityType, List[Dict[str, Any]]]:
        """Load and compile entity recognition patterns from YAML.

        Args:
            patterns_file: Path to entity_patterns.yaml

        Returns:
            Dictionary mapping entity types to compiled pattern lists

        Raises:
            FileNotFoundError: If patterns file not found
            ValueError: If pattern compilation fails
        """
        if not patterns_file.exists():
            raise FileNotFoundError(f"Entity patterns file not found: {patterns_file}")

        with open(patterns_file, "r", encoding="utf-8") as f:
            patterns_config = yaml.safe_load(f) or {}

        compiled_patterns: Dict[EntityType, List[Dict[str, Any]]] = {}

        # Map YAML keys to EntityType enum values (AC-2.2.1)
        type_mapping = {
            "processes": EntityType.PROCESS,
            "risks": EntityType.RISK,
            "controls": EntityType.CONTROL,
            "regulations": EntityType.REGULATION,
            "policies": EntityType.POLICY,
            "issues": EntityType.ISSUE,
        }

        for yaml_key, entity_type in type_mapping.items():
            if yaml_key not in patterns_config:
                continue

            patterns_list = patterns_config[yaml_key]
            compiled_list = []

            for pattern_def in patterns_list:
                try:
                    # Compile regex pattern (AC-2.2.7 determinism)
                    compiled_pattern = re.compile(pattern_def["pattern"])
                    pattern_entry = {
                        "pattern": compiled_pattern,
                        "raw_pattern": pattern_def["pattern"],
                        "description": pattern_def.get("description", ""),
                        "priority": pattern_def.get("priority", 99),
                        "context_required": pattern_def.get("context_required", False),
                        "context_keywords": pattern_def.get("context_keywords", []),
                        "id_formats": pattern_def.get("id_formats", []),
                    }
                    compiled_list.append(pattern_entry)
                except re.error as e:
                    raise ValueError(f"Invalid regex in {yaml_key}: {e}")

            # Sort by priority (AC-2.2.7)
            compiled_list.sort(key=lambda x: x["priority"])
            compiled_patterns[entity_type] = compiled_list

        return compiled_patterns

    def _load_dictionary(self, dictionary_file: Path) -> Dict[str, Dict[str, Any]]:
        """Load abbreviation expansion dictionary from YAML.

        Args:
            dictionary_file: Path to entity_dictionary.yaml

        Returns:
            Dictionary mapping abbreviations to expansion info

        Raises:
            FileNotFoundError: If dictionary file not found
        """
        if not dictionary_file.exists():
            raise FileNotFoundError(f"Entity dictionary file not found: {dictionary_file}")

        with open(dictionary_file, "r", encoding="utf-8") as f:
            dictionary_config = yaml.safe_load(f) or {}

        # Filter out configuration sections
        dictionary = {
            k: v for k, v in dictionary_config.items() if isinstance(v, dict) and "full_form" in v
        }

        return dictionary

    def recognize_entity_type(
        self, mention: str, context_words: List[str]
    ) -> Optional[Tuple[EntityType, float]]:
        """Classify entity mention by type using pattern matching.

        Args:
            mention: Entity text to classify
            context_words: Surrounding words for disambiguation (AC-2.2.1)

        Returns:
            Tuple of (EntityType, confidence) or None if no match

        Example:
            >>> normalizer.recognize_entity_type("Risk #123", ["identified", "operational"])
            (EntityType.RISK, 0.95)
        """
        best_match: Optional[Tuple[EntityType, float]] = None
        best_priority = 999

        for entity_type, patterns_list in self.patterns.items():
            for pattern_entry in patterns_list:
                # Skip if lower priority than best match
                if pattern_entry["priority"] > best_priority:
                    continue

                # Check pattern match
                if not pattern_entry["pattern"].search(mention):
                    continue

                # Context checking for disambiguation (AC-2.2.1)
                if pattern_entry["context_required"]:
                    context_keywords = pattern_entry["context_keywords"]
                    if context_keywords:
                        # Check if any context keyword appears in surrounding words
                        context_text = " ".join(context_words).lower()
                        has_context = any(kw.lower() in context_text for kw in context_keywords)
                        if not has_context:
                            continue  # Skip this pattern due to missing context

                # Calculate confidence based on priority and context
                confidence = 1.0 - (pattern_entry["priority"] * 0.1)
                if pattern_entry["context_required"] and context_words:
                    confidence *= 0.95  # Slightly lower for context-dependent matches

                # Update best match if this is higher priority
                if pattern_entry["priority"] < best_priority or (
                    pattern_entry["priority"] == best_priority
                    and confidence > (best_match[1] if best_match else 0)
                ):
                    best_match = (entity_type, min(confidence, 1.0))
                    best_priority = pattern_entry["priority"]

        return best_match

    def standardize_entity_id(self, entity_mention: str, entity_type: EntityType) -> str:
        """Normalize entity ID format to canonical form.

        Converts various ID formats to standard "EntityType-NNN" format (AC-2.2.2).

        Args:
            entity_mention: Raw entity text (e.g., "Risk #123", "risk 456")
            entity_type: Type of entity

        Returns:
            Canonical entity ID (e.g., "Risk-123")

        Example:
            >>> normalizer.standardize_entity_id("Risk #123", EntityType.RISK)
            "Risk-123"
            >>> normalizer.standardize_entity_id("CONTROL_456", EntityType.CONTROL)
            "Control-456"
        """
        # Extract numeric ID from mention
        id_match = re.search(r"\d+", entity_mention)
        if not id_match:
            # No numeric ID found, generate hash-based ID
            mention_hash = int(hashlib.sha256(entity_mention.encode()).hexdigest()[:5], 16) % 10000
            numeric_id = str(mention_hash)
        else:
            numeric_id = id_match.group()

        # Capitalize entity type name (AC-2.2.4)
        type_name = entity_type.value.capitalize()

        # Canonical format: "Type-NNN" (AC-2.2.2)
        return f"{type_name}-{numeric_id}"

    def normalize_capitalization(self, text: str, entity_type: EntityType) -> str:
        """Apply consistent capitalization to entity type names.

        Args:
            text: Text containing entity mention
            entity_type: Type of entity

        Returns:
            Text with normalized capitalization (AC-2.2.4)

        Example:
            >>> normalizer.normalize_capitalization("RISK assessment", EntityType.RISK)
            "Risk assessment"
        """
        type_name = entity_type.value
        # Replace case-insensitive matches with title case
        pattern = re.compile(rf"\b{re.escape(type_name)}\b", re.IGNORECASE)
        return pattern.sub(type_name.capitalize(), text)

    def expand_abbreviations(
        self, text: str, context_window: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Expand abbreviations using dictionary with context awareness.

        Args:
            text: Input text with abbreviations
            context_window: Words before/after for context checking (AC-2.2.3)

        Returns:
            Tuple of (expanded_text, expansion_log) for audit trail

        Example:
            >>> normalizer.expand_abbreviations("GRC framework review")
            ("Governance, Risk, and Compliance framework review", [...])
        """
        expanded_text = text
        expansion_log: List[Dict[str, Any]] = []

        for abbrev, entry in self.dictionary.items():
            # Build regex pattern for abbreviation
            case_sensitive = entry.get("case_sensitive", False)
            flags = 0 if case_sensitive else re.IGNORECASE

            # Try main abbreviation
            pattern = re.compile(rf"\b{re.escape(abbrev)}\b", flags)

            # Find all matches
            for match in pattern.finditer(expanded_text):
                match_pos = match.start()
                match_text = match.group()

                # Context checking for disambiguation (AC-2.2.3)
                if entry.get("context_required", False):
                    context_keywords = entry.get("context_keywords", [])
                    if context_keywords:
                        # Get surrounding words
                        before_text = expanded_text[max(0, match_pos - 50) : match_pos]
                        after_text = expanded_text[
                            match_pos : min(len(expanded_text), match_pos + 50)
                        ]
                        context_text = (before_text + " " + after_text).lower()

                        # Check if any keyword present
                        has_context = any(kw.lower() in context_text for kw in context_keywords)
                        if not has_context:
                            continue  # Skip expansion due to missing context

                # Perform expansion
                full_form = entry["full_form"]
                expanded_text = (
                    expanded_text[: match.start()] + full_form + expanded_text[match.end() :]
                )

                # Log expansion for audit trail (AC-2.2.3)
                expansion_log.append(
                    {
                        "abbreviation": match_text,
                        "expansion": full_form,
                        "position": match_pos,
                        "category": entry.get("category", "unknown"),
                    }
                )

                # Note: Only expand first occurrence to avoid conflicts
                # Re-find matches after modification would be needed for multiple expansions
                break

        return expanded_text, expansion_log

    def resolve_cross_references(self, entities: List[Entity]) -> List[Entity]:
        """Link entity mentions to canonical IDs and build entity graph.

        Handles partial matches and entity relationship preservation (AC-2.2.5).

        Args:
            entities: List of recognized entities

        Returns:
            List of entities with resolved canonical IDs

        Example:
            >>> entities = [Entity(...), Entity(...)]
            >>> resolved = normalizer.resolve_cross_references(entities)
        """
        # Build canonical ID mapping
        canonical_map: Dict[str, str] = {}
        for entity in entities:
            canonical_map[entity.text.lower()] = entity.id

        # Resolve references
        resolved_entities = []
        for entity in entities:
            # Check if this is a reference to another entity
            # (same type, partial text match)
            resolved_id = entity.id

            for canonical_text, canonical_id in canonical_map.items():
                # Partial match logic
                if entity.text.lower() in canonical_text or canonical_text in entity.text.lower():
                    # Use the canonical ID with higher confidence
                    if entity.confidence < 0.9:
                        resolved_id = canonical_id
                        break

            # Update entity with resolved ID
            resolved_entity = Entity(
                type=entity.type,
                id=resolved_id,
                text=entity.text,
                confidence=entity.confidence,
                location=entity.location,
            )
            resolved_entities.append(resolved_entity)

            # Build entity graph (AC-2.2.5)
            self.entity_graph[resolved_id].append(entity.text)

        return resolved_entities

    def process(self, document: Document, context: ProcessingContext) -> Document:
        """Process document to recognize and normalize entities.

        Main pipeline method implementing PipelineStage protocol.

        Args:
            document: Input document with text
            context: Processing context with config and logger

        Returns:
            Document with recognized entities and enriched metadata (AC-2.2.6)

        Example:
            >>> document = Document(id="doc1", text="Risk #123 identified...", ...)
            >>> normalized = normalizer.process(document, context)
            >>> len(normalized.entities)  # Entities recognized
            1
        """
        text = document.text
        entities: List[Entity] = []

        # Step 1: Expand abbreviations (AC-2.2.3)
        expanded_text, expansion_log = self.expand_abbreviations(text, self.context_window)

        if self.logger and expansion_log:
            self.logger.info(
                "abbreviations_expanded", count=len(expansion_log), expansions=expansion_log
            )

        # Step 2: Recognize entities using patterns (AC-2.2.1)
        words = expanded_text.split()
        for i, word in enumerate(words):
            # Get context window
            start_idx = max(0, i - self.context_window)
            end_idx = min(len(words), i + self.context_window + 1)
            context_words = words[start_idx:end_idx]

            # Try to recognize entity type
            result = self.recognize_entity_type(word, context_words)
            if result:
                entity_type, confidence = result

                # Calculate character position (approximate)
                char_position = len(" ".join(words[:i]))
                location = {"start": char_position, "end": char_position + len(word)}

                # Standardize entity ID (AC-2.2.2)
                canonical_id = self.standardize_entity_id(word, entity_type)

                # Create entity
                entity = Entity(
                    type=entity_type,
                    id=canonical_id,
                    text=word,
                    confidence=confidence,
                    location=location,
                )
                entities.append(entity)

        # Step 3: Resolve cross-references (AC-2.2.5)
        entities = self.resolve_cross_references(entities)

        # Step 4: Enrich metadata (AC-2.2.6)
        entity_tags = [e.id for e in entities]
        entity_counts: Dict[str, int] = defaultdict(int)
        for entity in entities:
            entity_counts[entity.type.value] += 1

        # Update document with new entities and enriched metadata
        document.entities = entities
        document.metadata = document.metadata.model_copy(
            update={
                "entity_tags": entity_tags,
                "entity_counts": dict(entity_counts),
            }
        )

        if self.logger:
            self.logger.info(
                "entities_normalized",
                total_entities=len(entities),
                entity_counts=dict(entity_counts),
            )

        return document

# Configuration and Dependency Injection

## Processor Configuration

**Pattern 1: Constructor Injection**
```python
class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.entity_extraction_enabled = self.config.get("entity_extraction", True)
        self.domain_model = self.config.get("domain_model", "general")
```

**Pattern 2: ConfigManager Integration**
```python
# config.yaml
processors:
  semantic_analyzer:
    enabled: true
    entity_extraction: true
    domain_model: "cybersecurity_audit"
    grc_entities:
      - processes
      - risks
      - controls
      - regulations
    confidence_threshold: 0.7
    nlp_library: "spacy"  # or "nltk"
    spacy_model: "en_core_web_sm"
```

```python
# In processor
from infrastructure import ConfigManager

class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None, config_manager: Optional[ConfigManager] = None):
        super().__init__(config)
        self.config_manager = config_manager

        # Load from ConfigManager if available
        if config_manager:
            self.processor_config = config_manager.get("processors.semantic_analyzer", default={})
        else:
            self.processor_config = self.config
```

## Logging Integration

```python
from infrastructure import get_logger

class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.logger = get_logger(__name__)

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        self.logger.info("Starting semantic analysis", extra={
            "processor": self.get_processor_name(),
            "block_count": len(extraction_result.content_blocks),
        })

        # Processing logic...

        self.logger.info("Semantic analysis complete", extra={
            "entities_found": total_entities,
            "processing_time_seconds": elapsed_time,
        })
```

---

# Next Steps - Immediate Action Guide

**Status**: Foundation Complete ✓ - Ready to Build
**Date**: 2025-10-29
**Priority**: Start with Week 1 (DocxExtractor + Pipeline MVP)

---

## 🎯 Recommended Starting Point

### Build DocxExtractor First (Week 1)

**Why this approach?**
- ✅ Validates architecture with real implementation
- ✅ Discovers actual infrastructure needs
- ✅ Provides working demo by end of week
- ✅ Sets patterns for all future extractors
- ✅ De-risks before parallelization

**Alternative**: Build infrastructure first
- ⚠️ Risk of over-engineering
- ⚠️ Might build wrong infrastructure
- ⚠️ No validation until later
- ⚠️ Delays visible progress

---

## 📋 Week 1 Checklist

### Day 1: DocxExtractor Core (8 hours)

**Setup (1 hour)**
```bash
# 1. Verify foundation works
cd /c/Users/Andrew/Documents/AI\ ideas\ for\ fun\ and\ work/Prompt\ Research/Data\ Extraction/data-extractor-tool
python examples/minimal_extractor.py
python examples/minimal_processor.py

# 2. Create directory structure
mkdir -p src/extractors
touch src/extractors/__init__.py
touch src/extractors/docx_extractor.py

# 3. Install dependencies
pip install python-docx pytest ruff bandit
```

**Implementation (3 hours)**
Create `src/extractors/docx_extractor.py`:
```python
from pathlib import Path
from docx import Document
from core import BaseExtractor, ExtractionResult, ContentBlock, ContentType, Position

class DocxExtractor(BaseExtractor):
    """Extract content from DOCX files."""

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is DOCX."""
        return file_path.suffix.lower() == ".docx"

    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract content blocks from DOCX file."""
        # Validate file
        is_valid, errors = self.validate_file(file_path)
        if not is_valid:
            return ExtractionResult(success=False, errors=tuple(errors))

        try:
            # Open document
            doc = Document(file_path)
            blocks = []

            # Extract paragraphs
            for idx, para in enumerate(doc.paragraphs):
                if not para.text.strip():
                    continue

                # Determine type (heading vs paragraph)
                block_type = (
                    ContentType.HEADING
                    if para.style.name.startswith("Heading")
                    else ContentType.PARAGRAPH
                )

                block = ContentBlock(
                    block_type=block_type,
                    content=para.text,
                    position=Position(sequence_index=idx),
                    metadata={
                        "style": para.style.name,
                        "is_bold": para.runs[0].bold if para.runs else False,
                    }
                )
                blocks.append(block)

            # TODO: Add table extraction (Day 2-3)
            # TODO: Add image extraction (Day 2-3)

            return ExtractionResult(
                content_blocks=tuple(blocks),
                success=True,
                source_metadata={"file_path": str(file_path)}
            )

        except Exception as e:
            return ExtractionResult(
                success=False,
                errors=(str(e),)
            )
```

**Testing (2 hours)**
Create `tests/test_docx_extractor.py`:
```python
import pytest
from pathlib import Path
from src.extractors.docx_extractor import DocxExtractor

def test_docx_extractor_basic():
    """Test basic DOCX extraction."""
    extractor = DocxExtractor()

    # Create test file (or use existing)
    test_file = Path("tests/fixtures/simple.docx")
    result = extractor.extract(test_file)

    assert result.success
    assert len(result.content_blocks) > 0
    assert all(block.content for block in result.content_blocks)

def test_docx_extractor_empty():
    """Test empty document handling."""
    extractor = DocxExtractor()
    test_file = Path("tests/fixtures/empty.docx")
    result = extractor.extract(test_file)

    assert result.success
    assert len(result.content_blocks) == 0

def test_docx_extractor_invalid():
    """Test invalid file handling."""
    extractor = DocxExtractor()
    result = extractor.extract(Path("nonexistent.docx"))

    assert not result.success
    assert len(result.errors) > 0
```

**Documentation (2 hours)**
- Add docstrings to all methods
- Create `src/extractors/README.md`
- Document known limitations

**✅ End of Day 1**: Working DocxExtractor with tests

---

### Days 2-3: Complete DocxExtractor

**Table Extraction** (4 hours)
```python
# Add to extract() method in DocxExtractor
for table in doc.tables:
    rows = []
    for row in table.rows:
        cells = [cell.text for cell in row.cells]
        rows.append(cells)

    block = ContentBlock(
        block_type=ContentType.TABLE,
        content="",  # Tables stored in metadata
        position=Position(sequence_index=len(blocks)),
        metadata={
            "rows": rows,
            "num_rows": len(rows),
            "num_cols": len(rows[0]) if rows else 0
        }
    )
    blocks.append(block)
```

**Image Extraction** (3 hours)
```python
# Add to extract() method
from docx.oxml import CT_Blip

for rel in doc.part.rels.values():
    if "image" in rel.target_ref:
        block = ContentBlock(
            block_type=ContentType.IMAGE,
            content="",
            position=Position(sequence_index=len(blocks)),
            metadata={
                "image_id": rel.rId,
                "image_type": rel.target_ref.split(".")[-1],
                "embedded": True
            }
        )
        blocks.append(block)
```

**Edge Cases** (4 hours)
- Empty documents
- Corrupted files
- Large documents (100+ pages)
- Documents with only images
- Documents with complex formatting

**✅ End of Day 3**: Complete DocxExtractor

---

### Days 4-5: Minimal Pipeline

**MetadataAggregator** (3 hours)
Create `src/processors/metadata_aggregator.py`:
```python
from core import BaseProcessor, ProcessingResult, ContentBlock

class MetadataAggregator(BaseProcessor):
    """Aggregate statistics about extracted content."""

    def process(self, extraction_result) -> ProcessingResult:
        """Compute metadata statistics."""
        blocks = extraction_result.content_blocks

        total_words = sum(
            len(block.content.split())
            for block in blocks
            if block.content
        )

        total_chars = sum(
            len(block.content)
            for block in blocks
            if block.content
        )

        return ProcessingResult(
            content_blocks=blocks,  # Pass through unchanged
            success=True,
            stage_metadata={
                "total_blocks": len(blocks),
                "total_words": total_words,
                "total_characters": total_chars,
                "block_types": {
                    bt.value: sum(1 for b in blocks if b.block_type == bt)
                    for bt in set(b.block_type for b in blocks)
                }
            }
        )
```

**JsonFormatter** (3 hours)
Create `src/formatters/json_formatter.py`:
```python
import json
from dataclasses import asdict
from core import BaseFormatter, FormattedOutput

class JsonFormatter(BaseFormatter):
    """Format extraction results as JSON."""

    def get_format_type(self) -> str:
        return "json"

    def format(self, processing_result) -> FormattedOutput:
        """Convert to JSON format."""
        data = {
            "success": processing_result.success,
            "metadata": processing_result.stage_metadata,
            "content_blocks": [
                {
                    "block_id": str(block.block_id),
                    "block_type": block.block_type.value,
                    "content": block.content[:200],  # Truncate for readability
                    "position": asdict(block.position) if block.position else None,
                    "metadata": block.metadata
                }
                for block in processing_result.content_blocks
            ]
        }

        return FormattedOutput(
            content=json.dumps(data, indent=2),
            format_type="json",
            success=True
        )
```

**Simple Pipeline** (4 hours)
Create `examples/demo_pipeline.py`:
```python
from pathlib import Path
from src.extractors.docx_extractor import DocxExtractor
from src.processors.metadata_aggregator import MetadataAggregator
from src.formatters.json_formatter import JsonFormatter

def run_pipeline(input_file: Path):
    """Run simple extraction pipeline."""
    print(f"Processing {input_file}...")

    # Step 1: Extract
    extractor = DocxExtractor()
    extraction_result = extractor.extract(input_file)

    if not extraction_result.success:
        print(f"[ERROR] Extraction failed: {extraction_result.errors}")
        return

    print(f"  ✓ Extracted {len(extraction_result.content_blocks)} blocks")

    # Step 2: Process
    processor = MetadataAggregator()
    processing_result = processor.process(extraction_result)

    stats = processing_result.stage_metadata
    print(f"  ✓ Words: {stats['total_words']}, Chars: {stats['total_characters']}")

    # Step 3: Format
    formatter = JsonFormatter()
    formatted_output = formatter.format(processing_result)

    # Step 4: Save
    output_file = input_file.with_suffix(".json")
    output_file.write_text(formatted_output.content)

    print(f"  ✓ Output saved to {output_file}")
    print(f"\n[SUCCESS] Pipeline complete!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python demo_pipeline.py <input.docx>")
        sys.exit(1)

    run_pipeline(Path(sys.argv[1]))
```

**Testing** (6 hours)
- End-to-end tests
- Multiple test documents
- Error scenarios
- Performance testing

**✅ End of Week 1**: Working pipeline demo

---

## 🚀 Week 1 Demo

```bash
# Run the pipeline
python examples/demo_pipeline.py sample.docx

# Expected output:
# Processing sample.docx...
#   ✓ Extracted 15 blocks
#   ✓ Words: 432, Chars: 2847
#   ✓ Output saved to sample.json
#
# [SUCCESS] Pipeline complete!

# View the output
cat sample.json
```

---

## 📊 Week 1 Success Criteria

- [ ] DocxExtractor extracts text, tables, images
- [ ] MetadataAggregator computes statistics
- [ ] JsonFormatter produces valid JSON
- [ ] Simple pipeline chains all three
- [ ] Tests pass with >80% coverage
- [ ] Demo ready for stakeholders
- [ ] Infrastructure needs documented

---

## 🔄 What Happens Next?

### Week 2: Infrastructure Formalization

Based on Week 1 learnings, build:
- **ConfigManager** - Settings management
- **LoggingFramework** - Structured logging
- **ErrorHandling** - Exception hierarchy
- **ProgressTracking** - Progress callbacks
- **Testing Framework** - Test utilities

### Week 3-4: Parallel Development

With infrastructure in place:
- **5 Teams** work independently
- **MCP Server** coordinates artifacts
- **Daily Reviews** catch integration issues
- **Complete MVP** by end of Week 4

---

## 🎓 Key Learnings to Document

During Week 1 implementation, document:

1. **Infrastructure Needs**
   - What configuration is needed?
   - What should be logged?
   - What errors need special handling?
   - What progress information is useful?

2. **Testing Patterns**
   - What test utilities would help?
   - What fixtures are needed?
   - What assertions are common?

3. **Common Patterns**
   - Code patterns to reuse
   - Boilerplate to extract
   - Helper functions needed

4. **Lessons Learned**
   - What worked well?
   - What was harder than expected?
   - What would you do differently?

This information drives Week 2 infrastructure design.

---

## 📚 Reference Documents

### Before Starting
- **EXECUTIVE_SUMMARY.md** - High-level overview (5 min read)
- **COORDINATION_PLAN.md** - Detailed development plan (23 pages)
- **ROADMAP_VISUAL.md** - Mermaid diagrams and timelines

### During Implementation
- **FOUNDATION.md** - Data models and interfaces
- **GETTING_STARTED.md** - Implementation patterns
- **QUICK_REFERENCE.md** - API cheat sheet

### For Examples
- **examples/minimal_extractor.py** - Reference extractor
- **examples/minimal_processor.py** - Reference processor

---

## 🛠️ Tools Available

### MCP Server Scripts

```bash
# Load NPL definitions
npl-load c "syntax,agent" --skip ""

# Load persona
npl-persona get alice-developer

# Dump files for context
dump-files src/extractors --glob "*.py"

# View directory structure
git-tree src/
```

### MCP Artifact Management

```bash
# Create artifact (via MCP tools)
# - Store design docs
# - Version implementations
# - Track reviews
# - Share reports
```

---

## ❓ Decision Points

### Choice 1: Start with DocxExtractor or Infrastructure?

**Recommended**: DocxExtractor (spike approach)
- Validates architecture
- Discovers real needs
- Working demo Week 1

**Alternative**: Infrastructure first
- Risk of over-engineering
- No validation until later
- Delays visible progress

### Choice 2: Test Data Source?

**Options**:
1. Use existing `test-files-assesses-extraction-tool/` directory
2. Generate synthetic test files
3. Use real documents (anonymized)

**Recommended**: Use existing files, supplement with synthetic

### Choice 3: Scope for Week 1?

**Minimal Viable**:
- Text extraction only
- Basic pipeline
- Simple tests

**Comprehensive** (Recommended):
- Text + tables + images
- Complete pipeline
- Edge cases + tests
- Sets pattern for future

---

## 💡 Tips for Success

### Development Tips

1. **Start Simple**: Get basic text extraction working first
2. **Test Early**: Write tests as you go
3. **Document Why**: Explain design decisions
4. **Use Foundation**: Follow patterns from examples
5. **Stay Immutable**: Never modify ContentBlock, create new

### Testing Tips

1. **Create Fixtures**: Build test file library early
2. **Test Edge Cases**: Empty, corrupted, large files
3. **Use Assertions**: Leverage pytest's assertion introspection
4. **Mock When Needed**: But prefer integration tests

### Documentation Tips

1. **Docstrings First**: Write before implementing
2. **Examples Help**: Show actual usage
3. **Document Limits**: Be honest about constraints
4. **Update README**: Keep directory READMEs current

---

## 🎯 Your Mission (If You Choose to Accept)

**Build Week 1 deliverables**:
1. Complete DocxExtractor (text, tables, images)
2. MetadataAggregator processor
3. JsonFormatter output
4. Simple pipeline demo
5. Comprehensive tests
6. Documentation

**Success means**:
- Working demo by Friday
- Architecture validated
- Infrastructure needs clear
- Ready for Week 2

---

## 🚦 Getting Started (Right Now)

### Option 1: Dive In (Recommended)

```bash
cd /c/Users/Andrew/Documents/AI\ ideas\ for\ fun\ and\ work/Prompt\ Research/Data\ Extraction/data-extractor-tool

# Verify foundation
python examples/minimal_extractor.py

# Create structure
mkdir -p src/extractors tests/fixtures
touch src/extractors/__init__.py

# Install deps
pip install python-docx pytest

# Start building!
code src/extractors/docx_extractor.py
```

### Option 2: Plan First

1. Review COORDINATION_PLAN.md
2. Read FOUNDATION.md
3. Study examples/
4. Then start implementing

### Option 3: Discuss

- Review this plan
- Ask questions
- Adjust priorities
- Then execute

---

## 📞 Support Resources

### Documentation
- All planning docs in project root
- Foundation docs in `docs/` (if exists)
- Examples in `examples/`

### MCP Server
- Artifact management
- Review system
- Chat rooms
- Script tools

### Foundation
- Working examples validated
- Clear interfaces
- Type-safe contracts
- Immutable models

---

## ✅ Next Action

**Choose one**:

1. **Start building** - Begin DocxExtractor implementation
2. **Review plan** - Discuss coordination strategy
3. **Adjust priorities** - Modify Week 1 scope
4. **Ask questions** - Clarify anything

**Default recommendation**: Start building DocxExtractor (Option 1)

---

**🚀 The foundation is solid. Let's build something amazing!**

---

## Document Metadata

**Version**: 1.0
**Date**: 2025-10-29
**Purpose**: Immediate action guide for Week 1
**Audience**: Developer starting Week 1 work
**Related**: COORDINATION_PLAN.md, EXECUTIVE_SUMMARY.md
**Status**: Ready for execution

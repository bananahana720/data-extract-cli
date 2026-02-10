# Performance Considerations

## Target Performance (NFR-P1)
- **100 mixed files in <10 minutes** (sustained throughput: ~10 files/min)
- **Individual file processing**: <5 seconds (excluding OCR)
- **OCR processing**: <10 seconds per scanned page
- **Similarity matrix**: <5 minutes for 1,000 documents

## Memory Efficiency (NFR-P2)
- **Max memory footprint**: 2GB during batch processing
- **Streaming architecture**: Process files one at a time, release memory after each
- **Sparse matrices**: Use scipy sparse matrices for TF-IDF vectors (memory efficient)
- **Chunked processing**: Don't load entire document corpus into RAM

## Optimization Strategies
- **Parallel processing**: Use `concurrent.futures` for I/O-bound tasks (file reading)
  - ThreadPoolExecutor for I/O (default: 4 workers)
  - ProcessPoolExecutor for CPU-bound (semantic analysis) if needed
- **Lazy loading**: Don't load spaCy model until first use
- **Vectorizer caching**: Fit TF-IDF vectorizer once, reuse for all documents
- **Progressive output**: Write chunks incrementally, don't buffer all in memory

## Bottleneck Analysis
- **Slowest operations**:
  1. OCR (pytesseract) - 10s per page
  2. spaCy sentence segmentation - ~0.5s per document
  3. TF-IDF vectorization - ~1s per 100 documents
- **Optimization priority**: OCR preprocessing (quality/speed tradeoff)

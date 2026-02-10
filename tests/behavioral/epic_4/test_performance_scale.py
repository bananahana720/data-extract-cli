"""BT-004: Performance at Scale Test.

This behavioral test validates that the semantic pipeline can process
enterprise-scale document volumes within acceptable resource constraints.
"""

import gc
import json
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import psutil
import pytest
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

pytestmark = [
    pytest.mark.P2,
    pytest.mark.behavioral,
    pytest.mark.semantic,
    pytest.mark.performance,
]


class SemanticPipeline:
    """Complete semantic processing pipeline for scale testing."""

    def __init__(self, seed: int = 42):
        """Initialize the semantic pipeline.

        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            use_idf=True,
            dtype=np.float32,  # Use float32 for memory efficiency
        )
        self.lsa = TruncatedSVD(n_components=100, random_state=seed)
        self.vectors = None
        self.similarity_matrix = None
        self.success = False

    def process_batch(self, documents: List[str]) -> "SemanticPipelineResult":
        """Process a batch of documents through the complete pipeline.

        Args:
            documents: List of document texts.

        Returns:
            Processing result with vectors and similarity matrix.
        """
        try:
            # TF-IDF vectorization
            tfidf_vectors = self.vectorizer.fit_transform(documents)

            # LSA dimensionality reduction
            lsa_vectors = self.lsa.fit_transform(tfidf_vectors)

            # Compute similarity matrix (sparse for efficiency)
            # For 10K docs, full matrix would be 100M entries
            # We'll compute on-demand or sample for testing
            similarity_sample = self._compute_similarity_sample(lsa_vectors)

            self.vectors = lsa_vectors
            self.similarity_matrix = similarity_sample
            self.success = True

            return SemanticPipelineResult(
                success=True,
                vectors=lsa_vectors,
                similarity_matrix=similarity_sample,
                tfidf_features=self.vectorizer.get_feature_names_out(),
                lsa_components=self.lsa.components_,
            )

        except Exception as e:
            return SemanticPipelineResult(success=False, error=str(e))

    def _compute_similarity_sample(
        self, vectors: np.ndarray, sample_size: int = 1000
    ) -> np.ndarray:
        """Compute similarity matrix for a sample of documents.

        Args:
            vectors: Document vectors.
            sample_size: Number of documents to sample.

        Returns:
            Similarity matrix for sampled documents.
        """
        n_docs = vectors.shape[0]
        if n_docs <= sample_size:
            # Compute full similarity matrix if small enough
            return cosine_similarity(vectors)
        else:
            # Sample for memory efficiency in testing
            indices = np.random.choice(n_docs, sample_size, replace=False)
            sampled_vectors = vectors[indices]
            return cosine_similarity(sampled_vectors)


class SemanticPipelineResult:
    """Result container for semantic pipeline processing."""

    def __init__(
        self,
        success: bool,
        vectors=None,
        similarity_matrix=None,
        tfidf_features=None,
        lsa_components=None,
        error=None,
    ):
        """Initialize the result container.

        Args:
            success: Whether processing succeeded.
            vectors: Document vectors.
            similarity_matrix: Document similarity matrix.
            tfidf_features: TF-IDF feature names.
            lsa_components: LSA component matrix.
            error: Error message if failed.
        """
        self.success = success
        self.vectors = vectors
        self.similarity_matrix = similarity_matrix
        self.tfidf_features = tfidf_features
        self.lsa_components = lsa_components
        self.error = error

    def to_dict(self) -> Dict:
        """Convert result to dictionary for serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "success": self.success,
            "n_documents": self.vectors.shape[0] if self.vectors is not None else 0,
            "n_features": len(self.tfidf_features) if self.tfidf_features is not None else 0,
            "n_components": self.lsa_components.shape[0] if self.lsa_components is not None else 0,
            "error": self.error,
        }


class TestScalePerformance:
    """Behavioral test for performance at scale."""

    @pytest.fixture
    def large_corpus_generator(self):
        """Generator for creating large document corpus.

        Returns:
            Function to generate corpus of specified size.
        """

        def generate(count: int = 10000) -> List[str]:
            """Generate synthetic audit documents.

            Args:
                count: Number of documents to generate.

            Returns:
                List of document texts.
            """
            # Load semantic corpus as base
            corpus_path = Path(__file__).parent.parent.parent / "fixtures/semantic/corpus"
            corpus_path.mkdir(parents=True, exist_ok=True)

            # Define document templates for variety
            templates = [
                # IT Security templates
                """Security Policy Document {id}
                Access control requirements for system {id}.
                Multi-factor authentication mandatory.
                Quarterly security reviews required.
                Incident response procedures defined.
                Data encryption standards enforced.
                Network segmentation implemented.
                Vulnerability scanning monthly.
                Patch management process active.
                Security awareness training required.
                """,
                # Financial Controls templates
                """Financial Control Document {id}
                SOX compliance requirements section {id}.
                Internal controls assessment procedures.
                Segregation of duties matrix defined.
                Journal entry approval workflow.
                Account reconciliation monthly.
                Budget variance analysis required.
                Procurement controls implemented.
                Fraud detection mechanisms active.
                Audit trail maintenance mandatory.
                """,
                # Compliance templates
                """Compliance Policy Document {id}
                GDPR requirements section {id}.
                Data retention policy defined.
                Privacy impact assessments required.
                Third party compliance monitoring.
                Regulatory change management active.
                Data classification standards enforced.
                Legal hold procedures documented.
                Records retention schedule maintained.
                Compliance metrics reporting monthly.
                """,
                # Risk Management templates
                """Risk Assessment Document {id}
                Risk category analysis for area {id}.
                Likelihood and impact assessment.
                Risk mitigation strategies defined.
                Risk monitoring procedures active.
                Key risk indicators tracked.
                Risk appetite statements approved.
                Control effectiveness testing.
                Risk register maintenance required.
                Executive risk reporting quarterly.
                """,
                # Business Continuity templates
                """Business Continuity Plan {id}
                Recovery objectives for system {id}.
                Disaster recovery procedures defined.
                Backup strategies implemented.
                Crisis communication plan active.
                Business impact analysis completed.
                Alternate site arrangements made.
                Recovery testing schedule defined.
                Supply chain continuity planning.
                Emergency contact lists maintained.
                """,
                # Audit templates
                """Internal Audit Report {id}
                Audit findings for process {id}.
                Control deficiencies identified.
                Management action plans required.
                Follow-up procedures defined.
                Risk-based audit approach used.
                Workpaper documentation standards.
                Finding severity ratings assigned.
                Remediation tracking active.
                Audit committee reporting quarterly.
                """,
            ]

            documents = []
            template_count = len(templates)

            # Add variation to documents
            variations = [
                "Updated version with enhanced controls.",
                "Revised to include new regulatory requirements.",
                "Modified based on audit recommendations.",
                "Expanded coverage for cloud environments.",
                "Includes remote work considerations.",
                "Aligned with industry best practices.",
                "Incorporates lessons learned from incidents.",
                "Enhanced monitoring and reporting added.",
                "Automation capabilities integrated.",
                "Risk-based approach implemented.",
            ]

            for i in range(count):
                # Select template cyclically
                template = templates[i % template_count]
                doc = template.format(id=i)

                # Add variations to some documents
                if i % 3 == 0:
                    doc += "\n" + variations[i % len(variations)]

                # Add some randomization for realistic variety
                if i % 5 == 0:
                    doc += f"\nRevision date: 2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"

                if i % 7 == 0:
                    doc += "\nPriority: High\nCompliance Required: Yes"

                documents.append(doc)

            # Save sample for reproducibility
            sample_file = corpus_path / "scale_test_sample.json"
            with open(sample_file, "w") as f:
                json.dump(documents[:100], f, indent=2)

            return documents

        return generate

    def test_bt004_scale_performance_10k_documents(self, large_corpus_generator):
        """Test BT-004: Process 10K documents within resource constraints.

        Given: 10,000 document corpus
        When: Processing through complete semantic pipeline
        Then: <60 seconds AND <500MB memory

        Behavioral Outcome: System remains responsive and stable
        at enterprise scale.
        """
        # Arrange
        documents = large_corpus_generator(count=10000)
        pipeline = SemanticPipeline()
        process = psutil.Process()

        # Force garbage collection before starting
        gc.collect()

        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Act
        start_time = time.time()
        result = pipeline.process_batch(documents)
        elapsed_time = time.time() - start_time

        # Measure peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - baseline_memory

        # Force garbage collection to test for memory leaks
        gc.collect()
        post_gc_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_after_gc = post_gc_memory - baseline_memory

        # Calculate throughput metrics
        throughput_docs_per_sec = 10000 / elapsed_time if elapsed_time > 0 else 0
        memory_per_doc_kb = (memory_used * 1024) / 10000 if memory_used > 0 else 0

        # Validate output completeness
        assert result.success, f"Pipeline failed to process documents: {result.error}"
        assert result.vectors.shape[0] == 10000, "Not all documents processed"
        assert result.similarity_matrix.shape[0] > 0, "No similarity matrix generated"
        assert len(result.tfidf_features) > 0, "No TF-IDF features extracted"
        assert result.lsa_components.shape[0] == 100, "Incorrect LSA components"

        # Check for memory leaks
        memory_leak = memory_after_gc - memory_used
        assert abs(memory_leak) < 50, f"Potential memory leak detected: {memory_leak:.1f}MB"

        # Log performance metrics
        self._log_performance_metrics(
            {
                "documents_processed": 10000,
                "elapsed_seconds": elapsed_time,
                "memory_mb": memory_used,
                "memory_after_gc_mb": memory_after_gc,
                "throughput_docs_per_sec": throughput_docs_per_sec,
                "memory_per_doc_kb": memory_per_doc_kb,
                "tfidf_features": len(result.tfidf_features),
                "lsa_components": result.lsa_components.shape[0],
                "vector_dimensions": result.vectors.shape[1],
            }
        )

        # Assert behavioral constraints
        assert elapsed_time < 60, f"Processing time {elapsed_time:.1f}s exceeds 60s limit"
        assert memory_used < 500, f"Memory usage {memory_used:.0f}MB exceeds 500MB limit"

    def test_bt004_incremental_processing_performance(self, large_corpus_generator):
        """Test incremental batch processing for memory efficiency.

        Given: 10K documents in 1K batches
        When: Processing incrementally
        Then: Memory stays under 200MB per batch

        Behavioral Outcome: System can handle continuous stream processing.
        """
        # Arrange
        batch_size = 1000
        n_batches = 10
        pipeline = SemanticPipeline()
        process = psutil.Process()

        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        batch_times = []
        batch_memories = []
        all_vectors = []

        # Act - Process in batches
        for i in range(n_batches):
            batch_docs = large_corpus_generator(count=batch_size)

            batch_start = time.time()
            result = pipeline.process_batch(batch_docs)
            batch_time = time.time() - batch_start

            batch_memory = process.memory_info().rss / 1024 / 1024 - baseline_memory

            batch_times.append(batch_time)
            batch_memories.append(batch_memory)
            all_vectors.append(result.vectors)

            assert result.success, f"Batch {i} failed"
            assert batch_memory < 200, f"Batch {i} memory {batch_memory:.0f}MB exceeds 200MB"

        # Aggregate metrics
        total_time = sum(batch_times)
        max_memory = max(batch_memories)
        avg_batch_time = np.mean(batch_times)
        avg_batch_memory = np.mean(batch_memories)

        # Log incremental processing metrics
        print("\n" + "=" * 60)
        print("BT-004: Incremental Processing Performance")
        print("=" * 60)
        print(f"Total documents: {batch_size * n_batches}")
        print(f"Batch size: {batch_size}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Avg batch time: {avg_batch_time:.2f}s")
        print(f"Max memory: {max_memory:.0f}MB")
        print(f"Avg batch memory: {avg_batch_memory:.0f}MB")
        print("=" * 60)

        assert total_time < 90, f"Total incremental time {total_time:.1f}s exceeds 90s"
        assert max_memory < 200, f"Max batch memory {max_memory:.0f}MB exceeds 200MB"

    def _log_performance_metrics(self, metrics: Dict):
        """Log performance test metrics.

        Args:
            metrics: Dictionary of performance metrics.
        """
        print("\n" + "=" * 60)
        print("BT-004: Scale Performance Metrics")
        print("=" * 60)
        print(f"Documents processed:     {metrics['documents_processed']}")
        print(f"Processing time:         {metrics['elapsed_seconds']:.2f} seconds")
        print(f"Memory usage:            {metrics['memory_mb']:.1f} MB")
        print(f"Memory after GC:         {metrics['memory_after_gc_mb']:.1f} MB")
        print(f"Throughput:              {metrics['throughput_docs_per_sec']:.1f} docs/sec")
        print(f"Memory per doc:          {metrics['memory_per_doc_kb']:.2f} KB")
        print(f"TF-IDF features:         {metrics['tfidf_features']}")
        print(f"LSA components:          {metrics['lsa_components']}")
        print(f"Vector dimensions:       {metrics['vector_dimensions']}")
        print("=" * 60)

    def _profile_bottlenecks(self, documents: List[str]) -> Dict:
        """Profile performance bottlenecks in the pipeline.

        Args:
            documents: Test documents.

        Returns:
            Profiling results.
        """
        pipeline = SemanticPipeline()
        profiling = {}

        # Profile TF-IDF
        start = time.time()
        vectorizer = TfidfVectorizer(max_features=5000)
        tfidf_vectors = vectorizer.fit_transform(documents)
        profiling["tfidf_time"] = time.time() - start

        # Profile LSA
        start = time.time()
        lsa = TruncatedSVD(n_components=100)
        lsa_vectors = lsa.fit_transform(tfidf_vectors)
        profiling["lsa_time"] = time.time() - start

        # Profile similarity computation
        start = time.time()
        sample_size = min(1000, len(documents))
        sample_vectors = lsa_vectors[:sample_size]
        _ = cosine_similarity(sample_vectors)
        profiling["similarity_time"] = time.time() - start
        profiling["similarity_sample_size"] = sample_size

        return profiling

"""
Semantic corpus fixtures for testing.

Provides reusable test corpora with varied content types for semantic analysis testing.
These fixtures support Epic 4 semantic feature development and validation.
"""

from typing import Dict, List


def get_technical_corpus() -> List[str]:
    """
    Generate technical documentation corpus.

    Returns:
        List of technical documents for testing
    """
    return [
        """The extraction system follows a modular architecture. Each processing stage
        has one clear job and a stable interface. Teams can test stages alone, then
        chain them in a full run. This design keeps changes local and makes failures
        easy to trace during review.""",
        """Engineers use ML and AI methods to map raw text into useful features.
        The pipeline can run TF-IDF, LSA, and basic NLP steps on the same input.
        Each algorithm writes scores and labels that support later search and
        analysis tasks in production tools. Feature calibration uses probabilistic
        normalization and parameter regularization for domain-specific vocabularies.
        This implementation improves data processing quality in the system architecture.""",
        """The service reads PDF, DOCX, XLSX, and PPTX files through one adapter
        layer. A common schema stores body text, headers, tables, and page data.
        Output is exported as JSON or XML so downstream systems can parse it
        without custom rules for every format.""",
        """Performance work focuses on fast I/O and low memory use. The code caches
        repeat reads, uses lazy loading, and streams chunks in order. Benchmarks
        track CPU time, queue wait, and throughput so optimization choices are
        based on data from real document workloads.""",
        """Quality checks run on every build before release. Unit tests, integration
        tests, and validation rules catch drift in extraction behavior. Regression
        suites compare new output with known baselines and block deploys when key
        metrics fall below target. The validation system records data and processing
        checks to verify architecture implementation choices.""",
    ]


def get_business_corpus() -> List[str]:
    """
    Generate business document corpus.

    Returns:
        List of business-oriented documents
    """
    return [
        """The quarterly report shows revenue growth in core markets. Sales rose
        after product updates and better partner coverage. Leaders expect steady
        demand next quarter, but they also track cost pressure and staffing plans
        to protect margin targets across all regions. The plan assumes 8% growth
        in 2026 with modest support cost increases.""",
        """Risk teams review supply, security, and legal exposure each month. They
        rank threats by impact and probability, then assign owners for mitigation
        work. Board updates include open issues, due dates, and control test
        results so actions stay on schedule.""",
        """Customer feedback improved across support and onboarding services. Net
        promoter scores moved up after faster response times and clearer help
        content. Teams now review top complaint themes weekly and tie fixes to
        retention goals and service quality plans.""",
        """Strategic planning links product bets to cash flow and capacity. Managers
        score each initiative on expected return, delivery risk, and team load.
        This process keeps the roadmap focused on high-value work with clear
        milestones and transparent tradeoff decisions.""",
        """Compliance programs require complete records for audits and policy reviews.
        Teams store approvals, exceptions, and evidence in one governed repository.
        Regular checks confirm controls are active and that regulatory deadlines
        are met without repeat findings.""",
    ]


def get_mixed_corpus() -> List[str]:
    """
    Generate mixed content corpus with varied topics and styles.

    Returns:
        List of mixed-content documents
    """
    technical = get_technical_corpus()
    business = get_business_corpus()

    # Additional varied content
    additional = [
        """Natural language processing enables computers to understand and generate
        human language. Applications include chatbots, translation services, and
        sentiment analysis systems.""",
        """Data governance frameworks establish policies for data quality, security,
        and privacy. Master data management ensures consistency across organizational
        systems.""",
        """Cloud computing platforms provide scalable infrastructure for modern
        applications. Serverless architectures reduce operational overhead while
        enabling rapid deployment.""",
    ]

    # Interleave different types
    mixed = []
    for i in range(max(len(technical), len(business), len(additional))):
        if i < len(technical):
            mixed.append(technical[i])
        if i < len(business):
            mixed.append(business[i])
        if i < len(additional):
            mixed.append(additional[i])

    return mixed


def get_edge_case_corpus() -> List[str]:
    """
    Generate corpus with edge cases for testing.

    Returns:
        List of edge case documents
    """
    return [
        # Very short document
        "Data extraction.",
        # Repeated content
        "Test test test. Testing testing testing. Tests tests tests.",
        # Numbers and symbols
        "Revenue: $1,234,567.89 (Q4 2024). Growth: +15.3%. Target: 2025-Q1.",
        # Unicode and special characters
        "International data: 数据提取 (Chinese), données (French), δεδομένα (Greek).",
        # Very long single sentence
        " ".join(["The"] + ["very"] * 100 + ["long sentence continues."]),
        # Empty-like content
        "   \n\n\t  \n   ",
        # Technical jargon heavy
        "TF-IDF LSA SVD NLP ML AI API REST JSON XML HTTP HTTPS SSL TLS DNS.",
    ]


def get_similarity_test_pairs() -> List[Dict[str, any]]:
    """
    Generate document pairs for similarity testing.

    Returns:
        List of document pairs with expected similarity ranges
    """
    return [
        {
            "doc1": "Machine learning enables artificial intelligence applications.",
            "doc2": "AI applications are powered by machine learning algorithms.",
            "expected_similarity": (0.7, 1.0),  # High similarity
            "description": "Semantically similar documents",
        },
        {
            "doc1": "The weather is sunny and warm today.",
            "doc2": "Quantum computing uses qubits for computation.",
            "expected_similarity": (0.0, 0.3),  # Low similarity
            "description": "Unrelated documents",
        },
        {
            "doc1": "Data extraction from PDF documents.",
            "doc2": "Data extraction from PDF documents.",
            "expected_similarity": (0.99, 1.0),  # Identical
            "description": "Identical documents",
        },
        {
            "doc1": "Natural language processing analyzes text data.",
            "doc2": "Text data analysis uses NLP techniques.",
            "expected_similarity": (0.5, 0.8),  # Moderate similarity
            "description": "Related but different phrasing",
        },
    ]


def generate_large_corpus(num_docs: int = 1000, words_per_doc: int = 100) -> List[str]:
    """
    Generate a large corpus for performance testing.

    Args:
        num_docs: Number of documents to generate
        words_per_doc: Approximate words per document

    Returns:
        Large corpus for performance testing
    """
    templates = [
        "The {} system processes {} with high efficiency and accuracy.",
        "Advanced {} techniques enable {} in enterprise environments.",
        "Quality {} ensures reliable {} across all components.",
        "Performance {} optimizes {} for scalable operations.",
        "Security {} protects {} from potential threats.",
    ]

    topics = [
        "data extraction",
        "machine learning",
        "natural language",
        "document processing",
        "semantic analysis",
        "information retrieval",
        "text mining",
        "content management",
        "knowledge graphs",
        "entity recognition",
    ]

    operations = [
        "documents",
        "datasets",
        "workflows",
        "pipelines",
        "transformations",
        "computations",
        "analyses",
        "validations",
        "integrations",
        "deployments",
    ]

    corpus = []
    for i in range(num_docs):
        doc_parts = []
        word_count = 0

        while word_count < words_per_doc:
            template = templates[i % len(templates)]
            topic = topics[i % len(topics)]
            operation = operations[(i + 1) % len(operations)]

            sentence = template.format(topic, operation)
            doc_parts.append(sentence)
            word_count += len(sentence.split())

        corpus.append(" ".join(doc_parts))

    return corpus


# Corpus characteristics for documentation
CORPUS_CHARACTERISTICS = {
    "technical": {
        "size": 5,
        "avg_words": 45,
        "vocabulary": "technical, enterprise, architecture",
        "diversity": "medium",
    },
    "business": {
        "size": 5,
        "avg_words": 42,
        "vocabulary": "business, finance, compliance",
        "diversity": "medium",
    },
    "mixed": {
        "size": 13,
        "avg_words": 43,
        "vocabulary": "technical + business + general",
        "diversity": "high",
    },
    "edge_cases": {
        "size": 7,
        "avg_words": "varies (2-100+)",
        "vocabulary": "varied, includes unicode",
        "diversity": "extreme",
    },
}


# Export functions
__all__ = [
    "get_technical_corpus",
    "get_business_corpus",
    "get_mixed_corpus",
    "get_edge_case_corpus",
    "get_similarity_test_pairs",
    "generate_large_corpus",
    "CORPUS_CHARACTERISTICS",
]

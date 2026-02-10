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
        """The enterprise data extraction pipeline leverages modular architecture patterns
        to ensure scalability and maintainability. Each processing stage implements
        well-defined interfaces that enable seamless integration and testing.""",
        """Machine learning algorithms transform unstructured text data into structured
        representations suitable for downstream analysis. Feature extraction techniques
        include TF-IDF vectorization and latent semantic analysis.""",
        """Document processing systems must handle diverse file formats including PDF,
        DOCX, XLSX, and PPTX. The extraction layer abstracts format-specific complexity
        through a unified interface.""",
        """Performance optimization strategies include caching frequently accessed data,
        implementing lazy evaluation patterns, and utilizing sparse matrix representations
        for efficient memory usage.""",
        """Quality assurance frameworks validate extraction accuracy through automated
        testing pipelines. Regression tests ensure consistent behavior across software
        updates and dependency changes.""",
    ]


def get_business_corpus() -> List[str]:
    """
    Generate business document corpus.

    Returns:
        List of business-oriented documents
    """
    return [
        """The quarterly financial report indicates strong revenue growth driven by
        increased market penetration and successful product launches. Operating margins
        improved due to operational efficiency initiatives.""",
        """Risk management protocols require regular assessment of potential threats
        to business continuity. Mitigation strategies include diversification of
        supply chains and implementation of robust cybersecurity measures.""",
        """Customer satisfaction metrics demonstrate consistent improvement across
        all service categories. Net promoter scores increased following the deployment
        of enhanced support systems.""",
        """Strategic initiatives focus on digital transformation and automation of
        core business processes. Investment in technology infrastructure enables
        competitive advantage in rapidly evolving markets.""",
        """Compliance with regulatory requirements necessitates comprehensive audit
        trails and documentation. Internal controls ensure adherence to industry
        standards and legal obligations.""",
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

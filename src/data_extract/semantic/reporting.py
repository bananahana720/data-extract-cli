"""Report generation for semantic analysis results.

Implements AC-4.5-5: HTML/JSON reports with similarity matrices,
cluster visualizations, quality distributions.

Implements AC-4.5-8: Export in multiple formats (JSON, CSV, HTML, graph).
"""

import json
from datetime import datetime
from typing import Any, Dict


def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate comprehensive HTML report from analysis results.

    Args:
        results: Analysis results dictionary from semantic pipeline

    Returns:
        Self-contained HTML string with inline CSS
    """
    summary = results.get("summary", {})
    similarity = results.get("similarity", {})
    topics = results.get("topics", {})
    clusters = results.get("clusters", {})
    quality = results.get("quality", {})
    config = results.get("config", {})

    # Format topics for display
    topics_html = ""
    for topic_idx, terms in sorted(
        topics.items(), key=lambda x: int(x[0]) if isinstance(x[0], (int, str)) else 0
    ):
        terms_list = terms if isinstance(terms, list) else []
        topics_html += f"""
        <div class="topic-card">
            <h4>Topic {topic_idx}</h4>
            <p>{', '.join(terms_list[:10])}</p>
        </div>
        """

    # Format duplicate groups
    duplicate_groups = similarity.get("duplicate_groups", [])
    duplicates_html = ""
    for idx, group in enumerate(duplicate_groups[:10]):
        members = ", ".join(group[:5]) + ("..." if len(group) > 5 else "")
        duplicates_html += f"""
        <tr>
            <td>Group {idx + 1}</td>
            <td>{len(group)}</td>
            <td>{members}</td>
        </tr>
        """

    # Format quality distribution
    quality_dist = quality.get("distribution", {})
    quality_total = sum(quality_dist.values()) if quality_dist else 1

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic Analysis Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #ca8a04;
            --error: #dc2626;
            --background: #f8fafc;
            --surface: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            background: var(--surface);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        h1 {{
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        .meta {{
            color: var(--muted);
            font-size: 0.875rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--surface);
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            color: var(--primary);
            margin-bottom: 1rem;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .stat {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
        }}
        .stat-label {{
            color: var(--muted);
            font-size: 0.875rem;
        }}
        .section {{
            background: var(--surface);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .section h2 {{
            color: var(--text);
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: var(--background);
            font-weight: 600;
        }}
        .topic-card {{
            background: var(--background);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.75rem;
        }}
        .topic-card h4 {{
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        .progress-bar {{
            height: 24px;
            background: #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
        }}
        .progress-segment {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .high {{ background: var(--success); }}
        .medium {{ background: var(--warning); }}
        .low {{ background: var(--error); }}
        .config-list {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }}
        .config-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem;
            background: var(--background);
            border-radius: 4px;
        }}
        .config-key {{
            color: var(--muted);
        }}
        .config-value {{
            font-weight: 600;
        }}
        footer {{
            text-align: center;
            color: var(--muted);
            padding: 2rem;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Semantic Analysis Report</h1>
            <p class="meta">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Documents</h3>
                <div class="stat">{summary.get('total_chunks', 0)}</div>
                <div class="stat-label">chunks analyzed</div>
            </div>
            <div class="card">
                <h3>Vocabulary</h3>
                <div class="stat">{summary.get('vocabulary_size', 0):,}</div>
                <div class="stat-label">unique terms</div>
            </div>
            <div class="card">
                <h3>Topics</h3>
                <div class="stat">{summary.get('n_components', 0)}</div>
                <div class="stat-label">extracted</div>
            </div>
            <div class="card">
                <h3>Clusters</h3>
                <div class="stat">{summary.get('n_clusters', 0)}</div>
                <div class="stat-label">document groups</div>
            </div>
        </div>

        <div class="section">
            <h2>Quality Distribution</h2>
            <div class="progress-bar">
                <div class="progress-segment high" style="width: {(quality_dist.get('high', 0) / quality_total) * 100:.1f}%">
                    {quality_dist.get('high', 0)} High
                </div>
                <div class="progress-segment medium" style="width: {(quality_dist.get('medium', 0) / quality_total) * 100:.1f}%">
                    {quality_dist.get('medium', 0)} Medium
                </div>
                <div class="progress-segment low" style="width: {(quality_dist.get('low', 0) / quality_total) * 100:.1f}%">
                    {quality_dist.get('low', 0)} Low
                </div>
            </div>
            <p style="margin-top: 1rem; color: var(--muted);">
                Mean quality score: <strong>{quality.get('mean_score', 0):.2f}</strong>
            </p>
        </div>

        <div class="section">
            <h2>Duplicate Analysis</h2>
            <p style="margin-bottom: 1rem;">
                Found <strong>{similarity.get('n_duplicates', 0)}</strong> duplicate groups
            </p>
            {f'''<table>
                <thead>
                    <tr>
                        <th>Group</th>
                        <th>Size</th>
                        <th>Members</th>
                    </tr>
                </thead>
                <tbody>
                    {duplicates_html}
                </tbody>
            </table>''' if duplicate_groups else '<p style="color: var(--muted);">No duplicates found above threshold.</p>'}
        </div>

        <div class="section">
            <h2>Extracted Topics</h2>
            {topics_html if topics else '<p style="color: var(--muted);">No topics extracted.</p>'}
        </div>

        <div class="section">
            <h2>Clustering Results</h2>
            <p>
                Silhouette Score: <strong>{clusters.get('silhouette_score', 0):.3f}</strong>
                <span style="color: var(--muted);">(higher is better, range -1 to 1)</span>
            </p>
        </div>

        <div class="section">
            <h2>Configuration</h2>
            <div class="config-list">
                <div class="config-item">
                    <span class="config-key">TF-IDF Max Features</span>
                    <span class="config-value">{config.get('tfidf_max_features', 'N/A')}</span>
                </div>
                <div class="config-item">
                    <span class="config-key">Similarity Threshold</span>
                    <span class="config-value">{config.get('similarity_threshold', 'N/A')}</span>
                </div>
                <div class="config-item">
                    <span class="config-key">LSA Components</span>
                    <span class="config-value">{config.get('lsa_n_components', 'N/A')}</span>
                </div>
                <div class="config-item">
                    <span class="config-key">Min Quality Score</span>
                    <span class="config-value">{config.get('quality_min_score', 'N/A')}</span>
                </div>
            </div>
        </div>

        <footer>
            <p>Data Extraction Tool - Semantic Analysis Report</p>
            <p>Processing time: {summary.get('processing_time_ms', 0):.2f}ms</p>
        </footer>
    </div>
</body>
</html>
"""
    return html


def generate_csv_report(results: Dict[str, Any]) -> str:
    """Generate CSV report from analysis results.

    Args:
        results: Analysis results dictionary

    Returns:
        CSV string with analysis data
    """
    lines = []

    # Header section
    lines.append("# Semantic Analysis Report")
    lines.append(f"# Generated: {datetime.now().isoformat()}")
    lines.append("")

    # Summary
    summary = results.get("summary", {})
    lines.append("# Summary")
    lines.append("metric,value")
    lines.append(f"total_chunks,{summary.get('total_chunks', 0)}")
    lines.append(f"vocabulary_size,{summary.get('vocabulary_size', 0)}")
    lines.append(f"n_topics,{summary.get('n_components', 0)}")
    lines.append(f"n_clusters,{summary.get('n_clusters', 0)}")
    lines.append(f"processing_time_ms,{summary.get('processing_time_ms', 0):.2f}")
    lines.append("")

    # Quality distribution
    quality = results.get("quality", {})
    dist = quality.get("distribution", {})
    lines.append("# Quality Distribution")
    lines.append("quality_level,count")
    for level, count in dist.items():
        lines.append(f"{level},{count}")
    lines.append(f"mean_score,{quality.get('mean_score', 0):.4f}")
    lines.append("")

    # Duplicate groups
    similarity = results.get("similarity", {})
    duplicate_groups = similarity.get("duplicate_groups", [])
    if duplicate_groups:
        lines.append("# Duplicate Groups")
        lines.append("group_id,size,members")
        for idx, group in enumerate(duplicate_groups):
            members = ";".join(group)
            lines.append(f'{idx},{len(group)},"{members}"')
        lines.append("")

    # Cluster assignments
    clusters = results.get("clusters", {})
    assignments = clusters.get("assignments", [])
    if assignments:
        lines.append("# Cluster Assignments")
        lines.append("document_index,cluster_id")
        for idx, cluster_id in enumerate(assignments):
            lines.append(f"{idx},{cluster_id}")
        lines.append("")

    return "\n".join(lines)


def generate_cluster_html(report: Dict[str, Any]) -> str:
    """Generate HTML report for cluster analysis.

    Args:
        report: Cluster analysis report dictionary

    Returns:
        Self-contained HTML string
    """
    cluster_rows = ""
    for cluster_id in range(report.get("n_clusters", 0)):
        size = report.get("cluster_sizes", {}).get(cluster_id, 0)
        topics = report.get("cluster_topics", {}).get(cluster_id, [])
        members = report.get("cluster_members", {}).get(cluster_id, [])

        cluster_rows += f"""
        <tr>
            <td><strong>Cluster {cluster_id}</strong></td>
            <td>{size}</td>
            <td>{', '.join(topics[:5])}</td>
            <td>{', '.join(members[:3])}{' ...' if len(members) > 3 else ''}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cluster Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2563eb;
            margin-bottom: 1rem;
        }}
        .stats {{
            display: flex;
            gap: 2rem;
            margin: 1.5rem 0;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 8px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #2563eb;
        }}
        .stat-label {{
            color: #64748b;
            font-size: 0.875rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
        }}
        .meta {{
            color: #64748b;
            font-size: 0.875rem;
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cluster Analysis Report</h1>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{report.get('n_documents', 0)}</div>
                <div class="stat-label">Documents</div>
            </div>
            <div class="stat">
                <div class="stat-value">{report.get('n_clusters', 0)}</div>
                <div class="stat-label">Clusters</div>
            </div>
            <div class="stat">
                <div class="stat-value">{report.get('silhouette_score', 0):.3f}</div>
                <div class="stat-label">Silhouette Score</div>
            </div>
        </div>

        <h2>Cluster Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Cluster</th>
                    <th>Size</th>
                    <th>Top Terms</th>
                    <th>Sample Members</th>
                </tr>
            </thead>
            <tbody>
                {cluster_rows}
            </tbody>
        </table>

        <p class="meta">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
    return html


def export_similarity_graph(results: Dict[str, Any], output_format: str = "json") -> str:
    """Export similarity graph in various formats.

    Args:
        results: Analysis results with similarity data
        output_format: Output format (json, csv, dot)

    Returns:
        Formatted graph data
    """
    similarity = results.get("similarity", {})
    statistics = similarity.get("statistics", {})
    similarity_graph = similarity.get("similarity_graph", {}) or {}
    similar_pairs = similarity.get("similar_pairs", []) or []
    duplicate_threshold = float(results.get("config", {}).get("similarity_threshold", 0.95))

    node_ids = set()
    edges: dict[tuple[str, str], dict[str, Any]] = {}

    if isinstance(similarity_graph, dict):
        for source, targets in similarity_graph.items():
            if not isinstance(source, str):
                continue
            node_ids.add(source)
            if not isinstance(targets, list):
                continue
            for target_entry in targets:
                if not isinstance(target_entry, (list, tuple)) or len(target_entry) < 2:
                    continue
                target = str(target_entry[0])
                try:
                    weight = float(target_entry[1])
                except (TypeError, ValueError):
                    weight = 0.0
                node_ids.add(target)
                key = tuple(sorted((source, target)))
                existing = edges.get(key)
                if existing is None or weight > float(existing.get("weight", 0.0)):
                    edges[key] = {
                        "source": key[0],
                        "target": key[1],
                        "weight": weight,
                        "type": "duplicate" if weight >= duplicate_threshold else "related",
                    }

    for pair in similar_pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) < 3:
            continue
        source = str(pair[0])
        target = str(pair[1])
        try:
            weight = float(pair[2])
        except (TypeError, ValueError):
            weight = 0.0
        node_ids.update({source, target})
        key = tuple(sorted((source, target)))
        existing = edges.get(key)
        if existing is None or weight > float(existing.get("weight", 0.0)):
            edges[key] = {
                "source": key[0],
                "target": key[1],
                "weight": weight,
                "type": "duplicate" if weight >= duplicate_threshold else "related",
            }

    # Fallback for legacy payloads that only include duplicate groups.
    if not edges:
        duplicate_groups = similarity.get("duplicate_groups", []) or []
        for group in duplicate_groups:
            if not isinstance(group, list):
                continue
            for member in group:
                node_ids.add(str(member))
            for index, node_a in enumerate(group):
                for node_b in group[index + 1 :]:
                    key = tuple(sorted((str(node_a), str(node_b))))
                    edges[key] = {
                        "source": key[0],
                        "target": key[1],
                        "weight": 1.0,
                        "type": "duplicate",
                    }

    ordered_nodes = [{"id": node_id} for node_id in sorted(node_ids)]
    ordered_edges = sorted(
        edges.values(),
        key=lambda edge: (edge["source"], edge["target"]),
    )

    if output_format == "json":
        graph_data = {
            "nodes": ordered_nodes,
            "edges": ordered_edges,
            "statistics": statistics,
        }
        return json.dumps(graph_data, indent=2)

    if output_format == "csv":
        lines = ["source,target,type,weight"]
        for edge in ordered_edges:
            lines.append(f'{edge["source"]},{edge["target"]},{edge["type"]},{edge["weight"]:.6f}')
        return "\n".join(lines)

    if output_format == "dot":
        lines = ["graph SimilarityGraph {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        for node in ordered_nodes:
            lines.append(f'  "{node["id"]}";')
        for edge in ordered_edges:
            lines.append(
                f'  "{edge["source"]}" -- "{edge["target"]}" '
                f'[label="{edge["weight"]:.3f}", color="{ "red" if edge["type"] == "duplicate" else "gray" }"];'
            )
        lines.append("}")
        return "\n".join(lines)

    return ""

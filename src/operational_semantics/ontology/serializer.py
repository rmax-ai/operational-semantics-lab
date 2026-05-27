"""Serialize RDFLib graphs in various formats."""

from pathlib import Path

from rdflib import Graph

from operational_semantics.ontology.namespace import PREFIX_MAP


class OntologySerializer:
    """Serializes RDFLib graphs to file or string in supported formats."""

    SUPPORTED_FORMATS = {"turtle", "json-ld", "xml", "n3", "nt", "trig"}

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self._bind_prefixes()

    def _bind_prefixes(self) -> None:
        """Bind namespace prefixes for clean serialization."""
        for prefix, ns in PREFIX_MAP.items():
            self.graph.bind(prefix, ns)

    def to_string(self, fmt: str = "turtle") -> str:
        """Serialize the graph to a string."""
        if fmt not in self.SUPPORTED_FORMATS:
            msg = f"Unsupported format: {fmt}. Choose from {self.SUPPORTED_FORMATS}"
            raise ValueError(msg)
        return self.graph.serialize(format=fmt).decode("utf-8") if isinstance(
            self.graph.serialize(format=fmt), bytes
        ) else self.graph.serialize(format=fmt)  # type: ignore[return-value]

    def to_file(self, path: str | Path, fmt: str = "turtle") -> Path:
        """Serialize the graph to a file."""
        path = Path(path)
        content = self.to_string(fmt)
        path.write_text(content, encoding="utf-8")
        return path

"""Configuration management for ContextPacket."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for ContextPacket pipeline."""

    # Chunking parameters
    chunk_size: int = Field(default=512, description="Size of each chunk in tokens")
    chunk_overlap: int = Field(default=256, description="Overlap between chunks (chunk_size/2)")

    # Token budgets
    large_limit: int = Field(default=32000, description="Token limit for large context")
    medium_limit: int = Field(default=16000, description="Token limit for medium context")
    small_limit: int = Field(default=8000, description="Token limit for small context")

    # Scoring
    score_threshold: float | None = Field(default=None, description="Score threshold (null = auto)")
    model_path: str = Field(default="mixedbread-ai/mxbai-rerank-base-v2", description="Path to reranker model")
    batch_size: int = Field(default=32, description="Batch size for scoring")

    # File processing
    include_extensions: list[str] = Field(
        default=[
            "txt", "md", "markdown", "html", "htm", "pdf",
            "py", "c", "cpp", "h", "hpp", "rs", "swift"
        ],
        description="File extensions to process"
    )
    recursive: bool = Field(default=True, description="Recurse into subdirectories")

    # Output
    output_dir: str = Field(default=".", description="Output directory")

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")


def load_config(config_path: str | Path) -> Config:
    """Load configuration from YAML file."""
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)


def create_default_config(output_path: str | Path) -> None:
    """Create a default configuration file."""
    config = Config()
    output_path = Path(output_path)

    config_dict = config.model_dump()

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, indent=2)

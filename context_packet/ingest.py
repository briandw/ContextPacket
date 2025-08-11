"""File ingestion and directory walking for ContextPacket."""

import hashlib
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel

from .config import Config


class FileInfo(BaseModel):
    """Information about an ingested file."""
    
    path: Path
    sha256: str
    size: int
    extension: str
    relative_path: str


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def should_include_file(file_path: Path, config: Config) -> bool:
    """Check if file should be included based on extension."""
    extension = file_path.suffix.lower().lstrip('.')
    return extension in config.include_extensions


def walk_directory(corpus_path: str | Path, config: Config) -> Iterator[FileInfo]:
    """Walk directory and yield file information for valid files."""
    corpus_path = Path(corpus_path)
    
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_path}")
    
    if not corpus_path.is_dir():
        raise ValueError(f"Corpus path is not a directory: {corpus_path}")
    
    # Use glob pattern based on recursive setting
    pattern = "**/*" if config.recursive else "*"
    
    for file_path in corpus_path.glob(pattern):
        # Skip directories and hidden files/dirs
        if file_path.is_dir() or file_path.name.startswith('.'):
            continue
            
        # Check if file extension is included
        if not should_include_file(file_path, config):
            continue
        
        try:
            # Compute file hash and metadata
            file_hash = compute_file_hash(file_path)
            file_size = file_path.stat().st_size
            extension = file_path.suffix.lower().lstrip('.')
            relative_path = str(file_path.relative_to(corpus_path))
            
            yield FileInfo(
                path=file_path,
                sha256=file_hash,
                size=file_size,
                extension=extension,
                relative_path=relative_path
            )
            
        except (OSError, PermissionError) as e:
            # Log error but continue processing other files
            print(f"Warning: Could not process {file_path}: {e}")
            continue


def ingest_corpus(corpus_path: str | Path, config: Config) -> list[FileInfo]:
    """Ingest entire corpus and return list of file information."""
    files = list(walk_directory(corpus_path, config))
    
    print(f"Ingested {len(files)} files from {corpus_path}")
    
    # Group by extension for summary
    by_ext: dict[str, int] = {}
    for file_info in files:
        ext = file_info.extension
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    for ext, count in sorted(by_ext.items()):
        print(f"  {ext}: {count} files")
    
    return files

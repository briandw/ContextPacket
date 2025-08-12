#!/usr/bin/env python3
"""Script to regenerate chunks for annotation with updated configuration."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> bool:
    """Run a shell command and return success status."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print("✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Update chunks for annotation."""
    print("🔄 Updating annotation chunks...")
    print()
    
    # Change to parent directory
    parent_dir = Path(__file__).parent.parent
    
    # Backup old annotations if they exist
    annotations_file = Path("annotation_tool/annotations.json")
    if annotations_file.exists():
        backup_file = Path("annotation_tool/annotations_backup.json")
        print(f"📂 Backing up existing annotations to {backup_file}")
        subprocess.run(f"cp {annotations_file} {backup_file}", shell=True)
    
    # Activate virtual environment and regenerate chunks
    cmd = """
    source .venv/bin/activate && \
    contextpacket --config annotation_config.yml \
                  --corpus test_corpus_small \
                  --goal "What is provenance in C memory model?" \
                  --dump-chunks --dump-scores
    """
    
    if not run_command(cmd, cwd=str(parent_dir)):
        print("❌ Failed to generate chunks")
        sys.exit(1)
    
    # Copy new chunks to annotation tool
    print("\n📁 Copying chunks to annotation tool...")
    
    # Backup old chunks
    old_chunks = Path("annotation_tool/chunks.jsonl")
    if old_chunks.exists():
        backup_chunks = Path("annotation_tool/chunks_backup.jsonl")
        subprocess.run(f"cp {old_chunks} {backup_chunks}", shell=True)
        print(f"📂 Backed up old chunks to {backup_chunks}")
    
    # Copy new chunks
    if not run_command("cp chunks.jsonl annotation_tool/", cwd=str(parent_dir)):
        print("❌ Failed to copy chunks")
        sys.exit(1)
    
    # Copy new scores  
    if not run_command("cp scores.jsonl annotation_tool/", cwd=str(parent_dir)):
        print("❌ Failed to copy scores")
        sys.exit(1)
    
    # Show summary
    print("\n📊 Summary:")
    chunks_file = Path("annotation_tool/chunks.jsonl")
    if chunks_file.exists():
        with open(chunks_file, 'r') as f:
            chunk_count = sum(1 for line in f if line.strip())
        print(f"✅ Generated {chunk_count} new chunks")
        
        # Show first chunk details
        with open(chunks_file, 'r') as f:
            import json
            first_line = f.readline()
            if first_line:
                chunk = json.loads(first_line)
                print(f"✅ Chunk size: {chunk['tokens']} tokens")
                print(f"✅ Text length: {len(chunk['text'])} characters")
    
    print("\n🎉 Chunks updated successfully!")
    print("Note: Old annotations were backed up. You'll need to re-annotate with the new chunks.")
    print("\nTo start annotating:")
    print("  cd annotation_tool")
    print("  python app.py")


if __name__ == "__main__":
    main()

# Apex Merge Engine

Hyper-powerful branch merge technique. Main branch is grown, not switched.

## Strategy

```
1. ANALYZE each branch for beneficial elements
2. TRANSCRIBE beneficial code into main (cherry-pick, not merge)
3. PRUNE branches with no remaining beneficial elements
```

## Benefits

- Main branch history is clean and linear
- No merge commits
- No branch switching
- No accidental overwrites
- Each branch is fully analyzed before integration
- Branches are pruned only when fully consumed

## Usage

```bash
# Analyze all branches (dry run)
python3 -m src.merge_engine /path/to/repo --dry-run

# Analyze and transcribe
python3 -m src.merge_engine /path/to/repo

# Output as JSON
python3 -m src.merge_engine /path/to/repo --json

# Output as Markdown
python3 -m src.merge_engine /path/to/repo --markdown
```

## Python API

```python
from src.merge_engine import MergeEngine

engine = MergeEngine("/path/to/repo")

# Analyze a single branch
analysis = engine.analyze_branch("feature-1")
print(f"Score: {analysis.score}")
print(f"Beneficial: {analysis.beneficial}")

# Transcribe beneficial elements
result = engine.transcribe(analysis)
print(f"Applied: {result.hunks_applied}")

# Run full merge process
report = engine.run()
print(report.to_markdown())
```

## Scoring

Branches are scored 0-1 based on:

- **Commits** (0-1): Number of new commits
- **Files** (0-1): Number of files changed
- **Additions** (0-1): Lines added
- **Deletions** (0-3): Lines deleted (bonus if cleanup)
- **New files** (0-0.5): New files added
- **Behind penalty** (-0.3 to 0): Penalty for diverged branches

Branches with score > 0 are considered beneficial.

## Testing

```bash
pytest tests/ -v
```

## License

MIT

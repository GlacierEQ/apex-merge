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

### Machine–Mesh Protocol Manifest

<!-- glacier-eq-protocol:start -->
```yaml
{
  "schema": "glacier-eq.readme.machine-mesh/v1",
  "repository": {
    "id": "GlacierEQ/apex-merge",
    "url": "https://github.com/GlacierEQ/apex-merge",
    "readme_contract": "estate-machine-v1",
    "default_branch": "main"
  },
  "machine": {
    "repository_kind": "migration-residue",
    "public_api": "inspect-declared-entrypoints",
    "protocol_files": [],
    "entrypoints": [
      {
        "kind": "source-area",
        "path": "src",
        "policy": "inspect-before-use"
      },
      {
        "kind": "test-area",
        "path": "tests",
        "policy": "run-before-reliance"
      }
    ]
  },
  "presentation": {
    "architecture": [
      "recruiter",
      "master",
      "machine",
      "mesh"
    ],
    "authority": {
      "capability": "stone-psysoc-x",
      "repository": "GlacierEQ/AKOS",
      "manifest": "stones/psysoc-x/stone.json",
      "engine": "infinity_stones/psysoc_x.py"
    },
    "truth_invariant": "presentation-may-change-sequence-density-tone-and-style; facts-evidence-uncertainty-provenance-dignity-and-reader-agency-may-not"
  },
  "license": {
    "class": "NO_ROOT_LICENSE_DETECTED",
    "status": "ORIGINALITY_AND_PROVENANCE_REVIEW_REQUIRED",
    "controlling_path": null,
    "policy": "GlacierEQ/job-app-helix/LICENSE_POLICY.json",
    "may_relicense_automatically": false,
    "upstream_rights_must_be_preserved": false
  },
  "mesh": {
    "primary_home": null,
    "branch": "migration-residue",
    "subcategory": "unresolved-primary-home",
    "routing": [
      {
        "relation": "estate-map",
        "target": "GlacierEQ/monolith",
        "url": "https://github.com/GlacierEQ/monolith"
      }
    ],
    "boundaries": [
      "routing-does-not-transfer-source-code-evidence-deployment-or-lifecycle-authority",
      "generated-contract-is-a-source-index-not-a-runtime-or-provider-receipt",
      "implementation-and-provider-state-require-independent-evidence",
      "presentation-calibration-cannot-promote-claim-or-evidence-state",
      "license-automation-cannot-relicense-unresolved-upstream-or-third-party-rights"
    ]
  },
  "provenance": {
    "generated_by": "GlacierEQ/job-app-helix",
    "generator_contract": "estate-machine-v1",
    "classification_source": null,
    "classification_evidence_path": null,
    "classification_evidence_blob_sha": null,
    "classification_status": null,
    "contract_digest": "4eeff1595dc27bfe24aee69c2f2026d54e6c12ed1d558dbc7643d53e4fc3ff9e"
  }
}
```
<!-- glacier-eq-protocol:end -->

#!/usr/bin/env python3
"""
Tests for Apex Merge Engine.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from merge_engine import (
    MergeEngine, BranchAnalysis, TranscribeResult, MergeReport, DiffHunk,
)


def create_test_repo(tmp_path):
    """Create a test git repo with branches."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Initialize
    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)

    # Create initial commit
    (repo / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, capture_output=True)

    return repo


class TestMergeEngine:
    def test_list_branches(self, tmp_path):
        repo = create_test_repo(tmp_path)

        # Create a branch
        subprocess.run(["git", "checkout", "-b", "feature-1"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        branches = engine.list_branches()
        assert "feature-1" in branches

    def test_analyze_beneficial_branch(self, tmp_path):
        repo = create_test_repo(tmp_path)

        # Create branch with changes
        subprocess.run(["git", "checkout", "-b", "feature-1"], cwd=repo, capture_output=True)
        (repo / "new_file.py").write_text("def hello(): pass")
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add new file"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        analysis = engine.analyze_branch("feature-1")
        assert analysis.ahead == 1
        assert analysis.beneficial is True
        assert analysis.score > 0

    def test_analyze_empty_branch(self, tmp_path):
        repo = create_test_repo(tmp_path)

        # Create branch with no changes
        subprocess.run(["git", "checkout", "-b", "empty-branch"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        analysis = engine.analyze_branch("empty-branch")
        assert analysis.ahead == 0
        assert analysis.beneficial is False

    def test_transcribe(self, tmp_path):
        repo = create_test_repo(tmp_path)

        # Create branch with new file
        subprocess.run(["git", "checkout", "-b", "feature-1"], cwd=repo, capture_output=True)
        (repo / "new_file.py").write_text("def hello(): pass")
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add new file"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        analysis = engine.analyze_branch("feature-1")
        result = engine.transcribe(analysis, dry_run=True)
        assert result.hunks_applied > 0

    def test_prune_branch(self, tmp_path):
        repo = create_test_repo(tmp_path)

        # Create and merge branch
        subprocess.run(["git", "checkout", "-b", "feature-1"], cwd=repo, capture_output=True)
        (repo / "file.txt").write_text("content")
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add file"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)
        subprocess.run(["git", "merge", "feature-1", "--no-ff", "-m", "Merge"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        pruned = engine.prune_branch("feature-1")
        assert pruned is True

    def test_full_run(self, tmp_path):
        repo = create_test_repo(tmp_path)

        # Create multiple branches
        for i in range(3):
            subprocess.run(["git", "checkout", "-b", f"feature-{i}"], cwd=repo, capture_output=True)
            (repo / f"file_{i}.py").write_text(f"# Feature {i}")
            subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Add feature {i}"], cwd=repo, capture_output=True)
            subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        report = engine.run(dry_run=True)
        assert report.branches_analyzed == 3
        assert report.branches_beneficial == 3


class TestBranchAnalysis:
    def test_to_dict(self):
        analysis = BranchAnalysis(
            name="feature-1",
            ahead=1,
            behind=0,
            commits=[{"hash": "abc123", "message": "test"}],
            files_changed=["test.py"],
            hunks=[],
            beneficial=True,
            score=0.8,
        )
        d = analysis.to_dict()
        assert d["name"] == "feature-1"
        assert d["beneficial"] is True


class TestMergeReport:
    def test_to_markdown(self):
        report = MergeReport(
            repo="/test",
            main_branch="main",
            branches_analyzed=2,
            branches_beneficial=1,
            branches_pruned=1,
            total_hunks_applied=5,
            total_hunks_skipped=2,
            total_files_transcribed=3,
            duration_ms=100.0,
            results=[],
        )
        md = report.to_markdown()
        assert "# Merge Report" in md
        assert "Branches analyzed: 2" in md


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

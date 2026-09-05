#!/usr/bin/env python3
"""
Additional tests for Apex Merge Engine — Edge Cases & Integration.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from merge_engine import (
    MergeEngine,
    BranchAnalysis,
    TranscribeResult,
    MergeReport,
    DiffHunk,
)


def create_test_repo(tmp_path):
    """Create a test git repo with branches."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)

    (repo / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, capture_output=True)

    return repo


class TestDiffHunk:
    def test_create(self):
        hunk = DiffHunk(
            file="test.py",
            additions=5,
            deletions=2,
            content="+ added line\n- removed line",
            start_line=10,
            end_line=20,
        )
        assert hunk.file == "test.py"
        assert hunk.additions == 5
        assert hunk.deletions == 2
        assert hunk.start_line == 10


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
        assert d["score"] == 0.8
        assert d["hunk_count"] == 0

    def test_not_beneficial(self):
        analysis = BranchAnalysis(
            name="empty",
            ahead=0,
            behind=0,
            commits=[],
            files_changed=[],
            hunks=[],
            beneficial=False,
            reason="No new commits",
        )
        assert analysis.beneficial is False
        assert analysis.reason == "No new commits"


class TestTranscribeResult:
    def test_create(self):
        result = TranscribeResult(
            branch="feature-1",
            files_transcribed=2,
            hunks_applied=5,
            hunks_skipped=0,
            conflicts=[],
            success=True,
        )
        assert result.branch == "feature-1"
        assert result.success is True

    def test_with_conflicts(self):
        result = TranscribeResult(
            branch="feature-1",
            files_transcribed=0,
            hunks_applied=0,
            hunks_skipped=2,
            conflicts=["file1.py", "file2.py"],
            success=False,
        )
        assert len(result.conflicts) == 2
        assert result.success is False

    def test_to_dict(self):
        result = TranscribeResult(
            branch="feature-1",
            files_transcribed=1,
            hunks_applied=1,
            hunks_skipped=0,
            conflicts=[],
            success=True,
        )
        d = result.to_dict()
        assert d["branch"] == "feature-1"
        assert d["success"] is True


class TestMergeReport:
    def test_create(self):
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
        assert report.branches_analyzed == 2

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

    def test_to_dict(self):
        report = MergeReport(
            repo="/test",
            main_branch="main",
            branches_analyzed=0,
            branches_beneficial=0,
            branches_pruned=0,
            total_hunks_applied=0,
            total_hunks_skipped=0,
            total_files_transcribed=0,
            duration_ms=0.0,
            results=[],
        )
        d = report.to_dict()
        assert d["repo"] == "/test"
        assert d["main_branch"] == "main"


class TestMergeEngine:
    def test_list_branches(self, tmp_path):
        repo = create_test_repo(tmp_path)
        subprocess.run(["git", "checkout", "-b", "feature-1"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        branches = engine.list_branches()
        assert "feature-1" in branches

    def test_analyze_beneficial_branch(self, tmp_path):
        repo = create_test_repo(tmp_path)
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
        subprocess.run(["git", "checkout", "-b", "empty-branch"], cwd=repo, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        analysis = engine.analyze_branch("empty-branch")
        assert analysis.ahead == 0
        assert analysis.beneficial is False

    def test_full_run_dry(self, tmp_path):
        repo = create_test_repo(tmp_path)
        for i in range(2):
            subprocess.run(["git", "checkout", "-b", f"feature-{i}"], cwd=repo, capture_output=True)
            (repo / f"file_{i}.py").write_text(f"# Feature {i}")
            subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Add feature {i}"], cwd=repo, capture_output=True)
            subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)

        engine = MergeEngine(str(repo))
        report = engine.run(dry_run=True)
        assert report.branches_analyzed == 2
        assert report.branches_beneficial == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

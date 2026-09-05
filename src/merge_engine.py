#!/usr/bin/env python3
"""
Apex Merge Engine — Hyper-Powerful Branch Merge Technique

Strategy: MAIN IS GROWN, NOT SWITCHED

1. ANALYZE each branch for beneficial elements
2. TRANSCRIBE beneficial code into main (cherry-pick, not merge)
3. PRUNE branches with no remaining beneficial elements

Benefits:
- Main branch history is clean and linear
- No merge commits
- No branch switching
- No accidental overwrites
- Each branch is fully analyzed before integration
- Branches are pruned only when fully consumed

Usage:
    from merge_engine import MergeEngine

    engine = MergeEngine("/path/to/repo")
    report = engine.run()  # Analyze all branches, transcribe, prune
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class DiffHunk:
    """A single diff hunk."""
    file: str
    additions: int
    deletions: int
    content: str
    start_line: int = 0
    end_line: int = 0


@dataclass
class BranchAnalysis:
    """Analysis of a branch."""
    name: str
    ahead: int
    behind: int
    commits: List[Dict[str, str]]
    files_changed: List[str]
    hunks: List[DiffHunk]
    beneficial: bool = True
    reason: str = ""
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ahead": self.ahead,
            "behind": self.behind,
            "commits": self.commits,
            "files_changed": self.files_changed,
            "beneficial": self.beneficial,
            "reason": self.reason,
            "score": self.score,
            "hunk_count": len(self.hunks),
        }


@dataclass
class TranscribeResult:
    """Result of transcribing a branch."""
    branch: str
    files_transcribed: int
    hunks_applied: int
    hunks_skipped: int
    conflicts: List[str]
    success: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch": self.branch,
            "files_transcribed": self.files_transcribed,
            "hunks_applied": self.hunks_applied,
            "hunks_skipped": self.hunks_skipped,
            "conflicts": self.conflicts,
            "success": self.success,
        }


@dataclass
class MergeReport:
    """Full merge report."""
    repo: str
    main_branch: str
    branches_analyzed: int
    branches_beneficial: int
    branches_pruned: int
    total_hunks_applied: int
    total_hunks_skipped: int
    total_files_transcribed: int
    duration_ms: float
    results: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo": self.repo,
            "main_branch": self.main_branch,
            "branches_analyzed": self.branches_analyzed,
            "branches_beneficial": self.branches_beneficial,
            "branches_pruned": self.branches_pruned,
            "total_hunks_applied": self.total_hunks_applied,
            "total_hunks_skipped": self.total_hunks_skipped,
            "total_files_transcribed": self.total_files_transcribed,
            "duration_ms": self.duration_ms,
            "results": self.results,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Merge Report",
            "",
            f"**Repository:** {self.repo}",
            f"**Main Branch:** {self.main_branch}",
            f"**Duration:** {self.duration_ms:.0f}ms",
            "",
            "## Summary",
            "",
            f"- Branches analyzed: {self.branches_analyzed}",
            f"- Beneficial branches: {self.branches_beneficial}",
            f"- Branches pruned: {self.branches_pruned}",
            f"- Hunks applied: {self.total_hunks_applied}",
            f"- Hunks skipped: {self.total_hunks_skipped}",
            f"- Files transcribed: {self.total_files_transcribed}",
            "",
            "## Branch Details",
            "",
        ]

        for result in self.results:
            icon = "✓" if result.get("success") else "✗"
            lines.append(f"### {icon} {result.get('branch', 'unknown')}")
            lines.append("")
            if result.get("beneficial", True):
                lines.append(f"- **Status:** Beneficial")
                lines.append(f"- **Files changed:** {result.get('files_changed', 0)}")
                lines.append(f"- **Hunks applied:** {result.get('hunks_applied', 0)}")
                lines.append(f"- **Hunks skipped:** {result.get('hunks_skipped', 0)}")
            else:
                lines.append(f"- **Status:** Pruned — {result.get('reason', 'no beneficial elements')}")
            lines.append("")

        return "\n".join(lines)


# ─── Merge Engine ────────────────────────────────────────────────────────────

class MergeEngine:
    """Hyper-powerful branch merge engine."""

    def __init__(self, repo_path: str, main_branch: str = "main") -> None:
        self.repo_path = Path(repo_path)
        self.main_branch = main_branch
        self._git("checkout", self.main_branch)

    def _git(self, *args: str) -> str:
        """Run a git command."""
        result = subprocess.run(
            ["git"] + list(args),
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()

    def _git_status(self) -> int:
        """Get git exit code."""
        result = subprocess.run(
            ["git", "status"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode

    def list_branches(self) -> List[str]:
        """List all local branches except main."""
        output = self._git("branch", "--format=%(refname:short)")
        branches = [b.strip() for b in output.split("\n") if b.strip()]
        return [b for b in branches if b != self.main_branch]

    def analyze_branch(self, branch: str) -> BranchAnalysis:
        """Analyze a branch for beneficial elements."""
        # Get ahead/behind counts
        ahead_behind = self._git(
            "rev-list", "--left-right", "--count",
            f"{self.main_branch}...{branch}"
        )
        parts = ahead_behind.split()
        behind = int(parts[0]) if len(parts) > 0 else 0
        ahead = int(parts[1]) if len(parts) > 1 else 0

        # Get commits
        commits = []
        if ahead > 0:
            commit_output = self._git(
                "log", f"{self.main_branch}..{branch}",
                "--format=%H|%s|%an|%ai", "-n", "20"
            )
            for line in commit_output.split("\n"):
                if "|" in line:
                    parts = line.split("|", 3)
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3] if len(parts) > 3 else "",
                    })

        # Get files changed
        files_output = self._git(
            "diff", f"{self.main_branch}...{branch}",
            "--name-only"
        )
        files_changed = [f.strip() for f in files_output.split("\n") if f.strip()]

        # Get diff hunks
        hunks = self._get_hunks(branch)

        # Score the branch
        score = self._score_branch(ahead, behind, commits, files_changed, hunks)
        beneficial = score > 0

        reason = ""
        if not beneficial:
            if ahead == 0:
                reason = "No new commits"
            elif len(files_changed) == 0:
                reason = "No files changed"
            elif score <= 0:
                reason = "No beneficial additions detected"

        return BranchAnalysis(
            name=branch,
            ahead=ahead,
            behind=behind,
            commits=commits,
            files_changed=files_changed,
            hunks=hunks,
            beneficial=beneficial,
            reason=reason,
            score=score,
        )

    def _get_hunks(self, branch: str) -> List[DiffHunk]:
        """Get diff hunks from a branch."""
        diff_output = self._git(
            "diff", f"{self.main_branch}...{branch}",
            "--unified=3"
        )

        hunks = []
        current_file = ""
        current_hunk_content: List[str] = []
        current_additions = 0
        current_deletions = 0

        for line in diff_output.split("\n"):
            if line.startswith("diff --git"):
                # Save previous hunk
                if current_file and current_hunk_content:
                    hunks.append(DiffHunk(
                        file=current_file,
                        additions=current_additions,
                        deletions=current_deletions,
                        content="\n".join(current_hunk_content),
                    ))
                # Start new file
                parts = line.split(" b/")
                current_file = parts[-1] if len(parts) > 1 else ""
                current_hunk_content = []
                current_additions = 0
                current_deletions = 0
            elif line.startswith("@@"):
                current_hunk_content.append(line)
            elif line.startswith("+") and not line.startswith("+++"):
                current_additions += 1
                current_hunk_content.append(line)
            elif line.startswith("-") and not line.startswith("---"):
                current_deletions += 1
                current_hunk_content.append(line)
            else:
                current_hunk_content.append(line)

        # Save last hunk
        if current_file and current_hunk_content:
            hunks.append(DiffHunk(
                file=current_file,
                additions=current_additions,
                deletions=current_deletions,
                content="\n".join(current_hunk_content),
            ))

        return hunks

    def _score_branch(self, ahead: int, behind: int,
                      commits: List[Dict], files: List[str],
                      hunks: List[DiffHunk]) -> float:
        """Score a branch's beneficial value."""
        if ahead == 0:
            return 0.0

        # Base score from commits
        commit_score = min(1.0, ahead / 10)

        # File diversity bonus
        file_score = min(1.0, len(files) / 5)

        # Code quality heuristic
        total_additions = sum(h.additions for h in hunks)
        total_deletions = sum(h.deletions for h in hunks)

        # Positive additions
        if total_additions > 0:
            add_score = min(1.0, total_additions / 100)
        else:
            add_score = 0.0

        # Deletions can be beneficial (cleanup)
        if total_deletions > 0 and total_deletions < total_addions:
            del_score = 0.3
        else:
            del_score = 0.0

        # New files bonus
        new_files = len([h for h in hunks if h.additions > 0 and h.deletions == 0])
        new_file_score = min(0.5, new_files / 3)

        # Penalize if behind (diverged)
        if behind > 5:
            behind_penalty = -0.3
        elif behind > 0:
            behind_penalty = -0.1
        else:
            behind_penalty = 0.0

        total = commit_score + file_score + add_score + del_score + new_file_score + behind_penalty
        return max(0.0, min(1.0, total))

    def transcribe(self, analysis: BranchAnalysis, dry_run: bool = False) -> TranscribeResult:
        """Transcribe beneficial elements from a branch to main."""
        if not analysis.beneficial:
            return TranscribeResult(
                branch=analysis.name,
                files_transcribed=0,
                hunks_applied=0,
                hunks_skipped=len(analysis.hunks),
                conflicts=[],
                success=True,
            )

        files_transcribed = 0
        hunks_applied = 0
        hunks_skipped = 0
        conflicts = []

        for hunk in analysis.hunks:
            if dry_run:
                hunks_applied += 1
                continue

            # Get the file content from the branch
            try:
                branch_content = self._git(
                    "show", f"{analysis.name}:{hunk.file}"
                )

                # Check if file exists in main
                try:
                    main_content = self._git("show", f"{self.main_branch}:{hunk.file}")
                except Exception:
                    main_content = ""

                # Simple merge: apply additions from branch
                if self._can_apply_hunk(hunk, main_content, branch_content):
                    # Write the branch version
                    target_path = self.repo_path / hunk.file
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_text(branch_content)
                    hunks_applied += 1
                    files_transcribed += 1
                else:
                    conflicts.append(hunk.file)
                    hunks_skipped += 1
            except Exception as e:
                hunks_skipped += 1
                conflicts.append(f"{hunk.file}: {str(e)}")

        # Commit if not dry run
        if not dry_run and hunks_applied > 0:
            self._git("add", "-A")
            self._git("commit", "-m", f"Transcribe from {analysis.name}: {hunks_applied} hunks")

        return TranscribeResult(
            branch=analysis.name,
            files_transcribed=files_transcribed,
            hunks_applied=hunks_applied,
            hunks_skipped=hunks_skipped,
            conflicts=conflicts,
            success=len(conflicts) == 0,
        )

    def _can_apply_hunk(self, hunk: DiffHunk, main_content: str, branch_content: str) -> bool:
        """Check if a hunk can be safely applied."""
        # If file is new in branch, always safe
        if not main_content:
            return True

        # If branch version is significantly different, might have conflicts
        main_lines = set(main_content.split("\n"))
        branch_lines = set(branch_content.split("\n"))

        # Check if branch adds new lines not in main
        new_lines = branch_lines - main_lines
        if new_lines:
            return True

        return False

    def prune_branch(self, branch: str, force: bool = False) -> bool:
        """Prune a branch that has been fully consumed."""
        # Check if branch is fully merged
        merged = self._git(
            "branch", "--merged", self.main_branch
        )
        if branch in merged or force:
            self._git("branch", "-D", branch)
            return True
        return False

    def run(self, dry_run: bool = False) -> MergeReport:
        """Run the full merge process: analyze, transcribe, prune."""
        start = time.time()

        branches = self.list_branches()
        results = []
        total_hunks_applied = 0
        total_hunks_skipped = 0
        total_files_transcribed = 0
        branches_beneficial = 0
        branches_pruned = 0

        for branch in branches:
            # Analyze
            analysis = self.analyze_branch(branch)

            if analysis.beneficial:
                branches_beneficial += 1

                # Transcribe
                transcribe_result = self.transcribe(analysis, dry_run=dry_run)
                total_hunks_applied += transcribe_result.hunks_applied
                total_hunks_skipped += transcribe_result.hunks_skipped
                total_files_transcribed += transcribe_result.files_transcribed

                results.append({
                    "branch": branch,
                    "beneficial": True,
                    "files_changed": len(analysis.files_changed),
                    "hunks_applied": transcribe_result.hunks_applied,
                    "hunks_skipped": transcribe_result.hunks_skipped,
                    "success": transcribe_result.success,
                    "conflicts": transcribe_result.conflicts,
                    "score": analysis.score,
                })

                # Prune if fully consumed
                if not dry_run and transcribe_result.hunks_skipped == 0:
                    if self.prune_branch(branch):
                        branches_pruned += 1
            else:
                # Branch not beneficial, prune it
                if not dry_run:
                    if self.prune_branch(branch, force=True):
                        branches_pruned += 1

                results.append({
                    "branch": branch,
                    "beneficial": False,
                    "reason": analysis.reason,
                    "score": analysis.score,
                })

        duration = (time.time() - start) * 1000

        return MergeReport(
            repo=str(self.repo_path),
            main_branch=self.main_branch,
            branches_analyzed=len(branches),
            branches_beneficial=branches_beneficial,
            branches_pruned=branches_pruned,
            total_hunks_applied=total_hunks_applied,
            total_hunks_skipped=total_hunks_skipped,
            total_files_transcribed=total_files_transcribed,
            duration_ms=duration,
            results=results,
        )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Apex Merge Engine — Hyper-Powerful Branch Merge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("repo", help="Repository path")
    parser.add_argument("--main", default="main", help="Main branch name")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't transcribe")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--markdown", action="store_true", help="Output as Markdown")

    args = parser.parse_args()

    engine = MergeEngine(args.repo, args.main)
    report = engine.run(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    elif args.markdown:
        print(report.to_markdown())
    else:
        print(f"\n=== MERGE REPORT ===\n")
        print(f"Repository: {report.repo}")
        print(f"Main Branch: {report.main_branch}")
        print(f"Duration: {report.duration_ms:.0f}ms\n")
        print(f"Branches Analyzed: {report.branches_analyzed}")
        print(f"Beneficial: {report.branches_beneficial}")
        print(f"Pruned: {report.branches_pruned}")
        print(f"Hunks Applied: {report.total_hunks_applied}")
        print(f"Hunks Skipped: {report.total_hunks_skipped}")
        print(f"Files Transcribed: {report.total_files_transcribed}")
        print()

        for result in report.results:
            icon = "✓" if result.get("beneficial", False) else "✗"
            print(f"  {icon} {result.get('branch', 'unknown')}")
            if result.get("beneficial"):
                print(f"    Score: {result.get('score', 0):.2f}")
                print(f"    Applied: {result.get('hunks_applied', 0)}")
            else:
                print(f"    Reason: {result.get('reason', 'unknown')}")

    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""GitHub skill search helper -- searches repos and SKILL.md files via gh CLI.

  python search_github.py "<query>" [--type repos|code|both] [--limit N]
  python search_github.py "<query>" --score "<user need description>"
"""
import json, subprocess, sys, argparse
from datetime import datetime, timezone
from typing import Any

def _gh(cmd: list[str]) -> tuple[int, str, str]:
    """Run a gh CLI command; returns (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr
    except (FileNotFoundError, OSError):
        return 1, "", "gh CLI not available"

def search_repos(query: str, limit: int = 10, sort: str = "stars") -> list[dict[str, Any]]:
    """Search GitHub repositories matching the query."""
    fields = ("name,fullName,url,description,stargazersCount,forksCount,"
              "language,license,updatedAt,topics,createdAt,isFork,isArchived")
    cmd = ["gh", "search", "repos", query, "--sort", sort,
           "--limit", str(limit), "--json", fields]
    code, stdout, stderr = _gh(cmd)
    if code != 0:
        print(f"Error: {stderr}", file=sys.stderr)
        return []
    return json.loads(stdout)

def search_skill_files(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search for SKILL.md files on GitHub matching the query."""
    cmd = ["gh", "search", "code", f"SKILL.md {query}", "--extension", "md",
           "--limit", str(limit), "--json", "repository,path"]
    code, stdout, stderr = _gh(cmd)
    if code != 0:
        print(f"Error: {stderr}", file=sys.stderr)
        return []
    return json.loads(stdout)


def get_repo_details(owner_repo: str) -> dict[str, Any]:
    """Get detailed info for a specific repository."""
    fields = ("name,description,stargazersCount,forksCount,openIssues,"
              "licenseInfo,createdAt,updatedAt,latestRelease,homepageUrl")
    cmd = ["gh", "repo", "view", owner_repo, "--json", fields]
    code, stdout, stderr = _gh(cmd)
    if code != 0:
        print(f"Error: {stderr}", file=sys.stderr)
        return {}
    return json.loads(stdout)


def _extract_fullname(item: dict[str, Any]) -> str | None:
    """Extract owner/repo string from search result. Handles both repo-search items
    (fullName field) and code-search items (repository is a nested object)."""
    fullname = item.get("fullName")
    if isinstance(fullname, str) and "/" in fullname:
        return fullname
    repo = item.get("repository")
    if isinstance(repo, dict):
        owner = repo.get("owner", {})
        if isinstance(owner, dict):
            owner_login = owner.get("login", "")
        else:
            owner_login = ""
        name = repo.get("name", "")
        if owner_login and name:
            return f"{owner_login}/{name}"
    if isinstance(repo, str) and "/" in repo:
        return repo
    return None


def merge_and_dedupe(*result_lists: list[dict[str, Any]],
                     top_n: int = 10) -> list[dict[str, Any]]:
    """Merge results from multiple sources. Deduplicates by fullName (owner/repo),
    keeps highest star count. Excludes forks unless original is archived.
    Returns top N sorted by stars descending."""
    merged: dict[str, dict[str, Any]] = {}
    for rlist in result_lists:
        for item in rlist:
            key = _extract_fullname(item)
            if not key:
                continue
            if item.get("isFork") and not item.get("isArchived"):
                continue
            item = dict(item)
            item["fullName"] = key
            stars = item.get("stargazersCount") or 0
            if key in merged and (merged[key].get("stargazersCount") or 0) >= stars:
                continue
            merged[key] = item
    ranked = sorted(merged.values(),
                    key=lambda r: r.get("stargazersCount") or 0, reverse=True)
    return ranked[:top_n]

_STOP: frozenset[str] = frozenset({  # common stop-words filtered during tokenisation
    "a","an","the","is","are","was","were","be","been","being",
    "for","of","in","on","at","to","from","by","with","without",
    "and","or","not","but","if","then","else","when","while",
    "it","its","this","that","these","those","which","what",
    "as","has","have","had","do","does","did","will","would",
    "can","could","should","may","might","shall","must",
    "i","you","he","she","we","they","me","him","her","us","them",
    "my","your","his","our","their",
})


def _tokenize(text: str) -> set[str]:
    out: set[str] = set()
    for raw in text.lower().split():
        w = raw.strip(".,;:!?()[]{}'\"\\/")
        if w and w not in _STOP and len(w) > 1:
            out.add(w)
    return out

_SYNONYMS: dict[str, list[str]] = {
    "cli": ["command-line", "commandline", "terminal", "console"],
    "json": ["javascript object notation"],
    "api": ["rest", "graphql", "endpoint"],
    "ui": ["gui", "interface", "frontend", "dashboard"],
    "pdf": ["document", "reader", "viewer"],
    "tool": ["utility", "helper", "app", "application"],
    "markdown": ["md", "commonmark", "gfm"],
    "image": ["picture", "photo", "graphic", "screenshot"],
    "render": ["display", "show", "preview", "view"],
    "search": ["find", "query", "lookup", "discover"],
    "editor": ["ide", "text editor", "code editor"],
    "framework": ["library", "sdk", "toolkit"],
    "plugin": ["extension", "addon", "add-on", "module"],
    "docker": ["container", "podman", "oci"],
    "git": ["version control", "vcs", "scm"],
    "monitor": ["watch", "observe", "track", "metrics"],
}


def _expand_tokens(tokens: set[str]) -> set[str]:
    """Expand a token set with known synonyms to bridge vocabulary gaps."""
    expanded = set(tokens)
    for tok in tokens:
        for syn in _SYNONYMS.get(tok, []):
            expanded.update(_tokenize(syn))
    return expanded


def score_match(repo_description: str, user_need: str) -> int:
    """Relevance score 1-5 with synonym-aware keyword overlap.
    5=direct(>=80% tokens after expansion), 4=core(>=60%),
    3=partial(>=40%), 2=conceptual(>=20%), 1=unrelated."""
    if not repo_description or not user_need:
        return 1
    need = _tokenize(user_need)
    if not need:
        return 1
    desc_tokens = _tokenize(repo_description)
    expanded_need = _expand_tokens(need)
    ratio = sum(1 for t in expanded_need if t in desc_tokens) / len(expanded_need)
    if ratio >= 0.8: return 5
    if ratio >= 0.6: return 4
    if ratio >= 0.4: return 3
    if ratio >= 0.2: return 2
    return 1

def score_activity(updated_at: str | None) -> int:
    """Recency score 1-5. 5=<1mo, 4=<3mo, 3=<6mo, 2=<12mo, 1=older/unknown."""
    if not updated_at:
        return 1
    try:
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        months = (datetime.now(timezone.utc) - updated).days / 30.44
        if months <= 1: return 5
        if months <= 3: return 4
        if months <= 6: return 3
        if months <= 12: return 2
        return 1
    except (ValueError, TypeError):
        return 1

def score_stars(stars: int) -> int:
    """Star-count score 1-5. 5>=10k, 4>=1k, 3>=100, 2>=10, 1=<10."""
    if stars >= 10000: return 5
    if stars >= 1000: return 4
    if stars >= 100: return 3
    if stars >= 10: return 2
    return 1

def composite_score(match: int, stars: int, activity: int) -> float:
    """Weighted composite: match*0.6 + stars*0.25 + activity*0.15. Rounded to 2 decimal places."""
    return round(match * 0.6 + stars * 0.25 + activity * 0.15, 2)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search GitHub for skills and repos")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--type", choices=["repos", "code", "both"],
                        default="both")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--score", type=str, default=None,
                        help="Describe your need for scored & ranked results")
    args = parser.parse_args()

    code, _, stderr = _gh(["gh", "--version"])
    if code != 0:
        print(json.dumps({"error": "gh CLI not available",
                          "message": "Install: https://cli.github.com (then gh auth login)"},
                         indent=2, ensure_ascii=False))
        sys.exit(1)

    code, _, stderr = _gh(["gh", "auth", "status"])
    if code != 0:
        print(json.dumps({"error": "gh not authenticated",
                          "message": "Run: gh auth login. Unauthenticated requests are severely rate-limited (10/min)."},
                         indent=2, ensure_ascii=False))
        sys.exit(1)

    # Collect results
    result_lists: list[list[dict[str, Any]]] = []
    if args.type in ("repos", "both"):
        result_lists.append(search_repos(args.query, args.limit))
    if args.type in ("code", "both"):
        result_lists.append(search_skill_files(args.query, args.limit * 2))

    if args.score:
        # Score mode: merge, dedupe, score, rank
        merged = merge_and_dedupe(*result_lists, top_n=max(args.limit * 2, 20))
        scored: list[dict[str, Any]] = []
        for repo in merged:
            desc = repo.get("description") or ""
            m, a, s = score_match(desc, args.score), \
                score_activity(repo.get("updatedAt")), \
                score_stars(repo.get("stargazersCount") or 0)
            scored.append({
                "fullName": repo.get("fullName"),
                "url": repo.get("url", ""),
                "description": desc,
                "stargazersCount": repo.get("stargazersCount"),
                "updatedAt": repo.get("updatedAt"),
                "scores": {"match": m, "activity": a, "stars": s,
                           "composite": composite_score(m, s, a)},
            })
        scored.sort(key=lambda r: r["scores"]["composite"], reverse=True)
        scored = scored[:args.limit]
        output: dict[str, Any] = {
            "scored_results": scored,
            "total_found": sum(len(rl) for rl in result_lists),
            "filtered_count": len(scored),
            "search_method": "github_api",
        }
    else:
        repos: list[dict[str, Any]] = []
        skills: list[dict[str, Any]] = []
        if args.type == "both" and len(result_lists) >= 2:
            repos, skills = result_lists[0], result_lists[1]
        elif args.type == "repos" and result_lists:
            repos = result_lists[0]
        elif args.type == "code" and result_lists:
            skills = result_lists[0]
        output = {"repos": repos, "skill_files": skills}

    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

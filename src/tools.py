"""Grounded research, citation verification, deterministic linting, and loop-control tools."""

import os
import re
import time
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Optional

import defusedxml.ElementTree as DefusedET
import requests

from .knowledge_base import load_banned_phrases

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS  # type: ignore[no-redef]
    except ImportError:  # pragma: no cover
        DDGS = None  # type: ignore[assignment]

try:
    from google.adk.tools.tool_context import ToolContext
except ImportError:  # pragma: no cover
    ToolContext = Any  # type: ignore[misc,assignment]


SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_API_URL = "https://export.arxiv.org/api/query"


def _make_bibtex_key(authors: list[str], year: int | str | None, title: str) -> str:
    """Create a deterministic BibTeX citation key (e.g. xiao2025optimizing)."""
    first_author = authors[0] if authors else "unknown"
    last_name = re.sub(r"[^a-z]", "", first_author.split()[-1].lower()) or "author"
    year_str = str(year) if year else "nd"
    first_word = next(
        (
            w
            for w in re.findall(r"[a-z]{4,}", title.lower())
            if w not in {"with", "from", "that", "this"}
        ),
        "paper",
    )
    return f"{last_name}{year_str}{first_word}"


def _format_single_bibtex(paper: dict[str, Any]) -> str:
    """Format a paper dictionary as a valid BibTeX entry."""
    authors = paper.get("authors", [])
    if isinstance(authors, str):
        authors = [a.strip() for a in authors.split(",") if a.strip()]
    title = str(paper.get("title", "Untitled")).replace("{", "").replace("}", "")
    year = paper.get("year") or ""
    venue = str(paper.get("venue", "")).strip()
    url = str(paper.get("url") or paper.get("link") or "").strip()
    arxiv_id = str(paper.get("arxiv_id", "")).strip()
    doi = str(paper.get("doi", "")).strip()

    key = _make_bibtex_key(authors, year, title)
    author_field = " and ".join(authors) if authors else "Unknown"
    entry_type = "inproceedings" if venue and "arxiv" not in venue.lower() else "misc"

    lines = [
        f"@{entry_type}{{{key},",
        f"  title = {{{title}}},",
        f"  author = {{{author_field}}},",
    ]
    if year:
        lines.append(f"  year = {{{year}}},")
    if venue and entry_type == "inproceedings":
        lines.append(f"  booktitle = {{{venue}}},")
    if arxiv_id:
        lines.append(f"  eprint = {{{arxiv_id}}},")
        lines.append("  archivePrefix = {arXiv},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    if url:
        lines.append(f"  url = {{{url}}},")
    lines.append("}")
    return "\n".join(lines)


def search_semantic_scholar(
    query: str,
    max_results: int = 5,
    year_from: Optional[int] = None,  # noqa: UP007, UP045
) -> dict[str, Any]:
    """Search verified academic papers via the Semantic Scholar Graph API.

    Returns full abstracts, publication years, venues, citation counts, URLs,
    and valid BibTeX entries (PaperOrchestra literature grounding pattern).

    Args:
        query: Academic search query (e.g., "ad fraud detection made for advertising").
        max_results: Maximum number of papers to return (1-20, default: 5).
        year_from: Optional minimum publication year filter (e.g., 2023).

    Returns:
        Dictionary with status, papers list, and count.
    """
    if not query or not query.strip():
        return {"status": "error", "error_message": "Search query cannot be empty."}

    max_results = max(1, min(int(max_results), 20))
    params: dict[str, Any] = {
        "query": query.strip(),
        "limit": max_results,
        "fields": "title,authors,year,venue,citationCount,abstract,url,externalIds",
    }
    if year_from:
        params["year"] = f"{year_from}-"

    headers = {"User-Agent": "agentic-content-generation/2.0"}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key and not api_key.startswith("your_"):
        headers["x-api-key"] = api_key

    last_error = ""
    for attempt in range(2):
        try:
            response = requests.get(
                SEMANTIC_SCHOLAR_SEARCH_URL,
                params=params,
                headers=headers,
                timeout=15,
            )
            if response.status_code == 429 and attempt == 0:
                time.sleep(1.5)
                continue
            response.raise_for_status()
            payload = response.json()

            papers: list[dict[str, Any]] = []
            for item in payload.get("data", []):
                authors = [
                    a.get("name", "").strip() for a in item.get("authors", [])[:6] if a.get("name")
                ]
                ext_ids = item.get("externalIds") or {}
                abstract = (item.get("abstract") or "").strip()
                if len(abstract) > 1500:
                    abstract = abstract[:1500] + "..."

                paper_dict: dict[str, Any] = {
                    "title": (item.get("title") or "Untitled").strip(),
                    "authors": authors,
                    "year": item.get("year"),
                    "venue": (item.get("venue") or "").strip(),
                    "citation_count": item.get("citationCount"),
                    "abstract": abstract or "No abstract available.",
                    "url": item.get("url") or "",
                    "arxiv_id": ext_ids.get("ArXiv", ""),
                    "doi": ext_ids.get("DOI", ""),
                    "source": "semantic_scholar",
                }
                paper_dict["bibtex"] = _format_single_bibtex(paper_dict)
                papers.append(paper_dict)

            return {"status": "success", "papers": papers, "count": len(papers)}
        except requests.RequestException as exc:
            last_error = str(exc)
        except Exception as exc:
            last_error = str(exc)
            break

    return {
        "status": "error",
        "error_message": f"Semantic Scholar search failed: {last_error}",
    }


def verify_citation_semantic_scholar(title: str) -> dict[str, Any]:
    """Verify that a cited paper title exists on Semantic Scholar and return canonical metadata.

    Implements PaperOrchestra's sequential citation verification step to prevent
    hallucinated references and missing years.

    Args:
        title: Exact or near-exact title of the paper to verify.

    Returns:
        Dictionary with status, verified boolean, similarity score, and canonical paper metadata.
    """
    if not title or len(title.strip()) < 5:
        return {"status": "error", "verified": False, "error_message": "Title is too short."}

    result = search_semantic_scholar(title.strip(), max_results=3)
    if result.get("status") != "success":
        return {
            "status": "error",
            "verified": False,
            "error_message": result.get("error_message", "Verification lookup failed."),
        }

    papers = result.get("papers", [])
    if not papers:
        return {"status": "success", "verified": False, "similarity": 0.0, "paper": None}

    target_norm = re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()
    best_paper = None
    best_score = 0.0
    for paper in papers:
        cand_norm = re.sub(r"[^a-z0-9 ]", "", paper["title"].lower()).strip()
        score = SequenceMatcher(None, target_norm, cand_norm).ratio()
        if score > best_score:
            best_score = score
            best_paper = paper

    return {
        "status": "success",
        "verified": best_score >= 0.72,
        "similarity": round(best_score, 3),
        "paper": best_paper,
    }


def search_arxiv_papers(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",
) -> dict[str, Any]:
    """Search arXiv academic papers sorted by relevance (not raw submission date).

    Returns full abstracts (up to 1,500 chars), real publication years, arXiv IDs,
    and BibTeX entries.

    Args:
        query: Research query (e.g., "multi-agent LLM evaluation cost latency").
        max_results: Maximum number of papers to return (default: 5).
        sort_by: arXiv sort criterion ("relevance", "lastUpdatedDate", or "submittedDate").

    Returns:
        Dictionary with status, papers list, and count.
    """
    if not query or not query.strip():
        return {"status": "error", "error_message": "arXiv query cannot be empty."}

    valid_sorts = {"relevance", "lastUpdatedDate", "submittedDate"}
    sort_criterion = sort_by if sort_by in valid_sorts else "relevance"
    max_results = max(1, min(int(max_results), 20))

    try:
        params = {
            "search_query": f"all:{query.strip()}",
            "max_results": max_results,
            "sortBy": sort_criterion,
            "sortOrder": "descending",
        }
        response = requests.get(ARXIV_API_URL, params=params, timeout=15)
        response.raise_for_status()

        try:
            root = DefusedET.fromstring(response.content)
        except Exception as exc:
            return {"status": "error", "error_message": f"Failed to parse arXiv XML: {exc}"}

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers: list[dict[str, Any]] = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            title_el = entry.find("atom:title", ns)
            title = (
                " ".join(title_el.text.split())
                if title_el is not None and title_el.text
                else "Untitled"
            )

            summary_el = entry.find("atom:summary", ns)
            abstract = (
                " ".join(summary_el.text.split())
                if summary_el is not None and summary_el.text
                else "No abstract available."
            )
            if len(abstract) > 1500:
                abstract = abstract[:1500] + "..."

            id_el = entry.find("atom:id", ns)
            link = id_el.text.strip() if id_el is not None and id_el.text else ""
            arxiv_id = link.rsplit("/", 1)[-1] if "/abs/" in link else ""

            pub_el = entry.find("atom:published", ns)
            year: int | None = None
            if pub_el is not None and pub_el.text and len(pub_el.text) >= 4:
                try:
                    year = int(pub_el.text[:4])
                except ValueError:
                    year = None

            authors: list[str] = []
            for author_el in entry.findall("atom:author", ns)[:6]:
                name_el = author_el.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            paper_dict: dict[str, Any] = {
                "title": title,
                "authors": authors,
                "year": year,
                "venue": "arXiv",
                "citation_count": None,
                "abstract": abstract,
                "url": link,
                "arxiv_id": arxiv_id,
                "doi": "",
                "source": "arxiv",
            }
            paper_dict["bibtex"] = _format_single_bibtex(paper_dict)
            papers.append(paper_dict)

        if not papers:
            return {"status": "error", "error_message": f"No arXiv papers found for: {query}"}

        return {"status": "success", "papers": papers, "count": len(papers)}
    except requests.RequestException as exc:
        return {"status": "error", "error_message": f"arXiv request failed: {exc}"}
    except Exception as exc:
        return {"status": "error", "error_message": f"Unexpected arXiv error: {exc}"}


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web via DuckDuckGo for industry context, benchmarks, and real-world news."""
    if not query or not query.strip():
        return {"status": "error", "error_message": "Web query cannot be empty."}
    if DDGS is None:
        return {
            "status": "error",
            "error_message": "duckduckgo-search / ddgs package not installed.",
        }

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query.strip(), max_results=max_results))
        formatted = [
            {
                "title": r.get("title", ""),
                "link": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
        return {"status": "success", "results": formatted, "count": len(formatted)}
    except Exception as exc:
        return {"status": "error", "error_message": f"Web search error: {exc}"}


def search_industry_context(
    topic: str,
    region: str = "Europe",
    max_results: int = 5,
) -> dict[str, Any]:
    """Search current-year industry news and market adoption signals for a topic.

    Uses the dynamic current year (never hardcoded) to ground B2B positioning.
    """
    current_year = datetime.now().year
    query = f"{topic} industry benchmark production adoption {region} {current_year}"
    result = search_web(query, max_results=max_results)
    result["year"] = current_year
    result["region"] = region
    return result


def generate_bibtex(papers: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile a deduplicated BibTeX bibliography string from verified paper dicts.

    Directly reusable in LaTeX manuscripts and PaperOrchestra workflows.
    """
    if not papers:
        return {"status": "error", "error_message": "No papers provided for BibTeX generation."}

    entries: list[str] = []
    seen_titles: set[str] = set()
    for paper in papers:
        title_key = str(paper.get("title", "")).strip().lower()
        if not title_key or title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        entry = paper.get("bibtex") or _format_single_bibtex(paper)
        entries.append(entry)

    return {
        "status": "success",
        "bibtex": "\n\n".join(entries),
        "count": len(entries),
    }


def validate_deliverables_deterministic(
    linkedin_post: str = "",
    x_tweets: Optional[list[str]] = None,  # noqa: UP007, UP045
    youtube_script: str = "",
    banned_phrases: Optional[list[str]] = None,  # noqa: UP007, UP045
) -> dict[str, Any]:
    """Deterministic Python quality & formatting gate for LinkedIn, X, and YouTube.

    Detects hard violations that LLMs routinely miss:
    - Unfilled placeholders like ``[mention a project]`` or ``[Add citations here]``
    - Broken Markdown syntax in LinkedIn posts (``**bold**``, ``###``, code fences)
    - X tweets exceeding 280 characters
    - Banned AI-slop clichés (FR & EN)
    - Missing visual cues in YouTube scripts

    Args:
        linkedin_post: Draft LinkedIn post plain text.
        x_tweets: List of individual tweets in the X thread.
        youtube_script: Draft YouTube long-form script.
        banned_phrases: Optional override list of banned cliché phrases.

    Returns:
        Dictionary with ``passed`` (bool), ``violations`` (blocking), ``warnings``, and ``stats``.
    """
    violations: list[str] = []
    warnings: list[str] = []
    cliches = [
        p.lower() for p in (banned_phrases if banned_phrases is not None else load_banned_phrases())
    ]

    # Placeholder pattern: catches [mention ...], [insert ...], [Add ...], [Continue ...], TODO, TBD
    placeholder_re = re.compile(
        r"\[(?!VISUAL|B-ROLL|CHART|DIAGRAM|CUT|DEMO|SCREEN|OVERLAY|0-9|\d+\])"
        r"(?:mention|insert|add|continue|your|include|link|placeholder|todo|tbd)[^\]]*\]",
        re.IGNORECASE,
    )

    def _scan_common(label: str, text: str) -> None:
        if not text:
            return
        for match in placeholder_re.findall(text):
            violations.append(f"[{label}] Unfilled placeholder detected: {match}")
        if re.search(r"\b(TODO|TBD)\b", text):
            violations.append(f"[{label}] Contains TODO/TBD marker.")
        lower_text = text.lower()
        for phrase in cliches:
            if phrase and phrase in lower_text:
                violations.append(f"[{label}] Banned AI cliché detected: '{phrase}'")

    # 1. LinkedIn checks
    if linkedin_post:
        _scan_common("LinkedIn", linkedin_post)
        if re.search(r"\*\*[^*]+\*\*", linkedin_post):
            violations.append(
                "[LinkedIn] Contains Markdown bold (**text**), which renders literally on LinkedIn."
            )
        if re.search(r"^#{1,6}\s", linkedin_post, flags=re.MULTILINE):
            violations.append(
                "[LinkedIn] Contains Markdown headings (###), not supported on LinkedIn."
            )
        if "```" in linkedin_post:
            violations.append(
                "[LinkedIn] Contains Markdown code fences (```), not supported on LinkedIn."
            )
        hashtags = re.findall(r"(?<!\w)#[A-Za-z0-9À-ÿ_]+", linkedin_post)
        if len(hashtags) > 5:
            warnings.append(
                f"[LinkedIn] Too many hashtags ({len(hashtags)}); keep <= 4 at the end."
            )
        word_count = len(linkedin_post.split())
        if word_count < 80:
            warnings.append(f"[LinkedIn] Post looks very short ({word_count} words).")
        elif word_count > 650:
            warnings.append(
                f"[LinkedIn] Post is long ({word_count} words); consider tightening or moving details to carousel."
            )

    # 2. X / Twitter thread checks
    tweets = x_tweets or []
    over_limit: list[dict[str, Any]] = []
    for idx, tweet in enumerate(tweets, start=1):
        clean_tweet = tweet.strip()
        _scan_common(f"X Tweet {idx}", clean_tweet)
        if len(clean_tweet) > 280:
            over_limit.append({"index": idx, "length": len(clean_tweet)})
            violations.append(f"[X Tweet {idx}] Exceeds 280 characters ({len(clean_tweet)} chars).")

    # 3. YouTube checks
    if youtube_script:
        _scan_common("YouTube", youtube_script)
        if not re.search(
            r"\[(VISUAL|B-ROLL|CHART|DIAGRAM|DEMO|SCREEN)", youtube_script, re.IGNORECASE
        ):
            warnings.append(
                "[YouTube] No visual cues found (e.g., [VISUAL #1: ...]). Add cues tied to generated figures."
            )

    return {
        "status": "success",
        "passed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "stats": {
            "linkedin_words": len(linkedin_post.split()) if linkedin_post else 0,
            "x_tweet_count": len(tweets),
            "x_over_280_count": len(over_limit),
            "youtube_words": len(youtube_script.split()) if youtube_script else 0,
        },
    }


def exit_loop(tool_context: ToolContext) -> dict[str, Any]:
    """Terminate the ADK LoopAgent once all fact-check and anti-slop quality gates pass.

    Call this tool ONLY when:
    1. ``validate_deliverables_deterministic`` reports ``passed == True``.
    2. Fact-checker confirms zero unsourced statistics or hallucinated citations.
    3. Editorial critic score is >= 85/100 with no blocking issues.
    """
    if hasattr(tool_context, "actions"):
        tool_context.actions.escalate = True
    return {"status": "success", "message": "Quality gate passed. Exiting refinement loop."}

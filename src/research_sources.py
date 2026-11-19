"""Extended high-ROI research & industry intelligence sources for HybridLiteratureAgent.

Sources implemented (all strictly SSRF-hardened, timeout-bounded, and defusedxml-parsed):
1. OpenAlex API (`search_openalex_papers`) — Broad academic + Econometrics, Finance & AdTech
2. HuggingFace Daily Papers (`search_huggingface_daily_papers`) — Trending AI/Agent papers + GitHub repos
3. alphaXiv (`fetch_alphaxiv_overview`) — Structured AI/community Markdown overviews for arXiv papers
4. HAL Archives Ouvertes (`search_hal_papers`) — French academic research (ideal for CIR/CII dossiers)
5. arXiv Full-Text PDF Reader (`fetch_arxiv_pdf_text`) — In-memory extraction of results/tables beyond abstracts
6. Curated Industry RSS (`fetch_industry_rss_feeds`) — Allowlisted AdTech & AI Engineering feeds
"""

from __future__ import annotations

import io
import os
import re
from typing import Any

import defusedxml.ElementTree as DefusedET
import requests

from .tools import _format_single_bibtex

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore[assignment]

OPENALEX_API_URL = "https://api.openalex.org/works"
HF_DAILY_PAPERS_URL = "https://huggingface.co/api/daily_papers"
HAL_API_URL = "https://api.archives-ouvertes.fr/search/"
ALPHAXIV_OVERVIEW_TEMPLATE = "https://www.alphaxiv.org/overview/{arxiv_id}.md"
ALPHAXIV_ABS_MD_TEMPLATE = "https://www.alphaxiv.org/abs/{arxiv_id}.md"
ARXIV_PDF_TEMPLATE = "https://arxiv.org/pdf/{arxiv_id}.pdf"

# Strict arXiv ID pattern to prevent SSRF / URL injection
ARXIV_ID_RE = re.compile(r"^(?:\d{4}\.\d{4,5}|[a-z\-]+/\d{7})(?:v\d+)?$", re.IGNORECASE)
MAX_PDF_BYTES = 15 * 1024 * 1024  # 15 MB safety ceiling for remote PDF downloads

# Strictly allowlisted RSS/Atom feeds (LLM can only select category, never pass arbitrary URLs)
CURATED_RSS_FEEDS: dict[str, list[tuple[str, str]]] = {
    "adtech": [
        ("AdExchanger", "https://www.adexchanger.com/feed/"),
        ("Digiday", "https://digiday.com/feed/"),
        ("IAB Tech Lab", "https://iabtechlab.com/feed/"),
    ],
    "ai_engineering": [
        ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
        ("Google Research Blog", "https://research.google/blog/rss/"),
        ("arXiv cs.AI", "https://rss.arxiv.org/rss/cs.AI"),
    ],
}


def validate_arxiv_id(raw_id: str) -> str:
    """Validate and normalize an arXiv identifier (strict SSRF protection).

    Accepts bare IDs like ``2604.05018`` or ``2604.05018v1`` as well as canonical
    arXiv/alphaXiv URLs like ``https://arxiv.org/abs/2604.05018``.

    Raises:
        ValueError: If the identifier does not match the strict arXiv ID format.
    """
    cleaned = raw_id.strip()
    # Extract ID from canonical arxiv.org / alphaxiv.org URLs if passed
    url_match = re.match(
        r"^https?://(?:www\.)?(?:arxiv|alphaxiv)\.org/(?:abs|pdf|overview)/([^?#]+?)(?:\.pdf|\.md)?$",
        cleaned,
        re.IGNORECASE,
    )
    if url_match:
        cleaned = url_match.group(1)

    cleaned = cleaned.removeprefix("arXiv:").strip()
    if not ARXIV_ID_RE.match(cleaned):
        raise ValueError(
            f"Invalid arXiv ID '{raw_id}'. Expected format like '2604.05018' or '2604.05018v1'."
        )
    return cleaned


def _reconstruct_openalex_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct plain-text abstract from OpenAlex's inverted index representation."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    pos_to_word: dict[int, str] = {}
    for word, positions in inverted_index.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            if isinstance(pos, int):
                pos_to_word[pos] = word
    if not pos_to_word:
        return ""
    return " ".join(pos_to_word[idx] for idx in sorted(pos_to_word))


def search_openalex_papers(
    query: str,
    max_results: int = 5,
    year_from: int | None = None,
) -> dict[str, Any]:
    """Search OpenAlex works (250M+ papers across AI, Econometrics, Finance, Marketing & AdTech).

    Free, high-quota academic index with citation counts, venues, open-access PDF links,
    and reconstructed full abstracts.

    Args:
        query: Research query (e.g., "programmatic advertising fraud econometrics").
        max_results: Number of papers to return (1-20, default: 5).
        year_from: Optional minimum publication year filter (e.g., 2022).

    Returns:
        Dictionary with status, papers list, and count.
    """
    if not query or not query.strip():
        return {"status": "error", "error_message": "OpenAlex query cannot be empty."}

    max_results = max(1, min(int(max_results), 20))
    params: dict[str, Any] = {
        "search": query.strip(),
        "per-page": max_results,
        "sort": "relevance_score:desc",
    }
    if year_from:
        params["filter"] = f"from_publication_date:{int(year_from)}-01-01"

    polite_email = os.getenv("OPENALEX_EMAIL", "").strip()
    if polite_email and "@" in polite_email:
        params["mailto"] = polite_email

    try:
        response = requests.get(
            OPENALEX_API_URL,
            params=params,
            headers={"User-Agent": "agentic-content-generation/2.1"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()

        papers: list[dict[str, Any]] = []
        for work in payload.get("results", [])[:max_results]:
            authors = [
                a.get("author", {}).get("display_name", "").strip()
                for a in work.get("authorships", [])[:6]
                if a.get("author", {}).get("display_name")
            ]
            abstract = _reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
            if len(abstract) > 1500:
                abstract = abstract[:1500] + "..."

            primary_loc = work.get("primary_location") or {}
            source_obj = primary_loc.get("source") or {}
            venue = (source_obj.get("display_name") or "").strip()
            oa_info = work.get("open_access") or {}
            pdf_url = oa_info.get("oa_url") or primary_loc.get("pdf_url") or ""
            doi = (work.get("doi") or "").removeprefix("https://doi.org/").strip()
            url = primary_loc.get("landing_page_url") or work.get("doi") or work.get("id") or ""

            paper_dict: dict[str, Any] = {
                "title": (work.get("display_name") or work.get("title") or "Untitled").strip(),
                "authors": authors,
                "year": work.get("publication_year"),
                "venue": venue,
                "citation_count": work.get("cited_by_count"),
                "abstract": abstract or "No abstract available.",
                "url": url,
                "open_access_pdf": pdf_url,
                "arxiv_id": "",
                "doi": doi,
                "source": "openalex",
            }
            paper_dict["bibtex"] = _format_single_bibtex(paper_dict)
            papers.append(paper_dict)

        return {"status": "success", "papers": papers, "count": len(papers)}
    except requests.RequestException as exc:
        return {"status": "error", "error_message": f"OpenAlex request failed: {exc}"}
    except Exception as exc:
        return {"status": "error", "error_message": f"Unexpected OpenAlex error: {exc}"}


def search_huggingface_daily_papers(
    query: str = "",
    max_results: int = 5,
    sort: str = "trending",
) -> dict[str, Any]:
    """Fetch trending AI/LLM/Agent papers from Hugging Face Daily Papers.

    Includes community upvotes, GitHub repository links, and direct alphaXiv URLs —
    ideal for high-signal LinkedIn and X technical commentary.

    Args:
        query: Optional keyword filter applied to title and abstract.
        max_results: Maximum papers to return (1-20, default: 5).
        sort: Sort order ("trending" or "publishedAt").

    Returns:
        Dictionary with status, papers list, and count.
    """
    max_results = max(1, min(int(max_results), 20))
    sort_mode = sort if sort in {"trending", "publishedAt"} else "trending"
    fetch_limit = 30 if query.strip() else max_results

    try:
        response = requests.get(
            HF_DAILY_PAPERS_URL,
            params={"sort": sort_mode, "limit": fetch_limit},
            headers={"User-Agent": "agentic-content-generation/2.1"},
            timeout=15,
        )
        response.raise_for_status()
        items = response.json()
        if not isinstance(items, list):
            return {"status": "error", "error_message": "Unexpected HuggingFace API format."}

        query_terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9]{2,}", query)]
        papers: list[dict[str, Any]] = []

        for entry in items:
            paper_obj = entry.get("paper") or entry
            arxiv_id = str(paper_obj.get("id") or entry.get("id") or "").strip()
            title = str(paper_obj.get("title") or entry.get("title") or "Untitled").strip()
            abstract = str(
                paper_obj.get("summary") or entry.get("summary") or paper_obj.get("abstract") or ""
            ).strip()

            if query_terms:
                haystack = f"{title} {abstract}".lower()
                if not any(term in haystack for term in query_terms):
                    continue

            raw_authors = paper_obj.get("authors") or []
            authors = [
                str(a.get("name") or a.get("fullname") or "").strip()
                for a in raw_authors[:6]
                if isinstance(a, dict) and (a.get("name") or a.get("fullname"))
            ]

            published_at = str(paper_obj.get("publishedAt") or entry.get("publishedAt") or "")
            year: int | None = None
            if len(published_at) >= 4 and published_at[:4].isdigit():
                year = int(published_at[:4])

            if len(abstract) > 1500:
                abstract = abstract[:1500] + "..."

            paper_dict: dict[str, Any] = {
                "title": title,
                "authors": authors,
                "year": year,
                "venue": "HuggingFace Daily Papers / arXiv",
                "citation_count": None,
                "upvotes": paper_obj.get("upvotes", entry.get("upvotes", 0)),
                "github_url": entry.get("githubUrl") or paper_obj.get("githubUrl") or "",
                "project_page": entry.get("projectPage") or paper_obj.get("projectPage") or "",
                "abstract": abstract or "No abstract available.",
                "url": f"https://huggingface.co/papers/{arxiv_id}" if arxiv_id else "",
                "alphaxiv_url": f"https://www.alphaxiv.org/abs/{arxiv_id}" if arxiv_id else "",
                "arxiv_id": arxiv_id,
                "doi": "",
                "source": "huggingface_daily",
            }
            paper_dict["bibtex"] = _format_single_bibtex(paper_dict)
            papers.append(paper_dict)
            if len(papers) >= max_results:
                break

        return {"status": "success", "papers": papers, "count": len(papers)}
    except requests.RequestException as exc:
        return {"status": "error", "error_message": f"HuggingFace Daily Papers failed: {exc}"}
    except Exception as exc:
        return {"status": "error", "error_message": f"Unexpected HuggingFace error: {exc}"}


def fetch_alphaxiv_overview(arxiv_id: str) -> dict[str, Any]:
    """Fetch structured Markdown research overview for an arXiv paper from alphaXiv.

    Provides alphaXiv's structured breakdown (core problem, methodology, experimental
    insights, limitations) directly for a validated arXiv ID.

    Args:
        arxiv_id: Valid arXiv ID (e.g., ``"2604.05018"``) or canonical arXiv/alphaXiv URL.

    Returns:
        Dictionary with status, arxiv_id, overview_markdown, and alphaxiv_url.
    """
    try:
        clean_id = validate_arxiv_id(arxiv_id)
    except ValueError as exc:
        return {"status": "error", "error_message": str(exc)}

    headers = {"User-Agent": "agentic-content-generation/2.1"}
    api_key = os.getenv("ALPHAXIV_API_KEY", "").strip()
    if api_key and not api_key.startswith("your_"):
        headers["Authorization"] = f"Bearer {api_key}"

    urls_to_try = [
        ALPHAXIV_OVERVIEW_TEMPLATE.format(arxiv_id=clean_id),
        ALPHAXIV_ABS_MD_TEMPLATE.format(arxiv_id=clean_id),
    ]

    last_error = "No overview returned."
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200 and response.text.strip():
                text = response.text.strip()
                # Reject HTML fallback pages if endpoint returned a web shell instead of Markdown
                if text.lower().startswith("<!doctype html") or "<html" in text[:200].lower():
                    last_error = f"HTML page returned instead of Markdown at {url}"
                    continue
                if len(text) > 6000:
                    text = text[:6000] + "\n...[truncated]..."
                return {
                    "status": "success",
                    "arxiv_id": clean_id,
                    "overview_markdown": text,
                    "alphaxiv_url": f"https://www.alphaxiv.org/abs/{clean_id}",
                    "source": "alphaxiv",
                }
            last_error = f"HTTP {response.status_code} from {url}"
        except requests.RequestException as exc:
            last_error = str(exc)

    return {
        "status": "error",
        "arxiv_id": clean_id,
        "alphaxiv_url": f"https://www.alphaxiv.org/abs/{clean_id}",
        "error_message": f"alphaXiv overview unavailable: {last_error}",
    }


def search_hal_papers(
    query: str,
    max_results: int = 5,
    year_from: int | None = None,
) -> dict[str, Any]:
    """Search HAL (French Open Archive — CNRS, INRIA, French universities).

    Particularly valuable for French CIR/CII R&D state-of-the-art documentation,
    applied econometrics, and French academic AI research.

    Args:
        query: Research query in French or English.
        max_results: Maximum papers to return (1-20, default: 5).
        year_from: Optional minimum publication year filter.

    Returns:
        Dictionary with status, papers list, and count.
    """
    if not query or not query.strip():
        return {"status": "error", "error_message": "HAL query cannot be empty."}

    max_results = max(1, min(int(max_results), 20))
    params: dict[str, Any] = {
        "q": query.strip(),
        "rows": max_results,
        "wt": "json",
        "fl": "title_s,abstract_s,authFullName_s,producedDateY_i,uri_s,doiId_s,journalTitle_s,halId_s",
    }
    if year_from:
        params["fq"] = f"producedDateY_i:[{int(year_from)} TO *]"

    try:
        response = requests.get(
            HAL_API_URL,
            params=params,
            headers={"User-Agent": "agentic-content-generation/2.1"},
            timeout=15,
        )
        response.raise_for_status()
        docs = response.json().get("response", {}).get("docs", [])

        papers: list[dict[str, Any]] = []
        for doc in docs[:max_results]:
            raw_title = doc.get("title_s", ["Untitled"])
            title = raw_title[0] if isinstance(raw_title, list) and raw_title else str(raw_title)

            raw_abs = doc.get("abstract_s", [])
            abstract = raw_abs[0] if isinstance(raw_abs, list) and raw_abs else str(raw_abs or "")
            if len(abstract) > 1500:
                abstract = abstract[:1500] + "..."

            authors = list(doc.get("authFullName_s", []))[:6]
            venue = str(doc.get("journalTitle_s") or "HAL Open Archive").strip()
            paper_dict: dict[str, Any] = {
                "title": title.strip(),
                "authors": authors,
                "year": doc.get("producedDateY_i"),
                "venue": venue,
                "citation_count": None,
                "abstract": abstract.strip() or "No abstract available.",
                "url": str(doc.get("uri_s") or "").strip(),
                "hal_id": str(doc.get("halId_s") or "").strip(),
                "arxiv_id": "",
                "doi": str(doc.get("doiId_s") or "").strip(),
                "source": "hal",
            }
            paper_dict["bibtex"] = _format_single_bibtex(paper_dict)
            papers.append(paper_dict)

        return {"status": "success", "papers": papers, "count": len(papers)}
    except requests.RequestException as exc:
        return {"status": "error", "error_message": f"HAL search failed: {exc}"}
    except Exception as exc:
        return {"status": "error", "error_message": f"Unexpected HAL error: {exc}"}


def fetch_arxiv_pdf_text(
    arxiv_id: str,
    max_pages: int = 8,
) -> dict[str, Any]:
    """Download and extract full text (in memory) from a validated arXiv PDF.

    Enables deep-dive extraction of benchmark tables, ablation numbers, and
    experimental setups beyond the abstract. Strictly bounded to ``arxiv.org/pdf``
    and capped at 15 MB to prevent SSRF and memory exhaustion.

    Args:
        arxiv_id: Valid arXiv ID (e.g., ``"2604.05018"``) or canonical arXiv URL.
        max_pages: Maximum number of PDF pages to extract (1-15, default: 8).

    Returns:
        Dictionary with status, arxiv_id, pages_extracted, text, and pdf_url.
    """
    if PdfReader is None:
        return {"status": "error", "error_message": "pypdf is not installed."}

    try:
        clean_id = validate_arxiv_id(arxiv_id)
    except ValueError as exc:
        return {"status": "error", "error_message": str(exc)}

    max_pages = max(1, min(int(max_pages), 15))
    pdf_url = ARXIV_PDF_TEMPLATE.format(arxiv_id=clean_id)

    try:
        response = requests.get(
            pdf_url,
            headers={"User-Agent": "agentic-content-generation/2.1"},
            timeout=25,
            stream=True,
        )
        response.raise_for_status()

        chunks: list[bytes] = []
        total_bytes = 0
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total_bytes += len(chunk)
            if total_bytes > MAX_PDF_BYTES:
                return {
                    "status": "error",
                    "error_message": f"PDF exceeds maximum allowed size ({MAX_PDF_BYTES // (1024 * 1024)} MB).",
                }
            chunks.append(chunk)

        pdf_bytes = b"".join(chunks)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages: list[str] = []
        for page in reader.pages[:max_pages]:
            page_text = (page.extract_text() or "").strip()
            if page_text:
                extracted_pages.append(page_text)

        full_text = "\n\n".join(extracted_pages)
        if len(full_text) > 8000:
            full_text = full_text[:8000] + "\n...[truncated]..."

        return {
            "status": "success",
            "arxiv_id": clean_id,
            "pdf_url": pdf_url,
            "pages_extracted": len(extracted_pages),
            "text": full_text,
        }
    except requests.RequestException as exc:
        return {"status": "error", "error_message": f"Failed to fetch arXiv PDF: {exc}"}
    except Exception as exc:
        return {"status": "error", "error_message": f"Failed to parse arXiv PDF: {exc}"}


def _strip_html(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _parse_rss_or_atom(xml_bytes: bytes, feed_name: str) -> list[dict[str, str]]:
    """Safely parse RSS 2.0 or Atom XML feeds using defusedxml."""
    root = DefusedET.fromstring(xml_bytes)
    items: list[dict[str, str]] = []

    # RSS 2.0: <rss><channel><item>
    for item in root.findall(".//item")[:10]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = _strip_html(item.findtext("description") or "")[:400]
        if title:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": pub,
                    "summary": desc,
                    "source_feed": feed_name,
                }
            )

    if items:
        return items

    # Atom: <feed xmlns="http://www.w3.org/2005/Atom"><entry>
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns)[:10]:
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.attrib.get("href", "").strip() if link_el is not None else ""
        pub = (
            entry.findtext("atom:updated", default="", namespaces=ns)
            or entry.findtext("atom:published", default="", namespaces=ns)
            or ""
        ).strip()
        summary = _strip_html(entry.findtext("atom:summary", default="", namespaces=ns) or "")[:400]
        if title:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": pub,
                    "summary": summary,
                    "source_feed": feed_name,
                }
            )
    return items


def fetch_industry_rss_feeds(
    category: str = "all",
    query: str = "",
    max_items: int = 8,
) -> dict[str, Any]:
    """Fetch recent articles from curated, allowlisted AdTech and AI Engineering RSS feeds.

    Security: Only queries strictly allowlisted feeds by category key (no arbitrary URLs).
    XML is parsed exclusively via ``defusedxml``.

    Args:
        category: ``"adtech"``, ``"ai_engineering"``, or ``"all"`` (default).
        query: Optional keyword filter applied across article titles and summaries.
        max_items: Maximum total items to return (1-20, default: 8).

    Returns:
        Dictionary with status, items list, count, and feeds_checked.
    """
    cat = category.strip().lower()
    if cat not in {"adtech", "ai_engineering", "all"}:
        return {
            "status": "error",
            "error_message": f"Invalid category '{category}'. Choose 'adtech', 'ai_engineering', or 'all'.",
        }

    max_items = max(1, min(int(max_items), 20))
    feeds = (
        CURATED_RSS_FEEDS["adtech"] + CURATED_RSS_FEEDS["ai_engineering"]
        if cat == "all"
        else CURATED_RSS_FEEDS[cat]
    )

    query_terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9]{2,}", query)]
    collected: list[dict[str, str]] = []
    errors: list[str] = []

    for feed_name, feed_url in feeds:
        try:
            resp = requests.get(
                feed_url,
                headers={"User-Agent": "agentic-content-generation/2.1"},
                timeout=10,
            )
            resp.raise_for_status()
            parsed = _parse_rss_or_atom(resp.content, feed_name)
            for item in parsed:
                if query_terms:
                    blob = f"{item['title']} {item['summary']}".lower()
                    if not any(term in blob for term in query_terms):
                        continue
                collected.append(item)
        except Exception as exc:
            errors.append(f"{feed_name}: {exc}")

    return {
        "status": "success",
        "items": collected[:max_items],
        "count": len(collected[:max_items]),
        "feeds_checked": [name for name, _ in feeds],
        "feed_errors": errors,
    }

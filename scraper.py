#!/usr/bin/env python3
"""
Web Page Change Monitor
Scrapes monitored pages, compares with previous snapshots,
and sends email notifications when changes are detected.
"""

import difflib
import json
import logging
import os
import re
import smtplib
import sys
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values
try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional fallback dependency
    PlaywrightError = Exception
    PlaywrightTimeoutError = Exception
    sync_playwright = None

from config import HISTORY_DIR, LOGS_DIR, MONITORED_PAGES, SECRETS_ENV_PATH, SNAPSHOTS_DIR

# Ensure directories exist
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# Setup logging
log_file = os.path.join(LOGS_DIR, f"scraper_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Request headers to mimic a browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Keep each email body under a conservative size and split into parts when needed.
MAX_EMAIL_BODY_CHARS = 90000
ERROR_STATE_PATH = os.path.join(HISTORY_DIR, "_fetch_error_state.json")


def slugify(name: str) -> str:
    """Convert a page name to a safe filename."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fetch_page(url: str) -> str:
    """Fetch HTML content from a URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code in {403, 429}:
            logger.info(f"Retrying with browser fallback for {url} after HTTP {status_code}")
            return fetch_page_with_browser(url)
        raise
    except requests.RequestException as exc:
        if should_retry_with_browser(exc):
            logger.info(f"Retrying with browser fallback for {url} after requests error: {exc}")
            return fetch_page_with_browser(url)
        raise


def should_retry_with_browser(error: requests.RequestException) -> bool:
    """Return True when a failed request is worth retrying in a real browser."""
    message = str(error).lower()
    retry_markers = [
        "connection refused",
        "remote end closed connection",
        "tls",
        "ssl",
        "403",
        "429",
    ]
    return any(marker in message for marker in retry_markers)


def fetch_page_with_browser(url: str) -> str:
    """Fetch page HTML using headless Chromium for bot-protected sites."""
    if sync_playwright is None:
        raise requests.RequestException(
            f"Browser fallback unavailable because Playwright is not installed for {url}"
        )

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="en-US",
            )
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if response is not None and response.status >= 400:
                error_response = requests.Response()
                error_response.status_code = response.status
                error_response.url = url
                raise requests.HTTPError(
                    f"{response.status} Client Error: browser fetch failed for url: {url}",
                    response=error_response,
                )
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except PlaywrightTimeoutError:
                pass
            html = page.content()
            browser.close()
            return html
    except (PlaywrightError, PlaywrightTimeoutError) as exc:
        raise requests.RequestException(f"Browser fetch failed for {url}: {exc}") from exc


def is_pga_tour_page(page: dict | None) -> bool:
    """Return True when the page is one of the PGA TOUR legal pages."""
    if not page:
        return False
    company = page.get("company", "")
    url = page.get("url", "")
    return company == "PGA TOUR" or "pgatour.com/company/" in url


def is_redfin_page(page: dict | None) -> bool:
    """Return True when the page is one of the Redfin legal/support pages."""
    if not page:
        return False
    company = page.get("company", "")
    url = page.get("url", "")
    return company == "Redfin" or "redfin.com" in url


def is_royal_caribbean_page(page: dict | None) -> bool:
    """Return True when the page is one of the Royal Caribbean legal pages."""
    if not page:
        return False
    company = page.get("company", "")
    url = page.get("url", "")
    return company == "Royal Caribbean" or "royalcaribbean" in url


def normalize_text_from_node(node: BeautifulSoup) -> str:
    """Extract normalized text from a DOM node."""
    text = node.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]

    cleaned = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned.append("")
                prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    return "\n".join(cleaned).strip()


def clean_royal_caribbean_text(text: str) -> str:
    """Normalize broken inline text fragments from Royal Caribbean pages."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"(\d)\s+(st|nd|rd|th)\b", r"\1\2", text)
    text = re.sub(r"(\d(?:st|nd|rd|th))\n&\s*(\d(?:st|nd|rd|th))\n+([A-Za-z])", r"\1 & \2 \3", text)
    text = re.sub(r"(\d(?:st|nd|rd|th))\n+([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])\n+([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"\bGuest\s+s\b", "Guests", text)
    text = re.sub(r"\b([A-Za-z])\s+\.\s+([A-Za-z])\b", r"\1. \2", text)
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"([A-Za-z0-9])\n([a-z])", r"\1 \2", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pga_tour_text(soup: BeautifulSoup) -> str:
    """Extract only the PGA TOUR legal content, excluding live widgets and page chrome."""
    selector_candidates = [
        'div[class*="PageContainer_innerContainer"]',
        'div[class*="PageContainer_grid"]',
        'main',
    ]

    selected = None
    for selector in selector_candidates:
        for candidate in soup.select(selector):
            candidate_text = " ".join(candidate.get_text(" ", strip=True).split())
            if "terms" in candidate_text.lower() and len(candidate_text) > 1000:
                selected = deepcopy(candidate)
                break
        if selected is not None:
            break

    if selected is None:
        selected = deepcopy(soup)

    for tag in selected(["script", "style", "nav", "header", "footer", "noscript", "meta", "link", "aside"]):
        tag.decompose()

    noise_selectors = [
        '[class*="Leaderboard"]',
        '[class*="leaderboard"]',
        '[class*="Footer"]',
        '[class*="footer"]',
        '[class*="Sidebar"]',
        '[class*="sidebar"]',
        '.no-print',
    ]
    for selector in noise_selectors:
        for node in selected.select(selector):
            node.decompose()

    text = normalize_text_from_node(selected)
    marker = "Terms"
    marker_index = text.find(marker)
    if marker_index > 0:
        text = text[marker_index:].strip()
    return text


def extract_redfin_text(soup: BeautifulSoup) -> str:
    """Extract Redfin terms text while excluding MLS disclaimer noise."""
    selected = soup.find(class_="TermsOfUse") or soup.find(id="content") or soup
    selected = deepcopy(selected)

    for tag in selected(["script", "style", "nav", "header", "footer", "noscript", "meta", "link", "aside"]):
        tag.decompose()

    noise_selectors = [
        ".disclaimerContent",
        ".disclaimer",
        '[id*="disclaimer"]',
        '[class*="disclaimer"]',
        ".legal",
        ".text-center.font-color-gray-light.font-size-smaller",
    ]
    for selector in noise_selectors:
        for node in selected.select(selector):
            node.decompose()

    text = normalize_text_from_node(selected)
    marker = "Redfin Terms of Use"
    marker_index = text.find(marker)
    if marker_index > 0:
        text = text[marker_index:].strip()

    end_markers = [
        "2.10. Location-Specific Agreements and Disclaimers for MLS",
        "ADDENDUM: REDFIN MORTGAGE SERVICES",
        "ADDENDUM: WALK SCORE SERVICES",
    ]
    for end_marker in end_markers:
        end_index = text.find(end_marker)
        if end_index > 0:
            text = text[:end_index].rstrip()
            break

    return text


def extract_royal_caribbean_text(soup: BeautifulSoup) -> str:
    """Extract Royal Caribbean legal/promotions text while excluding page chrome."""
    selector_candidates = [
        ".termsAndCondXFContainer",
        ".textUI__base",
        "#root",
        "main",
    ]

    selected = None
    for selector in selector_candidates:
        for candidate in soup.select(selector):
            candidate_text = " ".join(candidate.get_text(" ", strip=True).split())
            if "terms" in candidate_text.lower() and len(candidate_text) > 500:
                selected = deepcopy(candidate)
                break
        if selected is not None:
            break

    if selected is None:
        selected = deepcopy(soup)

    for tag in selected(["script", "style", "nav", "header", "footer", "noscript", "meta", "link", "aside"]):
        tag.decompose()

    noise_selectors = [
        ".page__main--newStructure",
        ".skip-to-content",
        ".globalnav",
        ".footer",
        '[class*="footer"]',
        '[class*="nav"]',
        '[class*="Navigation"]',
    ]
    for selector in noise_selectors:
        for node in selected.select(selector):
            node.decompose()

    text = normalize_text_from_node(selected)
    start_markers = [
        "PROMOTIONS TERMS AND CONDITIONS",
        "Terms and Conditions",
    ]
    for marker in start_markers:
        marker_index = text.find(marker)
        if marker_index >= 0:
            text = text[marker_index:].strip()
            break

    return clean_royal_caribbean_text(text)


def extract_text(html: str, page: dict | None = None) -> str:
    """Extract meaningful text content from HTML, stripping boilerplate."""
    soup = BeautifulSoup(html, "lxml")

    if is_pga_tour_page(page):
        return extract_pga_tour_text(soup)
    if is_redfin_page(page):
        return extract_redfin_text(soup)
    if is_royal_caribbean_page(page):
        return extract_royal_caribbean_text(soup)

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "meta", "link"]):
        tag.decompose()

    return normalize_text_from_node(soup)


def get_snapshot_path(name: str) -> str:
    """Get the file path for a page's snapshot."""
    return os.path.join(SNAPSHOTS_DIR, f"{slugify(name)}.txt")


def load_snapshot(name: str) -> str | None:
    """Load a previous snapshot. Returns None if no snapshot exists."""
    path = get_snapshot_path(name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def save_snapshot(name: str, content: str) -> None:
    """Save current content as a snapshot."""
    path = get_snapshot_path(name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Snapshot saved: {path}")


def get_history_path(name: str) -> str:
    """Get the JSON history file path for a specific page."""
    return os.path.join(HISTORY_DIR, f"{slugify(name)}.json")


def load_history(name: str) -> dict:
    """Load the JSON history file for a specific page."""
    path = get_history_path(name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_to_history(name: str, date_str: str, url: str, content: str, changed: bool) -> None:
    """Save scraped content into the page's JSON history file under today's date."""
    history = load_history(name)

    history[date_str] = {
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "content_length": len(content),
        "changed": changed,
        "content": content,
    }

    path = get_history_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    logger.info(f"History saved: {path} ({date_str})")


def load_error_state() -> dict:
    """Load persisted fetch-error state for deduplicating repeated alerts."""
    if os.path.exists(ERROR_STATE_PATH):
        with open(ERROR_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_error_state(state: dict) -> None:
    """Persist fetch-error state for future runs."""
    with open(ERROR_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def error_signature(url: str, error: str) -> str:
    """Create a stable signature for a fetch error on a page."""
    return f"{url}::{error}"


def compare(old_text: str, new_text: str, page_name: str) -> str | None:
    """Compare old and new text. Returns unified diff string or None if identical."""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{page_name} (previous)",
            tofile=f"{page_name} (current)",
            lineterm="",
        )
    )

    if diff:
        return "\n".join(diff)
    return None


def parse_diff_lines(diff: str) -> tuple[list[str], list[str]]:
    """Parse a unified diff string into lists of added and removed lines."""
    additions = []
    deletions = []
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            text = line[1:].strip()
            if text:
                additions.append(text)
        elif line.startswith("-"):
            text = line[1:].strip()
            if text:
                deletions.append(text)
    return additions, deletions


def is_reorder(additions: list[str], deletions: list[str]) -> bool:
    """Return True if the diff is a pure reorder (same items, different order)."""
    if not additions or not deletions:
        return False
    return set(additions) == set(deletions)


def dedupe_preserving_order(items: list[str]) -> list[str]:
    """Remove duplicate items while preserving the first-seen order."""
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items


def classify_brand(result: dict) -> str:
    """Map a page result to a brand bucket for summary output."""
    if result.get("company"):
        return result["company"]
    if "47brand" in result["url"].lower() or "47Brand" in result["name"]:
        return "47Brand"
    if "otterbox" in result["url"].lower():
        return "OtterBox"
    return result["name"]


def build_shared_note(peers: list[dict]) -> str:
    """Describe a repeated change pattern shared across multiple pages."""
    if len(peers) == 2 and all(classify_brand(peer) == "47Brand" for peer in peers):
        return (
            "The changes on both 47Brand pages appear identical and likely reflect an "
            "update to shared site navigation or footer links rather than page-specific legal text."
        )

    if len(peers) == 2:
        return (
            "The changes on both pages appear identical and likely reflect shared site "
            "navigation or footer updates rather than page-specific content."
        )

    return (
        f"The changes across these {len(peers)} pages appear identical and likely reflect "
        "a shared site navigation or footer update rather than page-specific content."
    )


def format_initial_snapshot_email(company: str, pages: list[dict]) -> str:
    """Build one first-run email body for all pages in a company."""
    lines = [
        f"Initial snapshots have been captured for {company}.",
        "",
    ]

    for idx, page in enumerate(pages, start=1):
        lines.extend(
            [
                f"{idx}. {page['name']}",
                f"URL: {page['url']}",
                f"Timestamp: {page['timestamp']}",
                "",
            ]
        )

    lines.extend(
        [
            "Future changes will be reported in consolidated monitoring emails.",
            "",
            "The latest page snapshots are attached.",
        ]
    )
    return "\n".join(lines)


def format_error_email(company: str, errors: list[dict]) -> str:
    """Build one error email body for all failed pages in a company."""
    lines = [
        f"One or more pages for {company} could not be fetched.",
        "",
    ]

    for idx, error in enumerate(errors, start=1):
        lines.extend(
            [
                f"{idx}. {error['name']}",
                f"URL: {error['url']}",
                f"Timestamp: {error['timestamp']}",
                f"Error: {error['error']}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def format_company_change_section(company: str, page_results: list[dict]) -> str:
    """Wrap a company's change report in a company section heading."""
    return "\n".join(
        [
            f"Company: {company}",
            "",
            format_structured_email(page_results),
        ]
    )


def format_company_initial_section(company: str, pages: list[dict]) -> str:
    """Wrap a company's first-snapshot report in a company section heading."""
    return "\n".join(
        [
            f"Company: {company}",
            "",
            format_initial_snapshot_email(company, pages),
        ]
    )


def format_company_error_section(company: str, errors: list[dict]) -> str:
    """Wrap a company's fetch-error report in a company section heading."""
    return "\n".join(
        [
            f"Company: {company}",
            "",
            format_error_email(company, errors),
        ]
    )


def split_text_to_limit(text: str, limit: int) -> list[str]:
    """Split oversized text into line-based chunks within the given character limit."""
    if len(text) <= limit:
        return [text]

    chunks = []
    current_lines = []
    current_len = 0

    for line in text.splitlines():
        line_with_break = f"{line}\n"
        if len(line_with_break) > limit:
            if current_lines:
                chunks.append("\n".join(current_lines).rstrip())
                current_lines = []
                current_len = 0

            start = 0
            while start < len(line):
                end = min(start + limit, len(line))
                chunks.append(line[start:end])
                start = end
            continue

        if current_len + len(line_with_break) > limit and current_lines:
            chunks.append("\n".join(current_lines).rstrip())
            current_lines = [line]
            current_len = len(line_with_break)
        else:
            current_lines.append(line)
            current_len += len(line_with_break)

    if current_lines:
        chunks.append("\n".join(current_lines).rstrip())

    return chunks


def build_email_parts(sections: list[dict], limit: int) -> list[dict]:
    """Pack notification sections into one or more email parts."""
    parts = []
    current_body = ""
    current_attachments: list[str] = []

    for section in sections:
        section_chunks = split_text_to_limit(section["body"], limit)
        for idx, section_chunk in enumerate(section_chunks):
            candidate = section_chunk if not current_body else f"{current_body}\n\n{section_chunk}"
            chunk_attachments = section["attachments"] if idx == 0 else []

            if current_body and len(candidate) > limit:
                parts.append({
                    "body": current_body,
                    "attachments": list(dict.fromkeys(current_attachments)),
                })
                current_body = section_chunk
                current_attachments = list(chunk_attachments)
            else:
                current_body = candidate
                current_attachments.extend(chunk_attachments)

    if current_body:
        parts.append({
            "body": current_body,
            "attachments": list(dict.fromkeys(current_attachments)),
        })

    return parts


def send_batched_emails(
    email_config: dict,
    sections: list[dict],
    run_timestamp: str,
) -> None:
    """Send one consolidated email, split into additional parts if needed."""
    if not sections:
        return

    intro = "\n".join(
        [
            "Web Page Change Monitor Summary",
            f"Run Timestamp: {run_timestamp}",
        ]
    )
    parts = build_email_parts(sections, MAX_EMAIL_BODY_CHARS - len(intro) - 32)

    total_parts = len(parts)
    for idx, part in enumerate(parts, start=1):
        body = "\n\n".join(
            [
                intro,
                f"Email Part: {idx} of {total_parts}",
                "",
                part["body"],
            ]
        )
        subject = "[Page Monitor] Consolidated summary"
        if total_parts > 1:
            subject += f" (Part {idx}/{total_parts})"

        send_email(subject, body, email_config, attachments=part["attachments"])


def format_structured_email(page_results: list[dict]) -> str:
    """Build a structured, human-readable email body from page change results."""

    def change_key(r):
        return (
            r["reorder"],
            tuple(r["additions"]),
            tuple(r["deletions"]),
        )

    # Detect pages that share identical changes
    shared_groups: dict = {}
    for result in page_results:
        key = change_key(result)
        shared_groups.setdefault(key, []).append(result)

    sections = []
    for idx, result in enumerate(page_results, start=1):
        name = result["name"]
        url = result["url"]
        timestamp = result["timestamp"]
        additions = result["additions"]
        deletions = result["deletions"]
        reorder = result["reorder"]

        lines = [f"{idx}. {name}"]
        lines.append(f"URL: {url}")
        lines.append(f"Timestamp: {timestamp}")

        if reorder:
            lines.append("Observed change:")
            lines.append("No content appears to have been newly added or removed.")
            lines.append("The detected difference is a reordering of existing policy/support links.")
            lines.append("Links reordered:")
            for item in additions:
                lines.append(item)
        else:
            if additions:
                lines.append("Additions:")
                for item in additions:
                    lines.append(item)
            if deletions:
                lines.append("Deletions:")
                for item in deletions:
                    lines.append(item)
            if not additions and not deletions:
                lines.append("Observed change:")
                lines.append("A text difference was detected, but no distinct added or removed lines were identified.")

        # Add one shared note at the end of a repeated change group.
        peers = shared_groups[change_key(result)]
        if len(peers) > 1 and peers[-1]["name"] == name:
            lines.append("Note:")
            lines.append(build_shared_note(peers))

        sections.append("\n".join(lines))

    # Overall Summary
    summary_lines = ["Overall Summary"]
    brand_summaries: dict = {}
    for result in page_results:
        brand = classify_brand(result)
        brand_summaries.setdefault(brand, []).append(result)

    for brand, results in brand_summaries.items():
        all_reorders = all(result["reorder"] for result in results)
        if all_reorders:
            summary_lines.append(
                f"{brand}: Existing links were rearranged, with no clear net additions or deletions."
            )
        else:
            unique_change_patterns = {
                (
                    tuple(result["additions"]),
                    tuple(result["deletions"]),
                    result["reorder"],
                )
                for result in results
                if not result["reorder"]
            }
            sample = next(result for result in results if not result["reorder"])
            add_count = len(sample["additions"])
            del_count = len(sample["deletions"])
            if len(results) > 1 and len(unique_change_patterns) == 1:
                summary_lines.append(
                    f"{brand}: {add_count} new link(s) were added and {del_count} existing label(s) were removed."
                )
            else:
                summary_lines.append(
                    f"{brand}: {add_count} item(s) added, {del_count} item(s) removed."
                )

    return "\n\n".join(sections) + "\n\n" + "\n".join(summary_lines)


def load_email_config() -> dict:
    """Load email configuration from the secrets env file."""
    if not os.path.exists(SECRETS_ENV_PATH):
        logger.error(f"Secrets file not found: {SECRETS_ENV_PATH}")
        sys.exit(1)

    secrets = dotenv_values(SECRETS_ENV_PATH)

    required_keys = ["SMTP_SERVER", "SMTP_PORT", "SENDER_EMAIL", "SENDER_PASSWORD", "RECEIVER_EMAILS"]
    for key in required_keys:
        if key not in secrets:
            logger.error(f"Missing key '{key}' in {SECRETS_ENV_PATH}")
            sys.exit(1)

    return {
        "smtp_server": secrets["SMTP_SERVER"],
        "smtp_port": int(secrets["SMTP_PORT"]),
        "use_ssl": secrets.get("USE_SSL", "false").lower() == "true",
        "sender_email": secrets["SENDER_EMAIL"],
        "sender_password": secrets["SENDER_PASSWORD"],
        "receiver_emails": [e.strip() for e in secrets["RECEIVER_EMAILS"].split(",")],
    }


def send_email(subject: str, body: str, email_config: dict, attachments: list[str] | None = None) -> None:
    """Send an email notification with optional file attachments."""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = email_config["sender_email"]
    msg["To"] = ", ".join(email_config["receiver_emails"])

    # Plain text body
    msg.attach(MIMEText(body, "plain"))

    # Attach files
    for filepath in (attachments or []):
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(filepath)}")
            msg.attach(part)

    try:
        if email_config["use_ssl"]:
            server = smtplib.SMTP_SSL(email_config["smtp_server"], email_config["smtp_port"])
        else:
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()

        server.login(email_config["sender_email"], email_config["sender_password"])
        server.sendmail(
            email_config["sender_email"],
            email_config["receiver_emails"],
            msg.as_string(),
        )
        server.quit()
        logger.info(f"Email sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def main():
    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("=" * 60)
    logger.info("Web Page Change Monitor - Starting run")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    email_config = load_email_config()
    today = datetime.now().strftime("%Y-%m-%d")
    persisted_error_state = load_error_state()
    current_error_state = dict(persisted_error_state)
    changes_found = 0
    page_results_by_company: dict[str, list[dict]] = defaultdict(list)
    snapshot_attachments_by_company: dict[str, list[str]] = defaultdict(list)
    initial_pages_by_company: dict[str, list[dict]] = defaultdict(list)
    initial_attachments_by_company: dict[str, list[str]] = defaultdict(list)
    errors_by_company: dict[str, list[dict]] = defaultdict(list)

    for page in MONITORED_PAGES:
        company = page.get("company") or classify_brand(page)
        name = page["name"]
        url = page["url"]
        logger.info(f"\nChecking: {name}")
        logger.info(f"URL: {url}")

        try:
            html = fetch_page(url)
            current_text = extract_text(html, page)
            previous_text = load_snapshot(name)

            if previous_text is None:
                # First run - save initial snapshot
                save_snapshot(name, current_text)
                save_to_history(name, today, url, current_text, changed=False)
                current_error_state.pop(name, None)
                logger.info(f"First snapshot captured for: {name}")
                initial_pages_by_company[company].append({
                    "name": name,
                    "url": url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                initial_attachments_by_company[company].append(get_snapshot_path(name))
            else:
                diff = compare(previous_text, current_text, name)
                if diff:
                    changes_found += 1
                    logger.info(f"CHANGES DETECTED for: {name}")
                    save_snapshot(name, current_text)
                    save_to_history(name, today, url, current_text, changed=True)
                    current_error_state.pop(name, None)

                    additions, deletions = parse_diff_lines(diff)
                    additions = dedupe_preserving_order(additions)
                    deletions = dedupe_preserving_order(deletions)
                    reorder = is_reorder(additions, deletions)
                    page_results_by_company[company].append({
                        "company": company,
                        "name": name,
                        "url": url,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "additions": additions,
                        "deletions": deletions,
                        "reorder": reorder,
                    })
                    snapshot_attachments_by_company[company].append(get_snapshot_path(name))
                else:
                    save_to_history(name, today, url, current_text, changed=False)
                    current_error_state.pop(name, None)
                    logger.info(f"No changes detected for: {name}")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {name}: {e}")
            error_text = str(e)
            signature = error_signature(url, error_text)
            if persisted_error_state.get(name) != signature:
                errors_by_company[company].append({
                    "name": name,
                    "url": url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": error_text,
                })
            current_error_state[name] = signature
        except Exception as e:
            logger.error(f"Unexpected error for {name}: {e}")

    sections = []

    if initial_pages_by_company:
        for company in sorted(initial_pages_by_company):
            sections.append({
                "body": "\n".join(
                    [
                        "=== Initial Snapshots ===",
                        format_company_initial_section(company, initial_pages_by_company[company]),
                    ]
                ),
                "attachments": initial_attachments_by_company[company],
            })

    if page_results_by_company:
        for company in sorted(page_results_by_company):
            sections.append({
                "body": "\n".join(
                    [
                        "=== Detected Changes ===",
                        format_company_change_section(company, page_results_by_company[company]),
                    ]
                ),
                "attachments": snapshot_attachments_by_company[company],
            })

    if errors_by_company:
        for company in sorted(errors_by_company):
            sections.append({
                "body": "\n".join(
                    [
                        "=== Fetch Errors ===",
                        format_company_error_section(company, errors_by_company[company]),
                    ]
                ),
                "attachments": [],
            })

    send_batched_emails(email_config, sections, run_timestamp)
    save_error_state(current_error_state)

    logger.info(f"\nRun complete. Changes found: {changes_found}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

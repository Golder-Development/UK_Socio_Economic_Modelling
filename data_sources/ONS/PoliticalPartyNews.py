"""
UK party official announcements proxy counter.

Counts items in each party's official news/press archive since a given date.
Big 6: Conservative, Labour, Lib Dem, SNP, Green, Reform.

Notes:
- This is a proxy: "official posts in the party press/news archive".
- Party sites change. If one parser breaks, the script will tell you which.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class Post:
    party: str
    title: str
    url: str
    published: date


@dataclass(frozen=True)
class PartyConfig:
    name: str
    start_url: str
    fetch_pages: Callable[[requests.Session, str, date], Iterable[str]]
    parse_posts: Callable[[str, str], List[Post]]  # (html, base_url) -> posts


def _session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    return sess


def _get(sess: requests.Session, url: str, timeout: int = 30) -> str:
    resp = sess.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _parse_date_loose(text: str) -> Optional[date]:
    """
    Parse a date from common UK site formats.
    Returns None if it can't parse.
    """
    t = re.sub(r"\s+", " ", text.strip())

    # Common patterns: "5 July 2024", "05 Jul 2024", "2024-07-05"
    fmts = [
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue

    # Try to extract e.g. "5 July 2024" from longer strings
    m = re.search(r"(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})", t)
    if m:
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(m.group(1), fmt).date()
            except ValueError:
                continue

    # ISO date inside attributes
    m = re.search(r"(\d{4}-\d{2}-\d{2})", t)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None

    return None


# -------------------------
# Party-specific scrapers
# -------------------------

def labour_fetch_pages(sess: requests.Session, start_url: str, since: date) -> Iterable[str]:
    """
    Labour press releases are paginated with /page/{n}/.
    We keep paging until the oldest date on a page is before 'since'.
    """
    page = 1
    while True:
        url = start_url if page == 1 else urljoin(start_url.rstrip("/") + "/", f"page/{page}/")
        html = _get(sess, url)
        yield html

        posts = labour_parse_posts(html, start_url)
        if not posts:
            break

        oldest = min(p.published for p in posts)
        if oldest < since:
            break

        page += 1
        time.sleep(0.4)


def labour_parse_posts(html: str, base_url: str) -> List[Post]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Post] = []

    # Labour pages commonly have article cards with time/date
    for card in soup.select("article"):
        a = card.select_one("a")
        if not a or not a.get("href"):
            continue

        title = a.get_text(" ", strip=True) or "Untitled"
        url = urljoin(base_url, a["href"])

        # Look for <time> or date text
        dt = None
        t = card.select_one("time")
        if t and (t.get("datetime") or t.get_text(strip=True)):
            dt = _parse_date_loose(t.get("datetime", "") or t.get_text(strip=True))
        if dt is None:
            # fallback: any element with "date"
            d_el = card.select_one(".date, .post-date, .entry-date")
            if d_el:
                dt = _parse_date_loose(d_el.get_text(" ", strip=True))

        if dt is None:
            continue

        out.append(Post(party="Labour", title=title, url=url, published=dt))
    return out


def conservatives_fetch_pages(sess: requests.Session, start_url: str, since: date) -> Iterable[str]:
    """
    Conservatives news often uses "Earlier" pagination.
    We follow the "Earlier" link until a page's oldest post is before since.
    """
    next_url = start_url
    seen_urls = set()

    while next_url and next_url not in seen_urls:
        seen_urls.add(next_url)
        html = _get(sess, next_url)
        yield html

        posts = conservatives_parse_posts(html, next_url)
        if not posts:
            break

        oldest = min(p.published for p in posts)
        if oldest < since:
            break

        soup = BeautifulSoup(html, "html.parser")
        # Try to find a link that indicates older items
        link = soup.find("a", string=re.compile(r"Earlier|Older|Next", re.I))
        if link and link.get("href"):
            next_url = urljoin(next_url, link["href"])
        else:
            # fallback: try rel="next"
            rel_next = soup.find("a", rel=lambda v: v and "next" in v)
            next_url = urljoin(next_url, rel_next["href"]) if rel_next and rel_next.get("href") else ""

        time.sleep(0.4)


def conservatives_parse_posts(html: str, base_url: str) -> List[Post]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Post] = []

    # Conservative news cards can vary; try common patterns
    for card in soup.select("article, .news-card, .card"):
        a = card.select_one("a[href]")
        if not a:
            continue

        title = a.get_text(" ", strip=True) or "Untitled"
        url = urljoin(base_url, a["href"])

        dt = None
        t = card.select_one("time")
        if t:
            dt = _parse_date_loose(t.get("datetime", "") or t.get_text(" ", strip=True))
        if dt is None:
            d_el = card.select_one(".date, .post-date, .entry-date, .meta__date")
            if d_el:
                dt = _parse_date_loose(d_el.get_text(" ", strip=True))

        if dt is None:
            continue

        out.append(Post(party="Conservative", title=title, url=url, published=dt))

    return out


def libdem_fetch_pages(sess: requests.Session, start_url: str, since: date) -> Iterable[str]:
    """
    Lib Dem press pages are paginated; typically /press?page=N or /press/page/N.
    We'll try both styles by detecting a "next" link.
    """
    next_url = start_url
    seen_urls = set()

    while next_url and next_url not in seen_urls:
        seen_urls.add(next_url)
        html = _get(sess, next_url)
        yield html

        posts = libdem_parse_posts(html, next_url)
        if not posts:
            break

        oldest = min(p.published for p in posts)
        if oldest < since:
            break

        soup = BeautifulSoup(html, "html.parser")
        # Detect next page link
        nxt = soup.find("a", string=re.compile(r"Next|Older|→", re.I))
        if nxt and nxt.get("href"):
            next_url = urljoin(next_url, nxt["href"])
        else:
            # fallback: common pagination rel next
            rel_next = soup.find("a", rel=lambda v: v and "next" in v)
            next_url = urljoin(next_url, rel_next["href"]) if rel_next and rel_next.get("href") else ""

        time.sleep(0.4)


def libdem_parse_posts(html: str, base_url: str) -> List[Post]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Post] = []

    for card in soup.select("article, .press-release, .card, .item"):
        a = card.select_one("a[href]")
        if not a:
            continue
        title = a.get_text(" ", strip=True) or "Untitled"
        url = urljoin(base_url, a["href"])

        dt = None
        t = card.select_one("time")
        if t:
            dt = _parse_date_loose(t.get("datetime", "") or t.get_text(" ", strip=True))
        if dt is None:
            d_el = card.select_one(".date, .post-date, .entry-date")
            if d_el:
                dt = _parse_date_loose(d_el.get_text(" ", strip=True))

        if dt is None:
            continue

        out.append(Post(party="Lib Dem", title=title, url=url, published=dt))

    return out


def snp_fetch_pages(sess: requests.Session, start_url: str, since: date) -> Iterable[str]:
    """
    SNP news often paginated with page numbers or "load more".
    We'll follow rel=next or "Older/Next" links.
    """
    next_url = start_url
    seen_urls = set()

    while next_url and next_url not in seen_urls:
        seen_urls.add(next_url)
        html = _get(sess, next_url)
        yield html

        posts = snp_parse_posts(html, next_url)
        if not posts:
            break

        oldest = min(p.published for p in posts)
        if oldest < since:
            break

        soup = BeautifulSoup(html, "html.parser")
        rel_next = soup.find("a", rel=lambda v: v and "next" in v)
        if rel_next and rel_next.get("href"):
            next_url = urljoin(next_url, rel_next["href"])
        else:
            nxt = soup.find("a", string=re.compile(r"Older|Next", re.I))
            next_url = urljoin(next_url, nxt["href"]) if nxt and nxt.get("href") else ""

        time.sleep(0.4)


def snp_parse_posts(html: str, base_url: str) -> List[Post]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Post] = []

    for card in soup.select("article, .post, .news-item, .card"):
        a = card.select_one("a[href]")
        if not a:
            continue
        title = a.get_text(" ", strip=True) or "Untitled"
        url = urljoin(base_url, a["href"])

        dt = None
        t = card.select_one("time")
        if t:
            dt = _parse_date_loose(t.get("datetime", "") or t.get_text(" ", strip=True))
        if dt is None:
            d_el = card.select_one(".date, .post-date, .entry-date")
            if d_el:
                dt = _parse_date_loose(d_el.get_text(" ", strip=True))

        if dt is None:
            continue

        out.append(Post(party="SNP", title=title, url=url, published=dt))

    return out


def greens_fetch_pages(sess: requests.Session, start_url: str, since: date) -> Iterable[str]:
    """
    Green Party (England & Wales) news is usually paginated.
    Follow rel=next or explicit Next.
    """
    next_url = start_url
    seen_urls = set()

    while next_url and next_url not in seen_urls:
        seen_urls.add(next_url)
        html = _get(sess, next_url)
        yield html

        posts = greens_parse_posts(html, next_url)
        if not posts:
            break

        oldest = min(p.published for p in posts)
        if oldest < since:
            break

        soup = BeautifulSoup(html, "html.parser")
        rel_next = soup.find("a", rel=lambda v: v and "next" in v)
        if rel_next and rel_next.get("href"):
            next_url = urljoin(next_url, rel_next["href"])
        else:
            nxt = soup.find("a", string=re.compile(r"Next|Older", re.I))
            next_url = urljoin(next_url, nxt["href"]) if nxt and nxt.get("href") else ""

        time.sleep(0.4)


def greens_parse_posts(html: str, base_url: str) -> List[Post]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Post] = []

    for card in soup.select("article, .post, .news-item, .card"):
        a = card.select_one("a[href]")
        if not a:
            continue
        title = a.get_text(" ", strip=True) or "Untitled"
        url = urljoin(base_url, a["href"])

        dt = None
        t = card.select_one("time")
        if t:
            dt = _parse_date_loose(t.get("datetime", "") or t.get_text(" ", strip=True))
        if dt is None:
            d_el = card.select_one(".date, .post-date, .entry-date")
            if d_el:
                dt = _parse_date_loose(d_el.get_text(" ", strip=True))

        if dt is None:
            continue

        out.append(Post(party="Green", title=title, url=url, published=dt))

    return out


def reform_fetch_pages(sess: requests.Session, start_url: str, since: date) -> Iterable[str]:
    """
    Reform news/press page pagination varies. We'll follow rel=next or "Next".
    """
    next_url = start_url
    seen_urls = set()

    while next_url and next_url not in seen_urls:
        seen_urls.add(next_url)
        html = _get(sess, next_url)
        yield html

        posts = reform_parse_posts(html, next_url)
        if not posts:
            break

        oldest = min(p.published for p in posts)
        if oldest < since:
            break

        soup = BeautifulSoup(html, "html.parser")
        rel_next = soup.find("a", rel=lambda v: v and "next" in v)
        if rel_next and rel_next.get("href"):
            next_url = urljoin(next_url, rel_next["href"])
        else:
            nxt = soup.find("a", string=re.compile(r"Next|Older", re.I))
            next_url = urljoin(next_url, nxt["href"]) if nxt and nxt.get("href") else ""

        time.sleep(0.4)


def reform_parse_posts(html: str, base_url: str) -> List[Post]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Post] = []

    for card in soup.select("article, .post, .news-item, .card"):
        a = card.select_one("a[href]")
        if not a:
            continue
        title = a.get_text(" ", strip=True) or "Untitled"
        url = urljoin(base_url, a["href"])

        dt = None
        t = card.select_one("time")
        if t:
            dt = _parse_date_loose(t.get("datetime", "") or t.get_text(" ", strip=True))
        if dt is None:
            d_el = card.select_one(".date, .post-date, .entry-date")
            if d_el:
                dt = _parse_date_loose(d_el.get_text(" ", strip=True))

        if dt is None:
            continue

        out.append(Post(party="Reform", title=title, url=url, published=dt))

    return out


# -------------------------
# Runner + output
# -------------------------

def _count_since(posts: List[Post], since: date) -> Tuple[int, List[Post]]:
    filtered = [p for p in posts if p.published >= since]
    return len(filtered), filtered


def _dedupe(posts: List[Post]) -> List[Post]:
    seen = set()
    out = []
    for p in posts:
        key = (p.party, p.url)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def build_configs() -> List[PartyConfig]:
    # You can edit these URLs if the parties change their structure.
    return [
        PartyConfig(
            name="Conservative",
            start_url="https://www.conservatives.com/news",
            fetch_pages=conservatives_fetch_pages,
            parse_posts=conservatives_parse_posts,
        ),
        PartyConfig(
            name="Labour",
            start_url="https://labour.org.uk/updates/press-releases/",
            fetch_pages=labour_fetch_pages,
            parse_posts=labour_parse_posts,
        ),
        PartyConfig(
            name="Lib Dem",
            start_url="https://www.libdems.org.uk/press",
            fetch_pages=libdem_fetch_pages,
            parse_posts=libdem_parse_posts,
        ),
        PartyConfig(
            name="SNP",
            start_url="https://www.snp.org/news/",
            fetch_pages=snp_fetch_pages,
            parse_posts=snp_parse_posts,
        ),
        PartyConfig(
            name="Green",
            start_url="https://www.greenparty.org.uk/news/",
            fetch_pages=greens_fetch_pages,
            parse_posts=greens_parse_posts,
        ),
        PartyConfig(
            name="Reform",
            start_url="https://www.reformparty.uk/news",
            fetch_pages=reform_fetch_pages,
            parse_posts=reform_parse_posts,
        ),
    ]


def scrape_party(cfg: PartyConfig, since: date) -> List[Post]:
    sess = _session()
    all_posts: List[Post] = []

    for html in cfg.fetch_pages(sess, cfg.start_url, since):
        posts = cfg.parse_posts(html, cfg.start_url)
        all_posts.extend(posts)

    # normalise party name from config (parsers hardcode, but keep consistent)
    normalised = []
    for p in all_posts:
        normalised.append(Post(party=cfg.name, title=p.title, url=p.url, published=p.published))

    return _dedupe(normalised)


def write_csv(posts: List[Post], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["party", "published", "title", "url"])
        for p in sorted(posts, key=lambda x: (x.party, x.published, x.url)):
            w.writerow([p.party, p.published.isoformat(), p.title, p.url])


def print_summary(counts: Dict[str, int]) -> None:
    width = max(len(k) for k in counts) if counts else 10
    print("\nOfficial archive posts since 2024-07-05\n")
    for party, cnt in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{party:<{width}}  {cnt:>6}")
    print("")


def main() -> int:
    since = date(2024, 7, 5)
    configs = build_configs()

    totals: Dict[str, int] = {}
    all_filtered_posts: List[Post] = []
    all_posts_any_date: List[Post] = []

    for cfg in configs:
        try:
            posts = scrape_party(cfg, since=since)
            all_posts_any_date.extend(posts)

            cnt, filtered = _count_since(posts, since)
            totals[cfg.name] = cnt
            all_filtered_posts.extend(filtered)

            print(f"✅ {cfg.name}: scraped {len(posts)} items, {cnt} since {since.isoformat()}")
        except Exception as exc:  # noqa: BLE001
            totals[cfg.name] = -1
            print(f"❌ {cfg.name}: failed ({exc})", file=sys.stderr)

    print_summary({k: v for k, v in totals.items() if v >= 0})

    out_path = "uk_party_comms_counts.csv"
    write_csv(all_filtered_posts, out_path)
    print(f"Wrote CSV: {out_path} ({len(all_filtered_posts)} rows)")

    failures = [k for k, v in totals.items() if v < 0]
    if failures:
        print("\nSome parties failed to scrape:", ", ".join(failures), file=sys.stderr)
        print("Tip: open their start_url in a browser and tweak the parser selectors.\n", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

--Notes
pip install requests beautifulsoup4
python uk_party_announcement_counter.py
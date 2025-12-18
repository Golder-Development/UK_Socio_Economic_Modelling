"""
Build an interactive "mind map" of WordPress posts from a WXR export (XML or ZIP).

Output: political_posts_mindmap.html (standalone HTML, uses Plotly CDN)
Usage:
    python build_posts_mindmap.py /path/to/export.xml
    python build_posts_mindmap.py /path/to/export.zip

Notes:
- Edges are based on (a) shared tags (IDF-weighted, ignoring ultra-common tags)
  and (b) explicit links between posts found inside post content.
- To keep things readable, we keep the top K strongest edges per node.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import math
import re
import sys
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np


URL_RE = re.compile(r'https?://[^\s"<>]+')


def _read_xml_bytes(path: Path) -> bytes:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            xml_names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
            if not xml_names:
                raise ValueError("ZIP contains no .xml file")
            return zf.read(xml_names[0])
    return path.read_bytes()


def _get_namespaces(xml_bytes: bytes) -> Dict[str, str]:
    namespaces: Dict[str, str] = {}
    for event, elem in ET.iterparse(io.BytesIO(xml_bytes), events=("start-ns",)):
        prefix, uri = elem
        namespaces[prefix] = uri
    return namespaces


def _get_text(elem: ET.Element, path: str, ns: Dict[str, str]) -> Optional[str]:
    found = elem.find(path, ns)
    return found.text if found is not None else None


def parse_posts(xml_bytes: bytes) -> List[Dict[str, Any]]:
    namespaces = _get_namespaces(xml_bytes)
    tree = ET.parse(io.BytesIO(xml_bytes))
    root = tree.getroot()
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Invalid WXR: missing <channel>")

    wp_ns = {
        "wp": namespaces.get("wp", ""),
        "content": namespaces.get("content", ""),
        "dc": namespaces.get("dc", ""),
        "excerpt": namespaces.get("excerpt", ""),
    }

    posts: List[Dict[str, Any]] = []
    for it in channel.findall("item"):
        post_type = _get_text(it, "wp:post_type", wp_ns)
        if post_type != "post":
            continue

        post_id = _get_text(it, "wp:post_id", wp_ns)
        slug = _get_text(it, "wp:post_name", wp_ns)

        cats: List[str] = []
        tags: List[str] = []
        for c in it.findall("category"):
            domain = c.attrib.get("domain")
            text = c.text or ""
            if domain == "category":
                cats.append(text)
            elif domain == "post_tag":
                tags.append(text)

        posts.append(
            {
                "post_id": int(post_id) if post_id else None,
                "title": _get_text(it, "title", {}),
                "link": _get_text(it, "link", {}),
                "slug": slug,
                "status": _get_text(it, "wp:status", wp_ns),
                "post_date": _get_text(it, "wp:post_date", wp_ns),
                "categories": cats,
                "tags": tags,
                "content": _get_text(it, "content:encoded", wp_ns) or "",
                "excerpt": _get_text(it, "excerpt:encoded", wp_ns) or "",
            }
        )

    # Keep just Politics category posts if present
    politics_posts = [p for p in posts if "Politics" in (p.get("categories") or [])]
    return politics_posts if politics_posts else posts


def _build_internal_link_edges(posts: List[Dict[str, Any]]) -> Set[Tuple[int, int]]:
    link_to_id = {p["link"]: p["post_id"] for p in posts if p.get("link") and p.get("post_id")}
    path_to_id: Dict[str, int] = {}

    for p in posts:
        link = p.get("link") or ""
        if not link:
            continue
        parsed = urllib.parse.urlparse(link)
        path = parsed.path.strip("/")
        if path:
            path_to_id[path] = p["post_id"]
            path_to_id[path.split("/")[-1]] = p["post_id"]

    edges: Set[Tuple[int, int]] = set()
    for p in posts:
        src = p.get("post_id")
        if not src:
            continue
        urls = URL_RE.findall(p.get("content") or "")
        for u in urls:
            u = u.rstrip(').,;\'"!?')
            parsed = urllib.parse.urlparse(u)
            if "wordpress.com" not in parsed.netloc:
                continue
            path = parsed.path.strip("/")
            tgt = link_to_id.get(u) or path_to_id.get(path) or path_to_id.get(path.split("/")[-1])
            if tgt and tgt != src:
                edges.add((src, tgt))
    return edges


def build_graph(posts: List[Dict[str, Any]], top_k_edges: int = 6) -> nx.Graph:
    g = nx.Graph()
    for p in posts:
        g.add_node(p["post_id"], **p)

    tag_df = Counter([t for p in posts for t in (p.get("tags") or [])])
    n_posts = len(posts)
    ignored = {t for t, df in tag_df.items() if df / max(n_posts, 1) > 0.6}

    idf = {t: math.log((n_posts + 1) / (df + 1)) + 1 for t, df in tag_df.items()}

    edge_w: Dict[Tuple[int, int], float] = defaultdict(float)
    edge_meta: Dict[Tuple[int, int], List[str]] = defaultdict(list)

    # tag similarity (IDF-weighted)
    for i, a in enumerate(posts):
        for b in posts[i + 1 :]:
            shared = set(a.get("tags") or []) & set(b.get("tags") or [])
            shared = {t for t in shared if t not in ignored}
            if not shared:
                continue
            u, v = a["post_id"], b["post_id"]
            key = tuple(sorted((u, v)))
            edge_w[key] += float(sum(idf[t] for t in shared))
            edge_meta[key] = sorted(shared)

    # explicit internal links (boost)
    for u, v in _build_internal_link_edges(posts):
        key = tuple(sorted((u, v)))
        edge_w[key] += 3.0
        edge_meta[key] = (edge_meta.get(key, []) or []) + ["linked"]

    # keep top K edges per node
    node_edges: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
    for (u, v), w in edge_w.items():
        node_edges[u].append((v, w))
        node_edges[v].append((u, w))

    kept: Set[Tuple[int, int]] = set()
    for u, lst in node_edges.items():
        for v, _w in sorted(lst, key=lambda x: x[1], reverse=True)[:top_k_edges]:
            kept.add(tuple(sorted((u, v))))

    for u, v in kept:
        g.add_edge(u, v, weight=edge_w[(u, v)], tags=edge_meta[(u, v)])

    return g


def _layout(g: nx.Graph) -> Dict[int, Tuple[float, float]]:
    pos = nx.spring_layout(g, k=0.6, iterations=200, seed=42, weight="weight")
    xs = np.array([pos[n][0] for n in g.nodes()])
    ys = np.array([pos[n][1] for n in g.nodes()])
    xs = (xs - xs.mean()) / (xs.std() if xs.std() else 1.0)
    ys = (ys - ys.mean()) / (ys.std() if ys.std() else 1.0)
    return {n: (float(xs[i]), float(ys[i])) for i, n in enumerate(g.nodes())}


def _date_disp(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        d = dt.datetime.fromisoformat(s)
        return d.strftime("%Y-%m-%d")
    except ValueError:
        return s[:10]


def write_html(g: nx.Graph, out_path: Path) -> None:
    pos = _layout(g)
    deg = dict(g.degree())

    nodes: List[Dict[str, Any]] = []
    for n, data in g.nodes(data=True):
        nodes.append(
            {
                "id": n,
                "title": data.get("title") or "",
                "link": data.get("link") or "",
                "status": data.get("status") or "",
                "date": _date_disp(data.get("post_date")),
                "tags": data.get("tags") or [],
                "x": pos[n][0],
                "y": pos[n][1],
                "degree": int(deg.get(n, 0)),
            }
        )

    edges: List[Dict[str, Any]] = []
    for u, v, data in g.edges(data=True):
        edges.append(
            {
                "source": u,
                "target": v,
                "weight": float(data.get("weight", 1.0)),
                "tags": data.get("tags") or [],
            }
        )

    payload = json.dumps({"nodes": nodes, "edges": edges})
    plotly_cdn = "https://cdn.plot.ly/plotly-2.27.0.min.js"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Political Posts Mind Map</title>
<script src="{plotly_cdn}"></script>
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin:0; }}
  #wrap {{ display:flex; height: 100vh; }}
  #left {{ flex: 1 1 auto; position:relative; }}
  #plot {{ width:100%; height:100%; }}
  #right {{ width: 360px; max-width: 45vw; border-left: 1px solid #ddd; padding: 12px; overflow:auto; }}
  h2 {{ margin: 6px 0 8px; font-size: 16px; }}
  .muted {{ color:#666; font-size: 12px; }}
  .row {{ margin: 10px 0; }}
  input[type="text"] {{ width:100%; padding:8px; }}
  .pill {{ display:inline-block; padding: 2px 8px; border: 1px solid #ddd; border-radius: 999px; margin: 2px; font-size: 12px; }}
  .post-title {{ font-weight: 700; }}
  .btn {{ display:inline-block; padding:6px 10px; border:1px solid #ccc; border-radius:8px; cursor:pointer; background:#fafafa; margin-right:6px; }}
  .btn:hover {{ background:#f2f2f2; }}
  .small {{ font-size: 12px; }}
  .sep {{ border-top:1px solid #eee; margin: 10px 0; }}
</style>
</head>
<body>
<div id="wrap">
  <div id="left"><div id="plot"></div></div>
  <div id="right">
    <h2>Posts mind map</h2>
    <div class="muted">Click a node to see details. Double-click to open the post.</div>

    <div class="row">
      <div><strong>Filter by status</strong></div>
      <label class="small"><input type="checkbox" id="f_publish" checked> publish</label><br/>
      <label class="small"><input type="checkbox" id="f_future" checked> future (scheduled)</label><br/>
      <label class="small"><input type="checkbox" id="f_private" checked> private</label>
    </div>

    <div class="row">
      <div><strong>Search title</strong></div>
      <input id="search" type="text" placeholder="Type to highlight…"/>
      <div class="muted">Tip: try “ECHR”, “electoral”, “schools”, “markets”…</div>
    </div>

    <div class="row">
      <span class="btn" id="btn_reset">Reset view</span>
      <span class="btn" id="btn_zoom">Zoom to matches</span>
    </div>

    <div class="sep"></div>

    <div id="details">
      <div class="muted">No post selected yet.</div>
    </div>
  </div>
</div>

<script>
const DATA = {payload};

function buildPlot(filteredNodeIds=null, highlightIds=new Set()) {{
  const nodes = DATA.nodes.filter(n => {{
    if (filteredNodeIds && !filteredNodeIds.has(n.id)) return false;
    return true;
  }});
  const nodeIdSet = new Set(nodes.map(n=>n.id));
  const edges = DATA.edges.filter(e => nodeIdSet.has(e.source) && nodeIdSet.has(e.target));

  const edgeX = [];
  const edgeY = [];
  for (const e of edges) {{
    const s = nodes.find(n => n.id === e.source);
    const t = nodes.find(n => n.id === e.target);
    if (!s || !t) continue;
    edgeX.push(s.x, t.x, null);
    edgeY.push(s.y, t.y, null);
  }}

  const edgeTrace = {{
    x: edgeX, y: edgeY,
    mode: 'lines',
    hoverinfo: 'none',
    line: {{ width: 1 }},
    name: 'connections'
  }};

  function nodeTraceForStatus(status) {{
    const ns = nodes.filter(n => n.status === status);
    return {{
      x: ns.map(n=>n.x),
      y: ns.map(n=>n.y),
      mode: 'markers+text',
      text: ns.map(n => n.title.length > 28 ? n.title.slice(0,28) + '…' : n.title),
      textposition: 'top center',
      hovertext: ns.map(n => `<b>${{n.title}}</b><br>${{n.date}}<br>Status: ${{n.status}}<br>Degree: ${{n.degree}}`),
      hoverinfo: 'text',
      customdata: ns,
      marker: {{
        size: ns.map(n => 10 + n.degree * 2),
        opacity: 0.9,
        line: {{
          width: ns.map(n => highlightIds.has(n.id) ? 3 : 1)
        }}
      }},
      name: status
    }};
  }}

  const traces = [edgeTrace,
    nodeTraceForStatus('publish'),
    nodeTraceForStatus('future'),
    nodeTraceForStatus('private')
  ];

  const layout = {{
    margin: {{l:10,r:10,t:10,b:10}},
    xaxis: {{visible:false}},
    yaxis: {{visible:false}},
    hovermode: 'closest',
    dragmode: 'pan',
    showlegend: true
  }};

  Plotly.newPlot('plot', traces, layout, {{
    responsive: true,
    displaylogo: false,
    modeBarButtonsToAdd: ['resetScale2d']
  }});

  const plotDiv = document.getElementById('plot');
  plotDiv.on('plotly_click', function(evt) {{
    if (!evt.points || !evt.points.length) return;
    const pt = evt.points[0];
    if (!pt.customdata) return;
    renderDetails(pt.customdata);
  }});

  plotDiv.on('plotly_doubleclick', function() {{
    const last = window.__selectedNode;
    if (last && last.link) window.open(last.link, '_blank');
  }});
}}

function renderDetails(n) {{
  window.__selectedNode = n;
  const tagsHtml = (n.tags || []).slice(0, 50).map(t => `<span class="pill">${{escapeHtml(t)}}</span>`).join(' ');
  document.getElementById('details').innerHTML = `
    <div class="post-title">${{escapeHtml(n.title)}}</div>
    <div class="muted">${{escapeHtml(n.date)}} · status: <b>${{escapeHtml(n.status)}}</b></div>
    <div class="row"><a href="${{n.link}}" target="_blank">Open post</a></div>
    <div class="row"><strong>Tags</strong><div>${{tagsHtml || '<span class="muted">No tags</span>'}}</div></div>
  `;
}}

function escapeHtml(str) {{
  return String(str || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;");
}}

function currentFilterSet() {{
  const showPublish = document.getElementById('f_publish').checked;
  const showFuture = document.getElementById('f_future').checked;
  const showPrivate = document.getElementById('f_private').checked;

  const ids = new Set();
  for (const n of DATA.nodes) {{
    if (n.status === 'publish' && showPublish) ids.add(n.id);
    if (n.status === 'future' && showFuture) ids.add(n.id);
    if (n.status === 'private' && showPrivate) ids.add(n.id);
  }}
  return ids;
}}

function applyFiltersAndSearch() {{
  const ids = currentFilterSet();
  const q = document.getElementById('search').value.trim().toLowerCase();
  const highlight = new Set();
  if (q) {{
    for (const n of DATA.nodes) {{
      if (!ids.has(n.id)) continue;
      if ((n.title || '').toLowerCase().includes(q)) highlight.add(n.id);
    }}
  }}
  buildPlot(ids, highlight);
  window.__highlight = highlight;
}}

document.getElementById('f_publish').addEventListener('change', applyFiltersAndSearch);
document.getElementById('f_future').addEventListener('change', applyFiltersAndSearch);
document.getElementById('f_private').addEventListener('change', applyFiltersAndSearch);
document.getElementById('search').addEventListener('input', applyFiltersAndSearch);

document.getElementById('btn_reset').addEventListener('click', function() {{
  document.getElementById('search').value = '';
  document.getElementById('f_publish').checked = true;
  document.getElementById('f_future').checked = true;
  document.getElementById('f_private').checked = true;
  applyFiltersAndSearch();
}});

document.getElementById('btn_zoom').addEventListener('click', function() {{
  const highlight = window.__highlight || new Set();
  if (!highlight.size) return;
  const ids = currentFilterSet();
  const nodes = DATA.nodes.filter(n => ids.has(n.id) && highlight.has(n.id));
  if (!nodes.length) return;
  const xs = nodes.map(n=>n.x), ys = nodes.map(n=>n.y);
  const xmin = Math.min(...xs), xmax = Math.max(...xs);
  const ymin = Math.min(...ys), ymax = Math.max(...ys);
  Plotly.relayout('plot', {{
    'xaxis.range': [xmin - 0.5, xmax + 0.5],
    'yaxis.range': [ymin - 0.5, ymax + 0.5]
  }});
}});

applyFiltersAndSearch();
</script>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python build_posts_mindmap.py <export.xml|export.zip>")
        return 2

    in_path = Path(sys.argv[1]).expanduser()
    if not in_path.exists():
        print(f"File not found: {in_path}")
        return 2

    xml_bytes = _read_xml_bytes(in_path)
    posts = parse_posts(xml_bytes)
    g = build_graph(posts, top_k_edges=6)
    out_path = Path("political_posts_mindmap.html")
    write_html(g, out_path)
    print(f"Wrote: {out_path.resolve()}")
    print(f"Posts: {len(posts)} | Nodes: {g.number_of_nodes()} | Edges: {g.number_of_edges()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

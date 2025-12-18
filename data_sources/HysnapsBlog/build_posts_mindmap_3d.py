"""
Build an interactive 3D "mind map" of WordPress posts from a WXR export (XML or ZIP).

Output: political_posts_mindmap_3d.html (standalone HTML, uses Plotly CDN)
Usage:
    python build_posts_mindmap_3d.py /path/to/export.xml
    python build_posts_mindmap_3d.py /path/to/export.zip

Notes:
- X/Y: semantic layout (spring layout based on edge weights)
- Z-axis: Selectable metric (Connectedness, Word Count, or Sentiment)
- Edges based on (a) shared tags (IDF-weighted) and (b) explicit links between posts
- Posts with 'private' status are automatically excluded
- Posts in the EXCLUDED_POST_TITLES list below will be removed from the visualization

CONFIGURATION: Customize the list below to exclude specific posts by title.
Simply copy-paste the exact post title as it appears in the HTML visualization.
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans


# ============================================================
# CONFIG
# ============================================================

EXCLUDED_POST_TITLES = [
    "Why use synthetic but Realistic data.",
    "Uk Politics - They Work For You",
    "Mental Health- the dominance of fear",
]

N_CLUSTERS = 7
TOP_K_EDGES = 6

URL_RE = re.compile(r'https?://[^\s"<>]+')
HTML_TAG_RE = re.compile(r'<[^>]+>')

# Simple sentiment word lists
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 
    'success', 'successful', 'benefit', 'benefits', 'opportunity', 'growth', 'improve',
    'better', 'best', 'progress', 'win', 'winning', 'achieve', 'achievement', 'hope',
    'hopeful', 'optimistic', 'strong', 'stronger', 'effective', 'efficient', 'gain'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'negative', 'fail', 'failure', 'failed',
    'problem', 'problems', 'crisis', 'damage', 'worse', 'worst', 'decline', 'loss',
    'lose', 'losing', 'fear', 'fearful', 'pessimistic', 'weak', 'weaker', 'ineffective',
    'corrupt', 'corruption', 'threat', 'threaten', 'disaster', 'concern', 'concerns'
}


# ============================================================
# HELPERS
# ============================================================

def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = HTML_TAG_RE.sub(" ", text)
    return " ".join(text.split())


def _read_xml_bytes(path: Path) -> bytes:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            xmls = [n for n in zf.namelist() if n.lower().endswith(".xml")]
            if not xmls:
                raise ValueError("ZIP contains no XML")
            return zf.read(xmls[0])
    return path.read_bytes()


def _get_namespaces(xml_bytes: bytes) -> Dict[str, str]:
    ns = {}
    for _, elem in ET.iterparse(io.BytesIO(xml_bytes), events=("start-ns",)):
        prefix, uri = elem
        ns[prefix] = uri
    return ns


def _get_text(elem: ET.Element, path: str, ns: Dict[str, str]) -> Optional[str]:
    found = elem.find(path, ns)
    return found.text if found is not None else None


def compute_sentiment(text: str) -> float:
    """
    Simple sentiment score: (positive_words - negative_words) / total_words.
    Returns value roughly in range [-1, 1].
    """
    if not text:
        return 0.0
    
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    
    # normalize by total words for comparability
    return (pos_count - neg_count) / len(words) * 100  # scale up for visibility


# ============================================================
# PARSE POSTS
# ============================================================

def parse_posts(xml_bytes: bytes) -> List[Dict[str, Any]]:
    namespaces = _get_namespaces(xml_bytes)
    tree = ET.parse(io.BytesIO(xml_bytes))
    root = tree.getroot()

    channel = root.find("channel")
    if channel is None:
        raise ValueError("No <channel> in XML")

    wp = namespaces.get("wp", "")
    items = channel.findall("item")

    posts = []
    for it in items:
        post_type = _get_text(it, "wp:post_type", {"wp": wp})
        if post_type != "post":
            continue

        status = _get_text(it, "wp:status", {"wp": wp})
        if status == "private":
            continue

        title = _get_text(it, "title", {}) or ""
        if title in EXCLUDED_POST_TITLES:
            continue
        if "Music" in title:
            continue

        tags, cats = [], []
        for c in it.findall("category"):
            domain = c.attrib.get("domain")
            txt = c.text
            if domain == "post_tag" and txt:
                if txt.lower() != "music":
                    tags.append(txt)
            elif domain == "category" and txt:
                cats.append(txt)

        posts.append({
            "post_id": int(_get_text(it, "wp:post_id", {"wp": wp})),
            "title": title,
            "link": _get_text(it, "link", {}),
            "status": status,
            "post_date": _get_text(it, "wp:post_date", {"wp": wp}),
            "tags": tags,
            "categories": cats,
            "content": _get_text(it, "content:encoded", {"content": namespaces.get("content", "")}) or "",
        })

    politics = [p for p in posts if "Politics" in p["categories"]]
    return politics or posts


# ============================================================
# NLP CLUSTERING
# ============================================================

def assign_clusters(posts: List[Dict[str, Any]]) -> Dict[int, int]:
    texts, ids = [], []

    for p in posts:
        clean = _strip_html(p["content"])
        title = p["title"]
        texts.append(f"{title} {title} {clean}")
        ids.append(p["post_id"])

    tfidf = TfidfVectorizer(
        max_features=600,
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.8,
        min_df=2,
    ).fit_transform(texts)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = km.fit_predict(tfidf)

    return dict(zip(ids, labels))


def infer_cluster_names(posts: List[Dict[str, Any]], clusters: Dict[int, int]) -> Dict[int, str]:
    """Infer human-readable cluster names from common tags and content."""
    from collections import Counter
    
    cluster_posts = {}
    for p in posts:
        c = clusters[p["post_id"]]
        if c not in cluster_posts:
            cluster_posts[c] = []
        cluster_posts[c].append(p)
    
    names = {}
    for c, group in cluster_posts.items():
        # collect tags
        tag_counter = Counter()
        for p in group:
            tag_counter.update(p["tags"])
        # get top 2-3 tags
        top_tags = [t for t, _ in tag_counter.most_common(3)]
        if top_tags:
            names[c] = " / ".join(top_tags[:2])
        else:
            names[c] = f"Group {c}"
    
    return names


def compute_content_similarity(posts: List[Dict[str, Any]], min_sim: float = 0.15) -> Dict[Tuple[int, int], float]:
    """Compute pairwise content similarity using TF-IDF and cosine similarity."""
    if len(posts) < 2:
        return {}
    
    texts, ids = [], []
    for p in posts:
        clean = _strip_html(p["content"])
        title = p["title"]
        texts.append(f"{title} {title} {title} {clean}")
        ids.append(p["post_id"])
    
    try:
        tfidf = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            max_df=0.8,
            min_df=1
        ).fit_transform(texts)
        
        sim_matrix = cosine_similarity(tfidf)
        
        edges = {}
        for i in range(len(posts)):
            for j in range(i + 1, len(posts)):
                sim = sim_matrix[i, j]
                if sim >= min_sim:
                    key = tuple(sorted((ids[i], ids[j])))
                    edges[key] = float(sim)
        
        return edges
    except Exception as e:
        print(f"Warning: Content similarity failed: {e}")
        return {}


# ============================================================
# GRAPH BUILDING
# ============================================================

def build_graph(posts: List[Dict[str, Any]]) -> Tuple[nx.Graph, Dict[int, int]]:
    g = nx.Graph()
    clusters = assign_clusters(posts)

    for p in posts:
        g.add_node(p["post_id"], **p, cluster=clusters[p["post_id"]])

    tag_df = Counter(t for p in posts for t in p["tags"])
    idf = {t: math.log(len(posts) / (df + 1)) + 1 for t, df in tag_df.items()}

    edge_w = defaultdict(float)
    edge_tags = defaultdict(list)

    # tag similarity
    for p1 in posts:
        for p2 in posts:
            if p1["post_id"] >= p2["post_id"]:
                continue
            shared = set(p1["tags"]) & set(p2["tags"])
            if shared:
                w = sum(idf[t] for t in shared)
                key = tuple(sorted((p1["post_id"], p2["post_id"])))
                edge_w[key] += w
                edge_tags[key].append("tag")

    # explicit links
    for p in posts:
        urls = URL_RE.findall(p["content"])
        for other in posts:
            if other["post_id"] == p["post_id"]:
                continue
            if other["link"] and other["link"] in urls:
                key = tuple(sorted((p["post_id"], other["post_id"])))
                edge_w[key] += 3.0
                edge_tags[key].append("linked")

    # content similarity
    sim_edges = compute_content_similarity(posts, min_sim=0.15)
    for key, sim in sim_edges.items():
        edge_w[key] += sim * 5
        if "similarity" not in edge_tags[key]:
            edge_tags[key].append("similarity")

    # keep top K per node
    by_node = defaultdict(list)
    for (u, v), w in edge_w.items():
        by_node[u].append((v, w))
        by_node[v].append((u, w))

    keep = set()
    for u, lst in by_node.items():
        for v, _ in sorted(lst, key=lambda x: x[1], reverse=True)[:TOP_K_EDGES]:
            keep.add(tuple(sorted((u, v))))

    for u, v in keep:
        g.add_edge(u, v, weight=edge_w[(u, v)], tags=edge_tags[(u, v)])

    return g, clusters


# ============================================================
# Z-AXIS METRICS
# ============================================================

def compute_z_metrics(g: nx.Graph) -> Dict[int, Dict[str, float]]:
    """
    Compute three Z-axis metrics for each node:
    - connectedness: sum of edge weights
    - word_count: number of words in content
    - sentiment: sentiment polarity score
    """
    metrics = {}
    
    for n, d in g.nodes(data=True):
        # Connectedness: sum of edge weights
        connectedness = sum(g[n][nbr]['weight'] for nbr in g.neighbors(n))
        
        # Word count
        clean = _strip_html(d.get("content", ""))
        word_count = len(clean.split())
        
        # Sentiment
        sentiment = compute_sentiment(clean)
        
        metrics[n] = {
            "connectedness": float(connectedness),
            "word_count": float(word_count),
            "sentiment": float(sentiment)
        }
    
    return metrics


# ============================================================
# HTML OUTPUT
# ============================================================

def write_html(g: nx.Graph, out: Path, cluster_names: Dict[int, str], cluster_counts: Dict[int, int]):
    pos = nx.spring_layout(g, seed=42, weight="weight")
    z_metrics = compute_z_metrics(g)
    
    nodes, edges = [], []
    
    # prepare cluster info for JS
    cluster_info = []
    for c in sorted(cluster_names.keys()):
        cluster_info.append({
            "id": int(c),
            "name": cluster_names[c],
            "count": int(cluster_counts[c])
        })

    for n, d in g.nodes(data=True):
        # build a short summary from the original content
        raw = d.get("content", "") or ""
        clean = _strip_html(raw)
        clean = " ".join(clean.split())
        summary = clean[:300] + ("…" if len(clean) > 300 else "")

        nodes.append({
            "id": int(n),
            "title": d["title"],
            "link": d["link"],
            "status": d["status"],
            "date": d["post_date"][:10] if d["post_date"] else "",
            "tags": list(d["tags"]),
            "cluster": int(d["cluster"]),
            "x": float(pos[n][0]),
            "y": float(pos[n][1]),
            "summary": summary,
            "z_connectedness": z_metrics[n]["connectedness"],
            "z_word_count": z_metrics[n]["word_count"],
            "z_sentiment": z_metrics[n]["sentiment"],
        })  

    for u, v, d in g.edges(data=True):
        edges.append({
            "source": int(u),
            "target": int(v),
            "weight": float(d["weight"]),
            "tags": list(d["tags"]),
        })

    payload = json.dumps({
        "nodes": nodes,
        "edges": edges,
        "clusters": cluster_info,
    }, separators=(',', ':'))

    html = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
body { margin:0; font-family: system-ui; height:100vh; background:#f2f4fa; }
#wrap { display:grid; grid-template-columns: 1fr 360px; height:100vh; }
#plot { width:100%; height:100%; min-height:600px; cursor:pointer; background:#f2f4fa; }
#side { padding:10px; border-left:1px solid #ccc; overflow:auto; background:#fff; }
.btn { border:1px solid #ccc; padding:6px 10px; cursor:pointer; margin-right:5px; }
.muted { color:#666; font-size:90%; margin-top:4px; }
select { padding:4px; margin-top:4px; width:100%; }
</style>
</head>
<body>
<div id="wrap">
<div id="plot"></div>
<div id="side">
  <h3>Political Posts Network 3D</h3>
  
  <div style="margin-bottom:16px;">
    <label><b>Z-Axis Metric:</b></label>
    <select id="zMetric">
      <option value="connectedness">Connectedness (Edge Weight Sum)</option>
      <option value="word_count">Content Depth (Word Count)</option>
      <option value="sentiment">Sentiment Polarity</option>
    </select>
  </div>
  
  <label>Min edge weight: <span id="edgeVal">0</span></label>
  <input id="edgeSlider" type="range" min="0" max="10" step="0.5" value="0" style="width:100%">
  <div id="edgeCount" style="margin-top:8px;font-size:90%"></div>
  
  <div style="margin-top:16px;">
    <h4 style="margin:0 0 8px 0;font-size:14px;">Connections</h4>
    <label style="display:block;margin:4px 0;cursor:pointer;">
      <input type="checkbox" id="cbThematic" checked> Thematic/Similarity
    </label>
    <label style="display:block;margin:4px 0;cursor:pointer;">
      <input type="checkbox" id="cbLinked" checked> Explicit links
    </label>
  </div>
  
  <div style="margin-top:16px;">
    <h4 style="margin:0 0 8px 0;font-size:14px;">Clusters</h4>
    <div id="clusterLegend"></div>
  </div>
  
  <div id="details" style="margin-top:16px;"></div>
</div>
</div>

<script>
const COLORS = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2'];
let EDGE_MIN = 0;
let FOCUS = null;
let INITIALIZED = false;
let SHOW_THEMATIC = true;
let SHOW_LINKED = true;
let SHOW_CLUSTERS = new Set();
let Z_METRIC = 'connectedness';

const DATA = ___DATA_PAYLOAD___;
const nodes = DATA.nodes;
const allEdges = DATA.edges;
const clusterInfo = DATA.clusters;

// initialize all clusters visible
for (const c of clusterInfo) {
  SHOW_CLUSTERS.add(c.id);
}

// build cluster legend
const clusterLegendEl = document.getElementById('clusterLegend');
for (const c of clusterInfo) {
  const color = COLORS[c.id % COLORS.length];
  const item = document.createElement('div');
  item.style.cssText = 'display:flex;align-items:center;margin:4px 0;cursor:pointer;';
  item.innerHTML = `
    <input type="checkbox" id="cbCluster${c.id}" checked style="margin-right:6px;">
    <span style="width:14px;height:14px;background:${color};margin-right:6px;border:1px solid #999;"></span>
    <span>${c.name} (${c.count})</span>
  `;
  item.onclick = () => {
    const cb = document.getElementById(`cbCluster${c.id}`);
    cb.checked = !cb.checked;
    if (cb.checked) {
      SHOW_CLUSTERS.add(c.id);
    } else {
      SHOW_CLUSTERS.delete(c.id);
    }
    draw();
  };
  clusterLegendEl.appendChild(item);
}

document.getElementById('cbThematic').onchange = e => {
  SHOW_THEMATIC = e.target.checked;
  draw();
};
document.getElementById('cbLinked').onchange = e => {
  SHOW_LINKED = e.target.checked;
  draw();
};
document.getElementById('zMetric').onchange = e => {
  Z_METRIC = e.target.value;
  draw();
};

function neighbours(id) {
  const s = new Set([id]);
  for (const e of DATA.edges) {
    if (e.source===id) s.add(e.target);
    if (e.target===id) s.add(e.source);
  }
  return s;
}

function draw() {
  const thematic=[], linked=[];
  let visibleEdges = 0;
  const totalEdges = allEdges.length;
  for (const e of allEdges) {
    if (FOCUS && !FOCUS.has(e.source) && !FOCUS.has(e.target)) continue;
    if (e.weight < EDGE_MIN) continue;
    const isLinked = e.tags.includes("linked");
    if (isLinked && !SHOW_LINKED) continue;
    if (!isLinked && !SHOW_THEMATIC) continue;
    visibleEdges++;
    (isLinked ? linked : thematic).push(e);
  }

  document.getElementById('edgeCount').innerText =
    `Showing ${visibleEdges} of ${totalEdges} connections`;

  function edgeTrace3d(es, style) {
    const x=[], y=[], z=[];
    for (const e of es) {
      const s = nodes.find(n=>n.id===e.source);
      const t = nodes.find(n=>n.id===e.target);
      if (!s || !t) continue;
      const sz = s[`z_${Z_METRIC}`] || 0;
      const tz = t[`z_${Z_METRIC}`] || 0;
      x.push(s.x, t.x, null);
      y.push(s.y, t.y, null);
      z.push(sz, tz, null);
    }
    return {
      type: 'scatter3d',
      mode: 'lines',
      x, y, z,
      line: style,
      hoverinfo: 'none',
      showlegend: false
    };
  }

    const thematicTrace = edgeTrace3d(thematic, {dash:'dot', color:'#999', width:1.2});
    const linkedTrace = edgeTrace3d(linked, {color:'#222', width:2.2});

    const clusters = Array.from(new Set(nodes.map(n=>n.cluster))).sort((a,b)=>a-b);
    const nodeTraces = clusters.map(c => {
        if (!SHOW_CLUSTERS.has(c)) return null;
        const group = nodes.filter(n=>n.cluster === c);
        if (FOCUS) {
            const focused = group.filter(n => FOCUS.has(n.id));
            if (focused.length === 0) return null;
            return {
                type: 'scatter3d',
                mode: 'markers+text',
                x: focused.map(n=>n.x),
                y: focused.map(n=>n.y),
                z: focused.map(n=>n[`z_${Z_METRIC}`] || 0),
                text: focused.map(n=>n.title.slice(0,30)),
                hovertext: focused.map(n=>n.title),
                hoverinfo: 'text',
                textposition: 'top center',
                marker: { size: 8, color: COLORS[c % COLORS.length] },
                customdata: focused,
                name: `Cluster ${c}`,
                showlegend: false
            };
        }
        return {
            type: 'scatter3d',
            mode: 'markers+text',
            x: group.map(n=>n.x),
            y: group.map(n=>n.y),
            z: group.map(n=>n[`z_${Z_METRIC}`] || 0),
            text: group.map(n=>n.title.slice(0,30)),
            hovertext: group.map(n=>n.title),
            hoverinfo: 'text',
            textposition: 'top center',
            marker: { size: 8, color: COLORS[c % COLORS.length] },
            customdata: group,
            name: `Cluster ${c}`,
            showlegend: false
        };
    }).filter(t => t !== null);

    const plotDiv = document.getElementById('plot');
    const traces = [thematicTrace, linkedTrace, ...nodeTraces];
    const lightBg = '#f2f4fa';
    const gridCol = '#d8dce6';
    const zeroCol = '#c4c9d6';
    const layout = {
        scene: {
            bgcolor: lightBg,
            xaxis: {
                visible: false,
                showbackground: true,
                backgroundcolor: lightBg,
                gridcolor: gridCol,
                zerolinecolor: zeroCol
            },
            yaxis: {
                visible: false,
                showbackground: true,
                backgroundcolor: lightBg,
                gridcolor: gridCol,
                zerolinecolor: zeroCol
            },
            zaxis: {
                title: Z_METRIC === 'connectedness' ? 'Connectedness' :
                       Z_METRIC === 'word_count' ? 'Word Count' : 'Sentiment',
                showgrid: true,
                showline: true,
                showbackground: true,
                backgroundcolor: lightBg,
                gridcolor: gridCol,
                zerolinecolor: zeroCol
            },
            camera: {
                eye: {x: 1.5, y: 1.5, z: 1.2}
            }
        },
        paper_bgcolor: lightBg,
        plot_bgcolor: lightBg,
        hovermode: 'closest',
        margin: {l:0, r:0, t:0, b:0},
        showlegend: false
    };
    const config = {
        responsive: true,
        displayModeBar: 'hover',
        scrollZoom: true
    };

    const bindClick = () => {
        plotDiv.on('plotly_click', ev => {
            if (!ev || !ev.points || !ev.points.length) return;
            const p = ev.points[0];
            const n = p.customdata;
            if (!n || !n.id) return;
            FOCUS = neighbours(n.id);
            const tags = (n.tags || []).join(', ');
            const zVal = n[`z_${Z_METRIC}`] || 0;
            const zLabel = Z_METRIC === 'connectedness' ? 'Connectedness' :
                          Z_METRIC === 'word_count' ? 'Words' : 'Sentiment';
            document.getElementById('details').innerHTML = `
                <div>
                    <b>${n.title}</b><br>
                    <a href="${n.link}" target="_blank">Open post</a>
                    ${n.date ? `<div class="muted">${n.date}</div>` : ''}
                    ${tags ? `<div class="muted">Tags: ${tags}</div>` : ''}
                    <div class="muted">${zLabel}: ${zVal.toFixed(2)}</div>
                    <p style="margin-top:8px;">${n.summary || ''}</p>
                    <button class="btn" onclick="FOCUS=null;draw()">Reset</button>
                </div>`;
            draw();
        });
    };

    Plotly.newPlot(plotDiv, traces, layout, config).then(() => {
        bindClick();
        INITIALIZED = true;
    });
}

document.getElementById('edgeSlider').oninput = e => {
  EDGE_MIN = +e.target.value;
  document.getElementById('edgeVal').innerText = EDGE_MIN;
  draw();
};

draw();
</script>
</body>
</html>
"""
    html = html.replace("___DATA_PAYLOAD___", payload)
    out.write_text(html, encoding="utf-8")


# ============================================================
# MAIN
# ============================================================

def main():
    here = Path(__file__).parent

    if len(sys.argv) > 1:
        src = Path(sys.argv[1]).expanduser()
        if not src.is_absolute():
            src = here / src
        if not src.exists():
            raise FileNotFoundError(f"File not found: {src}")
    else:
        # Auto-detect WordPress export
        candidates = list(here.glob("*.zip")) + list(here.glob("*.xml"))

        if not candidates:
            raise FileNotFoundError(
                "No WordPress export found (.zip or .xml). "
                "Either place it next to the script or pass it explicitly."
            )

        if len(candidates) > 1:
            names = "\n".join(c.name for c in candidates)
            raise RuntimeError(
                "Multiple possible exports found. Please specify one:\n" + names
            )

        src = candidates[0]

    xml = _read_xml_bytes(src)
    posts = parse_posts(xml)
    g, clusters = build_graph(posts)
    
    # compute cluster names and counts
    cluster_names = infer_cluster_names(posts, clusters)
    cluster_counts = {}
    for p in posts:
        c = clusters[p["post_id"]]
        cluster_counts[c] = cluster_counts.get(c, 0) + 1

    out = here.parent.parent / "generated_charts" / "political_posts_mindmap_3d.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_html(g, out, cluster_names, cluster_counts)

    print(f"Wrote {out.resolve()}")
    print(f"Posts: {len(posts)} | Nodes: {g.number_of_nodes()} | Edges: {g.number_of_edges()}")

    
if __name__ == "__main__":
    main()

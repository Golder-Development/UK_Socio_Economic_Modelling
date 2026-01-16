"""
Core Formatting Reference Module
==================================

Unified styling and formatting system for all visualization dashboards.
Ensures consistency across all generated HTML outputs.

This module provides:
- CSS styling templates
- HTML structure templates
- Color schemes and palettes
- Typography standards
- Component builders

Usage:
    from formatting_reference import get_styled_html, CSS_STYLES, COLOR_PALETTE

    html_content = get_styled_html(
        title="My Dashboard",
        subtitle="Analysis subtitle",
        body_content=fig.to_html(include_plotlyjs='cdn'),
        include_timestamp=True
    )
"""

from datetime import datetime

# ============================================================================
# COLOR PALETTE
# ============================================================================

COLOR_PALETTE = {
    # Primary gradient (header)
    'gradient_dark': '#1a237e',
    'gradient_medium': '#283593',
    'gradient_light': '#3f51b5',
    
    # Status colors
    'success': '#4CAF50',      # Green
    'info': '#2196F3',         # Blue
    'warning': '#FF9800',      # Orange
    'danger': '#f44336',       # Red
    'secondary': '#9C27B0',    # Purple
    'neutral': '#999',         # Grey
    
    # Donation type colors (specific)
    'cash': '#4CAF50',
    'non_cash': '#2196F3',
    'sponsorship': '#FF9800',
    'public_fund': '#9C27B0',
    'bequest': '#f44336',
    'other': '#999',
    
    # Cabinet category colors
    'stalwart': '#c8e6c9',
    'pawn': '#ffcdd2',
    'one_hit': '#bbdefb',
    
    # Party colors
    'conservative': '#0087DC',
    'labour': '#E4003B',
    'liberal_democrat': '#FAA61A',
    
    # Neutral
    'background': '#fafafa',
    'white': '#ffffff',
    'text_dark': '#333',
    'text_light': '#666',
    'border': '#ddd',
}

# ============================================================================
# CSS STYLES
# ============================================================================

CSS_STYLES = """
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: {bg_color};
    color: {text_color};
    line-height: 1.6;
}}

/* ===== HEADER ===== */
.header {{
    background: linear-gradient(135deg, {grad_dark} 0%, {grad_medium} 50%, {grad_light} 100%);
    color: white;
    padding: 40px;
    text-align: center;
    border-radius: 8px;
    margin-bottom: 30px;
}}

.header h1 {{
    font-size: 2.5em;
    margin-bottom: 10px;
    font-weight: 700;
    letter-spacing: -0.5px;
}}

.header p {{
    font-size: 1.1em;
    opacity: 0.95;
    margin: 5px 0;
}}

.header .timestamp {{
    font-size: 0.9em;
    opacity: 0.7;
    margin-top: 15px;
    font-style: italic;
}}

/* ===== CONTAINER ===== */
.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 30px;
}}

/* ===== SECTIONS ===== */
.section {{
    background: white;
    padding: 25px;
    margin: 20px 0;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.section h2 {{
    color: {grad_dark};
    border-bottom: 3px solid {grad_medium};
    padding-bottom: 10px;
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 1.5em;
    font-weight: 600;
}}

.section h3 {{
    color: {grad_medium};
    margin-top: 20px;
    margin-bottom: 15px;
    font-size: 1.1em;
    font-weight: 600;
}}

.section p {{
    margin-bottom: 15px;
    color: {text_light};
}}

/* ===== STATISTICS CARDS ===== */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 30px 0;
}}

.stat-card {{
    background: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-left: 5px solid {grad_dark};
    transition: transform 0.2s, box-shadow 0.2s;
}}

.stat-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}

.stat-card.accent1 {{
    border-left-color: {success};
}}

.stat-card.accent2 {{
    border-left-color: {info};
}}

.stat-card.accent3 {{
    border-left-color: {warning};
}}

.stat-card.accent4 {{
    border-left-color: {danger};
}}

.stat-label {{
    color: {text_light};
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
    font-weight: 600;
}}

.stat-value {{
    font-size: 2em;
    font-weight: bold;
    color: {grad_dark};
    word-break: break-word;
}}

.stat-subvalue {{
    color: #999;
    font-size: 0.85em;
    margin-top: 8px;
}}

/* ===== CHARTS ===== */
.chart-container {{
    margin: 20px 0;
    border-radius: 4px;
    overflow: hidden;
}}

/* ===== BADGES ===== */
.badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: bold;
    color: white;
    margin-right: 8px;
    margin-bottom: 5px;
}}

.badge-success {{
    background-color: {success};
}}

.badge-info {{
    background-color: {info};
}}

.badge-warning {{
    background-color: {warning};
}}

.badge-danger {{
    background-color: {danger};
}}

.badge-secondary {{
    background-color: {secondary};
}}

.badge-neutral {{
    background-color: {neutral};
}}

/* Specific donation types */
.badge-cash {{
    background-color: {cash};
}}

.badge-non-cash {{
    background-color: {non_cash};
}}

.badge-sponsorship {{
    background-color: {sponsorship};
}}

.badge-public-fund {{
    background-color: {public_fund};
}}

.badge-bequest {{
    background-color: {bequest};
}}

.badge-other {{
    background-color: {other};
}}

/* Cabinet categories */
.badge-stalwart {{
    background-color: {stalwart};
    color: #1b5e20;
}}

.badge-pawn {{
    background-color: {pawn};
    color: #b71c1c;
}}

.badge-one-hit {{
    background-color: {one_hit};
    color: #0d47a1;
}}

/* ===== INSIGHT BOX ===== */
.insight {{
    background-color: #e3f2fd;
    border-left: 4px solid {info};
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}}

.insight h3 {{
    color: #1565c0;
    margin-bottom: 10px;
}}

.insight ul {{
    list-style-position: inside;
    line-height: 1.8;
}}

.insight li {{
    color: {text_dark};
    margin-bottom: 8px;
}}

.insight strong {{
    color: {grad_dark};
}}

/* ===== TABLES ===== */
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 15px 0;
    font-size: 0.95em;
}}

th, td {{
    border: 1px solid {border};
    padding: 12px;
    text-align: left;
}}

th {{
    background-color: #f0f0f0;
    font-weight: bold;
    border-bottom: 2px solid {text_dark};
    color: {grad_dark};
}}

tr:nth-child(even) {{
    background-color: #f9f9f9;
}}

tr:hover {{
    background-color: #f5f5f5;
}}

/* ===== FOOTER ===== */
.footer {{
    text-align: center;
    color: {text_light};
    font-size: 0.9em;
    margin-top: 40px;
    padding: 20px;
    border-top: 1px solid {border};
}}

.footer p {{
    margin: 5px 0;
}}

/* ===== UTILITY CLASSES ===== */
.text-center {{
    text-align: center;
}}

.text-right {{
    text-align: right;
}}

.text-muted {{
    color: {text_light};
}}

.mb-0 {{
    margin-bottom: 0;
}}

.mb-1 {{
    margin-bottom: 10px;
}}

.mb-2 {{
    margin-bottom: 20px;
}}

.mt-1 {{
    margin-top: 10px;
}}

.mt-2 {{
    margin-top: 20px;
}}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {{
    .header {{
        padding: 30px 20px;
    }}
    
    .header h1 {{
        font-size: 1.8em;
    }}
    
    .container {{
        padding: 15px;
    }}
    
    .stats-grid {{
        grid-template-columns: 1fr;
        gap: 15px;
    }}
    
    table {{
        font-size: 0.85em;
    }}
    
    th, td {{
        padding: 8px;
    }}
}}
"""

# ============================================================================
# DONATION TYPE LEGEND
# ============================================================================

DONATION_TYPE_LEGEND = """
<div class="section">
    <h2>Donation Type Reference</h2>
    <p>Understanding the different categories of political donations:</p>
    <br>
    <p>
        <span class="badge badge-cash">Cash</span>
        Direct monetary contributions to political parties
    </p>
    <br>
    <p>
        <span class="badge badge-non-cash">Non-Cash</span>
        In-kind donations (goods, services, resources)
    </p>
    <br>
    <p>
        <span class="badge badge-sponsorship">Sponsorship</span>
        Funding for party events and activities
    </p>
    <br>
    <p>
        <span class="badge badge-public-fund">Public Fund</span>
        State-funded donations or grants
    </p>
    <br>
    <p>
        <span class="badge badge-bequest">Bequest</span>
        Donations from wills and legacies
    </p>
    <br>
    <p>
        <span class="badge badge-other">Other</span>
        Miscellaneous donation types
    </p>
</div>
"""

# ============================================================================
# HTML TEMPLATE BUILDER
# ============================================================================

def get_styled_html(
    title,
    subtitle,
    body_content,
    include_timestamp=True,
    include_donation_legend=False,
    footer_text=None,
    custom_header_html=None
):
    """
    Generate a complete styled HTML document.
    
    Parameters:
    -----------
    title : str
        Main title for the dashboard
    subtitle : str
        Subtitle/description
    body_content : str
        Main HTML content (typically Plotly charts)
    include_timestamp : bool, default=True
        Include generation timestamp
    include_donation_legend : bool, default=False
        Include donation type reference legend
    footer_text : str, optional
        Custom footer text
    custom_header_html : str, optional
        Custom HTML to add in header after subtitle
    
    Returns:
    --------
    str
        Complete HTML document
    """
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if include_timestamp else ""
    
    # Format CSS with color values
    css = CSS_STYLES.format(
        bg_color=COLOR_PALETTE['background'],
        text_color=COLOR_PALETTE['text_dark'],
        text_dark=COLOR_PALETTE['text_dark'],
        text_light=COLOR_PALETTE['text_light'],
        grad_dark=COLOR_PALETTE['gradient_dark'],
        grad_medium=COLOR_PALETTE['gradient_medium'],
        grad_light=COLOR_PALETTE['gradient_light'],
        success=COLOR_PALETTE['success'],
        info=COLOR_PALETTE['info'],
        warning=COLOR_PALETTE['warning'],
        danger=COLOR_PALETTE['danger'],
        secondary=COLOR_PALETTE['secondary'],
        neutral=COLOR_PALETTE['neutral'],
        cash=COLOR_PALETTE['cash'],
        non_cash=COLOR_PALETTE['non_cash'],
        sponsorship=COLOR_PALETTE['sponsorship'],
        public_fund=COLOR_PALETTE['public_fund'],
        bequest=COLOR_PALETTE['bequest'],
        other=COLOR_PALETTE['other'],
        stalwart=COLOR_PALETTE['stalwart'],
        pawn=COLOR_PALETTE['pawn'],
        one_hit=COLOR_PALETTE['one_hit'],
        border=COLOR_PALETTE['border'],
    )
    
    header_timestamp_html = f'<div class="timestamp">Generated: {timestamp}</div>' if timestamp else ""
    
    header_extra_html = f'\n{custom_header_html}' if custom_header_html else ""
    
    donation_legend_html = f'\n{DONATION_TYPE_LEGEND}' if include_donation_legend else ""
    
    footer_html = f"""
    <div class="footer">
        {footer_text if footer_text else '<p>Data analysis dashboard generated automatically</p>'}
        <p>Last updated: {timestamp if timestamp else 'N/A'}</p>
    </div>
    """ if (footer_text or include_timestamp) else '<div class="footer"></div>'
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
{css}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
        {header_timestamp_html}
        {header_extra_html}
    </div>
    
    <div class="container">
        {body_content}
        {donation_legend_html}
        {footer_html}
    </div>
</body>
</html>
"""
    
    return html


def create_stat_card_html(label, value, subvalue="", accent_class=""):
    """
    Generate HTML for a statistics card.
    
    Parameters:
    -----------
    label : str
        Card label (e.g., "Total Donations")
    value : str
        Main value to display (e.g., "£1.55B")
    subvalue : str, optional
        Additional information
    accent_class : str, optional
        CSS class for accent color (accent1-4)
    
    Returns:
    --------
    str
        HTML for statistics card
    """
    subvalue_html = f'<div class="stat-subvalue">{subvalue}</div>' if subvalue else ""
    
    return f"""
    <div class="stat-card {accent_class}">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        {subvalue_html}
    </div>
    """


def create_badge_html(text, badge_type="info"):
    """
    Generate HTML for a badge.
    
    Parameters:
    -----------
    text : str
        Badge text
    badge_type : str, default="info"
        Badge type (success, info, warning, danger, secondary, neutral)
    
    Returns:
    --------
    str
        HTML for badge
    """
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def create_insight_box_html(title, content_html):
    """
    Generate HTML for an insight/information box.
    
    Parameters:
    -----------
    title : str
        Box title
    content_html : str
        HTML content (can include lists, paragraphs, etc.)
    
    Returns:
    --------
    str
        HTML for insight box
    """
    return f"""
    <div class="insight">
        <h3>{title}</h3>
        {content_html}
    </div>
    """


# ============================================================================
# PRESET TEMPLATES
# ============================================================================

def get_political_donations_styled_html(
    title,
    subtitle,
    body_content,
    include_legend=True
):
    """
    Get styled HTML specifically for political donations dashboards.
    """
    
    custom_header = """
    <p style="font-size: 0.95em; opacity: 0.8;">
        Interactive dashboard with comprehensive analysis and filtering capabilities
    </p>
    """
    
    footer = """
    <p>Data source: Electoral Commission</p>
    <p>For more information, visit: www.electoralcommission.org.uk</p>
    """
    
    return get_styled_html(
        title=title,
        subtitle=subtitle,
        body_content=body_content,
        include_timestamp=True,
        include_donation_legend=include_legend,
        footer_text=footer,
        custom_header_html=custom_header
    )


def get_cabinet_analysis_styled_html(
    title,
    subtitle,
    body_content
):
    """
    Get styled HTML specifically for cabinet analysis dashboards.
    """
    
    custom_header = """
    <p style="font-size: 0.95em; opacity: 0.8;">
        Senior Cabinet Members (Commons) from 1970 onwards
    </p>
    """
    
    footer = """
    <p>Analysis of UK Cabinet tenure patterns and career trajectories</p>
    """
    
    return get_styled_html(
        title=title,
        subtitle=subtitle,
        body_content=body_content,
        include_timestamp=True,
        include_donation_legend=False,
        footer_text=footer,
        custom_header_html=custom_header
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_currency(value):
    """Format value as currency string."""
    if value >= 1_000_000:
        return f"£{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"£{value / 1_000:.0f}K"
    else:
        return f"£{value:.0f}"


def format_number(value):
    """Format number with thousand separators."""
    return f"{value:,}"


if __name__ == "__main__":
    print("Formatting Reference Module")
    print("=" * 50)
    print(f"Color Palette: {len(COLOR_PALETTE)} colors defined")
    print(f"CSS Styles: {len(CSS_STYLES)} characters")
    print(f"\nAvailable functions:")
    print("  - get_styled_html()")
    print("  - get_political_donations_styled_html()")
    print("  - get_cabinet_analysis_styled_html()")
    print("  - create_stat_card_html()")
    print("  - create_badge_html()")
    print("  - create_insight_box_html()")
    print("  - format_currency()")
    print("  - format_number()")


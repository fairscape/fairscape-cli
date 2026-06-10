"""Generate a standalone, self-contained HTML visualization of an evidence graph.

The HTML shell lives in templates/evidence_graph/evidence_graph.html.j2 and the
application JavaScript in evidence_graph.js next to it. React, ReactDOM and
dagre are vendored under templates/evidence_graph/vendor/ and inlined into the
output, so the generated file is a single offline-shareable HTML document with
no CDN dependency.
"""
import argparse
import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / 'templates' / 'evidence_graph'
VENDOR_FILES = (
    'vendor/react.production.min.js',
    'vendor/react-dom.production.min.js',
    'vendor/dagre.min.js',
)


def _inline_script_safe(js: str) -> str:
    """Make JS safe to inline in a <script> tag (no '</script>' breakout)."""
    return js.replace('</script', '<\\/script')


def generate_evidence_graph_html(rocrate_path, output_path=None):
    """
    Generate a standalone HTML file containing an interactive React
    visualization of the evidence graph extracted from an RO-Crate.

    Args:
        rocrate_path: Path to the RO-Crate metadata.json file
        output_path: Path where the HTML output should be saved
            (default: same path as input with .html extension)

    Returns:
        Path to the generated HTML file as str, or None on failure.
    """
    try:
        with open(rocrate_path, 'r', encoding='utf-8') as f:
            rocrate_data = json.load(f)
    except FileNotFoundError:
        logger.error("RO-Crate file not found at %s", rocrate_path)
        return None
    except json.JSONDecodeError:
        logger.error("Could not parse JSON from %s", rocrate_path)
        return None
    except Exception:
        logger.error("Unexpected error reading RO-Crate %s", rocrate_path, exc_info=True)
        return None

    if output_path is None:
        output_path = Path(rocrate_path).with_suffix('.html')
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    vendor_js = ';\n'.join(
        (TEMPLATE_DIR / name).read_text(encoding='utf-8') for name in VENDOR_FILES
    )
    app_js = (TEMPLATE_DIR / 'evidence_graph.js').read_text(encoding='utf-8')

    # Escaping '<' keeps the JSON valid JS while preventing a '</script>' (or
    # '<!--') inside metadata values from terminating the script tag.
    graph_json = json.dumps(rocrate_data).replace('<', '\\u003c')

    # autoescape stays off: everything injected is our own JS or the
    # pre-escaped JSON above.
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    template = env.get_template('evidence_graph.html.j2')
    html_content = template.render(
        title='Evidence Graph Visualization',
        vendor_js=_inline_script_safe(vendor_js),
        graph_json=graph_json,
        app_js=_inline_script_safe(app_js),
    )

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(output_path)
    except IOError:
        logger.error("Error writing HTML file to %s", output_path, exc_info=True)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate an evidence graph visualization from an RO-Crate'
    )
    parser.add_argument('rocrate_path', help='Path to the RO-Crate metadata.json file (or equivalent .jsonld)')
    parser.add_argument('--output', '-o', help='Output HTML file path (default: <rocrate_path_base>-evidence-graph.html)')

    args = parser.parse_args()

    crate_path = Path(args.rocrate_path)
    if not crate_path.is_file():
        print(f"Error: Input file not found at '{args.rocrate_path}'")
    else:
        output_file = args.output
        if not output_file:
            output_file = crate_path.parent / f"{crate_path.stem}-evidence-graph.html"
        result = generate_evidence_graph_html(str(crate_path), str(output_file))
        print(result if result else "Failed to generate evidence graph HTML")

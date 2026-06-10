import json
import pathlib

import pytest

from fairscape_cli.datasheet_builder.evidence_graph.html_builder import (
    generate_evidence_graph_html,
)


@pytest.fixture
def graph_json_file(tmp_path: pathlib.Path):
    data = {
        "@id": "ark:59852/evidence-graph-test",
        "@graph": [
            {
                "@id": "ark:59852/dataset-test",
                "@type": "https://w3id.org/EVI#Dataset",
                "name": "Test Dataset",
                "description": "A dataset",
                "generatedBy": {"@id": "ark:59852/computation-test"},
            },
            {
                "@id": "ark:59852/computation-test",
                "@type": "https://w3id.org/EVI#Computation",
                "name": "Test Computation",
            },
        ],
    }
    path = tmp_path / "provenance-graph.json"
    path.write_text(json.dumps(data))
    return path


class TestEvidenceGraphHtml:
    def test_generates_self_contained_html(self, graph_json_file, tmp_path):
        output = tmp_path / "provenance-graph.html"
        result = generate_evidence_graph_html(str(graph_json_file), str(output))

        assert result == str(output)
        html = output.read_text()

        # data is injected via the global, read by the app script
        assert "window.__EVIDENCE_GRAPH_DATA__" in html
        assert "ark:59852/dataset-test" in html
        # app JS made it in
        assert "getInitialGraphState" in html
        # legend present
        assert "graph-legend" in html
        # vendored libraries inlined; no CDN script tags remain
        assert "@license React" in html
        assert "unpkg.com" not in html
        assert "jsdelivr" not in html

    def test_script_breakout_is_escaped(self, tmp_path):
        data = {
            "@graph": [
                {
                    "@id": "ark:59852/evil",
                    "@type": "https://w3id.org/EVI#Dataset",
                    "name": "</script><script>alert(1)</script>",
                }
            ]
        }
        src = tmp_path / "evil.json"
        src.write_text(json.dumps(data))
        output = tmp_path / "evil.html"

        result = generate_evidence_graph_html(str(src), str(output))
        assert result is not None
        html = output.read_text()

        # the hostile name must be <-escaped inside the data assignment
        data_line = next(
            line for line in html.splitlines()
            if "__EVIDENCE_GRAPH_DATA__" in line
        )
        payload = data_line.split("=", 1)[1].rsplit("</script>", 1)[0]
        assert "</script>" not in payload
        assert "\\u003c/script" in payload

        # only the three structural script blocks close in the document
        assert html.count("</script>") == 3

    def test_missing_input_returns_none(self, tmp_path):
        assert generate_evidence_graph_html(str(tmp_path / "nope.json")) is None

    def test_invalid_json_returns_none(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        assert generate_evidence_graph_html(str(bad)) is None

    def test_default_output_path(self, graph_json_file):
        result = generate_evidence_graph_html(str(graph_json_file))
        expected = graph_json_file.with_suffix(".html")
        assert result == str(expected)
        assert expected.exists()

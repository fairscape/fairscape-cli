"""SHACL validation of an RO-Crate against the bundled FAIRSCAPE profile.

This is an OPTIONAL feature: it needs `pyshacl`, which is not a core dependency.
Install it with:

    pip install 'fairscape-cli[shacl]'

`rdflib` and `pyshacl` are imported lazily inside `shacl_report()` so that merely
importing this module never requires the optional packages — the CLI imports it
unconditionally and only pays the cost when `--shacl` is actually used. A missing
`pyshacl` surfaces as an ImportError that the command layer turns into a friendly
"install with…" message.

Ported from the reference implementation in NewMoniWork/shacl/validate.py (the
canonical source of the shapes profile), kept self-contained so the CLI does not
depend on that research directory.
"""

import json
import pathlib
from typing import Union

# The bundled shapes snapshot, resolved relative to the package (mirrors how the
# entailments ontology is located in commands/augment_commands.py). The canonical
# source lives in NewMoniWork/shacl/; see data/shapes/README.md to refresh it.
_PACKAGE_ROOT = pathlib.Path(__file__).parent.parent
DEFAULT_SHAPES_PATH = _PACKAGE_ROOT / "data" / "shapes" / "fairscape-shapes-v0.2.0.ttl"

# SHACL result vocabulary (avoids needing rdflib at import time).
_SHACL_NS = "http://www.w3.org/ns/shacl#"


def resolve_metadata_path(crate_path: Union[str, pathlib.Path]) -> pathlib.Path:
    """Resolve a crate path to its ro-crate-metadata.json file.

    Same rule as models.rocrate.ReadROCrateMetadata: a path that already names the
    metadata file is used as-is; otherwise it is treated as the crate directory and
    `ro-crate-metadata.json` is appended.
    """
    crate_path = pathlib.Path(crate_path)
    if "ro-crate-metadata.json" in str(crate_path):
        return crate_path
    return crate_path / "ro-crate-metadata.json"


def shacl_report(metadata_path: pathlib.Path,
                 shapes_path: pathlib.Path = DEFAULT_SHAPES_PATH) -> dict:
    """Validate a crate's JSON-LD against the SHACL shapes and split by severity.

    Returns a dict: {passes, violations, warnings, results, text} where `results`
    is a list of (severity, shape_label, message) tuples.

    pyshacl's own `conforms` is False if the report has ANY result, including
    sh:Warning. This profile uses sh:Warning for advisory findings (dangling refs,
    malformed ARKs) that must NOT fail an otherwise-valid crate, so we define the
    pass verdict ourselves: `passes` is True iff there are zero sh:Violation
    results. The pyshacl call needs advanced=True for the SPARQL-based custom rules.

    Raises ImportError if the optional `pyshacl` (or `rdflib`) is not installed.
    """
    import rdflib
    from pyshacl import validate as shacl_validate

    metadata_path = pathlib.Path(metadata_path)
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    data_graph = rdflib.Graph()
    data_graph.parse(data=json.dumps(data), format="json-ld")

    shapes_graph = rdflib.Graph().parse(str(shapes_path), format="turtle")

    _conforms, results_graph, results_text = shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="none",          # parity with Pydantic: no RDFS/OWL entailment
        advanced=True,             # required for the SPARQL-based custom rules
        meta_shacl=False,
        debug=False,
    )

    sh = rdflib.Namespace(_SHACL_NS)
    results = []  # (severity_local, shape_label, message)
    for r in results_graph.subjects(rdflib.RDF.type, sh.ValidationResult):
        sev = results_graph.value(r, sh.resultSeverity)
        msg = results_graph.value(r, sh.resultMessage)
        shape = results_graph.value(r, sh.sourceShape)
        # A sh:property constraint reports the inner (blank) property shape as its
        # sourceShape; resolve it back to the owning named NodeShape so the label
        # is readable (e.g. DatasetAuthorShape, not a blank-node id). sh:sparql
        # constraints already report the NodeShape, so the lookup is a no-op there.
        if shape is not None:
            parent = shapes_graph.value(predicate=sh.property, object=shape)
            if parent is not None:
                shape = parent
        results.append((str(sev).split("#")[-1] if sev else "?",
                        str(shape).split("#")[-1] if shape else "?",
                        str(msg) if msg else ""))

    violations = sum(1 for sev, _, _ in results if sev == "Violation")
    warnings = sum(1 for sev, _, _ in results if sev == "Warning")
    return {"passes": violations == 0, "violations": violations,
            "warnings": warnings, "results": results, "text": results_text}

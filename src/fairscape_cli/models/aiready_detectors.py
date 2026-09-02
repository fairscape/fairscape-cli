"""Graph-only entity detectors used by the sub-crate metric rollups.

These mirror the detectors in fairscape-grader's ``aireadiness_evidence``
package so that ``collect_subcrate_aggregated_metrics`` rolls entities up the
same way the grader would compute over an inlined graph.

They are duplicated here rather than imported. fairscape-grader already
declares a dependency on fairscape-cli, so importing it back would close a
dependency cycle and leave this package unable to build a crate without the
grader installed. Keep the tables below in step with
``aireadiness_evidence.crate`` and ``aireadiness_evidence.known``.
"""

import re
from typing import Any, Dict, Optional, Tuple

# --- Field tables ----------------------------------------------------------

CONTENT_URL_KEYS: Tuple[str, ...] = (
    "contentUrl", "url", "downloadUrl", "distribution",
)

# Fields that link an entity into the provenance graph (EVI + PROV spellings).
PROV_LINK_FIELDS: Tuple[str, ...] = (
    "generatedBy", "prov:wasGeneratedBy",
    "derivedFrom", "prov:wasDerivedFrom", "derivedTo",
    "usedByComputation", "usedBy", "usedByExperiment",
    "usedSoftware", "usedDataset", "usedSample", "usedInstrument",
    "usedTreatment", "usedStain", "usedContainer",
    "generated", "prov:used",
    "inputs", "outputs",
    "https://w3id.org/EVI#inputs", "https://w3id.org/EVI#outputs",
)

SCHEMA_REF_FIELDS: Tuple[str, ...] = (
    "EVI:Schema", "evi:Schema", "hasSchema", "dataSchema",
)

USED_SOFTWARE_KEYS: Tuple[str, ...] = (
    "usedSoftware", "https://w3id.org/EVI#usedSoftware",
)

INPUTS_KEYS: Tuple[str, ...] = (
    "usedDataset", "usedSample", "usedInstrument", "inputs",
    "https://w3id.org/EVI#inputs", "prov:used",
)

OUTPUTS_KEYS: Tuple[str, ...] = (
    "generated", "outputs", "https://w3id.org/EVI#outputs",
)

# A dataset states its origin through provenance or a repository accession.
DATASET_SOURCE_KEYS: Tuple[str, ...] = (
    "derivedFrom", "prov:wasDerivedFrom",
    "generatedBy", "prov:wasGeneratedBy",
)

# --- Repositories and identifiers ------------------------------------------

SPECIALIST_REPOS: Dict[str, str] = {
    "massive.ucsd.edu": "MassIVE (proteomics)",
    "massive-ftp.ucsd.edu": "MassIVE (proteomics)",
    "proteomecentral": "ProteomeXchange (proteomics)",
    "ebi.ac.uk/pride": "PRIDE (proteomics)",
    "ncbi.nlm.nih.gov/geo": "GEO (functional genomics)",
    "ncbi.nlm.nih.gov/sra": "SRA (sequence reads)",
    "trace.ncbi.nlm.nih.gov": "SRA (sequence reads)",
    "ncbi.nlm.nih.gov/gap": "dbGaP (genotype/phenotype)",
    "ebi.ac.uk/ena": "ENA (nucleotide archive)",
    "ebi.ac.uk/biostudies": "BioStudies",
    "empiar": "EMPIAR (EM imaging)",
    "proteinatlas.org": "Human Protein Atlas (imaging)",
    "physionet.org": "PhysioNet (physiologic signals)",
    "openneuro.org": "OpenNeuro (neuroimaging)",
    "idr.openmicroscopy.org": "IDR (imaging)",
    "cellosaurus": "Cellosaurus (cell lines)",
    "addgene.org": "Addgene (plasmids)",
}

GENERALIST_REPOS: Dict[str, str] = {
    "dataverse": "Dataverse",
    "zenodo.org": "Zenodo",
    "figshare.com": "Figshare",
    "datadryad.org": "Dryad",
    "osf.io": "OSF",
    "fairhub.io": "FAIRhub",
    "dataverse.lib.virginia.edu": "University of Virginia Dataverse (LibraData)",
    "data.mendeley.com": "Mendeley Data",
    "vivli.org": "Vivli",
    "icpsr.umich.edu": "ICPSR",
    "ddbj.nig.ac.jp": "DDBJ",
}

SOFTWARE_ARCHIVE_HOSTS: Dict[str, str] = {
    "zenodo.org": "Zenodo",
    "softwareheritage.org": "Software Heritage",
    "archive.softwareheritage.org": "Software Heritage",
    "doi.org": "DOI-registered archive",
    "dataverse": "Dataverse",
    "pypi.org": "PyPI",
}

PID_PATTERNS: Dict[str, "re.Pattern"] = {
    "DOI": re.compile(r"(doi\.org/|^doi:|^10\.\d{4,9}/)", re.I),
    "ARK": re.compile(r"(^ark:|/ark:)", re.I),
    "Handle": re.compile(r"(hdl\.handle\.net/|^hdl:)", re.I),
    "PURL": re.compile(r"purl\.(org|obolibrary\.org)/", re.I),
    "w3id": re.compile(r"w3id\.org/", re.I),
    "URN": re.compile(r"^urn:", re.I),
    "IGSN": re.compile(r"igsn\.org/|^igsn:", re.I),
    "CSTR": re.compile(r"cstr\.cn/|^cstr:", re.I),
}

# Accession syntaxes issued by specialist repositories.
ACCESSION_PATTERNS: Dict[str, "re.Pattern"] = {
    "MassIVE": re.compile(r"\bMSV\d{6,}\b"),
    "ProteomeXchange": re.compile(r"\bPXD\d{4,}\b"),
    "SRA": re.compile(r"\b[SED]R[RXSP]\d{5,}\b"),
    "BioProject": re.compile(r"\bPRJ(NA|EB|DB)\d+\b"),
    "BioSample": re.compile(r"\bSAM[NED][A-Z]?\d+\b"),
    "GEO": re.compile(r"\bG(SE|SM|PL)\d{3,}\b"),
    "dbGaP": re.compile(r"\bphs\d{6}\b"),
    "ArrayExpress": re.compile(r"\bE-[A-Z]{4}-\d+\b"),
    "EMPIAR": re.compile(r"\bEMPIAR-\d+\b"),
}

_TABULAR_FORMAT_RE = re.compile(
    r"csv|tsv|parquet|xlsx?|tab-separated|comma-separated|spreadsheet", re.I)
_TABULAR_EXT_RE = re.compile(r"\.(csv|tsv|parquet|xlsx?)(\?|#|$)", re.I)


# --- Generic helpers -------------------------------------------------------

def as_list(value: Any) -> list:
    """Wrap a scalar in a list; pass lists through; drop None."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def first_present(entity: Dict[str, Any], *keys: str) -> Any:
    """First non-empty value among ``keys``, or None."""
    for key in keys:
        value = entity.get(key)
        if value:
            return value
    return None


def _has_any(entity: Dict[str, Any], keys) -> bool:
    return any(entity.get(k) for k in keys)


def _text_of(value: Any) -> str:
    """Flatten a ref/list/scalar into one searchable string."""
    parts = []
    for item in as_list(value):
        if isinstance(item, dict):
            item = item.get("@id") or item.get("url") or item.get("contentUrl")
        if isinstance(item, str):
            parts.append(item)
    return " ".join(parts)


def _match_host(value: Any, table: Dict[str, str]) -> Optional[str]:
    text = _text_of(value).lower()
    if not text:
        return None
    for fragment, label in table.items():
        if fragment in text:
            return label
    return None


# --- Entity detectors ------------------------------------------------------

def has_provenance_link(entity: Dict[str, Any]) -> bool:
    return _has_any(entity, PROV_LINK_FIELDS)


def is_tabular_dataset(entity: Dict[str, Any]) -> bool:
    fmt = _text_of(first_present(entity, "format", "encodingFormat", "fileFormat"))
    if fmt and _TABULAR_FORMAT_RE.search(fmt):
        return True
    url = _text_of(first_present(entity, *CONTENT_URL_KEYS))
    return bool(url and _TABULAR_EXT_RE.search(url))


def get_dataset_schema_link(entity: Dict[str, Any]) -> Any:
    return first_present(entity, *SCHEMA_REF_FIELDS)


def get_used_software(entity: Dict[str, Any]) -> Any:
    return first_present(entity, *USED_SOFTWARE_KEYS)


def get_inputs(entity: Dict[str, Any]) -> Any:
    return first_present(entity, *INPUTS_KEYS)


def get_outputs(entity: Dict[str, Any]) -> Any:
    return first_present(entity, *OUTPUTS_KEYS)


def in_recognized_repository(value: Any) -> bool:
    """True when the link resolves into a specialist or generalist repository."""
    return bool(_match_host(value, SPECIALIST_REPOS)
                or _match_host(value, GENERALIST_REPOS))


def has_dataset_source(entity: Dict[str, Any]) -> bool:
    """The dataset states where it came from: provenance or an accession."""
    if _has_any(entity, DATASET_SOURCE_KEYS):
        return True
    return bool(AccessionDetector.detect(first_present(entity, *CONTENT_URL_KEYS)))


class AccessionDetector:
    """Specialist-repository accessions carried on a dataset link."""

    @staticmethod
    def detect(value: Any) -> Optional[str]:
        text = _text_of(value)
        if not text:
            return None
        for label, pattern in ACCESSION_PATTERNS.items():
            if pattern.search(text):
                return label
        return _match_host(text, SPECIALIST_REPOS)


class ArchiveDetector:
    """Resolvable / archival identifiers for software links."""

    @staticmethod
    def is_persistent_id(value: Any) -> bool:
        text = _text_of(value)
        if not text:
            return False
        if any(pattern.search(text) for pattern in PID_PATTERNS.values()):
            return True
        return bool(_match_host(text, SOFTWARE_ARCHIVE_HOSTS))

import json
import pathlib

from fairscape_models.rocrate import ROCrateV1_2

from fairscape_cli.utils.rocrate_helpers import get_root_entity, get_root_entity_dict


DESCRIPTOR = {
    "@id": "ro-crate-metadata.json",
    "@type": "CreativeWork",
    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2-DRAFT"},
    "about": {"@id": "ark:59852/rocrate-test"},
}

ROOT = {
    "@id": "ark:59852/rocrate-test",
    "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
    "name": "Test Crate",
}

OTHER_DATASET = {
    "@id": "ark:59852/dataset-other",
    "@type": ["https://w3id.org/EVI#Dataset"],
    "name": "Some file",
}


class TestGetRootEntityDict:
    def test_resolves_descriptor_about(self):
        graph = [DESCRIPTOR, ROOT, OTHER_DATASET]
        assert get_root_entity_dict(graph) is graph[1]

    def test_root_not_at_index_1(self):
        graph = [DESCRIPTOR, OTHER_DATASET, ROOT]
        root = get_root_entity_dict(graph)
        assert root is graph[2]
        assert root["@id"] == "ark:59852/rocrate-test"

    def test_descriptor_not_first(self):
        graph = [OTHER_DATASET, ROOT, DESCRIPTOR]
        assert get_root_entity_dict(graph)["@id"] == "ark:59852/rocrate-test"

    def test_no_descriptor_falls_back_to_rocrate_type(self):
        graph = [OTHER_DATASET, ROOT]
        assert get_root_entity_dict(graph)["@id"] == "ark:59852/rocrate-test"

    def test_no_descriptor_no_rocrate_type_falls_back_to_index_1(self):
        graph = [OTHER_DATASET, {"@id": "x", "@type": "Thing"}]
        assert get_root_entity_dict(graph)["@id"] == "x"

    def test_empty_graph(self):
        assert get_root_entity_dict([]) is None

    def test_single_entry_graph(self):
        assert get_root_entity_dict([OTHER_DATASET]) is None

    def test_returned_dict_is_mutable_reference(self):
        graph = [DESCRIPTOR, ROOT.copy(), OTHER_DATASET]
        root = get_root_entity_dict(graph)
        root["localEvidenceGraph"] = {"@id": "graph.html"}
        assert graph[1]["localEvidenceGraph"] == {"@id": "graph.html"}


class TestGetRootEntity:
    def test_resolves_root_on_fixture_crate(self):
        metadata_path = pathlib.Path("tests/data/cm4ai-release/ro-crate-metadata.json")
        with open(metadata_path) as f:
            crate_dict = json.load(f)
        # model_validate mutates @graph in place, so resolve the expected
        # root id from the raw dicts first
        descriptor = next(
            e for e in crate_dict["@graph"]
            if e["@id"].endswith("ro-crate-metadata.json")
        )
        expected_root_id = descriptor["about"]["@id"]

        crate = ROCrateV1_2.model_validate(crate_dict)
        root = get_root_entity(crate)

        assert root is not None
        assert root.guid == expected_root_id

    def test_root_not_at_index_1_in_model(self):
        other = {"@id": "ark:59852/thing-other", "@type": "Thing", "name": "Other"}
        full_root = dict(
            ROOT,
            description="d",
            keywords=["k"],
            version="1.0",
            hasPart=[],
            author="a",
            license="https://example.org/l",
        )
        crate_dict = {
            "@context": {},
            "@graph": [DESCRIPTOR, other, full_root],
        }
        crate = ROCrateV1_2.model_validate(crate_dict)
        root = get_root_entity(crate)
        assert root is not None
        assert root.guid == "ark:59852/rocrate-test"

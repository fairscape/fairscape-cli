import json
import pathlib

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import h5py
import pandas as pd
import pytest

from fairscape_cli.__main__ import cli as fairscape_cli_app


@pytest.fixture
def sample_parquet(tmp_path: pathlib.Path) -> pathlib.Path:
    """Parquet file exercising exact type fidelity (int64, float64, string, timestamp)."""
    table = pa.table({
        "count": pa.array([1, 2, 3], type=pa.int64()),
        "value": pa.array([1.5, 2.5, 3.5], type=pa.float64()),
        "label": pa.array(["a", "b", "c"]),
        "ts": pa.array(pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                       type=pa.timestamp("us")),
    })
    path = tmp_path / "sample.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture
def sample_h5(tmp_path: pathlib.Path) -> pathlib.Path:
    """HDF5 file with a root 1-D dataset and a nested structured-array dataset."""
    path = tmp_path / "sample.h5"
    with h5py.File(path, "w") as f:
        f.create_dataset("root_data", data=np.arange(10.0))
        grp = f.create_group("grp")
        arr = np.array([(1, 2.5), (2, 3.5)], dtype=[("id", "i8"), ("score", "f8")])
        grp.create_dataset("ds", data=arr)
    return path


class TestParquetHandler:
    def test_infer_preserves_exact_types(self, runner, tmp_path, sample_parquet):
        schema_path = tmp_path / "s_pq.json"
        result = runner.invoke(fairscape_cli_app, [
            "schema", "infer",
            "--name", "Parquet Schema",
            "--description", "Schema inferred from a parquet file for testing",
            str(sample_parquet), str(schema_path),
        ])
        assert result.exit_code == 0, result.output

        data = json.loads(schema_path.read_text())
        props = data["properties"]
        assert props["count"]["type"] == "integer"
        assert props["count"]["source-type"] == "int64"
        assert props["value"]["type"] == "number"
        assert props["value"]["source-type"] == "double"
        assert props["label"]["type"] == "string"
        # timestamp collapses to the canonical 'string' but records the exact source
        assert props["ts"]["type"] == "string"
        assert props["ts"]["source-type"] == "timestamp[us]"

    def test_validate_success(self, runner, tmp_path, sample_parquet):
        schema_path = tmp_path / "s_pq.json"
        runner.invoke(fairscape_cli_app, [
            "schema", "infer", "--name", "PQ", "--description", "parquet schema test",
            str(sample_parquet), str(schema_path),
        ])
        result = runner.invoke(fairscape_cli_app, [
            "schema", "validate", "--schema", str(schema_path), "--data", str(sample_parquet),
        ])
        assert result.exit_code == 0, result.output
        assert "Validation Success" in result.output

    def test_validate_type_and_missing_column(self, runner, tmp_path, sample_parquet):
        schema_path = tmp_path / "s_pq.json"
        runner.invoke(fairscape_cli_app, [
            "schema", "infer", "--name", "PQ", "--description", "parquet schema test",
            str(sample_parquet), str(schema_path),
        ])
        data = json.loads(schema_path.read_text())
        # break the count column's declared source type + add a nonexistent column
        data["properties"]["count"]["type"] = "number"
        data["properties"]["count"]["source-type"] = "float64"
        data["properties"]["missing_col"] = {"type": "string", "index": 9, "description": "not present"}
        schema_path.write_text(json.dumps(data))

        result = runner.invoke(fairscape_cli_app, [
            "schema", "validate", "--schema", str(schema_path), "--data", str(sample_parquet),
        ])
        assert result.exit_code != 0
        assert "type" in result.output
        assert "required" in result.output


class TestHDF5Handler:
    def test_infer_maps_datasets_to_object_properties(self, runner, tmp_path, sample_h5):
        schema_path = tmp_path / "s_h5.json"
        result = runner.invoke(fairscape_cli_app, [
            "schema", "infer",
            "--name", "HDF5 Schema",
            "--description", "Schema inferred from an hdf5 file for testing",
            str(sample_h5), str(schema_path),
        ])
        assert result.exit_code == 0, result.output

        data = json.loads(schema_path.read_text())
        props = data["properties"]
        assert "grp/ds" in props
        assert "root_data" in props
        ds = props["grp/ds"]
        assert ds["type"] == "object"
        assert ds["hdf5-path"] == "grp/ds"
        assert ds["properties"]["id"]["type"] == "integer"
        assert ds["properties"]["score"]["type"] == "number"
        # every nested column type is one of the six canonical types
        canonical = {"integer", "number", "string", "array", "boolean", "object"}
        for dataset_prop in props.values():
            for col in dataset_prop["properties"].values():
                assert col["type"] in canonical

    def test_validate_success(self, runner, tmp_path, sample_h5):
        schema_path = tmp_path / "s_h5.json"
        runner.invoke(fairscape_cli_app, [
            "schema", "infer", "--name", "H5", "--description", "hdf5 schema test",
            str(sample_h5), str(schema_path),
        ])
        result = runner.invoke(fairscape_cli_app, [
            "schema", "validate", "--schema", str(schema_path), "--data", str(sample_h5),
        ])
        assert result.exit_code == 0, result.output
        assert "Validation Success" in result.output

    def test_validate_missing_dataset(self, runner, tmp_path, sample_h5):
        schema_path = tmp_path / "s_h5.json"
        runner.invoke(fairscape_cli_app, [
            "schema", "infer", "--name", "H5", "--description", "hdf5 schema test",
            str(sample_h5), str(schema_path),
        ])
        data = json.loads(schema_path.read_text())
        data["properties"]["grp/nope"] = json.loads(json.dumps(data["properties"]["grp/ds"]))
        data["properties"]["grp/nope"]["hdf5-path"] = "grp/nope"
        schema_path.write_text(json.dumps(data))

        result = runner.invoke(fairscape_cli_app, [
            "schema", "validate", "--schema", str(schema_path), "--data", str(sample_h5),
        ])
        assert result.exit_code != 0
        assert "required" in result.output
        assert "grp/nope" in result.output

    def test_add_to_crate(self, runner, tmp_path, sample_h5):
        schema_path = tmp_path / "s_h5.json"
        runner.invoke(fairscape_cli_app, [
            "schema", "infer", "--name", "H5 Crate Schema",
            "--description", "hdf5 schema for crate integration testing",
            str(sample_h5), str(schema_path),
        ])
        crate_dir = tmp_path / "crate"
        runner.invoke(fairscape_cli_app, [
            "rocrate", "create", str(crate_dir),
            "--name", "Test Crate", "--organization-name", "Org",
            "--project-name", "Proj",
            "--description", "A test crate for hdf5 schema integration testing",
            "--keywords", "testing",
        ])
        # Previously HDF5 schemas lacked @type and failed crate validation.
        result = runner.invoke(fairscape_cli_app, [
            "schema", "add-to-crate", str(crate_dir), str(schema_path),
        ])
        assert result.exit_code == 0, result.output

        metadata = json.loads((crate_dir / "ro-crate-metadata.json").read_text())
        schema_entity = next(
            item for item in metadata["@graph"]
            if item.get("@type") == "EVI:Schema"
        )
        assert schema_entity["name"] == "H5 Crate Schema"
        assert "fairscapeVersion" in schema_entity


class TestLegacyCompat:
    def test_legacy_hdf5_schema_loads_validates_and_registers(self, runner, tmp_path, sample_h5):
        legacy = {
            "@id": "ark:59852/schema-legacy-hdf5",
            "name": "legacy hdf5",
            "description": "legacy format hdf5 schema for backward-compat testing",
            "required": ["root_data", "grp/ds"],
            "properties": {
                "root_data": {
                    "@id": "ark:59852/schema-sub1", "name": "legacy_root_data",
                    "description": "Dataset at root_data", "type": "object",
                    "separator": ",", "header": True, "additionalProperties": True,
                    "required": ["value"],
                    "properties": {"value": {"type": "number", "description": "Column value", "index": 0}},
                },
                "grp/ds": {
                    "@id": "ark:59852/schema-sub2", "name": "legacy_grp_ds",
                    "description": "Dataset at grp/ds", "type": "object",
                    "separator": ",", "header": True, "additionalProperties": True,
                    "required": ["id", "score"],
                    "properties": {
                        # non-canonical legacy frictionless type that must be
                        # normalized to a canonical type ('year' -> 'integer')
                        "id": {"type": "year", "description": "Column id", "index": 0},
                        "score": {"type": "number", "description": "Column score", "index": 1},
                    },
                },
            },
        }
        schema_path = tmp_path / "legacy_hdf5_schema.json"
        schema_path.write_text(json.dumps(legacy, indent=2))

        # the legacy non-canonical 'year' type must normalize to 'integer' on load
        from fairscape_cli.models.schema import load_schema
        normalized = load_schema(schema_path)
        id_prop = normalized.properties["grp/ds"].properties["id"]
        assert id_prop.type == "integer"
        assert (id_prop.model_extra or {}).get("source-type") == "year"

        validate_result = runner.invoke(fairscape_cli_app, [
            "schema", "validate", "--schema", str(schema_path), "--data", str(sample_h5),
        ])
        assert validate_result.exit_code == 0, validate_result.output

        crate_dir = tmp_path / "crate"
        runner.invoke(fairscape_cli_app, [
            "rocrate", "create", str(crate_dir),
            "--name", "Legacy Crate", "--organization-name", "Org",
            "--project-name", "Proj",
            "--description", "A test crate for legacy schema backward compat testing",
            "--keywords", "testing",
        ])
        add_result = runner.invoke(fairscape_cli_app, [
            "schema", "add-to-crate", str(crate_dir), str(schema_path),
        ])
        assert add_result.exit_code == 0, add_result.output


class TestValidateCommandRegistration:
    def test_validate_registered_once(self, runner):
        """The duplicate 'validate' definition was removed; it must appear once."""
        result = runner.invoke(fairscape_cli_app, ["schema", "--help"])
        assert result.exit_code == 0
        assert result.output.count("validate") == 1

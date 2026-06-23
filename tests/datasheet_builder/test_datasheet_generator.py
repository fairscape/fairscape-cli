import json
import logging
import pathlib
import shutil

import pytest

import fairscape_cli.datasheet_builder.rocrate.datasheet_generator as dg_module
from fairscape_cli.datasheet_builder import get_default_template_dir
from fairscape_cli.datasheet_builder.rocrate.datasheet_generator import DatasheetGenerator


@pytest.fixture
def release_crate(tmp_path: pathlib.Path):
    source_crate_dir = pathlib.Path("tests/data/cm4ai-release")
    temp_crate_dir = tmp_path / "cm4ai-release"
    shutil.copytree(source_crate_dir, temp_crate_dir)
    return temp_crate_dir


def make_generator(crate_dir: pathlib.Path) -> DatasheetGenerator:
    return DatasheetGenerator(
        json_path=str(crate_dir / "ro-crate-metadata.json"),
        template_dir=str(get_default_template_dir()),
    )


class TestDatasheetGenerator:
    def test_save_datasheet_renders_redesigned_output(self, release_crate):
        generator = make_generator(release_crate)
        generator.process_subcrates()
        output_path = generator.save_datasheet()

        assert output_path.exists()
        html = output_path.read_text()

        # content
        assert "Cell Maps for Artificial Intelligence" in html
        assert "Perturbation Cell Atlas" in html
        # hero badges
        assert 'class="badge-row"' in html
        assert 'class="badge"' in html
        # AI-readiness donut (pure SVG, no chart library)
        assert 'class="aiready-donut"' in html
        assert "stroke-dasharray=" in html
        # theme variables present
        assert "--color-primary" in html

        # subcrate previews regenerated
        assert (release_crate / "Perturb-Seq/cell-atlas/ro-crate-preview.html").exists()
        assert (release_crate / "mass-spec/cancer-cells/ro-crate-preview.html").exists()

    def test_subcrate_metadata_loaded_once(self, release_crate, monkeypatch):
        """Index building, composition, and previews share one load per subcrate."""
        counts = {}
        real_load = json.load

        def counting_load(fp, *args, **kwargs):
            name = getattr(fp, "name", "")
            counts[name] = counts.get(name, 0) + 1
            return real_load(fp, *args, **kwargs)

        monkeypatch.setattr(dg_module.json, "load", counting_load)

        generator = make_generator(release_crate)
        generator.process_subcrates()
        generator.save_datasheet()

        subcrate_loads = {
            name: n for name, n in counts.items()
            if name.endswith("ro-crate-metadata.json")
            and ("cell-atlas" in name or "cancer-cells" in name)
        }
        assert subcrate_loads, "expected subcrate metadata files to be loaded"
        assert all(n == 1 for n in subcrate_loads.values()), subcrate_loads

    def test_broken_subcrate_is_skipped_and_logged(self, release_crate, caplog):
        broken = release_crate / "Perturb-Seq/cell-atlas/ro-crate-metadata.json"
        broken.write_text("{ not valid json")

        with caplog.at_level(logging.ERROR):
            generator = make_generator(release_crate)
            output_path = generator.save_datasheet()

        assert output_path.exists()
        html = output_path.read_text()
        # the intact subcrate still made it in
        assert "Mass Spec" in html
        # the failure was logged, not printed/silenced
        assert any("cell-atlas" in r.message or "Error loading subcrate" in r.message
                   for r in caplog.records)

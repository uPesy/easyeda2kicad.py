from __future__ import annotations

import base64
import re

import zstandard

from easyeda2kicad.__main__ import get_parser
from easyeda2kicad.easyeda.parameters_easyeda import (
    Ee3dModel,
    Ee3dModelBase,
    EeFootprint,
    EeFootprintBbox,
    EeFootprintInfo,
)
from easyeda2kicad.kicad.embedded_files import (
    format_embedded_model,
    kicad_embedded_checksum,
)
from easyeda2kicad.kicad.export_kicad_footprint import ExporterFootprintKicad

MODEL_DATA = b"#VRML V2.0 utf8\nShape {}\n"


def _footprint_with_model() -> EeFootprint:
    return EeFootprint(
        info=EeFootprintInfo(
            name="TEST_FOOTPRINT",
            fp_type="smd",
            model_3d_name="Test Model",
        ),
        bbox=EeFootprintBbox(x=0, y=0),
        model_3d=Ee3dModel(
            name="Test Model",
            uuid="model-uuid",
            translation=Ee3dModelBase(),
            rotation=Ee3dModelBase(),
        ),
    )


def test_embed_3d_model_is_enabled_by_default() -> None:
    parser = get_parser()
    default_args = parser.parse_args(["--lcsc_id", "C1", "--footprint"])
    external_args = parser.parse_args(
        ["--lcsc_id", "C1", "--footprint", "--no-embed-3d-model"]
    )

    assert default_args.embed_3d_model is True
    assert external_args.embed_3d_model is False


def test_kicad_embedded_checksum_matches_known_value() -> None:
    assert (
        kicad_embedded_checksum(MODEL_DATA)
        == "5AE369D6E830F6B533847216BB6D0518"
    )


def test_embedded_model_payload_round_trips() -> None:
    embedded = format_embedded_model(name="Test Model.wrl", data=MODEL_DATA)
    encoded = re.search(r"\(data \|(.*?)\|", embedded, flags=re.DOTALL)

    assert encoded is not None
    compressed = base64.b64decode("".join(encoded.group(1).split()))
    assert zstandard.ZstdDecompressor().decompress(compressed) == MODEL_DATA
    assert '(name "Test Model.wrl")' in embedded
    assert "(type model)" in embedded
    assert '(checksum "5AE369D6E830F6B533847216BB6D0518")' in embedded


def test_footprint_export_uses_embedded_model_uri(tmp_path) -> None:
    output = tmp_path / "TEST_FOOTPRINT.kicad_mod"
    ExporterFootprintKicad(footprint=_footprint_with_model()).export(
        footprint_full_path=str(output),
        model_3d_path="/external/models",
        embedded_model_data=MODEL_DATA,
    )
    footprint = output.read_text(encoding="utf-8")

    assert "(embedded_fonts no)" in footprint
    assert "(embedded_files" in footprint
    assert '(model "kicad-embed://Test Model.wrl"' in footprint
    assert "/external/models" not in footprint


def test_footprint_export_can_keep_external_model_reference(tmp_path) -> None:
    output = tmp_path / "TEST_FOOTPRINT.kicad_mod"
    ExporterFootprintKicad(footprint=_footprint_with_model()).export(
        footprint_full_path=str(output),
        model_3d_path="/external/models",
    )
    footprint = output.read_text(encoding="utf-8")

    assert "(embedded_files" not in footprint
    assert '(model "/external/models/Test Model.wrl"' in footprint

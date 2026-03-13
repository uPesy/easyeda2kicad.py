from __future__ import annotations

# Global imports
import argparse
import logging
import sys
from pathlib import Path
from typing import Any

# Local imports
from ._version import __version__
from .easyeda.easyeda_api import EasyedaApi
from .easyeda.easyeda_importer import (
    Easyeda3dModelImporter,
    EasyedaFootprintImporter,
    EasyedaSymbolImporter,
)
from .easyeda.parameters_easyeda import EeSymbol
from .kicad.export_kicad_3d_model import Exporter3dModelKicad
from .kicad.export_kicad_footprint import ExporterFootprintKicad
from .kicad.export_kicad_symbol import ExporterSymbolKicad


def parse_custom_fields(custom_field_args: list[str]) -> dict[str, str]:
    custom_fields: dict[str, str] = {}
    for custom_field in custom_field_args:
        key, separator, value = custom_field.partition(":")
        key = key.strip()
        value = value.strip()
        if not separator:
            raise ValueError(
                f'Invalid custom field "{custom_field}". Expected KEY:VALUE.'
            )
        if not key:
            raise ValueError(
                f'Invalid custom field "{custom_field}". Key must not be empty.'
            )
        custom_fields[key] = value
    return custom_fields


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "A Python script that convert any electronic components from LCSC or"
            " EasyEDA to a Kicad library"
        )
    )

    parser.add_argument(
        "--lcsc_id", help="LCSC id(s)", required=True, type=str, nargs="+"
    )

    parser.add_argument(
        "--symbol", help="Get symbol of this id", required=False, action="store_true"
    )

    parser.add_argument(
        "--footprint",
        help="Get footprint of this id",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--3d",
        help="Get the 3d model of this id",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--full",
        help="Get the symbol, footprint and 3d model of this id",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--output",
        required=False,
        metavar="file.kicad_sym",
        help="Output file",
        type=str,
    )

    parser.add_argument(
        "--overwrite",
        required=False,
        help=(
            "overwrite symbol, footprint, and 3D model if there is already a component"
            " with this lcsc_id"
        ),
        action="store_true",
    )

    parser.add_argument(
        "--project-relative",
        required=False,
        help="Sets the 3D file path stored relative to the project",
        action="store_true",
    )

    parser.add_argument(
        "--debug",
        help="set the logging level to debug",
        required=False,
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--use-cache",
        dest="use_cache",
        help="cache API responses in .easyeda_cache/ to avoid repeated network requests",
        required=False,
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--custom-field",
        dest="custom_field",
        nargs="+",
        default=[],
        metavar="KEY:VALUE",
        help="Add custom symbol properties, e.g. --custom-field 'Mfr:TI' 'Package:SOT-23'",
    )

    return parser


def valid_arguments(arguments: dict[str, Any]) -> bool:
    for lcsc_id in arguments["lcsc_id"]:
        if not lcsc_id.startswith("C"):
            logging.error(f"lcsc_id '{lcsc_id}' should start with C")
            return False

    if arguments["full"]:
        arguments["symbol"], arguments["footprint"], arguments["3d"] = True, True, True

    if not any([arguments["symbol"], arguments["footprint"], arguments["3d"]]):
        logging.error(
            "Missing action arguments\n"
            "  easyeda2kicad --lcsc_id=C2040 --footprint\n"
            "  easyeda2kicad --lcsc_id=C2040 --symbol"
        )
        return False

    try:
        arguments["custom_fields"] = parse_custom_fields(arguments["custom_field"])
    except ValueError as err:
        logging.error(str(err))
        return False

    if arguments["project_relative"] and not arguments["output"]:
        logging.error(
            "A project specific library path should be given with --output option when"
            " using --project-relative option\nFor example: easyeda2kicad"
            " --lcsc_id=C2040 --full"
            " --output=C:/Users/your_username/Documents/Kicad/6.0/projects/my_project"
            " --project-relative"
        )
        return False

    if arguments["output"]:
        output_path = Path(arguments["output"])

        # If the user passed a directory (no filename), use default lib name
        if output_path.is_dir():
            base_folder = output_path
            lib_name = "EasyEDA"
        else:
            base_folder = output_path.parent
            lib_name = output_path.stem or "EasyEDA"

        if not base_folder.is_dir():
            logging.error(f"Can't find the folder : {base_folder}")
            return False
    else:
        base_folder = Path.home() / "Documents" / "Kicad" / "easyeda2kicad"
        base_folder.mkdir(parents=True, exist_ok=True)
        lib_name = "easyeda2kicad"
        arguments["use_default_folder"] = True

    arguments["output"] = str(base_folder / lib_name)

    return True


def _process_component(
    component_id: str,
    arguments: dict[str, Any],
    api: EasyedaApi,
) -> bool:
    """Process a single LCSC component. Returns True on success, False on error."""
    cad_data = api.get_cad_data_of_component(lcsc_id=component_id)
    if not cad_data:
        logging.error(f"Failed to fetch data from EasyEDA API for part {component_id}")
        return False

    output = arguments["output"]

    if arguments["symbol"]:
        # ---------------- SYMBOL ----------------
        easyeda_symbol: EeSymbol = EasyedaSymbolImporter(
            easyeda_cp_cad_data=cad_data
        ).get_symbol()
        lib_path = f"{output}.kicad_sym"
        exporter = ExporterSymbolKicad(
            symbol=easyeda_symbol,
            lib_path=lib_path,
            custom_fields=arguments["custom_fields"],
        )
        if not exporter.save_to_lib(
            lib_path=lib_path,
            footprint_lib_name=Path(output).stem,
            overwrite=arguments["overwrite"],
        ):
            logging.error(
                f"Symbol for {component_id} already exists. Use --overwrite to update"
            )
            return False
        if easyeda_symbol.sub_symbols:
            logging.info(
                f"Integrated {len(easyeda_symbol.sub_symbols)} sub-symbols into main symbol"
            )
        logging.info(
            f"Created Kicad symbol for ID : {component_id}\n"
            f"       Symbol name : {easyeda_symbol.info.name}\n"
            f"       Library path : {lib_path}"
        )

    if arguments["footprint"]:
        # ---------------- FOOTPRINT ----------------
        easyeda_footprint = EasyedaFootprintImporter(
            easyeda_cp_cad_data=cad_data
        ).get_footprint()
        if (
            Path(f"{output}.pretty") / f"{easyeda_footprint.info.name}.kicad_mod"
        ).is_file() and not arguments["overwrite"]:
            logging.error(
                f"Footprint for {component_id} already exists. Use --overwrite to replace"
            )
            return False
        footprint_path = Path(f"{output}.pretty")
        if arguments.get("use_default_folder"):
            model_3d_path = "${EASYEDA2KICAD}/easyeda2kicad.3dshapes"
        elif arguments["project_relative"]:
            model_3d_path = (
                "${KIPRJMOD}/"
                + Path(f"{output}.3dshapes").relative_to(Path.cwd()).as_posix()
            )
        else:
            model_3d_path = Path(f"{output}.3dshapes").as_posix()
        footprint_filename = f"{easyeda_footprint.info.name}.kicad_mod"
        ExporterFootprintKicad(footprint=easyeda_footprint).export(
            footprint_full_path=str(footprint_path / footprint_filename),
            model_3d_path=model_3d_path,
        )
        logging.info(
            f"Created Kicad footprint for ID: {component_id}\n"
            f"       Footprint name: {easyeda_footprint.info.name}\n"
            f"       Footprint path: {footprint_path / footprint_filename}"
        )

    if arguments["3d"]:
        # ---------------- 3D MODEL ----------------
        model_exporter = Exporter3dModelKicad(
            model_3d=Easyeda3dModelImporter(
                easyeda_cp_cad_data=cad_data,
                download_raw_3d_model=True,
                api=api,
            ).output,
        )
        output_dir = Path(f"{output}.3dshapes")
        if not model_exporter.output:
            logging.warning(f"No 3D model available for ID: {component_id}")
        elif not model_exporter.export(
            output_dir=str(output_dir), overwrite=arguments["overwrite"]
        ):
            logging.error(
                f"3D model for {component_id} already exists. Use --overwrite to replace"
            )
            return False
        else:
            model_name = model_exporter.output.name
            logging.info(
                f"Created 3D model for ID: {component_id}\n"
                f"       3D model name: {model_name}\n"
                f"       3D model path (wrl): {output_dir / f'{model_name}.wrl'}\n"
                f"       3D model path (step): {output_dir / f'{model_name}.step'}"
            )

    return True


def main(argv: list[str] = sys.argv[1:]) -> int:
    print(f"-- easyeda2kicad.py v{__version__} --")

    # cli interface
    parser = get_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as err:
        return err.code if isinstance(err.code, int) else 1
    arguments = vars(args)

    log_level = logging.DEBUG if arguments["debug"] else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(
            logging.Formatter(fmt="[{levelname}] {message}", style="{")
        )
        root_logger.addHandler(handler)

    if not valid_arguments(arguments=arguments):
        return 1

    api = EasyedaApi(use_cache=arguments["use_cache"])
    had_errors = False

    for component_id in arguments["lcsc_id"]:
        if not _process_component(component_id, arguments, api):
            had_errors = True

    return 1 if had_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

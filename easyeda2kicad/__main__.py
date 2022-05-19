# Global imports
import argparse
import logging
import os
import re
import sys
from textwrap import dedent
from typing import List

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
from easyeda2kicad.easyeda.easyeda_importer import (
    Easyeda3dModelImporter,
    EasyedaFootprintImporter,
    EasyedaSymbolImporter,
)
from easyeda2kicad.easyeda.parameters_easyeda import EeSymbol
from easyeda2kicad.helpers import (
    add_component_in_symbol_lib_file,
    id_already_in_symbol_lib,
    set_logger,
    update_component_in_symbol_lib_file,
)
from easyeda2kicad.kicad.export_kicad_3d_model import Exporter3dModelKicad
from easyeda2kicad.kicad.export_kicad_footprint import ExporterFootprintKicad
from easyeda2kicad.kicad.export_kicad_symbol import ExporterSymbolKicad
from easyeda2kicad.kicad.parameters_kicad_symbol import KicadVersion


def get_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "A Python script that convert any electronic components from LCSC or"
            " EasyEDA to a Kicad library"
        )
    )

    parser.add_argument("--lcsc_id", help="LCSC id", required=True, type=str)

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
        metavar="file.lib",
        help="Output file",
        type=str,
        # default=
    )

    parser.add_argument(
        "--overwrite",
        required=False,
        help=(
            "overwrite symbol and footprint lib if there is already a component with"
            " this lcsc_id"
        ),
        action="store_true",
    )

    parser.add_argument(
        "--v5",
        required=False,
        help="Convert library in legacy format for KiCad 5.x",
        action="store_true",
    )

    return parser


def valid_arguments(arguments: dict) -> bool:

    if not arguments["lcsc_id"].startswith("C"):
        logging.error("lcsc_id should start by C....")
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

    kicad_version = KicadVersion.v5 if arguments.get("v5") else KicadVersion.v6
    arguments["kicad_version"] = kicad_version

    if arguments["output"]:
        base_folder = "/".join(arguments["output"].replace("\\", "/").split("/")[:-1])
        lib_name = (
            arguments["output"]
            .replace("\\", "/")
            .split("/")[-1]
            .split(".lib")[0]
            .split(".kicad_sym")[0]
        )

        if not os.path.isdir(base_folder):
            logging.error("Can't find the folder")
            return False
    else:
        default_folder = os.path.join(
            os.path.expanduser("~"),
            "Documents",
            "Kicad",
            "easyeda2kicad",
        )
        if not os.path.isdir(default_folder):
            os.mkdir(default_folder)

        base_folder = default_folder
        lib_name = "easyeda2kicad"
    arguments["output"] = f"{base_folder}/{lib_name}"

    # Create new footprint folder if it does not exist
    if not os.path.isdir(f"{arguments['output']}.pretty"):
        os.mkdir(f"{arguments['output']}.pretty")
        logging.info(f"Create {lib_name}.pretty footprint folder in {base_folder}")

    # Create new 3d model folder if don't exist
    if not os.path.isdir(f"{arguments['output']}.3dshapes"):
        os.mkdir(f"{arguments['output']}.3dshapes")
        logging.info(f"Create {lib_name}.3dshapes 3D model folder in {base_folder}")

    lib_extension = "kicad_sym" if kicad_version == KicadVersion.v6 else "lib"
    if not os.path.isfile(f"{arguments['output']}.{lib_extension}"):
        with open(
            file=f"{arguments['output']}.{lib_extension}", mode="w+", encoding="utf-8"
        ) as my_lib:
            my_lib.write(
                dedent(
                    """\
                (kicad_symbol_lib
                  (version 20211014)
                  (generator https://github.com/uPesy/easyeda2kicad.py)
                )
                """
                )
                if kicad_version == KicadVersion.v6
                else "EESchema-LIBRARY Version 2.4\n#encoding utf-8\n"
            )
        logging.info(f"Create {lib_name}.{lib_extension} symbol lib in {base_folder}")

    return True


def delete_component_in_symbol_lib(
    lib_path: str, component_id: str, component_name: str
) -> None:
    with open(file=lib_path, encoding="utf-8") as f:
        current_lib = f.read()
        new_data = re.sub(
            rf'(#\n# {component_name}\n#\n.*?F6 "{component_id}".*?ENDDEF\n)',
            "",
            current_lib,
            flags=re.DOTALL,
        )

    with open(file=lib_path, mode="w", encoding="utf-8") as my_lib:
        my_lib.write(new_data)


def fp_already_in_footprint_lib(lib_path: str, package_name: str) -> bool:
    if os.path.isfile(f"{lib_path}/{package_name}.kicad_mod"):
        logging.warning(f"The footprint for this id is already in {lib_path}")
        return True
    return False


def main(argv: List[str] = sys.argv[1:]) -> int:

    set_logger(log_file=None, log_level=logging.INFO)

    # cli interface
    parser = get_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as err:
        return err.code
    arguments = vars(args)

    if not valid_arguments(arguments=arguments):
        return 1

    print("-- easyeda2kicad.py --")
    component_id = arguments["lcsc_id"]
    kicad_version = arguments["kicad_version"]
    sym_lib_ext = "kicad_sym" if kicad_version == KicadVersion.v6 else "lib"

    # Get CAD data of the component using easyeda API
    api = EasyedaApi()
    cad_data = api.get_cad_data_of_component(lcsc_id=component_id)

    # ---------------- SYMBOL ----------------
    if arguments["symbol"]:
        importer = EasyedaSymbolImporter(easyeda_cp_cad_data=cad_data)
        easyeda_symbol: EeSymbol = importer.get_symbol()

        is_id_already_in_symbol_lib = id_already_in_symbol_lib(
            lib_path=f"{arguments['output']}.{sym_lib_ext}",
            component_name=easyeda_symbol.info.name,
            kicad_version=kicad_version,
        )

        if not arguments["overwrite"] and is_id_already_in_symbol_lib:
            logging.error("Use --overwrite to update the older symbol lib")
            return 1

        logging.info(f"Creating Kicad symbol library for LCSC id : {component_id}")

        exporter = ExporterSymbolKicad(
            symbol=easyeda_symbol, kicad_version=kicad_version
        )
        # print(exporter.output)
        kicad_symbol_lib = exporter.get_kicad_lib()
        # print(kicad_symbol_lib)

        if is_id_already_in_symbol_lib:
            update_component_in_symbol_lib_file(
                lib_path=f"{arguments['output']}.{sym_lib_ext}",
                component_name=easyeda_symbol.info.name,
                component_content=kicad_symbol_lib,
                kicad_version=kicad_version,
            )
        else:
            add_component_in_symbol_lib_file(
                lib_path=f"{arguments['output']}.{sym_lib_ext}",
                component_content=kicad_symbol_lib,
                kicad_version=kicad_version,
            )

    # ---------------- FOOTPRINT ----------------
    if arguments["footprint"]:
        importer = EasyedaFootprintImporter(easyeda_cp_cad_data=cad_data)
        easyeda_footprint = importer.get_footprint()

        is_id_already_in_footprint_lib = fp_already_in_footprint_lib(
            lib_path=f"{arguments['output']}.pretty",
            package_name=easyeda_footprint.info.name,
        )
        if not arguments["overwrite"] and is_id_already_in_footprint_lib:
            logging.error("Use --overwrite to replace the older footprint lib")
            return 1

        logging.info(f"Creating Kicad footprint library for LCSC id : {component_id}")
        ExporterFootprintKicad(footprint=easyeda_footprint).export(
            output_path=arguments["output"]
        )

    # ---------------- 3D MODEL ----------------
    if arguments["3d"]:
        logging.info(f"Creating 3D model for LCSC id : {component_id}")
        exporter = Exporter3dModelKicad(
            model_3d=Easyeda3dModelImporter(easyeda_cp_cad_data=cad_data).output
        ).export(lib_path=arguments["output"])

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

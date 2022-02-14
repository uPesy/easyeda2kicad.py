# Global import

# Local imports
from core.cmd import cmd_interface

# Local import
from core.easyeda.easyeda_api import easyeda_api
from core.easyeda.easyeda_importer import (
    easyeda_footprint_importer,
    easyeda_symbol_importer,
)
from core.kicad.export_kicad_footprint import exporter_footprint_kicad
from core.kicad.export_kicad_symbol import exporter_symbol_kicad

if __name__ == "__main__":
    # Create cli interface
    cmd = cmd_interface()
    component_id = cmd.lcsc_id
    print("-- easyeda2kicad.py --")

    # Get CAD data of the component using easyeda API
    api = easyeda_api()
    cad_data = api.get_cad_data_of_component(lcsc_id=component_id)

    # For testing
    # with open('samples/test4.json') as json_file:
    #     cad_data = json.load(json_file)['result']

    # ---------------- SYMBOL ----------------
    if cmd.get_symbol:
        print(f"[*] Creating Kicad symbol library for LCSC id : {component_id}")
        importer = easyeda_symbol_importer(easyeda_cp_cad_data=cad_data)
        easyeda_symbol = importer.get_symbol()
        exporter = exporter_symbol_kicad(symbol=easyeda_symbol)
        # print(exporter.output)
        kicad_symbol_lib = exporter.export_symbol()
        with open(
            file="output_lib/easyeda2kicad.lib", mode="a+", encoding="utf-8"
        ) as my_lib:
            my_lib.write(kicad_symbol_lib)

        # print(kicad_symbol_lib)

    # ---------------- FOOTPRINT ----------------

    if cmd.get_footprint:
        print(f"[*] Creating Kicad footprint library for LCSC id : {component_id}")
        importer = easyeda_footprint_importer(easyeda_cp_cad_data=cad_data)
        easyeda_footprint = importer.get_footprint()

        if cmd.get_footprint:
            exporter = exporter_footprint_kicad(footprint=easyeda_footprint)
            # kicad_footprint = exporter.get_ki_footprint()
            # print(exporter.output)
            kicad_footprint_lib, lib_name = exporter.export_footprint()
            # print(kicad_footprint_lib)
            with open(
                file=f"output_lib/easyeda2kicad.pretty/{lib_name}.kicad_mod",
                mode="w",
                encoding="utf-8",
            ) as my_lib:
                my_lib.write(kicad_footprint_lib)

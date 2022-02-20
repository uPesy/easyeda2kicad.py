# Global imports
import argparse
import os

# -----------------------------------------------------------------------------


class cmd_interface:
    def __init__(self):

        # For the first run
        if not os.path.isdir("output_lib"):
            os.mkdir("output_lib")
        if not os.path.isdir("output_lib/easyeda2kicad.pretty"):
            os.mkdir("output_lib/easyeda2kicad.pretty")
        if not os.path.isfile("output_lib/easyeda2kicad.lib"):
            with open(
                file="output_lib/easyeda2kicad.lib", mode="w+", encoding="utf-8"
            ) as my_lib:
                my_lib.write("EESchema-LIBRARY Version 2.4\n#encoding utf-8\n")

        self.parser = argparse.ArgumentParser(description="easyeda2kicad")
        # self.parser.add_argument("--lcsc_id", help="LCSC id", required=True, default=None)
        self.parser.add_argument(
            "--lcsc_id", help="LCSC id", required=True
        )  # For devlopment
        self.parser.add_argument(
            "--symbol", help="Get symbol of the id", required=False, action="store_true"
        )
        self.parser.add_argument(
            "--footprint",
            help="Get footprint of the id",
            required=False,
            action="store_true",
        )

        self.lcsc_id = self.parser.parse_args().lcsc_id
        self.get_symbol = self.parser.parse_args().symbol
        self.get_footprint = self.parser.parse_args().footprint

        # Arguments validation
        self.verify_if_fp_or_sb_in_input()
        self.verify_id_not_already_done()

    def verify_if_fp_or_sb_in_input(self):
        if not (self.get_symbol or self.get_footprint):
            print("easyeda2kicad.py: error: add --symbol or  --footprint parameters")
            quit()

    def verify_id_not_already_done(self):
        if self.get_symbol:
            with open("output_lib/easyeda2kicad.lib", encoding="utf-8") as f:
                current_lib = f.read()
                if self.lcsc_id in current_lib:
                    print("[-] This id is already in easyeda2kicad.lib")
                    self.get_symbol = False

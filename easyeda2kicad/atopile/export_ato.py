# Global imports
import logging
from pathlib import Path
import re
from textwrap import dedent

log = logging.getLogger(__name__)

from easyeda2kicad.easyeda.parameters_easyeda import (
    EasyedaPinType,
    EeSymbol,
)

ee_pin_type_to_ato_pin_type = {
    EasyedaPinType.unspecified: None,
    EasyedaPinType._input: "input",
    EasyedaPinType.output: "output",
    EasyedaPinType.bidirectional: "bidirectional",
    EasyedaPinType.power: "power",
}
ee_pin_rotation_to_vis_side = {0: "right", 90: "bottom", 180: "left", 270: "top"}


def add_pin_vis(name, pos):
    return f"""
  - name: {name}
    index: 0
    private: false
    port: {pos}"""


def sanitize_name(name: str) -> str:
    # Replace all non-alphanumeric characters with underscores
    sanitized = re.sub(r"\W", "_", name)

    # Check if the first character is a digit, and if so, prepend an underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"

    return sanitized

replacement_dict = {
    "+": "plus",
    "-": "minus",
    "/": "slash",
    "*": "star",
    "(": "lparen",
    ")": "rparen",
    "[": "lbracket",
    "]": "rbracket",
    "{": "lbrace",
    "}": "rbrace",
    "<": "less",
    ">": "greater",
    "=": "equal",
    "~": "tilde",
    "!": "exclamation",
    "@": "at",
    "#": "hash",
    "$": "dollar",
    "%": "percent",
    "^": "caret",
    "&": "ampersand",
    "|": "pipe",
    "\\": "backslash",
    ":": "colon",
    ";": "semicolon",
    "'": "apostrophe",
    '"': "quote",
    "?": "question",
    ",": "comma",
    ".": "period",
    " ": "space",
    "\t": "tab",
}

def convert_to_ato(
    ee_symbol: EeSymbol, component_id: str, component_name: str, footprint: str
) -> str:
    ato_str = f"component {sanitize_name(component_name)}:\n"
    ato_str += f"    # component {component_name}\n"
    ato_str += f'    footprint = "{footprint}"\n'
    ato_str += f'    lcsc_id = "{component_id}"\n'
    ato_str += "    # pins\n"

    defined_signals = set()
    for ee_pin in ee_symbol.pins:
        signal = sanitize_name(ee_pin.name.text)
        # add an underscore to the start of the signal name if it starts with a number
        if signal in replacement_dict:
            signal = replacement_dict[signal]
        if signal[0].isdigit():
            signal = "_" + signal
        pin = ee_pin.settings.spice_pin_number.replace(" ", "")
        #check if the signal name has already been defined
        if signal in defined_signals:
            #if it has, append the pin number to the signal name
            ato_str += f"    {signal} ~ pin {pin}\n"
        else:
            defined_signals.add(signal)
            ato_str += f"    signal {signal} ~ pin {pin}\n"
        ato_pin_type = ee_pin_type_to_ato_pin_type[ee_pin.settings.type]

    return ato_str + "\n"


class ExporterAto:
    def __init__(self, symbol, component_id: str, component_name: str, footprint: str):
        self.input: EeSymbol = symbol
        self.output = (
            convert_to_ato(
                ee_symbol=self.input,
                component_id=component_id,
                component_name=component_name,
                footprint=footprint,
            )
            if isinstance(self.input, EeSymbol)
            else logging.error("Unknown input symbol format")
        )

    def export(self, ato_full_path: str) -> str:
        # Get the directory of the file
        ato_dir = Path(ato_full_path).parent
        ato_dir.mkdir(parents=True, exist_ok=True)
        log.log(level=logging.INFO, msg=ato_full_path)
        with open(file=ato_full_path, mode="w", encoding="utf-8") as my_lib:
            my_lib.write(self.output)
            log.log(level=logging.INFO, msg="ATO file written")


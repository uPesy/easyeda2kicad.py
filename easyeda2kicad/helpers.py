# Global imports
import logging
import math
import re

# Local imports
from .kicad.parameters_kicad_symbol import KicadVersion

sym_lib_regex_pattern = {
    "v5": r"(#\n# {component_name}\n#\n.*?ENDDEF\n)",
    # v6 covers KiCad 6 through current (7/8/9/10+): the .kicad_sym S-Expression
    # format has been stable since KiCad 6.0.
    "v6": r'\n(\s*)\(symbol "{component_name}".*?\n\1\)(?=\n|$)',
}


def set_logger(log_file: str | None, log_level: int) -> None:
    root_log = logging.getLogger()
    root_log.setLevel(log_level)

    if log_file:
        file_handler = logging.FileHandler(
            filename=log_file, mode="w", encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="[{asctime}][{levelname}][{funcName}] {message}", style="{"
            )
        )
        root_log.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(
        logging.Formatter(fmt="[{levelname}] {message}", style="{")
    )
    root_log.addHandler(stream_handler)


def sanitize_for_regex(field: str) -> str:
    return re.escape(field)


def id_already_in_symbol_lib(
    lib_path: str, component_name: str, kicad_version: KicadVersion
) -> bool:
    with open(lib_path, encoding="utf-8") as lib_file:
        current_lib = lib_file.read()
        component = re.findall(
            sym_lib_regex_pattern[kicad_version.name].format(
                component_name=sanitize_for_regex(component_name)
            ),
            current_lib,
            flags=re.DOTALL,
        )
        if component != []:
            logging.warning(f"This id is already in {lib_path}")
            return True
    return False


def update_component_in_symbol_lib_file(
    lib_path: str,
    component_name: str,
    component_content: str,
    kicad_version: KicadVersion,
) -> None:
    with open(file=lib_path, encoding="utf-8") as lib_file:
        current_lib = lib_file.read()
        new_lib = re.sub(
            sym_lib_regex_pattern[kicad_version.name].format(
                component_name=sanitize_for_regex(component_name)
            ),
            component_content,
            current_lib,
            flags=re.DOTALL,
        )

        new_lib = new_lib.replace(
            "(generator kicad_symbol_editor)",
            "(generator https://github.com/uPesy/easyeda2kicad.py)",
        )

    with open(file=lib_path, mode="w", encoding="utf-8") as lib_file:
        lib_file.write(new_lib)


def add_component_in_symbol_lib_file(
    lib_path: str, component_content: str, kicad_version: KicadVersion
) -> None:
    if kicad_version == KicadVersion.v5:
        with open(file=lib_path, mode="a+", encoding="utf-8") as lib_file:
            lib_file.write(component_content)
    elif kicad_version == KicadVersion.v6:
        # Read the current library file
        with open(file=lib_path, encoding="utf-8") as lib_file:
            current_lib_data = lib_file.read()

        # Find the position before the closing parenthesis of the library
        # The library structure should be: (kicad_symbol_lib ... )
        # We need to insert the symbol before the final closing parenthesis
        last_paren_pos = current_lib_data.rfind(")")
        if last_paren_pos == -1:
            raise ValueError("Invalid KiCad library file: no closing parenthesis found")

        # Ensure proper indentation for the component content
        # Split component_content into lines and add proper indentation
        component_lines = component_content.split("\n")
        indented_component = "\n".join(
            "  " + line if line.strip() else line for line in component_lines
        )

        # Insert the component content before the closing parenthesis
        new_lib_data = (
            current_lib_data[:last_paren_pos]
            + indented_component
            + "\n"
            + current_lib_data[last_paren_pos:]
        )

        # Write the updated library file
        with open(file=lib_path, mode="w", encoding="utf-8") as lib_file:
            lib_file.write(
                new_lib_data.replace(
                    "(generator kicad_symbol_editor)",
                    "(generator https://github.com/uPesy/easyeda2kicad.py)",
                )
            )


def get_middle_arc_pos(
    center_x: float,
    center_y: float,
    radius: float,
    angle_start: float,
    angle_end: float,
) -> tuple[float, float]:
    middle_x = center_x + radius * math.cos((angle_start + angle_end) / 2)
    middle_y = center_y + radius * math.sin((angle_start + angle_end) / 2)
    return middle_x, middle_y

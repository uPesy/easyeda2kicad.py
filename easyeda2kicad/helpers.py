from __future__ import annotations

# Global imports
import logging
import re

__all__ = ["KicadVersion"]

# Local imports
from ._version import GENERATOR_URL
from .kicad.parameters_kicad_symbol import KicadVersion

sym_lib_regex_pattern = {
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
            component_content.rstrip("\n"),
            current_lib,
            flags=re.DOTALL,
        )

        new_lib = new_lib.replace(
            "(generator kicad_symbol_editor)",
            f"(generator {GENERATOR_URL})",
        )

    with open(file=lib_path, mode="w", encoding="utf-8") as lib_file:
        lib_file.write(new_lib)


def add_component_in_symbol_lib_file(lib_path: str, component_content: str) -> None:
    # Read the current library file
    with open(file=lib_path, encoding="utf-8") as lib_file:
        current_lib_data = lib_file.read()

    # Find the position before the closing parenthesis of the library
    # The library structure should be: (kicad_symbol_lib ... )
    # We need to insert the symbol before the final closing parenthesis
    last_paren_pos = current_lib_data.rfind(")")
    if last_paren_pos == -1:
        raise ValueError("Invalid KiCad library file: no closing parenthesis found")

    # Insert the component content before the closing parenthesis.
    # Ensure exactly one newline between the symbol and the closing paren.
    sep = "" if component_content.endswith("\n") else "\n"
    new_lib_data = (
        current_lib_data[:last_paren_pos]
        + component_content
        + sep
        + current_lib_data[last_paren_pos:]
    )

    # Write the updated library file
    with open(file=lib_path, mode="w", encoding="utf-8") as lib_file:
        lib_file.write(
            new_lib_data.replace(
                "(generator kicad_symbol_editor)",
                f"(generator {GENERATOR_URL})",
            )
        )

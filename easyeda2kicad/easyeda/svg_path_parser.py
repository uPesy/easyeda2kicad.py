# Global imports
import logging
import re
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import List, Union


@dataclass
class SvgPathMoveTo:
    start_x: float
    start_y: float


@dataclass
class SvgPathLineTo:
    pos_x: float
    pos_y: float


@dataclass
class SvgPathEllipticalArc:
    radius_x: float
    radius_y: float
    x_axis_rotation: float
    flag_large_arc: bool
    flag_sweep: bool
    end_x: float
    end_y: float


@dataclass
class SvgPathClosePath:
    pass


svg_path_handlers = {
    "M": (SvgPathMoveTo, 2),
    "A": (SvgPathEllipticalArc, 7),
    "L": (SvgPathLineTo, 2),
    "Z": (SvgPathClosePath, 0),
}


def parse_svg_path(svg_path: str) -> list:
    if not svg_path.endswith(" "):
        svg_path += " "
    svg_path = svg_path.replace(",", " ")

    path_splited = re.findall(r"([a-zA-Z])([ ,\-\+.\d]+)", svg_path)

    parsed_path = []
    for path_command in path_splited:
        if cmd_class_info := svg_path_handlers.get(path_command[0]):
            cmd_class, cmd_nb_arguments = cmd_class_info
            arguments = path_command[1].strip().split(" ")
            # if multiple (x y) in a command
            # Create instances using dataclass fields

            field_names = [f.name for f in fields(cmd_class)]
            # Safe argument extraction with bounds checking
            for i in range(0, len(arguments), cmd_nb_arguments or 1):
                arg_slice = arguments[i : i + cmd_nb_arguments]
                if len(arg_slice) >= cmd_nb_arguments:
                    try:
                        parsed_path.append(
                            cmd_class(**dict(zip(field_names, arg_slice)))
                        )
                    except (ValueError, TypeError) as e:
                        logging.warning(
                            f"Failed to create SVG path element {cmd_class.__name__}: {e}"
                        )
                else:
                    logging.warning(
                        f"Insufficient arguments for SVG command {cmd_class.__name__}, expected {cmd_nb_arguments}, got {len(arg_slice)}"
                    )
                    break
        else:
            logging.warning("SVG command path not supported")

    return parsed_path


if __name__ == "__main__":
    path_1 = "M 400.067 299.929 A 4 3.9 0 1 1 408.032 299.934 L 5 6 5 7 Z"
    path_0 = "M 5 -6 L -5 0 L 5 6 Z"
    path_2 = "M -5 3 L -2 0 L -5 -3"

    print(parse_svg_path(svg_path=path_0))

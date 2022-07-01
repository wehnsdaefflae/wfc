# coding=utf-8
import itertools
import random

from PIL import Image


COLOR = tuple[int, int, int]
COORDS = tuple[int, int]

FREQUENCY_TABLE = dict[COLOR, int]
COLOR_TABLE = dict[COLOR, dict[COORDS, dict[COLOR, int]]]
EVIDENCE_TABLE = dict[COORDS, FREQUENCY_TABLE]

NEIGHBORS = tuple[COORDS, ...]


def get_tables(image: Image, neighbors: NEIGHBORS) -> tuple[FREQUENCY_TABLE, COLOR_TABLE]:
    frequency_table: FREQUENCY_TABLE = dict()
    full_table: COLOR_TABLE = dict()

    for coords in itertools.product(range(image.width), range(image.height)):
        color = image.getpixel(coords)
        frequency_table[color] = frequency_table.get(color, 0) + 1

        color_neighbors_dict = full_table.get(color)
        if color_neighbors_dict is None:
            color_neighbors_dict = dict()
            full_table[color] = color_neighbors_dict

        x, y = coords
        for each_neighbor in neighbors:
            neighbor_dict = color_neighbors_dict.get(each_neighbor)
            if neighbor_dict is None:
                neighbor_dict = dict()
                color_neighbors_dict[each_neighbor] = neighbor_dict

            each_x = x + each_neighbor[0]
            each_y = y + each_neighbor[1]

            if each_x < 0 or each_x >= image.width or each_y < 0 or each_y >= image.height:
                continue

            neighbor_color = image.getpixel((each_x, each_y))
            neighbor_dict[neighbor_color] = neighbor_dict.get(neighbor_color, 0) + 1

    return frequency_table, full_table


def collapse_pixel(coords: COORDS, table: EVIDENCE_TABLE) -> COLOR:
    frequency_table = table[coords]

    colors, frequencies = zip(*frequency_table.items())
    target_color, = random.choices(colors, weights=frequencies, k=1)

    # target_color, _ = max(frequency_table.items(), key=lambda x: x[1])

    table[coords] = {target_color: 1}

    return target_color


def update_evidence_table(coords: COORDS, evidence_table: EVIDENCE_TABLE, color_table: COLOR_TABLE, width: int, height: int):
    x, y = coords
    color = collapse_pixel((x, y), evidence_table)
    color_neighbors = color_table[color]

    for each_neighbor, each_colors in color_neighbors.items():
        neighbor_coords = x + each_neighbor[0], y + each_neighbor[1]
        if neighbor_coords[0] < 0 or neighbor_coords[0] >= width or neighbor_coords[1] < 0 or neighbor_coords[1] >= height:
            continue

        color_evidence = evidence_table.get(neighbor_coords)
        if len(each_colors) < 1 or (color_evidence is not None and len(color_evidence) < 2):
            continue

        if color_evidence is None:
            evidence_table[neighbor_coords] = dict(each_colors)

        else:
            for _color, _frequency in each_colors.items():
                color_evidence[_color] = color_evidence.get(_color, 0) + _frequency


def image_from_matrix(evidence_table: EVIDENCE_TABLE, width: int, height: int) -> Image:
    image = Image.new("RGB", (width, height))
    for coords, colors in evidence_table.items():
        assert len(colors) == 1
        color, = colors.keys()
        image.putpixel(coords, color)
    return image


def get_best_coords(evidence_table: EVIDENCE_TABLE) -> COORDS | None:
    selection = tuple(x for x in evidence_table.items() if len(x[1]) >= 2)
    if len(selection) < 1:
        return None
    coords, _ = max(selection, key=lambda x: sum(x[1].values()))
    return coords


def generate_image(frequency_table: FREQUENCY_TABLE, color_table: COLOR_TABLE, width: int, height: int) -> Image:
    colors, frequencies = zip(*frequency_table.items())
    target_color, = random.choices(colors, weights=frequencies, k=1)

    evidence_table = {(0, 0): {target_color: 1}}
    coords = (0, 0)

    while coords is not None:
        update_evidence_table(coords, evidence_table, color_table, width, height)
        coords = get_best_coords(evidence_table)

    return image_from_matrix(evidence_table, width, height)


def main():
    file_path = "samples/Skyline.png"
    image = Image.open(file_path)
    # neighbors = (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)
    neighbors = (1, 0), (0, -1), (-1, 0), (0, 1)

    frequency_table, full_table = get_tables(image, neighbors)

    generated = generate_image(frequency_table, full_table, image.width, image.height)

    image.show()
    generated.show()


if __name__ == "__main__":
    main()

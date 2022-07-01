# coding=utf-8
import itertools
import random

from PIL import Image


COLOR = tuple[int, int, int]
COORDS = tuple[int, int]
CONSTRAINTS = dict[COORDS, set[COLOR]]

CONSTRAINT_TABLE = dict[COLOR, CONSTRAINTS]
SUPER_POSITION = dict[COORDS, set[COLOR]]

NEIGHBORS = tuple[tuple[int, int], ...]


def get_constraints(image: Image, neighbors: tuple) -> tuple[CONSTRAINT_TABLE, set[COLOR]]:
    table = dict()
    colors = set()
    for x, y in itertools.product(range(image.width), range(image.height)):
        color = image.getpixel((x, y))
        colors.add(color)

        adjacent_colors = table.get(color)
        if adjacent_colors is None:
            adjacent_colors = dict()
            table[color] = adjacent_colors

        for each_neighbor in neighbors:
            superposition = adjacent_colors.get(each_neighbor)
            if superposition is None:
                superposition = set()
                adjacent_colors[each_neighbor] = superposition

            neighbor_x, neighbor_y = x + each_neighbor[0],  y + each_neighbor[1]
            if neighbor_x < 0 or neighbor_x >= image.width or neighbor_y < 0 or neighbor_y >= image.height:
                continue

            neighbor_color = image.getpixel((neighbor_x, neighbor_y))
            superposition.add(neighbor_color)

    return table, colors


def collapse(super_position: SUPER_POSITION, constraints: CONSTRAINT_TABLE, neighbors: NEIGHBORS, width: int, height: int):
    min_choices = -1
    min_coords = set()

    for coords, colors in super_position.items():
        no_colors = len(colors)
        if no_colors < min_choices or min_choices == -1:
            min_choices = len(colors)
            min_coords.clear()
            min_coords.add((coords, tuple(colors)))

        elif no_colors == min_choices:
            min_coords.add((coords, tuple(colors)))

    selected_coords, selected_colors = random.choice(list(min_coords))
    final_color = random.choice(selected_colors)
    super_position[selected_coords] = {final_color}

    stack = {selected_coords: selected_colors}
    while len(stack) >= 1:
        coords = list(stack.keys())[0]
        cols = stack.pop(coords)
        for x_relative, y_relative in neighbors:
            x_total, y_total = coords[0] + x_relative, coords[1] + y_relative
            if x_total < 0 or x_total >= width or y_total < 0 or y_total >= height:
                continue
            neighbor_cols = super_position.get((x_total, y_total))
            if len(neighbor_cols) < 2:
                continue

            allowed = {x for each_color in cols for x in constraints[each_color][(x_relative, y_relative)]}
            effective = neighbor_cols & allowed
            neighbor_cols.clear()
            neighbor_cols.update(effective)
            stack[(x_total, y_total)] = neighbor_cols

    return selected_coords


def generate_image(super_position: SUPER_POSITION, width: int, height: int) -> Image:
    image = Image.new("RGB", (width, height))
    for coords, colors in super_position.items():
        assert len(colors) == 1
        color, = colors
        image.putpixel(coords, color)
    return image


def main():
    file_path = "samples/Skyline.png"
    image = Image.open(file_path)
    # neighbors = (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)
    neighbors = (1, 0), (0, -1), (-1, 0), (0, 1)

    table, colors = get_constraints(image, neighbors)

    super_position = {coords: set(colors) for coords in itertools.product(range(image.width), range(image.height))}

    collapse(super_position, table, neighbors, image.width, image.height)

    generated = generate_image(super_position, image.width, image.height)

    image.show()
    generated.show()


if __name__ == "__main__":
    main()

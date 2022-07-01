# coding=utf-8
import itertools
import random
from collections import Counter
from typing import Sequence, Collection, Any, Callable

from PIL import Image


COORDINATES = tuple[int, int]
COLOR = tuple[int, int, int]


class Tile:
    def __init__(self, array: tuple[COLOR, ...]):
        self.array = array

    def __hash__(self) -> int:
        return hash(self.array)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Tile):
            return False
        if other is self:
            return True
        return other.array == self.array


TILING = dict[COORDINATES, Tile]


def tile_image(image: Image, tile_size: int) -> TILING:
    width = image.width
    height = image.height

    assert width % tile_size == 0, "wrong width"
    assert height % tile_size == 0, "wrong height"

    horizontal_tiles = width // tile_size
    vertical_tiles = height // tile_size

    tiling = dict()
    for xt, yt in itertools.product(range(horizontal_tiles), range(vertical_tiles)):
        x_offset, y_offset = xt * tile_size, yt * tile_size
        array = tuple(image.getpixel((x_offset + x, y_offset + y)) for x, y in itertools.product(range(tile_size), range(tile_size)))
        tiling[(xt, yt)] = Tile(array)

    return tiling


FREQUENCIES = Counter[Tile, int]
SUPERPOSITION = dict[COORDINATES, FREQUENCIES]
CONSTRAINTS = dict[tuple[Tile, COORDINATES], FREQUENCIES]


def get_constraints(tiling: TILING, neighborhood: Collection[COORDINATES], width: int, height: int) -> CONSTRAINTS:
    constraints = dict()

    for x, y in itertools.product(range(width), range(height)):
        each_tile = tiling.get((x, y))
        for each_neighbor in neighborhood:
            x_offset, y_offset = each_neighbor
            x_total, y_total = x + x_offset, y + y_offset
            if width > x_total >= 0 and height > y_total >= 0:
                adjacent_tile = tiling.get((x_total, y_total))
                possibilities = constraints.get((each_tile, each_neighbor))
                if possibilities is None:
                    possibilities = Counter({adjacent_tile: 1})
                    constraints[(each_tile, each_neighbor)] = possibilities
                else:
                    possibilities[adjacent_tile] = possibilities.get(adjacent_tile, 0) + 1

    return constraints


def get_superposition(frequencies: Counter[Tile, int], width: int, height: int) -> SUPERPOSITION:
    return {(x, y): frequencies.copy() for x, y in itertools.product(range(width), range(height))}


def get_lowest_entropy(superposition: SUPERPOSITION) -> COORDINATES | None:
    max_options = max(len(each_frequency) for each_frequency in superposition.values())
    if max_options < 2:
        return None

    max_concentration = -1.
    coordinates = set()

    for each_coordinate, each_frequency in superposition.items():
        if len(each_frequency) < 2:
            continue

        each_concentration = len(each_frequency.values())
        if max_concentration < 0. or max_concentration < each_concentration:
            coordinates.clear()
            coordinates.add(each_coordinate)
            max_concentration = each_concentration

        elif each_concentration == max_concentration:
            coordinates.add(each_coordinate)

    return random.choice(list(coordinates))


def collapse(coordinates: COORDINATES, superposition: SUPERPOSITION):
    possibilities = superposition.get(coordinates)
    population, weights = tuple(zip(*possibilities.items()))
    observation, = random.choices(population, weights=weights, k=1)
    possibilities.clear()
    possibilities[observation] = 1


class Contradiction(ValueError):
    pass


NEIGHBORHOOD = Collection[COORDINATES]


def flood_fill(coordinates: COORDINATES, neighborhood: NEIGHBORHOOD, width: int, height: int, f: Callable[[COORDINATES], None]):
    processed = set()
    stack = [coordinates]
    while 0 < len(stack):
        x, y = each_coordinates = stack.pop()
        f(each_coordinates)
        processed.add(each_coordinates)
        for delta_x, delta_y in neighborhood:
            x_offset, y_offset = each_neighbor = x + delta_x, y + delta_y
            if width > x_offset >= 0 and height > y_offset >= 0 and each_neighbor not in processed:
                stack.append(each_neighbor)


def propagate(coordinates: COORDINATES, superposition: SUPERPOSITION, constraints: CONSTRAINTS, neighbors: Collection[COORDINATES], width: int, height: int):
    frequencies = superposition.get(coordinates)
    tiles = frequencies.keys()
    x, y = coordinates
    for delta_x, delta_y in neighbors:
        x_offset, y_offset = each_neighbor = x + delta_x, y + delta_y
        if not (width > x_offset >= 0 and height > y_offset >= 0):
            continue

        neighbor_frequencies = superposition.get(each_neighbor)

        allowed = Counter()
        for each_tile in tiles:
            each_constraint = constraints.get((each_tile, (delta_x, delta_y)))
            if each_constraint is None:
                continue
            allowed += each_constraint

        # allowed = sum((constraints.get((each_tile, (delta_x, delta_y))) for each_tile in tiles), Counter())
        to_delete = set()
        for each_tile in neighbor_frequencies:
            if each_tile not in allowed:
                to_delete.add(each_tile)

        for each_tile in to_delete:
            if len(neighbor_frequencies) >= 2:
                neighbor_frequencies.pop(each_tile)


def get_image(superposition: SUPERPOSITION, tile_size: int, width: int, height: int) -> Image:
    image = Image.new("RGB", (width * tile_size, height * tile_size))
    for x, y in itertools.product(range(width), range(height)):
        try:
            tile, = superposition.get((x, y))
        except ValueError:
            raise Contradiction(f"position {str((x, y)):s} is empty")

        for i, pixel in enumerate(tile.array):
            delta_x, delta_y = i // tile_size, i % tile_size
            coordinates = x * tile_size + delta_x, y * tile_size + delta_y
            image.putpixel(coordinates, pixel)
    return image


def get_total_frequencies(input_tiles: TILING) -> Counter[Tile, int]:
    tile_frequencies = Counter()
    for each_tile in input_tiles.values():
        tile_frequencies[each_tile] = tile_frequencies.get(each_tile, 0) + 1
    return tile_frequencies


def generate_image(input_image: Image, tile_size: int, neighborhood: Sequence[tuple[int, int]]) -> Image:
    horizontal_tiles = input_image.width // tile_size
    vertical_tiles = input_image.height // tile_size

    input_tiles = tile_image(input_image.convert("RGB"), tile_size)
    constraints = get_constraints(input_tiles, neighborhood, horizontal_tiles, vertical_tiles)
    tile_frequencies = get_total_frequencies(input_tiles)
    superposition = get_superposition(tile_frequencies, horizontal_tiles, vertical_tiles)

    iterations = 0
    while (coordinates := get_lowest_entropy(superposition)) is not None:
        collapse(coordinates, superposition)
        flood_fill(coordinates, neighborhood, horizontal_tiles, vertical_tiles, lambda x: propagate(x, superposition, constraints, neighborhood, horizontal_tiles, vertical_tiles))
        iterations += 1
        print(iterations)

    return get_image(superposition, tile_size, horizontal_tiles, vertical_tiles)


def main():
    file_path = "samples/Platformer.png"
    tile_size = 2
    neighborhood = (0, -1), (0, 1), (-1, 0), (1, 0)

    input_image = Image.open(file_path)

    assert input_image.width % tile_size == 0, f"width of {input_image.width:d} not divisible by {tile_size:d}."
    assert input_image.height % tile_size == 0, f"height of {input_image.height:d} not divisible by {tile_size:d}."

    output_image = generate_image(input_image, tile_size, neighborhood)

    output_image.show()


if __name__ == "__main__":
    main()

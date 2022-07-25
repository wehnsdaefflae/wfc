# coding=utf-8

import pyglet
from pyglet import shapes


class Canvas(pyglet.window.Window):
    def __init__(self, map_width: int, map_height: int, *args, updates_per_second: int = 10, **kwargs):
        # super().__init__(*args, config=pyglet.gl.Config(sample_buffers=1, samples=4), **kwargs)
        super().__init__(*args, **kwargs)
        self.map_width = map_width
        self.map_height = map_height
        if self.map_height < self.map_width:
            self.small_edge = self.map_height
            self.large_edge = self.map_width
        else:
            self.small_edge = self.map_width
            self.large_edge = self.map_height

        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.edge = .2
        self.pixel_gap = 1

        if updates_per_second >= 1:
            pyglet.clock.schedule_interval(self.update, 1. / updates_per_second)

    def update(self, dt: float) -> None:
        if self.has_exit:
            pyglet.app.exit()

        self._update(dt)

    def on_draw(self) -> None:
        self._on_draw()

    def _update(self, dt: float) -> None:
        return
        raise NotImplementedError()

    def _relative_coords_to_absolute(self, x: float, y: float, fixed_ratio: bool = False) -> tuple[int, int]:
        x_factor, y_factor = self.get_viewport_size()
        if fixed_ratio:
            if x_factor < y_factor:
                y_factor = x_factor
            elif y_factor < x_factor:
                x_factor = y_factor
        return int(x * x_factor), int(y * y_factor)

    def _on_draw(self) -> None:
        rectangles = set()
        batch = pyglet.graphics.Batch()

        for _x in range(self.map_width):
            x = self.edge + (_x * (1. - 2. * self.edge)) / self.large_edge

            for _y in range(self.map_height):
                y = self.edge + (_y * (1. - 2. * self.edge)) / self.large_edge

                position = self._relative_coords_to_absolute(x, y, fixed_ratio=True)

                relative_size = (1. - 2. * self.edge) / self.large_edge
                size = self._relative_coords_to_absolute(relative_size, relative_size, fixed_ratio=True)

                rectangle = shapes.Rectangle(*(position[0] + self.pixel_gap, position[1] + self.pixel_gap), *(size[0] - self.pixel_gap, size[1] - self.pixel_gap),
                                             color=(255, 22, 20), batch=batch)
                rectangles.add(rectangle)

                # rectangle.opacity = 128
                # rectangle.rotation = 33

        self.clear()
        batch.draw()

    def run(self) -> None:
        pyglet.app.run()


if __name__ == "__main__":
    c = Canvas(100, 100, 1280, 720, resizable=True)
    c.run()

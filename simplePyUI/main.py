import abc
import ctypes
import enum

import sdl2
import sdl2.ext
import sdl2.sdlttf

from . import abstarct_classes

class TEXT_ALIGN(enum.IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2

class Render:

    def __init__(self, sdl_window, start_ui_node, font_path):

        self.sdl_window = sdl_window
        self.start_ui_node = start_ui_node

        self.sprite_factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
        self.sprite_renderer = self.sprite_factory.create_sprite_render_system(
            sdl_window)
        self.font_manager = sdl2.ext.FontManager(font_path)

    def draw(self):

        self.sprites_to_render = list()
        self.start_ui_node.get_sprites(self, (0, 0))
        self.sprite_renderer.render(self.sprites_to_render)

    def click(self, pos_click):
        self.start_ui_node.handle_mouse_event(pos_click, (0, 0), "click_event")

    def hover(self, pos_mouse):
        nodes_with = list()
        self.start_ui_node.get_nodes_with(nodes_with, "hover")
        hovered_node = self.start_ui_node.get_hovered_node(pos_mouse, (0, 0))
        if hovered_node in nodes_with:
            nodes_with.remove(hovered_node)
            hovered_node.hover[0]()
        for node in nodes_with:
            node.hover[1]()


class UINode(metaclass=abc.ABCMeta):

    clickable = True  # Перехватывать события мыши

    def __init__(self, pos, size, nodes=None, **kwargs):
        self.pos = pos
        self.size = size

        self.nodes = nodes
        if not nodes:
            self.nodes = list()

        for key, val in kwargs.items():
            setattr(self, key, val)

    def get_sprites(self, render: Render, pos_off):

        pos_off = (self.pos[0] + pos_off[0], self.pos[1] + pos_off[1])

        render.sprites_to_render.extend(self.create_sprites(render, pos_off))

        for node in self.nodes:
            node.get_sprites(render, pos_off)

    @abc.abstractmethod
    def create_sprites(self, render: Render, pos):
        pass

    def handle_mouse_event(self, pos_mouse, pos_off, event):
        pos_off = (self.pos[0] + pos_off[0], self.pos[1] + pos_off[1])

        if not self.clickable:
            return False

        for node in reversed(self.nodes):
            if node.handle_mouse_event(pos_mouse, pos_off, event):
                return True

        if pos_off[0] < pos_mouse[0] and \
                pos_mouse[0] < pos_off[0] + self.size[0] and \
                pos_off[1] < pos_mouse[1] and \
                pos_mouse[1] < pos_off[1] + self.size[1]:
            has_event = hasattr(self, event)
            if has_event:  # ! СДЕЛАЙ КРАСИВО
                getattr(self, event)()
            return True
        return False

    def get_nodes_with(self, nodes_acc: list, event):
        if hasattr(self, event):
            nodes_acc.append(self)

        for node in reversed(self.nodes):
            node.get_nodes_with(nodes_acc, event)

    def get_hovered_node(self, pos_mouse, pos_off):
        pos_off = (self.pos[0] + pos_off[0], self.pos[1] + pos_off[1])

        if not self.clickable:
            return None

        for node in reversed(self.nodes):
            hovered_node = node.get_hovered_node(pos_mouse, pos_off)
            if hovered_node:
                return hovered_node

        if pos_off[0] < pos_mouse[0] and \
                pos_mouse[0] < pos_off[0] + self.size[0] and \
                pos_off[1] < pos_mouse[1] and \
                pos_mouse[1] < pos_off[1] + self.size[1]:
            return self
        return None


class UIPanel(UINode):
    """kwargs = {
        "color": (r, g, b, a)
    }"""
    color = tuple()

    def create_sprites(self, render: Render, pos_off=(0, 0)):

        sprite = render.sprite_factory.create_software_sprite(self.size)
        sdl2.ext.fill(sprite, self.color)
        sprite.position = pos_off
        return [sprite]


class UIText(UINode):
    """kwargs = {
        "text" : str()
        "color": (r, g, b, a)
        "text_align": TEXT_ALIGN
    }"""
    text = str()
    color = tuple()
    text_align = TEXT_ALIGN.LEFT

    clickable = False

    def create_sprites(self, render: Render, pos_off=(0, 0)):


        text = render.font_manager.render(self.text, color=self.color)
        sprite = render.sprite_factory.from_surface(text)

        if self.text_align == TEXT_ALIGN.CENTER:
            pos_off = ( pos_off[0] + self.size[0] // 2 - text.w // 2, pos_off[1])

        sprite.position = pos_off
        return [sprite]


class UIFactory(abstarct_classes.AbstarctUIFactory):

    def Panel(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
        "color": (r, g, b, a)
        }"""
        return UIPanel(pos, size, nodes, **kwargs)

    def Text(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
        "text" : str()
        "color": (r, g, b, a)
        }"""
        return UIText(pos, size, nodes, **kwargs)


class SimpleUI:

    def __init__(self, win_name, win_size, ui_three_configure, font_path):
        sdl2.ext.init()
        sdl2.sdlttf.TTF_Init()

        self.sdl_window = sdl2.ext.Window(win_name, win_size)
        self.sdl_window.show()

        start_ui_node = ui_three_configure(UIFactory())

        self.render = Render(self.sdl_window, start_ui_node, font_path)

        self.running = True

    def run_loop(self):
        while self.running:
            self.render.draw()
            events = sdl2.ext.get_events()
            for event in events:
                if event.type == sdl2.SDL_QUIT:
                    self.running = False
                    break
                if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    x, y = ctypes.c_int(0), ctypes.c_int(0)
                    sdl2.mouse.SDL_GetMouseState(
                        ctypes.byref(x), ctypes.byref(y))
                    self.render.click((x.value, y.value))
                    break
                if event.type == sdl2.SDL_MOUSEMOTION:
                    x, y = ctypes.c_int(0), ctypes.c_int(0)
                    sdl2.mouse.SDL_GetMouseState(
                        ctypes.byref(x), ctypes.byref(y))
                    self.render.hover((x.value, y.value))
                    break
            self.sdl_window.refresh()

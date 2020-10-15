import abc
import ctypes
import enum
import time

import threading

import sdl2
import sdl2.ext
import sdl2.sdlttf

from . import abstarct_classes

TIME_TO_CLICK = 0.2


class ALIGN(enum.IntEnum):
    LEFT = 1
    HCENTER = 2
    RIGHT = 4
    TOP = 8
    BOTTOM = 16
    VCENTER = 32


class Render:

    def __init__(self, sdl_window, start_ui_node, font_path):

        self.sdl_window = sdl_window
        self.start_ui_node = start_ui_node

        self.sprite_factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
        self.sprite_renderer = self.sprite_factory.create_sprite_render_system(
            sdl_window)
        self.font_manager = sdl2.ext.FontManager(font_path)

        self.click_timer = float()
        self.selected_node = None
        self.last_mouse_pos = None

    def draw(self):
        self.sprites_to_render = list()
        self.start_ui_node.get_sprites(self, (0, 0))
        self.sprite_renderer.render(self.sprites_to_render)

    def mouse_down(self, pos_click):
        self.click_timer = time.time()
        self.last_mouse_pos = pos_click
        self.selected_node = self.start_ui_node.handle_mouse_event(
            pos_click, (0, 0), "mouse_down")

    def mouse_up(self, pos_click):
        self.selected_node = None
        if (time.time() - self.click_timer < TIME_TO_CLICK):
            self.start_ui_node.handle_mouse_event(
                pos_click, (0, 0), "mouse_click")
        self.click_timer = float()
        self.start_ui_node.handle_mouse_event(pos_click, (0, 0), "mouse_up")

    def mouse_hover(self, pos_mouse):
        nodes_with = list()
        self.start_ui_node.get_nodes_with(nodes_with, "hover")
        hovered_node = self.start_ui_node.get_hovered_node(pos_mouse, (0, 0))
        if hovered_node in nodes_with:
            nodes_with.remove(hovered_node)
            hovered_node.hover[0]()
        for node in nodes_with:
            node.hover[1]()

    def mouse_drag(self, pos_mouse):
            pos_mouse_dff = (pos_mouse[0] - self.last_mouse_pos[0] , pos_mouse[1] - self.last_mouse_pos[1])
            self.last_mouse_pos = pos_mouse
            getattr(self.selected_node, "mouse_drag", lambda x,_y: x)(pos_mouse, pos_mouse_dff)

    def _all_nodes_thrunking(self):
        res = list()
        res.extend(self.start_ui_node.nodes)
        for node in res:
            yield node
            res.extend(node.nodes)
        return res

    def get_node_by_name(self, name):
        for node in self._all_nodes_thrunking():
            s_id = getattr(node, "s_id", None)
            if s_id and s_id == name:
                return node

class UINode(metaclass=abc.ABCMeta):

    clickable = True  # Перехватывать события мыши
    align = ALIGN.LEFT | ALIGN.TOP

    def __init__(self, pos, size, nodes=None, **kwargs):
        self.pos = pos
        self.size = size

        self.nodes = nodes
        if nodes == None:
            self.nodes = list()

        for key, val in kwargs.items():
            setattr(self, key, val)

    def calc_pos(self, pos_off):
        return (self.pos[0] + pos_off[0], self.pos[1] + pos_off[1])

    def calc_next_node_pos(self, next_node, pos_off):

        if next_node.align & ALIGN.HCENTER:
            pos_off = (pos_off[0] + self.size[0] //
                       2 - next_node.size[0] // 2, pos_off[1])
        if next_node.align & ALIGN.VCENTER:
            pos_off = (pos_off[0], pos_off[1] +
                       self.size[1] // 2 - next_node.size[1] // 2)
        if next_node.align & ALIGN.RIGHT:
            pos_off = (pos_off[0] + self.size[0] -
                       next_node.size[0], pos_off[1])
        if next_node.align & ALIGN.BOTTOM:
            pos_off = (pos_off[0], pos_off[1] +
                       self.size[1] - next_node.size[1])

        return pos_off

    def get_sprites(self, render: Render, pos_off):
        pos_off = self.calc_pos(pos_off)
        render.sprites_to_render.extend(self.create_sprites(render, pos_off))
        for node in self.nodes:
            next_pos_off = self.calc_next_node_pos(node, pos_off)
            node.get_sprites(render, next_pos_off)

    @abc.abstractmethod
    def create_sprites(self, render: Render, pos):
        pass

    def handle_mouse_event(self, pos_mouse, pos_off, event, *args):
        if not self.clickable:
            return None

        pos_off = self.calc_pos(pos_off)
        for node in reversed(self.nodes):
            next_pos_off = self.calc_next_node_pos(node, pos_off)
            node = node.handle_mouse_event(pos_mouse, next_pos_off, event, *args)
            if node:
                return node

        if pos_off[0] < pos_mouse[0] and \
                pos_mouse[0] < pos_off[0] + self.size[0] and \
                pos_off[1] < pos_mouse[1] and \
                pos_mouse[1] < pos_off[1] + self.size[1]:
            if hasattr(self, event):
                getattr(self, event)(*args)

            return self
        return None

    def get_nodes_with(self, nodes_acc: list, event):
        if hasattr(self, event):
            nodes_acc.append(self)

        for node in reversed(self.nodes):
            node.get_nodes_with(nodes_acc, event)

    def get_hovered_node(self, pos_mouse, pos_off):
        if not self.clickable:
            return None

        pos_off = self.calc_pos(pos_off)
        for node in reversed(self.nodes):
            next_pos_off = self.calc_next_node_pos(node, pos_off)
            hovered_node = node.get_hovered_node(pos_mouse, next_pos_off)
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
        "id": str()
        "color": (r, g, b, a)
        "align": ALIGN
    }"""
    color = tuple()

    def create_sprites(self, render: Render, pos_off=(0, 0)):

        sprite = render.sprite_factory.create_software_sprite(self.size)
        sdl2.ext.fill(sprite, self.color)
        sprite.position = pos_off
        return [sprite]


class UIText(UINode):
    """kwargs = {
        "id": str()
        "text" : str()
        "color": (r, g, b, a)
        "align": ALIGN
        "text_align": ALIGN
        "text_size" : int()
    }"""
    text = str()
    color = tuple()
    text_align = ALIGN.VCENTER | ALIGN.HCENTER
    text_size = 16

    clickable = False

    def create_sprites(self, render: Render, pos_off=(0, 0)):
        text = render.font_manager.render(self.text, color=self.color, size=self.text_size)
        sprite = render.sprite_factory.from_surface(text)

        if self.text_align & ALIGN.HCENTER:
            pos_off = (pos_off[0] + self.size[0] //
                       2 - text.w // 2, pos_off[1])
        if self.text_align & ALIGN.VCENTER:
            pos_off = (pos_off[0], pos_off[1] +
                       self.size[1] // 2 - text.h // 2)
        if self.text_align & ALIGN.RIGHT:
            pos_off = (pos_off[0] + self.size[0] - text.w, pos_off[1])
        if self.text_align & ALIGN.BOTTOM:
            pos_off = (pos_off[0], pos_off[1] + self.size[1] - text.h)
        sprite.position = pos_off
        return [sprite]


class UIFactory(abstarct_classes.AbstarctUIFactory):

    def __init__(self, sdl_window):
        self.sdl_window = sdl_window

    def Panel(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
        "s_id": str()
        "color": (r, g, b, a)
        "align": ALIGN
        }"""
        return UIPanel(pos, size, nodes, **kwargs)

    def Text(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
        "s_id": str()
        "text" : str()
        "color": (r, g, b, a)
        "align": ALIGN
        }"""
        return UIText(pos, size, nodes, **kwargs)


class SimpleUI:

    win_name = str()
    win_size = (0,0)
    ui_three_configure = callable
    font_path = str()
    running = False
    render = None

    def __init__(self, win_name, win_size, ui_three_configure, font_path):
        self.win_name = win_name
        self.win_size = win_size
        self.ui_three_configure = ui_three_configure
        self.font_path = font_path
        self.running = True

    def run_loop(self):
        t = threading.Thread(target=self._ui_loop)
        t.start()
        time.sleep(1)

    def _ui_loop(self):
        sdl2.ext.init()
        sdl2.sdlttf.TTF_Init()

        self.sdl_window = sdl2.ext.Window(self.win_name, self.win_size)
        self.sdl_window.show()

        self.start_ui_node = self.ui_three_configure(UIFactory(self.sdl_window))

        self.render = Render(self.sdl_window, self.start_ui_node, self.font_path)

        while self.running:
            self.render.draw()
            events = sdl2.ext.get_events()
            for event in events:
                if event.type == sdl2.SDL_QUIT:
                    self.running = False
                    break
                if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    self.render.mouse_down((event.button.x, event.button.y))
                    break
                if event.type == sdl2.SDL_MOUSEBUTTONUP:
                    self.render.mouse_up((event.button.x, event.button.y))
                    break
                if event.type == sdl2.SDL_MOUSEMOTION:
                    x, y = event.button.x, event.button.y
                    self.render.mouse_hover((x, y))
                    if (time.time() - self.render.click_timer > TIME_TO_CLICK and self.render.selected_node):
                        self.render.mouse_drag((x, y))
                    break
            self.sdl_window.refresh()

    def get_node_by_name(self, name):
        return self.render.get_node_by_name(name)
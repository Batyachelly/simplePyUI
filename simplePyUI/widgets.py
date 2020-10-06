import enum

from .main import UINode, UIPanel, UIText, Render, TEXT_ALIGN
from .abstarct_classes import AbstarctUIFactory


class STATE(enum.IntEnum):
    NONE = 0
    HOVER = 1
    PRESS = 2
    CHECK = 4


class UIWidgetsFactory:

    def __init__(self, ui_factory: AbstarctUIFactory):
        self.ui_factory = ui_factory

    class Button(UINode):

        ui_factory = AbstarctUIFactory
        text = str()
        color_text = tuple()
        color = tuple()
        color_hover = tuple()
        color_press = tuple()
        click_event = callable
        mouse_up = callable
        mouse_down = callable
        status = STATE.NONE
        text_align = TEXT_ALIGN.VCENTER | TEXT_ALIGN.HCENTER

        def __init__(self, pos, size, nodes,  **kwargs):
            super().__init__(pos, size, nodes, **kwargs)

            panel: UIPanel = self.ui_factory.Panel(
                (0, 0), self.size, [], color=self.color)
            text: UIText = self.ui_factory.Text((0, 0), self.size, [
            ], color=self.color_text, text=self.text, text_align=self.text_align)

            def mouse_down():
                self.status = self.status | STATE.PRESS
                panel.color = self.color_press
                self.click_event()

            def mouse_up():
                self.status = self.status & ~ STATE.PRESS
                panel.color = self.color_hover
                # self.click_event()

            panel.mouse_down = mouse_down
            panel.mouse_up = mouse_up

            def click():
                self.click_event()
            panel.click_event = click

            def mouse_in():
                if not self.status & STATE.PRESS:
                    panel.color = self.color_hover

            def mouse_out():
                self.status = self.status & ~ STATE.PRESS
                panel.color = self.color
            panel.hover = (mouse_in, mouse_out)

            self.nodes = [panel, text]

        def create_sprites(self, render: Render, pos_off=(0, 0)):
            sprites = list()
            for node in self.nodes:
                sprites.extend(node.create_sprites(render, pos_off))
            return sprites

    class ElementsList(UINode):

        ui_factory = AbstarctUIFactory
        color = tuple()
        force_element_height = int()

        def __init__(self, pos, size, nodes,  **kwargs):
            super().__init__(pos, size, nodes, **kwargs)
            panel: UIPanel = self.ui_factory.Panel(
                (0, 0), self.size, [], color=self.color)
            self.nodes.insert(0, panel)
            self.update_list()

        def update_list(self):
            x_off = y_off = 0
            for node in self.nodes[1:]:
                node.pos = (x_off, y_off)
                y_off += node.size[1]

        def add_elem(self, node, pos=-1):
            if pos == -1:
                self.nodes.append(node)
            else:
                self.nodes.insert(pos+1, node)

        def rem_elem(self, pos):
            del self.nodes[pos + 1]

        def get_elems(self):
            return self.nodes[1:]

        def create_sprites(self, render: Render, pos_off=(0, 0)):
            sprites = list()
            for node in self.nodes:
                sprites.extend(node.create_sprites(render, pos_off))
            return sprites

    def button(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
            "s_id": str()
            "text" : str()
            "color_text": (r, g, b, a)
            "color": (r, g, b, a)
            "color_hover": (r, g, b, a)
            "color_press": (r, g, b, a)
            "click_event" : fun()
        }"""
        return self.Button(pos, size, None, ui_factory=self.ui_factory, **kwargs)

    def elements_list(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
            "s_id": str()
            "color": (r, g, b, a)
        }"""
        return self.ElementsList(pos, size, nodes, ui_factory=self.ui_factory, **kwargs)

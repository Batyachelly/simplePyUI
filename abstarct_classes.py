import abc


class AbstarctUIFactory(metaclass=abc.ABCMeta):

    @abc.abstractclassmethod
    def Panel(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
        "color": (r, g, b, a)
        }"""
        pass

    @abc.abstractclassmethod
    def Text(self, pos, size, nodes=None, **kwargs):
        """kwargs = {
        "text" : str()
        "color": (r, g, b, a)
        }"""
        pass

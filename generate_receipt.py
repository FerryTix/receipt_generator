import qrcode
import yaml
from PIL import Image, ImageDraw, ImageFont
from timeit import timeit


class Receipt:
    def __init__(self):
        self.width = 384
        self.height = 0
        self.elements = []
        self.font_name = "Oxygen-Sans"
        self.mono_font_name = "Oxygen Mono"
        self.y = 0
        # self.font_name = "/home/elsholz/.fonts/comic-sans-ms/COMIC.TTF"

    def add_element(self, element):
        self.elements.append(element)
        self.height += element.height

    def render(self):
        i = Image.new(mode='L', size=(self.width, self.height), color=255)
        self.y = 0
        for element in self.elements:
            i, self.y = element.render(i, y=self.y)
        return i

    @staticmethod
    def from_stream(stream):
        root = yaml.safe_load(stream)
        rec = Receipt()

        for element in root:
            element_type, element_value = list(element.items())[0]
            print(element_type, element_value)
            rec.add_element(
                {
                    'title': TitleElement,
                    'margin': MarginElement,
                    'subtitle': SubtitleElement,
                    'qrcode': QRCodeElement,
                    'table': TableElement,
                }[element_type](element_value, **element)
            )
        return rec.render()


class StyleElement(Receipt):
    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__.update(kwargs)

    def render(self, i, y: int):
        return i, y


class MarginElement(StyleElement):
    def __init__(self, height=None, **kwargs):
        super().__init__(**kwargs)
        self.height = height
        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        if kwargs.get('hbar', False):
            self.c = ImageDraw.ImageDraw(self.i)
            self.c.line(((0, self.height // 2), (self.width, self.height // 2)), fill=0, width=1)

    def render(self, i, y: int):
        i.paste(self.i, (0, y))
        return i, y + self.height


class QRCodeElement(StyleElement):
    def __init__(self, text=None, width=50, center=True, **kwargs):
        super().__init__(**kwargs)
        self.i = qrcode.make(text)
        self.i = self.i.resize(size=(self.width * width // 100, self.width * width // 100))
        self.height = self.i.height
        self.center = center

    def render(self, i: Image, y: int):
        i.paste(self.i, (abs(self.i.height - self.width) // 2 if self.center else 0, y))

        return i, y + self.i.height


class SubtitleElement(StyleElement):
    def __init__(self, text=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 25
        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        self.f = ImageFont.truetype(font=self.font_name, size=18)
        text_size = self.c.textsize(text=text, font=self.f)
        self.c.text(xy=(abs(text_size[0] - self.width) // 2, 0), text=text, font=self.f)

    def render(self, i: Image, y: int):
        i.paste(self.i, (0, y))
        return i, y + self.i.height


class TitleElement(StyleElement):
    def __init__(self, text=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 40
        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        self.f = ImageFont.truetype(font=self.font_name, size=28)
        text_size = self.c.textsize(text=text, font=self.f)
        self.c.text(xy=(abs(text_size[0] - self.width) // 2, 0), text=text, font=self.f)

    def render(self, i: Image, y: int):
        i.paste(self.i, (0, y))
        return i, y + self.i.height


class TableElement(StyleElement):
    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.columns = data['columns']
        self.values = data['values']

    def render(self, i, y: int):
        return i, y


def main():
    Receipt.from_stream(open('receipt.yaml')).show()


if __name__ == '__main__':
    main()

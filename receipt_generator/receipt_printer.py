import qrcode
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from escpos.printer import Usb


class ReceiptPrinter:
    def __init__(self, id_vendor=0x0416, id_product=0x5011, in_ep=0x81, out_ep=0x03):
        self._printer = Usb(id_vendor, id_product, in_ep=in_ep, out_ep=out_ep)

    def print(self, img):
        self._printer.image(img)
        self._printer.cut()

    def print_data(self, data):
        img = Receipt.from_data(data)
        self.print(img)

    def print_stream(self, stream):
        img = Receipt.from_stream(stream)
        self.print(img)


class Receipt:
    def __init__(self):
        self.width = 384
        self.height = 0
        self.elements = []
        self.font_name = "Oxygen-Sans"
        self.font_name_bold = "Oxygen-Sans-Bold"
        self.mono_font_name = "Oxygen Mono"
        self.y = 0

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
    def from_data(data):
        rec = Receipt()
        for element in data:
            element_type, element_value = list(element.items())[0]
            print(element_type, element_value)
            rec.add_element(
                {
                    'title': TitleElement,
                    'margin': MarginElement,
                    'subtitle': SubtitleElement,
                    'qrcode': QRCodeElement,
                    'table': TableElement,
                    'picture': PictureElement,
                    'tickets': TicketsElement,
                }[element_type](element_value, **element)
            )
        return rec.render()

    @staticmethod
    def from_stream(stream):
        root = yaml.safe_load(stream)
        return Receipt.from_data(root)


class StyleElement(Receipt):
    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__.update(kwargs)

    def render(self, i, y: int):
        i.paste(self.i, (0, y))
        return i, y + self.i.height


class MarginElement(StyleElement):
    def __init__(self, height=None, **kwargs):
        super().__init__(**kwargs)
        hbar_width = kwargs.get('hbar', False)
        fill = kwargs.get('fill', 0)
        self.height = height
        if hbar_width and hbar_width is not True:
            if int(hbar_width) > height:
                self.height = int(hbar_width)
        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        if hbar_width:
            self.c.line(
                ((0, self.height // 2 - 0.5), (self.width, self.height // 2 + 0.5)),
                fill=fill,
                width=1 if hbar_width is True else int(hbar_width)
            )


class QRCodeElement(StyleElement):
    def __init__(self, text=None, width=100, center=True, **kwargs):
        super().__init__(**kwargs)
        self.i = qrcode.make(text, border=4)
        self.i = self.i.resize(size=(self.width * width // 100, self.width * width // 100))
        self.height = self.i.height
        self.center = center

    def render(self, i: Image, y: int):
        i.paste(self.i, (abs(self.i.height - self.width) // 2 if self.center else 0, y))
        return i, y + self.i.height


class SubtitleElement(StyleElement):
    def __init__(self, text=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 35
        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        self.f = ImageFont.truetype(font=self.font_name_bold, size=28)
        text_size = self.c.textsize(text=text, font=self.f)
        self.c.text(xy=(abs(text_size[0] - self.width) // 2, 0), text=text, font=self.f)


class TitleElement(StyleElement):
    def __init__(self, text=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 50
        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        self.f = ImageFont.truetype(font=self.font_name_bold, size=36)
        text_size = self.c.textsize(text=text, font=self.f)
        self.c.text(xy=(abs(text_size[0] - self.width) // 2, 0), text=text, font=self.f)


class TableElement(StyleElement):
    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.columns = data['columns']
        self.values = data['values']

        self.height = (len(self.values) + 2) * 25

        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        self.f = ImageFont.truetype(font=self.font_name, size=21)

        # calculate breadths of text. Height is 25.
        col_widths = [self.c.textsize(text=col, font=self.f)[0] for col in self.columns]
        xs = [0]

        spacing = (self.width - sum(col_widths)) / (len(self.columns) - 1)
        print(spacing, col_widths)
        print(self.width, sum(col_widths))

        # calculate x positions for even distribution of column titles
        for x in range(len(self.columns) - 1):
            xs.append(xs[x] + col_widths[x] + spacing)

        # positions for vertical separation lines
        separator_xs = [x - spacing / 2 for x in xs[1:]]

        for x, width, col in zip(xs, col_widths, self.columns):
            self.c.text(xy=(x, 0), text=col, font=self.f)

        for sep_line_x in separator_xs:
            self.c.line(((sep_line_x, 0), (sep_line_x, self.height)), fill=0, width=2)

        # horizontal separation line
        self.c.line(((0, 27), (self.width, 27)), fill=0, width=2)


class TicketsElement(StyleElement):
    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.return_trip = data['return']
        self.values = data['positions']
        self.sum = data['sum']

        self.height = 38 + len(self.values) * (27 * 2) + (7 * len(self.values) - 1) + 40

        self.i = Image.new(mode="L", size=(self.width, self.height), color=255)
        self.c = ImageDraw.ImageDraw(self.i)
        self.f = ImageFont.truetype(font=self.font_name, size=21)
        self.b = ImageFont.truetype(font=self.font_name_bold, size=25)

        y = 0
        self.c.text(xy=(0, y), text='Tickets', font=self.b)
        self.c.text(
            xy=(self.width - self.c.textsize(text='inkl. Rückfahrt', font=self.b)[0], y),
            text='inkl. Rückfahrt', font=self.b
        )
        y += 33
        self.c.line(((0, y), (self.width, y)), fill=0, width=2)
        y += 4
        self.c.line(((0, y), (self.width, y)), fill=0, width=2)
        y = 38
        for ind, position in enumerate(self.values):
            self.c.text(xy=(0, y), text=position['title'], font=self.f)
            text = str(position['count']) + ' × ' + position['single_fare']
            self.c.text(
                xy=(self.width - self.c.textsize(text=text, font=self.f)[0], y),
                text=text, font=self.f
            )
            y += 27

            self.c.text(xy=(0, y), text=position['subtitle'], font=self.f)
            text = 'Summe: ' + position['sum']
            self.c.text(
                xy=(self.width - self.c.textsize(text=text, font=self.f)[0], y),
                text=text, font=self.f
            )
            y += 27

            if ind < len(self.values) - 1:
                self.c.line(((0, y), (self.width, y)), fill=0, width=2)
                y += 7
        y += 3
        self.c.line(((0, y), (self.width, y)), fill=0, width=2)
        y += 4
        self.c.line(((0, y), (self.width, y)), fill=0, width=2)
        y += 5
        text = 'Summe: ' + self.sum
        self.c.text(
            xy=(self.width - self.c.textsize(text=text, font=self.b)[0], y),
            text=text, font=self.b
        )


class PictureElement(StyleElement):
    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        fp = data['file_path']

        self.i = Image.open(fp)
        enhancer = ImageEnhance.Brightness(self.i)
        self.i = enhancer.enhance(2.)
        self.i = self.i.resize(size=(self.width, int((self.width / self.i.width) * self.i.height)))
        self.height = self.i.height


def main():
    ReceiptPrinter().print_stream(open('receipt.yaml').read())


if __name__ == '__main__':
    main()

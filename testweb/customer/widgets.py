# customer/widgets.py
from django.forms.widgets import RadioSelect

class TileRadioSelect(RadioSelect):
    template_name = "widgets/tile_radio.html"
    option_template_name = "widgets/tile_radio_option.html"

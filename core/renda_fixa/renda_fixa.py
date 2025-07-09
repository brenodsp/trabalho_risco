from datetime import date

from pandas import DataFrame

from core.carteira import Carteira
from inputs.data_handler import InputsDataHandler


class RendaFixa:
    def __init__(self, data_referencia: date, vencimento: date, inputs_data_handler: InputsDataHandler):
        self.data_referencia = data_referencia
        self.vencimento = vencimento
        self.inputs_data_handler = inputs_data_handler

    

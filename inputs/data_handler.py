from pandas import DataFrame, read_excel

from utils.enums import Indices
from utils.formatters import to_snake_case

class InputsDataHandler:
    _INPUTS_PATH = "dados\Dados trabalho 2025.xlsx"

    def feriados(self) -> DataFrame:
        df = read_excel(self._INPUTS_PATH, sheet_name="Feriados Brasil").dropna(subset="Feriado")
        df.columns = [to_snake_case(col) for col in df.columns]

        return df

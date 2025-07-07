from pandas import DataFrame, read_excel

class InputsDataHandler:
    _INPUTS_PATH = "dados\Dados trabalho 2025.xlsx"

    def feriados(self) -> DataFrame:
        return read_excel(self._INPUTS_PATH, sheet_name="Feriados Brasil").dropna(subset="Feriado")
    

if __name__ == "__main__":
    data_handler = InputsDataHandler()
    feriados = data_handler.feriados()
    teste = 0

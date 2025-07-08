from pandas import DataFrame, read_excel

from utils.enums import Indices
from utils.formatters import to_snake_case


class InputsDataHandler:
    _INPUTS_PATH = "dados\Dados trabalho 2025.xlsx"

    def feriados(self) -> DataFrame:
        df = read_excel(self._INPUTS_PATH, sheet_name="Feriados Brasil").dropna(subset="Feriado")
        df.columns = [to_snake_case(col) for col in df.columns]

        return df

    def acoes_br(self) -> DataFrame:
        return (
            read_excel(self._INPUTS_PATH, sheet_name="Acoes BZ e IBOV")
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .iloc[:, :-1]
            .melt(id_vars=Indices.DATA.value, var_name=Indices.ATIVO.value, value_name=Indices.PRECO.value)
        )

    def ibov(self) -> DataFrame:
        return (
            read_excel(self._INPUTS_PATH, sheet_name="Acoes BZ e IBOV")
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            [[Indices.DATA.value, "IBOV"]]
            .melt(id_vars=Indices.DATA.value, var_name=Indices.ATIVO.value, value_name=Indices.PRECO.value)
        )

    def acoes_us(self) -> DataFrame:
        df = (
            read_excel(self._INPUTS_PATH, sheet_name="Acoes US")
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .melt(id_vars=Indices.DATA.value, var_name=Indices.ATIVO.value, value_name=Indices.PRECO.value)
        )
        df[Indices.ATIVO.value] = df[Indices.ATIVO.value].str.replace(" US Equity", "")

        return df

    def juros_nominal_br(self) -> DataFrame:
        return (
            read_excel(self._INPUTS_PATH, sheet_name="Juros nominal Brasil", skiprows=1)
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .melt(id_vars=Indices.DATA.value, var_name=Indices.PRAZO.value, value_name=Indices.VALOR.value)
        )

    def juros_real_br(self) -> DataFrame:
        return (
            read_excel(self._INPUTS_PATH, sheet_name="Juros Real Brasil", skiprows=1)
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .melt(id_vars=Indices.DATA.value, var_name=Indices.PRAZO.value, value_name=Indices.VALOR.value)
        )

    def di(self) -> DataFrame:
        return (
            read_excel(self._INPUTS_PATH, sheet_name="DI", skiprows=1)
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .melt(id_vars=Indices.DATA.value, var_name=Indices.PRAZO.value, value_name=Indices.VALOR.value)
        )

    def treasury(self) -> DataFrame:
        df = (
            read_excel(self._INPUTS_PATH, sheet_name="Treasury")
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .melt(id_vars=Indices.DATA.value, var_name=Indices.PRAZO.value, value_name=Indices.VALOR.value)
        )
        df[Indices.PRAZO.value] = df[Indices.PRAZO.value].str.replace("Treasury ", "")

        return df

    def fx(self) -> DataFrame:
        df = (
            read_excel(self._INPUTS_PATH, sheet_name="fx", skiprows=1)
            .rename(columns={"Unnamed: 0": Indices.DATA.value})
            .melt(id_vars=Indices.DATA.value, var_name=Indices.CAMBIO.value, value_name=Indices.VALOR.value)
        )
        df[Indices.CAMBIO.value] = df[Indices.CAMBIO.value].str.replace(" Curncy", "")

        return df
    
    def opcoes(self) -> DataFrame:
        # Ler Excel
        df = (
            read_excel(self._INPUTS_PATH, sheet_name="Dados Carteiras", skiprows=40, usecols="B:H", nrows=15)
            .rename(columns={"Unnamed: 1": Indices.ID.value})
        )

        # Ajustar nomes das colunas
        df.columns = [to_snake_case(col) for col in df.columns]

        # Retirar sufixos da coluna "underlying"
        df["underlying"] = df["underlying"].str.replace(" BZ Equity", "").str.replace(" Index", "")

        # Renomear coluna de preços
        df = df.rename(columns={df.columns[-1]: Indices.PRECO.value})

        return df

    def titulos(self) -> DataFrame:
        # Ler Excel
        df = (
            read_excel(self._INPUTS_PATH, sheet_name="Dados Carteiras", skiprows=58, usecols="B:G", nrows=11)
            .rename(columns={"Título": Indices.ID.value})
        )

        # Ajustar nomes das colunas
        df.columns = [to_snake_case(col) for col in df.columns]

        # Renomear colunas de preços e taxas
        df = df.rename(columns={
            df.columns[-2]: Indices.PRECO.value,
            df.columns[-1]: "taxa"
        })

        return df

    def futuros(self) -> DataFrame:
        # Ler Excel
        df = (
            read_excel(self._INPUTS_PATH, sheet_name="Dados Carteiras", skiprows=72, usecols="B:F", nrows=27)
            .rename(columns={"Unnamed: 1": Indices.ID.value})
        )

        # Ajustar nomes das colunas
        df.columns = [to_snake_case(col) for col in df.columns]

        # Remover sufixos da coluna de tipo
        df["tipo"] = df["tipo"].str.replace(" BMF", "")

        # Renomear coluna de preços
        df = df.rename(columns={df.columns[-1]: Indices.PRECO.value})

        # Dividir coluna de tamanho de contratos para extrair a moeda
        df[["tamanho_contrato", "moeda"]] = df["tamanho_contrato"].str.extract(r'([\d\.,]+)\s*\(?([A-Z]+)\)?')
        df["tamanho_contrato"] = df["tamanho_contrato"].str.replace('.', '', regex=False)\
                                                       .str.replace(',', '.', regex=False)\
                                                       .astype(float)
        return df

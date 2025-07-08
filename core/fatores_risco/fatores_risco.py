from pandas import DataFrame

from core.carteira import Carteira, Posicao
from utils.enums import Colunas, FatoresRisco


class MatrizFatoresRisco:
    def __init__(self, carteira: Carteira):
        self.carteira = carteira
class CalculosFatoresRisco:
    @classmethod
    def calcular_variacao(
        cls, 
        df: DataFrame, 
        fator_risco: FatoresRisco,
        agrupar_por: Colunas,
        coluna_valor: Colunas
    ) -> DataFrame:
        # Valores nominais
        if fator_risco in [FatoresRisco.ACAO, FatoresRisco.CAMBIO, FatoresRisco.MERCADO]:
            df[Colunas.VARIACAO.value] = df.sort_values(Colunas.DATA.value)\
                                           .groupby(agrupar_por.value)\
                                           [coluna_valor.value]\
                                           .transform(lambda row: (row/row.shift(1)) - 1)
            return df
        
        # Valores percentuais
        elif fator_risco in [FatoresRisco.JUROS, FatoresRisco.VOLATILIDADE]:
            df[Colunas.VARIACAO.value] = df.sort_values(Colunas.DATA.value)\
                                           .groupby(agrupar_por.value)\
                                           [coluna_valor.value]\
                                           .transform(lambda row: row - row.shift(1))
            return df
        
        else:
            raise ValueError("Fator de risco desconhecido.")

from typing import Optional

from pandas import DataFrame

from core.carteira import Carteira, Posicao
from inputs.data_handler import InputsDataHandler
from utils.enums import Colunas, FatoresRisco, Localidade


class MatrizFatoresRisco:
    def __init__(self, carteira: Carteira):
        self.carteira = carteira

    def cov_ewma(self) -> DataFrame:
        pass

    def cov_garch(self) -> DataFrame:
        pass


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
    
    @classmethod
    def calcular_volatilidade(cls, df: DataFrame, lambda_: float = 0.94) -> DataFrame:
        pass

    @classmethod
    def variancia_ewma(cls, df: DataFrame, lambda_: float = 0.94) -> DataFrame:
        assert lambda_ >= 0 and lambda_ <= 1, "Parâmetro lambda fora do domínio (entre 0 e 1)."

    
    @classmethod
    def definir_variacao_fator_risco(
        cls,
        fator_risco: FatoresRisco,
        localidade: Localidade,
        inputs: InputsDataHandler,
        posicao: Optional[Posicao] = None,
        lambda_: float = 0.94
    ) -> DataFrame:
        # Checar se posição é fornecida para o caso de fator de risco de juros
        assert (fator_risco != FatoresRisco.JUROS) or ((fator_risco == FatoresRisco.JUROS) and posicao), "Posição deve ser fornecida para o fator de risco de juros."
        assert localidade in [Localidade.BR, Localidade.US], "Localidade desconhecida"

        # Retornar variação do fator de risco, considerando a localidade
        if fator_risco in [FatoresRisco.ACAO, FatoresRisco.VOLATILIDADE]:
            df = inputs.acoes_br() if localidade == Localidade.BR else inputs.acoes_us()
            colunas = [
                Colunas.DATA.value,
                Colunas.ATIVO.value,
                Colunas.VARIACAO.value if fator_risco == FatoresRisco.ACAO else Colunas.VOLATILIDADE.value
            ]
            return cls.calcular_volatilidade(
                cls.calcular_variacao(df, fator_risco, Colunas.ATIVO, Colunas.PRECO),
                lambda_
            )[colunas]
        elif fator_risco == FatoresRisco.JUROS:
            pass
        elif fator_risco == FatoresRisco.CAMBIO:
            colunas = [
                Colunas.DATA.value,
                Colunas.CAMBIO.value,
                Colunas.VARIACAO.value
            ]
            return cls.calcular_variacao(df, fator_risco, Colunas.ATIVO, Colunas.PRECO)[colunas]
        else:
            raise ValueError("Fator de risco inválido.")

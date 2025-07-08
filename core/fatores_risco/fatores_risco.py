from typing import Optional

from numpy import sqrt
from pandas import DataFrame, Series

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
    def calcular_volatilidade(cls, df: DataFrame, localidade: Localidade,  lambda_: float = 0.94) -> DataFrame:
        # Calcular variância EWMA dos ativos do mercado
        df = CalculosFatoresRisco.variancia_ewma(
                CalculosFatoresRisco.calcular_variacao(df, FatoresRisco.ACAO, Colunas.ATIVO, Colunas.PRECO),
                Colunas.ATIVO,
                lambda_
             )
        
        # Definir parâmetro de ajuste de período
        ajuste_periodo = sqrt(252) if localidade == Localidade.BR else 1.0

        # Calcular volatilidade
        df[Colunas.VOLATILIDADE.value] = df.sort_values(Colunas.DATA.value)\
                                             .groupby(Colunas.ATIVO.value)\
                                             .apply(lambda group:
                                                sqrt(group[Colunas.VARIANCIA_EWMA.value]) * ajuste_periodo
                                             )\
                                             .reset_index()\
                                             .iloc[:, -1]
        return df

    @classmethod
    def ewma(cls, valor_calculado: Series, valor_fator_risco: Series, lambda_: float = 0.94) -> Series:
        return lambda_ * valor_calculado.shift(1) + (1 - lambda_) * valor_fator_risco

    @classmethod
    def variancia_ewma(cls, df: DataFrame, agrupar_por: Colunas, lambda_: float = 0.94) -> DataFrame:
        # Validar valor do lambda
        assert lambda_ >= 0 and lambda_ <= 1, "Parâmetro lambda fora do domínio (entre 0 e 1)."

        # Iniciar modelo
        df[Colunas.VARIANCIA_EWMA.value] = 0.0

        # Efetuar cálculo de variância seguindo modelo EWMA
        df[Colunas.VARIANCIA_EWMA.value] = df.sort_values(Colunas.DATA.value)\
                                             .groupby(agrupar_por.value)\
                                             .apply(lambda group: cls.ewma(
                                                 group[Colunas.VARIANCIA_EWMA.value], group[Colunas.VARIACAO.value] ** 2, lambda_
                                             ))\
                                             .reset_index()\
                                             [0]
        return df

    
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
                localidade,
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

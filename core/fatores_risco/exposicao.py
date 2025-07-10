from pandas import DataFrame

from core.carteira import Posicao
from utils.enums import FatoresRisco, Opcoes


class Exposicao:
    def __init__(self, posicao: Posicao):
        self.posicao = posicao

    def calcular_exposicao(self) -> DataFrame:
        exposicoes_fatores_risco = []
        if isinstance(self.posicao.ativo, Opcoes):
            # TODO: implementar calculo de exposição para opcoes
            pass

        for fr in self.posicao.fatores_risco:
            if fr == FatoresRisco.ACAO:
                # TODO: implementar calculo de exposição simples para ações
                pass
            elif fr in [FatoresRisco.CAMBIO_USDBRL, FatoresRisco.CAMBIO_USDOUTROS]:
                # TODO: implementar calculo de exposição para cambio
                pass
            elif fr == FatoresRisco.JUROS:
                # TODO: implementar calculo de exposição para juros
                pass
            else:
                raise ValueError("Fator de risco desconhecido.")

    @staticmethod
    def _exposicao_acao(quantidade: float, preco: float, delta: float = 1.0) -> float:
        return delta * quantidade * preco
    
    @staticmethod
    def _exposicao_volatilidade(quantidade: float, vega: float) -> float:
        return quantidade * vega

    @staticmethod
    def _exposicao_cambio(quantidade: float, preco_original: float, cambio: float, cambio_dolar: float = 1.0) -> float:
        return quantidade * (preco_original * cambio * cambio_dolar)
    
    @staticmethod
    def _exposicao_juros(quantidade: float, pu: float, duration_modificada: float) -> float:
        return -quantidade * pu * duration_modificada

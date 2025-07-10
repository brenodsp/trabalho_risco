from pandas import DataFrame

from core.carteira import Posicao
from core.fatores_risco.fatores_risco import nomear_vetor_fator_risco
from inputs.data_handler import InputsDataHandler
from utils.enums import FatoresRisco, Opcoes, Localidade, Colunas, TipoFuturo


class Exposicao:
    def __init__(self, posicao: Posicao, inputs: InputsDataHandler):
        self.posicao = posicao
        self.inputs = inputs

    def calcular_exposicao(self) -> DataFrame:
        exposicoes_fatores_risco = []
        if isinstance(self.posicao.ativo, Opcoes):
            # TODO: implementar calculo de exposição para opcoes
            pass

        for fr in self.posicao.fatores_risco:
            if fr == FatoresRisco.ACAO:
                # Fazer distinção entre ações brasileiras e americanas
                if self.posicao.localidade == Localidade.BR:
                    precos = self.inputs.acoes_br()
                    cambio = 1.0
                elif self.posicao.localidade == Localidade.US:
                    precos = self.inputs.acoes_br()
                    df_cambio = self.inputs.fx()
                    cambio = float(df_cambio.loc[
                        (df_cambio[Colunas.DATA.value] == df_cambio[Colunas.DATA.value].max()) &
                        (df_cambio[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name)
                    ][Colunas.VALOR.value].values[0])
                # Buscar último preco da ação
                precos = self.inputs.acoes_br() if self.posicao.localidade == Localidade.BR else self.inputs.acoes_us()
                ultimo_preco = precos.loc[
                    (precos[Colunas.ATIVO.value] == self.posicao.ativo.value) &
                    (precos[Colunas.DATA.value] == precos[Colunas.DATA.value].max())
                ][Colunas.PRECO.value].values[0]

                # Calcular exposição e adicionar ao vetor de exposições
                w = float(self._exposicao_acao(self.posicao.quantidade, ultimo_preco))
                exposicoes_fatores_risco.append(w)

            elif fr in [FatoresRisco.CAMBIO_USDBRL, FatoresRisco.CAMBIO_USDOUTROS]:
                # TODO: implementar calculo de exposição para cambio
                pass
            elif fr == FatoresRisco.JUROS:
                # TODO: implementar calculo de exposição para juros
                pass
            else:
                raise ValueError("Fator de risco desconhecido.")
            
        return DataFrame(
            data=exposicoes_fatores_risco,
            columns=nomear_vetor_fator_risco()
        )

    @staticmethod
    def _exposicao_acao(quantidade: float, preco: float, delta: float = 1.0, cambio: float = 1.0) -> float:
        return (delta * quantidade) * (preco * cambio)
    
    @staticmethod
    def _exposicao_volatilidade(quantidade: float, vega: float) -> float:
        return quantidade * vega

    @staticmethod
    def _exposicao_cambio(quantidade: float, preco_original: float, cambio: float, cambio_dolar: float = 1.0) -> float:
        return quantidade * (preco_original * cambio * cambio_dolar)
    
    @staticmethod
    def _exposicao_juros(quantidade: float, pu: float, duration_modificada: float) -> float:
        return -quantidade * pu * duration_modificada

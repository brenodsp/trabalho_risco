from datetime import date
from math import sqrt

from numpy import array
from pandas import DataFrame

from core.carteira import Carteira, Posicao
from core.fatores_risco.exposicao import ExposicaoCarteira
from core.fatores_risco.fatores_risco import MatrizFatoresRisco, nomear_vetor_fator_risco
from inputs.data_handler import InputsDataHandler
from utils.enums import IntervaloConfianca


class VarParametrico:
    def __init__(
            self, 
            exposicoes: ExposicaoCarteira, 
            retornos_fatores_risco: MatrizFatoresRisco,
            intervalo_confianca: IntervaloConfianca
    ):
        self.exposicoes = exposicoes
        self.retornos_fatores_risco = retornos_fatores_risco
        self.intervalo_confianca = intervalo_confianca

    def var_parametrico_carteira(self) -> float:
        return self._calculo_var_matricial(
            self.exposicoes.exposicao_carteira().values, 
            self.retornos_fatores_risco.matriz_cov_ewma().values, 
            self.intervalo_confianca.value
        )

    def var_parametrico_posicao(self, posicao: Posicao, data_referencia: date, inputs: InputsDataHandler):
        fatores_risco_posicao = [nomear_vetor_fator_risco(fr, posicao) for fr in posicao.fatores_risco]
        fatores_risco_carteira = self.exposicoes.exposicao_carteira().columns.to_list()
        assert len([fr for fr in fatores_risco_posicao if fr in fatores_risco_carteira]) > 0, "Posição fornecida não consta na carteira."

        carteira_simples = Carteira([posicao], data_referencia)
        retorno = self.retornos_fatores_risco.matriz_cov_ewma().loc[fatores_risco_posicao, fatores_risco_posicao]
        exposicao = ExposicaoCarteira(carteira_simples, inputs).exposicao_carteira()

        return self._calculo_var_matricial(exposicao.values, retorno.values, self.intervalo_confianca.value)
    
    @staticmethod
    def _calculo_var_matricial(vetor_exposicao: array, matriz_retorno: array, intervalo_confianca: float) -> float:
        return sqrt((vetor_exposicao @ matriz_retorno @ vetor_exposicao.T) * (intervalo_confianca ** 2))

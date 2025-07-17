from datetime import date
from math import sqrt

from numpy import array
from pandas import DataFrame, Series, to_datetime, concat

from core.carteira import Carteira, Posicao
from core.fatores_risco.black_scholes import bs_implied_vol, bs_price
from core.fatores_risco.exposicao import ExposicaoCarteira
from core.fatores_risco.fatores_risco import MatrizFatoresRisco, nomear_vetor_fator_risco
from core.renda_fixa.renda_fixa import RendaFixa
from inputs.data_handler import InputsDataHandler
from utils.enums import IntervaloConfianca, AcoesBr, AcoesUs, Opcoes, Futuros, TipoFuturo, Titulos, Localidade, Colunas


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


class VarHistorico:
    def __init__(
            self,
            carteira: Carteira,
            retornos: MatrizFatoresRisco, 
            inputs: InputsDataHandler
    ):
        self.carteira = carteira
        self.retornos = retornos
        self.inputs = inputs

    def _gerar_cenarios(self, n_cenarios: int) -> DataFrame:
        retornos = self.retornos.fatores_risco_carteira()
        posicoes = [p for p in self.carteira.__dict__.values() if isinstance(p, Posicao)]
        
        lista_pnl_posicao = []
        for posicao in posicoes:
            # Filtrar retornos pertinentes à posição avaliada
            fatores_risco = [
                nomear_vetor_fator_risco(fr, posicao)
                for fr in posicao.fatores_risco
            ]
            retornos_posicao = retornos.loc[:, fatores_risco]
            retornos_posicao[Colunas.POSICAO.value] = posicao.ativo.name

            # Pegar valores de referência para a geração de cenários
            if isinstance(posicao.ativo, AcoesBr) or isinstance(posicao.ativo, AcoesUs):
                if posicao.localidade == Localidade.BR:
                    ultimo_preco = self.inputs.acoes_br()
                    cambio = 1.0
                else:
                    ultimo_preco = self.inputs.acoes_us()
                    cambio = self.inputs.fx()
                    cambio = float(cambio.loc[
                        (cambio[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name) &
                        (cambio[Colunas.DATA.value] == data_ref)
                    ][Colunas.VALOR.value].values[0])
                    
                data_ref = ultimo_preco.loc[ultimo_preco[Colunas.DATA.value] <= to_datetime(self.carteira.data_referencia)][Colunas.DATA.value].max()
                ultimo_preco = float(ultimo_preco.loc[
                    (ultimo_preco[Colunas.ATIVO.value] == posicao.ativo.value) &
                    (ultimo_preco[Colunas.DATA.value] == data_ref)
                ][Colunas.PRECO.value].values[0])

                retornos_posicao[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    cambio * ultimo_preco, 
                    ultimo_preco * (1 + retornos_posicao[posicao.ativo.name])
                )

            elif isinstance(posicao.ativo, Opcoes):
                # Recuperar informações de opções
                acoes = self.inputs.acoes_br()
                acoes = acoes.loc[acoes[Colunas.ATIVO.value] == posicao.produto.value][[Colunas.DATA.value, Colunas.PRECO.value]]
                opcoes = self.inputs.opcoes()
                opcoes = opcoes.loc[opcoes[Colunas.ID.value] == posicao.ativo.value]

                # Definir características da opção
                S = float(opcoes["strike"].values[0])
                K = float(opcoes["nocional"].values[0])
                T = RendaFixa.calcular_du(to_datetime(self.carteira.data_referencia), to_datetime(opcoes["vencimento"].values[0]), self.inputs)/252
                preco_opcao = float(opcoes["preco"].values[0])
                tipo = 1 if opcoes["tipo"].values[0] == "call" else -1

                # Calcular propriedades Black-Scholes
                vol_implicita = float(bs_implied_vol(S, K, T, 0, 0, preco_opcao, tipo, 1))
                coluna_vol = [c for c in retornos_posicao.columns if "VOL" in c][0]

                # Precificar cenários de preço da opção
                retornos_posicao = retornos_posicao.merge(acoes, on=Colunas.DATA.value)
                retornos_posicao["cenario_vol"] = retornos_posicao[coluna_vol] + vol_implicita/100
                retornos_posicao["cenario_preco"] = retornos_posicao.apply(
                    lambda row: bs_price(row[Colunas.PRECO.value], K, T-(1/252), 0, 0, row["cenario_vol"]*100, tipo, 1),
                    axis=1
                )
                
                # Produzir cenários de P&L
                retornos_posicao[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    preco_opcao, 
                    retornos_posicao["cenario_preco"]
                )
            
            # elif futuro_di:
            
            # elif futuro_cambio:
            
            # elif futuro_indice:
            
            # elif titulo:
            
            else:
                raise ValueError("Ativo não mapeado.")

            df_posicao = retornos_posicao[[
                Colunas.DATA.value,
                Colunas.POSICAO.value,
                Colunas.PNL.value
            ]]

            lista_pnl_posicao.append(df_posicao)
        
        return concat(lista_pnl_posicao)
            

    @staticmethod
    def _calcular_pnl(qtd: float, preco_referencia: float, preco_cenario: Series) -> Series:
        return qtd * (preco_cenario - preco_referencia)

    def var_historico_carteira(self, n_cenarios: int) -> float:
        # TODO: LEMBRANDO QUE O VAR DEVE SER UM VALOR ABSOLUTO
        # TODO: implementar regra de VaR histórico da carteira
        cenarios_pnl = self._gerar_cenarios()
        pass

    def var_historico_posição(self, posicao: Posicao, n_cenarios: int) -> float:
        # TODO: implementar regra de VaR histórico da posição
        self._gerar_cenarios()
        pass

    def estresse_carteira(self, n_cenarios: int) -> float:
        # TODO: implementar regra de estresse da carteira (pior cenário)
        cenarios_pnl = self._gerar_cenarios()
        pass

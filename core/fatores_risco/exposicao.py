from datetime import date

from pandas import DataFrame, concat, to_datetime

from core.carteira import Carteira, Posicao
from core.fatores_risco.black_scholes import bs_delta, bs_implied_vol, bs_price, bs_vega
from core.fatores_risco.fatores_risco import nomear_vetor_fator_risco
from core.renda_fixa.renda_fixa import RendaFixa
from inputs.data_handler import InputsDataHandler
from utils.enums import FatoresRisco, Opcoes, Localidade, Colunas, TipoFuturo, Futuros, AcoesUs, Titulos


class ExposicaoCarteira:
    def __init__(self, carteira: Carteira, inputs: InputsDataHandler):
        self.carteira = carteira
        self.inputs = inputs

    def exposicao_carteira(self) -> DataFrame:
        # Calcular exposição de cada posição da carteira
        exposicoes = [
            Exposicao(p, self.inputs, self.carteira.data_referencia).calcular_exposicao() 
            for p in [p for p in self.carteira.__dict__.values() if isinstance(p, Posicao)]
        ]

        # Juntar exposições e formatar como vetor
        return (
            concat(exposicoes)
            .groupby(Colunas.FATOR_RISCO.value)
            .sum()
            .T
        )


class Exposicao:
    def __init__(self, posicao: Posicao, inputs: InputsDataHandler, data_referencia: date):
        self.posicao = posicao
        self.inputs = inputs
        self.data_referencia = to_datetime(data_referencia)

    def calcular_exposicao(self) -> DataFrame:
        exposicoes_fatores_risco = []
        if isinstance(self.posicao.ativo, Opcoes):
            # Recuperar informações de opções
            opcoes = self.inputs.opcoes()
            opcoes = opcoes.loc[opcoes[Colunas.ID.value] == self.posicao.ativo.value]

            # Definir características da opção
            S = float(opcoes["strike"].values[0])
            K = float(opcoes["nocional"].values[0])
            T = RendaFixa.calcular_du(self.data_referencia, to_datetime(opcoes["vencimento"].values[0]), self.inputs)/252
            preco_opcao = float(opcoes["preco"].values[0])
            tipo = 1 if opcoes["tipo"].values[0] == "call" else -1

            # Calcular propriedades Black-Scholes
            vol_implicita = float(bs_implied_vol(S, K, T, 0, 0, preco_opcao, tipo, 1))
            delta = float(bs_delta(S, K, T, 0, 0, vol_implicita, tipo, 1))
            vega = float(bs_vega(S, K, T, 0, 0, vol_implicita, tipo, 1))

            # Determinar exposições por parte do efeito do preço da ação e da volatilidade
            w1_s = self._exposicao_acao(self.posicao.quantidade, S, delta)
            df_w1_s = self._criar_df_exposicao(
                nomear_vetor_fator_risco(FatoresRisco.ACAO, self.posicao),
                w1_s
            ) 
            exposicoes_fatores_risco.append(df_w1_s)

            w2_vol = self._exposicao_volatilidade(self.posicao.quantidade, vega)
            df_w2_vol = self._criar_df_exposicao(
                nomear_vetor_fator_risco(FatoresRisco.VOLATILIDADE, self.posicao),
                w2_vol
            ) 
            exposicoes_fatores_risco.append(df_w2_vol)

            return concat(exposicoes_fatores_risco)

        # Calcular exposição para futuros
        if isinstance(self.posicao.ativo, Futuros):
            df_futuros = self.inputs.futuros()
            contratos = float(df_futuros.loc[df_futuros[Colunas.ID.value] == self.posicao.ativo.value]["tamanho_contrato"].values[0])
            if not ((FatoresRisco.CAMBIO_USDBRL in self.posicao.fatores_risco) or (FatoresRisco.CAMBIO_USDOUTROS in self.posicao.fatores_risco)):
                w = self._exposicao_futuros(self.posicao.quantidade, contratos)

        for fr in self.posicao.fatores_risco:
            if fr == FatoresRisco.ACAO:
                # Considerar exposição já calculada para futuros
                if isinstance(self.posicao.ativo, Futuros):
                    w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(fr, self.posicao), w)
                    exposicoes_fatores_risco.append(w_df)
                    continue

                # Fazer distinção entre ações brasileiras e americanas
                elif self.posicao.localidade == Localidade.BR:
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
                ultimo_preco = float(precos.loc[
                    (precos[Colunas.ATIVO.value] == self.posicao.ativo.value) &
                    (precos[Colunas.DATA.value] == precos[Colunas.DATA.value].max())
                ][Colunas.PRECO.value].values[0])

                # Calcular exposição e adicionar ao vetor de exposições
                w = float(self._exposicao_acao(self.posicao.quantidade, ultimo_preco, cambio=cambio))
                w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(fr, self.posicao), w)
                exposicoes_fatores_risco.append(w_df)

                # Utilizar exposição para o fator de risco de câmbio em caso de ação americana
                if self.posicao.localidade == Localidade.US:
                    w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(FatoresRisco.CAMBIO_USDBRL, self.posicao), w)
                    exposicoes_fatores_risco.append(w_df)
                    
            elif fr in [FatoresRisco.CAMBIO_USDBRL, FatoresRisco.CAMBIO_USDOUTROS]:
                # Herdar exposição em caso de produtos americanos
                if fr == FatoresRisco.CAMBIO_USDBRL and len(self.posicao.fatores_risco) > 1:
                   continue

                df_cambio = self.inputs.fx()
                
                filtro = TipoFuturo.USDBRL.name if fr == FatoresRisco.CAMBIO_USDBRL else self.posicao.produto.name
                cambio_dolar = float(df_cambio.loc[
                    (df_cambio[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name) &
                    (df_cambio[Colunas.DATA.value] == df_cambio[Colunas.DATA.value].max())
                ][Colunas.VALOR.value].values[0])
                
                ultimo_cambio = (
                    float(df_cambio.loc[
                        (df_cambio[Colunas.CAMBIO.value] == filtro) &
                        (df_cambio[Colunas.DATA.value] == df_cambio[Colunas.DATA.value].max())
                    ][Colunas.VALOR.value].values[0])
                    if fr == FatoresRisco.CAMBIO_USDOUTROS
                    else
                    1.0 
                )

                w = float(self._exposicao_cambio(self.posicao.quantidade, contratos, cambio_dolar, ultimo_cambio))
                w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(fr, self.posicao), w)
                exposicoes_fatores_risco.append(w_df)

                # Utilizar exposição para o fator de risco de câmbio em caso de ação americana
                if fr == FatoresRisco.CAMBIO_USDOUTROS:
                    w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(FatoresRisco.CAMBIO_USDBRL, self.posicao), w)
                    exposicoes_fatores_risco.append(w_df)

            elif fr == FatoresRisco.JUROS:
                # Se for proveniente de futuros, apenas utilizar exposição calculada para esse tipo de ativo
                if isinstance(self.posicao.ativo, Futuros):
                    w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(fr, self.posicao), w)
                    exposicoes_fatores_risco.append(w_df)
                    continue

                # Instanciar calculadora de renda fixa
                df_titulos = self.inputs.titulos()
                cupom = float(df_titulos.loc[df_titulos[Colunas.ID.value] == self.posicao.ativo.value]["cupom"].values[0])
                taxa = float(df_titulos.loc[df_titulos[Colunas.ID.value] == self.posicao.ativo.value]["taxa"].values[0])
                rf = RendaFixa(
                    self.data_referencia,
                    self.posicao.vencimento,
                    self.posicao.localidade,
                    self.inputs,
                    cupom,
                    taxa
                )

                # Calcular PU e Duration Modificada
                pu = rf.pu()
                duration_modificada = rf.duration_modificada()

                # Calcular exposição
                df_cambio = self.inputs.fx()
                cambio_dolar = (
                    float(df_cambio.loc[
                        (df_cambio[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name) &
                        (df_cambio[Colunas.DATA.value] == df_cambio[Colunas.DATA.value].max())
                    ][Colunas.VALOR.value].values[0])
                    if self.posicao.localidade == Localidade.US
                    else
                    1.0 
                )

                w = self._exposicao_juros(self.posicao.quantidade, pu, duration_modificada, cambio_dolar)
                w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(fr, self.posicao), w)
                exposicoes_fatores_risco.append(w_df)

                # Utilizar exposição para o fator de risco de câmbio em caso de ação americana
                if self.posicao.localidade == Localidade.US:
                    w_df = self._criar_df_exposicao(nomear_vetor_fator_risco(FatoresRisco.CAMBIO_USDBRL, self.posicao), w)
                    exposicoes_fatores_risco.append(w_df)
                pass
            
            else:
                raise ValueError("Fator de risco desconhecido.")
            
        return concat(exposicoes_fatores_risco)
    
    @staticmethod
    def _criar_df_exposicao(nome_fator_risco: str, exposicao: float):
        return DataFrame({
            Colunas.FATOR_RISCO.value: [nome_fator_risco],
            Colunas.EXPOSICAO.value: [exposicao]
        })

    @staticmethod
    def _exposicao_acao(quantidade: float, preco: float, delta: float = 1.0, cambio: float = 1.0) -> float:
        return (delta * quantidade) * (preco * cambio)
    
    @staticmethod
    def _exposicao_volatilidade(quantidade: float, vega: float) -> float:
        return quantidade * vega

    @staticmethod
    def _exposicao_cambio(quantidade: float, preco_original: float, cambio_dolar: float, cambio_outros: float = 1.0) -> float:
        return quantidade * ((preco_original / cambio_outros) * cambio_dolar)
    
    @staticmethod
    def _exposicao_juros(quantidade: float, pu: float, duration_modificada: float, cambio_dolar: float = 1.0) -> float:
        return (quantidade * pu * duration_modificada) * cambio_dolar
    
    @staticmethod
    def _exposicao_futuros(quantidade: float, tamanho_contrato: float) -> float:
        return quantidade * tamanho_contrato

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
from utils.enums import IntervaloConfianca, AcoesBr, AcoesUs, Opcoes, Futuros, TipoFuturo, Titulos, \
                        Localidade, Colunas, TipoVarHistorico


class VarParametrico:
    def __init__(
            self, 
            carteira: Carteira,
            exposicoes: ExposicaoCarteira, 
            retornos_fatores_risco: MatrizFatoresRisco,
            intervalo_confianca: IntervaloConfianca
    ):
        self.carteira = carteira
        self.exposicoes = exposicoes
        self.retornos_fatores_risco = retornos_fatores_risco
        self.intervalo_confianca = intervalo_confianca

    def var_parametrico_carteira(self) -> float:
        return self._calculo_var_matricial(
            self.exposicoes.exposicao_carteira().values, 
            self.retornos_fatores_risco.matriz_cov_ewma().values, 
            self.intervalo_confianca.value
        )
    
    def participacao_percentual_posicoes(self) -> DataFrame:
        # Calcular exposição da carteira aos fatores de risco
        exposicao = self.exposicoes.exposicao_carteira()

        # Calcular participação percentual de cada fator de risco ao VaR da carteira
        percent_fatores_risco = self._participacao_percentual_fatores_risco(exposicao)

        # Percorrer cada posição da carteira
        posicoes = [p for p in self.carteira.__dict__.values() if isinstance(p, Posicao)]

        lista_participacao = []
        for posicao in posicoes:
            # Nomear posicao
            nome_posicao = posicao.ativo.name if isinstance(posicao.ativo, (AcoesBr, AcoesUs)) else posicao.produto.name

            # Instanciar carteira simples para cálculo de exposição
            carteira_simples = Carteira([posicao], self.carteira.data_referencia)
        
            # Calcular exposição da posição aos fatores de risco da carteira e o quanto a posição 
            # é representativa para a exposição ao fator de risco na carteira
            exposicao_posicao = ExposicaoCarteira(carteira_simples, self.exposicoes.inputs).exposicao_carteira()
            representacao_fator_risco = (exposicao_posicao / exposicao.loc[:, exposicao_posicao.columns]).reset_index(drop=True)

            # Calcular participacao percentual da posição para o risco da carteira
            participacao_posicao = DataFrame((
                representacao_fator_risco * percent_fatores_risco.loc[:, exposicao_posicao.columns]
            ).sum(axis=1).reset_index(drop=True)).rename(columns={0: nome_posicao})

            lista_participacao.append(participacao_posicao)
        
        # Concatenar participações percentuais de cada posição
        participacao_df = concat(lista_participacao, axis=1).fillna(0).reset_index(drop=True)
        assert float(participacao_df.values.sum()) == 1.0, "Participação percentual das posições não soma 100%."
        return participacao_df

    def _participacao_percentual_fatores_risco(self, exposicao: DataFrame) -> DataFrame:
        # Calcular VaR marginal de cada fator de risco
        var_marginal = self._var_marginal_carteira(exposicao)

        # Calcular VaR componente de cada fator de risco
        var_componente = self._var_componente_carteira(exposicao, var_marginal)
        componente_total = float(var_componente.values.sum())

        # Calcular participação percentual de cada fator de risco
        return var_componente / componente_total

    def var_parametrico_posicao(self) -> DataFrame:
        # Percorrer cada posição da carteira
        posicoes = [p for p in self.carteira.__dict__.values() if isinstance(p, Posicao)]

        lista_var = []
        for posicao in posicoes:
            # Nomear posicao
            nome_posicao = posicao.ativo.name if isinstance(posicao.ativo, (AcoesBr, AcoesUs)) else posicao.produto.name

            # Instanciar carteira simples para cálculo de exposição
            carteira_simples = Carteira([posicao], self.carteira.data_referencia)
        
            # Calcular exposição da posição aos fatores de risco da carteira e o quanto a posição 
            # é representativa para a exposição ao fator de risco na carteira
            exposicao_posicao = ExposicaoCarteira(carteira_simples, self.exposicoes.inputs).exposicao_carteira()

            # Calcular retornos dos fatores de risco
            fatores_risco = MatrizFatoresRisco(carteira_simples, self.exposicoes.inputs).matriz_cov_ewma()

            # Calcular VaR da posição
            var_posicao = DataFrame({nome_posicao: [self._calculo_var_matricial(
                exposicao_posicao.values, 
                fatores_risco.values, 
                self.intervalo_confianca.value
            )]})
            
            lista_var.append(var_posicao)

        return DataFrame(concat(lista_var, axis=1))
    
    @staticmethod
    def _calculo_var_matricial(vetor_exposicao: array, matriz_retorno: array, intervalo_confianca: float) -> float:
        return sqrt((vetor_exposicao @ matriz_retorno @ vetor_exposicao.T) * (intervalo_confianca ** 2))
    
    @staticmethod
    def _calculo_var_matricial(vetor_exposicao: array, matriz_retorno: array, intervalo_confianca: float) -> float:
        return sqrt((vetor_exposicao @ matriz_retorno @ vetor_exposicao.T) * (intervalo_confianca ** 2))
    
    def _var_marginal_carteira(self, exposicao: DataFrame) -> DataFrame:
        """
        Calcula o VaR marginal de cada fator de risco da carteira.
        """
        # Calcular exposições da carteira
        nomes_fatores_risco = exposicao.columns.to_list()

        # Calcular matriz de covariância dos retornos
        matriz_cov = self.retornos_fatores_risco.matriz_cov_ewma()

        # Calcuar VaR marginal da carteira e posteriormente transformar em DataFrame
        var_marginal = self._calcular_var_marginal(
            exposicao.values, 
            matriz_cov.values,
            self._desvio_padrao_carteira(exposicao.values, matriz_cov.values),
            self.intervalo_confianca.value
        )
        
        return DataFrame(var_marginal, columns=nomes_fatores_risco)
    
    def _var_componente_carteira(self, exposicao: DataFrame, var_marginal: DataFrame) -> DataFrame:
        return DataFrame(
            self._calcular_var_componente(var_marginal.values, exposicao.values),
            columns=exposicao.columns.to_list()
        )
    
    @staticmethod
    def _calcular_var_marginal(
        vetor_exposicao: array, 
        matriz_retorno: array, 
        desvio_padrao_carteira: float,
        intervalo_confianca: float
    ) -> array:
        """
        Calcula o VaR marginal de um vetor de exposições e uma matriz de retornos.
        """
        return abs((intervalo_confianca / desvio_padrao_carteira) * (vetor_exposicao @ matriz_retorno))
    
    @staticmethod
    def _desvio_padrao_carteira(vetor_exposicao: array, matriz_retorno: array) -> float:
        """
        Calcula o desvio padrão da carteira a partir do vetor de exposições e da matriz de retornos.
        """
        return sqrt(vetor_exposicao @ matriz_retorno @ vetor_exposicao.T)
    
    @staticmethod
    def _calcular_var_componente(var_marginal: array, vetor_exposicao: array) -> array:
        """
        Calcula o VaR componente de cada fator de risco da carteira.
        """
        return var_marginal * vetor_exposicao


class VarHistorico:
    #TODO: Adicionar metodologia de pesos mais recentes
    LAMBDA = 0.94
    def __init__(
            self,
            carteira: Carteira,
            retornos: MatrizFatoresRisco, 
            inputs: InputsDataHandler,
            tipo: TipoVarHistorico = TipoVarHistorico
    ):
        self.carteira = carteira
        self.retornos = retornos
        self.inputs = inputs
        self.tipo = tipo

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
            retornos_posicao = retornos.loc[:, fatores_risco].reset_index()
            retornos_posicao[Colunas.POSICAO.value] = posicao.ativo.name

            # Pegar valores de referência para a geração de cenários
            if isinstance(posicao.ativo, AcoesBr) or isinstance(posicao.ativo, AcoesUs):
                if posicao.localidade == Localidade.BR:
                    nocional = self.inputs.acoes_br()
                    cambio = 1.0
                else:
                    nocional = self.inputs.acoes_us()
                    cambio = self.inputs.fx()
                    data_ref = cambio.loc[cambio[Colunas.DATA.value] <= to_datetime(self.carteira.data_referencia)][Colunas.DATA.value].max()
                    cambio = float(cambio.loc[
                        (cambio[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name) &
                        (cambio[Colunas.DATA.value] == data_ref)
                    ][Colunas.VALOR.value].values[0])
                    
                data_ref = nocional.loc[nocional[Colunas.DATA.value] <= to_datetime(self.carteira.data_referencia)][Colunas.DATA.value].max()
                nocional = float(nocional.loc[
                    (nocional[Colunas.ATIVO.value] == posicao.ativo.value) &
                    (nocional[Colunas.DATA.value] == data_ref)
                ][Colunas.PRECO.value].values[0])

                retorno = (
                    (1 + retornos_posicao[posicao.ativo.name]) * (1 + retornos_posicao[TipoFuturo.USDBRL.name])
                    if posicao.localidade == Localidade.US
                    else
                    (1 + retornos_posicao[posicao.ativo.name])
                )

                retornos_posicao[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    cambio * nocional, 
                    cambio *nocional * retorno
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
            
            elif isinstance(posicao.ativo, Futuros) and posicao.produto == TipoFuturo.IBOV:
                # Recuperar informações de IBOV
                acoes = self.inputs.acoes_br()
                acoes = acoes.loc[acoes[Colunas.ATIVO.value] == posicao.produto.value]

                # Definir referência de preço e data de avaliação
                data_ref = acoes.loc[acoes[Colunas.DATA.value] <= to_datetime(self.carteira.data_referencia)][Colunas.DATA.value].max()
                nocional = float(acoes.loc[
                    (acoes[Colunas.DATA.value] == data_ref)
                ][Colunas.PRECO.value].values[0])

                # Calcular PnL
                retornos_posicao[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    nocional, 
                    nocional * (1 + retornos_posicao[posicao.produto.value])
                )

            elif isinstance(posicao.ativo, Futuros) and posicao.produto not in [TipoFuturo.DI, TipoFuturo.IBOV]:
                # Recuperar informações de cambio
                fx = self.inputs.fx()
                fx_filtro = fx.loc[fx[Colunas.CAMBIO.value] == posicao.produto.name]

                # Definir referência de preço e data de avaliação
                data_ref = fx_filtro.loc[fx_filtro[Colunas.DATA.value] <= to_datetime(self.carteira.data_referencia)][Colunas.DATA.value].max()
                ultimo_cambio = float(fx_filtro.loc[
                    (fx_filtro[Colunas.DATA.value] == data_ref)
                ][Colunas.VALOR.value].values[0])

                # Ajustar valor nocional
                if posicao.produto == TipoFuturo.USDBRL:
                    dolar_brl = ultimo_cambio
                    para_dolar = 1.0
                else:
                    dolar_brl = float(fx.loc[
                        (fx[Colunas.DATA.value] == data_ref) &
                        (fx[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name)
                    ][Colunas.VALOR.value].values[0])
                    para_dolar = ultimo_cambio
                
                nocional_ajustado = (100000 / para_dolar) * dolar_brl

                # Calcular PnL
                retornos_posicao[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    nocional_ajustado, 
                    nocional_ajustado * (1 + retornos_posicao[posicao.produto.name])
                )
            
            elif isinstance(posicao.ativo, Futuros) and posicao.produto == TipoFuturo.DI:
                # Calcular PnL
                nocional = 100000
                retornos_posicao[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    nocional, 
                    nocional * (1 + retornos_posicao[posicao.produto.value]/100)
                )
            
            elif isinstance(posicao.ativo, Titulos):
                # Recuperar informações de títulos
                metadados_titulos = self.inputs.titulos()
                metadados_titulos = metadados_titulos.loc[metadados_titulos[Colunas.ID.value] == posicao.ativo.value]
                titulos = (
                    self.inputs.treasury()
                    if posicao.localidade == Localidade.US
                    else
                    self.inputs.di()
                )

                # Utilizar framework de renda fixa para calcular propriedades do título
                rf = RendaFixa(
                    self.carteira.data_referencia, 
                    to_datetime(metadados_titulos["vencimento"].values[0]).date(), 
                    posicao.localidade, 
                    self.inputs,
                    cupom=float(metadados_titulos["cupom"].values[0]),
                    taxa=float(metadados_titulos["taxa"].values[0])
                )
                pu = rf.pu()
                curva_juros = rf.curva_juros()
                _, _, total_periodos = rf._base_semestral(
                    0,
                    0.1,
                    0.1,
                    (rf.vencimento - rf.data_referencia).days
                )

                # Adicionar dólar ao DataFrame de juros
                fx = self.inputs.fx()
                dolar = fx.loc[fx[Colunas.CAMBIO.value] == TipoFuturo.USDBRL.name]\
                        [[Colunas.DATA.value, Colunas.VALOR.value]]\
                        .rename(columns={Colunas.VALOR.value: TipoFuturo.USDBRL.name})
                if posicao.localidade == Localidade.BR:
                    dolar[TipoFuturo.USDBRL.name] = 1.0
                curva_juros = curva_juros.merge(dolar, on=Colunas.DATA.value, how="left")

                # Calcular cupons por cada periodo
                for i in range(1, total_periodos + 1):
                    coluna_fluxo = f"cupom_{i}"
                    curva_juros[coluna_fluxo] = curva_juros.apply(
                        lambda row: rf._vpl(
                            rf._base_semestral(rf.VALOR_FACE * row[TipoFuturo.USDBRL.name], rf.cupom/100, 0.1, 1)[0], 
                            row[Colunas.VALOR.value]/200,
                            i
                        ), axis=1
                    )
                
                # Calcular pu para cada data
                curva_juros["total_cupons"] = curva_juros[[f"cupom_{i}" for i in range(1, total_periodos + 1)]].sum(axis=1)
                curva_juros["pu"] = curva_juros.apply(
                    lambda row: rf._vpl(
                            rf.VALOR_FACE * row[TipoFuturo.USDBRL.name], 
                            row[Colunas.VALOR.value]/200,
                            total_periodos
                        ) + row["total_cupons"], axis=1
                    )
                
                # Calcular retornos do título
                curva_juros[Colunas.RETORNO.value] = curva_juros["pu"].pct_change().fillna(0)

                # Calcular PnL
                curva_juros[Colunas.PNL.value] = self._calcular_pnl(
                    posicao.quantidade, 
                    pu, 
                    pu * (1 + curva_juros[Colunas.RETORNO.value])
                )

                # Adicionar coluna de PnL ao DataFrame de retornos
                retornos_posicao = retornos_posicao.merge(
                    curva_juros[[Colunas.DATA.value, Colunas.PNL.value]],
                    on=Colunas.DATA.value,
                    how="left"
                )
            
            else:
                raise ValueError("Ativo não mapeado.")

            df_posicao = retornos_posicao[[
                Colunas.DATA.value,
                Colunas.POSICAO.value,
                Colunas.PNL.value
            ]]

            lista_pnl_posicao.append(df_posicao)
        
        pnl_carteira = concat(lista_pnl_posicao).sort_values(Colunas.DATA.value, ascending=False).reset_index(drop=True)

        # Filtrar janela de cenários de PnL
        datas = pnl_carteira[Colunas.DATA.value].drop_duplicates().reset_index(drop=True)[:n_cenarios]
        return pnl_carteira.loc[pnl_carteira[Colunas.DATA.value].isin(datas)]
            

    @staticmethod
    def _calcular_pnl(qtd: float, preco_referencia: float, preco_cenario: Series) -> Series:
        return qtd * (preco_cenario - preco_referencia)

    def var_historico_carteira(self, n_cenarios: int, intervalo_confianca: IntervaloConfianca) -> float:
        # LEMBRANDO QUE O VAR É UM VALOR ABSOLUTO
        cenarios_pnl = self._gerar_cenarios(n_cenarios).groupby(Colunas.DATA.value).sum().reset_index()
        if self.tipo == TipoVarHistorico.SIMPLES:
            return self._calcular_var_historico(
                cenarios_pnl[Colunas.PNL.value],
                intervalo_confianca
            )
        elif self.tipo == TipoVarHistorico.BOUDOUKH:
            # Calcular pesos baseados no método de Boudoukh (mais recentes)
            pesos_brutos = array([(1-self.LAMBDA) * (self.LAMBDA)** i for i in range(len(cenarios_pnl))][::-1])
            somatorio_pesos = pesos_brutos.sum()
            pesos_normalizados = pesos_brutos / somatorio_pesos
            cenarios_pnl["peso"] = pesos_normalizados
            cenarios_pnl = cenarios_pnl.sort_values(Colunas.PNL.value, ascending=True).reset_index(drop=True)

            # Calcular VaR baseado no método de Boudoukh
            percent = 1 - (int(intervalo_confianca.name.split("P")[1])/100)
            var = float(cenarios_pnl.loc[cenarios_pnl["peso"].cumsum() >= percent][Colunas.PNL.value].min())

            return abs(var)
    
    #TODO: Implementar metodologia de cenários de TVE
    def var_historico_carteira_tve(self, n_cenarios: int, intervalo_confianca: IntervaloConfianca) -> float:
        pass
        

    @staticmethod
    def _calcular_var_historico(
        cenarios_pnl: Series, 
        intervalo_confianca: IntervaloConfianca
    ) -> float:
        ic = int(intervalo_confianca.name.split("P")[1])/100
        return float(abs(cenarios_pnl.quantile(1-ic)))
        
    
    def estresse_carteira(self, n_cenarios: int) -> float:
        cenarios_pnl = self._gerar_cenarios(n_cenarios).groupby(Colunas.DATA.value).sum().reset_index()
        return abs(float(cenarios_pnl[Colunas.PNL.value].min()))

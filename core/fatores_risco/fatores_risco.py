from datetime import date
from typing import Optional

from arch import arch_model
from numpy import array, diag, sqrt
from pandas import DataFrame, Series, concat

from core.carteira import Carteira, Posicao
from core.renda_fixa.renda_fixa import RendaFixa
from inputs.data_handler import InputsDataHandler
from utils.enums import Colunas, FatoresRisco, Localidade, TipoFuturo, Futuros, Opcoes, AcoesBr, AcoesUs


class MatrizFatoresRisco:
    def __init__(
            self, 
            carteira: Carteira, 
            inputs: InputsDataHandler, 
            lambda_: float = 0.94
    ):
        self.carteira = carteira
        self.inputs = inputs
        self.lambda_ = lambda_

    def fatores_risco_carteira(self) -> DataFrame:
        # Extrair posições
        posicoes: list[Posicao] = [p for p in self.carteira.__dict__.values() if isinstance(p, Posicao)]

        # Iterar posições para extrair dados sobre cada um dos fatores de risco
        lista_fatores_risco = []
        for p in posicoes:
            for fr in p.fatores_risco:
                # Consultar dado cru
                df = CalculosFatoresRisco.definir_variacao_fator_risco(
                        fr,
                        p.localidade,
                        self.inputs,
                        p,
                        self.lambda_,
                        self.carteira.data_referencia
                )
                
                # Definir filtro a ser utilizado sobre o dataframe de fatores de risco
                nome_serie = nomear_vetor_fator_risco(fr, p)
                if (fr == FatoresRisco.ACAO) and (isinstance(p.ativo, AcoesBr) or isinstance(p.ativo, AcoesUs)):
                    filtro = p.ativo.value
                elif (fr == FatoresRisco.ACAO) or (fr == FatoresRisco.VOLATILIDADE):
                    filtro = p.produto.value
                elif (fr == FatoresRisco.CAMBIO_USDBRL) and (len(p.fatores_risco) > 1):
                    filtro = TipoFuturo.USDBRL.name
                elif fr == FatoresRisco.JUROS:
                    df = df.drop(Colunas.VALOR.value, axis=1)
                    filtro = None
                else: 
                    filtro = p.produto.value.replace("/", "")

                # Normalizar formato
                df.columns = [Colunas.DATA.value, Colunas.ATIVO.value, Colunas.VALOR.value]
                df = df.loc[df[Colunas.ATIVO.value] == filtro] if fr != FatoresRisco.JUROS else df
                df[Colunas.ATIVO.value] = nome_serie

                lista_fatores_risco.append(df)
        
        # Produzir dataframe contendo todos os fatores de risco da carteira
        dados_fatores_risco = concat(lista_fatores_risco).drop_duplicates(subset=[Colunas.DATA.value, Colunas.ATIVO.value])

        return dados_fatores_risco.pivot(
            index=Colunas.DATA.value,
            columns=Colunas.ATIVO.value,
            values=Colunas.VALOR.value
        ).dropna()
    
    def matriz_cov_ewma(self, lambda_: float = 0.94):
        # Inicializa com a covariância amostral
        retornos = self.fatores_risco_carteira()
        cov_ewma = retornos.cov()
        for i in range(1, len(retornos)):
            r_t = retornos.iloc[i].values.reshape(-1, 1)
            cov_ewma = lambda_ * cov_ewma + (1 - lambda_) * (r_t @ r_t.T)
        return DataFrame(cov_ewma, index=retornos.columns, columns=retornos.columns)

    def matriz_cov_garch(self) -> DataFrame:
        df_retornos = self.fatores_risco_carteira()
        modelos_garch = {}
        volatilidades = {}

        for coluna in df_retornos.columns:
            serie = df_retornos[coluna].dropna()
            modelo = arch_model(serie, vol='Garch', p=1, q=1)
            resultado = modelo.fit(disp="off")
            modelos_garch[coluna] = resultado

            # Extrai volatilidade condicional estimada
            volatilidades[coluna] = resultado.conditional_volatility

        # Usar correlação empírica entre retornos (últimos N dias)
        corr_matrix = df_retornos.corr()

        # Pegar as últimas volatilidades estimadas (último valor de cada série)
        vols_hoje = {k: v.iloc[-1] for k, v in volatilidades.items()}

        # Criar matriz de volatilidades
        vol_array = array([vols_hoje[col] for col in df_retornos.columns])
        vol_matrix = diag(vol_array)

        # Covariância = Corr * Vol_i * Vol_j
        cov_garch = vol_matrix @ corr_matrix.values @ vol_matrix

        # Montar DataFrame da matriz final
        return DataFrame(cov_garch, index=df_retornos.columns, columns=df_retornos.columns)


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
        if fator_risco in [FatoresRisco.ACAO, FatoresRisco.CAMBIO_USDBRL, FatoresRisco.CAMBIO_USDOUTROS]:
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
    def ewma_recursivo(cls, coluna_ewma: Series, serie_fator_risco: Series, lambda_: float = 0.94) -> Series:
        return lambda_ * coluna_ewma.shift(1).fillna(0) + (1 - lambda_) * serie_fator_risco
    
    @classmethod
    def ewma_unitario(cls, valor_calculado: float, valor_fator_risco: float, lambda_: float = 0.94) -> float:
        return lambda_ * valor_calculado + (1 - lambda_) * valor_fator_risco

    @classmethod
    def variancia_ewma(cls, df: DataFrame, agrupar_por: Colunas, lambda_: float = 0.94, eh_serie_unica: bool = False) -> DataFrame:
        # Validar valor do lambda
        assert lambda_ >= 0 and lambda_ <= 1, "Parâmetro lambda fora do domínio (entre 0 e 1)."

        # Iniciar modelo
        df[Colunas.VARIANCIA_EWMA.value] = 0.0
        df = df.sort_values([Colunas.ATIVO.value, Colunas.DATA.value]).reset_index(drop=True)
        datas = df.sort_values(Colunas.DATA.value)[Colunas.DATA.value].drop_duplicates()
        for data in datas:
            ids = df.loc[df[Colunas.DATA.value] == data].index

            # Efetuar cálculo de variância seguindo modelo EWMA
            calc_ewma_df = (
                df.groupby(agrupar_por.value)
                  .apply(lambda group: cls.ewma_recursivo(
                      group[Colunas.VARIANCIA_EWMA.value], pow(group[Colunas.VARIACAO.value], 2), lambda_
                  ))
                  .reset_index()
            )
            if eh_serie_unica:
                calc_ewma = calc_ewma_df.filter(items=ids, axis=1)[ids.to_list()[0]][0]
            else:
                calc_ewma = calc_ewma_df.filter(items=ids, axis=0)[0]

            df.loc[df[Colunas.DATA.value] == data, Colunas.VARIANCIA_EWMA.value] = calc_ewma
            
        return df

    
    @classmethod
    def definir_variacao_fator_risco(
        cls,
        fator_risco: FatoresRisco,
        localidade: Localidade,
        inputs: InputsDataHandler,
        posicao: Optional[Posicao] = None,
        lambda_: float = 0.94,
        data_referencia: Optional[date] = None
    ) -> DataFrame:
        # Checar se posição é fornecida para o caso de fator de risco de juros
        assert (fator_risco != FatoresRisco.JUROS) or ((fator_risco == FatoresRisco.JUROS) and posicao and data_referencia), "Posição e data de referência devem ser fornecida para o fator de risco de juros."
        assert localidade in [Localidade.BR, Localidade.US], "Localidade desconhecida"

        # Retornar variação do fator de risco, considerando a localidade
        if fator_risco in [FatoresRisco.ACAO, FatoresRisco.VOLATILIDADE]:
            df = inputs.acoes_br() if localidade == Localidade.BR else inputs.acoes_us()
            colunas = [
                Colunas.DATA.value,
                Colunas.ATIVO.value,
                Colunas.VARIACAO.value
            ]
            retorno = cls.calcular_variacao(df, FatoresRisco.ACAO, Colunas.ATIVO, Colunas.PRECO)
            if fator_risco == FatoresRisco.VOLATILIDADE:
                return cls.calcular_variacao(
                    cls.calcular_volatilidade(
                        retorno,
                        localidade,
                        lambda_
                    ).sort_values(Colunas.DATA.value, ascending=False),
                    fator_risco,
                    Colunas.ATIVO,
                    Colunas.VOLATILIDADE
                )[colunas]
            else:
                return retorno[colunas]
        elif fator_risco == FatoresRisco.JUROS:
            df = RendaFixa(
                data_referencia,
                posicao.vencimento,
                localidade,
                inputs,
                posicao.cupom,
                posicao.taxa
            ).curva_juros()
            return cls.calcular_variacao(df, fator_risco, Colunas.PRAZO, Colunas.VALOR)
        elif fator_risco in [FatoresRisco.CAMBIO_USDBRL, FatoresRisco.CAMBIO_USDOUTROS]:
            df = inputs.fx()
            colunas = [
                Colunas.DATA.value,
                Colunas.CAMBIO.value,
                Colunas.VARIACAO.value
            ]
            return cls.calcular_variacao(df, fator_risco, Colunas.CAMBIO, Colunas.VALOR)[colunas]
        else:
            raise ValueError("Fator de risco inválido.")

def nomear_vetor_fator_risco(fr: FatoresRisco, p: Posicao) -> str:
    if (fr == FatoresRisco.ACAO) and isinstance(p.ativo, Opcoes):
        return p.produto.name
    elif (fr == FatoresRisco.ACAO) and not isinstance(p.ativo, Futuros):
        return p.ativo.name
    elif fr == FatoresRisco.VOLATILIDADE:
        return f"{p.produto.name}_VOL"
    elif (fr == FatoresRisco.CAMBIO_USDBRL) and (len(p.fatores_risco) > 1):
        return TipoFuturo.USDBRL.name
    else: 
        return p.produto.name

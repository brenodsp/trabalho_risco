from datetime import date
from typing import Optional, Union

from pandas import DataFrame, Timestamp, date_range, to_datetime

from inputs.data_handler import InputsDataHandler
from utils.enums import Colunas, Localidade


class RendaFixa:
    VALOR_FACE = 1000

    def __init__(
            self, 
            data_referencia: date, 
            vencimento: date,
            localidade: Localidade,
            inputs_data_handler: InputsDataHandler,
            cupom: Optional[float] = None,
            taxa: Optional[float] = None
    ):
        self.data_referencia = to_datetime(data_referencia)
        self.vencimento = to_datetime(vencimento)
        self.cupom = cupom
        self.taxa = taxa
        self.localidade = localidade
        self.inputs_data_handler = inputs_data_handler

    @property
    def periodo(self) -> Union[int, str]:
        # Não fazer o cálculo de DU em caso de renda fixa americana
        if self.localidade == Localidade.BR:
            return self.calcular_du(self.data_referencia, self.vencimento, self.inputs_data_handler)
        elif self.localidade == Localidade.US:
            return self._definir_vertice_treasury()
        else:
            raise ValueError("Localidade desconhecida.")
        
    @classmethod
    def calcular_du(cls, data_referencia: Timestamp, vencimento: Timestamp, inputs: InputsDataHandler) -> int:
        # Carregar dados de feriados, filtrar datas e criar coluna de validação de feriado
        feriados = inputs.feriados()
        feriados = feriados.loc[
            (feriados[Colunas.DATA.value] >= data_referencia) & 
            (feriados[Colunas.DATA.value] <= vencimento)
        ]

        feriados = feriados.assign(eh_feriado=True)[[Colunas.DATA.value, "eh_feriado"]]

        # Criar DataFrame com horizonte completo de dias da data de referência até o vencimento
        dias_corridos = date_range(data_referencia, vencimento)

        # Juntar filtrar feriados e finais de semana
        feriados[Colunas.DATA.value] = to_datetime(feriados[Colunas.DATA.value])
        dias_uteis = DataFrame(dias_corridos, columns=[Colunas.DATA.value])\
                     .merge(feriados, on=[Colunas.DATA.value], how="left")\
                     .assign(
                        eh_feriado=lambda df: df["eh_feriado"].fillna(False).astype(bool),
                        dia_semana=lambda df: df[Colunas.DATA.value].dt.day_of_week
                     )
        
        dias_uteis = dias_uteis.loc[
            (dias_uteis["eh_feriado"] == False) &
            ~(dias_uteis["dia_semana"].isin([5, 6]))
        ]

        # Contar número de dias e desconsiderar o dia de referência
        return dias_uteis.index.__len__() - 1
    
    def _definir_vertice_treasury(self) -> str:
        # Calcular diferença, em anos, entre a data de referência e o vencimento
        delta_anos = (self.vencimento - self.data_referencia).days / 365

        # Carregar produtos Treasury
        treasuries = self.inputs_data_handler.treasury()[Colunas.PRAZO.value].drop_duplicates().to_list()
        treasuries = {
            t: int(t.replace("Y", "")) 
            if "Y" in t 
            else int(t.replace("M", ""))/12
            for t in treasuries 
        }

        # Identificar produto cujo vértice é mais significativo
        return min(treasuries, key=lambda k: abs(treasuries[k] - delta_anos))

    def curva_juros(self) -> DataFrame:
        if self.localidade == Localidade.US:
            df = self.inputs_data_handler.treasury()
            df = df.loc[df[Colunas.PRAZO.value] == self.periodo]
            return df
        elif self.localidade == Localidade.BR:
            return self._definir_curva_di()
        else:
            ValueError("Localidade desconhecida.")
    
    def _definir_curva_di(self) -> DataFrame:
        # Carregar curvas DI
        di = self.inputs_data_handler.di()

        # Checar se existe algum produto com o mesmo du calculado e entregar curva específica, se houver
        du = self.periodo
        if du in di[Colunas.PRAZO.value].drop_duplicates().to_list():
            return di.loc[di[Colunas.PRAZO.value] == du]
        
        # Caso contrário, calcular curva interpolada
        vertice_inferior = di[Colunas.PRAZO.value].drop_duplicates().loc[di[Colunas.PRAZO.value] < du].max()
        vertice_superior = di[Colunas.PRAZO.value].drop_duplicates().loc[di[Colunas.PRAZO.value] > du].min()
        fator_multiplicador = (du - vertice_inferior)/(vertice_superior - vertice_inferior)

        interpol_df = (
            di.loc[di[Colunas.PRAZO.value].isin([vertice_inferior, vertice_superior])]
              .dropna()
              .pivot(index=Colunas.DATA.value, columns=Colunas.PRAZO.value, values=Colunas.VALOR.value)
        )
        interpol_df[du] = interpol_df[vertice_inferior] + \
                          fator_multiplicador * (interpol_df[vertice_superior] - interpol_df[vertice_inferior])
        
        return (
            interpol_df.reset_index()
                       .melt(
                           id_vars=Colunas.DATA.value, 
                           value_vars=du, 
                           var_name=Colunas.PRAZO.value,
                           value_name=Colunas.VALOR.value
                       )
        )

    def pu(self) -> float:
        # TODO: talvez implementar depois método para juros BR
        if self.localidade == Localidade.BR:
            return None
        
        # TODO: condicionar lógica à localidade em caso de posterior aplicação da regra BR 
        dias_totais = (self.vencimento - self.data_referencia).days

        # ASSUMINDO PAGAMENTO DE CUPOM SEMESTRAL
        valor_cupom, taxa, total_periodos = self._base_semestral(self.VALOR_FACE, self.cupom/100, self.taxa/100, dias_totais)

        # Calcular soma dos VPLs dos fluxos de caixa de cupons
        vpl_cupons = sum([self._vpl(valor_cupom, taxa, t) for t in range(1, total_periodos + 1)])

        # Calcular VPL da curva
        vpl_curva = self._vpl(self.VALOR_FACE, taxa, total_periodos)

        return vpl_cupons + vpl_curva

    def duration_modificada(self) -> float:
        return self._duration() / (1 + self.taxa/100)

    def _duration(self) -> float:
        if self.localidade == Localidade.BR:
            return self.periodo / 252
        elif self.localidade == Localidade.US:
            # EMPREGANDO LÓGICA SEMESTRAL
            dias_totais = (self.vencimento - self.data_referencia).days
            valor_cupom, taxa, total_periodos = self._base_semestral(self.VALOR_FACE, self.cupom/100, self.taxa/100, dias_totais)

            # Calcular VPL dos fluxos de caixa dos cupons
            vpl_cupons = sum([self._vpl(valor_cupom, taxa, t) for t in range(1, total_periodos + 1)])

            # Calcular VPL dos fluxos de caixa dos cupons ponderado pelo tempo
            vpl_cupons_ponderado = sum([self._vpl(valor_cupom, taxa, t) * t for t in range(1, total_periodos + 1)])

            return (vpl_cupons_ponderado / vpl_cupons) / 2 # Dividir por 2 para encontrar base anual
        else:
            raise ValueError("Localidade inválida.")

    @staticmethod
    def _vpl(valor_base: float, taxa: float, periodo: float) -> float:
        assert (taxa > 0) and (taxa <= 1), "Taxa muito alta. Checar se valor inserido foi nominal ao invés de percentual."
        return valor_base / ((1 + taxa) ** periodo)

    @staticmethod
    def _base_semestral(
            valor_face: float,
            cupom_anual: float,
            taxa_anual: float,
            dias_totais: float
    ) -> tuple[float, float, float]:
         valor_cupom_semestral = (valor_face * (cupom_anual/100))/2 # Cupom é valor anual, então divide-se por dois para encontrar o semestral
         taxa_semestral = taxa_anual / 2 # Dividir por 2 para transformar anual em semestral
         total_periodos = (dias_totais / 180).__floor__() # Dividir por 180 dias para determinar o número de semestres
         return valor_cupom_semestral, taxa_semestral, total_periodos
        
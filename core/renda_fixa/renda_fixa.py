from datetime import date
from typing import Optional, Union

from pandas import DataFrame, date_range, to_datetime

from inputs.data_handler import InputsDataHandler
from utils.enums import Colunas, Localidade


class RendaFixa:
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
            return self._calcular_du()
        elif self.localidade == Localidade.US:
            return self._definir_vertice_treasury()
        else:
            raise ValueError("Localidade desconhecida.")
        
    def _calcular_du(self) -> int:
        # Carregar dados de feriados, filtrar datas e criar coluna de validação de feriado
        feriados = self.inputs_data_handler.feriados()
        feriados = feriados.loc[
            (feriados[Colunas.DATA.value] >= self.data_referencia) & 
            (feriados[Colunas.DATA.value] <= self.vencimento)
        ]

        feriados = feriados.assign(eh_feriado=True)[[Colunas.DATA.value, "eh_feriado"]]

        # Criar DataFrame com horizonte completo de dias da data de referência até o vencimento
        dias_corridos = date_range(self.data_referencia, self.vencimento)

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
        delta_anos = (self.vencimento - self.data_referencia).days / 360

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


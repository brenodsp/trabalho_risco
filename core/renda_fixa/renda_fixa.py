from datetime import date
from typing import Optional

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
        self.data_referencia = data_referencia
        self.vencimento = vencimento
        self.cupom = cupom
        self.taxa = taxa
        self.localidade = localidade
        self.inputs_data_handler = inputs_data_handler
        self._calcular_du()

    def _calcular_du(self) -> None:
        # Não fazer o cálculo de DU em caso de renda fixa americana
        if self.localidade == Localidade.US:
            return None
        
        # Carregar dados de feriados, filtrar datas e criar coluna de validação de feriado
        feriados = self.inputs_data_handler.feriados()
        feriados = feriados.loc[
            (feriados[Colunas.DATA.value] >= to_datetime(self.data_referencia)) & 
            (feriados[Colunas.DATA.value] <= to_datetime(self.vencimento))
        ]

        feriados = feriados.assign(eh_feriado=True)[[Colunas.DATA.value, "eh_feriado"]]

        # Criar DataFrame com horizonte completo de dias da data de referência até o vencimento
        dias_corridos = date_range(to_datetime(self.data_referencia), to_datetime(self.vencimento))

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
        self.du = dias_uteis.index.__len__() - 1

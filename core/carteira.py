from datetime import date
from typing import Optional, Union

from inputs.data_handler import InputsDataHandler
from utils.enums import AcoesBr, AcoesUs, Opcoes, Titulos, Futuros, TipoFuturo, FatoresRisco, Localidade, definir_tipo_futuro


class Posicao:
    def __init__(
            self, 
            ativo: Union[AcoesBr, AcoesUs, Opcoes, Titulos, Futuros], 
            quantidade: float,
            inputs_data_handler: Optional[InputsDataHandler] = None
    ):
        self.ativo = ativo
        self.quantidade = quantidade
        self.gerar_informacao_adicional(inputs_data_handler)

    def gerar_informacao_adicional(self, inputs_data_handler: Optional[InputsDataHandler]) -> None:
        # Forçar necessidade de prover inputs para certos ativos
        assert (
            ((isinstance(self.ativo, Futuros) or isinstance(self.ativo, Titulos)) and inputs_data_handler) or
            not (isinstance(self.ativo, Futuros) or isinstance(self.ativo, Titulos))
        ), f"Informações adicionais são necessárias para o tipo de ativo: {self.ativo.name}, mas inputs não foram fornecidos."
        
        # Extrair informações adicionais
        if isinstance(self.ativo, Futuros):
            df = inputs_data_handler.futuros()
            tipo_futuro = df[df["id"] == self.ativo.value]["tipo"].values[0]
            self.tipo_futuro = definir_tipo_futuro(tipo_futuro)
        elif isinstance(self.ativo, Titulos):
            df = inputs_data_handler.titulos()
            self.tipo_titulo = df[df["id"] == self.ativo.value]["tipo"].values[0]

    @property
    def localidade(self) -> Localidade:
        if (not isinstance(self.ativo, AcoesUs)) and (not isinstance(self.ativo, Titulos)):
            return Localidade.BR
        elif isinstance(self.ativo, Titulos) and "Note" not in self.tipo_titulo:
            return Localidade.BR
        else:
            return Localidade.US

    @property
    def fatores_risco(self) -> tuple[FatoresRisco]:
        adicional_cambio = (FatoresRisco.CAMBIO,) if self.localidade == Localidade.US else ()
        if isinstance(self.ativo, Union[AcoesBr, AcoesUs]):
            fatores_risco = FatoresRisco.ACAO,
        elif isinstance(self.ativo, Opcoes):
            fatores_risco = FatoresRisco.ACAO, FatoresRisco.VOLATILIDADE
        elif isinstance(self.ativo, Titulos):
            fatores_risco = FatoresRisco.JUROS,
        elif isinstance(self.ativo, Futuros):
            if self.tipo_futuro == TipoFuturo.CAMBIO:
                fatores_risco = FatoresRisco.CAMBIO,
            elif self.tipo_futuro == TipoFuturo.DI:
                fatores_risco = FatoresRisco.JUROS,
            elif self.tipo_futuro == TipoFuturo.INDICE:
                fatores_risco = FatoresRisco.ACAO,
            else:
                raise ValueError("Fator de risco desconhecido para o respectivo ativo.")    
        else:
            raise ValueError("Fator de risco desconhecido para o respectivo ativo.")
        
        return tuple(set(fatores_risco + adicional_cambio))
        

class Carteira:
    DATA_REFERENCIA = date(2025, 5, 26)

    def __init__(self, inputs_data_handler: InputsDataHandler):
        self.POSICAO_1 = Posicao(AcoesBr.EMBRAER, 1500)
        self.POSICAO_2 = Posicao(AcoesBr.CASAS_BAHIA, 24500)
        self.POSICAO_3 = Posicao(AcoesUs.FORD_MOTORS, 1700)
        self.POSICAO_4 = Posicao(Opcoes.OPCAO_9, 1.5)
        self.POSICAO_5 = Posicao(Futuros.FUTURO_15, 0.6, inputs_data_handler)
        self.POSICAO_6 = Posicao(Futuros.FUTURO_9, 0.2, inputs_data_handler)
        self.POSICAO_7 = Posicao(Futuros.FUTURO_25, 1700, inputs_data_handler)
        self.POSICAO_8 = Posicao(Titulos.TITULO_9, 250000, inputs_data_handler)

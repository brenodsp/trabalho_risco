from typing import Optional, Union

from inputs.data_handler import InputsDataHandler
from utils.enums import AcoesBr, AcoesUs, Opcoes, Titulos, Futuros, TipoFuturo, FatoresRisco, definir_tipo_futuro


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
        if isinstance(self.ativo, Futuros) and not inputs_data_handler:
            raise ValueError("Informações adicionais são necessárias, mas inputs não foram fornecidos.")
        
        # Extrair informações adicionais
        if isinstance(self.ativo, Futuros):
            df = inputs_data_handler.futuros()
            tipo_futuro = df[df["id"] == self.ativo.value]["tipo"].values[0]
            self.tipo_futuro = definir_tipo_futuro(tipo_futuro)

    @property
    def fatores_risco(self) -> tuple[FatoresRisco]:
        if isinstance(self.ativo, Union[AcoesBr, AcoesUs]):
            return FatoresRisco.ACAO,
        elif isinstance(self.ativo, Opcoes):
            return FatoresRisco.OPCAO_S, FatoresRisco.OPCAO_VOL
        elif isinstance(self.ativo, Titulos):
            return FatoresRisco.JUROS,
        elif isinstance(self.ativo, Futuros):
            if self.tipo_futuro == TipoFuturo.CAMBIO:
                return FatoresRisco.CAMBIO,
            elif self.tipo_futuro == TipoFuturo.DI:
                return FatoresRisco.JUROS,
            elif self.tipo_futuro == TipoFuturo.INDICE:
                return FatoresRisco.ACAO,
            else:
                raise ValueError("Fator de risco desconhecido para o respectivo ativo.")    
        else:
            raise ValueError("Fator de risco desconhecido para o respectivo ativo.")    
        

class Carteira:
    def __init__(self, inputs_data_handler: InputsDataHandler):
        self.POSICAO_1 = Posicao(AcoesBr.EMBRAER, 1500)
        self.POSICAO_2 = Posicao(AcoesBr.CASAS_BAHIA, 24500)
        self.POSICAO_3 = Posicao(AcoesUs.FORD_MOTORS, 1700)
        self.POSICAO_4 = Posicao(Opcoes.OPCAO_9, 1.5)
        self.POSICAO_5 = Posicao(Futuros.FUTURO_15, 0.6, inputs_data_handler)
        self.POSICAO_6 = Posicao(Futuros.FUTURO_9, 0.2, inputs_data_handler)
        self.POSICAO_7 = Posicao(Futuros.FUTURO_25, 1700, inputs_data_handler)
        self.POSICAO_8 = Posicao(Titulos.TITULO_9, 250000)

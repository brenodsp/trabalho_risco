from datetime import date
from typing import Union

from inputs.data_handler import InputsDataHandler
from utils.enums import Colunas, AcoesBr, AcoesUs, Opcoes, Titulos, Futuros, TipoFuturo, TipoTitulo, FatoresRisco, Localidade, \
                        definir_tipo_futuro, definir_produto_opcao, definir_tipo_titulo


class Posicao:
    def __init__(
            self, 
            ativo: Union[AcoesBr, AcoesUs, Opcoes, Titulos, Futuros], 
            quantidade: float,
            inputs_data_handler: InputsDataHandler
    ):
        self.ativo = ativo
        self.quantidade = quantidade
        self._gerar_informacao_adicional(inputs_data_handler)
        self._gerar_informacao_juros(inputs_data_handler)

    def _gerar_informacao_adicional(self, inputs_data_handler: InputsDataHandler) -> None:
        # Extrair informações adicionais sobre futuros, títulos e opções
        if isinstance(self.ativo, Futuros):
            df = inputs_data_handler.futuros()
            tipo_futuro = df[df["id"] == self.ativo.value]["tipo"].values[0]
            self.produto = definir_tipo_futuro(tipo_futuro)
        elif isinstance(self.ativo, Titulos):
            df = inputs_data_handler.titulos()
            produto = df[df["id"] == self.ativo.value]["tipo"].values[0]
            self.produto = definir_tipo_titulo(produto)
        elif isinstance(self.ativo, Opcoes):
            df = inputs_data_handler.opcoes()
            produto = df[df["id"] == self.ativo.value]["underlying"].values[0]
            self.produto = definir_produto_opcao(produto)

    def _gerar_informacao_juros(self, inputs_data_handler: InputsDataHandler) -> None:
        # Não implementado para posições sem a presença de juros como fator de risco
        if FatoresRisco.JUROS not in self.fatores_risco:
            return None
        
        # Extrair informações necessárias dependendo do tipo de fonte
        if isinstance(self.ativo, Titulos):
            df = inputs_data_handler.titulos()
            df = df.loc[df[Colunas.ID.value] == self.ativo.value]
            self.vencimento = df[Colunas.VENCIMENTO.value].values[0]
            self.cupom = df["cupom"].values[0]
            self.taxa = df["taxa"].values[0]

        elif isinstance(self.ativo, Futuros):
            df = inputs_data_handler.futuros()
            df = df.loc[df[Colunas.ID.value] == self.ativo.value]
            self.vencimento = df[Colunas.VENCIMENTO.value].values[0]
            self.cupom = None
            self.taxa = None
        

    @property
    def localidade(self) -> Localidade:
        if (not isinstance(self.ativo, AcoesUs)) and (not isinstance(self.ativo, Titulos)):
            return Localidade.BR
        elif isinstance(self.ativo, Titulos) and not self.produto == TipoTitulo.TREASURY:
            return Localidade.BR
        else:
            return Localidade.US

    @property
    def fatores_risco(self) -> tuple[FatoresRisco]:
        adicional_cambio = (FatoresRisco.CAMBIO_USDBRL,) if self.localidade == Localidade.US else ()
        if isinstance(self.ativo, Union[AcoesBr, AcoesUs]):
            fatores_risco = FatoresRisco.ACAO,
        elif isinstance(self.ativo, Opcoes):
            fatores_risco = FatoresRisco.ACAO, FatoresRisco.VOLATILIDADE
        elif isinstance(self.ativo, Titulos):
            fatores_risco = FatoresRisco.JUROS,
        elif isinstance(self.ativo, Futuros):
            if self.produto == TipoFuturo.USDBRL:
                fatores_risco = FatoresRisco.CAMBIO_USDBRL,
            if self.produto in [TipoFuturo.EURUSD, TipoFuturo.USDCAD, TipoFuturo.USDJPY, TipoFuturo.USDMXN]:
                fatores_risco = FatoresRisco.CAMBIO_USDOUTROS, FatoresRisco.CAMBIO_USDBRL,
            elif self.produto == TipoFuturo.DI:
                fatores_risco = FatoresRisco.JUROS,
            elif self.produto == TipoFuturo.IBOV:
                fatores_risco = FatoresRisco.ACAO,
            else:
                raise ValueError("Fator de risco desconhecido para o respectivo ativo.")    
        else:
            raise ValueError("Fator de risco desconhecido para o respectivo ativo.")
        
        return tuple(set(fatores_risco + adicional_cambio))
        

class Carteira:
    def __init__(self, posicoes: list[Posicao], data_referencia: date):
        self.data_referencia = data_referencia
        
        for i, posicao in enumerate(posicoes, start=1):
            atributo = f"POSICAO_{i}"
            setattr(self, atributo, posicao)

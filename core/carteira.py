from typing import Union

from utils.enums import AcoesBr, AcoesUs, Opcoes, Titulos, Futuros


class Posicao:
    def __init__(self, ativo: Union[AcoesBr, AcoesUs, Opcoes, Titulos, Futuros], quantidade: float):
        self.ativo = ativo,
        self.quantidade = quantidade


class Carteira:
    POSICAO_1 = Posicao(AcoesBr.EMBRAER, 1500)
    POSICAO_2 = Posicao(AcoesBr.CASAS_BAHIA, 24500)
    POSICAO_3 = Posicao(AcoesUs.FORD_MOTORS, 1700)
    POSICAO_4 = Posicao(Opcoes.OPCAO_9, 1.5)
    POSICAO_5 = Posicao(Futuros.FUTURO_15, 0.6)
    POSICAO_6 = Posicao(Futuros.FUTURO_9, 0.2)
    POSICAO_7 = Posicao(Futuros.FUTURO_25, 1700)
    POSICAO_8 = Posicao(Titulos.TITULO_9, 250000)

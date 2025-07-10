from datetime import date, datetime

from core.carteira import Carteira, Posicao
from inputs.data_handler import InputsDataHandler
from core.fatores_risco.fatores_risco import CalculosFatoresRisco, MatrizFatoresRisco
from core.renda_fixa.renda_fixa import RendaFixa
from utils.enums import IntervaloConfianca, FatoresRisco, Colunas, Localidade, AcoesBr, AcoesUs, Opcoes, Futuros, Titulos

# Pegar inputs
data_handler = InputsDataHandler()

# Definir posições da carteira
posicoes_canonicas = [
    Posicao(AcoesBr.EMBRAER, 1500, data_handler),
    Posicao(AcoesBr.CASAS_BAHIA, 24500, data_handler),
    Posicao(AcoesUs.FORD_MOTORS, 1700, data_handler),
    Posicao(Opcoes.OPCAO_9, 1.5, data_handler),
    Posicao(Futuros.FUTURO_15, 0.6, data_handler),
    Posicao(Futuros.FUTURO_9, 0.2, data_handler),
    Posicao(Futuros.FUTURO_25, 1700, data_handler),
    Posicao(Titulos.TITULO_9, 250000, data_handler)
]

carteira_canonica = Carteira(posicoes_canonicas)

# Questões
## a
print(f"[{datetime.now()}] Solucionando questão a)")
a = {
    p: [f.name for f in carteira.__getattribute__(p).fatores_risco]
    for p in carteira.__dict__
}

## b
fatores_risco = MatrizFatoresRisco(carteira, data_handler)

print(f"[{datetime.now()}] Solucionando questão b)")
b = fatores_risco.matriz_cov_ewma()

## c
print(f"[{datetime.now()}] Solucionando questão b)")
c = fatores_risco.matriz_cov_garch()

from datetime import date, datetime

from core.carteira import Carteira, Posicao
from core.var.var import VarParametrico, VarHistorico
from inputs.data_handler import InputsDataHandler
from core.fatores_risco.exposicao import ExposicaoCarteira
from core.fatores_risco.fatores_risco import MatrizFatoresRisco
from core.renda_fixa.renda_fixa import RendaFixa
from utils.enums import IntervaloConfianca, AcoesBr, AcoesUs, Opcoes, Futuros, Titulos

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
    Posicao(Futuros.FUTURO_25, 17, data_handler),
    Posicao(Titulos.TITULO_9, 25, data_handler)
]

carteira_canonica = Carteira(posicoes_canonicas, date(2025, 5, 26))
# teste = VarHistorico(
#     carteira_canonica,
#     MatrizFatoresRisco(carteira_canonica, data_handler),
#     data_handler
# ).var_historico_carteira(500, IntervaloConfianca.P99)


# Questões
## a
# print(f"[{datetime.now()}] Solucionando questão a)")
# a = {
#     p: [f.name for f in carteira_canonica.__getattribute__(p).fatores_risco]
#     for p in carteira_canonica.__dict__
#     if "POSICAO" in p
# }

## b
fatores_risco = MatrizFatoresRisco(carteira_canonica, data_handler)

print(f"[{datetime.now()}] Solucionando questão b)")
# b = fatores_risco.matriz_cov_ewma()

## c
print(f"[{datetime.now()}] Solucionando questão c)")
# c = fatores_risco.matriz_cov_garch()

## d
print(f"[{datetime.now()}] Solucionando questão d)")
calculadora_var_parametrico = VarParametrico(
    carteira_canonica,
    ExposicaoCarteira(carteira_canonica, data_handler),
    fatores_risco,
    IntervaloConfianca.P99
).var_parametrico_posicao()

d = {
    p: calculadora_var_parametrico.var_parametrico_posicao(
        carteira_canonica.__getattribute__(p), 
        carteira_canonica.data_referencia,
        data_handler
        )
    for p in carteira_canonica.__dict__
    if "POSICAO" in p
}

## e
print(f"[{datetime.now()}] Solucionando questão e)")
e = calculadora_var_parametrico.var_parametrico_carteira()

## h
h = {
    posicao: f"{round(d[posicao]/e, 6)}%"
    for posicao in d
}

## i
print(f"[{datetime.now()}] Solucionando questão i)")
i = 0

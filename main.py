from datetime import date, datetime

from core.carteira import Carteira
from inputs.data_handler import InputsDataHandler
from core.fatores_risco.fatores_risco import CalculosFatoresRisco, MatrizFatoresRisco
from core.renda_fixa.renda_fixa import RendaFixa
from utils.enums import IntervaloConfianca, FatoresRisco, Colunas, Localidade

# Pegar inputs
data_handler = InputsDataHandler()
carteira = Carteira(data_handler)

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

from core.carteira import Carteira
from inputs.data_handler import InputsDataHandler
from core.fatores_risco.fatores_risco import CalculosFatoresRisco, MatrizFatoresRisco
from utils.enums import IntervaloConfianca, FatoresRisco, Colunas, Localidade

# Pegar inputs
data_handler = InputsDataHandler()
carteira = Carteira(data_handler)

# Questões
## a
a = {
    p: [f.name for f in carteira.__getattribute__(p).fatores_risco]
    for p in carteira.__dict__
}

## b
fatores_risco = MatrizFatoresRisco(carteira, data_handler)

b = fatores_risco.matriz_cov_ewma()

## c
teste = 0
# cov_ewma = fatores_risco.cov()

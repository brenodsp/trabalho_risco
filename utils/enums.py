from enum import Enum, auto

class Indices(Enum):
    ATIVO = "ativo"
    CAMBIO = "cambio"
    DATA = "data"
    PRAZO = "prazo"
    PRECO = "preco"
    VALOR = "valor"

class AcoesBr(Enum):
    IBOVESPA = "IBOV"
    AMBEV = "AMBV3"
    BANCO_DO_BRASIL = "BBAS3"
    B3 = "B3SA3"
    BRADESCO = "BBDC4"
    BRASKEM = "BRKM5"
    BRF = "BRFS3"
    CMIG = "CMIG4"
    CSN = "CSNA3"
    EMBRAER = "EMBR3"
    GERDAU = "GOAU4"
    ITAU = "ITUB4"
    MAGAZINE_LUIZA = "MGLU3"
    MARFRIG = "MRFG3"
    LOJAS_RENNER = "LREN3"
    PETROBRAS = "PETR4"
    PRIO = "PRIO3"
    SUZANO = "SUZB3"
    VALE = "VALE3"
    CASAS_BAHIA = "BHIA3"

class AcoesUs(Enum):
    ALCOA = "AA"
    AMAZON = "AMZN"
    APPLE = "AAPL"
    ATnT = "T"
    BANK_OF_AMERICA = "BAC"
    GOOGLE = "GOOGL"
    INTEL = "INTC"
    MICROSOFT = "MSFT"
    FORD_MOTORS = "F"
    TESLA = "TSLA"


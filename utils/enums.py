from enum import Enum, auto

class Colunas(Enum):
    ATIVO = "ativo"
    CAMBIO = "cambio"
    DATA = "data"
    DELTA = "delta"
    ID = "id"
    PRAZO = "prazo"
    PRECO = "preco"
    RETORNO = "retorno"
    TIPO = "tipo"
    VALOR = "valor"
    VARIACAO = "variacao"
    VARIANCIA_EWMA = "variancia_ewma"
    VENCIMENTO = "vencimento"
    VOLATILIDADE = "volatilidade"

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

class Opcoes(Enum):
    OPCAO_1 = "Opção 1"
    OPCAO_2 = "Opção 2"
    OPCAO_3 = "Opção 3"
    OPCAO_4 = "Opção 4"
    OPCAO_5 = "Opção 5"
    OPCAO_6 = "Opção 6"
    OPCAO_7 = "Opção 7"
    OPCAO_8 = "Opção 8"
    OPCAO_9 = "Opção 9"
    OPCAO_10 = "Opção 10"
    OPCAO_11 = "Opção 11"
    OPCAO_12 = "Opção 12"
    OPCAO_13 = "Opção 13"
    OPCAO_14 = "Opção 14"

class ProdutosOpcoes(Enum):
    ABEV3 = "AMBV3"
    IBOVE = "IBOV"
    O_B3SA3 = "B3SA3"
    O_BBDC4 = "BBDC4"
    O_LREN3 = "LREN3"
    O_PETR4 = "PETR4"
    O_VALE3 = "VALE3"

def definir_produto_opcao(produto: str) -> ProdutosOpcoes:
    resultado = [n for n in ProdutosOpcoes._member_names_ if produto in n]
    assert len(resultado) != 0, "Produto não encontrado."
    assert len(resultado) == 1, "Produto ambíguo."
    return ProdutosOpcoes[resultado[0]]

class Titulos(Enum):
    TITULO_1 = "Título 1"
    TITULO_2 = "Título 2"
    TITULO_3 = "Título 3"
    TITULO_4 = "Título 4"
    TITULO_5 = "Título 5"
    TITULO_6 = "Título 6"
    TITULO_7 = "Título 7"
    TITULO_8 = "Título 8"
    TITULO_9 = "Título 9"
    TITULO_10 = "Título 10"

class TipoTitulo(Enum):
    NTNB = "NTN-B"
    NTNF = "NTN-F"
    TREASURY = "Teasury Note"

def definir_tipo_titulo(tipo: str) -> TipoTitulo:
    try:
        return TipoTitulo._value2member_map_[tipo]
    except:
        raise ValueError("Produto não encontrado.")

class Futuros(Enum):
    FUTURO_1 = "Futuro 1"
    FUTURO_2 = "Futuro 2"
    FUTURO_3 = "Futuro 3"
    FUTURO_4 = "Futuro 4"
    FUTURO_5 = "Futuro 5"
    FUTURO_6 = "Futuro 6"
    FUTURO_7 = "Futuro 7"
    FUTURO_8 = "Futuro 8"
    FUTURO_9 = "Futuro 9"
    FUTURO_10 = "Futuro 10"
    FUTURO_11 = "Futuro 11"
    FUTURO_12 = "Futuro 12"
    FUTURO_13 = "Futuro 13"
    FUTURO_14 = "Futuro 14"
    FUTURO_15 = "Futuro 15"
    FUTURO_16 = "Futuro 16"
    FUTURO_17 = "Futuro 17"
    FUTURO_18 = "Futuro 18"
    FUTURO_19 = "Futuro 19"
    FUTURO_20 = "Futuro 20"
    FUTURO_21 = "Futuro 21"
    FUTURO_22 = "Futuro 22"
    FUTURO_23 = "Futuro 23"
    FUTURO_24 = "Futuro 24"
    FUTURO_25 = "Futuro 25"
    FUTURO_26 = "Futuro 26"

class TipoFuturo(Enum):
    EURUSD = "EUR/USD"
    DI = "DI"
    IBOV = "IBOV"
    USDBRL = "USD/BRL"
    USDCAD = "USD/CAD"
    USDJPY = "USD/JPY"
    USDMXN = "USD/MXN"

def definir_tipo_futuro(tipo: str) -> TipoFuturo:
    try:
        return TipoFuturo._value2member_map_[tipo]
    except:
        raise ValueError("Produto não encontrado.")

class IntervaloConfianca(Enum):
    P90 = 1.2816
    P95 = 1.6449
    P99 = 2.3263

class FatoresRisco(Enum):
    ACAO = auto()
    CAMBIO = auto()
    JUROS = auto()
    MERCADO = auto()
    VOLATILIDADE = auto()

class Localidade(Enum):
    BR = auto()
    US = auto()

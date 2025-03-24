import tiktoken

MODELO_CARO = "gpt-4"
MODELO_BARATO = "gpt-3.5-turbo"

LIMITE_TOKENS_TROCA_MODELO = 1000  

tokenizer_caro = tiktoken.encoding_for_model(MODELO_CARO)  
tokenizer_barato = tiktoken.encoding_for_model(MODELO_BARATO)  

def contar_tokens(texto, modelo=MODELO_CARO):
    """
    Função que conta os tokens de um texto com base no modelo escolhido.
    Se o modelo for o mais caro, usa o tokenizer correspondente.
    Se o modelo for o mais barato, usa o tokenizer do modelo barato.
    """
    if modelo == MODELO_CARO:
        return len(tokenizer_caro.encode(texto))
    else:
        return len(tokenizer_barato.encode(texto))

def escolher_modelo(texto):
    """
    Função que escolhe o modelo com base no número de tokens da resposta do usuário.
    - Se a resposta for maior que o limite de tokens definido, troca para o modelo mais barato.
    """
    tokens_resposta = contar_tokens(texto, modelo=MODELO_CARO)

    if tokens_resposta > LIMITE_TOKENS_TROCA_MODELO:
        return MODELO_BARATO
    else:
        return MODELO_CARO





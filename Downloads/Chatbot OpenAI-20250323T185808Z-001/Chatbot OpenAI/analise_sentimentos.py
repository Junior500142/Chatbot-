from textblob import TextBlob

def analisar_sentimento(texto):
    """
    Função para analisar o sentimento do texto.
    Retorna um dicionário com o sentimento e a polaridade.
    
    Categorias definidas:
    - "empolgado": polaridade alta (> 0.5)
    - "satisfeito": polaridade positiva moderada (0.1 a 0.5)
    - "neutro": polaridade próxima de zero (-0.1 a 0.1)
    - "preocupado": polaridade negativa moderada (-0.5 a -0.1)
    - "frustrado": polaridade baixa (<= -0.5)
    
    Ajustes com base em palavras-chave:
    - "cético": se o texto contém termos como "duvido", "cético", "desconfio"
    - "confuso": se o texto contém termos como "não sei", "confuso", "inseguro"
    """
    blob = TextBlob(texto)
    polaridade = blob.sentiment.polarity

    if polaridade > 0.5:
        sentimento = "empolgado"
    elif polaridade > 0.1:
        sentimento = "satisfeito"
    elif polaridade >= -0.1:
        sentimento = "neutro"
    elif polaridade > -0.5:
        sentimento = "preocupado"
    else:
        sentimento = "frustrado"
    
    texto_lower = texto.lower()
    if any(palavra in texto_lower for palavra in ["duvido", "cético", "desconfio"]):
        sentimento = "cético"
    if any(palavra in texto_lower for palavra in ["não sei", "confuso", "inseguro"]):
        sentimento = "confuso"
    
    return {"sentimento": sentimento, "polaridade": polaridade}

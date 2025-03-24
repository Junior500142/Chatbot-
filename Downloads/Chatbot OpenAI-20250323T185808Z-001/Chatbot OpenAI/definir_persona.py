def definir_persona(sentimento):
    """
    Função para definir o tom da resposta com base no sentimento do cliente.
    Retorna uma string com a persona adequada.
    
    Categorias adaptadas:
    - "empolgado": Responda com energia, entusiasmo e otimismo.
    - "satisfeito": Responda de forma cordial, reforçando a satisfação.
    - "neutro": Responda de forma neutra e informativa.
    - "preocupado": Responda de maneira empática e tranquilizadora.
    - "frustrado": Responda de forma empática, reconhecendo a frustração e oferecendo suporte.
    - "cético": Responda de maneira clara, objetiva e baseada em evidências.
    - "confuso": Responda de forma clara, simples e esclarecedora.
    """
    if sentimento == "empolgado":
        return "Responda de maneira entusiasmada, vibrante e cheia de energia, transmitindo otimismo."
    elif sentimento == "satisfeito":
        return "Responda de forma cordial, demonstrando agradecimento e reforçando a satisfação do cliente."
    elif sentimento == "neutro":
        return "Responda de forma neutra e informativa, sendo claro e objetivo."
    elif sentimento == "preocupado":
        return "Responda de maneira empática e tranquilizadora, reconhecendo as preocupações e oferecendo apoio."
    elif sentimento == "frustrado":
        return "Responda de forma extremamente empática, reconhecendo a frustração e oferecendo soluções e suporte."
    elif sentimento == "cético":
        return "Responda de maneira clara, objetiva e baseada em evidências, fornecendo dados e informações que inspirem confiança."
    elif sentimento == "confuso":
        return "Responda de forma clara e didática, simplificando os conceitos e esclarecendo as dúvidas do cliente."
    else:
        return "Responda de forma neutra e informativa."

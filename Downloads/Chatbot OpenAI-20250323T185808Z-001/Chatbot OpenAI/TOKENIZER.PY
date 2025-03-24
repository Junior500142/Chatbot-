import tiktoken

modelo = "gpt-4"


tokenizer = tiktoken.encoding_for_model(modelo)

def contar_tokens(texto):
    """Retorna a quantidade de tokens usada em um texto."""
    tokens = tokenizer.encode(texto)
    return len(tokens)

while True:
    texto = input("Digite um texto para contar os tokens (ou 'sair' para encerrar): ")
    
    if texto.lower() == "sair":
        print("Encerrando o programa.")
        break

    num_tokens = contar_tokens(texto)
    print(f"O texto digitado contém {num_tokens} tokens.")

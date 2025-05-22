from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import tiktoken  
from analise_sentimentos import analisar_sentimento  
from definir_persona import definir_persona

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = "gpt-4"

tokenizer = tiktoken.encoding_for_model(modelo)
LIMITE_TOKENS_RESPOSTA = 200  
CAMINHO_ARQUIVO = "leadbox_info.txt"

app = Flask(__name__)

def carregar_conhecimento():
    """Carrega as informações sobre a Leadbox a partir de um arquivo."""
    if os.path.exists(CAMINHO_ARQUIVO):
        with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as arquivo:
            return arquivo.read()
    else:
        return "Informações sobre a Leadbox não encontradas. Verifique o arquivo."

informacoes_leadbox = carregar_conhecimento()

def contar_tokens(texto):
    """Conta os tokens de uma string usando o tokenizer do modelo GPT-4."""
    return len(tokenizer.encode(texto))

def assistente_leadbox(pergunta_cliente, primeira_interacao=False):
    """Função que interage com a API da OpenAI para gerar respostas baseadas na pergunta do cliente."""
    
    sentimento = analisar_sentimento(pergunta_cliente)
    persona = definir_persona(sentimento)
    
    if primeira_interacao:
        prompt_usuario = """
        Inicie a conversa como um assistente amigável da Leadbox.
        Diga que pode responder dúvidas sobre a plataforma. Tense ser coeso e resumido na primeira interação.
        """
    else:
        prompt_usuario = f"""
        {persona}
        Responda de forma clara e direta a seguinte pergunta do cliente: "{pergunta_cliente}". 
        No final, adicione uma variação de perguntas como 'Ajudo em algo mais?', 'Posso te ajudar com mais alguma dúvida?' ou 'Se precisar de mais alguma coisa, estou por aqui!'.
        """

    prompt_sistema = f"""
    Você é o assistente virtual da Leadbox, uma plataforma omnichannel e CRM de vendas que oferece automações focadas no atendimento ao cliente.
    Seu papel é responder de maneira cordial, amigável e direta apenas a perguntas relacionadas à Leadbox.
    Caso o cliente pergunte sobre algo não relacionado, informe educadamente que só pode ajudar com dúvidas sobre a empresa.

    Aqui estão as informações oficiais da Leadbox que você deve usar para responder:
    
    {informacoes_leadbox}
    """

    try:
        resposta = cliente.chat.completions.create(
            messages=[ 
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            model=modelo,
            temperature=0.7,
            max_tokens=LIMITE_TOKENS_RESPOSTA
        )

        resposta_texto = resposta.choices[0].message.content
        tokens_resposta = contar_tokens(resposta_texto)

        # Se a resposta exceder o limite de tokens, resumir a resposta
        while tokens_resposta > LIMITE_TOKENS_RESPOSTA:
            resposta_resumida = cliente.chat.completions.create(
                messages=[ 
                    {"role": "system", "content": "Resuma o seguinte texto mantendo o significado:"},
                    {"role": "user", "content": resposta_texto}
                ],
                model=modelo,
                temperature=0.7,
                max_tokens=LIMITE_TOKENS_RESPOSTA  
            )
            resposta_texto = resposta_resumida.choices[0].message.content
            tokens_resposta = contar_tokens(resposta_texto)
        

        return resposta_texto
    
    except Exception as e:
        return f"Erro ao obter resposta: {str(e)}"

@app.route("/chat", methods=["POST"])
def chat():
    """Rota de interação do chatbot, recebe uma pergunta e retorna a resposta do assistente."""
    dados = request.get_json()

    pergunta = dados.get("pergunta", "")
    
    # Chama o assistente para obter a resposta
    resposta = assistente_leadbox(pergunta)
    
    return jsonify({"resposta": resposta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


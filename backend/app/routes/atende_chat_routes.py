from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os
from PIL import Image
import io
import base64

# --- SUA API KEY ---
GOOGLE_API_KEY = "AIzaSyBAXqKJZ9nCyXxPSbzmSZHh2VkYoaezcT4" 
genai.configure(api_key=GOOGLE_API_KEY)

atende_chat_bp = Blueprint('atende_chat', __name__)

# Prompt para conversa normal
TEXT_PROMPT = "Você é a Ana, Consultora Estética da OdontoSys. Analise a imagem e seja simpática."

# Prompt para o "Artista"
IMAGE_PROMPT = """
Atue como um simulador odontológico avançado.
Gere uma NOVA imagem baseada na foto fornecida.
A nova imagem deve mostrar a mesma pessoa, mas com um SORRISO PERFEITO:
- Dentes alinhados, brancos (tom natural) e simétricos.
- Gengiva saudável e harmoniosa.
- Mantenha o resto do rosto e iluminação idênticos.
O resultado deve ser fotorrealista.
"""

@atende_chat_bp.route('/chat/message', methods=['POST'])
def chat_message():
    image_file = request.files.get('image')
    text_message = request.form.get('message', '')

    # Se não tiver imagem, conversa normal com o modelo rápido
    if not image_file:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{TEXT_PROMPT}\nCliente: {text_message}")
        return jsonify({'response': response.text})

    # --- SE TIVER IMAGEM: TENTA GERAR SIMULAÇÃO ---
    try:
        print("Tentando gerar imagem com gemini-2.0-flash-exp...")
        img_bytes = image_file.read()
        input_img = Image.open(io.BytesIO(img_bytes))

        # Modelo capaz de gerar imagens
        gen_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = gen_model.generate_content([IMAGE_PROMPT, input_img])
        
        # Tenta extrair a imagem gerada
        try:
            # O Gemini retorna a imagem em partes. Precisamos pegar os bytes.
            img_data = response.candidates[0].content.parts[0].inline_data.data
            base64_img = base64.b64encode(img_data).decode('utf-8')
            image_url = f"data:image/png;base64,{base64_img}"
            
            return jsonify({
                'response': "✨ Aqui está uma simulação de como seu sorriso pode ficar! Lembre-se que o resultado real depende da avaliação clínica.",
                'image': image_url # Manda a imagem para o site
            })
        except:
            # Se o modelo respondeu texto em vez de imagem (acontece às vezes)
            raise Exception("O modelo não gerou pixels, apenas texto.")

    except Exception as e:
        # --- PLANO B: FALLBACK PARA TEXTO ---
        print(f"Falha na geração de imagem ({str(e)}). Caindo para análise de texto.")
        
        # Se falhou (Cota ou Erro Técnico), usa o modelo 2.5-Flash para descrever
        # Assim o usuário não fica na mão
        fallback_model = genai.GenerativeModel('gemini-2.5-flash')
        response = fallback_model.generate_content([
            "Analise tecnicamente este sorriso e descreva como ficaria após o tratamento (facetas/clareamento).", 
            input_img
        ])
        
        aviso = ""
        if "429" in str(e) or "Quota" in str(e):
            aviso = "⚠️ (O sistema de simulação visual está sobrecarregado agora, mas fiz a análise técnica abaixo):\n\n"
            
        return jsonify({'response': aviso + response.text})
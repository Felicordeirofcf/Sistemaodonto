from PIL import Image, ImageDraw, ImageFont
import os

# Configurações do Design
COR_FUNDO = "#2563eb" # O Azul do seu tema
COR_TEXTO = "#ffffff"
TAMANHO_TOTAL = 512

def desenhar_dente(draw, x, y, size):
    # Desenha um formato abstrato de dente (um retângulo arredondado com raiz)
    # Corpo do dente
    draw.rounded_rectangle(
        [x + size*0.2, y + size*0.2, x + size*0.8, y + size*0.7],
        radius=40, fill=COR_TEXTO
    )
    # Raiz esquerda
    draw.rounded_rectangle(
        [x + size*0.25, y + size*0.6, x + size*0.45, y + size*0.85],
        radius=20, fill=COR_TEXTO
    )
    # Raiz direita
    draw.rounded_rectangle(
        [x + size*0.55, y + size*0.6, x + size*0.75, y + size*0.85],
        radius=20, fill=COR_TEXTO
    )

def criar_icones():
    # Cria a imagem base (512x512)
    img = Image.new('RGB', (TAMANHO_TOTAL, TAMANHO_TOTAL), color=COR_FUNDO)
    draw = ImageDraw.Draw(img)

    # Desenha o ícone
    desenhar_dente(draw, 0, 0, TAMANHO_TOTAL)

    # Garante que a pasta public existe
    if not os.path.exists('public'):
        os.makedirs('public')

    # Salva pwa-512x512.png
    img.save('public/pwa-512x512.png')
    print("✅ pwa-512x512.png criado!")

    # Redimensiona e salva pwa-192x192.png
    img_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    img_192.save('public/pwa-192x192.png')
    print("✅ pwa-192x192.png criado!")

    # Salva o favicon.ico (tamanhos múltiplos para ficar bom no navegador)
    img.save('public/favicon.ico', format='ICO', sizes=[(32, 32), (64, 64), (256, 256)])
    print("✅ favicon.ico criado!")

    # Salva ícones para Apple também (opcional mas bom)
    img_apple = img.resize((180, 180), Image.Resampling.LANCZOS)
    img_apple.save('public/apple-touch-icon.png')
    print("✅ apple-touch-icon.png criado!")

if __name__ == "__main__":
    criar_icones()
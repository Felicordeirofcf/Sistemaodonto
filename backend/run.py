import os
from app import create_app

# Cria a aplicação Flask
app = create_app()

if __name__ == "__main__":
    # Pega a porta do ambiente ou usa 10000 como padrão
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

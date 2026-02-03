import os
from app import create_app
# CORREÇÃO AQUI: Mudamos de 'tasks' para 'task' (singular, igual na sua imagem)
from app.task.scheduler import start_scheduler 

app = create_app()

if __name__ == "__main__":
    # INICIALIZA O ROBÔ DE RECALL / CRM
    # Verifica se não é o reloader do Flask (para não rodar 2x em dev)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("FLASK_ENV") == "production":
        try:
            print("🚀 Iniciando Scheduler de Automação...")
            start_scheduler()
        except Exception as e:
            print(f"❌ Erro ao iniciar Scheduler: {e}")
    else:
        # Se estiver rodando direto sem reloader (ex: produção gunicorn), inicia também
        # Mas em ambiente dev simples local, isso garante 1 execução
        if not os.environ.get("FLASK_DEBUG"):
             try:
                print("🚀 Iniciando Scheduler de Automação (Prod)...")
                start_scheduler()
             except:
                 pass

    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    
    app.run(host="0.0.0.0", port=port, debug=debug)
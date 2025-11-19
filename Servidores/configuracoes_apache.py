import json
import subprocess
import time
import sys
import signal


def criar_arquivos_api():
    #Cria os arquivos JSON para os endpoints da API
    print("Criando arquivos da API...")
    
    with open("/var/www/html/api/pequeno", "w") as f:
        json.dump({"status": "ok", "servidor": "Apache", "tipo": "pequeno"}, f)
    
    with open("/var/www/html/api/medio", "w") as f:
        json.dump({"status": "ok", "servidor": "Apache", "tipo": "medio", "dados": "x" * 200}, f)
    
    with open("/var/www/html/api/grande", "w") as f:
        json.dump({"status": "ok", "servidor": "Apache", "tipo": "grande", "dados": "x" * 500}, f)
    
    print("Arquivos da API criados com sucesso!")


def criar_configuracao_apache():
    #Cria o arquivo de configuracao do Apache VirtualHost
    print("Criando configuracao do Apache...")
    
    config = """<VirtualHost *:80>
    ServerAdmin webmaster@76.1.0.11
    DocumentRoot /var/www/html

    <Directory /var/www/html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    <Location /api>
        Header set Content-Type application/json
    </Location>

    <Location /status-servidor>
        SetHandler server-status
        Require all granted
    </Location>

    # Echo do X-Custom-ID em todas as respostas
    Header always echo X-Custom-ID

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
"""
    
    with open("/etc/apache2/sites-available/000-default.conf", "w") as f:
        f.write(config)
    
    print("Configuracao do Apache criada com sucesso!")


def iniciar_exportador_metricas():
    #Inicia o Apache Exporter
    print("Iniciando exportador de metricas...")
    sys.stdout.flush()
    
    exportador = subprocess.Popen([
        "/usr/local/bin/apache_exporter",
        "--scrape_uri=http://76.1.0.11:80/status-servidor?auto"
    ])
    
    print("Exportador Prometheus iniciado na porta 9117")
    sys.stdout.flush()
    
    return exportador


def iniciar_node_exporter():
    #Inicia o Node Exporter
    print("Iniciando Node Exporter...")
    sys.stdout.flush()
    
    node_exporter = subprocess.Popen([
        "/usr/local/bin/node_exporter",
        "--web.listen-address=:9101"
    ])
    
    print("Node Exporter iniciado na porta 9101")
    sys.stdout.flush()
    
    return node_exporter


def iniciar_apache():
    #Inicia o servidor Apache
    time.sleep(2)
    
    print("Iniciando Apache...")
    sys.stdout.flush()
    
    apache_proc = subprocess.Popen(["apachectl", "-D", "FOREGROUND"])
    
    print("Apache iniciado")
    sys.stdout.flush()
    
    return apache_proc


def criar_signal_handler(processos):
    #Cria um handler para sinais de encerramento
    def sinal_handler(sig, frame):
        print("Encerrando servicos...")
        for proc in processos:
            if proc:
                proc.terminate()
        sys.exit(0)
    
    return sinal_handler


def main():
    #Funcao principal
    print("=" * 70)
    print("CONFIGURANDO E INICIANDO SERVIDOR APACHE")
    print("=" * 70)
    
    #Fase 1: Configuracao
    try:
        criar_arquivos_api()
        criar_configuracao_apache()
    except Exception as e:
        print(f"ERRO durante a configuracao: {e}")
        sys.exit(1)
    
    #Fase 2: Inicializacao
    exportador = iniciar_exportador_metricas()
    node_exporter = iniciar_node_exporter()
    apache_proc = iniciar_apache()
    
    #Configurar handler de sinais
    processos = [apache_proc, node_exporter, exportador]
    handler = criar_signal_handler(processos)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    
    print("=" * 70)
    print("CONFIGURACAO E INICIALIZACAO CONCLUIDAS COM SUCESSO!")
    print("=" * 70)
    
    #Aguardar processo principal
    try:
        apache_proc.wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
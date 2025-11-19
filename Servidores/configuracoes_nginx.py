#!/usr/bin/env python3
"""
Script de configuracao e inicializacao do servidor Nginx
Gera configuracoes, cria arquivos estaticos e gerencia processos
"""

import json
import subprocess
import time
import sys
import signal
import urllib.request


def criar_arquivos_api():
    """Cria os arquivos JSON para os endpoints da API"""
    print("Criando arquivos da API...")
    
    with open("/usr/share/nginx/html/api/pequeno", "w") as f:
        json.dump({"status": "ok", "servidor": "Nginx", "tipo": "pequeno"}, f)
    
    with open("/usr/share/nginx/html/api/medio", "w") as f:
        json.dump({"status": "ok", "servidor": "Nginx", "tipo": "medio", "dados": "x" * 200}, f)
    
    with open("/usr/share/nginx/html/api/grande", "w") as f:
        json.dump({"status": "ok", "servidor": "Nginx", "tipo": "grande", "dados": "x" * 500}, f)
    
    print("Arquivos da API criados com sucesso!")


def criar_configuracao_nginx():
    """Cria o arquivo de configuracao do Nginx"""
    print("Criando configuracao do Nginx...")
    
    config = """user www-data;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                     '$status $body_bytes_sent "$http_referer" '
                     '"$http_user_agent" X-Custom-ID: $http_x_custom_id';

    access_log /var/log/nginx/access.log main;
    sendfile on;
    keepalive_timeout 65;

    # Echo do X-Custom-ID em todas as respostas
    add_header X-Custom-ID $http_x_custom_id always;

    server {
        listen 80;
        server_name 76.1.0.10;

        location / {
            root /usr/share/nginx/html;
            index index.html;
        }

        location /api/ {
            root /usr/share/nginx/html;
            default_type application/json;
        }

        location /estatico/ {
            alias /usr/share/nginx/html/estatico/;
            autoindex on;
        }

        location /status_nginx {
            stub_status on;
            access_log off;
        }
    }
}
"""
    
    with open("/etc/nginx/nginx.conf", "w") as f:
        f.write(config)
    
    print("Configuracao do Nginx criada com sucesso!")


def iniciar_nginx():
    """Inicia o servidor Nginx"""
    print("Iniciando Nginx...")
    sys.stdout.flush()
    
    nginx_proc = subprocess.Popen(["nginx", "-g", "daemon off;"])
    print("Nginx iniciado, aguardando estar pronto...")
    sys.stdout.flush()
    
    return nginx_proc


def aguardar_nginx_pronto():
    """Aguarda o Nginx estar pronto para receber requisicoes"""
    for i in range(30):
        try:
            urllib.request.urlopen("http://76.1.0.10:80/status_nginx", timeout=1)
            print("Nginx pronto!")
            sys.stdout.flush()
            return True
        except:
            time.sleep(0.5)
    
    print("AVISO: Nginx pode nao estar respondendo")
    sys.stdout.flush()
    return False


def iniciar_exportador_metricas():
    """Inicia o Nginx Prometheus Exporter"""
    time.sleep(1)
    
    print("Iniciando exportador de metricas...")
    sys.stdout.flush()
    
    exportador = subprocess.Popen([
        "/usr/local/bin/nginx-prometheus-exporter",
        "-nginx.scrape-uri=http://76.1.0.10:80/status_nginx"
    ])
    
    print("Exportador Prometheus iniciado na porta 9113")
    sys.stdout.flush()
    
    return exportador


def iniciar_node_exporter():
    """Inicia o Node Exporter"""
    print("Iniciando Node Exporter...")
    sys.stdout.flush()
    
    node_exporter = subprocess.Popen([
        "/usr/local/bin/node_exporter",
        "--web.listen-address=:9100"
    ])
    
    print("Node Exporter iniciado na porta 9100")
    sys.stdout.flush()
    
    return node_exporter


def criar_signal_handler(processos):
    """Cria um handler para sinais de encerramento"""
    def sinal_handler(sig, frame):
        print("Encerrando servicos...")
        for proc in processos:
            if proc:
                proc.terminate()
        sys.exit(0)
    
    return sinal_handler


def main():
    """Funcao principal"""
    print("=" * 70)
    print("CONFIGURANDO E INICIANDO SERVIDOR NGINX")
    print("=" * 70)
    
    # Fase 1: Configuracao
    try:
        criar_arquivos_api()
        criar_configuracao_nginx()
    except Exception as e:
        print(f"ERRO durante a configuracao: {e}")
        sys.exit(1)
    
    # Fase 2: Inicializacao
    nginx_proc = iniciar_nginx()
    aguardar_nginx_pronto()
    exportador = iniciar_exportador_metricas()
    node_exporter = iniciar_node_exporter()
    
    # Configurar handler de sinais
    processos = [node_exporter, exportador, nginx_proc]
    handler = criar_signal_handler(processos)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    
    print("=" * 70)
    print("CONFIGURACAO E INICIALIZACAO CONCLUIDAS COM SUCESSO!")
    print("=" * 70)
    
    # Aguardar processo principal
    try:
        nginx_proc.wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

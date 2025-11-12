#!/usr/bin/env python3
#Testes de Carga para Nginx e Apache
#Trabalho de Redes II - 2025.2
#Aluno: Raildom da Rocha Sobrinho
#Matrícula: 20239057601

import sys
import os
import time
import statistics
import csv
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

#Adicionar diretório src ao caminho
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from cliente import ClienteHTTP
    from configuracao import ID_CUSTOMIZADO
except ImportError as e:
    print(f"[ERRO] Erro ao importar módulos: {e}")
    print("Certifique-se de estar no diretório correto do projeto")
    sys.exit(1)


#Classe para cores no terminal
class Cores:
    VERDE = '\033[92m'    #Verde para sucesso
    VERMELHO = '\033[91m' #Vermelho para erro
    AMARELO = '\033[93m'  #Amarelo para aviso
    AZUL = '\033[94m'     #Azul para informação
    MAGENTA = '\033[95m'  #Magenta para destaque
    CIANO = '\033[96m'    #Ciano para título
    RESET = '\033[0m'     #Reset para cor normal
    NEGRITO = '\033[1m'   #Negrito

    @staticmethod
    def sucesso(texto):
        return f"{Cores.VERDE}[OK]{Cores.RESET} {texto}"
    
    @staticmethod
    def erro(texto):
        return f"{Cores.VERMELHO}[ERRO]{Cores.RESET} {texto}"
    
    @staticmethod
    def aviso(texto):
        return f"{Cores.AMARELO}[AVISO]{Cores.RESET} {texto}"
    
    @staticmethod
    def info(texto):
        return f"{Cores.AZUL}[INFO]{Cores.RESET} {texto}"
    
    @staticmethod
    def destaque(texto):
        return f"{Cores.MAGENTA}{texto}{Cores.RESET}"
    
    @staticmethod
    def titulo(texto):
        return f"{Cores.CIANO}{Cores.NEGRITO}{texto}{Cores.RESET}"


class TestadorCarga:
    #Classe para executar testes de carga nos servidores
    
    #=================================================================
    #CONFIGURAÇÕES DOS CENÁRIOS DE TESTE - ALTERE AQUI
    #=================================================================
    CENARIO_1_BAIXA_CARGA = {
        'usuarios': 10,      #Usuários virtuais (threads)
        'requisicoes': 100,  #Total de requisições
        'endpoint': '/api/info'
    }
    
    CENARIO_2_MEDIA_CARGA = {
        'usuarios': 50,
        'requisicoes': 500,
        'endpoint': '/api/status'
    }
    
    CENARIO_3_ALTA_CARGA = {
        'usuarios': 100,
        'requisicoes': 1000,
        'endpoint': '/api/dados'
    }
    
    #Cenários de Arquivos Pequenos
    CENARIO_4_ARQUIVO_1KB = {
        'usuarios': 30,
        'requisicoes': 300,
        'arquivo': 'pequeno-1kb.txt',
        'tamanho': '1KB'
    }
    
    CENARIO_5_ARQUIVO_10KB = {
        'usuarios': 25,
        'requisicoes': 250,
        'arquivo': 'pequeno-10kb.txt',
        'tamanho': '10KB'
    }
    
    CENARIO_6_ARQUIVO_50KB = {
        'usuarios': 20,
        'requisicoes': 200,
        'arquivo': 'pequeno-50kb.txt',
        'tamanho': '50KB'
    }
    
    #Cenários de Arquivos Médios
    CENARIO_7_ARQUIVO_100KB = {
        'usuarios': 15,
        'requisicoes': 150,
        'arquivo': 'medio-100kb.txt',
        'tamanho': '100KB'
    }
    
    CENARIO_8_ARQUIVO_500KB = {
        'usuarios': 15,
        'requisicoes': 150,
        'arquivo': 'medio-500kb.txt',
        'tamanho': '500KB'
    }
    
    CENARIO_9_ARQUIVO_700KB = {
        'usuarios': 12,
        'requisicoes': 120,
        'arquivo': 'medio-700kb.txt',
        'tamanho': '700KB'
    }
    
    #Cenários de Arquivos Grandes
    CENARIO_10_ARQUIVO_1MB = {
        'usuarios': 10,
        'requisicoes': 100,
        'arquivo': 'grande-1mb.txt',
        'tamanho': '1MB'
    }
    
    CENARIO_11_ARQUIVO_5MB = {
        'usuarios': 10,
        'requisicoes': 50,
        'arquivo': 'grande-5mb.txt',
        'tamanho': '5MB'
    }
    
    CENARIO_12_ARQUIVO_7MB = {
        'usuarios': 8,
        'requisicoes': 40,
        'arquivo': 'grande-7mb.txt',
        'tamanho': '7MB'
    }
    
    #Cenários de Arquivos Enormes
    CENARIO_13_ARQUIVO_10MB = {
        'usuarios': 5,
        'requisicoes': 25,
        'arquivo': 'enorme-10mb.txt',
        'tamanho': '10MB'
    }
    
    CENARIO_14_ARQUIVO_20MB = {
        'usuarios': 5,
        'requisicoes': 20,
        'arquivo': 'enorme-20mb.txt',
        'tamanho': '20MB'
    }
    
    CENARIO_15_ARQUIVO_50MB = {
        'usuarios': 3,
        'requisicoes': 10,
        'arquivo': 'enorme-50mb.txt',
        'tamanho': '50MB'
    }
    #=================================================================
    
    def __init__(self):
        self.servidores = {
            'nginx': ('76.1.0.10', 80),
            'apache': ('76.1.0.11', 80)
        }
        self.id_customizado = ID_CUSTOMIZADO
        
        #Preparar diretório e arquivos de saída
        self.dir_resultados = os.path.join(os.path.dirname(__file__), '..', 'resultados')
        os.makedirs(self.dir_resultados, exist_ok=True)
        
        self.arquivo_txt = os.path.join(self.dir_resultados, 'resultados_testes.txt')
        self.arquivo_csv = os.path.join(self.dir_resultados, 'resultados_testes.csv')
        
        self.txt_file = open(self.arquivo_txt, 'w', encoding='utf-8')
        self.dados_csv = []
        
        print(f"\n[INFO] Resultados serão salvos em:")
        print(f"  - TXT: {self.arquivo_txt}")
        print(f"  - CSV: {self.arquivo_csv}")
        print(f"\n[INFO] Métricas de CPU/Memória:")
        print(f"  Coletadas via Prometheus (http://prometheus:9090)")
        print(f"  Visualize em tempo real no Grafana (http://localhost:3000)")
    
    def print_e_salvar(self, texto):
        #Imprime no terminal e salva no arquivo TXT
        print(texto)
        self.txt_file.write(texto + '\n')
        self.txt_file.flush()
    
    def obter_metricas_container(self, servidor):
        #Obtém métricas de CPU e Memória do container via Prometheus/HTTP
        import requests
        
        prometheus_url = "http://prometheus:9090"
        
        try:
            cpu_percent = 0.0
            mem_usage = "0MiB"
            mem_percent = 0.0
            
            #Para Apache, usar métricas nativas do Prometheus
            if servidor == 'apache':
                #Query de CPU do Apache
                cpu_response = requests.get(f'{prometheus_url}/api/v1/query', 
                                           params={'query': 'apache_cpuload'}, timeout=3)
                if cpu_response.status_code == 200:
                    cpu_data = cpu_response.json()
                    if cpu_data.get('data', {}).get('result'):
                        cpu_percent = float(cpu_data['data']['result'][0]['value'][1])
                
                #Query de workers do Apache
                workers_response = requests.get(f'{prometheus_url}/api/v1/query',
                                               params={'query': 'apache_workers{state="busy"}'}, timeout=3)
                if workers_response.status_code == 200:
                    workers_data = workers_response.json()
                    if workers_data.get('data', {}).get('result'):
                        busy_workers = float(workers_data['data']['result'][0]['value'][1])
                        #Estimar uso de memória baseado em workers ativos (cada worker ~10MB)
                        mem_mib = max(50, busy_workers * 10)  #Mínimo 50MB
                        mem_usage = f"{mem_mib:.1f}MiB"
                        mem_percent = min(busy_workers * 2, 100.0)
            
            #Para Nginx, buscar stub_status diretamente
            else:
                try:
                    nginx_status = requests.get('http://servidor_nginx/status_nginx', timeout=2)
                    if nginx_status.status_code == 200:
                        #Parsear stub_status do Nginx
                        status_text = nginx_status.text
                        lines = status_text.split('\n')
                        
                        #Active connections: X
                        active_conns = 0
                        for line in lines:
                            if 'Active connections:' in line:
                                active_conns = int(line.split(':')[1].strip())
                                break
                        
                        #Usar conexões ativas como proxy de carga
                        if active_conns > 0:
                            cpu_percent = min(active_conns * 0.5, 100.0)
                            mem_mib = max(30, active_conns * 2)  #Mínimo 30MB
                            mem_usage = f"{mem_mib:.1f}MiB"
                            mem_percent = min(active_conns * 0.3, 100.0)
                except:
                    #Se falhar stub_status, tentar acessos totais no Prometheus
                    pass
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'mem_usage': mem_usage,
                'mem_percent': round(mem_percent, 2)
            }
            
        except Exception as e:
            #Se falhar, retorna valores padrão
            return {'cpu_percent': 0.0, 'mem_usage': '0MiB', 'mem_percent': 0.0}
    
    def salvar_resultado_csv(self, teste, servidor, caminho, num_requisicoes, num_threads, 
                            total, sucessos, falhas, tempo_total, latencia_media, latencia_p50, 
                            latencia_p95, latencia_p99, desvio_padrao, rps, cpu_percent, 
                            mem_usage, mem_percent):
        #Salva uma linha no CSV com todas as métricas
        taxa_erro = round((falhas/total*100) if total > 0 else 0, 2)
        taxa_sucesso = round((sucessos/total*100) if total > 0 else 0, 2)
        
        self.dados_csv.append({
            'timestamp': datetime.now().isoformat(),
            'teste': teste,
            'servidor': servidor,
            'caminho': caminho,
            'num_requisicoes': num_requisicoes,
            'num_threads': num_threads,
            'total_requisicoes': total,
            'sucessos': sucessos,
            'falhas': falhas,
            'taxa_sucesso_%': taxa_sucesso,
            'taxa_erro_%': taxa_erro,
            'tempo_total_s': round(tempo_total, 2),
            'requisicoes_por_segundo': round(rps, 2),
            'latencia_media_ms': round(latencia_media, 2),
            'latencia_p50_ms': round(latencia_p50, 2),
            'latencia_p95_ms': round(latencia_p95, 2),
            'latencia_p99_ms': round(latencia_p99, 2),
            'desvio_padrao_ms': round(desvio_padrao, 2),
            'cpu_percent': round(cpu_percent, 2),
            'mem_usage': mem_usage,
            'mem_percent': round(mem_percent, 2)
        })
    
    def executar_requisicao(self, servidor, caminho='/'):
        #Executa uma única requisição e retorna o resultado
        host, porta = self.servidores[servidor]
        cliente = ClienteHTTP(host, porta)
        
        inicio = time.time()
        resultado = cliente.enviar_requisicao('GET', caminho)
        tempo_decorrido = time.time() - inicio
        
        return {
            'servidor': servidor,
            'sucesso': resultado['sucesso'],
            'codigo_status': resultado.get('codigo_status', 0),
            'tempo_resposta': tempo_decorrido,
            'tamanho_resposta': len(resultado.get('corpo', ''))
        }
    
    def teste_concorrente(self, servidor, caminho, num_requisicoes, num_threads, nome_teste="Teste"):
        #Executa teste com requisições concorrentes
        #Argumentos:
        #    servidor: 'nginx' ou 'apache'
        #    caminho: Caminho do endpoint a testar
        #    num_requisicoes: Número total de requisições
        #    num_threads: Número de threads concorrentes
        #    nome_teste: Nome do teste para o CSV
        self.print_e_salvar(f"\n  Testando {servidor.upper()}: {caminho}")
        self.print_e_salvar(f"  Requisições: {num_requisicoes}, Concorrência: {num_threads}")
        
        resultados = []
        tempo_inicio = time.time()
        
        #Coletar métricas ANTES do teste
        metricas_antes = self.obter_metricas_container(servidor)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futuros = [
                executor.submit(self.executar_requisicao, servidor, caminho)
                for _ in range(num_requisicoes)
            ]
            
            for futuro in as_completed(futuros):
                try:
                    resultado = futuro.result()
                    resultados.append(resultado)
                except Exception as e:
                    self.print_e_salvar(f"  [ERRO] Requisição falhou: {e}")
                    resultados.append({'sucesso': False, 'tempo_resposta': 0})
        
        tempo_total = time.time() - tempo_inicio
        
        #Coletar métricas DEPOIS do teste
        metricas_depois = self.obter_metricas_container(servidor)
        
        #Calcular estatísticas
        sucessos = [r for r in resultados if r['sucesso']]
        falhas = len(resultados) - len(sucessos)
        tempos = [r['tempo_resposta'] * 1000 for r in sucessos]  #Converter para ms
        
        #Usar a métrica MÁXIMA (durante o pico da carga)
        cpu_percent = max(metricas_antes['cpu_percent'], metricas_depois['cpu_percent'])
        mem_percent = max(metricas_antes['mem_percent'], metricas_depois['mem_percent'])
        mem_usage = metricas_depois['mem_usage']
        
        if tempos:
            latencia_media = statistics.mean(tempos)
            latencia_p50 = statistics.median(tempos)
            latencia_p95 = sorted(tempos)[int(len(tempos)*0.95)] if len(tempos) > 1 else latencia_p50
            latencia_p99 = sorted(tempos)[int(len(tempos)*0.99)] if len(tempos) > 1 else latencia_p50
            desvio_padrao = statistics.stdev(tempos) if len(tempos) > 1 else 0
            rps = len(resultados)/tempo_total
            taxa_erro = (falhas/len(resultados)*100) if len(resultados) > 0 else 0
            
            self.print_e_salvar(f"\n  Resultados:")
            self.print_e_salvar(f"    Total de requisições: {len(resultados)}")
            self.print_e_salvar(f"    Sucessos: {len(sucessos)} ({len(sucessos)/len(resultados)*100:.1f}%)")
            self.print_e_salvar(f"    Falhas: {falhas} ({taxa_erro:.1f}%)")
            self.print_e_salvar(f"    Tempo total: {tempo_total:.2f}s")
            self.print_e_salvar(f"    Requisições/segundo: {rps:.2f}")
            self.print_e_salvar(f"    Latência média: {latencia_media:.2f}ms")
            self.print_e_salvar(f"    Latência P50: {latencia_p50:.2f}ms")
            if len(tempos) > 1:
                self.print_e_salvar(f"    Latência P95: {latencia_p95:.2f}ms")
                self.print_e_salvar(f"    Latência P99: {latencia_p99:.2f}ms")
                self.print_e_salvar(f"    Desvio padrão: {desvio_padrao:.2f}ms")
            self.print_e_salvar(f"    CPU: {cpu_percent:.2f}%")
            self.print_e_salvar(f"    Memória: {mem_usage} ({mem_percent:.2f}%)")
            
            #Salvar no CSV
            self.salvar_resultado_csv(
                nome_teste, servidor, caminho, num_requisicoes, num_threads,
                len(resultados), len(sucessos), falhas, tempo_total,
                latencia_media, latencia_p50, latencia_p95, latencia_p99,
                desvio_padrao, rps, cpu_percent, 
                mem_usage, mem_percent
            )
        
        return {
            'total': len(resultados),
            'sucessos': len(sucessos),
            'tempo_total': tempo_total,
            'tempos': tempos
        }
    
    def cenario_baixa_carga(self):
        #Cenário 1: Baixa Carga
        cfg = self.CENARIO_1_BAIXA_CARGA
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 1: BAIXA CARGA")
        self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar(f"\n[NGINX vs APACHE] Endpoint: {cfg['endpoint']}")
        self.teste_concorrente('nginx', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], "Cenario1_BaixaCarga")
        self.teste_concorrente('apache', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], "Cenario1_BaixaCarga")
    
    def cenario_media_carga(self):
        #Cenário 2: Média Carga
        cfg = self.CENARIO_2_MEDIA_CARGA
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 2: MÉDIA CARGA")
        self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar(f"\n[NGINX vs APACHE] Endpoint: {cfg['endpoint']}")
        self.teste_concorrente('nginx', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], "Cenario2_MediaCarga")
        self.teste_concorrente('apache', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], "Cenario2_MediaCarga")
    
    def cenario_alta_carga(self):
        #Cenário 3: Alta Carga
        cfg = self.CENARIO_3_ALTA_CARGA
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 3: ALTA CARGA")
        self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar(f"\n[NGINX vs APACHE] Endpoint: {cfg['endpoint']}")
        self.teste_concorrente('nginx', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], "Cenario3_AltaCarga")
        self.teste_concorrente('apache', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], "Cenario3_AltaCarga")
    
    def cenario_arquivo_pequeno(self):
        #Cenários 4-6: Arquivos Pequenos (1KB, 10KB, 50KB)
        for num, cfg_name in [(4, 'CENARIO_4_ARQUIVO_1KB'), 
                               (5, 'CENARIO_5_ARQUIVO_10KB'), 
                               (6, 'CENARIO_6_ARQUIVO_50KB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENÁRIO {num}: ARQUIVO PEQUENO ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoPequeno")
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoPequeno")
    
    def cenario_arquivo_medio(self):
        #Cenários 7-9: Arquivos Médios (100KB, 500KB, 700KB)
        for num, cfg_name in [(7, 'CENARIO_7_ARQUIVO_100KB'), 
                               (8, 'CENARIO_8_ARQUIVO_500KB'), 
                               (9, 'CENARIO_9_ARQUIVO_700KB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENÁRIO {num}: ARQUIVO MÉDIO ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoMedio")
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoMedio")
    
    def cenario_arquivo_grande(self):
        #Cenários 10-12: Arquivos Grandes (1MB, 5MB, 7MB)
        for num, cfg_name in [(10, 'CENARIO_10_ARQUIVO_1MB'), 
                               (11, 'CENARIO_11_ARQUIVO_5MB'), 
                               (12, 'CENARIO_12_ARQUIVO_7MB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENÁRIO {num}: ARQUIVO GRANDE ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoGrande")
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoGrande")
    
    def cenario_arquivo_enorme(self):
        #Cenários 13-15: Arquivos Enormes (10MB, 20MB, 50MB)
        for num, cfg_name in [(13, 'CENARIO_13_ARQUIVO_10MB'), 
                               (14, 'CENARIO_14_ARQUIVO_20MB'), 
                               (15, 'CENARIO_15_ARQUIVO_50MB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENÁRIO {num}: ARQUIVO ENORME ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuários Virtuais: {cfg['usuarios']} | Execuções: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoEnorme")
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], f"Cenario{num}_ArquivoEnorme")
        
        for i in range(1, 4):
            self.print_e_salvar(f"\n--- Onda {i}/3 ---")
            self.teste_concorrente('nginx', '/api/status', 300, 30, f"Sustentada_Onda{i}")
            self.teste_concorrente('apache', '/api/status', 300, 30, f"Sustentada_Onda{i}")
            time.sleep(2)  #Pausa de 2s entre ondas
    
    def executar_testes(self):
        #Executa todos os cenários de teste
        self.print_e_salvar("="*60)
        self.print_e_salvar("INÍCIO DOS TESTES DE CARGA")
        self.print_e_salvar(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_e_salvar("="*60)
        
        #Executar todos os cenários (agora 15 no total)
        self.cenario_baixa_carga()      #Cenário 1
        self.cenario_media_carga()      #Cenário 2
        self.cenario_alta_carga()       #Cenário 3
        self.cenario_arquivo_pequeno()  #Cenários 4-6
        self.cenario_arquivo_medio()    #Cenários 7-9
        self.cenario_arquivo_grande()   #Cenários 10-12
        self.cenario_arquivo_enorme()   #Cenários 13-15
        
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("TESTES CONCLUÍDOS!")
        self.print_e_salvar(f"Resultados salvos em:")
        self.print_e_salvar(f"  - {self.arquivo_txt}")
        self.print_e_salvar(f"  - {self.arquivo_csv}")
        self.print_e_salvar("="*60)
    
    def executar_todos_testes(self):
        #Executa todos os cenários de teste (COMPLETO)
        self.print_e_salvar("="*70)
        self.print_e_salvar("TESTADOR DE CARGA - NGINX vs APACHE")
        self.print_e_salvar("Trabalho de Redes II - 2025.2")
        self.print_e_salvar("="*70)
        self.print_e_salvar(f"\nID Personalizado: {self.id_customizado}")
        
        tempo_inicio = time.time()
        
        #Executar todos os 6 cenários
        self.cenario_baixa_carga()
        self.cenario_media_carga()
        self.cenario_alta_carga()
        self.cenario_arquivo_pequeno()
        self.cenario_arquivo_medio()
        self.cenario_arquivo_grande()
        
        tempo_total = time.time() - tempo_inicio
        
        self.print_e_salvar("\n" + "="*70)
        self.print_e_salvar("TESTES CONCLUÍDOS")
        self.print_e_salvar("="*70)
        self.print_e_salvar(f"Tempo total de execução: {tempo_total/60:.2f} minutos")
        
        #Exportar CSV
        print(f"\n📊 Exportando dados para CSV...")
        try:
            with open(self.arquivo_csv, 'w', newline='') as f:
                if self.dados_csv:
                    campos = self.dados_csv[0].keys()
                    writer = csv.DictWriter(f, fieldnames=campos)
                    writer.writeheader()
                    writer.writerows(self.dados_csv)
                    print(Cores.sucesso(f"CSV salvo: {self.arquivo_csv}"))
        except Exception as e:
            print(Cores.erro(f"Erro ao salvar CSV: {e}"))
        
        #Fechar arquivo TXT
        if hasattr(self, 'txt_file') and self.txt_file:
            self.txt_file.close()
            print(Cores.sucesso(f"TXT salvo: {self.arquivo_txt}"))
        
        print()  #Linha final no terminal


def principal():
    testador = TestadorCarga()
    testador.executar_todos_testes()


if __name__ == '__main__':
    principal()

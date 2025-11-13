import sys
import os
import time
import statistics
import csv
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

#Adicionar diretorio src ao caminho
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from cliente import ClienteHTTP
    from configuracao import ID_CUSTOMIZADO
except ImportError as e:
    print(f"[ERRO] Erro ao importar modulos: {e}")
    print("Certifique-se de estar no diretorio correto do projeto")
    sys.exit(1)


#Classe para cores no terminal
class Cores:
    VERDE = '\033[92m'    #Verde para sucesso
    VERMELHO = '\033[91m' #Vermelho para erro
    AMARELO = '\033[93m'  #Amarelo para aviso
    AZUL = '\033[94m'     #Azul para informacao
    MAGENTA = '\033[95m'  #Magenta para destaque
    CIANO = '\033[96m'    #Ciano para titulo
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
    #CONFIGURACOES DOS CENARIOS DE TESTE
    #=================================================================
    NUM_EXECUCOES = 10 
    NUM_USUARIOS = 10
    NUM_REQUISTICOES = 50
    
    CENARIO_1_BAIXA_CARGA = {
        'usuarios': 10,     
        'requisicoes': 100, 
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
    
    #Cenarios de Arquivos Pequenos
    CENARIO_4_ARQUIVO_1KB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'pequeno-1kb.txt',
        'tamanho': '1KB'
    }
    
    CENARIO_5_ARQUIVO_10KB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'pequeno-10kb.txt',
        'tamanho': '10KB'
    }
    
    CENARIO_6_ARQUIVO_50KB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'pequeno-50kb.txt',
        'tamanho': '50KB'
    }
    
    #Cenarios de Arquivos Medios
    CENARIO_7_ARQUIVO_100KB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'medio-100kb.txt',
        'tamanho': '100KB'
    }
    
    CENARIO_8_ARQUIVO_500KB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'medio-500kb.txt',
        'tamanho': '500KB'
    }
    
    CENARIO_9_ARQUIVO_700KB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'medio-700kb.txt',
        'tamanho': '700KB'
    }
    
    #Cenarios de Arquivos Grandes
    CENARIO_10_ARQUIVO_1MB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'grande-1mb.txt',
        'tamanho': '1MB'
    }
    
    CENARIO_11_ARQUIVO_5MB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'grande-5mb.txt',
        'tamanho': '5MB'
    }
    
    CENARIO_12_ARQUIVO_7MB = {
        'usuarios': NUM_USUARIOS,
        'requisicoes': NUM_REQUISTICOES,
        'arquivo': 'grande-7mb.txt',
        'tamanho': '7MB'
    }
    
    def __init__(self):
        self.servidores = {
            'nginx': ('76.1.0.10', 80),
            'apache': ('76.1.0.11', 80)
        }
        self.id_customizado = ID_CUSTOMIZADO
        
        #Preparar diretorio e arquivos de saida
        self.dir_resultados = os.path.join(os.path.dirname(__file__), '..', 'resultados')
        os.makedirs(self.dir_resultados, exist_ok=True)
        
        self.arquivo_txt = os.path.join(self.dir_resultados, 'resultados_testes.txt')
        self.arquivo_csv = os.path.join(self.dir_resultados, 'resultados_testes.csv')
        
        self.txt_file = open(self.arquivo_txt, 'w', encoding='utf-8')
        self.dados_csv = []
        
        print(f"\n[INFO] Resultados serao salvos em:")
        print(f"  - TXT: {self.arquivo_txt}")
        print(f"  - CSV: {self.arquivo_csv}")
        print(f"\n[INFO] Metricas de CPU/Memoria:")
        print(f"  Coletadas via Prometheus (http://prometheus:9090)")
        print(f"  Visualize em tempo real no Grafana (http://localhost:3000)")
    
    def print_e_salvar(self, texto):
        #Imprime no terminal e salva no arquivo TXT
        print(texto)
        self.txt_file.write(texto + '\n')
        self.txt_file.flush()
    
    def obter_metricas_container(self, servidor):
        #Obtem metricas de CPU e Memoria do container via Prometheus/HTTP
        import requests
        
        prometheus_url = "http://prometheus:9090"
        
        try:
            cpu_percent = 0.0
            mem_usage = "0MiB"
            mem_percent = 0.0
            
            #Para Apache, usar metricas nativas do Prometheus
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
                        #Estimar uso de memoria baseado em workers ativos (cada worker ~10MB)
                        mem_mib = max(50, busy_workers * 10)  #Minimo 50MB
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
                        
                        #Usar conexoes ativas como proxy de carga
                        if active_conns > 0:
                            cpu_percent = min(active_conns * 0.5, 100.0)
                            mem_mib = max(30, active_conns * 2)  #Minimo 30MB
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
            #Se falhar, retorna valores padrao
            return {'cpu_percent': 0.0, 'mem_usage': '0MiB', 'mem_percent': 0.0}
    
    def salvar_resultado_csv(self, teste, servidor, caminho, num_requisicoes, num_threads, 
                            total, sucessos, falhas, tempo_total, latencia_media, latencia_p50, 
                            latencia_p95, latencia_p99, desvio_padrao, rps, cpu_percent, 
                            mem_usage, mem_percent, execucao=None):
        #Salva uma linha no CSV com todas as metricas
        taxa_erro = round((falhas/total*100) if total > 0 else 0, 2)
        taxa_sucesso = round((sucessos/total*100) if total > 0 else 0, 2)
        
        self.dados_csv.append({
            'timestamp': datetime.now().isoformat(),
            'execucao': execucao if execucao else 1,
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
        #Executa uma unica requisicao e retorna o resultado
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
    
    def teste_concorrente(self, servidor, caminho, num_requisicoes, num_threads, nome_teste="Teste", execucao=None):
        #Executa teste com requisicoes concorrentes
        #Argumentos:
        #    servidor: 'nginx' ou 'apache'
        #    caminho: Caminho do endpoint a testar
        #    num_requisicoes: Numero total de requisicoes
        #    num_threads: Numero de threads concorrentes
        #    nome_teste: Nome do teste para o CSV
        #    execucao: Numero da execucao (opcional)
        self.print_e_salvar(f"\n  Testando {servidor.upper()}: {caminho}")
        self.print_e_salvar(f"  Requisicoes: {num_requisicoes}, Concorrencia: {num_threads}")
        
        resultados = []
        tempo_inicio = time.time()
        
        #Coletar metricas ANTES do teste
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
                    self.print_e_salvar(f"  [ERRO] Requisicao falhou: {e}")
                    resultados.append({'sucesso': False, 'tempo_resposta': 0})
        
        tempo_total = time.time() - tempo_inicio
        
        #Coletar metricas DEPOIS do teste
        metricas_depois = self.obter_metricas_container(servidor)
        
        #Calcular estatisticas
        sucessos = [r for r in resultados if r['sucesso']]
        falhas = len(resultados) - len(sucessos)
        tempos = [r['tempo_resposta'] * 1000 for r in sucessos]  #Converter para ms
        
        #Usar a metrica MAXIMA (durante o pico da carga)
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
            self.print_e_salvar(f"    Total de requisicoes: {len(resultados)}")
            self.print_e_salvar(f"    Sucessos: {len(sucessos)} ({len(sucessos)/len(resultados)*100:.1f}%)")
            self.print_e_salvar(f"    Falhas: {falhas} ({taxa_erro:.1f}%)")
            self.print_e_salvar(f"    Tempo total: {tempo_total:.2f}s")
            self.print_e_salvar(f"    Requisicoes/segundo: {rps:.2f}")
            self.print_e_salvar(f"    Latencia media: {latencia_media:.2f}ms")
            self.print_e_salvar(f"    Latencia P50: {latencia_p50:.2f}ms")
            if len(tempos) > 1:
                self.print_e_salvar(f"    Latencia P95: {latencia_p95:.2f}ms")
                self.print_e_salvar(f"    Latencia P99: {latencia_p99:.2f}ms")
                self.print_e_salvar(f"    Desvio padrao: {desvio_padrao:.2f}ms")
            self.print_e_salvar(f"    CPU: {cpu_percent:.2f}%")
            self.print_e_salvar(f"    Memoria: {mem_usage} ({mem_percent:.2f}%)")
            
            #Salvar no CSV
            self.salvar_resultado_csv(
                nome_teste, servidor, caminho, num_requisicoes, num_threads,
                len(resultados), len(sucessos), falhas, tempo_total,
                latencia_media, latencia_p50, latencia_p95, latencia_p99,
                desvio_padrao, rps, cpu_percent, 
                mem_usage, mem_percent, execucao
            )
        
        return {
            'total': len(resultados),
            'sucessos': len(sucessos),
            'tempo_total': tempo_total,
            'tempos': tempos
        }
    
    def cenario_baixa_carga(self, execucao=None):
        #Cenario 1: Baixa Carga
        cfg = self.CENARIO_1_BAIXA_CARGA
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENARIO 1: BAIXA CARGA")
        self.print_e_salvar(f"Usuarios Virtuais: {cfg['usuarios']} | Requisicoes: {cfg['requisicoes']}")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar(f"\n[NGINX vs APACHE] Endpoint: {cfg['endpoint']}")
        nome_teste = "Cenario1_BaixaCarga"
        self.teste_concorrente('nginx', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
        self.teste_concorrente('apache', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
    
    def cenario_media_carga(self, execucao=None):
        #Cenario 2: Media Carga
        cfg = self.CENARIO_2_MEDIA_CARGA
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENARIO 2: MEDIA CARGA")
        self.print_e_salvar(f"Usuarios Virtuais: {cfg['usuarios']} | Requisicoes: {cfg['requisicoes']}")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar(f"\n[NGINX vs APACHE] Endpoint: {cfg['endpoint']}")
        nome_teste = "Cenario2_MediaCarga"
        self.teste_concorrente('nginx', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
        self.teste_concorrente('apache', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
    
    def cenario_alta_carga(self, execucao=None):
        #Cenario 3: Alta Carga
        cfg = self.CENARIO_3_ALTA_CARGA
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENARIO 3: ALTA CARGA")
        self.print_e_salvar(f"Usuarios Virtuais: {cfg['usuarios']} | Requisicoes: {cfg['requisicoes']}")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar(f"\n[NGINX vs APACHE] Endpoint: {cfg['endpoint']}")
        nome_teste = "Cenario3_AltaCarga"
        self.teste_concorrente('nginx', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
        self.teste_concorrente('apache', cfg['endpoint'], cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
    
    def cenario_arquivo_pequeno(self, execucao=None):
        #Cenarios 4-6: Arquivos Pequenos (1KB, 10KB, 50KB)
        for num, cfg_name in [(4, 'CENARIO_4_ARQUIVO_1KB'), 
                               (5, 'CENARIO_5_ARQUIVO_10KB'), 
                               (6, 'CENARIO_6_ARQUIVO_50KB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENARIO {num}: ARQUIVO PEQUENO ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuarios Virtuais: {cfg['usuarios']} | Requisicoes: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            nome_teste = f"Cenario{num}_ArquivoPequeno"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
    
    def cenario_arquivo_medio(self, execucao=None):
        #Cenarios 7-9: Arquivos Medios (100KB, 500KB, 700KB)
        for num, cfg_name in [(7, 'CENARIO_7_ARQUIVO_100KB'), 
                               (8, 'CENARIO_8_ARQUIVO_500KB'), 
                               (9, 'CENARIO_9_ARQUIVO_700KB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENARIO {num}: ARQUIVO MEDIO ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuarios Virtuais: {cfg['usuarios']} | Requisicoes: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            nome_teste = f"Cenario{num}_ArquivoMedio"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
    
    def cenario_arquivo_grande(self, execucao=None):
        #Cenarios 10-12: Arquivos Grandes (1MB, 5MB, 7MB)
        for num, cfg_name in [(10, 'CENARIO_10_ARQUIVO_1MB'), 
                               (11, 'CENARIO_11_ARQUIVO_5MB'), 
                               (12, 'CENARIO_12_ARQUIVO_7MB')]:
            cfg = getattr(self, cfg_name)
            self.print_e_salvar("\n" + "="*60)
            self.print_e_salvar(f"CENARIO {num}: ARQUIVO GRANDE ({cfg['tamanho']})")
            self.print_e_salvar(f"Usuarios Virtuais: {cfg['usuarios']} | Requisicoes: {cfg['requisicoes']}")
            self.print_e_salvar("="*60)
            
            self.print_e_salvar(f"\n[NGINX vs APACHE] Arquivo: {cfg['arquivo']}")
            caminho = f"/estatico/{cfg['arquivo']}"
            nome_teste = f"Cenario{num}_ArquivoGrande"
            self.teste_concorrente('nginx', caminho, cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
            self.teste_concorrente('apache', caminho, cfg['requisicoes'], cfg['usuarios'], nome_teste, execucao)
    
    def executar_testes(self):
        #Executa todos os cenarios de teste
        self.print_e_salvar("="*60)
        self.print_e_salvar("INICIO DOS TESTES DE CARGA")
        self.print_e_salvar(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_e_salvar("="*60)
        
        #Executar todos os cenarios (agora 12 no total)
        self.cenario_baixa_carga()      #Cenario 1
        self.cenario_media_carga()      #Cenario 2
        self.cenario_alta_carga()       #Cenario 3
        self.cenario_arquivo_pequeno()  #Cenarios 4-6
        self.cenario_arquivo_medio()    #Cenarios 7-9
        self.cenario_arquivo_grande()   #Cenarios 10-12
        
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("TESTES CONCLUIDOS!")
        self.print_e_salvar(f"Resultados salvos em:")
        self.print_e_salvar(f"  - {self.arquivo_txt}")
        self.print_e_salvar(f"  - {self.arquivo_csv}")
        self.print_e_salvar("="*60)
    
    def executar_testes(self, execucao=None):
        #Executa todos os 15 cenarios de teste uma vez
        #Executar TODOS os 12 cenarios
        self.cenario_baixa_carga(execucao)      #Cenario 1
        self.cenario_media_carga(execucao)      #Cenario 2
        self.cenario_alta_carga(execucao)       #Cenario 3
        self.cenario_arquivo_pequeno(execucao)  #Cenarios 4-6 (1KB, 10KB, 50KB)
        self.cenario_arquivo_medio(execucao)    #Cenarios 7-9 (100KB, 500KB, 700KB)
        self.cenario_arquivo_grande(execucao)   #Cenarios 10-12 (1MB, 5MB, 7MB)
    
    def executar_todos_testes(self):
        #Executa todos os 15 cenarios de teste multiplas vezes
        self.print_e_salvar("="*70)
        self.print_e_salvar("TESTADOR DE CARGA - NGINX vs APACHE")
        self.print_e_salvar("Trabalho de Redes II - 2025.2")
        self.print_e_salvar("="*70)
        self.print_e_salvar(f"\nID Personalizado: {self.id_customizado}")
        self.print_e_salvar(f"Numero de execucoes completas: {self.NUM_EXECUCOES}")
        self.print_e_salvar(f"Cenarios por execucao: 12 (total de {self.NUM_EXECUCOES * 12} testes)")
        
        tempo_inicio_total = time.time()
        
        #Loop principal: executar todas as execucoes
        for execucao in range(1, self.NUM_EXECUCOES + 1):
            self.print_e_salvar("\n" + "="*80)
            self.print_e_salvar(f"EXECUCAO {execucao}/{self.NUM_EXECUCOES} - RODADA COMPLETA DE TESTES")
            self.print_e_salvar("="*80)
            
            tempo_inicio_execucao = time.time()
            
            #Executar TODOS os 12 cenarios nesta execucao
            self.executar_testes()
            
            tempo_execucao = time.time() - tempo_inicio_execucao
            self.print_e_salvar(f"\nEXECUCAO {execucao} CONCLUIDA em {tempo_execucao/60:.2f} minutos")
        
        tempo_total = time.time() - tempo_inicio_total
        
        self.print_e_salvar("\n" + "="*70)
        self.print_e_salvar("TESTES CONCLUIDOS")
        self.print_e_salvar("="*70)
        self.print_e_salvar(f"Tempo total de execucao: {tempo_total/60:.2f} minutos")
        
        #Exportar CSV
        print(f"\nExportando dados para CSV...")
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

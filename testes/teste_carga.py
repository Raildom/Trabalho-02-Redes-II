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
import subprocess
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
        print(f"\n[AVISO] Métricas de CPU/Memória:")
        print(f"  As métricas podem aparecer como 0% se executadas de dentro do container.")
        print(f"  Para métricas em tempo real, use Prometheus (http://localhost:9090)")
        print(f"  ou execute 'docker stats' em outro terminal durante os testes.")
    
    def print_e_salvar(self, texto):
        #Imprime no terminal e salva no arquivo TXT
        print(texto)
        self.txt_file.write(texto + '\n')
        self.txt_file.flush()
    
    def obter_metricas_container(self, servidor):
        #Obtém métricas de CPU e Memória do container via docker stats
        #Nota: Este método tenta coletar métricas do host Docker.
        #Se executado de dentro de um container, pode não funcionar.
        #Use Prometheus/Grafana para métricas em tempo real.
        nome_container = f"servidor_{servidor}"
        try:
            resultado = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 
                 '{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}', nome_container],
                capture_output=True, text=True, timeout=5
            )
            if resultado.returncode == 0:
                linha = resultado.stdout.strip()
                partes = linha.split(',')
                if len(partes) >= 3:
                    cpu_perc = partes[0].replace('%', '').strip()
                    mem_uso = partes[1].split('/')[0].strip()  #Ex: "25MiB / 1GiB" -> "25MiB"
                    mem_perc = partes[2].replace('%', '').strip()
                    return {
                        'cpu_percent': float(cpu_perc),
                        'mem_usage': mem_uso,
                        'mem_percent': float(mem_perc)
                    }
        except Exception:
            pass
        #Retorna valores padrão (use Prometheus para métricas reais)
        return {'cpu_percent': 0.0, 'mem_usage': 'Use_Prometheus', 'mem_percent': 0.0}
    
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
        #Cenário 1: Baixa Carga - 10 usuários virtuais, 100 execuções
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 1: BAIXA CARGA")
        self.print_e_salvar("Usuários Virtuais: 10 | Execuções: 100")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar("\n[NGINX vs APACHE] Endpoint: /api/info")
        self.teste_concorrente('nginx', '/api/info', 100, 10, "Cenario1_BaixaCarga")
        self.teste_concorrente('apache', '/api/info', 100, 10, "Cenario1_BaixaCarga")
    
    def cenario_media_carga(self):
        #Cenário 2: Média Carga - 50 usuários virtuais, 500 execuções
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 2: MÉDIA CARGA")
        self.print_e_salvar("Usuários Virtuais: 50 | Execuções: 500")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar("\n[NGINX vs APACHE] Endpoint: /api/status")
        self.teste_concorrente('nginx', '/api/status', 500, 50, "Cenario2_MediaCarga")
        self.teste_concorrente('apache', '/api/status', 500, 50, "Cenario2_MediaCarga")
    
    def cenario_alta_carga(self):
        #Cenário 3: Alta Carga - 100 usuários virtuais, 1000 execuções
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 3: ALTA CARGA")
        self.print_e_salvar("Usuários Virtuais: 100 | Execuções: 1000")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar("\n[NGINX vs APACHE] Endpoint: /api/dados")
        self.teste_concorrente('nginx', '/api/dados', 1000, 100, "Cenario3_AltaCarga")
        self.teste_concorrente('apache', '/api/dados', 1000, 100, "Cenario3_AltaCarga")
    
    def cenario_arquivo_pequeno(self):
        #Cenário 4: Arquivo Pequeno - 20 usuários, 200 execuções
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 4: ARQUIVO PEQUENO (10KB)")
        self.print_e_salvar("Usuários Virtuais: 20 | Execuções: 200")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar("\n[NGINX vs APACHE] Arquivo: pequeno-10kb.txt")
        self.teste_concorrente('nginx', '/estatico/pequeno-10kb.txt', 200, 20, "Cenario4_ArquivoPequeno")
        self.teste_concorrente('apache', '/estatico/pequeno-10kb.txt', 200, 20, "Cenario4_ArquivoPequeno")
    
    def cenario_arquivo_medio(self):
        #Cenário 5: Arquivo Médio - 15 usuários, 150 execuções
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 5: ARQUIVO MÉDIO (500KB)")
        self.print_e_salvar("Usuários Virtuais: 15 | Execuções: 150")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar("\n[NGINX vs APACHE] Arquivo: medio-500kb.txt")
        self.teste_concorrente('nginx', '/estatico/medio-500kb.txt', 150, 15, "Cenario5_ArquivoMedio")
        self.teste_concorrente('apache', '/estatico/medio-500kb.txt', 150, 15, "Cenario5_ArquivoMedio")
    
    def cenario_arquivo_grande(self):
        #Cenário 6: Arquivo Grande - 10 usuários, 50 execuções
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("CENÁRIO 6: ARQUIVO GRANDE (5MB)")
        self.print_e_salvar("Usuários Virtuais: 10 | Execuções: 50")
        self.print_e_salvar("="*60)
        
        self.print_e_salvar("\n[NGINX vs APACHE] Arquivo: grande-5mb.txt")
        self.teste_concorrente('nginx', '/estatico/grande-5mb.txt', 50, 10, "Cenario6_ArquivoGrande")
        self.teste_concorrente('apache', '/estatico/grande-5mb.txt', 50, 10, "Cenario6_ArquivoGrande")
        
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
        
        #Executar todos os 6 cenários
        self.cenario_baixa_carga()
        self.cenario_media_carga()
        self.cenario_alta_carga()
        self.cenario_arquivo_pequeno()
        self.cenario_arquivo_medio()
        self.cenario_arquivo_grande()
        
        self.print_e_salvar("\n" + "="*60)
        self.print_e_salvar("TESTES CONCLUÍDOS!")
        self.print_e_salvar(f"Resultados salvos em:")
        self.print_e_salvar(f"  - {self.arquivo_txt}")
        self.print_e_salvar(f"  - {self.arquivo_csv}")
        self.print_e_salvar("="*60)
    
    def executar_todos_testes(self):
        #Executa todos os cenários de teste
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

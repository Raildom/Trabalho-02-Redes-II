#!/usr/bin/env python3

#Teste Completo do Projeto Re# ============================================================================
#CONFIGURACOES DE TESTE
#============================================================================

#Quantidades de clientes simultaneos para testar (altere aqui)
clientes_teste = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

#Numero de requisicoes por cliente em cada teste (altere aqui)  
requisicoes_por_cliente = 2

#Numero de execucoes para cada teste (para calcular media e desvio padrao)
execucoes_por_teste = 10

concorrencia_clientes = 5
concorrencia_requisicoes = 2

import sys
import os
import csv
import time
import argparse
import threading
import statistics
from datetime import datetime

#Classe para cores no terminal
class Cores:
    VERDE = '\033[92m'    # Verde para sucesso
    VERMELHO = '\033[91m' # Vermelho para erro
    AMARELO = '\033[93m'  # Amarelo para aviso
    AZUL = '\033[94m'     # Azul para informação
    MAGENTA = '\033[95m'  # Magenta para destaque
    CIANO = '\033[96m'    # Ciano para título
    RESET = '\033[0m'     # Reset para cor normal
    NEGRITO = '\033[1m'   # Negrito

    @staticmethod
    def sucesso(texto):
        return f"{Cores.VERDE}[SUCESSO]{Cores.RESET} {texto}"
    
    @staticmethod
    def erro(texto):
        return f"{Cores.VERMELHO}[ERRO]{Cores.RESET} {texto}"
    
    @staticmethod
    def aviso(texto):
        return f"{Cores.AMARELO}[AVISO]{Cores.RESET} {texto}"
    
    @staticmethod
    def info(texto):
        return f"{Cores.AZUL}[INFO]{Cores.RESET} {texto}"

#Adicionar diretório src ao path (um nível acima da pasta testes)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from cliente import ClienteHTTP
    from configuracao import ID_CUSTOMIZADO, PORTA_SERVIDOR
except ImportError as e:
    print(Cores.erro(f"Erro ao importar módulos: {e}"))
    print("Certifique-se de estar no diretório correto do projeto")
    sys.exit(1)

class TestadorCarga:
    #Classe para executar testes de carga e concorrencia
    def __init__(self, host_servidor, porta_servidor=PORTA_SERVIDOR):
        self.cliente = ClienteHTTP(host_servidor, porta_servidor)
        self.resultados = []
        self.lock = threading.Lock()
        
    def teste_requisicao_unica(self, metodo='GET', caminho='/', id_cliente=None):
        #Executa um único teste de requisição
        resultado = self.cliente.enviar_requisicao(metodo, caminho)
        resultado['id_cliente'] = id_cliente
        resultado['timestamp'] = time.time()
        
        with self.lock:
            self.resultados.append(resultado)
        
        return resultado
    
    def teste_concorrente(self, num_clientes, requisicoes_por_cliente, metodo='GET', caminho='/'):
        #Executa teste com múltiplos clientes simultâneos
        threads = []
        self.resultados = []
        
        tempo_inicio = time.time()
        
        def executar_cliente(id_cliente):
            for i in range(requisicoes_por_cliente):
                self.teste_requisicao_unica(metodo, caminho, f"{id_cliente}-{i}")
                time.sleep(0.01)  #Pequeno delay entre requisições
        
        #Criar e iniciar threads
        for i in range(num_clientes):
            thread = threading.Thread(target=executar_cliente, args=(i,))
            threads.append(thread)
            thread.start()

        #Aguardar conclusão de todas as threads
        for thread in threads:
            thread.join()
        
        tempo_total = time.time() - tempo_inicio
        
        return {
            'tempo_total': tempo_total,
            'num_clientes': num_clientes,
            'requisicoes_por_cliente': requisicoes_por_cliente,
            'total_requisicoes': len(self.resultados),
            'resultados': self.resultados
        }
    
    def gerar_relatorio(self, resultado_teste):
        #Gera relatório detalhado do teste (silencioso durante execução automática)
        pass

class TestadorAutomatizado:
    #Classe para executar testes automatizados
    def __init__(self):
        self.resultados = {}
        
    def executar_todos_testes(self):
        #Executa todos os testes automatizados com multiplas execucoes
        
        #Endereços dos servidores (baseado no docker-compose)
        servidores = {
            'sequencial': '76.1.0.10',
            'concorrente': '76.1.0.11'
        }
        
        #Diferentes cenários de teste
        cenarios_teste = [
            {'nome': 'rapido', 'caminho': '/rapido', 'descricao': 'Processamento rapido'},
            {'nome': 'medio', 'caminho': '/medio', 'descricao': 'Processamento medio (0.5s)'},
            {'nome': 'lento', 'caminho': '/lento', 'descricao': 'Processamento lento (2s)'},
        ]
        
        #Configurações de teste (usando valores das configurações do topo)
        #Para alterar: modifique as variáveis no topo do arquivo
        
        for tipo_servidor, ip_servidor in servidores.items():
            self.resultados[tipo_servidor] = {}
            
            for cenario in cenarios_teste:
                self.resultados[tipo_servidor][cenario['nome']] = {}
                
                for num_clientes in clientes_teste:
                    #Realizar multiplas execucoes para calcular estatisticas
                    execucoes_resultados = []
                    
                    for execucao in range(execucoes_por_teste):
                        testador = TestadorCarga(ip_servidor)
                        resultado = testador.teste_concorrente(
                            num_clientes, 
                            requisicoes_por_cliente,
                            'GET',
                            cenario['caminho']
                        )
                        execucoes_resultados.append(resultado)
                        
                        #Pequena pausa entre execucoes para evitar sobrecarga
                        time.sleep(0.5)
                    
                    #Calcular estatisticas das multiplas execucoes
                    self.resultados[tipo_servidor][cenario['nome']][num_clientes] = self.calcular_estatisticas(execucoes_resultados)
        
        self.salvar_resultados()
        self.gerar_comparacao()
    
    def calcular_estatisticas(self, execucoes_resultados):
        #Calcula media e desvio padrao das multiplas execucoes
        if not execucoes_resultados:
            return None
            
        #Extrair metricas de cada execucao
        throughputs = []
        tempos_resposta_medios = []
        taxas_sucesso = []
        tempos_totais = []
        
        for resultado in execucoes_resultados:
            #Calcular throughput básico
            sucessos = len([r for r in resultado['resultados'] if r['sucesso']])
            throughput = sucessos / resultado['tempo_total'] if resultado['tempo_total'] > 0 else 0
            throughputs.append(throughput)
            
            #Calcular tempo de resposta medio
            tempos_resposta = [r['tempo_resposta'] for r in resultado['resultados'] if r['sucesso']]
            tempo_medio = statistics.mean(tempos_resposta) if tempos_resposta else 0
            tempos_resposta_medios.append(tempo_medio)
            
            #Calcular taxa de sucesso
            total = len(resultado['resultados'])
            taxa = (sucessos / total * 100) if total > 0 else 0
            taxas_sucesso.append(taxa)
            
            #Tempo total
            tempos_totais.append(resultado['tempo_total'])
        
        #Calcular estatisticas finais
        resultado_estatistico = {
            'throughput': {
                'media': statistics.mean(throughputs),
                'desvio_padrao': statistics.stdev(throughputs) if len(throughputs) > 1 else 0,
                'valores': throughputs
            },
            'tempo_resposta': {
                'media': statistics.mean(tempos_resposta_medios),
                'desvio_padrao': statistics.stdev(tempos_resposta_medios) if len(tempos_resposta_medios) > 1 else 0,
                'valores': tempos_resposta_medios
            },
            'taxa_sucesso': {
                'media': statistics.mean(taxas_sucesso),
                'desvio_padrao': statistics.stdev(taxas_sucesso) if len(taxas_sucesso) > 1 else 0,
                'valores': taxas_sucesso
            },
            'tempo_total': {
                'media': statistics.mean(tempos_totais),
                'desvio_padrao': statistics.stdev(tempos_totais) if len(tempos_totais) > 1 else 0,
                'valores': tempos_totais
            },
            'execucoes': len(execucoes_resultados),
            'resultados_detalhados': execucoes_resultados  # Manter para compatibilidade
        }
        
        return resultado_estatistico
    
    def salvar_resultados(self):
        #Salva os resultados finais em arquivo TXT e CSV
        os.makedirs('/app/resultados', exist_ok=True)
        
        #Primeiro gerar o arquivo CSV
        self.gerar_csv()
        
        nome_arquivo = '/app/resultados/resultados dos testes.txt'
        
        with open(nome_arquivo, 'w', encoding='ascii', errors='ignore') as f:
            f.write(f"ID Personalizado: {ID_CUSTOMIZADO}\n")
            
            #Resumo detalhado por servidor
            for tipo_servidor in ['sequencial', 'concorrente']:
                if tipo_servidor in self.resultados:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"SERVIDOR {tipo_servidor.upper()}\n")
                    f.write(f"{'='*80}\n")
                    
                    #Estatísticas gerais do servidor
                    total_requisicoes = 0
                    total_sucessos = 0
                    
                    for cenario in ['rapido', 'medio', 'lento']:
                        if cenario in self.resultados[tipo_servidor]:
                            descricoes = {
                                'rapido': 'Processamento Instantaneo',
                                'medio': 'Processamento 0.5 segundos',
                                'lento': 'Processamento 2.0 segundos'
                            }
                            
                            f.write(f"\n[{cenario.upper()} - {descricoes[cenario]}]\n")
                            f.write(f"{'-'*60}\n")
                            
                            for num_clientes in clientes_teste:
                                if num_clientes in self.resultados[tipo_servidor][cenario]:
                                    resultado = self.resultados[tipo_servidor][cenario][num_clientes]
                                    
                                    #Usar estatisticas ja calculadas
                                    throughput_medio = resultado['throughput']['media']
                                    tempo_resposta_medio = resultado['tempo_resposta']['media']
                                    taxa_sucesso_media = resultado['taxa_sucesso']['media']
                                    tempo_total_medio = resultado['tempo_total']['media']
                                    execucoes = resultado['execucoes']
                                    
                                    #Para calcular totais, usar primeiro resultado detalhado
                                    primeiro_resultado = resultado['resultados_detalhados'][0] if resultado['resultados_detalhados'] else {}
                                    if primeiro_resultado:
                                        total_por_execucao = len(primeiro_resultado['resultados'])
                                        sucessos_por_execucao = len([r for r in primeiro_resultado['resultados'] if r['sucesso']])
                                        total_requisicoes += total_por_execucao * execucoes
                                        total_sucessos += sucessos_por_execucao * execucoes
                                        
                                        #Calcular requisições totais para este teste específico
                                        requisicoes_teste = total_por_execucao * execucoes
                                        sucessos_teste = sucessos_por_execucao * execucoes
                                    else:
                                        requisicoes_teste = 0
                                        sucessos_teste = 0
                                    
                                    #Linha principal com metricas estatisticas
                                    f.write(f"  {num_clientes:2d} clientes simultaneos (media de {execucoes} execucoes):\n")
                                    f.write(f"    - Requisicoes enviadas: {requisicoes_teste} total ({total_por_execucao if primeiro_resultado else 0} por execucao)\n")
                                    f.write(f"    - Sucessos: {sucessos_teste} | Taxa de sucesso media: {taxa_sucesso_media:5.1f}%\n")
                                    f.write(f"    - Throughput medio: {throughput_medio:.3f} req/s\n")
                                    f.write(f"    - Tempo medio de resposta: {tempo_resposta_medio*1000:6.1f}ms\n")
                                    f.write(f"    - Tempo medio de execucao: {tempo_total_medio:.2f} segundos\n")
                                    
                                    #Avaliacao qualitativa baseada no throughput medio
                                    if throughput_medio >= 50:
                                        avaliacao = "EXCELENTE"
                                    elif throughput_medio >= 20:
                                        avaliacao = "MUITO BOM"
                                    elif throughput_medio >= 10:
                                        avaliacao = "BOM"
                                    elif throughput_medio >= 5:
                                        avaliacao = "REGULAR"
                                    else:
                                        avaliacao = "BAIXO"
                                    
                                    f.write(f"    - Avaliacao de desempenho: {avaliacao}\n")
                                    
                                    #Mostrar desvios padrao para avaliar consistencia
                                    throughput_desvio = resultado['throughput']['desvio_padrao']
                                    tempo_desvio = resultado['tempo_resposta']['desvio_padrao']
                                    f.write(f"    - Desvio Padrao: Throughput +/-{throughput_desvio:.3f}, Tempo +/-{tempo_desvio*1000:.1f}ms\n")
                                    
                                    f.write(f"\n")
                    
                    #Resumo geral do servidor baseado nas estatisticas
                    if total_requisicoes > 0:
                        taxa_geral = (total_sucessos / total_requisicoes * 100)
                        f.write(f"{'-'*60}\n")
                        f.write(f"RESUMO GERAL DO SERVIDOR {tipo_servidor.upper()}:\n")
                        f.write(f"  - Total de requisicoes estimadas: {total_requisicoes}\n")
                        f.write(f"  - Taxa de sucesso estimada: {taxa_geral:.1f}%\n")
                        
                        #Classificacao geral baseada na taxa de sucesso
                        if taxa_geral >= 99:
                            classificacao = "EXCELENTE - Sistema muito confiavel"
                        elif taxa_geral >= 95:
                            classificacao = "MUITO BOM - Sistema confiavel"
                        elif taxa_geral >= 90:
                            classificacao = "BOM - Sistema estavel"
                        elif taxa_geral >= 80:
                            classificacao = "REGULAR - Necessita melhorias"
                        else:
                            classificacao = "CRITICO - Sistema instavel"
                        
                        f.write(f"  - Classificacao: {classificacao}\n")
                    else:
                        f.write(f"{'-'*60}\n")
                        f.write(f"RESUMO GERAL DO SERVIDOR {tipo_servidor.upper()}:\n")
                        f.write(f"  - Nenhum dado de teste disponivel\n")
            
            #Comparacao detalhada entre servidores
            f.write(f"\n{'='*80}\n")
            f.write("                  COMPARACAO DETALHADA ENTRE SERVIDORES\n")
            f.write(f"{'='*80}\n")
            
            if 'sequencial' in self.resultados and 'concorrente' in self.resultados:
                #Cabecalho da tabela de comparacao
                f.write(f"\nFormato: [Cenario] Clientes -> Sequencial vs Concorrente (Diferenca)\n")
                f.write(f"{'-'*80}\n")
                
                for cenario in ['rapido', 'medio', 'lento']:
                    if (cenario in self.resultados['sequencial'] and 
                        cenario in self.resultados['concorrente']):
                        
                        descricoes = {
                            'rapido': 'Processamento Instantaneo',
                            'medio': 'Processamento 0.5s',
                            'lento': 'Processamento 2.0s'
                        }
                        
                        f.write(f"\n[{cenario.upper()} - {descricoes[cenario]}]\n")
                        
                        melhorias_cenario = []
                        
                        for num_clientes in clientes_teste:
                            if (num_clientes in self.resultados['sequencial'][cenario] and 
                                num_clientes in self.resultados['concorrente'][cenario]):
                                
                                seq = self.resultados['sequencial'][cenario][num_clientes]
                                conc = self.resultados['concorrente'][cenario][num_clientes]
                                
                                #Usar estatisticas pre-calculadas
                                seq_throughput = seq['throughput']['media']
                                conc_throughput = conc['throughput']['media']
                                seq_tempo_medio = seq['tempo_resposta']['media'] * 1000  # converter para ms
                                conc_tempo_medio = conc['tempo_resposta']['media'] * 1000  # converter para ms
                                
                                f.write(f"  {num_clientes:2d} clientes simultaneos:\n")
                                f.write(f"    + Sequencial:  {seq_throughput:6.3f} req/s | Tempo medio: {seq_tempo_medio:6.1f}ms\n")
                                f.write(f"    + Concorrente: {conc_throughput:6.3f} req/s | Tempo medio: {conc_tempo_medio:6.1f}ms\n")
                                
                                if seq_throughput > 0 and conc_throughput > 0:
                                    melhoria_throughput = ((conc_throughput - seq_throughput) / seq_throughput) * 100
                                    melhoria_tempo = ((seq_tempo_medio - conc_tempo_medio) / seq_tempo_medio) * 100 if seq_tempo_medio > 0 else 0
                                    
                                    melhorias_cenario.append(melhoria_throughput)
                                    
                                    f.write(f"    > Throughput: ")
                                    if melhoria_throughput > 20:
                                        f.write(f"CONCORRENTE MUITO MELHOR (+{melhoria_throughput:5.1f}%)\n")
                                    elif melhoria_throughput > 5:
                                        f.write(f"CONCORRENTE MELHOR (+{melhoria_throughput:5.1f}%)\n")
                                    elif melhoria_throughput > -5:
                                        f.write(f"EMPATE TECNICO ({melhoria_throughput:+5.1f}%)\n")
                                    elif melhoria_throughput > -20:
                                        f.write(f"SEQUENCIAL MELHOR ({melhoria_throughput:5.1f}%)\n")
                                    else:
                                        f.write(f"SEQUENCIAL MUITO MELHOR ({melhoria_throughput:5.1f}%)\n")
                                    
                                    f.write(f"    > Tempo resposta: ")
                                    if melhoria_tempo > 20:
                                        f.write(f"CONCORRENTE MUITO MAIS RAPIDO (-{abs(melhoria_tempo):5.1f}%)\n")
                                    elif melhoria_tempo > 5:
                                        f.write(f"CONCORRENTE MAIS RAPIDO (-{abs(melhoria_tempo):5.1f}%)\n")
                                    elif melhoria_tempo > -5:
                                        f.write(f"TEMPOS SIMILARES ({melhoria_tempo:+5.1f}%)\n")
                                    elif melhoria_tempo > -20:
                                        f.write(f"SEQUENCIAL MAIS RAPIDO (+{abs(melhoria_tempo):5.1f}%)\n")
                                    else:
                                        f.write(f"SEQUENCIAL MUITO MAIS RAPIDO (+{abs(melhoria_tempo):5.1f}%)\n")
                                else:
                                    f.write(f"    > ERRO: Não foi possível comparar (falhas nas requisições)\n")
                                
                                f.write(f"\n")
                        
                        #Resumo do cenario
                        if melhorias_cenario:
                            melhoria_media = sum(melhorias_cenario) / len(melhorias_cenario)
                            f.write(f"  Resumo do cenario {cenario.upper()}:\n")
                            if melhoria_media > 30:
                                f.write(f"    * CONCORRENTE MUITO SUPERIOR (media +{melhoria_media:.1f}%)\n")
                            elif melhoria_media > 15:
                                f.write(f"    * CONCORRENTE SUPERIOR (media +{melhoria_media:.1f}%)\n")
                            elif melhoria_media > 5:
                                f.write(f"    * CONCORRENTE LIGEIRAMENTE MELHOR (media +{melhoria_media:.1f}%)\n")
                            elif melhoria_media > -5:
                                f.write(f"    = DESEMPENHO SIMILAR (media {melhoria_media:+.1f}%)\n")
                            else:
                                f.write(f"    - SEQUENCIAL MELHOR (media {melhoria_media:+.1f}%)\n")
                        f.write(f"\n")
            

        
        print(Cores.sucesso(f"Resultados finais salvos em {nome_arquivo}"))
    
    def gerar_csv(self):
        """Gera arquivo CSV com todos os resultados dos testes incluindo estatisticas"""
        import csv
        
        nome_arquivo_csv = '/app/resultados/resultados_completos.csv'
        
        try:
            with open(nome_arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'servidor', 'cenario', 'num_clientes', 'execucoes',
                    'throughput_media', 'throughput_desvio', 
                    'tempo_resposta_media', 'tempo_resposta_desvio',
                    'taxa_sucesso_media', 'taxa_sucesso_desvio',
                    'tempo_total_media', 'tempo_total_desvio'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                #Processar dados de cada servidor
                for tipo_servidor in ['sequencial', 'concorrente']:
                    if tipo_servidor in self.resultados:
                        for cenario in ['rapido', 'medio', 'lento']:
                            if cenario in self.resultados[tipo_servidor]:
                                for num_clientes in clientes_teste:
                                    if num_clientes in self.resultados[tipo_servidor][cenario]:
                                        resultado = self.resultados[tipo_servidor][cenario][num_clientes]
                                        
                                        #Escrever linha no CSV com estatisticas
                                        writer.writerow({
                                            'servidor': tipo_servidor,
                                            'cenario': cenario,
                                            'num_clientes': num_clientes,
                                            'execucoes': resultado['execucoes'],
                                            'throughput_media': round(resultado['throughput']['media'], 3),
                                            'throughput_desvio': round(resultado['throughput']['desvio_padrao'], 3),
                                            'tempo_resposta_media': round(resultado['tempo_resposta']['media'] * 1000, 1),  # em ms
                                            'tempo_resposta_desvio': round(resultado['tempo_resposta']['desvio_padrao'] * 1000, 1),  # em ms
                                            'taxa_sucesso_media': round(resultado['taxa_sucesso']['media'], 1),
                                            'taxa_sucesso_desvio': round(resultado['taxa_sucesso']['desvio_padrao'], 1),
                                            'tempo_total_media': round(resultado['tempo_total']['media'], 2),
                                            'tempo_total_desvio': round(resultado['tempo_total']['desvio_padrao'], 2)
                                        })
            
            pass  # Arquivo CSV gerado silenciosamente
            
        except Exception as e:
            print(Cores.erro(f"Falha ao gerar CSV: {e}"))
    
    def gerar_comparacao(self):
        #Gera comparação entre servidores com estatisticas
        print(f"\n{Cores.CIANO}{Cores.NEGRITO}=== COMPARAÇÃO ENTRE SERVIDORES (ESTATÍSTICAS) ==={Cores.RESET}")
        
        if 'sequencial' in self.resultados and 'concorrente' in self.resultados:
            for cenario in ['rapido', 'medio', 'lento']:
                if cenario in self.resultados['sequencial'] and cenario in self.resultados['concorrente']:
                    print(f"\n--- Cenário: {cenario} ---")
                    
                    for num_clientes in clientes_teste:
                        if (num_clientes in self.resultados['sequencial'][cenario] and 
                            num_clientes in self.resultados['concorrente'][cenario]):
                            
                            seq = self.resultados['sequencial'][cenario][num_clientes]
                            conc = self.resultados['concorrente'][cenario][num_clientes]
                            
                            seq_throughput = seq['throughput']['media']
                            conc_throughput = conc['throughput']['media']
                            seq_desvio = seq['throughput']['desvio_padrao']
                            conc_desvio = conc['throughput']['desvio_padrao']
                            
                            print(f"  {num_clientes} clientes (media +/- desvio de {seq['execucoes']} execucoes):")
                            print(f"    Sequencial: {seq_throughput:.3f} +/- {seq_desvio:.3f} req/s")
                            print(f"    Concorrente: {conc_throughput:.3f} +/- {conc_desvio:.3f} req/s")
                            
                            if seq_throughput > 0:
                                melhoria = ((conc_throughput - seq_throughput) / seq_throughput) * 100
                                print(f"    Melhoria: {melhoria:.1f}%")

class TestadorProjeto:
    #Classe principal para testes do projeto
    def __init__(self):
        self.servidores_docker = {
            'sequencial': '76.1.0.10',
            'concorrente': '76.1.0.11'
        }
        self.servidores_local = {
            'sequencial': 'localhost:8080',
            'concorrente': 'localhost:8081'
        }
    
    def detectar_ambiente(self):
        #Detecta qual ambiente está disponível
        #Tenta Docker primeiro
        try:
            cliente = ClienteHTTP(self.servidores_docker['sequencial'])
            resultado = cliente.enviar_requisicao('GET', '/')
            if resultado['sucesso']:
                return 'docker'
        except:
            pass
        
        #Tenta local
        try:
            cliente = ClienteHTTP('localhost', 8080)
            resultado = cliente.enviar_requisicao('GET', '/')
            if resultado['sucesso']:
                return 'local'
        except:
            pass
        
        return None
    
    def teste_conectividade_basica(self, ambiente='docker'):
        #Executa teste básico de conectividade
        print("\n" + "="*70)
        print(f"{Cores.CIANO}{Cores.NEGRITO}                    TESTE DE CONECTIVIDADE{Cores.RESET}")
        print("="*70)
        
        if ambiente == 'docker':
            configuracao_rede = "76.01.0.0/16"
            ip_servidor = "76.01.0.10"
            print(f"\n{Cores.AZUL}[CONFIGURAÇÃO DE REDE]{Cores.RESET}")
            print(f"  Ambiente:           Docker Contêineres")
            print(f"  Subnet configurada: {configuracao_rede}")
            print(f"  IP base servidor:   {ip_servidor}")
            print(f"  ID Personalizado:   {ID_CUSTOMIZADO}")
        else:
            print(f"\n{Cores.AZUL}[CONFIGURAÇÃO DE REDE]{Cores.RESET}")
            print(f"  Ambiente:           Local (Host)")
            print(f"  ID Personalizado:   {ID_CUSTOMIZADO}")
        
        servidores = self.servidores_docker if ambiente == 'docker' else self.servidores_local
        resultados_conectividade = {}
        
        print(f"\n[TESTANDO SERVIDORES]")
        for tipo_servidor, endereco in servidores.items():
            print(f"\n  Servidor {tipo_servidor.upper()} ({endereco})")
            print(f"  {'-'*50}")
            
            try:
                if ':' in endereco:
                    host, porta = endereco.split(':')
                    cliente = ClienteHTTP(host, int(porta))
                else:
                    cliente = ClienteHTTP(endereco)
                
                #Executa múltiplas requisições para teste mais robusto
                testes = []
                for i in range(3):
                    resultado = cliente.enviar_requisicao('GET', '/')
                    testes.append(resultado)
                
                sucessos = [t for t in testes if t['sucesso']]
                resultados_conectividade[tipo_servidor] = {
                    'total': len(testes),
                    'sucessos': len(sucessos),
                    'falhas': len(testes) - len(sucessos)
                }
                
                if sucessos:
                    tempo_medio = sum(t['tempo_resposta'] for t in sucessos) / len(sucessos)
                    tempo_min = min(t['tempo_resposta'] for t in sucessos)
                    tempo_max = max(t['tempo_resposta'] for t in sucessos)
                    
                    print(f"  Status:               [CONECTADO]")
                    print(f"  Código HTTP:          {sucessos[0]['codigo_status']}")
                    print(f"  Taxa de sucesso:      {len(sucessos)}/{len(testes)} ({len(sucessos)/len(testes)*100:.0f}%)")
                    print(f"  Tempo médio:          {tempo_medio*1000:.1f} ms")
                    print(f"  Tempo mínimo:         {tempo_min*1000:.1f} ms")
                    print(f"  Tempo máximo:         {tempo_max*1000:.1f} ms")
                    
                    #Verificar cabeçalhos
                    cabecalhos = sucessos[0].get('cabecalhos', {})
                    if 'X-Custom-ID' in cabecalhos:
                        print(f"  X-Custom-ID:          [PRESENTE] {cabecalhos['X-Custom-ID'][:16]}...")
                    else:
                        print(f"  X-Custom-ID:          [AUSENTE]")
                        
                    #Avaliação de desempenho
                    if tempo_medio < 0.050:
                        print(f"  Avaliação:            EXCELENTE (< 50ms)")
                    elif tempo_medio < 0.100:
                        print(f"  Avaliação:            MUITO BOM (< 100ms)")
                    elif tempo_medio < 0.200:
                        print(f"  Avaliação:            BOM (< 200ms)")
                    else:
                        print(f"  Avaliação:            LENTO (> 200ms)")
                        
                else:
                    print(f"  Status:               [DESCONECTADO]")
                    print(f"  Erro:                 {testes[0].get('erro', 'Erro desconhecido')}")
                    
            except Exception as e:
                print(f"  Status:               [ERRO CRÍTICO]")
                print(f"  Exceção:              {str(e)}")
                resultados_conectividade[tipo_servidor] = {
                    'total': 0,
                    'sucessos': 0,
                    'falhas': 1
                }
        
        #Resumo final
        print(f"\n{'='*70}")
        print(f"                      RESUMO DE CONECTIVIDADE")
        print(f"{'='*70}")
        
        total_servidores = len(servidores)
        servidores_online = sum(1 for r in resultados_conectividade.values() if r['sucessos'] > 0)
        
        print(f"\n[RESUMO GERAL]")
        print(f"  Servidores testados:      {total_servidores}")
        print(f"  Servidores online:        {servidores_online}")
        print(f"  Servidores offline:       {total_servidores - servidores_online}")
        print(f"  Taxa de disponibilidade:  {servidores_online/total_servidores*100:.0f}%")
        
        if servidores_online == total_servidores:
            print(f"  Status geral:             [TODOS OPERACIONAIS]")
        elif servidores_online > 0:
            print(f"  Status geral:             [PARCIALMENTE OPERACIONAL]")
        else:
            print(f"  Status geral:             [SISTEMA INDISPONÍVEL]")
        
        print(f"\n  Para executar todos os testes, use:")
        print(f"  python teste_completo.py --completo")
        print(f"{'='*70}")
    
    def teste_endpoints(self, ambiente='docker'):
        #Testa diferentes endpoints dos servidores
        print("\n" + "="*70)
        print("                    TESTE DE ENDPOINTS")
        print("="*70)
        
        servidores = self.servidores_docker if ambiente == 'docker' else self.servidores_local
        endpoints_config = [
            {'path': '/', 'nome': 'Raiz', 'descricao': 'Endpoint padrão'},
            {'path': '/rapido', 'nome': 'Rápido', 'descricao': 'Processamento instantâneo'},
            {'path': '/medio', 'nome': 'Médio', 'descricao': 'Processamento 0.5s'},
            {'path': '/lento', 'nome': 'Lento', 'descricao': 'Processamento 2s'}
        ]
        
        resultados_endpoints = {}
        
        for tipo_servidor, endereco in servidores.items():
            print(f"\n[SERVIDOR {tipo_servidor.upper()}] ({endereco})")
            print(f"  {'-'*60}")
            
            if ':' in endereco:
                host, porta = endereco.split(':')
                cliente = ClienteHTTP(host, int(porta))
            else:
                cliente = ClienteHTTP(endereco)
            
            resultados_servidor = {}
            
            for endpoint_config in endpoints_config:
                endpoint = endpoint_config['path']
                nome = endpoint_config['nome']
                descricao = endpoint_config['descricao']
                
                try:
                    resultado = cliente.enviar_requisicao('GET', endpoint)
                    
                    if resultado['sucesso']:
                        tempo_ms = resultado['tempo_resposta'] * 1000
                        status_icon = "[OK]" if resultado['codigo_status'] == 200 else "[!]"
                        
                        print(f"  {nome:8} {endpoint:8} {status_icon} HTTP {resultado['codigo_status']} - {tempo_ms:6.1f} ms - {descricao}")
                        
                        resultados_servidor[endpoint] = {
                            'sucesso': True,
                            'tempo': resultado['tempo_resposta'],
                            'status': resultado['codigo_status']
                        }
                    else:
                        print(f"  {nome:8} {endpoint:8} [X] ERRO     - {resultado.get('erro', 'Falha na requisição')}")
                        resultados_servidor[endpoint] = {
                            'sucesso': False,
                            'erro': resultado.get('erro', 'Erro desconhecido')
                        }
                        
                except Exception as e:
                    print(f"  {nome:8} {endpoint:8} [X] EXCEÇÃO - {str(e)}")
                    resultados_servidor[endpoint] = {
                        'sucesso': False,
                        'erro': str(e)
                    }
            
            resultados_endpoints[tipo_servidor] = resultados_servidor
            
            #Estatísticas do servidor
            sucessos = sum(1 for r in resultados_servidor.values() if r.get('sucesso', False))
            total = len(resultados_servidor)
            print(f"  {'-'*60}")
            print(f"  Endpoints funcionais: {sucessos}/{total} ({sucessos/total*100:.0f}%)")
            
            if sucessos > 0:
                tempos = [r['tempo'] for r in resultados_servidor.values() if r.get('sucesso', False)]
                tempo_medio = sum(tempos) / len(tempos)
                print(f"  Tempo médio:         {tempo_medio*1000:.1f} ms")
        
        #Resumo comparativo
        print(f"\n{'='*70}")
        print(f"                     RESUMO DE ENDPOINTS")
        print(f"{'='*70}")
        
        for endpoint_config in endpoints_config:
            endpoint = endpoint_config['path']
            nome = endpoint_config['nome']
            
            print(f"\n[{nome.upper()} - {endpoint}]")
            
            for tipo_servidor in servidores.keys():
                if tipo_servidor in resultados_endpoints and endpoint in resultados_endpoints[tipo_servidor]:
                    resultado = resultados_endpoints[tipo_servidor][endpoint]
                    if resultado.get('sucesso', False):
                        tempo_ms = resultado['tempo'] * 1000
                        print(f"  {tipo_servidor:12}: [OK] {tempo_ms:6.1f} ms (HTTP {resultado['status']})")
                    else:
                        print(f"  {tipo_servidor:12}: [ERRO] {resultado.get('erro', 'Falha')}")
                else:
                    print(f"  {tipo_servidor:12}: [N/A] Não testado")
        
        print(f"{'='*70}")
    
    def teste_validacao_cabecalho(self, ambiente='docker'):
        #Valida se o cabeçalho X-Custom-ID está presente
        print("\n=== Teste de Validação de Cabeçalho ===")
        
        servidores = self.servidores_docker if ambiente == 'docker' else self.servidores_local
        
        for tipo_servidor, endereco in servidores.items():
            print(f"\n--- Servidor {tipo_servidor} ---")
            
            if ':' in endereco:
                host, porta = endereco.split(':')
                cliente = ClienteHTTP(host, int(porta))
            else:
                cliente = ClienteHTTP(endereco)
            
            resultado = cliente.enviar_requisicao('GET', '/')
            
            if resultado['sucesso']:
                cabecalhos = resultado.get('cabecalhos', {})
                if 'X-Custom-ID' in cabecalhos:
                    print(f"  [SUCESSO] X-Custom-ID encontrado: {cabecalhos['X-Custom-ID']}")
                    if cabecalhos['X-Custom-ID'] == ID_CUSTOMIZADO:
                        print(f"  [SUCESSO] ID correto!")
                    else:
                        print(f"  [AVISO] ID diferente do esperado")
                else:
                    print(f"  [ERRO] X-Custom-ID não encontrado nos cabeçalhos")
            else:
                print(f"  [ERRO] Falha na requisição")
    
    def teste_concorrencia(self, ambiente='docker'):
        #Executa teste de concorrência básico
        print("\n=== Teste de Concorrência ===")
        
        servidores = self.servidores_docker if ambiente == 'docker' else self.servidores_local
        resultados = {}
        
        for tipo_servidor, endereco in servidores.items():
            print(f"\n--- Servidor {tipo_servidor} ---")
            
            if ':' in endereco:
                host, porta = endereco.split(':')
            else:
                host, porta = endereco, PORTA_SERVIDOR
            
            testador = TestadorCarga(host, int(porta))
            resultado = testador.teste_concorrente(concorrencia_clientes, concorrencia_requisicoes, 'GET', '/medio')
            testador.gerar_relatorio(resultado)
            resultados[tipo_servidor] = resultado
        
        return resultados
    
    def executar_tudo(self, ambiente=None):
        #Executa todos os testes disponíveis
        if ambiente is None:
            ambiente = self.detectar_ambiente()
            if ambiente is None:
                print("[ERRO] Nenhum servidor disponível")
                return
        
        print(f"=== Executando todos os testes (ambiente: {ambiente}) ===")
        
        self.teste_conectividade_basica(ambiente)
        self.teste_endpoints(ambiente)
        self.teste_validacao_cabecalho(ambiente)
        resultados_concorrencia = self.teste_concorrencia(ambiente)
        
        #Gerar CSV com os resultados dos testes de concorrência
        self.gerar_csv_basico(resultados_concorrencia)
        
        print("\n" + "="*60)
        
        return True

    #Gera arquivo CSV com os resultados dos testes básicos de concorrência
    def gerar_csv_basico(self, resultados_concorrencia):
        
        #Criar diretório se não existir
        os.makedirs('resultados', exist_ok=True)
        nome_arquivo_csv = 'resultados/resultados_completos.csv'
        
        try:
            with open(nome_arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'servidor', 'cenario', 'num_clientes', 'requisicoes_enviadas', 
                    'sucessos', 'falhas', 'taxa_sucesso', 'throughput', 
                    'tempo_total', 'tempo_medio_ms', 'tempo_min_ms', 'tempo_max_ms'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                #Processar dados de cada servidor
                for tipo_servidor, resultado in resultados_concorrencia.items():
                    #Calcular métricas
                    sucessos = len([r for r in resultado['resultados'] if r['sucesso']])
                    total = len(resultado['resultados'])
                    falhas = total - sucessos
                    taxa_sucesso = (sucessos / total * 100) if total > 0 else 0
                    throughput = sucessos / resultado['tempo_total'] if resultado['tempo_total'] > 0 else 0
                    
                    if sucessos > 0:
                        tempos = [r['tempo_resposta'] for r in resultado['resultados'] if r['sucesso']]
                        tempo_medio = sum(tempos) / len(tempos) * 1000  #em ms
                        tempo_min = min(tempos) * 1000
                        tempo_max = max(tempos) * 1000
                    else:
                        tempo_medio = tempo_min = tempo_max = 0
                    
                    #Escrever linha no CSV
                    writer.writerow({
                        'servidor': tipo_servidor,
                        'cenario': 'medio',
                        'num_clientes': concorrencia_clientes,
                        'requisicoes_enviadas': total,
                        'sucessos': sucessos,
                        'falhas': falhas,
                        'taxa_sucesso': round(taxa_sucesso, 1),
                        'throughput': round(throughput, 2),
                        'tempo_total': round(resultado['tempo_total'], 2),
                        'tempo_medio_ms': round(tempo_medio, 1),
                        'tempo_min_ms': round(tempo_min, 1),
                        'tempo_max_ms': round(tempo_max, 1)
                    })
            
            print(f"\n[SUCESSO] Arquivo CSV gerado: {nome_arquivo_csv}")
            
        except Exception as e:
            print(f"[ERRO] Falha ao gerar CSV: {e}")

def main():
    #Função principal
    parser = argparse.ArgumentParser(description='Testador Completo do Projeto Redes II')
    parser.add_argument('--ambiente', choices=['docker', 'local'], 
                       help='Especificar ambiente (docker ou local)')
    parser.add_argument('--conectividade', action='store_true',
                       help='Executar apenas teste de conectividade')
    parser.add_argument('--endpoints', action='store_true',
                       help='Executar apenas teste de endpoints')
    parser.add_argument('--cabecalho', action='store_true',
                       help='Executar apenas teste de validação de cabeçalho')
    parser.add_argument('--concorrencia', action='store_true',
                       help='Executar apenas teste de concorrência')
    parser.add_argument('--completo', action='store_true',
                       help='Executar testes automatizados completos')
    
    args = parser.parse_args()
    
    if args.completo:
        #Executar testes automatizados completos
        testador_auto = TestadorAutomatizado()
        testador_auto.executar_todos_testes()
    else:
        #Executar testes básicos
        testador = TestadorProjeto()
        
        #Se nenhum teste específico foi especificado, executar tudo
        if not any([args.conectividade, args.endpoints, args.cabecalho, args.concorrencia]):
            testador.executar_tudo(args.ambiente)
        else:
            #Detectar ambiente se não especificado
            ambiente = args.ambiente
            if ambiente is None:
                ambiente = testador.detectar_ambiente()
                if ambiente is None:
                    print("[ERRO] Nenhum servidor disponível")
                    return

            #Executar testes específicos
            if args.conectividade:
                testador.teste_conectividade_basica(ambiente)
            
            if args.endpoints:
                testador.teste_endpoints(ambiente)
            
            if args.cabecalho:
                testador.teste_validacao_cabecalho(ambiente)
            
            if args.concorrencia:
                testador.teste_concorrencia(ambiente)

if __name__ == "__main__":
    main()

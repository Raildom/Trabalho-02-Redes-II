#Script para gerar gráficos e análises dos resultados dos testes a partir do CSV
#Inclui estatisticas com media e desvio padrao de multiplas execucoes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import os

#Classe para cores no terminal
class Cores:
    VERDE = '\033[92m'    #Verde para sucesso
    VERMELHO = '\033[91m' #Vermelho para erro
    AMARELO = '\033[93m'  #Amarelo para aviso
    AZUL = '\033[94m'     #Azul para informação
    RESET = '\033[0m'     #Reset para cor normal

    @staticmethod
    def sucesso(texto):
        return f"{Cores.VERDE}[SUCESSO]{Cores.RESET} {texto}"
    
    @staticmethod
    def erro(texto):
        return f"{Cores.VERMELHO}[ERRO]{Cores.RESET} {texto}"
    
    @staticmethod
    def info(texto):
        return f"{Cores.AZUL}[INFO]{Cores.RESET} {texto}"

class AnalisadorResultados:
    def __init__(self, arquivo_csv='resultados/resultados_completos.csv'):
        self.arquivo_csv = arquivo_csv
        self.df = None
        self.carregar_resultados_csv()
        
    def carregar_resultados_csv(self):
        #Carrega os resultados dos testes do arquivo CSV
        try:
            self.df = pd.read_csv(self.arquivo_csv)
            
            #Assumir 2 requisições por cliente (conforme configuração do teste)
            requisicoes_por_cliente = 2
            self.df['num_requisicoes'] = self.df['num_clientes'] * requisicoes_por_cliente
            
            print(Cores.info(f"Dados carregados: {len(self.df)} registros encontrados"))
        except FileNotFoundError:
            print(Cores.erro(f"Arquivo CSV não encontrado: {self.arquivo_csv}"))
            print("Execute primeiro os testes completos para gerar o arquivo CSV")
            self.df = None
        except Exception as e:
            print(Cores.erro(f"Erro ao carregar CSV: {e}"))
            self.df = None
    
    def gerar_todos_graficos(self):
        #Gera todos os gráficos de análise a partir do CSV com barras de erro
        if self.df is None or self.df.empty:
            print(Cores.erro("Nenhum resultado disponível para análise"))
            return
        
        print(Cores.info("Configurando estilo dos gráficos..."))
        #Configura o estilo dos gráficos
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
        #Cria diretório para gráficos
        os.makedirs('resultados/graficos', exist_ok=True)
        
        print(Cores.info("Gerando gráficos..."))
        
        #Gráficos individuais
        print(Cores.info("  • Plotando throughput..."))
        self.plotar_throughput_estatistico()
        
        print(Cores.info("  • Plotando tempo de resposta..."))
        self.plotar_tempo_resposta_estatistico()
        
        print(Cores.info("  • Plotando taxa de sucesso..."))
        self.plotar_taxa_sucesso_estatistico()
        
        print(Cores.info("  • Plotando tempo total (com desvio padrão)..."))
        self.plotar_tempo_total_estatistico()
        
        print(Cores.info("  • Plotando comparação de escalabilidade..."))
        self.plotar_comparacao_escalabilidade_estatistico()
        
        print(Cores.sucesso("Gráficos com estatísticas salvos em resultados/graficos/"))

    def plotar_throughput_estatistico(self):
        #Plota gráfico de throughput com barras de erro - um gráfico por cenário
        cenarios = ['rapido', 'medio', 'lento']
        cenarios_nomes = ['Rápido', 'Médio', 'Lento']
        
        try:
            for i, cenario in enumerate(cenarios):
                plt.figure(figsize=(12, 8))
                dados_cenario = self.df[self.df['cenario'] == cenario]
                
                print(Cores.info(f"    - Processando cenário {cenarios_nomes[i]}: {len(dados_cenario)} registros"))
                
                if dados_cenario.empty:
                    plt.text(0.5, 0.5, f'Sem dados para cenário {cenarios_nomes[i]}', 
                            ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                    plt.title(f'Throughput - Cenário {cenarios_nomes[i]}', fontsize=16, fontweight='bold')
                    plt.savefig(f'resultados/graficos/throughput_{cenario}.png', dpi=300, bbox_inches='tight')
                    plt.close()
                    continue
                
                dados_seq = dados_cenario[dados_cenario['servidor'] == 'sequencial'].sort_values('num_requisicoes')
                dados_conc = dados_cenario[dados_cenario['servidor'] == 'concorrente'].sort_values('num_requisicoes')
                
                print(Cores.info(f"      Sequencial: {len(dados_seq)} registros, Concorrente: {len(dados_conc)} registros"))
                
                if not dados_seq.empty:
                    plt.plot(dados_seq['num_requisicoes'], dados_seq['throughput_media'], 
                            'o-', label='Servidor Sequencial', color='red', linewidth=3, 
                            markersize=10, alpha=0.8)
                
                if not dados_conc.empty:
                    plt.plot(dados_conc['num_requisicoes'], dados_conc['throughput_media'],
                            's-', label='Servidor Concorrente', color='blue', linewidth=3, 
                            markersize=10, alpha=0.8)
                
                execucoes = self.df['execucoes'].iloc[0] if not self.df.empty else 10
                plt.title(f'Throughput - Cenário {cenarios_nomes[i]}\n(Média de {execucoes} execuções)', 
                         fontsize=16, fontweight='bold', pad=20)
                plt.xlabel('Número de Requisições', fontsize=14, fontweight='bold')
                plt.ylabel('Throughput (requisições/segundo)', fontsize=14, fontweight='bold')
                plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
                plt.grid(True, alpha=0.3, linestyle='--')
                plt.xlim(left=0)
                plt.ylim(bottom=0)
                
                #Adicionar valores nos pontos
                if not dados_seq.empty:
                    for x, y in zip(dados_seq['num_requisicoes'], dados_seq['throughput_media']):
                        plt.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                                   xytext=(0,10), ha='center', fontsize=10, color='red')
                
                if not dados_conc.empty:
                    for x, y in zip(dados_conc['num_requisicoes'], dados_conc['throughput_media']):
                        plt.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                                   xytext=(0,10), ha='center', fontsize=10, color='blue')
                
                plt.tight_layout()
                plt.savefig(f'resultados/graficos/throughput_{cenario}.png', dpi=300, bbox_inches='tight')
                plt.close()
                
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar throughput: {e}"))

    def plotar_tempo_resposta_estatistico(self):
        #Plota gráfico de tempo de resposta com barras de erro - um gráfico por cenário
        cenarios = ['rapido', 'medio', 'lento']
        cenarios_nomes = ['Rápido', 'Médio', 'Lento']
        
        for i, cenario in enumerate(cenarios):
            plt.figure(figsize=(12, 8))
            dados_cenario = self.df[self.df['cenario'] == cenario]
            
            if dados_cenario.empty:
                plt.text(0.5, 0.5, f'Sem dados para cenário {cenarios_nomes[i]}', 
                        ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                plt.title(f'Tempo de Resposta - Cenário {cenarios_nomes[i]}', fontsize=16, fontweight='bold')
                plt.savefig(f'resultados/graficos/tempo_resposta_{cenario}.png', dpi=300, bbox_inches='tight')
                plt.close()
                continue
            
            dados_seq = dados_cenario[dados_cenario['servidor'] == 'sequencial'].sort_values('num_requisicoes')
            dados_conc = dados_cenario[dados_cenario['servidor'] == 'concorrente'].sort_values('num_requisicoes')
            
            if not dados_seq.empty:
                plt.plot(dados_seq['num_requisicoes'], dados_seq['tempo_resposta_media'],
                        'o-', label='Servidor Sequencial', color='red', linewidth=3, 
                        markersize=10, alpha=0.8)
            
            if not dados_conc.empty:
                plt.plot(dados_conc['num_requisicoes'], dados_conc['tempo_resposta_media'],
                        's-', label='Servidor Concorrente', color='blue', linewidth=3, 
                        markersize=10, alpha=0.8)
            
            execucoes = self.df['execucoes'].iloc[0] if not self.df.empty else 10
            plt.title(f'Tempo de Resposta - Cenário {cenarios_nomes[i]}\n(Média de {execucoes} execuções)', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Número de Requisições', fontsize=14, fontweight='bold')
            plt.ylabel('Tempo Médio de Resposta (ms)', fontsize=14, fontweight='bold')
            plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.xlim(left=0)
            plt.ylim(bottom=0)
            
            #Adicionar valores nos pontos
            if not dados_seq.empty:
                for x, y in zip(dados_seq['num_requisicoes'], dados_seq['tempo_resposta_media']):
                    plt.annotate(f'{y:.1f}ms', (x, y), textcoords="offset points", 
                               xytext=(0,10), ha='center', fontsize=10, color='red')
            
            if not dados_conc.empty:
                for x, y in zip(dados_conc['num_requisicoes'], dados_conc['tempo_resposta_media']):
                    plt.annotate(f'{y:.1f}ms', (x, y), textcoords="offset points", 
                               xytext=(0,10), ha='center', fontsize=10, color='blue')
            
            plt.tight_layout()
            plt.savefig(f'resultados/graficos/tempo_resposta_{cenario}.png', dpi=300, bbox_inches='tight')
            plt.close()

    def plotar_taxa_sucesso_estatistico(self):
        #Plota gráfico de taxa de sucesso com barras de erro - um gráfico por cenário
        cenarios = ['rapido', 'medio', 'lento']
        cenarios_nomes = ['Rápido', 'Médio', 'Lento']
        
        for i, cenario in enumerate(cenarios):
            plt.figure(figsize=(12, 8))
            dados_cenario = self.df[self.df['cenario'] == cenario]
            
            if dados_cenario.empty:
                plt.text(0.5, 0.5, f'Sem dados para cenário {cenarios_nomes[i]}', 
                        ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                plt.title(f'Taxa de Sucesso - Cenário {cenarios_nomes[i]}', fontsize=16, fontweight='bold')
                plt.savefig(f'resultados/graficos/taxa_sucesso_{cenario}.png', dpi=300, bbox_inches='tight')
                plt.close()
                continue
            
            dados_seq = dados_cenario[dados_cenario['servidor'] == 'sequencial'].sort_values('num_requisicoes')
            dados_conc = dados_cenario[dados_cenario['servidor'] == 'concorrente'].sort_values('num_requisicoes')
            
            if not dados_seq.empty:
                plt.plot(dados_seq['num_requisicoes'], dados_seq['taxa_sucesso_media'],
                        'o-', label='Servidor Sequencial', color='red', linewidth=3, 
                        markersize=10, alpha=0.8)
            
            if not dados_conc.empty:
                plt.plot(dados_conc['num_requisicoes'], dados_conc['taxa_sucesso_media'],
                        's-', label='Servidor Concorrente', color='blue', linewidth=3, 
                        markersize=10, alpha=0.8)
            
            execucoes = self.df['execucoes'].iloc[0] if not self.df.empty else 10
            plt.title(f'Taxa de Sucesso - Cenário {cenarios_nomes[i]}\n(Média de {execucoes} execuções)', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Número de Requisições', fontsize=14, fontweight='bold')
            plt.ylabel('Taxa de Sucesso (%)', fontsize=14, fontweight='bold')
            plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.xlim(left=0)
            plt.ylim(0, 105)  #Foco em 0-105% para melhor visualização

            #Adicionar valores nos pontos
            if not dados_seq.empty:
                for x, y in zip(dados_seq['num_requisicoes'], dados_seq['taxa_sucesso_media']):
                    plt.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                               xytext=(0,10), ha='center', fontsize=10, color='red')
            
            if not dados_conc.empty:
                for x, y in zip(dados_conc['num_requisicoes'], dados_conc['taxa_sucesso_media']):
                    plt.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                               xytext=(0,10), ha='center', fontsize=10, color='blue')
            
            plt.tight_layout()
            plt.savefig(f'resultados/graficos/taxa_sucesso_{cenario}.png', dpi=300, bbox_inches='tight')
            plt.close()

    def plotar_tempo_total_estatistico(self):
        #Plota gráfico de tempo total com barras de erro - um gráfico por cenário
        cenarios = ['rapido', 'medio', 'lento']
        cenarios_nomes = ['Rápido', 'Médio', 'Lento']
        
        for i, cenario in enumerate(cenarios):
            plt.figure(figsize=(12, 8))
            dados_cenario = self.df[self.df['cenario'] == cenario]
            
            if dados_cenario.empty:
                plt.text(0.5, 0.5, f'Sem dados para cenário {cenarios_nomes[i]}', 
                        ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
                plt.title(f'Tempo Total de Execução - Cenário {cenarios_nomes[i]}', fontsize=16, fontweight='bold')
                plt.savefig(f'resultados/graficos/tempo_total_{cenario}.png', dpi=300, bbox_inches='tight')
                plt.close()
                continue
            
            dados_seq = dados_cenario[dados_cenario['servidor'] == 'sequencial'].sort_values('num_requisicoes')
            dados_conc = dados_cenario[dados_cenario['servidor'] == 'concorrente'].sort_values('num_requisicoes')
            
            if not dados_seq.empty:
                plt.errorbar(dados_seq['num_requisicoes'], dados_seq['tempo_total_media'], 
                           yerr=dados_seq['tempo_total_desvio'],
                           fmt='o-', label='Servidor Sequencial', color='red', linewidth=3, 
                           markersize=10, capsize=5, capthick=2, alpha=0.8)
            
            if not dados_conc.empty:
                plt.errorbar(dados_conc['num_requisicoes'], dados_conc['tempo_total_media'], 
                           yerr=dados_conc['tempo_total_desvio'],
                           fmt='s-', label='Servidor Concorrente', color='blue', linewidth=3, 
                           markersize=10, capsize=5, capthick=2, alpha=0.8)
            
            execucoes = self.df['execucoes'].iloc[0] if not self.df.empty else 10
            plt.title(f'Tempo Total de Execução - Cenário {cenarios_nomes[i]}\n(Média +/- Desvio Padrão de {execucoes} execuções)', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Número de Requisições', fontsize=14, fontweight='bold')
            plt.ylabel('Tempo Total de Execução (s)', fontsize=14, fontweight='bold')
            plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.xlim(left=0)
            plt.ylim(bottom=0)
            
            #Adicionar valores nos pontos
            if not dados_seq.empty:
                for x, y in zip(dados_seq['num_requisicoes'], dados_seq['tempo_total_media']):
                    plt.annotate(f'{y:.2f}s', (x, y), textcoords="offset points", 
                               xytext=(0,10), ha='center', fontsize=10, color='red')
            
            if not dados_conc.empty:
                for x, y in zip(dados_conc['num_requisicoes'], dados_conc['tempo_total_media']):
                    plt.annotate(f'{y:.2f}s', (x, y), textcoords="offset points", 
                               xytext=(0,10), ha='center', fontsize=10, color='blue')
            
            plt.tight_layout()
            plt.savefig(f'resultados/graficos/tempo_total_{cenario}.png', dpi=300, bbox_inches='tight')
            plt.close()

    def plotar_comparacao_escalabilidade_estatistico(self):
        #Plota gráfico de comparação de escalabilidade com barras de erro
        plt.figure(figsize=(14, 10))
        
#Calcular throughput médio por cenário para comparação
        throughput_seq = []
        throughput_conc = []
        throughput_seq_err = []
        throughput_conc_err = []
        labels = []
        
        cenarios = ['rapido', 'medio', 'lento']
        cenarios_nomes = ['Rápido', 'Médio', 'Lento']
        
        for i, cenario in enumerate(cenarios):
            dados_cenario = self.df[self.df['cenario'] == cenario]
            
            if not dados_cenario.empty:
#Calcular throughput médio geral para cada servidor neste cenário
                dados_seq = dados_cenario[dados_cenario['servidor'] == 'sequencial']
                dados_conc = dados_cenario[dados_cenario['servidor'] == 'concorrente']
                
                if not dados_seq.empty:
                    seq_media = dados_seq['throughput_media'].mean()
                    seq_desvio = np.sqrt((dados_seq['throughput_desvio']**2).mean())  # Desvio médio quadrático
                else:
                    seq_media = seq_desvio = 0
                    
                if not dados_conc.empty:
                    conc_media = dados_conc['throughput_media'].mean()
                    conc_desvio = np.sqrt((dados_conc['throughput_desvio']**2).mean())  # Desvio médio quadrático
                else:
                    conc_media = conc_desvio = 0
                
                throughput_seq.append(seq_media)
                throughput_conc.append(conc_media)
                throughput_seq_err.append(seq_desvio)
                throughput_conc_err.append(conc_desvio)
                labels.append(cenarios_nomes[i])
        
        if throughput_seq or throughput_conc:
            x = np.arange(len(labels))
            width = 0.35
            
            bars1 = plt.bar(x - width/2, throughput_seq, width,
                           label='Servidor Sequencial', color='red', alpha=0.8, 
                           edgecolor='darkred', linewidth=1)
            bars2 = plt.bar(x + width/2, throughput_conc, width,
                           label='Servidor Concorrente', color='blue', alpha=0.8,
                           edgecolor='darkblue', linewidth=1)
            
            execucoes = self.df['execucoes'].iloc[0] if not self.df.empty else 10
            plt.title(f'Comparação de Escalabilidade entre Servidores\n(Throughput Médio de {execucoes} execuções)', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Cenário de Processamento', fontsize=14, fontweight='bold')
            plt.ylabel('Throughput Médio (req/s)', fontsize=14, fontweight='bold')
            plt.xticks(x, labels, fontsize=12)
            plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
            plt.grid(True, alpha=0.3, axis='y', linestyle='--')
            plt.ylim(bottom=0)
            
            #Adicionar valores nas barras
            for bar, value in zip(bars1, throughput_seq):
                if value > 0:
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           f'{value:.1f}', ha='center', va='bottom', fontsize=10, color='red')
            
            for bar, value in zip(bars2, throughput_conc):
                if value > 0:
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           f'{value:.1f}', ha='center', va='bottom', fontsize=10, color='blue')
        else:
            plt.text(0.5, 0.5, 'Sem dados para comparação', 
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
            plt.title('Comparação de Escalabilidade entre Servidores', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('resultados/graficos/comparacao_throughput.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    #Função principal para executar a análise
    analisador = AnalisadorResultados()
    analisador.gerar_todos_graficos()

if __name__ == "__main__":
    main()

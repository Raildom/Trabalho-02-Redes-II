#Script para gerar gráficos e análises dos resultados dos testes a partir do CSV
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

class AnalisadorResultados:
    def __init__(self, arquivo_csv='resultados/resultados_testes.csv'):
        self.arquivo_csv = arquivo_csv
        self.df = None
        self.carregar_resultados_csv()
        
    def carregar_resultados_csv(self):
        #Carrega os resultados dos testes do arquivo CSV
        try:
            self.df = pd.read_csv(self.arquivo_csv)
            print(Cores.info(f"Dados carregados: {len(self.df)} registros encontrados"))
        except FileNotFoundError:
            print(Cores.erro(f"Arquivo CSV não encontrado: {self.arquivo_csv}"))
            print("Execute primeiro os testes completos para gerar o arquivo CSV")
            self.df = None
        except Exception as e:
            print(Cores.erro(f"Erro ao carregar CSV: {e}"))
            self.df = None
    
    def gerar_todos_graficos(self):
        #Gera todos os gráficos de análise a partir do CSV
        if self.df is None or self.df.empty:
            print(Cores.erro("Nenhum resultado disponível para análise"))
            return
        
        #Configura o estilo dos gráficos
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
        #Cria diretório para gráficos
        os.makedirs('resultados/graficos', exist_ok=True)
        
        print(Cores.info("Gerando gráficos..."))
        
        self.plotar_throughput()
        self.plotar_latencia()
        self.plotar_taxa_sucesso()
        self.plotar_cpu()
        self.plotar_tempo_total()
        self.plotar_comparacao_geral()
        
        print(Cores.sucesso("Gráficos salvos em resultados/graficos/"))

    def plotar_throughput(self):
        #Plota gráfico de throughput (requisições por segundo) para cada teste
        try:
            #Agrupar por teste e calcular estatísticas
            testes = self.df['teste'].unique()
            
            for teste in testes:
                plt.figure(figsize=(12, 8))
                dados_teste = self.df[self.df['teste'] == teste]
                
                #Agrupar por servidor e calcular média e desvio padrão
                stats = dados_teste.groupby('servidor')['requisicoes_por_segundo'].agg(['mean', 'std']).reset_index()
                
                servidores = stats['servidor'].tolist()
                medias = stats['mean'].tolist()
                desvios = stats['std'].fillna(0).tolist()
                
                x = np.arange(len(servidores))
                width = 0.6
                
                cores = {'nginx': 'blue', 'apache': 'red'}
                bars = plt.bar(x, medias, width, 
                              color=[cores.get(s, 'gray') for s in servidores],
                              alpha=0.8, edgecolor='black', linewidth=1.5,
                              yerr=desvios, capsize=10)
                
                plt.title(f'Throughput - {teste}\n(Média +/- Desvio Padrão)', 
                         fontsize=16, fontweight='bold', pad=20)
                plt.xlabel('Servidor', fontsize=14, fontweight='bold')
                plt.ylabel('Requisições por Segundo', fontsize=14, fontweight='bold')
                plt.xticks(x, servidores, fontsize=12)
                plt.grid(True, alpha=0.3, axis='y', linestyle='--')
                plt.ylim(bottom=0)
                
                #Adicionar valores nas barras
                for bar, media in zip(bars, medias):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'{media:.2f}', ha='center', va='bottom', 
                           fontsize=12, fontweight='bold')
                
                plt.tight_layout()
                nome_arquivo = teste.replace(' ', '_').lower()
                plt.savefig(f'resultados/graficos/throughput_{nome_arquivo}.png', 
                           dpi=300, bbox_inches='tight')
                plt.close()
                
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar throughput: {e}"))

    def plotar_latencia(self):
        #Plota gráfico de latência média para cada teste
        try:
            testes = self.df['teste'].unique()
            
            for teste in testes:
                plt.figure(figsize=(12, 8))
                dados_teste = self.df[self.df['teste'] == teste]
                
                #Agrupar por servidor e calcular média e desvio padrão
                stats = dados_teste.groupby('servidor')['latencia_media_ms'].agg(['mean', 'std']).reset_index()
                
                servidores = stats['servidor'].tolist()
                medias = stats['mean'].tolist()
                desvios = stats['std'].fillna(0).tolist()
                
                x = np.arange(len(servidores))
                width = 0.6
                
                cores = {'nginx': 'blue', 'apache': 'red'}
                bars = plt.bar(x, medias, width,
                              color=[cores.get(s, 'gray') for s in servidores],
                              alpha=0.8, edgecolor='black', linewidth=1.5,
                              yerr=desvios, capsize=10)
                
                plt.title(f'Latência Média - {teste}\n(Média +/- Desvio Padrão)', 
                         fontsize=16, fontweight='bold', pad=20)
                plt.xlabel('Servidor', fontsize=14, fontweight='bold')
                plt.ylabel('Latência Média (ms)', fontsize=14, fontweight='bold')
                plt.xticks(x, servidores, fontsize=12)
                plt.grid(True, alpha=0.3, axis='y', linestyle='--')
                plt.ylim(bottom=0)
                
                #Adicionar valores nas barras
                for bar, media in zip(bars, medias):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'{media:.2f}ms', ha='center', va='bottom',
                           fontsize=12, fontweight='bold')
                
                plt.tight_layout()
                nome_arquivo = teste.replace(' ', '_').lower()
                plt.savefig(f'resultados/graficos/latencia_{nome_arquivo}.png',
                           dpi=300, bbox_inches='tight')
                plt.close()
                
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar latência: {e}"))

    def plotar_taxa_sucesso(self):
        #Plota gráfico de taxa de sucesso para cada teste
        try:
            testes = self.df['teste'].unique()
            
            for teste in testes:
                plt.figure(figsize=(12, 8))
                dados_teste = self.df[self.df['teste'] == teste]
                
                #Agrupar por servidor e calcular média
                stats = dados_teste.groupby('servidor')['taxa_sucesso_%'].agg(['mean', 'std']).reset_index()
                
                servidores = stats['servidor'].tolist()
                medias = stats['mean'].tolist()
                desvios = stats['std'].fillna(0).tolist()
                
                x = np.arange(len(servidores))
                width = 0.6
                
                cores = {'nginx': 'blue', 'apache': 'red'}
                bars = plt.bar(x, medias, width,
                              color=[cores.get(s, 'gray') for s in servidores],
                              alpha=0.8, edgecolor='black', linewidth=1.5,
                              yerr=desvios, capsize=10)
                
                plt.title(f'Taxa de Sucesso - {teste}\n(Média +/- Desvio Padrão)',
                         fontsize=16, fontweight='bold', pad=20)
                plt.xlabel('Servidor', fontsize=14, fontweight='bold')
                plt.ylabel('Taxa de Sucesso (%)', fontsize=14, fontweight='bold')
                plt.xticks(x, servidores, fontsize=12)
                plt.grid(True, alpha=0.3, axis='y', linestyle='--')
                plt.ylim(0, 105)
                
                #Adicionar valores nas barras
                for bar, media in zip(bars, medias):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                           f'{media:.1f}%', ha='center', va='bottom',
                           fontsize=12, fontweight='bold')
                
                plt.tight_layout()
                nome_arquivo = teste.replace(' ', '_').lower()
                plt.savefig(f'resultados/graficos/taxa_sucesso_{nome_arquivo}.png',
                           dpi=300, bbox_inches='tight')
                plt.close()
                
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar taxa de sucesso: {e}"))

    def plotar_cpu(self):
        #Plota gráfico de uso de CPU para cada teste
        try:
            testes = self.df['teste'].unique()
            
            for teste in testes:
                plt.figure(figsize=(12, 8))
                dados_teste = self.df[self.df['teste'] == teste]
                
                #Agrupar por servidor e calcular média e desvio padrão
                stats = dados_teste.groupby('servidor')['cpu_percent'].agg(['mean', 'std']).reset_index()
                
                servidores = stats['servidor'].tolist()
                medias = stats['mean'].tolist()
                desvios = stats['std'].fillna(0).tolist()
                
                x = np.arange(len(servidores))
                width = 0.6
                
                cores = {'nginx': 'blue', 'apache': 'red'}
                bars = plt.bar(x, medias, width,
                              color=[cores.get(s, 'gray') for s in servidores],
                              alpha=0.8, edgecolor='black', linewidth=1.5,
                              yerr=desvios, capsize=10)
                
                plt.title(f'Uso de CPU - {teste}\n(Média +/- Desvio Padrão - CPU do Container)',
                         fontsize=16, fontweight='bold', pad=20)
                plt.xlabel('Servidor', fontsize=14, fontweight='bold')
                plt.ylabel('Uso de CPU (%)', fontsize=14, fontweight='bold')
                plt.xticks(x, servidores, fontsize=12)
                plt.grid(True, alpha=0.3, axis='y', linestyle='--')
                plt.ylim(bottom=0)
                
                #Adicionar valores nas barras
                for bar, media in zip(bars, medias):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'{media:.2f}%', ha='center', va='bottom',
                           fontsize=12, fontweight='bold')
                
                plt.tight_layout()
                nome_arquivo = teste.replace(' ', '_').lower()
                plt.savefig(f'resultados/graficos/cpu_{nome_arquivo}.png',
                           dpi=300, bbox_inches='tight')
                plt.close()
                
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar CPU: {e}"))

    def plotar_tempo_total(self):
        #Plota gráfico de tempo total de execução para cada teste
        try:
            testes = self.df['teste'].unique()
            
            for teste in testes:
                plt.figure(figsize=(12, 8))
                dados_teste = self.df[self.df['teste'] == teste]
                
                #Agrupar por servidor e calcular média e desvio padrão
                stats = dados_teste.groupby('servidor')['tempo_total_s'].agg(['mean', 'std']).reset_index()
                
                servidores = stats['servidor'].tolist()
                medias = stats['mean'].tolist()
                desvios = stats['std'].fillna(0).tolist()
                
                x = np.arange(len(servidores))
                width = 0.6
                
                cores = {'nginx': 'blue', 'apache': 'red'}
                bars = plt.bar(x, medias, width,
                              color=[cores.get(s, 'gray') for s in servidores],
                              alpha=0.8, edgecolor='black', linewidth=1.5,
                              yerr=desvios, capsize=10)
                
                plt.title(f'Tempo Total de Execução - {teste}\n(Média +/- Desvio Padrão)',
                         fontsize=16, fontweight='bold', pad=20)
                plt.xlabel('Servidor', fontsize=14, fontweight='bold')
                plt.ylabel('Tempo Total (segundos)', fontsize=14, fontweight='bold')
                plt.xticks(x, servidores, fontsize=12)
                plt.grid(True, alpha=0.3, axis='y', linestyle='--')
                plt.ylim(bottom=0)
                
                #Adicionar valores nas barras
                for bar, media in zip(bars, medias):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{media:.2f}s', ha='center', va='bottom',
                           fontsize=12, fontweight='bold')
                
                plt.tight_layout()
                nome_arquivo = teste.replace(' ', '_').lower()
                plt.savefig(f'resultados/graficos/tempo_total_{nome_arquivo}.png',
                           dpi=300, bbox_inches='tight')
                plt.close()
                
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar tempo total: {e}"))

    def plotar_comparacao_geral(self):
        #Plota gráfico comparativo geral entre nginx e apache
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Comparação Geral: Nginx vs Apache\n(Média de todos os testes)',
                        fontsize=18, fontweight='bold', y=0.995)
            
            #Calcular médias gerais por servidor
            stats_throughput = self.df.groupby('servidor')['requisicoes_por_segundo'].mean()
            stats_latencia = self.df.groupby('servidor')['latencia_media_ms'].mean()
            stats_cpu = self.df.groupby('servidor')['cpu_percent'].mean()
            stats_sucesso = self.df.groupby('servidor')['taxa_sucesso_%'].mean()
            
            servidores = stats_throughput.index.tolist()
            cores = {'nginx': 'blue', 'apache': 'red'}
            cores_list = [cores.get(s, 'gray') for s in servidores]
            
            #Gráfico 1: Throughput
            axes[0, 0].bar(servidores, stats_throughput.values, color=cores_list, alpha=0.8, edgecolor='black')
            axes[0, 0].set_title('Throughput Médio', fontsize=14, fontweight='bold')
            axes[0, 0].set_ylabel('Req/s', fontsize=12)
            axes[0, 0].grid(True, alpha=0.3, axis='y')
            for i, (srv, val) in enumerate(zip(servidores, stats_throughput.values)):
                axes[0, 0].text(i, val + 0.1, f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
            
            #Gráfico 2: Latência
            axes[0, 1].bar(servidores, stats_latencia.values, color=cores_list, alpha=0.8, edgecolor='black')
            axes[0, 1].set_title('Latência Média', fontsize=14, fontweight='bold')
            axes[0, 1].set_ylabel('ms', fontsize=12)
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            for i, (srv, val) in enumerate(zip(servidores, stats_latencia.values)):
                axes[0, 1].text(i, val + 0.1, f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
            
            #Gráfico 3: CPU
            axes[1, 0].bar(servidores, stats_cpu.values, color=cores_list, alpha=0.8, edgecolor='black')
            axes[1, 0].set_title('Uso Médio de CPU (Container)', fontsize=14, fontweight='bold')
            axes[1, 0].set_ylabel('%', fontsize=12)
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            for i, (srv, val) in enumerate(zip(servidores, stats_cpu.values)):
                axes[1, 0].text(i, val + 0.1, f'{val:.2f}%', ha='center', va='bottom', fontweight='bold')
            
            #Gráfico 4: Taxa de Sucesso
            axes[1, 1].bar(servidores, stats_sucesso.values, color=cores_list, alpha=0.8, edgecolor='black')
            axes[1, 1].set_title('Taxa de Sucesso Média', fontsize=14, fontweight='bold')
            axes[1, 1].set_ylabel('%', fontsize=12)
            axes[1, 1].set_ylim(0, 105)
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            for i, (srv, val) in enumerate(zip(servidores, stats_sucesso.values)):
                axes[1, 1].text(i, val + 1, f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('resultados/graficos/comparacao_geral.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar comparação geral: {e}"))


def main():
    #Função principal para executar a análise
    print(Cores.titulo("\n" + "="*70))
    print(Cores.titulo("ANÁLISE DE RESULTADOS - NGINX vs APACHE"))
    print(Cores.titulo("="*70 + "\n"))
    
    analisador = AnalisadorResultados()
    if analisador.df is not None:
        analisador.gerar_todos_graficos()
        print(Cores.sucesso("\nAnálise concluída com sucesso!"))
        print(Cores.info(f"Gráficos salvos em: resultados/graficos/\n"))
    else:
        print(Cores.erro("\nNão foi possível carregar os dados para análise\n"))

if __name__ == "__main__":
    main()

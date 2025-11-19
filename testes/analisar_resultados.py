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
        plt.rcParams['figure.figsize'] = (16, 10)
        plt.rcParams['font.size'] = 10
        
        #Cria diretório para gráficos
        os.makedirs('resultados/graficos', exist_ok=True)
        
        print(Cores.info("Gerando gráficos separados..."))
        
        self.plotar_throughput_separado()
        self.plotar_latencia_separado()
        self.plotar_tempo_total_separado()
        self.plotar_cpu_separado()
        
        print(Cores.sucesso("Gráficos salvos em resultados/graficos/"))


    def plotar_throughput_separado(self):
        #Plota gráfico de throughput separado
        try:
            #Obter lista de todos os testes
            testes = sorted(self.df['teste'].unique(), key=lambda x: int(x.split('Cenario')[1].split('_')[0]))
            
            #Calcular médias por teste e servidor
            stats = self.df.groupby(['teste', 'servidor']).agg({
                'requisicoes_por_segundo': 'mean'
            }).reset_index()
            
            #Preparar dados para cada servidor
            nginx_data = stats[stats['servidor'] == 'nginx'].sort_values('teste')
            apache_data = stats[stats['servidor'] == 'apache'].sort_values('teste')
            
            #Criar figura
            fig, ax = plt.subplots(figsize=(20, 10))
            
            x = np.arange(len(testes))
            width = 0.35
            
            cores = {'nginx': '#0066CC', 'apache': '#CC0000'}
            
            bars_nginx = ax.bar(x - width/2, nginx_data['requisicoes_por_segundo'], 
                               width, label='Nginx', color=cores['nginx'], 
                               alpha=0.8, edgecolor='black', linewidth=1.2)
            bars_apache = ax.bar(x + width/2, apache_data['requisicoes_por_segundo'], 
                                width, label='Apache', color=cores['apache'], 
                                alpha=0.8, edgecolor='black', linewidth=1.2)
            
            ax.set_title('Throughput (Requisições por Segundo)\nComparação: Nginx vs Apache', 
                        fontsize=20, fontweight='bold', pad=20)
            ax.set_ylabel('Requisições/s', fontsize=16, fontweight='bold')
            ax.set_xlabel('Cenários de Teste', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(testes, rotation=45, ha='right', fontsize=11)
            ax.legend(loc='upper left', fontsize=14, framealpha=0.9)
            ax.grid(True, alpha=0.3, axis='y', linestyle='--')
            ax.set_ylim(bottom=0)
            
            #Adicionar valores nas barras
            for bars in [bars_nginx, bars_apache]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}',
                               ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('resultados/graficos/01_throughput.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(Cores.sucesso("  [OK] Gráfico de Throughput gerado"))
            
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar throughput: {e}"))
            import traceback
            traceback.print_exc()

    def plotar_latencia_separado(self):
        #Plota gráfico de latência separado
        try:
            #Obter lista de todos os testes
            testes = sorted(self.df['teste'].unique(), key=lambda x: int(x.split('Cenario')[1].split('_')[0]))
            
            #Calcular médias por teste e servidor
            stats = self.df.groupby(['teste', 'servidor']).agg({
                'latencia_media_ms': 'mean'
            }).reset_index()
            
            #Preparar dados para cada servidor
            nginx_data = stats[stats['servidor'] == 'nginx'].sort_values('teste')
            apache_data = stats[stats['servidor'] == 'apache'].sort_values('teste')
            
            #Criar figura
            fig, ax = plt.subplots(figsize=(20, 10))
            
            x = np.arange(len(testes))
            width = 0.35
            
            cores = {'nginx': '#0066CC', 'apache': '#CC0000'}
            
            bars_nginx = ax.bar(x - width/2, nginx_data['latencia_media_ms'], 
                               width, label='Nginx', color=cores['nginx'], 
                               alpha=0.8, edgecolor='black', linewidth=1.2)
            bars_apache = ax.bar(x + width/2, apache_data['latencia_media_ms'], 
                                width, label='Apache', color=cores['apache'], 
                                alpha=0.8, edgecolor='black', linewidth=1.2)
            
            ax.set_title('Latência Média\nComparação: Nginx vs Apache', 
                        fontsize=20, fontweight='bold', pad=20)
            ax.set_ylabel('Latência (ms)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Cenários de Teste', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(testes, rotation=45, ha='right', fontsize=11)
            ax.legend(loc='upper left', fontsize=14, framealpha=0.9)
            ax.grid(True, alpha=0.3, axis='y', linestyle='--')
            ax.set_ylim(bottom=0)
            
            #Adicionar valores nas barras
            for bars in [bars_nginx, bars_apache]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}',
                               ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('resultados/graficos/02_latencia.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(Cores.sucesso("  [OK] Gráfico de Latência gerado"))
            
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar latência: {e}"))
            import traceback
            traceback.print_exc()

    def plotar_tempo_total_separado(self):
        #Plota gráfico de tempo total separado
        try:
            #Obter lista de todos os testes
            testes = sorted(self.df['teste'].unique(), key=lambda x: int(x.split('Cenario')[1].split('_')[0]))
            
            #Calcular médias por teste e servidor
            stats = self.df.groupby(['teste', 'servidor']).agg({
                'tempo_total_s': 'mean'
            }).reset_index()
            
            #Preparar dados para cada servidor
            nginx_data = stats[stats['servidor'] == 'nginx'].sort_values('teste')
            apache_data = stats[stats['servidor'] == 'apache'].sort_values('teste')
            
            #Criar figura
            fig, ax = plt.subplots(figsize=(20, 10))
            
            x = np.arange(len(testes))
            width = 0.35
            
            cores = {'nginx': '#0066CC', 'apache': '#CC0000'}
            
            bars_nginx = ax.bar(x - width/2, nginx_data['tempo_total_s'], 
                               width, label='Nginx', color=cores['nginx'], 
                               alpha=0.8, edgecolor='black', linewidth=1.2)
            bars_apache = ax.bar(x + width/2, apache_data['tempo_total_s'], 
                                width, label='Apache', color=cores['apache'], 
                                alpha=0.8, edgecolor='black', linewidth=1.2)
            
            ax.set_title('Tempo Total de Execução\nComparação: Nginx vs Apache', 
                        fontsize=20, fontweight='bold', pad=20)
            ax.set_ylabel('Tempo (segundos)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Cenários de Teste', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(testes, rotation=45, ha='right', fontsize=11)
            ax.legend(loc='upper left', fontsize=14, framealpha=0.9)
            ax.grid(True, alpha=0.3, axis='y', linestyle='--')
            ax.set_ylim(bottom=0)
            
            #Adicionar valores nas barras
            for bars in [bars_nginx, bars_apache]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}',
                               ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('resultados/graficos/03_tempo_total.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(Cores.sucesso("  [OK] Gráfico de Tempo Total gerado"))
            
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar tempo total: {e}"))
            import traceback
            traceback.print_exc()

    def plotar_cpu_separado(self):
        #Plota gráfico de CPU separado
        try:
            #Obter lista de todos os testes
            testes = sorted(self.df['teste'].unique(), key=lambda x: int(x.split('Cenario')[1].split('_')[0]))
            
            #Calcular médias por teste e servidor
            stats = self.df.groupby(['teste', 'servidor']).agg({
                'cpu_percent': 'mean'
            }).reset_index()
            
            #Preparar dados para cada servidor
            nginx_data = stats[stats['servidor'] == 'nginx'].sort_values('teste')
            apache_data = stats[stats['servidor'] == 'apache'].sort_values('teste')
            
            #Criar figura
            fig, ax = plt.subplots(figsize=(20, 10))
            
            x = np.arange(len(testes))
            width = 0.35
            
            cores = {'nginx': '#0066CC', 'apache': '#CC0000'}
            
            bars_nginx = ax.bar(x - width/2, nginx_data['cpu_percent'], 
                               width, label='Nginx', color=cores['nginx'], 
                               alpha=0.8, edgecolor='black', linewidth=1.2)
            bars_apache = ax.bar(x + width/2, apache_data['cpu_percent'], 
                                width, label='Apache', color=cores['apache'], 
                                alpha=0.8, edgecolor='black', linewidth=1.2)
            
            ax.set_title('Uso de CPU (Container)\nComparação: Nginx vs Apache', 
                        fontsize=20, fontweight='bold', pad=20)
            ax.set_ylabel('CPU (%)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Cenários de Teste', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(testes, rotation=45, ha='right', fontsize=11)
            ax.legend(loc='upper left', fontsize=14, framealpha=0.9)
            ax.grid(True, alpha=0.3, axis='y', linestyle='--')
            ax.set_ylim(bottom=0)
            
            #Adicionar valores nas barras
            for bars in [bars_nginx, bars_apache]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}',
                               ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('resultados/graficos/04_cpu.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(Cores.sucesso("  [OK] Gráfico de CPU gerado"))
            
        except Exception as e:
            print(Cores.erro(f"Erro ao plotar CPU: {e}"))
            import traceback
            traceback.print_exc()



def main():
    #Função principal para executar a análise
    print(Cores.titulo("\n" + "="*70))
    print(Cores.titulo("ANÁLISE DE RESULTADOS - NGINX vs APACHE"))
    print(Cores.titulo("="*70 + "\n"))
    
    analisador = AnalisadorResultados()
    if analisador.df is not None:
        analisador.gerar_todos_graficos()
        print(Cores.sucesso("\nAnálise concluída com sucesso!"))
        print(Cores.info(f"Gráficos salvos em: resultados/graficos/"))
        print(Cores.info(f"  - 01_throughput.png"))
        print(Cores.info(f"  - 02_latencia.png"))
        print(Cores.info(f"  - 03_tempo_total.png"))
        print(Cores.info(f"  - 04_cpu.png\n"))
    else:
        print(Cores.erro("\nNão foi possível carregar os dados para análise\n"))

if __name__ == "__main__":
    main()



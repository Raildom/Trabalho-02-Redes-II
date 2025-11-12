#!/usr/bin/env python3
#Script principal para executar o projeto Redes II

import subprocess
import sys
import os
import time
import argparse

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

class ProjetoRedes:
    def __init__(self):
        self.info_projeto()
    
    def info_projeto(self):
        print(f"{Cores.CIANO}{Cores.NEGRITO}=== Projeto Redes II - Servidor Web Sequencial vs Concorrente ==={Cores.RESET}")
        print(f"{Cores.AZUL}Matrícula: 20239057601{Cores.RESET}")
        print(f"{Cores.AZUL}Subnet configurada: 76.1.0.0/16{Cores.RESET}")
        print("")
    
    def verificar_docker(self):
        #Verifica se o Docker está rodando
        try:
            subprocess.run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(Cores.erro("Docker não está rodando ou não está instalado"))
            print("Por favor, inicie o Docker e tente novamente")
            return False
    
    def iniciar_conteineres(self):
        #Constrói e inicia os contêineres
        print("=== Construindo e iniciando contêineres ===")
        
        if not os.path.exists('docker'):
            print(Cores.erro("Diretório 'docker' não encontrado"))
            return False
        
        try:
            #Para contêineres existentes se estiverem rodando
            subprocess.run(['docker-compose', '-f', 'docker/docker-compose.yml', 'down'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            #Constrói e inicia os contêineres
            result = subprocess.run(['docker-compose', '-f', 'docker/docker-compose.yml', 'up', '--build', '-d'], check=True)
            
            print("Aguardando contêineres iniciarem...")
            time.sleep(2)
            
            #Verifica se os contêineres estão rodando
            result = subprocess.run(['docker-compose', '-f', 'docker/docker-compose.yml', 'ps'], capture_output=True, text=True)
            if 'Up' in result.stdout:
                print(Cores.sucesso("Contêineres iniciados com sucesso"))
                print(result.stdout)
                return True
            else:
                print(Cores.erro("Erro ao iniciar contêineres"))
                subprocess.run(['docker-compose', '-f', 'docker/docker-compose.yml', 'logs'])
                return False
                
        except subprocess.CalledProcessError as e:
            print(Cores.erro(f"Falha ao iniciar contêineres: {e}"))
            return False
    

    
    def teste_conectividade(self):
        #Executa teste de conectividade
        print("")
        print("=== Executando teste de conectividade ===")
        
        #Verifica se o contêiner está rodando
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if 'cliente_teste' not in result.stdout:
                print(Cores.erro("Contêiner de teste não está rodando."))
                print("Execute primeiro a opção 1 (Iniciar contêineres)")
                return False
        except subprocess.CalledProcessError:
            print(Cores.erro("Erro ao verificar contêineres"))
            return False
        
        #Executa o teste de conectividade
        try:
            subprocess.run(['docker', 'exec', 'cliente_teste', 'python3', 'testes/teste_completo.py', '--conectividade'], check=True)
            print(Cores.sucesso("Teste de conectividade concluído"))
            return True
        except subprocess.CalledProcessError:
            print(Cores.erro("Falha no teste de conectividade"))
            print("Verifique os logs para mais detalhes")
            return False
    
    def executar_testes_completos(self):
        #Executa testes completos
        print("")
        print("=== Executando testes completos ===")
        print("Isso pode demorar alguns minutos...")
        
        #Verifica se o contêiner está rodando
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if 'cliente_teste' not in result.stdout:
                print(Cores.erro("Contêiner de teste não está rodando."))
                print("Execute primeiro a opção 1 (Iniciar contêineres)")
                return False
        except subprocess.CalledProcessError:
            print(Cores.erro("Erro ao verificar contêineres"))
            return False
        
        #Executa os testes completos com tratamento de erro
        try:
            subprocess.run(['docker', 'exec', 'cliente_teste', 'python3', 'testes/teste_completo.py', '--completo'], check=True)
            print(Cores.sucesso("Testes completos concluídos"))
            return True
        except subprocess.CalledProcessError:
            print(Cores.erro("Falha nos testes completos"))
            print("Verifique os logs para mais detalhes")
            return False
    
    def gerar_analises(self):
        #Gera análises e gráficos
        print("")
        print("=== Gerando análises e gráficos ===")
        
        #Verifica se existem resultados para analisar localmente
        if os.path.exists('resultados/resultados_completos.csv'):
            try:
                #Executa a análise localmente
                subprocess.run(['python3', 'testes/analisar_resultados.py'], check=True)
                print(Cores.sucesso("Análises e gráficos gerados"))
                return True
            except subprocess.CalledProcessError as e:
                print(Cores.erro(f"Falha ao gerar análises: {e}"))
                return False
        else:
            #Tenta copiar do contêiner se não existir localmente
            try:
                subprocess.run(['docker', 'exec', 'cliente_teste', 'test', '-f', '/app/resultados/resultados_completos.csv'], check=True)
                subprocess.run(['docker', 'cp', 'cliente_teste:/app/resultados/', './'], check=True)
                
                #Executa a análise localmente
                subprocess.run(['python3', 'testes/analisar_resultados.py'], check=True)
                print(Cores.sucesso("Análises e gráficos gerados a partir do contêiner"))
                return True
                
            except subprocess.CalledProcessError:
                print(Cores.aviso("Nenhum resultado encontrado para análise."))
                print("Execute primeiro os testes com a opção 2 (Executar testes completos)")
                print("ou use a opção 8 (Executar tudo) para executar testes e análises automaticamente.")
                return False
    
    def parar_conteineres(self):
        #Para contêineres
        print("")
        print("=== Parando contêineres ===")
        
        try:
            subprocess.run(['docker-compose', '-f', 'docker/docker-compose.yml', 'down'], check=True)
            print(Cores.sucesso("Contêineres parados"))
            return True
        except subprocess.CalledProcessError as e:
            print(Cores.erro(f"Falha ao parar contêineres: {e}"))
            return False
    
    def entrar_conteiner_teste(self):
        #Entra no contêiner de teste
        print("")
        print(Cores.info("=== Entrando no contêiner de teste ==="))
        print(Cores.info("Bem-vindo ao contêiner do cliente!"))
        print(Cores.aviso("Para sair, digite 'exit'"))
        print("")
        
        #Verifica se o contêiner está rodando
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if 'cliente_teste' not in result.stdout:
                print(Cores.erro("Contêiner de teste não está rodando."))
                print(Cores.aviso("Execute primeiro a opção 1 (Iniciar contêineres)"))
                return False
        except subprocess.CalledProcessError:
            print(Cores.erro("Erro ao verificar contêineres"))
            return False
        
        try:
            subprocess.run(['docker', 'exec', '-it', 'cliente_teste', 'bash'])
            print("")
            print(Cores.sucesso("Você saiu do contêiner de teste"))
            return True
        except subprocess.CalledProcessError as e:
            print(Cores.erro(f"Falha ao entrar no contêiner: {e}"))
            print(Cores.aviso("Verifique se o contêiner está rodando"))
            return False
    
    def mostrar_menu(self):
        #Mostra menu principal
        print("")
        print(f"{Cores.CIANO}{Cores.NEGRITO}==== MENU PRINCIPAL ===={Cores.RESET}")
        print("1) Iniciar contêineres")
        print("2) Teste de conectividade")
        print("3) Executar testes completos")
        print("4) Gerar análises e gráficos")
        print("5) Entrar no contêiner de teste")
        print("6) Executar tudo (início ao fim)")
        print("0) Sair")
        print("")
    
    def executar_tudo(self):
        #Executa todo o fluxo do projeto
        if not self.iniciar_conteineres():
            return False
        
        print("")
        resposta = input("Executar testes completos? (pode demorar 10-15 minutos) [Y/N]: ").lower()
        
        if resposta in ['y', 'yes', 's', 'sim']:
            if self.executar_testes_completos():
                self.gerar_analises()
                print("")
                print("=== Projeto concluído! ===")
                print("Resultados disponíveis em ./resultados/")
                return True
        
        return True
    
    def executar_comando_linha(self, comando):
        #Executa comando da linha de comando
        comandos = {
            'start': self.iniciar_conteineres,
            'iniciar': self.iniciar_conteineres,
            'conectividade': self.teste_conectividade,
            'teste-conectividade': self.teste_conectividade,
            'full-test': self.executar_testes_completos,
            'teste-completo': self.executar_testes_completos,
            'analyze': self.gerar_analises,
            'analisar': self.gerar_analises,
            'shell': self.entrar_conteiner_teste,
            'all': self.executar_tudo,
            'tudo': self.executar_tudo
        }
        
        if comando in comandos:
            return comandos[comando]()
        else:
            print(f"Opção inválida: {comando}")
            print("Opções: iniciar, conectividade, teste-completo, analisar, shell, tudo")
            return False
    
    def menu_interativo(self):
        #Menu interativo principal
        while True:
            self.mostrar_menu()
            try:
                escolha = input("Escolha uma opção: ").strip()
                
                if escolha == '1':
                    self.iniciar_conteineres()
                elif escolha == '2':
                    self.teste_conectividade()
                elif escolha == '3':
                    self.executar_testes_completos()
                elif escolha == '4':
                    self.gerar_analises()
                elif escolha == '5':
                    self.entrar_conteiner_teste()
                elif escolha == '6':
                    self.executar_tudo()
                elif escolha == '0':
                    self.parar_conteineres()
                    print("Saindo...")
                    break
                else:
                    print("Opção inválida")
                    
            except KeyboardInterrupt:
                print("\n\nSaindo...")
                self.parar_conteineres()
                break
            except EOFError:
                print("\n\nSaindo...")
                self.parar_conteineres()
                break

def main():
    projeto = ProjetoRedes()
    
    #Verifica Docker
    if not projeto.verificar_docker():
        print("Não é possível continuar sem Docker funcionando")
        if len(sys.argv) > 1:
            sys.exit(1)
        else:
            input("Pressione Enter para tentar novamente ou Ctrl+C para sair")
            return main()
    
    #Se há argumentos, executa diretamente
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description='Gerenciador do Projeto Redes II')
        parser.add_argument('comando', choices=[
            'start', 'iniciar', 'conectividade', 'teste-conectividade',
            'full-test', 'teste-completo', 'analyze', 'analisar',
            'shell', 'all', 'tudo'
        ], help='Comando para executar')
        
        args = parser.parse_args()
        success = projeto.executar_comando_linha(args.comando)
        sys.exit(0 if success else 1)
    
    #Menu interativo
    projeto.menu_interativo()

if __name__ == "__main__":
    main()

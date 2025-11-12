#!/usr/bin/env python3
#Script principal para executar o projeto Redes II

import subprocess
import sys
import os
import time
import argparse

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
        print(f"{Cores.CIANO}{Cores.NEGRITO}=== Projeto Redes II - Comparação Nginx vs Apache ==={Cores.RESET}")
        print(f"{Cores.AZUL}Aluno: Raildom da Rocha Sobrinho{Cores.RESET}")
        print(f"{Cores.AZUL}Matrícula: 20239057601{Cores.RESET}")
        print(f"{Cores.AZUL}Subnet configurada: 76.1.0.0/16{Cores.RESET}")
        print(f"{Cores.VERDE}Observabilidade: Prometheus + Grafana{Cores.RESET}")
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
        print(Cores.info("Serviços: Nginx, Apache, Prometheus, Grafana"))
        
        if not os.path.exists('docker'):
            print(Cores.erro("Diretório 'docker' não encontrado"))
            return False
        
        try:
            #Para contêineres existentes se estiverem rodando
            print(Cores.info("Parando contêineres existentes..."))
            subprocess.run(['docker', 'compose', '-f', 'docker/docker-compose.yml', 'down'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            #Constrói e inicia os contêineres
            print(Cores.info("Construindo imagens Docker (pode demorar alguns minutos)..."))
            result = subprocess.run(['docker', 'compose', '-f', 'docker/docker-compose.yml', 'up', '--build', '-d'], 
                                  check=True)
            
            print(Cores.info("Aguardando contêineres iniciarem..."))
            time.sleep(2)
            
            #Verifica se os contêineres estão rodando
            result = subprocess.run(['docker', 'compose', '-f', 'docker/docker-compose.yml', 'ps'], 
                                  capture_output=True, text=True)
            if 'Up' in result.stdout or 'running' in result.stdout:
                print(Cores.sucesso("Contêineres iniciados com sucesso!"))
                print("")
                print(f"{Cores.CIANO}Serviços disponíveis:{Cores.RESET}")
                print(f"  {Cores.VERDE}• Nginx:      http://localhost:8080{Cores.RESET}")
                print(f"  {Cores.VERDE}• Apache:     http://localhost:8081{Cores.RESET}")
                print(f"  {Cores.VERDE}• Prometheus: http://localhost:9090{Cores.RESET}")
                print(f"  {Cores.VERDE}• Grafana:    http://localhost:3000{Cores.RESET} (admin/admin)")
                print("")
                return True
            else:
                print(Cores.erro("Erro ao iniciar contêineres"))
                subprocess.run(['docker', 'compose', '-f', 'docker/docker-compose.yml', 'logs'])
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
        
        #Testa conectividade com Nginx
        print(Cores.info("Testando Nginx..."))
        try:
            result = subprocess.run([
                'docker', 'exec', 'cliente_teste', 'python3', '-c',
                "import sys; sys.path.insert(0, '/app/src'); from cliente import ClienteHTTP; "
                "c = ClienteHTTP('76.1.0.10', 80); r = c.enviar_requisicao('GET', '/api/pequeno'); "
                "print('Status:', r['codigo_status'], '- OK' if r['sucesso'] else '- FALHA')"
            ], capture_output=True, text=True, check=True)
            print(Cores.sucesso(f"Nginx: {result.stdout.strip()}"))
        except subprocess.CalledProcessError as e:
            print(Cores.erro(f"Falha ao conectar com Nginx: {e.stderr}"))
            return False
        
        #Testa conectividade com Apache
        print(Cores.info("Testando Apache..."))
        try:
            result = subprocess.run([
                'docker', 'exec', 'cliente_teste', 'python3', '-c',
                "import sys; sys.path.insert(0, '/app/src'); from cliente import ClienteHTTP; "
                "c = ClienteHTTP('76.1.0.11', 80); r = c.enviar_requisicao('GET', '/api/pequeno'); "
                "print('Status:', r['codigo_status'], '- OK' if r['sucesso'] else '- FALHA')"
            ], capture_output=True, text=True, check=True)
            print(Cores.sucesso(f"Apache: {result.stdout.strip()}"))
        except subprocess.CalledProcessError as e:
            print(Cores.erro(f"Falha ao conectar com Apache: {e.stderr}"))
            return False
        
        print(Cores.sucesso("Teste de conectividade concluído com sucesso!"))
        return True
    
    def executar_testes_completos(self):
        #Executa testes completos de carga
        print("")
        print("=== Executando testes de carga completos ===")
        print(Cores.aviso("Isso pode demorar 5-10 minutos..."))
        print(Cores.info("Testes: API, Arquivos Estáticos, Pico de Carga, Carga Sustentada"))
        print("")
        
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
        
        #Executa os testes de carga
        try:
            subprocess.run([
                'docker', 'exec', '-it', 'cliente_teste', 
                'python3', '/app/testes/teste_carga.py'
            ], check=True)
            print("")
            print(Cores.sucesso("Testes de carga concluídos com sucesso!"))
            return True
        except subprocess.CalledProcessError:
            print(Cores.erro("Falha nos testes de carga"))
            print("Verifique os logs para mais detalhes")
            return False
        except KeyboardInterrupt:
            print("")
            print(Cores.aviso("Testes interrompidos pelo usuário"))
            return False
    
    def gerar_analises(self):
        #Acessa Grafana e Prometheus
        print("")
        print("=== Observabilidade e Análises ===" )
        print("")
        print(f"{Cores.CIANO}Acesse os serviços de observabilidade:{Cores.RESET}")
        print(f"  {Cores.VERDE}• Prometheus: http://localhost:9090{Cores.RESET}")
        print(f"    - Visualize métricas em tempo real")
        print(f"    - Query: rate(nginx_http_requests_total[1m])")
        print("")
        print(f"  {Cores.VERDE}• Grafana: http://localhost:3000{Cores.RESET}")
        print(f"    - Login: admin / admin")
        print(f"    - Crie dashboards personalizados")
        print(f"    - Compare Nginx vs Apache")
        print("")
        print(f"{Cores.AMARELO}Dica:{Cores.RESET} Execute os testes de carga primeiro para gerar métricas")
        print("")
        
        return True
    
    def gerar_arquivos_estaticos(self):
        #Gera arquivos estáticos de teste
        print("")
        print("=== Gerando arquivos estáticos de teste ===")
        
        try:
            subprocess.run(['python3', 'src/gerar_arquivos_estaticos.py'], check=True)
            print(Cores.sucesso("Arquivos estáticos gerados com sucesso"))
            return True
        except subprocess.CalledProcessError as e:
            print(Cores.erro(f"Falha ao gerar arquivos: {e}"))
            return False
    
    def parar_conteineres(self):
        #Para contêineres
        print("")
        print("=== Parando contêineres ===")
        
        try:
            subprocess.run(['docker', 'compose', '-f', 'docker/docker-compose.yml', 'down'], check=True)
            print(Cores.sucesso("Contêineres parados com sucesso"))
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
        print("1) Iniciar contêineres (Nginx, Apache, Prometheus, Grafana)")
        print("2) Teste de conectividade")
        print("3) Executar testes de carga completos")
        print("4) Acessar observabilidade (Prometheus/Grafana)")
        print("5) Entrar no contêiner de teste (Shell)")
        print("6) Gerar arquivos estáticos de teste")
        print("7) Executar tudo (início ao fim)")
        print("8) Parar contêineres")
        print("0) Sair")
        print("")
    
    def executar_tudo(self):
        #Executa todo o fluxo do projeto
        print(Cores.info("Iniciando execução completa do projeto..."))
        print("")
        
        if not self.iniciar_conteineres():
            return False
        
        print("")
        resposta = input(f"{Cores.AMARELO}Executar testes de carga? (pode demorar 5-10 minutos) [S/N]: {Cores.RESET}").lower()
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            if self.executar_testes_completos():
                print("")
                print(Cores.sucesso("=== Projeto executado com sucesso! ==="))
                print("")
                self.gerar_analises()
                return True
        else:
            print(Cores.info("Testes pulados. Servidores estão rodando."))
            self.gerar_analises()
        
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
            'gerar-arquivos': self.gerar_arquivos_estaticos,
            'arquivos': self.gerar_arquivos_estaticos,
            'shell': self.entrar_conteiner_teste,
            'all': self.executar_tudo,
            'tudo': self.executar_tudo
        }
        
        if comando in comandos:
            return comandos[comando]()
        else:
            print(f"Opção inválida: {comando}")
            print("Opções: iniciar, conectividade, teste-completo, analisar, gerar-arquivos, shell, tudo")
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
                    self.gerar_arquivos_estaticos()
                elif escolha == '7':
                    self.executar_tudo()
                elif escolha == '8':
                    self.parar_conteineres()
                elif escolha == '0':
                    print("Saindo...")
                    self.parar_conteineres()
                    break
                else:
                    print(Cores.erro("Opção inválida"))
                    
            except KeyboardInterrupt:
                print("\n")
                print(Cores.aviso("Interrompido pelo usuário"))
                print(Cores.info("Deseja parar os contêineres? [S/N]: "), end='')
                try:
                    resp = input().lower()
                    if resp in ['s', 'sim', 'y', 'yes']:
                        self.parar_conteineres()
                except:
                    pass
                print("Saindo...")
                break
            except EOFError:
                print("\n")
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
            'gerar-arquivos', 'arquivos', 'shell', 'all', 'tudo'
        ], help='Comando para executar')
        
        args = parser.parse_args()
        success = projeto.executar_comando_linha(args.comando)
        sys.exit(0 if success else 1)
    
    #Menu interativo
    projeto.menu_interativo()

if __name__ == "__main__":
    main()

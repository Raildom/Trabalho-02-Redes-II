# Trabalho 02 - Redes II - Comparação de Servidores Web

## Aluno: 
   Raildom da Rocha Sobrinho
## Matrícula: 
   20239057601

## Link do GITHUB

**Repositório**: [https://github.com/Raildom/Trabalho-02-Redes-II.git]

## Link do Youtube

**Vídeo de Demonstração**: [EM BREVE]

---

## Objetivo

Comparar o desempenho de dois servidores web (**Nginx** e **Apache**) utilizando **Prometheus** e **Grafana** para observabilidade, analisando vantagens e desvantagens em diferentes cenários de carga.

---

## Tecnologias Utilizadas

- **Servidores Web**: Nginx, Apache
- **Observabilidade**: Prometheus, Grafana, nginx-exporter, apache-exporter, node-exporter
- **Infraestrutura**: Docker e Docker Compose
- **Testes**: Script personalizado em Python

---

## Como Executar o Projeto

### Pré-requisitos
- Docker e Docker Compose instalados
- Python 3.9 ou superior

### Passos para Execução

1. **Clone o repositório**:
```bash
git clone https://github.com/Raildom/Trabalho-02-Redes-II.git
cd Trabalho-02-Redes-II
```

2. **Execute o menu principal**:
```bash
python3 run_project.py
```

3. **Opções disponíveis no menu**:
   - `1` - Iniciar contêineres (Nginx, Apache, Prometheus, Grafana)
   - `2` - Teste de conectividade
   - `3` - Executar testes de carga completos
   - `4` - Gerar gráficos de análise
   - `5` - Acessar observabilidade (Prometheus/Grafana)
   - `6` - Entrar no contêiner de teste (Shell)
   - `7` - Gerar arquivos estáticos de teste
   - `8` - Executar tudo (início ao fim)
   - `9` - Parar contêineres
   - `0` - Sair

---

## Acesso aos Serviços

### Servidores Web (Rede Docker Interna)
- **Nginx**: http://76.1.0.10:80
- **Apache**: http://76.1.0.11:80

### Observabilidade (Acesso Local)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## Estrutura do Projeto

```
Trabalho-02-Redes-II/
│
├── README.md
├── requisitos.txt
├── run_project.py
│
├── src/
│   ├── cliente.py
│   ├── configuracao.py
│   ├── gerador_hash.py
│   └── gerar_arquivos_estaticos.py
│
├── Servidores/
│   ├── configuracoes_nginx.py
│   ├── configuracoes_apache.py
│   ├── nginx.conf
│   ├── httpd.conf
│   ├── pagina_inicial_nginx.html
│   └── pagina_inicial_apache.html
│
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.nginx
│   ├── Dockerfile.apache
│   ├── Dockerfile.cliente
│   ├── prometheus.yml
│   └── grafana-fontes-dados.yml
│
├── testes/
│   ├── teste_carga.py
│   └── analisar_resultados.py
│
├── arquivos_estaticos/
│   ├── pequeno-1kb.txt
│   ├── pequeno-10kb.txt
│   ├── pequeno-50kb.txt
│   ├── medio-100kb.txt
│   ├── medio-500kb.txt
│   ├── medio-700kb.txt
│   ├── grande-1mb.txt
│   ├── grande-5mb.txt
│   └── grande-7mb.txt
│
├── dashboard/
│
└── resultados/
    ├── resultados_testes.txt
    ├── resultados_testes.csv
    └── graficos/
```

---

## Arquitetura

### Rede Docker
- Sub-rede: `76.1.0.0/16`
- Nginx: `76.1.0.10:80`
- Apache: `76.1.0.11:80`
- Prometheus: `76.1.0.30:9090`
- Grafana: `76.1.0.40:3000`
- Cliente: `76.1.0.20`

### Containers
1. docker_nginx
2. docker_apache
3. prometheus
4. grafana
5. cliente_teste

---

## Cenários de Teste

O sistema executa **10 execuções completas** com **12 cenários cada** (120 testes totais):

### Cenários de API (3 cenários)
1. **Baixa Carga** - /api/info (10 usuários, 100 requisições)
2. **Média Carga** - /api/status (10 usuários, 500 requisições)
3. **Alta Carga** - /api/dados (100 usuários, 1000 requisições)

### Arquivos Pequenos (3 cenários)
4. **1KB** - pequeno-1kb.txt (10 usuários, 50 requisições)
5. **10KB** - pequeno-10kb.txt (10 usuários, 50 requisições)
6. **50KB** - pequeno-50kb.txt (10 usuários, 50 requisições)

### Arquivos Médios (3 cenários)
7. **100KB** - medio-100kb.txt (10 usuários, 50 requisições)
8. **500KB** - medio-500kb.txt (10 usuários, 50 requisições)
9. **700KB** - medio-700kb.txt (10 usuários, 50 requisições)

### Arquivos Grandes (3 cenários)
10. **1MB** - grande-1mb.txt (10 usuários, 50 requisições)
11. **5MB** - grande-5mb.txt (10 usuários, 50 requisições)
12. **7MB** - grande-7mb.txt (10 usuários, 50 requisições)

Cada cenário é testado em **ambos os servidores** (Nginx e Apache).

**Total de testes**: 10 execuções × 12 cenários × 2 servidores = 240 testes

---

## Métricas Analisadas

1. **Requisições por Segundo (RPS)**
2. **Latência Média** (milissegundos)
3. **Tempo Total** (segundos)
4. **CPU do Container** (%)

### Arquivos de Resultado

- `resultados_testes.txt` - Relatório completo em texto
- `resultados_testes.csv` - Dados detalhados com todas as métricas
- `graficos/` - 4 gráficos comparativos:
  - `01_throughput.png` - Requisições por segundo
  - `02_latencia.png` - Latência média
  - `03_tempo_total.png` - Tempo total de execução
  - `04_cpu.png` - Uso de CPU do container

---

## Cabeçalho HTTP Personalizado

```
X-Custom-ID: 40093cb61c18ade519baca198537dd16
```
*Hash MD5 de "20239057601 Raildom"*

---

# Métricas Comparativas - Nginx vs Apache

### 1. Status do Servidor (UP/DOWN)

**Query Comparativa:**
```promql
label_replace(nginx_up, "servidor", "nginx", "", "") 
or 
label_replace(apache_up, "servidor", "apache", "", "")
```

### 2. Total de Requisições

**Query Comparativa:**
```promql
label_replace(nginx_http_requests_total, "servidor", "nginx", "", "") 
or 
label_replace(apache_accesses_total, "servidor", "apache", "", "")
```

### 3. Taxa de Requisições (req/s)

**Query Comparativa:**
```promql
label_replace(rate(nginx_http_requests_total[1m]), "servidor", "nginx", "", "") 
or 
label_replace(rate(apache_accesses_total[1m]), "servidor", "apache", "", "")
```

### 4. Conexões/Workers Ativos

**Query Comparativa:**
```promql
label_replace(nginx_connections_active, "servidor", "nginx", "", "") 
or 
label_replace(apache_workers{state="busy"}, "servidor", "apache", "", "")
```

### 5. Uso de CPU (%)

**Query Comparativa (ambos containers):**
```promql
label_replace((1 - avg(rate(node_cpu_seconds_total{job="nginx-node",mode="idle"}[30s]))) * 100, "servidor", "nginx", "", "") 
or 
label_replace((1 - avg(rate(node_cpu_seconds_total{job="apache-node",mode="idle"}[30s]))) * 100, "servidor", "apache", "", "")
```

**Observação:** 
- Mede CPU do CONTAINER completo (servidor web + exporters + sistema)

### 6. Uso de Memória RAM (MB)

**Query Comparativa em MB:**
```promql
label_replace(process_resident_memory_bytes{job="nginx"} / (1024*1024), "servidor", "nginx", "", "") 
or
 label_replace(process_resident_memory_bytes{job="apache"} / (1024*1024), "servidor", "apache", "", "")
```

### 7. Bytes Transferidos (MB)

**Query Comparativa (MB/s):**
```promql
label_replace(rate(node_network_transmit_bytes_total{job="nginx-node",device="eth0"}[1m]) / (1024*1024), "servidor", "nginx", "", "")
or
label_replace(rate(node_network_transmit_bytes_total{job="apache-node",device="eth0"}[1m]) / (1024*1024), "servidor", "apache", "", "")
```

**Total Acumulado (MB):**
```promql
label_replace(node_network_transmit_bytes_total{job="nginx-node",device="eth0"} / (1024*1024), "servidor", "nginx", "", "")
or
label_replace(node_network_transmit_bytes_total{job="apache-node",device="eth0"} / (1024*1024), "servidor", "apache", "", "")
```

**Observação:** 
- Mede bytes transmitidos pela interface de rede eth0
- Inclui todo o tráfego do container (HTTP + overhead de protocolo)
- Taxa (rate) mostra MB/s em tempo real
- Total acumulado mostra MB totais desde o início

**Data:** Novembro/2025
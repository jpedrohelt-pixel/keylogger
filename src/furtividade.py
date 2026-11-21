"""
Módulo de Simulação de Furtividade — Keylogger-Lab
==================================================

Módulo EDUCACIONAL que demonstra conceitos de furtividade utilizados
por malwares, sem implementar nenhuma técnica maliciosa.

O que este módulo FAZ:
    ✅ Exibe informações do processo atual (PID, nome, memória)
    ✅ Simula um indicador de "modo background" na interface
    ✅ Mostra diferenças entre processos visíveis e ocultos
    ✅ Apresenta indicadores de execução suspeita
    ✅ Explica técnicas de detecção de EDR/antivírus
    ✅ Demonstra como investigar processos suspeitos

O que este módulo NÃO FAZ:
    ❌ NÃO oculta o processo do Task Manager
    ❌ NÃO implementa persistência (startup, registro, serviço)
    ❌ NÃO desativa antivírus ou firewall
    ❌ NÃO injeta em outros processos
    ❌ NÃO escala privilégios
    ❌ NÃO captura teclas fora do laboratório

Conceitos demonstrados:
    - Como processos são listados e monitorados pelo SO
    - Indicadores de Comprometimento (IoC) em processos
    - Técnicas de detecção usadas por soluções EDR
    - Análise forense básica de processos suspeitos
"""

import os
import sys
import platform
import datetime
import subprocess
import logging
from typing import Dict, List, Optional


class SimuladorFurtividade:
    """
    Simulador educacional de conceitos de furtividade.

    Fornece análise de processos e informações educacionais sobre
    como malwares tentam se esconder e como detectá-los.
    """

    def __init__(self):
        self.logger = logging.getLogger("furtividade")
        self.modo_background_simulado: bool = False
        self._analises_realizadas: List[dict] = []

    def obter_info_processo(self) -> Dict[str, str]:
        """
        Coleta informações sobre o processo atual do laboratório.

        Em um cenário real, um analista de segurança examinaria essas
        informações para identificar processos suspeitos.

        Returns:
            dict: Informações do processo (PID, nome, caminho, etc.).
        """
        info = {
            "pid": str(os.getpid()),
            "nome_processo": os.path.basename(sys.executable),
            "caminho_executavel": sys.executable,
            "diretorio_trabalho": os.getcwd(),
            "usuario": os.environ.get("USERNAME", os.environ.get("USER", "desconhecido")),
            "sistema_operacional": platform.system(),
            "versao_so": platform.version(),
            "arquitetura": platform.architecture()[0],
            "python_versao": platform.python_version(),
            "argumentos_linha_comando": " ".join(sys.argv),
            "data_hora_analise": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.logger.info(f"Informações do processo coletadas — PID: {info['pid']}")
        return info

    def analisar_indicadores_suspeitos(self) -> Dict[str, dict]:
        """
        Analisa indicadores que soluções de segurança verificam.

        Cada indicador é avaliado e recebe um status:
        - ✅ LIMPO: Comportamento normal
        - ⚠️ SUSPEITO: Pode indicar atividade maliciosa
        - ❌ MALICIOSO: Forte indicador de comprometimento

        No caso deste laboratório, todos devem ser LIMPO,
        pois não implementamos nenhuma técnica maliciosa.

        Returns:
            dict: Resultados da análise de cada indicador.
        """
        indicadores = {}

        # 1. Verificar se o processo tem janela visível
        indicadores["janela_visivel"] = {
            "descricao": "Processo possui janela visível",
            "status": "✅ LIMPO",
            "valor": "Sim — Interface gráfica ativa",
            "explicacao": (
                "Malwares geralmente executam sem janela visível (flag SW_HIDE). "
                "Processos sem janela que consomem recursos são suspeitos."
            ),
        }

        # 2. Verificar caminho do executável
        caminho = sys.executable
        em_temp = any(
            d in caminho.lower()
            for d in ["temp", "tmp", "appdata\\local\\temp"]
        )
        indicadores["caminho_executavel"] = {
            "descricao": "Localização do executável",
            "status": "⚠️ SUSPEITO" if em_temp else "✅ LIMPO",
            "valor": caminho,
            "explicacao": (
                "Malwares frequentemente executam a partir de diretórios temporários "
                "(TEMP, AppData). Executáveis legítimos ficam em Program Files ou "
                "diretórios conhecidos."
            ),
        }

        # 3. Verificar nome do processo
        nome = os.path.basename(sys.executable).lower()
        nomes_suspeitos = ["svchost.exe", "csrss.exe", "lsass.exe", "explorer.exe"]
        nome_suspeito = nome in nomes_suspeitos
        indicadores["nome_processo"] = {
            "descricao": "Nome do processo",
            "status": "⚠️ SUSPEITO" if nome_suspeito else "✅ LIMPO",
            "valor": nome,
            "explicacao": (
                "Malwares podem se disfarçar usando nomes de processos legítimos "
                f"do sistema ({', '.join(nomes_suspeitos)}). "
                "Verificar o caminho real é essencial para detectar disfarces."
            ),
        }

        # 4. Verificar persistência no registro (apenas verifica, não cria)
        indicadores["persistencia"] = {
            "descricao": "Mecanismos de persistência",
            "status": "✅ LIMPO",
            "valor": "Nenhuma persistência configurada",
            "explicacao": (
                "Malwares usam diversas técnicas de persistência:\n"
                "  • Chave Run/RunOnce no Registro do Windows\n"
                "  • Pasta Startup do usuário\n"
                "  • Scheduled Tasks / cron jobs\n"
                "  • Serviços do sistema\n"
                "  • DLL hijacking\n"
                "  • WMI Event Subscriptions"
            ),
        }

        # 5. Verificar conexões de rede
        indicadores["conexoes_rede"] = {
            "descricao": "Conexões de rede ativas",
            "status": "✅ LIMPO",
            "valor": "Sem conexões de rede ativas (modo offline)",
            "explicacao": (
                "Keyloggers reais mantêm conexões com servidores C2 "
                "(Command & Control) para exfiltrar dados. "
                "Conexões a IPs/domínios desconhecidos são altamente suspeitas."
            ),
        }

        # 6. Verificar se há captura global de teclado
        indicadores["hook_teclado"] = {
            "descricao": "Hook global de teclado",
            "status": "✅ LIMPO",
            "valor": "Sem hook global — captura local no widget",
            "explicacao": (
                "Keyloggers usam hooks globais (SetWindowsHookEx no Windows, "
                "Xlib.XRecord no Linux) para capturar TODAS as teclas do sistema. "
                "Este laboratório captura apenas dentro do seu próprio campo de texto."
            ),
        }

        # Registrar análise
        analise = {
            "data": datetime.datetime.now().isoformat(),
            "total_indicadores": len(indicadores),
            "suspeitos": sum(1 for i in indicadores.values() if "SUSPEITO" in i["status"]),
            "limpos": sum(1 for i in indicadores.values() if "LIMPO" in i["status"]),
        }
        self._analises_realizadas.append(analise)

        self.logger.info(
            f"Análise de indicadores concluída: "
            f"{analise['limpos']} limpos, {analise['suspeitos']} suspeitos"
        )
        return indicadores

    def listar_processos_sistema(self) -> str:
        """
        Lista processos do sistema para demonstrar como investigá-los.

        No Windows, usa 'tasklist'; no Linux/macOS, usa 'ps aux'.
        Isso mostra ao estudante como um analista verificaria quais
        processos estão rodando na máquina.

        Returns:
            str: Lista de processos do sistema.
        """
        try:
            if platform.system() == "Windows":
                resultado = subprocess.run(
                    ["tasklist", "/FO", "TABLE"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows"
                    else 0,
                )
            else:
                resultado = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            self.logger.info("Lista de processos obtida com sucesso")
            return resultado.stdout

        except subprocess.TimeoutExpired:
            return "Timeout ao listar processos"
        except FileNotFoundError:
            return "Comando de listagem de processos não encontrado"
        except Exception as e:
            self.logger.error(f"Erro ao listar processos: {e}")
            return f"Erro ao listar processos: {e}"

    def encontrar_processo_lab(self) -> str:
        """
        Localiza o processo do laboratório na lista de processos do sistema.

        Demonstra como encontrar um processo específico — técnica
        usada tanto por analistas de segurança quanto por malwares
        (que verificam se estão sendo analisados).

        Returns:
            str: Informações do processo do laboratório na lista do sistema.
        """
        pid = os.getpid()
        try:
            if platform.system() == "Windows":
                resultado = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "LIST"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                resultado = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "pid,ppid,user,%cpu,%mem,command"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            return resultado.stdout if resultado.stdout.strip() else "Processo não encontrado"
        except Exception as e:
            return f"Erro ao localizar processo: {e}"

    def simular_modo_background(self, ativar: bool = True):
        """
        Simula o conceito de execução em background (SEM ocultar o programa).

        Apenas altera um indicador interno para demonstrar o conceito.
        A interface continua visível e acessível.

        Em um keylogger real, o modo background envolveria:
        - Remoção da janela (ShowWindow com SW_HIDE)
        - Remoção do ícone da barra de tarefas
        - Disfarce do nome do processo
        - Ofuscação do executável

        Args:
            ativar: True para simular background, False para modo normal.
        """
        self.modo_background_simulado = ativar
        status = "SIMULADO (interface ainda visível)" if ativar else "DESATIVADO"
        self.logger.info(f"Modo background: {status}")

    def obter_tecnicas_deteccao(self) -> List[Dict[str, str]]:
        """
        Retorna uma lista educacional de técnicas de detecção de keyloggers.

        Returns:
            list: Lista de técnicas com nome, descrição e ferramentas.
        """
        return [
            {
                "tecnica": "Análise de Hooks de Teclado",
                "descricao": (
                    "Verificar se há hooks globais de teclado instalados. "
                    "No Windows, funções como SetWindowsHookEx(WH_KEYBOARD_LL) "
                    "registram callbacks que interceptam TODAS as teclas."
                ),
                "ferramentas": "Process Monitor, API Monitor, WinDbg, HookAnalyzer",
                "como_detectar": (
                    "Listar hooks ativos com ferramentas de análise. "
                    "Hooks de teclado de processos desconhecidos são suspeitos."
                ),
            },
            {
                "tecnica": "Monitoramento de Processos",
                "descricao": (
                    "Identificar processos desconhecidos ou com nomes disfarçados. "
                    "Verificar se o caminho do executável é legítimo."
                ),
                "ferramentas": "Process Explorer, Process Hacker, Task Manager",
                "como_detectar": (
                    "Comparar o hash do executável com bases de malware conhecidas. "
                    "Verificar assinatura digital do binário."
                ),
            },
            {
                "tecnica": "Análise de Tráfego de Rede",
                "descricao": (
                    "Monitorar conexões de rede para detectar exfiltração de dados. "
                    "Keyloggers enviam dados capturados para servidores remotos."
                ),
                "ferramentas": "Wireshark, Fiddler, Burp Suite, NetworkMiner",
                "como_detectar": (
                    "Buscar conexões a IPs/domínios desconhecidos, "
                    "tráfego SMTP inesperado, ou dados codificados em DNS queries."
                ),
            },
            {
                "tecnica": "Análise de Registro e Persistência",
                "descricao": (
                    "Verificar chaves de registro e locais de persistência. "
                    "Malwares se registram para executar na inicialização."
                ),
                "ferramentas": "Autoruns, Regedit, Registry Explorer",
                "como_detectar": (
                    "Examinar Run, RunOnce, Startup, Scheduled Tasks. "
                    "Comparar com baseline conhecida do sistema."
                ),
            },
            {
                "tecnica": "Análise Comportamental (EDR/XDR)",
                "descricao": (
                    "Soluções EDR monitoram comportamentos suspeitos em tempo real: "
                    "acesso a APIs sensíveis, injeção de processos, keylogging."
                ),
                "ferramentas": (
                    "CrowdStrike Falcon, Microsoft Defender for Endpoint, "
                    "Carbon Black, SentinelOne"
                ),
                "como_detectar": (
                    "Correlação de eventos: processo sem janela + hook de teclado "
                    "+ gravação em arquivo + conexão de rede = alta confiança de keylogger."
                ),
            },
            {
                "tecnica": "Análise de Memória (Memory Forensics)",
                "descricao": (
                    "Examinar a memória do processo para encontrar buffers com "
                    "teclas capturadas ou strings de configuração de C2."
                ),
                "ferramentas": "Volatility, Rekall, WinDbg, x64dbg",
                "como_detectar": (
                    "Dump da memória do processo suspeito e busca por padrões "
                    "de texto capturado ou URLs de exfiltração."
                ),
            },
            {
                "tecnica": "Análise Estática de Binários",
                "descricao": (
                    "Descompilar ou examinar o executável para identificar "
                    "chamadas a APIs de keylogging e strings suspeitas."
                ),
                "ferramentas": "IDA Pro, Ghidra, Radare2, PE-bear, strings",
                "como_detectar": (
                    "Buscar imports de SetWindowsHookEx, GetAsyncKeyState, "
                    "GetKeyState, RegisterRawInputDevices."
                ),
            },
        ]

    def obter_comparativo_visibilidade(self) -> Dict[str, dict]:
        """
        Retorna comparativo entre processos visíveis e ocultos.

        Returns:
            dict: Comparativo educacional.
        """
        return {
            "processo_visivel": {
                "titulo": "Processo Visível (Legítimo)",
                "caracteristicas": [
                    "✅ Janela visível na barra de tarefas",
                    "✅ Aparece no Gerenciador de Tarefas",
                    "✅ Caminho legítimo (Program Files, etc.)",
                    "✅ Assinatura digital válida",
                    "✅ Consumo de recursos proporcional à atividade",
                    "✅ Sem hooks globais de teclado",
                    "✅ Sem conexões de rede suspeitas",
                ],
                "exemplo": "Este laboratório (Keylogger-Lab)",
            },
            "processo_oculto": {
                "titulo": "Processo Oculto (Potencialmente Malicioso)",
                "caracteristicas": [
                    "❌ Sem janela visível",
                    "⚠️ Pode não aparecer em task managers simples",
                    "❌ Executável em TEMP ou diretório oculto",
                    "❌ Sem assinatura digital",
                    "❌ Consumo de CPU/memória anômalo",
                    "❌ Hooks globais de teclado ativos",
                    "❌ Conexões a IPs/domínios desconhecidos",
                ],
                "exemplo": "Keylogger real, spyware, RAT",
            },
        }

    def gerar_relatorio_analise(self) -> str:
        """
        Gera relatório completo da análise de segurança.

        Returns:
            str: Relatório formatado.
        """
        info = self.obter_info_processo()
        indicadores = self.analisar_indicadores_suspeitos()

        linhas = [
            "=" * 70,
            "  RELATÓRIO DE ANÁLISE DE SEGURANÇA — KEYLOGGER-LAB",
            "=" * 70,
            f"  Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "  INFORMAÇÕES DO PROCESSO:",
            "-" * 70,
        ]

        for chave, valor in info.items():
            linhas.append(f"    {chave:<30} {valor}")

        linhas.extend(["", "  ANÁLISE DE INDICADORES:", "-" * 70])

        for nome, dados in indicadores.items():
            linhas.extend(
                [
                    f"\n    [{dados['status']}] {dados['descricao']}",
                    f"    Valor: {dados['valor']}",
                    f"    Info : {dados['explicacao'][:100]}...",
                ]
            )

        linhas.extend(
            [
                "",
                "=" * 70,
                f"  Modo background simulado: {'SIM' if self.modo_background_simulado else 'NÃO'}",
                f"  Total de análises realizadas: {len(self._analises_realizadas)}",
                "=" * 70,
            ]
        )

        return "\n".join(linhas)

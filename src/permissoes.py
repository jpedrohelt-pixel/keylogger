"""
Módulo de Permissões — Keylogger-Lab
====================================

Implementa um sistema de autorização que exige consentimento explícito
do usuário antes de ativar funcionalidades sensíveis.

Conceitos demonstrados:
    - Controle de acesso baseado em permissões
    - Tokens de autorização
    - Auditoria de concessão/revogação de permissões
    - Princípio do menor privilégio

Este módulo garante que nenhuma funcionalidade de captura, armazenamento
ou transmissão opere sem autorização prévia — reforçando o caráter ético
e educacional do projeto.
"""

import hashlib
import json
import os
import datetime
import logging
from typing import Dict, Optional


class SistemaPermissoes:
    """
    Gerencia permissões de acesso às funcionalidades do laboratório.

    Cada permissão é registrada com:
    - Status (concedida/revogada)
    - Usuário que autorizou
    - Data e horário da autorização
    - Token SHA-256 de verificação

    Attributes:
        PERMISSOES_DISPONIVEIS (list): Lista de permissões reconhecidas pelo sistema.
    """

    PERMISSOES_DISPONIVEIS = [
        "captura",          # Permissão para capturar teclas
        "armazenamento",    # Permissão para salvar logs em disco
        "envio_email",      # Permissão para enviar relatórios por e-mail
        "furtividade",      # Permissão para executar simulações de furtividade
        "criptografia",     # Permissão para criptografar/descriptografar arquivos
    ]

    def __init__(self, caminho_config: str = "config_permissoes.json"):
        """
        Inicializa o sistema de permissões.

        Args:
            caminho_config: Caminho do arquivo JSON que persiste as permissões.
        """
        self.caminho_config = caminho_config
        self.permissoes: Dict[str, dict] = {}
        self.logger = logging.getLogger("permissoes")
        self._carregar_config()

    def _carregar_config(self):
        """Carrega permissões salvas do disco, se existirem."""
        if os.path.exists(self.caminho_config):
            try:
                with open(self.caminho_config, "r", encoding="utf-8") as f:
                    self.permissoes = json.load(f)
                self.logger.info(f"Configuração de permissões carregada: {self.caminho_config}")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Erro ao carregar permissões, iniciando vazio: {e}")
                self.permissoes = {}
        else:
            self.logger.info("Nenhuma configuração de permissões encontrada — iniciando vazio")

    def _salvar_config(self):
        """Persiste as permissões atuais em disco."""
        try:
            with open(self.caminho_config, "w", encoding="utf-8") as f:
                json.dump(self.permissoes, f, indent=2, ensure_ascii=False)
            self.logger.debug("Configuração de permissões salva")
        except IOError as e:
            self.logger.error(f"Erro ao salvar configuração de permissões: {e}")

    def _gerar_token(self, permissao: str, usuario: str) -> str:
        """
        Gera um token SHA-256 para identificar a concessão de permissão.

        O token serve como prova criptográfica de que a permissão foi
        concedida por um usuário específico em um momento específico.

        Args:
            permissao: Nome da permissão.
            usuario: Identificador do usuário.

        Returns:
            str: Hash SHA-256 truncado (16 caracteres hexadecimais).
        """
        dados = f"{permissao}:{usuario}:{datetime.datetime.now().isoformat()}"
        return hashlib.sha256(dados.encode("utf-8")).hexdigest()[:16]

    def conceder_permissao(self, permissao: str, usuario: str = "laboratorio") -> bool:
        """
        Concede uma permissão específica.

        Args:
            permissao: Nome da permissão (deve estar em PERMISSOES_DISPONIVEIS).
            usuario: Identificador de quem está concedendo a permissão.

        Returns:
            bool: True se a permissão foi concedida, False se a permissão não existe.
        """
        if permissao not in self.PERMISSOES_DISPONIVEIS:
            self.logger.warning(f"Tentativa de conceder permissão desconhecida: {permissao}")
            return False

        self.permissoes[permissao] = {
            "concedida": True,
            "usuario": usuario,
            "data_concessao": datetime.datetime.now().isoformat(),
            "token": self._gerar_token(permissao, usuario),
        }
        self._salvar_config()
        self.logger.info(f"Permissão '{permissao}' concedida ao usuário '{usuario}'")
        return True

    def revogar_permissao(self, permissao: str) -> bool:
        """
        Revoga uma permissão específica.

        Args:
            permissao: Nome da permissão a ser revogada.

        Returns:
            bool: True se revogada com sucesso, False se não estava concedida.
        """
        if permissao not in self.permissoes:
            self.logger.warning(f"Tentativa de revogar permissão não concedida: {permissao}")
            return False

        self.permissoes[permissao]["concedida"] = False
        self.permissoes[permissao]["data_revogacao"] = datetime.datetime.now().isoformat()
        self._salvar_config()
        self.logger.info(f"Permissão '{permissao}' revogada")
        return True

    def verificar_permissao(self, permissao: str) -> bool:
        """
        Verifica se uma permissão está ativa.

        Args:
            permissao: Nome da permissão a verificar.

        Returns:
            bool: True se a permissão está concedida e ativa.
        """
        return self.permissoes.get(permissao, {}).get("concedida", False)

    def obter_detalhes(self, permissao: str) -> Optional[dict]:
        """
        Retorna os detalhes completos de uma permissão.

        Args:
            permissao: Nome da permissão.

        Returns:
            dict ou None: Detalhes da permissão ou None se não existir.
        """
        return self.permissoes.get(permissao)

    def listar_permissoes(self) -> Dict[str, dict]:
        """
        Lista todas as permissões e seus estados.

        Returns:
            dict: Dicionário com todas as permissões registradas.
        """
        return self.permissoes.copy()

    def listar_ativas(self) -> list:
        """
        Lista apenas as permissões atualmente ativas.

        Returns:
            list: Nomes das permissões ativas.
        """
        return [p for p, d in self.permissoes.items() if d.get("concedida", False)]

    def conceder_todas(self, usuario: str = "laboratorio"):
        """
        Concede todas as permissões disponíveis.

        Útil para configuração rápida do laboratório em ambiente controlado.

        Args:
            usuario: Identificador do usuário.
        """
        for permissao in self.PERMISSOES_DISPONIVEIS:
            self.conceder_permissao(permissao, usuario)
        self.logger.info(f"Todas as permissões concedidas ao usuário '{usuario}'")

    def revogar_todas(self):
        """Revoga todas as permissões ativas."""
        for permissao in list(self.permissoes.keys()):
            self.revogar_permissao(permissao)
        self.logger.info("Todas as permissões revogadas")

    def gerar_relatorio(self) -> str:
        """
        Gera um relatório textual do estado das permissões.

        Returns:
            str: Relatório formatado.
        """
        linhas = [
            "=" * 50,
            "  RELATÓRIO DE PERMISSÕES — KEYLOGGER-LAB",
            "=" * 50,
            f"  Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 50,
        ]

        for permissao in self.PERMISSOES_DISPONIVEIS:
            detalhes = self.permissoes.get(permissao, {})
            status = "✅ ATIVA" if detalhes.get("concedida", False) else "❌ INATIVA"
            usuario = detalhes.get("usuario", "—")
            data = detalhes.get("data_concessao", "—")
            linhas.append(f"  {permissao:<20} {status:<12} Usuário: {usuario}  Data: {data}")

        linhas.append("=" * 50)
        return "\n".join(linhas)

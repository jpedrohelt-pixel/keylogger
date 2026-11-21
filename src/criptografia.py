"""
Módulo de Criptografia — Keylogger-Lab
======================================

Implementa criptografia simétrica (Fernet/AES-128-CBC) para proteger
os arquivos de log gerados pelo laboratório.

Conceitos demonstrados:
    - Geração e gerenciamento de chaves simétricas
    - Criptografia e descriptografia de dados em memória
    - Criptografia de arquivos em disco
    - Boas práticas de armazenamento de chaves

Dependência: cryptography (pip install cryptography)
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken


class GerenciadorCriptografia:
    """
    Gerencia operações de criptografia simétrica usando Fernet (AES-128-CBC + HMAC).

    O Fernet garante que dados criptografados não possam ser manipulados
    ou lidos sem a chave correta, fornecendo confidencialidade e integridade.

    Attributes:
        caminho_chave (str): Caminho do arquivo que armazena a chave.
        chave (bytes): Chave Fernet de 32 bytes codificada em base64.
        fernet (Fernet): Instância do objeto Fernet para operações criptográficas.
    """

    def __init__(self, caminho_chave: str = "chave.key"):
        """
        Inicializa o gerenciador, carregando ou gerando uma chave.

        Args:
            caminho_chave: Caminho para o arquivo de chave. Se não existir,
                          uma nova chave será gerada automaticamente.
        """
        self.caminho_chave = caminho_chave
        self.logger = logging.getLogger("criptografia")
        self.chave = self._carregar_ou_gerar_chave()
        self.fernet = Fernet(self.chave)
        self.logger.info("Gerenciador de criptografia inicializado")

    def _carregar_ou_gerar_chave(self) -> bytes:
        """
        Carrega a chave do disco ou gera uma nova se não existir.

        A chave Fernet é uma string de 32 bytes codificada em URL-safe base64.
        Em um cenário real, a chave deveria ser armazenada em um cofre seguro
        (ex: AWS KMS, HashiCorp Vault), não em um arquivo de texto.

        Returns:
            bytes: Chave Fernet válida.
        """
        if os.path.exists(self.caminho_chave):
            try:
                with open(self.caminho_chave, "rb") as f:
                    chave = f.read().strip()
                # Validar que a chave é um Fernet válido
                Fernet(chave)
                self.logger.info(f"Chave carregada de: {self.caminho_chave}")
                return chave
            except (InvalidToken, ValueError, Exception) as e:
                self.logger.warning(f"Chave inválida encontrada, gerando nova: {e}")

        # Gerar nova chave
        chave = Fernet.generate_key()
        with open(self.caminho_chave, "wb") as f:
            f.write(chave)
        self.logger.info(f"Nova chave gerada e salva em: {self.caminho_chave}")
        return chave

    def criptografar(self, dados: str) -> bytes:
        """
        Criptografa uma string em memória.

        O Fernet adiciona automaticamente:
        - Versão do formato (1 byte)
        - Timestamp (8 bytes) — permite verificar idade do token
        - IV aleatório (16 bytes) — garante que textos iguais gerem cifras diferentes
        - Ciphertext (AES-128-CBC com padding PKCS7)
        - HMAC-SHA256 (32 bytes) — garante integridade

        Args:
            dados: String a ser criptografada.

        Returns:
            bytes: Token Fernet contendo os dados criptografados.

        Raises:
            ValueError: Se os dados forem None ou vazios.
        """
        if not dados:
            raise ValueError("Dados para criptografia não podem ser vazios")

        token = self.fernet.encrypt(dados.encode("utf-8"))
        self.logger.debug(f"Dados criptografados: {len(dados)} chars -> {len(token)} bytes")
        return token

    def descriptografar(self, dados: bytes) -> str:
        """
        Descriptografa um token Fernet de volta para string.

        A descriptografia também verifica:
        - Integridade (HMAC-SHA256) — detecta adulteração
        - Formato válido — detecta dados corrompidos

        Args:
            dados: Token Fernet a ser descriptografado.

        Returns:
            str: String original descriptografada.

        Raises:
            InvalidToken: Se o token for inválido, adulterado ou a chave estiver errada.
        """
        try:
            texto = self.fernet.decrypt(dados).decode("utf-8")
            self.logger.debug(f"Dados descriptografados: {len(dados)} bytes -> {len(texto)} chars")
            return texto
        except InvalidToken:
            self.logger.error("Falha na descriptografia: token inválido ou chave incorreta")
            raise
        except Exception as e:
            self.logger.error(f"Erro inesperado na descriptografia: {e}")
            raise

    def criptografar_arquivo(self, caminho: str) -> str:
        """
        Lê um arquivo de texto, criptografa seu conteúdo e salva com extensão .enc.

        O arquivo original NÃO é removido automaticamente. Em um cenário real
        de malware, o arquivo original seria deletado após a criptografia
        (técnica usada por ransomware).

        Args:
            caminho: Caminho do arquivo de texto a ser criptografado.

        Returns:
            str: Caminho do arquivo criptografado (.enc).

        Raises:
            FileNotFoundError: Se o arquivo de origem não existir.
        """
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()

        dados_criptografados = self.criptografar(conteudo)
        caminho_cripto = caminho + ".enc"

        with open(caminho_cripto, "wb") as f:
            f.write(dados_criptografados)

        self.logger.info(f"Arquivo criptografado: {caminho} -> {caminho_cripto}")
        return caminho_cripto

    def descriptografar_arquivo(self, caminho_cripto: str) -> str:
        """
        Lê um arquivo .enc e retorna seu conteúdo descriptografado.

        Args:
            caminho_cripto: Caminho do arquivo criptografado (.enc).

        Returns:
            str: Conteúdo original descriptografado.

        Raises:
            FileNotFoundError: Se o arquivo criptografado não existir.
            InvalidToken: Se a chave estiver incorreta ou o arquivo estiver corrompido.
        """
        if not os.path.exists(caminho_cripto):
            raise FileNotFoundError(f"Arquivo criptografado não encontrado: {caminho_cripto}")

        with open(caminho_cripto, "rb") as f:
            dados = f.read()

        texto = self.descriptografar(dados)
        self.logger.info(f"Arquivo descriptografado: {caminho_cripto}")
        return texto

    def rotacionar_chave(self) -> bytes:
        """
        Gera uma nova chave, substituindo a anterior.

        ATENÇÃO: Arquivos criptografados com a chave anterior não poderão
        ser descriptografados com a nova chave. Em produção, implementar
        um sistema de migração de chaves (re-encrypt com nova chave).

        Returns:
            bytes: Nova chave gerada.
        """
        nova_chave = Fernet.generate_key()
        with open(self.caminho_chave, "wb") as f:
            f.write(nova_chave)

        self.chave = nova_chave
        self.fernet = Fernet(self.chave)
        self.logger.warning("Chave rotacionada — arquivos anteriores podem ficar inacessíveis")
        return nova_chave

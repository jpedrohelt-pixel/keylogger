"""
Interface Gráfica — Keylogger-Lab
=================================

Interface moderna com CustomTkinter organizada em abas:
    1. 🔑 Captura   — Campo de entrada, controles, visualizador de teclas
    2. 📁 Arquivos  — Gerenciamento de sessões e visualizador de logs
    3. 📧 E-mail    — Configuração SMTP, envio e histórico
    4. 🛡 Segurança — Análise de processos e simulação de furtividade

Padrão arquitetural: MVC simplificado
    - Interface (View) → esta classe
    - Módulos (Model/Controller) → captura, armazenamento, email, furtividade
"""

import os
import threading
import datetime
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional

import customtkinter as ctk

from src.captura import MotorCaptura
from src.armazenamento import GerenciadorArmazenamento
from src.email_sender import GerenciadorEmail
from src.furtividade import SimuladorFurtividade
from src.permissoes import SistemaPermissoes


# ─── Configuração de aparência ──────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class InterfaceLab(ctk.CTk):
    """
    Janela principal do Keylogger-Lab.

    Integra todos os módulos do laboratório em uma interface gráfica
    unificada com navegação por abas.
    """

    # Dimensões da janela
    LARGURA = 1000
    ALTURA = 700

    def __init__(self):
        super().__init__()

        # ─── Configuração da janela ─────────────────────────────────
        self.title("🔬 KEYLOGGER-LAB — Laboratório Educacional de Cibersegurança")
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.minsize(900, 600)

        # ─── Logger ────────────────────────────────────────────────
        self.logger = logging.getLogger("interface")

        # ─── Inicializar módulos ───────────────────────────────────
        self.permissoes = SistemaPermissoes()
        self.armazenamento = GerenciadorArmazenamento(diretorio_logs="logs")
        self.motor_captura = MotorCaptura(
            armazenamento=self.armazenamento,
            callback_tecla=self._callback_tecla_capturada,
        )
        self.email_manager = GerenciadorEmail()
        self.simulador = SimuladorFurtividade()

        # ─── Variáveis de estado ───────────────────────────────────
        self._status_text = ctk.StringVar(value="● INATIVO")
        self._sessao_text = ctk.StringVar(value="Sessão: —")
        self._contagem_text = ctk.StringVar(value="Teclas: 0")
        self._timer_status: Optional[str] = None

        # ─── Construir interface ───────────────────────────────────
        self._criar_header()
        self._criar_abas()
        self._criar_barra_status()

        # ─── Atualizar status periodicamente ───────────────────────
        self._atualizar_status()

        # ─── Tratar fechamento ─────────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        self.logger.info("Interface inicializada com sucesso")

    # ═══════════════════════════════════════════════════════════════
    #  HEADER
    # ═══════════════════════════════════════════════════════════════

    def _criar_header(self):
        """Cria o cabeçalho da aplicação."""
        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        titulo = ctk.CTkLabel(
            header,
            text="🔬 KEYLOGGER-LAB",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        titulo.pack(side="left", padx=20)

        subtitulo = ctk.CTkLabel(
            header,
            text="Laboratório Educacional de Cibersegurança",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitulo.pack(side="left", padx=5)

        # Indicador de status no header
        self.status_indicator = ctk.CTkLabel(
            header,
            textvariable=self._status_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50",
        )
        self.status_indicator.pack(side="right", padx=20)

    # ═══════════════════════════════════════════════════════════════
    #  SISTEMA DE ABAS
    # ═══════════════════════════════════════════════════════════════

    def _criar_abas(self):
        """Cria o sistema de abas com as 4 seções do laboratório."""
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 0))

        # Criar abas
        self.tab_captura = self.tabview.add("🔑 Captura")
        self.tab_arquivos = self.tabview.add("📁 Arquivos")
        self.tab_email = self.tabview.add("📧 E-mail")
        self.tab_seguranca = self.tabview.add("🛡 Segurança")

        # Popular cada aba
        self._construir_aba_captura()
        self._construir_aba_arquivos()
        self._construir_aba_email()
        self._construir_aba_seguranca()

    # ═══════════════════════════════════════════════════════════════
    #  ABA 1: CAPTURA
    # ═══════════════════════════════════════════════════════════════

    def _construir_aba_captura(self):
        """Constrói a aba de captura de teclas."""
        frame = self.tab_captura

        # ─── Instrução ────────────────────────────────────────────
        instrucao = ctk.CTkLabel(
            frame,
            text=(
                "Digite no campo abaixo para capturar teclas. "
                "A captura ocorre APENAS neste campo."
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        instrucao.pack(pady=(5, 5))

        # ─── Campo de entrada (widget-alvo da captura) ────────────
        label_campo = ctk.CTkLabel(
            frame, text="Campo de Entrada (área monitorada):",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        label_campo.pack(anchor="w", padx=10, pady=(5, 2))

        self.campo_entrada = ctk.CTkTextbox(
            frame, height=100, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=14),
            border_width=2, border_color="#2196F3",
        )
        self.campo_entrada.pack(fill="x", padx=10, pady=(0, 5))

        # Vincular o motor de captura ao campo
        self.motor_captura.vincular_widget(self.campo_entrada)

        # ─── Botões de controle ───────────────────────────────────
        frame_botoes = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=10, pady=5)

        self.btn_iniciar = ctk.CTkButton(
            frame_botoes, text="▶ INICIAR CAPTURA",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50", hover_color="#388E3C",
            height=40, command=self._iniciar_captura,
        )
        self.btn_iniciar.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.btn_parar = ctk.CTkButton(
            frame_botoes, text="⏹ INTERROMPER CAPTURA",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#F44336", hover_color="#D32F2F",
            height=40, command=self._parar_captura, state="disabled",
        )
        self.btn_parar.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.btn_limpar = ctk.CTkButton(
            frame_botoes, text="🗑 Limpar",
            font=ctk.CTkFont(size=13),
            fg_color="#607D8B", hover_color="#455A64",
            height=40, width=100, command=self._limpar_campo,
        )
        self.btn_limpar.pack(side="left")

        # ─── Visualizador de teclas registradas ───────────────────
        label_log = ctk.CTkLabel(
            frame, text="Teclas Registradas (tempo real):",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        label_log.pack(anchor="w", padx=10, pady=(10, 2))

        self.log_teclas = ctk.CTkTextbox(
            frame, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled",
        )
        self.log_teclas.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    def _callback_tecla_capturada(self, tecla: str, tipo: str):
        """Callback chamado a cada tecla capturada — atualiza o visualizador."""
        horario = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        linha = f"  {horario}   {tipo:<12} {tecla}\n"

        self.log_teclas.configure(state="normal")
        self.log_teclas.insert("end", linha)
        self.log_teclas.see("end")
        self.log_teclas.configure(state="disabled")

        # Atualizar contagem
        self._contagem_text.set(f"Teclas: {self.motor_captura.contagem_teclas}")

    def _iniciar_captura(self):
        """Inicia a captura de teclas."""
        if not self.permissoes.verificar_permissao("captura"):
            resposta = messagebox.askyesno(
                "Permissão Necessária",
                "A captura de teclas requer autorização.\n\n"
                "Este é um ambiente educacional controlado.\n"
                "As teclas serão capturadas APENAS no campo de entrada.\n\n"
                "Deseja conceder permissão?",
            )
            if not resposta:
                return
            self.permissoes.conceder_permissao("captura")
            self.permissoes.conceder_permissao("armazenamento")

        try:
            sessao = self.motor_captura.iniciar_captura()
            self._sessao_text.set(f"Sessão: {sessao}")
            self._status_text.set("● CAPTURANDO")
            self.status_indicator.configure(text_color="#F44336")

            self.btn_iniciar.configure(state="disabled")
            self.btn_parar.configure(state="normal")

            # Log header
            self.log_teclas.configure(state="normal")
            self.log_teclas.insert(
                "end",
                f"\n{'─' * 50}\n"
                f"  Sessão {sessao} iniciada — "
                f"{datetime.datetime.now().strftime('%H:%M:%S')}\n"
                f"{'─' * 50}\n",
            )
            self.log_teclas.configure(state="disabled")

            self.logger.info(f"Captura iniciada pela interface — {sessao}")
        except RuntimeError as e:
            messagebox.showerror("Erro", str(e))

    def _parar_captura(self):
        """Interrompe a captura de teclas."""
        sessao = self.motor_captura.parar_captura()
        self._status_text.set("● INATIVO")
        self.status_indicator.configure(text_color="#4CAF50")
        self._sessao_text.set("Sessão: —")

        self.btn_iniciar.configure(state="normal")
        self.btn_parar.configure(state="disabled")

        # Log footer
        self.log_teclas.configure(state="normal")
        self.log_teclas.insert(
            "end",
            f"{'─' * 50}\n"
            f"  Sessão finalizada — "
            f"{self.motor_captura.contagem_teclas} teclas\n"
            f"{'─' * 50}\n\n",
        )
        self.log_teclas.configure(state="disabled")

        self.logger.info(f"Captura interrompida pela interface — {sessao}")

        # Atualizar lista de arquivos
        self._atualizar_lista_sessoes()

    def _limpar_campo(self):
        """Limpa o campo de entrada e o log de teclas."""
        self.campo_entrada.delete("1.0", "end")
        self.log_teclas.configure(state="normal")
        self.log_teclas.delete("1.0", "end")
        self.log_teclas.configure(state="disabled")
        self._contagem_text.set("Teclas: 0")

    # ═══════════════════════════════════════════════════════════════
    #  ABA 2: ARQUIVOS
    # ═══════════════════════════════════════════════════════════════

    def _construir_aba_arquivos(self):
        """Constrói a aba de gerenciamento de arquivos."""
        frame = self.tab_arquivos

        # Layout em duas colunas
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(1, weight=1)

        # ─── Coluna esquerda: lista de sessões ────────────────────
        label_sessoes = ctk.CTkLabel(
            frame, text="Sessões Disponíveis:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        label_sessoes.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 2))

        self.lista_sessoes = ctk.CTkTextbox(
            frame, width=250, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.lista_sessoes.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 5))
        self.lista_sessoes.bind("<ButtonRelease-1>", self._ao_clicar_sessao)

        # ─── Coluna direita: visualizador ─────────────────────────
        label_conteudo = ctk.CTkLabel(
            frame, text="Conteúdo da Sessão:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        label_conteudo.grid(row=0, column=1, sticky="w", padx=5, pady=(5, 2))

        self.viewer_sessao = ctk.CTkTextbox(
            frame, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
        )
        self.viewer_sessao.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 5))

        # ─── Botões de ação ───────────────────────────────────────
        frame_acoes = ctk.CTkFrame(frame, fg_color="transparent")
        frame_acoes.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkButton(
            frame_acoes, text="🔄 Atualizar",
            command=self._atualizar_lista_sessoes,
            width=120,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_acoes, text="📋 Gerar Relatório",
            command=self._gerar_relatorio,
            width=140,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_acoes, text="🗑 Excluir Sessão",
            command=self._excluir_sessao,
            fg_color="#F44336", hover_color="#D32F2F",
            width=140,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_acoes, text="🔐 Criptografar",
            command=self._criptografar_sessao,
            fg_color="#FF9800", hover_color="#F57C00",
            width=140,
        ).pack(side="left", padx=5)

        # Carregar lista inicial
        self._atualizar_lista_sessoes()

    def _atualizar_lista_sessoes(self):
        """Atualiza a lista de sessões disponíveis."""
        sessoes = self.armazenamento.listar_sessoes()
        self.lista_sessoes.delete("1.0", "end")
        if sessoes:
            for s in sessoes:
                self.lista_sessoes.insert("end", f"  📄 {s}\n")
        else:
            self.lista_sessoes.insert("end", "  Nenhuma sessão encontrada.\n")

    def _ao_clicar_sessao(self, _event=None):
        """Ao clicar em uma sessão, exibe seu conteúdo."""
        try:
            # Obter a linha clicada
            index = self.lista_sessoes.index("insert")
            linha = self.lista_sessoes.get(f"{index} linestart", f"{index} lineend").strip()
            # Extrair nome do arquivo
            nome = linha.replace("📄", "").strip()
            if nome and nome.endswith(".txt"):
                conteudo = self.armazenamento.ler_sessao(nome)
                self.viewer_sessao.configure(state="normal")
                self.viewer_sessao.delete("1.0", "end")
                if conteudo:
                    self.viewer_sessao.insert("1.0", conteudo)
                else:
                    self.viewer_sessao.insert("1.0", "Não foi possível ler o arquivo.")
                self.viewer_sessao.configure(state="disabled")
        except Exception:
            pass

    def _gerar_relatorio(self):
        """Gera e exibe o relatório geral."""
        relatorio = self.armazenamento.gerar_relatorio()
        self.viewer_sessao.configure(state="normal")
        self.viewer_sessao.delete("1.0", "end")
        self.viewer_sessao.insert("1.0", relatorio)
        self.viewer_sessao.configure(state="disabled")

    def _excluir_sessao(self):
        """Exclui a sessão selecionada."""
        try:
            index = self.lista_sessoes.index("insert")
            linha = self.lista_sessoes.get(f"{index} linestart", f"{index} lineend").strip()
            nome = linha.replace("📄", "").strip()
            if nome and nome.endswith(".txt"):
                if messagebox.askyesno("Confirmar", f"Excluir '{nome}'?"):
                    self.armazenamento.excluir_sessao(nome)
                    self._atualizar_lista_sessoes()
                    self.viewer_sessao.configure(state="normal")
                    self.viewer_sessao.delete("1.0", "end")
                    self.viewer_sessao.configure(state="disabled")
        except Exception:
            messagebox.showwarning("Aviso", "Selecione uma sessão na lista.")

    def _criptografar_sessao(self):
        """Criptografa a sessão selecionada."""
        try:
            index = self.lista_sessoes.index("insert")
            linha = self.lista_sessoes.get(f"{index} linestart", f"{index} lineend").strip()
            nome = linha.replace("📄", "").strip()
            if nome and nome.endswith(".txt"):
                from src.criptografia import GerenciadorCriptografia

                cripto = GerenciadorCriptografia()
                caminho = os.path.join("logs", nome)
                cripto.criptografar_arquivo(caminho)
                messagebox.showinfo("Sucesso", f"Arquivo criptografado: {nome}.enc")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criptografar: {e}")

    # ═══════════════════════════════════════════════════════════════
    #  ABA 3: E-MAIL
    # ═══════════════════════════════════════════════════════════════

    def _construir_aba_email(self):
        """Constrói a aba de configuração e envio de e-mail."""
        frame = self.tab_email

        # ─── Formulário de configuração ───────────────────────────
        frame_config = ctk.CTkFrame(frame, corner_radius=10)
        frame_config.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            frame_config, text="⚙ Configuração SMTP",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 5))

        # Linha 1: Servidor e Porta
        ctk.CTkLabel(frame_config, text="Servidor:").grid(
            row=1, column=0, sticky="e", padx=(10, 5), pady=3
        )
        self.entry_servidor = ctk.CTkEntry(frame_config, width=250)
        self.entry_servidor.grid(row=1, column=1, padx=5, pady=3)
        self.entry_servidor.insert(0, self.email_manager.config.get("servidor_smtp", ""))

        ctk.CTkLabel(frame_config, text="Porta:").grid(
            row=1, column=2, sticky="e", padx=(10, 5), pady=3
        )
        self.entry_porta = ctk.CTkEntry(frame_config, width=80)
        self.entry_porta.grid(row=1, column=3, padx=(5, 10), pady=3)
        self.entry_porta.insert(0, str(self.email_manager.config.get("porta", 587)))

        # Linha 2: E-mail remetente
        ctk.CTkLabel(frame_config, text="E-mail:").grid(
            row=2, column=0, sticky="e", padx=(10, 5), pady=3
        )
        self.entry_email = ctk.CTkEntry(frame_config, width=250)
        self.entry_email.grid(row=2, column=1, padx=5, pady=3)
        self.entry_email.insert(0, self.email_manager.config.get("email_remetente", ""))

        # Linha 2: Senha
        ctk.CTkLabel(frame_config, text="Senha:").grid(
            row=2, column=2, sticky="e", padx=(10, 5), pady=3
        )
        self.entry_senha = ctk.CTkEntry(frame_config, width=200, show="●")
        self.entry_senha.grid(row=2, column=3, padx=(5, 10), pady=3)

        # Linha 3: Destinatário e Intervalo
        ctk.CTkLabel(frame_config, text="Destinatário:").grid(
            row=3, column=0, sticky="e", padx=(10, 5), pady=3
        )
        self.entry_destinatario = ctk.CTkEntry(frame_config, width=250)
        self.entry_destinatario.grid(row=3, column=1, padx=5, pady=3)
        self.entry_destinatario.insert(
            0, self.email_manager.config.get("email_destinatario", "")
        )

        ctk.CTkLabel(frame_config, text="Intervalo (min):").grid(
            row=3, column=2, sticky="e", padx=(10, 5), pady=3
        )
        self.entry_intervalo = ctk.CTkEntry(frame_config, width=80)
        self.entry_intervalo.grid(row=3, column=3, padx=(5, 10), pady=(3, 10))
        self.entry_intervalo.insert(
            0, str(self.email_manager.config.get("intervalo_minutos", 60))
        )

        # ─── Botões de ação ───────────────────────────────────────
        frame_botoes_email = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botoes_email.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            frame_botoes_email, text="💾 Salvar Configuração",
            command=self._salvar_config_email, width=160,
        ).pack(side="left", padx=5)

        self.btn_autorizar = ctk.CTkButton(
            frame_botoes_email, text="✅ Autorizar Envio",
            command=self._autorizar_email,
            fg_color="#4CAF50", hover_color="#388E3C", width=150,
        )
        self.btn_autorizar.pack(side="left", padx=5)

        ctk.CTkButton(
            frame_botoes_email, text="📤 Enviar Agora",
            command=self._enviar_email_agora,
            fg_color="#2196F3", hover_color="#1976D2", width=130,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_botoes_email, text="⏱ Envio Automático",
            command=self._toggle_envio_automatico,
            fg_color="#FF9800", hover_color="#F57C00", width=150,
        ).pack(side="left", padx=5)

        # ─── Histórico de envios ──────────────────────────────────
        ctk.CTkLabel(
            frame, text="📜 Histórico de Envios:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 2))

        self.historico_email = ctk.CTkTextbox(
            frame, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
        )
        self.historico_email.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    def _salvar_config_email(self):
        """Salva a configuração de e-mail."""
        try:
            self.email_manager.configurar(
                servidor=self.entry_servidor.get().strip(),
                porta=int(self.entry_porta.get().strip()),
                remetente=self.entry_email.get().strip(),
                senha=self.entry_senha.get(),
                destinatario=self.entry_destinatario.get().strip(),
                intervalo=int(self.entry_intervalo.get().strip()),
            )
            messagebox.showinfo("Sucesso", "Configuração de e-mail salva!")
        except ValueError as e:
            messagebox.showerror("Erro", f"Configuração inválida: {e}")

    def _autorizar_email(self):
        """Autoriza o envio de e-mails após confirmação."""
        if not self.permissoes.verificar_permissao("envio_email"):
            resposta = messagebox.askyesno(
                "Autorização de Envio",
                "Você autoriza o envio de relatórios por e-mail?\n\n"
                "Os logs do laboratório serão enviados como anexos.\n"
                "Apenas dados digitados voluntariamente serão transmitidos.",
            )
            if not resposta:
                return
            self.permissoes.conceder_permissao("envio_email")

        self.email_manager.autorizar_envio()
        self.btn_autorizar.configure(
            text="✅ Autorizado", fg_color="#388E3C", state="disabled"
        )
        messagebox.showinfo("Autorizado", "Envio de e-mails autorizado!")

    def _enviar_email_agora(self):
        """Envia os logs por e-mail imediatamente (em thread separada)."""
        if not self.email_manager.autorizado:
            messagebox.showwarning("Aviso", "Autorize o envio primeiro!")
            return

        arquivos = [
            os.path.join("logs", f)
            for f in self.armazenamento.listar_sessoes()
        ]
        if not arquivos:
            messagebox.showinfo("Info", "Nenhum arquivo de log disponível.")
            return

        def _enviar():
            try:
                sucesso, msg = self.email_manager.enviar_relatorio(arquivos)
                self.after(0, lambda: self._atualizar_historico_email())
                if sucesso:
                    self.after(
                        0, lambda: messagebox.showinfo("Sucesso", msg)
                    )
                else:
                    self.after(0, lambda: messagebox.showerror("Erro", msg))
            except Exception as e:
                self.after(
                    0, lambda: messagebox.showerror("Erro", str(e))
                )

        thread = threading.Thread(target=_enviar, daemon=True)
        thread.start()

    def _toggle_envio_automatico(self):
        """Alterna o envio automático."""
        if self.email_manager._envio_automatico_ativo:
            self.email_manager.parar_envio_automatico()
            messagebox.showinfo("Info", "Envio automático desativado.")
        else:
            if not self.email_manager.autorizado:
                messagebox.showwarning("Aviso", "Autorize o envio primeiro!")
                return
            try:
                self.email_manager.iniciar_envio_automatico("logs")
                intervalo = self.email_manager.config.get("intervalo_minutos", 60)
                messagebox.showinfo(
                    "Info",
                    f"Envio automático ativado — intervalo: {intervalo} min",
                )
            except PermissionError as e:
                messagebox.showerror("Erro", str(e))

    def _atualizar_historico_email(self):
        """Atualiza a exibição do histórico de e-mails."""
        texto = self.email_manager.formatar_historico()
        self.historico_email.configure(state="normal")
        self.historico_email.delete("1.0", "end")
        self.historico_email.insert("1.0", texto)
        self.historico_email.configure(state="disabled")

    # ═══════════════════════════════════════════════════════════════
    #  ABA 4: SEGURANÇA
    # ═══════════════════════════════════════════════════════════════

    def _construir_aba_seguranca(self):
        """Constrói a aba de análise de segurança."""
        frame = self.tab_seguranca

        # ─── Botões de análise ────────────────────────────────────
        frame_controles = ctk.CTkFrame(frame, fg_color="transparent")
        frame_controles.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            frame_controles, text="🔍 Analisar Processo",
            command=self._analisar_processo, width=160,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_controles, text="📊 Indicadores de Segurança",
            command=self._exibir_indicadores, width=190,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_controles, text="🛡 Técnicas de Detecção",
            command=self._exibir_tecnicas_deteccao, width=180,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_controles, text="📋 Listar Processos",
            command=self._listar_processos, width=150,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame_controles, text="🔄 Comparativo",
            command=self._exibir_comparativo, width=130,
        ).pack(side="left", padx=5)

        # ─── Switch de modo background simulado ──────────────────
        frame_bg = ctk.CTkFrame(frame, fg_color="transparent")
        frame_bg.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(
            frame_bg, text="Modo Background (simulado):",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)

        self.switch_background = ctk.CTkSwitch(
            frame_bg, text="",
            command=self._toggle_background,
        )
        self.switch_background.pack(side="left", padx=5)

        self.label_background = ctk.CTkLabel(
            frame_bg, text="Desativado",
            font=ctk.CTkFont(size=12), text_color="gray",
        )
        self.label_background.pack(side="left", padx=5)

        # ─── Área de resultados ───────────────────────────────────
        ctk.CTkLabel(
            frame, text="Resultados da Análise:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.resultado_seguranca = ctk.CTkTextbox(
            frame, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
        )
        self.resultado_seguranca.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    def _exibir_no_painel_seguranca(self, texto: str):
        """Exibe texto no painel de resultados de segurança."""
        self.resultado_seguranca.configure(state="normal")
        self.resultado_seguranca.delete("1.0", "end")
        self.resultado_seguranca.insert("1.0", texto)
        self.resultado_seguranca.configure(state="disabled")

    def _analisar_processo(self):
        """Exibe informações do processo atual."""
        info = self.simulador.obter_info_processo()
        linhas = [
            "=" * 60,
            "  INFORMAÇÕES DO PROCESSO — KEYLOGGER-LAB",
            "=" * 60, "",
        ]
        for chave, valor in info.items():
            linhas.append(f"  {chave:<30} {valor}")
        linhas.extend(["", "=" * 60])
        self._exibir_no_painel_seguranca("\n".join(linhas))

    def _exibir_indicadores(self):
        """Exibe a análise de indicadores de segurança."""
        indicadores = self.simulador.analisar_indicadores_suspeitos()
        linhas = [
            "=" * 70,
            "  ANÁLISE DE INDICADORES DE SEGURANÇA",
            "=" * 70, "",
        ]
        for _nome, dados in indicadores.items():
            linhas.extend([
                f"  [{dados['status']}] {dados['descricao']}",
                f"    Valor    : {dados['valor']}",
                f"    Explicação: {dados['explicacao']}",
                "",
            ])
        linhas.append("=" * 70)
        self._exibir_no_painel_seguranca("\n".join(linhas))

    def _exibir_tecnicas_deteccao(self):
        """Exibe as técnicas de detecção de keyloggers."""
        tecnicas = self.simulador.obter_tecnicas_deteccao()
        linhas = [
            "=" * 70,
            "  TÉCNICAS DE DETECÇÃO DE KEYLOGGERS",
            "=" * 70, "",
        ]
        for i, t in enumerate(tecnicas, 1):
            linhas.extend([
                f"  [{i}] {t['tecnica']}",
                f"      {t['descricao']}",
                f"      Ferramentas: {t['ferramentas']}",
                f"      Detecção: {t['como_detectar']}",
                "",
            ])
        linhas.append("=" * 70)
        self._exibir_no_painel_seguranca("\n".join(linhas))

    def _listar_processos(self):
        """Lista processos do sistema."""
        texto = self.simulador.listar_processos_sistema()
        self._exibir_no_painel_seguranca(
            "LISTA DE PROCESSOS DO SISTEMA\n"
            "=" * 60 + "\n\n" + texto
        )

    def _exibir_comparativo(self):
        """Exibe comparativo entre processos visíveis e ocultos."""
        comp = self.simulador.obter_comparativo_visibilidade()
        linhas = [
            "=" * 70,
            "  COMPARATIVO: PROCESSOS VISÍVEIS vs. OCULTOS",
            "=" * 70, "",
        ]
        for _tipo, dados in comp.items():
            linhas.append(f"  {dados['titulo']}")
            linhas.append(f"  Exemplo: {dados['exemplo']}")
            for c in dados["caracteristicas"]:
                linhas.append(f"    {c}")
            linhas.append("")
        linhas.append("=" * 70)
        self._exibir_no_painel_seguranca("\n".join(linhas))

    def _toggle_background(self):
        """Alterna o modo background simulado."""
        ativo = self.switch_background.get()
        self.simulador.simular_modo_background(bool(ativo))
        if ativo:
            self.label_background.configure(
                text="ATIVADO (simulado — interface visível)",
                text_color="#FF9800",
            )
        else:
            self.label_background.configure(
                text="Desativado", text_color="gray",
            )

    # ═══════════════════════════════════════════════════════════════
    #  BARRA DE STATUS
    # ═══════════════════════════════════════════════════════════════

    def _criar_barra_status(self):
        """Cria a barra de status inferior."""
        status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        ctk.CTkLabel(
            status_bar, textvariable=self._status_text,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=15)

        ctk.CTkLabel(
            status_bar, textvariable=self._sessao_text,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=15)

        ctk.CTkLabel(
            status_bar, textvariable=self._contagem_text,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=15)

        ctk.CTkLabel(
            status_bar,
            text="Keylogger-Lab v1.0 — Uso Educacional",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        ).pack(side="right", padx=15)

    # ═══════════════════════════════════════════════════════════════
    #  UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    def _atualizar_status(self):
        """Atualiza os indicadores de status periodicamente."""
        status = self.motor_captura.status
        if status == "CAPTURANDO":
            self._status_text.set("● CAPTURANDO")
            self.status_indicator.configure(text_color="#F44336")
        else:
            self._status_text.set("● INATIVO")
            self.status_indicator.configure(text_color="#4CAF50")

        self._contagem_text.set(f"Teclas: {self.motor_captura.contagem_teclas}")
        self._timer_status = self.after(1000, self._atualizar_status)

    def _ao_fechar(self):
        """Procedimento de encerramento seguro."""
        if self.motor_captura.capturando:
            if messagebox.askyesno(
                "Encerrar",
                "A captura está ativa. Deseja interromper e sair?",
            ):
                self.motor_captura.parar_captura()
            else:
                return

        # Parar envio automático
        self.email_manager.parar_envio_automatico()

        # Cancelar timer de atualização
        if self._timer_status:
            self.after_cancel(self._timer_status)

        self.logger.info("Aplicação encerrada pelo usuário")
        self.destroy()

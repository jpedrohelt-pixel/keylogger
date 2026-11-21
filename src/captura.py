"""
Módulo de Captura — Keylogger-Lab
=================================

Implementa o motor de captura de eventos de teclado, operando
EXCLUSIVAMENTE dentro de um widget Tkinter designado.

Conceitos demonstrados:
    - Como eventos de teclado são interceptados (event binding)
    - Diferença entre keysym, keycode e char
    - Mapeamento de teclas especiais
    - Captura controlada vs. captura global (hooks de sistema)

SEGURANÇA: Este módulo NÃO utiliza hooks globais de teclado.
A captura ocorre apenas dentro do campo de entrada do laboratório,
vinculado explicitamente via o método vincular_widget().

Comparação educacional — como um keylogger real funciona:
    ┌────────────────────────────────────────────────────────────┐
    │  KEYLOGGER REAL (malicioso)          KEYLOGGER-LAB (este) │
    │  ─────────────────────────           ──────────────────── │
    │  Hook global (SetWindowsHookEx)      Bind em widget local │
    │  Captura TODO o sistema              Captura SÓ no campo  │
    │  Roda oculto em background           Interface visível     │
    │  Persiste na inicialização           Sem persistência      │
    │  Exfiltra dados pela rede            Envio autorizado      │
    └────────────────────────────────────────────────────────────┘
"""

import datetime
import logging
from typing import Callable, Optional


class MotorCaptura:
    """
    Motor de captura de teclas vinculado a um widget Tkinter específico.

    Opera exclusivamente dentro do widget-alvo, sem interceptar
    eventos fora da interface do laboratório.

    Attributes:
        TECLAS_ESPECIAIS (dict): Mapeamento de keysyms para representações legíveis.
    """

    # Mapeamento de teclas especiais para representação textual
    # Em Tkinter, 'keysym' identifica a tecla independente do layout do teclado
    TECLAS_ESPECIAIS = {
        "Return": "[ENTER]",
        "BackSpace": "[BACKSPACE]",
        "space": "[ESPAÇO]",
        "Tab": "[TAB]",
        "Shift_L": "[SHIFT_E]",
        "Shift_R": "[SHIFT_D]",
        "Control_L": "[CTRL_E]",
        "Control_R": "[CTRL_D]",
        "Alt_L": "[ALT_E]",
        "Alt_R": "[ALT_D]",
        "Caps_Lock": "[CAPS_LOCK]",
        "Escape": "[ESC]",
        "Delete": "[DELETE]",
        "Insert": "[INSERT]",
        "Home": "[HOME]",
        "End": "[END]",
        "Prior": "[PAGE_UP]",
        "Next": "[PAGE_DOWN]",
        "Up": "[SETA_CIMA]",
        "Down": "[SETA_BAIXO]",
        "Left": "[SETA_ESQ]",
        "Right": "[SETA_DIR]",
        "F1": "[F1]",
        "F2": "[F2]",
        "F3": "[F3]",
        "F4": "[F4]",
        "F5": "[F5]",
        "F6": "[F6]",
        "F7": "[F7]",
        "F8": "[F8]",
        "F9": "[F9]",
        "F10": "[F10]",
        "F11": "[F11]",
        "F12": "[F12]",
        "Num_Lock": "[NUM_LOCK]",
        "Scroll_Lock": "[SCROLL_LOCK]",
        "Print": "[PRINT_SCREEN]",
        "Pause": "[PAUSE]",
        "Menu": "[MENU]",
    }

    def __init__(self, armazenamento, callback_tecla: Optional[Callable] = None):
        """
        Inicializa o motor de captura.

        Args:
            armazenamento: Instância de GerenciadorArmazenamento para persistir eventos.
            callback_tecla: Função opcional chamada a cada tecla capturada.
                           Recebe (tecla_registrada: str, tipo: str) como argumentos.
                           Útil para atualizar a interface em tempo real.
        """
        self.armazenamento = armazenamento
        self.callback_tecla = callback_tecla
        self.capturando: bool = False
        self.widget_alvo = None
        self.sessao_id: Optional[str] = None
        self.contagem_teclas: int = 0
        self._bind_id: Optional[str] = None
        self.logger = logging.getLogger("captura")

    def vincular_widget(self, widget):
        """
        Vincula o motor de captura a um widget Tkinter.

        O evento <KeyPress> do widget será interceptado pelo motor.
        Isso é análogo ao conceito de hooking, mas limitado a um único widget.

        Em contraste, um keylogger real usaria:
        - Windows: SetWindowsHookEx(WH_KEYBOARD_LL, ...) para hook global
        - Linux: /dev/input/eventX ou Xlib.XRecord
        - macOS: CGEventTapCreate com kCGEventKeyDown

        Args:
            widget: Widget Tkinter (Entry, Text ou CTkTextbox) que receberá
                   os eventos de teclado.
        """
        # Remove binding anterior, se existir
        if self.widget_alvo and self._bind_id:
            try:
                self.widget_alvo.unbind("<KeyPress>", self._bind_id)
            except Exception:
                pass

        self.widget_alvo = widget
        self._bind_id = widget.bind("<KeyPress>", self._ao_pressionar_tecla, add="+")
        self.logger.info(f"Widget vinculado ao motor de captura: {type(widget).__name__}")

    def desvincular_widget(self):
        """Remove o binding de captura do widget atual."""
        if self.widget_alvo and self._bind_id:
            try:
                self.widget_alvo.unbind("<KeyPress>", self._bind_id)
            except Exception:
                pass
            self.logger.info("Widget desvinculado do motor de captura")
        self.widget_alvo = None
        self._bind_id = None

    def iniciar_captura(self) -> str:
        """
        Inicia uma nova sessão de captura.

        Cria uma nova sessão no sistema de armazenamento e começa
        a registrar os eventos de teclado do widget vinculado.

        Returns:
            str: Identificador da sessão iniciada.

        Raises:
            RuntimeError: Se a captura já estiver ativa ou nenhum widget vinculado.
        """
        if self.capturando:
            self.logger.warning("Tentativa de iniciar captura já ativa")
            raise RuntimeError("A captura já está em andamento")

        if not self.widget_alvo:
            self.logger.error("Nenhum widget vinculado para captura")
            raise RuntimeError("Nenhum widget vinculado. Use vincular_widget() primeiro.")

        self.capturando = True
        self.contagem_teclas = 0

        # Iniciar nova sessão de armazenamento
        self.sessao_id = self.armazenamento.iniciar_sessao()
        self.logger.info(f"Captura iniciada — Sessão: {self.sessao_id}")
        return self.sessao_id

    def parar_captura(self) -> Optional[str]:
        """
        Para a captura e finaliza a sessão atual.

        Returns:
            str ou None: Identificador da sessão finalizada.
        """
        if not self.capturando:
            self.logger.warning("Tentativa de parar captura já inativa")
            return None

        self.capturando = False
        self.armazenamento.finalizar_sessao()

        sessao = self.sessao_id
        self.logger.info(
            f"Captura interrompida — Sessão: {sessao}, "
            f"{self.contagem_teclas} teclas registradas"
        )
        self.sessao_id = None
        return sessao

    def _ao_pressionar_tecla(self, evento):
        """
        Callback executado a cada KeyPress no widget vinculado.

        Analisa o evento Tkinter e classifica a tecla:
        - Teclas especiais (Enter, Backspace, etc.) → mapeamento definido
        - Caracteres imprimíveis (a-z, 0-9, símbolos) → char literal
        - Teclas de sistema (Win, Fn, etc.) → keysym entre colchetes

        Conceitos de KeyEvent do Tkinter:
        - evento.keysym: Nome simbólico da tecla (ex: 'Return', 'a', 'space')
        - evento.char: Caractere Unicode gerado (vazio para teclas especiais)
        - evento.keycode: Código numérico dependente da plataforma
        - evento.state: Estado dos modificadores (Shift, Ctrl, Alt)

        Args:
            evento: Objeto tkinter.Event com informações da tecla pressionada.
        """
        if not self.capturando:
            return

        keysym = evento.keysym
        caractere = evento.char

        # Classificação da tecla
        if keysym in self.TECLAS_ESPECIAIS:
            # Tecla especial reconhecida
            tecla_registrada = self.TECLAS_ESPECIAIS[keysym]
            tipo = "especial"
        elif caractere and caractere.isprintable():
            # Caractere imprimível (letra, número, símbolo)
            tecla_registrada = caractere
            tipo = "caractere"
        else:
            # Tecla de sistema ou modificador não mapeado
            tecla_registrada = f"[{keysym}]"
            tipo = "sistema"

        # Registrar no sistema de armazenamento
        self.armazenamento.registrar_evento(tecla_registrada, tipo)
        self.contagem_teclas += 1

        # Notificar a interface (se callback configurado)
        if self.callback_tecla:
            try:
                self.callback_tecla(tecla_registrada, tipo)
            except Exception as e:
                self.logger.error(f"Erro no callback de tecla: {e}")

    @property
    def status(self) -> str:
        """Retorna o status textual do motor de captura."""
        if self.capturando:
            return "CAPTURANDO"
        return "INATIVO"

    @property
    def info(self) -> dict:
        """
        Retorna informações detalhadas sobre o estado do motor.

        Returns:
            dict: Dicionário com status, sessão, contagem e widget.
        """
        return {
            "status": self.status,
            "sessao_id": self.sessao_id,
            "contagem_teclas": self.contagem_teclas,
            "widget_vinculado": type(self.widget_alvo).__name__ if self.widget_alvo else None,
            "capturando": self.capturando,
        }

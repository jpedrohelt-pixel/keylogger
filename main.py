"""
Keylogger-Lab — Ponto de Entrada Principal
==========================================

Inicializa o sistema de logging, verifica dependências e executa
a interface gráfica do laboratório.

Uso:
    python main.py

Requisitos:
    pip install -r requirements.txt
"""

import sys
import os
import logging
import datetime


def configurar_logging():
    """
    Configura o sistema de logging da aplicação.

    Gera logs tanto no console quanto em arquivo, permitindo
    rastrear toda a atividade do laboratório para análise posterior.

    Formato do log:
        2024-01-15 10:30:00 [INFO   ] captura     : Captura iniciada — Sessão: sessao_001
    """
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)

    # Arquivo de log do sistema (não confundir com logs de captura)
    log_sistema = os.path.join(
        "logs",
        f"sistema_{datetime.datetime.now().strftime('%Y%m%d')}.log",
    )

    # Formato detalhado para arquivo
    formato_arquivo = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)-15s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Formato simplificado para console
    formato_console = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Handler para arquivo
    handler_arquivo = logging.FileHandler(log_sistema, encoding="utf-8")
    handler_arquivo.setLevel(logging.DEBUG)
    handler_arquivo.setFormatter(formato_arquivo)

    # Handler para console
    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setLevel(logging.INFO)
    handler_console.setFormatter(formato_console)

    # Configurar logger raiz
    logger_raiz = logging.getLogger()
    logger_raiz.setLevel(logging.DEBUG)
    logger_raiz.addHandler(handler_arquivo)
    logger_raiz.addHandler(handler_console)

    logging.info("=" * 60)
    logging.info("  KEYLOGGER-LAB — Laboratório Educacional de Cibersegurança")
    logging.info("=" * 60)
    logging.info(f"  Início: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"  Python: {sys.version}")
    logging.info(f"  Plataforma: {sys.platform}")
    logging.info(f"  Diretório: {os.getcwd()}")
    logging.info("=" * 60)


def verificar_dependencias():
    """
    Verifica se todas as dependências estão instaladas.

    Returns:
        bool: True se todas as dependências estão disponíveis.
    """
    dependencias = {
        "customtkinter": "CustomTkinter (interface gráfica)",
        "cryptography": "Cryptography (criptografia de logs)",
    }

    faltando = []
    for modulo, descricao in dependencias.items():
        try:
            __import__(modulo)
        except ImportError:
            faltando.append(f"  - {modulo}: {descricao}")

    if faltando:
        print("\n" + "=" * 50)
        print("  DEPENDÊNCIAS NÃO ENCONTRADAS")
        print("=" * 50)
        print("\n  Instale as dependências com:")
        print("    pip install -r requirements.txt\n")
        print("  Módulos faltando:")
        for m in faltando:
            print(m)
        print("\n" + "=" * 50)
        return False

    return True


def main():
    """Ponto de entrada principal da aplicação."""
    # Garantir que estamos no diretório correto
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    os.chdir(diretorio_script)

    # Verificar dependências
    if not verificar_dependencias():
        sys.exit(1)

    # Configurar logging
    configurar_logging()

    # Importar e iniciar a interface
    try:
        from src.interface import InterfaceLab

        logging.info("Iniciando interface gráfica...")
        app = InterfaceLab()
        app.mainloop()

    except Exception as e:
        logging.critical(f"Erro fatal ao iniciar a aplicação: {e}", exc_info=True)
        print(f"\nErro fatal: {e}")
        print("Verifique o arquivo de log para detalhes.")
        sys.exit(1)

    finally:
        logging.info("Aplicação encerrada")
        logging.info("=" * 60)


if __name__ == "__main__":
    main()

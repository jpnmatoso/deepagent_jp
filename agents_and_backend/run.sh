#!/bin/bash

# Script de inicialização para o Agent Backend LangGraph
# Executa o servidor com as configurações corretas de PYTHONPATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

cd "$SCRIPT_DIR"

# Configura PYTHONPATH para incluir os módulos locais
export PYTHONPATH="$SCRIPT_DIR/src:$SCRIPT_DIR/src/agent:$PYTHONPATH"

# Ativa o ambiente virtual se existir
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
fi

echo "Iniciando Agent Backend LangGraph..."
echo "PYTHONPATH: $PYTHONPATH"
echo ""

# Executa o servidor langgraph
langgraph dev --port 8101 --no-browser "$@"

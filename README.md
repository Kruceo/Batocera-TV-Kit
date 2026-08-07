# Batocera Firefox

Sistema para rodar o **Firefox** como aplicativo (kiosk/porta) dentro do **Batocera**, com navegação controlada por gamepad via mapeamento para teclado/mouse.

## Estrutura

```
.
├── install-firefox.sh              # Baixa e instala o Firefox oficial em /userdata
├── roms/firefox/                   # Entradas do EmulationStation (Firefox, Netflix, Youtube, Max)
│   ├── Firefox.sh / Netflix.sh / Youtube.sh / Max.sh
│   ├── gamelist.xml                # Metadados e imagens das entradas
│   └── images/                     # Capas (webp/jpg/png)
├── system/
│   ├── custom.sh                   # Inicia o controllerd.py na inicialização
│   ├── configs/emulationstation/es_systems_firefox.cfg   # Define o sistema "firefox" no ES
│   └── tools/
│       ├── controllerd.py          # Daemon que mapeia gamepad → teclado/mouse (uinput)
│       ├── find_controller.py      # Utilitário para localizar o device do controle
│       └── profiles/               # Perfis de mapeamento (disabled, youtube, max, netflix)
├── extension/                      # Extensão Firefox (Shift+Backspace = ESC no YouTube)
├── keyboard/                       # Teclado virtual em Go (SDL2 + uinput)
├── test.sh                         # Helper de teste (Playwright MCP via Docker)
└── web-controller-plan.md          # Plano de um futuro controlador web
```

## Instalação

1. **Instalar o Firefox** (no Batocera):
   ```bash
   ./install-firefox.sh
   ```

2. **Instalar os arquivos do sistema** copiando para os caminhos do Batocera:
   - `system/tools/` → `/userdata/system/tools/`
   - `system/custom.sh` → `/userdata/system/custom.sh`
   - `system/configs/emulationstation/es_systems_firefox.cfg` → `/userdata/system/configs/emulationstation/`
   - `roms/firefox/` → `/userdata/roms/firefox/`

## Controller (gamepad → teclado/mouse)

O `system/tools/controllerd.py` é um daemon que:
- Lê perfis de `profiles/*.cfg`.
- Aceita comandos via FIFO em `/run/controllerd.cmd` (`profile <name>`, `reload`, `list`, `status`, `stop`, `controller <path>`).
- Reconecta automaticamente se o controle for desconectado.
- Hotkey **PS + Start** fecha o Firefox (sai do kiosk).

Exemplos de uso do FIFO:
```bash
echo 'profile youtube' > /run/controllerd.cmd
echo 'status' > /run/controllerd.cmd
```

Para achar o caminho do controle:
```bash
python3 system/tools/find_controller.py --list
```

## Requisitos

- Python 3 com `evdev` (`pip install evdev`).
- Acesso a `/dev/input/*` e `/dev/uinput`.
- Firefox instalado via `install-firefox.sh`.

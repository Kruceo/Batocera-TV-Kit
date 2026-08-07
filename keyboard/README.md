# Virtual Keyboard

Aplicativo de teclado virtual desenvolvido em Go utilizando SDL2 para interface gráfica e uinput para simulação de eventos de teclado.

## Descrição

Este projeto cria um teclado virtual com interface gráfica que permite simular pressionamentos de teclas. É útil para sistemas embarcados, dispositivos com tela sensível ao toque ou como alternativa de acessibilidade.

## Tecnologias Utilizadas

- **Go 1.25** - Linguagem de programação
- **SDL2** - Biblioteca para interface gráfica e renderização
- **go-sdl2** - Bindings Go para SDL2
- **go-uinput** - Biblioteca para simulação de dispositivos de entrada Linux

## Estrutura do Projeto

```
.
├── Dockerfile              # Configuração para build com Docker
├── main.go                 # Código principal da aplicação
├── buttonWithText.go       # Componente de botão com texto
├── go.mod                  # Módulos Go
├── go.sum                  # Checksums dos módulos
├── keyboard                # Binário local (macOS)
├── keyboard-linux          # Binário Linux (ARM64)
└── keyboard-linux-amd64    # Binário Linux (AMD64)
```

## Como Buildar com Docker

O Dockerfile configura um ambiente completo para compilar a aplicação para Linux AMD64.

### Pré-requisitos

- Docker instalado e em execução
- Acesso à internet para download das dependências

### Passos para Build

1. **Clone ou acesse o diretório do projeto:**

```bash
cd /caminho/para/o/projeto
```

2. **Build da imagem Docker:**

```bash
docker build -t keyboard-builder .
```

Este comando:
- Usa a imagem base `golang:1.25-bookworm` (Linux AMD64)
- Instala as bibliotecas de desenvolvimento SDL2
- Baixa as dependências Go
- Compila o binário `keyboard-linux`

3. **Extrair o binário compilado:**

Após o build, você pode extrair o binário do container:

```bash
# Criar um container temporário
docker create --name temp-keyboard keyboard-builder

# Copiar o binário
docker cp temp-keyboard:/build/keyboard-linux ./keyboard-linux-amd64

# Remover o container temporário
docker rm temp-keyboard
```

### Build Multi-plataforma (Opcional)

Para buildar diretamente para outras arquiteturas:

```bash
# Build para Linux ARM64
docker buildx build --platform linux/arm64 -t keyboard-builder:arm64 .

# Build para Linux AMD64 (padrão)
docker buildx build --platform linux/amd64 -t keyboard-builder:amd64 .
```

## Como Executar

### No Linux (nativo ou Docker)

O aplicativo requer acesso ao dispositivo `uinput` para simular teclas:

```bash
# Executar com privilégios de root (necessário para uinput)
sudo ./keyboard-linux-amd64

# Ou com permissões específicas para o dispositivo uinput
sudo chmod 666 /dev/uinput
./keyboard-linux-amd64
```

### Usando Docker para Execução

```bash
# Executar o container com acesso aos dispositivos de entrada
docker run --rm -it \
  --privileged \
  -v /dev/uinput:/dev/uinput \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  keyboard-builder ./keyboard-linux
```

**Nota:** A execução com Docker requer:
- `--privileged` ou `--device /dev/uinput` para acesso ao dispositivo de entrada
- Montagem do socket X11 para exibição gráfica
- Variável `DISPLAY` configurada

## Variáveis de Ambiente

- `DISPLAY` - Define qual display X11 usar (padrão: `:0`)

## Requisitos de Runtime

### Bibliotecas SDL2

O sistema onde o binário será executado precisa ter as bibliotecas SDL2 instaladas:

```bash
# Debian/Ubuntu
sudo apt-get install libsdl2-2.0-0 libsdl2-ttf-2.0-0

# Fedora/RHEL
sudo dnf install SDL2 SDL2_ttf

# Arch Linux
sudo pacman -S sdl2 sdl2_ttf
```

### Permissões uinput

O usuário precisa de acesso ao dispositivo `/dev/uinput`:

```bash
# Adicionar usuário ao grupo input
sudo usermod -a -G input $USER

# Ou conceder permissões temporárias
sudo chmod 666 /dev/uinput
```

## Desenvolvimento Local

Para desenvolver sem Docker, instale as dependências SDL2 no seu sistema:

### macOS

```bash
brew install sdl2 sdl2_ttf sdl2_image sdl2_mixer sdl2_gfx
```

### Linux

```bash
sudo apt-get install libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-gfx-dev
```

### Compilar localmente

```bash
go build -o keyboard .
```

## Solução de Problemas

### Erro: "Could not load font"

O aplicativo tenta carregar fontes em ordem:
1. `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`
2. `/usr/share/fonts/TTF/DejaVuSans-Bold.ttf`
3. `/System/Library/Fonts/Helvetica.ttc` (macOS)

Instale o pacote de fontes DejaVu:

```bash
# Debian/Ubuntu
sudo apt-get install fonts-dejavu

# Fedora
sudo dnf install dejavu-sans-fonts
```

### Erro: "permission denied" no uinput

Execute com `sudo` ou configure permissões adequadas para `/dev/uinput`.

### Erro de display no Docker

Certifique-se de que:
1. O X11 está permitindo conexões: `xhost +local:docker`
2. A variável `DISPLAY` está correta
3. O socket `/tmp/.X11-unix` está montado

## Licença

Este projeto é de código aberto. Consulte o arquivo LICENSE para mais detalhes.

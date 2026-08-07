# Plan: web-controller — Simulador Web de Controle (Estilo PS4/PS5)

## Goal
Criar um pequeno servidor HTTP em uma nova pasta `web-controller/` que sirva um frontend minimalista representando um controle de videogame (estilo PlayStation) e execute ações reais no host via dispositivos de entrada virtuais (`uinput`/`evdev`) quando o usuário pressionar botões na página.

## Scope
### In Scope
- Nova pasta `web-controller/` na raiz do projeto.
- Backend HTTP simples (recomendado: Go, reaproveitando a experiência de `keyboard/` com `go-uinput`) que:
  - Sirva o frontend estático.
  - Exponha endpoints REST para pressionar/soltar botões e analógicos.
  - Emite eventos de teclado/mouse/joystick via `/dev/uinput` no host Linux.
- Frontend HTML/CSS/JS vanilla, extremamente simples, com layout visual de controle (botões △○×□, direcionais, L/R, analog sticks, start/select/PS).
- Suporte a toque/clique nos botões e possibilidade de mapear ações para teclas/mouse (ex: × = Enter, ○ = Esc, direcional = setas, R2 = PageDown, etc.).
- README com instruções de build/run e permissões de `uinput`.

### Out of Scope
- Integração direta com o daemon `controllerd.py` ou com o teclado SDL de `keyboard/` (podem coexistir, mas não serão acoplados nesta primeira versão).
- Suporte a múltiplos clientes simultâneos avançado (autenticação, sessões, filas).
- Reconhecimento nativo de controle físico como input — o input vem exclusivamente do navegador.
- Aplicação gráfica desktop (SDL, etc.); o frontend é web.
- Perfilagem avançada via arquivos de configuração (pode ser adicionado depois).

## Execution Phases

| Phase | Task | Owner Hint | Estimated Effort | Definition of Done |
|-------|------|------------|--------------------|--------------------|
| 1 | Estruturar `web-controller/` (main, static/, README, go.mod) | junior / backend | XS (1–2h) | Pasta criada, módulo Go inicializado, frontend estático servido em `/`. |
| 2 | Implementar backend HTTP: endpoints `/api/press`, `/api/release`, `/api/stick` e configuração de uinput | junior / backend | M (2–3 dias) | Server recebe JSON, cria/tecla virtual via `uinput`, testes manuais em Linux confirmam eventos reais. |
| 3 | Criar frontend vanilla: SVG/HTML do controle PlayStation, eventos touch/mouse, polling/throttling básico | junior / frontend | S (1–2 dias) | Página renderiza controle, cliques disparam chamadas HTTP, feedback visual ao pressionar. |
| 4 | Mapear botões para ações padrão (×=Enter, ○=Esc, △=F5, □=Tab, direcionais=setas, etc.) | junior / backend | XS (2–4h) | Tabela de mapeamento documentada e funcional; ações cobrem navegação web básica. |
| 5 | Testes no Batocera/Firefox target: permissões uinput, responsividade, latência | QA / dev | S (1 dia) | README contém troubleshooting; pelo menos 80% dos botões testados no hardware real. |
| 6 | README, build cruzado (Linux ARM64/AMD64) e instruções de execução | junior / docs | XS (2–4h) | README cobre build local, Docker opcional, permissões e exemplos de uso. |

## Key Decisions & Trade-offs
- **Linguagem do backend: Go** (recomendado). Justificativa: o projeto já tem `keyboard/` em Go usando `go-uinput`, então a curva de aprendizado e manutenção é menor; compilação estática facilita deploy no Batocera. Python/evdev é viável, mas adicionaria uma segunda stack.
- **Frontend vanilla**. Justificativa: atende ao requisito de “extremamente simples”, evita build de JS, e pode ser servido diretamente pelo binário Go via `embed` ou `http.FileServer`.
- **Input via uinput em vez de X11/wayland**. Justificativa: é o mesmo mecanismo usado por `keyboard/` e `controllerd.py`, funciona em ambientes embarcados/sem display X11 e não depende de janela focada.
- **HTTP em vez de WebSocket**. Justificativa: menor complexidade. Para latência baixa entre press/release, o frontend envia requisições rápidas de `press`/`release`; se necessário, WebSocket pode ser adicionado em fase futura.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Permissão negada em `/dev/uinput` | H | H | Documentar `sudo`, grupo `input`, ou `chmod 666 /dev/uinput`; considerar udev rule no README. |
| Latência perceptível entre toque e ação | M | M | Usar fetch simples, evitar logs síncronos excessivos; avaliar WebSocket se fetch não for suficiente. |
| Incompatibilidade de eventos uinput com o Batocera/Firefox | M | H | Validar códigos de tecla/mouse (evdev) usados em `controllerd.py` (ex: `KEY_ENTER`, `BTN_LEFT`, `REL_X`). |
| Conflito com teclado virtual ou controllerd rodando simultaneamente | M | M | Cada ferramenta abre seu próprio dispositivo uinput; documentar que podem coexistir, mas só uma deve emitir para a mesma ação por vez. |
| Frontend não responsivo em telas pequenas | M | L | Usar viewport e CSS flexível; botões grandes para toque. |

## Dependencies
- Internal: conhecimento dos códigos de tecla já utilizados em `keyboard/main.go` e `system/tools/controllerd.py`.
- External:
  - Go 1.25+ para build.
  - Biblioteca `go-uinput` (ou equivalente) para eventos de entrada.
  - Acesso a `/dev/uinput` no host Linux.
  - Navegador moderno no cliente (para fetch + touch events).

## Acceptance Criteria
- [ ] Servidor inicia e serve a página do controle em `http://<host>:porta/`.
- [ ] Pressionar um botão no navegador gera evento real visível via `evtest` ou `cat /dev/input/event*`, ou a ação é percebida pelo Firefox.
- [ ] Mapeamento mínimo funcional: ×=Enter, ○=Esc, direcional=setas, R2=PageDown, L2=PageUp, analógico direito=movimento do mouse (opcional).
- [ ] README explica como buildar e como resolver erros de permissão `uinput`.
- [ ] Build funciona tanto em AMD64 quanto em ARM64 Linux (via Docker ou cross-compile).

## Open Questions
1. Qual linguagem prefere para o backend — Go (recomendado, reaproveita `keyboard/`) ou Python (reaproveita `controllerd.py`)?
2. Há uma porta padrão que o servidor deve usar (ex: `8080`, `7777`) ou deve ser configurável por flag/variável de ambiente?
3. O analógico direito deve controlar o mouse (como no `controllerd.py`) ou apenas emitir teclas/setas?
4. O objetivo principal é controlar o Firefox dentro do Batocera, ou um uso mais genérico?

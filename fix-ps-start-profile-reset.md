# Plan: Corrigir perfil do controle preso após fechar app com PS+Start

## Goal
Garantir que o `controllerd.py` sempre volte ao perfil `disabled` quando o app Firefox fecha (via PS+Start, crash ou kill do launcher), eliminando o comportamento bugado do controle no EmulationStation.

## Contexto (causa raiz)
`_close_app()` executa `pkill -f firefox`, que casa a cmdline completa de **todos** os processos — incluindo os launchers (`bash /userdata/roms/firefox/Youtube.sh`, caminho contém "firefox"). O launcher morre antes do `wait $FF_PID` retornar, e o `echo "profile disabled" > /run/controllerd.cmd` final **nunca executa**. O perfil do app (bindings + mouse) continua ativo no ES.

## Scope
### In Scope
- `roms/firefox/{Firefox,Netflix,Youtube,max}.sh` — trap de cleanup + correção `profile nothing` → `profile disabled`
- `system/tools/controllerd.py` — estreitar `pkill` + self-heal para `disabled` em `_close_app()`

### Out of Scope
- `grab()` exclusivo do device (decisão: manter como está)
- Alterar perfis existentes (`*.cfg`)
- `Firefox.sh` carregar `profile max` na abertura (ver Open Questions)

## Execution Phases
| Phase | Task | Owner Hint | Effort | Definition of Done |
|-------|------|------------|--------|--------------------|
| 1 | **Trap de cleanup nos 4 launchers**: `trap 'echo "profile disabled" > /run/controllerd.cmd' EXIT` + `trap 'exit' TERM INT HUP` (sem o trap de TERM, o EXIT não roda em SIGTERM), remover echo duplicado final, trocar `profile nothing` → `profile disabled` | junior | XS (1–2h) | `kill -TERM` no launcher durante o app ainda envia `profile disabled` |
| 2 | **Estreitar o pkill** em `_close_app()`: `pkill -f '/userdata/system/.dev/apps/firefox/firefox'` (casa binário + filhos, não os launchers) | junior | XS (< 1h) | Após PS+Start: Firefox morto, launcher sobrevive e completa a execução |
| 3 | **Self-heal no daemon**: após o kill, `self._load_profile('disabled')` | junior/pleno | XS (1h) | Com launchers deliberadamente quebrados, PS+Start ainda reseta o daemon |
| 4 | **Validação no aparelho**: PS+Start em cada app; kill -TERM no launcher; kill -9 no Firefox; conferir `status` no FIFO e logs | QA/dev | S (½–1 dia) | Todos os cenários terminam com `Profile: disabled` |

## Key Decisions & Trade-offs
- **Camadas independentes**: trap (1), pkill preciso (2), self-heal (3) — qualquer uma resolve sozinha; juntas cobrem SIGKILL e launchers ausentes.
- **`trap 'exit' TERM` além do `EXIT`**: EXIT trap sozinho não executa em processo morto por SIGTERM não-trapado.
- **Self-heal mantém o daemon como dono final do estado**: uinput recriado no `_load_profile`, seguro pois `_release_all_keys()` já rodou.
- **Sem `grab()`**: decisão do usuário.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Padrão do pkill não casar a versão instalada (hotkey "não fecha") | M | H | Validar com `pgrep -f '<pattern>'`; fallback `pkill -x firefox` |
| `_load_profile` no event loop recriar uinput causa atraso | L | L | Já ocorre em trocas de perfil; medir na fase 4 |
| SIGKILL no launcher pula o trap | L | M | Coberto pelo self-heal (fase 3) |
| `.sh` instalados em `/userdata/roms` desatualizados | M | M | Reinstalar os 4 `.sh` no dispositivo no deploy |

## Dependencies
- Internal: apenas os arquivos citados.
- External: nenhuma (evdev/uinput já em uso).

## Acceptance Criteria
- [ ] PS+Start em qualquer dos 4 apps → `echo 'status' > /run/controllerd.cmd` mostra `Profile: disabled`, mouse e D-pad off
- [ ] Controle no ES se comporta como antes de abrir o app (sem teclas/mouse fantasma)
- [ ] `kill -TERM` manual no launcher durante o app → perfil reseta
- [ ] `kill -9` no Firefox (crash) → perfil reseta
- [ ] Nenhum processo Firefox remanescente após fechamento

## Open Questions
- `Firefox.sh` carrega `profile max` na abertura (parece copy-paste). Intencional? Se não, qual perfil correto?

# Architektura lib-unreal

`src/lib_unreal/client.py` udostępnia lokalny odczytowy adapter
JSON-RPC MCP dla Unreal Editor. Obsługuje `initialize`,
`notifications/initialized` i `tools/list` z JSON/SSE,
bez `tools/call`, narzędzi mutujących i serwera pośredniczącego.

**Granice:** literalne `127.0.0.1` lub `[::1]`, port wymagany,
HTTP bez proxy i redirectów. `localhost` nie jest akceptowany,
aby uniknąć zależności od DNS/hosts. Sesja `Mcp-Session-Id`
pozostaje w pamięci. Timeout 10 s, maksymalnie 60 s.

**Limity:** 1 MiB na odpowiedź, do 32 stron paginacji,
2048 narzędzi i 2 MiB łącznie. Serwer musi zaakceptować
wersję `2025-06-18`; niekompatybilne negocjowanie kończy się
wyjątkiem. Nie ma implementacji operacji write.

**Dowody:** syntetyczne testy JSON-RPC/SSE, timeoutów, odmowy
przekierowań i kontroli granic w izolowanym CI. Testy na
rzeczywistym Unreal Editor/Andromedzie **NOT_RUN**.
Architektura nie zapewnia uwierzytelnienia procesu nasłuchującego
ani bezpieczeństwa innych procesów lokalnych.

Szczegóły: [model zagrożeń](docs/security/threat-model.md),
[przepływ danych](docs/architecture/data-flow.md).

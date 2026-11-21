# Architektura lib-unreal

`src/lib_unreal/client.py` realizuje minimalny klient JSON-RPC 2.0 dla Streamable HTTP MCP. Działający edytor Unreal pozostaje właścicielem serwera MCP i narzędzi z Toolset Registry. Adapter nie uruchamia drugiego serwera, nie przechowuje poświadczeń ani nie wywołuje operacji mutujących.

Wejście: lokalny endpoint HTTP. Wyjście: opis serwera i lista narzędzi MCP (ewentualnie metanarzędzi wyszukiwania) w JSON. Obsługa: `initialize`, `notifications/initialized`, `tools/list`; sesja przez `Mcp-Session-Id`, ograniczone odpowiedzi JSON/SSE, paginacja.

Granice: tylko loopback, brak automatycznych przekierowań, timeout 10 s, limit odpowiedzi 1 MiB. Zmiana scen wymaga kolejnego, osobno testowanego adaptera write z kontrolą dozwolonego projektu i polityką Research Autopilot. Protokół zainicjowany według MCP 2025-06-18; zgodność z wersją serwera wymaga weryfikacji na urządzeniu.

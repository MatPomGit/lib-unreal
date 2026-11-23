# Przepływ danych MCP i granice zaufania

**Stan: klient read-only IMPLEMENTED, rzeczywiste Unreal E2E NOT_RUN.**

Przepływ: konsument Python → walidacja literalnego adresu loopback
`127.0.0.1` lub `[::1]` z jawnym portem → lokalny MCP HTTP →
`initialize` → `notifications/initialized` → paginowane `tools/list`
→ wynik JSON-RPC w pamięci konsumenta. Nie ma `tools/call`, zapisu
scen, eksportu projektów ani automatycznej transmisji do sieci.

Transport ma timeout domyślnie 10 s (maksymalnie 60 s), bez proxy
i przekierowań. Odpowiedź JSON/SSE jest ograniczona do 1 MiB.
Paginacja jest dodatkowo ograniczona do 32 stron, 2048 narzędzi
i 2 MiB łącznego rozmiaru odpowiedzi. Kursory nie mogą się powtarzać.
Wersja negocjowana musi być `2025-06-18`, inaczej połączenie
zostaje odrzucone przed powiadomieniem o inicjalizacji.

`Mcp-Session-Id` pozostaje w pamięci klienta i wraca w nagłówku
kolejnych żądań. Nie jest uwierzytelnieniem, a port loopback nie
izoluje klienta od innych procesów lokalnych. Zaufanie do procesu
Unreal MCP, nasłuchu i uprawnień systemowych jest poza kontrolą
biblioteki. Narzędzia odkryte przez MCP mogą zawierać prywatne
nazwy/ścieżki projektów. Konsument ma ograniczyć logi,
retencję i eksport; CI pracuje wyłącznie na syntetycznych
danych, bez faktycznego edytora.

[Model zagrożeń](../security/threat-model.md) ·
[Kontrakt](../contracts.md) · [Prywatność](../privacy.md)

# Model zagrożeń lib-unreal

**Zakres: ocena implementacji read-only na poziomie źródeł.** Test rzeczywistego
Unreal Editor MCP oraz izolacji hosta: **NOT_RUN**. Ta analiza nie
potwierdza bezpieczeństwa produkcyjnego serwera.

| Granica i aktywo | Scenariusz zagrożenia | Kontrola / ograniczenie |
| --- | --- | --- |
| Endpoint MCP | `localhost` może wskazać adres spoza loopback wskutek zmian DNS/hosts | Akceptowane wyłącznie literalne `127.0.0.1` lub `[::1]`, jawny port, HTTP bez loginu, query i fragmentu |
| Transport | Proxy lub redirect może wynieść dane poza lokalny host | `ProxyHandler({})`, odmowa przekierowań; wymagany przegląd konfiguracji serwera |
| Dostęp do lokalnego portu | Inne procesy na hoście mogą uruchomić niezabezpieczony serwer lub kontaktować się z nim | Sam loopback **nie zapewnia autoryzacji**. Należy zatwierdzić binarkę, port i uprawnienia użytkownika |
| MCP JSON-RPC | Odpowiedź o błędnym identyfikatorze, typie lub kodzie błędu | Walidacja `jsonrpc`, `id`, `error` i `result` |
| Sesja i SSE | Ujawnienie identyfikatora sesji lub odpowiedź na obce żądanie | Sesja w pamięci, dopasowanie JSON-RPC `id`, ograniczenie strumienia 1 MiB; nie logować `Mcp-Session-Id` |
| Paginacja `tools/list` | Nieskończone unikatowe kursory, wzrost pamięci i żądań | Maksymalnie 32 strony, 2048 pozycji, 2 MiB skumulowanych danych; odmowa powtórzonego kursora |
| Protokół | Serwer negocjuje nieobsługiwaną wersję | Odmowa wersji różnej od `2025-06-18`, bez wysyłania `notifications/initialized` |
| Dane edytora | Nazwy narzędzi i metadane projektu mogą ujawnić informacje | Brak automatycznego zapisu/egress; aplikacja konsumenta odpowiada za retencję i logowanie |

**Ryzyko rezydualne:** własność procesu nasłuchującego na porcie,
zabezpieczenia lokalnego serwera MCP, dostęp innych procesów na hoście,
zgodność Unreal 5.8+/5.9, mechanizmy sesji i testy sprzętowe nie są
zweryfikowane. `SECURITY.md` nadal ma `CONTACT_NOT_CONFIGURED`.
Wydanie, port forwarding, sieć LAN, produkcja i komendy mutujące są
poza zakresem PR; wymagają osobnych bramek.

[Przepływ danych](../architecture/data-flow.md) ·
[Bezpieczeństwo](../../SECURITY.md) · [Testy](../testing.md)

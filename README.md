# lib-unreal

Biblioteka Python do lokalnego wykrywania możliwości **Unreal Engine MCP**. Wersja rozwojowa: API eksperymentalne, brak wydania. Nie wymaga konta Claude ani dodatkowych usług.

## Zakres wersji rozwojowej

Klient łączy się wyłącznie z `http://127.0.0.1:<port>/mcp`, wykonuje `initialize`, wysyła `notifications/initialized` i odczytuje `tools/list` z obsługą paginacji. Nie wykonuje `tools/call`, nie modyfikuje scen ani zasobów. W Unreal 5.8+ `tools/list` może zwrócić wyłącznie narzędzia wyszukiwania; lista nie musi obejmować wszystkich operacji edytora.

## Instalacja i użycie

W środowisku Python 3.11+:

```bash
python -m pip install -e .
python -m lib_unreal --endpoint http://127.0.0.1:8000/mcp
python -m unittest discover -s tests -v
```

W Unreal włącz **Unreal MCP** i właściwe **Toolsets**; lokalny endpoint konfiguruje się w ustawieniach edytora. Domyślny adres to `http://127.0.0.1:8000/mcp`. Dalsze informacje: [dokumentacja Epic](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor).

## Bezpieczeństwo i status

Transport ogranicza się do loopback, blokuje przekierowania i ogranicza rozmiar odpowiedzi. MCP Unreal działa lokalnie bez uwierzytelnienia, dlatego nie należy wystawiać portu poza host. Testy sieciowe na rzeczywistym Unreal i operacje mutujące: **NOT_RUN**. [Kontrakt](contracts/api.json) · [Architektura](ARCHITECTURE.md) · [Licencja](LICENSE).

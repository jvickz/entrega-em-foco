"""Download the published 2024 Brazilian road-freight dataset from Mendeley Data."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
URL = "https://data.mendeley.com/public-api/zip/jn2dcs2m77/download/1"
EXPECTED = {
    "Dados Pedido Perfeito.xlsx",
    "Dados Viagem Perfeita.xlsx",
    "Dados problemas e causas .xlsx",
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "Entrega2024Portfolio/1.0"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()

    if payload[:2] != b"PK":
        raise RuntimeError("O arquivo recebido não é o ZIP público esperado.")

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        found: set[str] = set()
        for member in archive.infolist():
            name = Path(member.filename).name
            if name in EXPECTED:
                (RAW / name).write_bytes(archive.read(member))
                found.add(name)
                print(f"Baixado: {name}")
    missing = EXPECTED - found
    if missing:
        raise RuntimeError(f"Arquivos ausentes na fonte: {', '.join(sorted(missing))}")

    print("\nFonte: Data Set Perfect Trip, Mendeley Data, DOI 10.17632/jn2dcs2m77.1")
    print("Licença da fonte: CC BY 4.0. Preserve atribuição e citação.")


if __name__ == "__main__":
    main()

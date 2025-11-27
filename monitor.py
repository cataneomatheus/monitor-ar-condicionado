import os
import math
import requests
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup
from twilio.rest import Client

# ==========================
# CONFIGURAÇÕES GERAIS
# ==========================

BRANDS = ["Agratto", "Elgin", "TCL"]
QUERY_BASE = "ar condicionado 30000 btus"
RESULTADOS_MAX = 10

# se quiser limitar preço, coloca um valor aqui; se não quiser limite, deixa como None
PRECO_LIMITE = None  # ex: Decimal("6000") se quiser


# ==========================
# HELPERS COMUNS
# ==========================

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def parse_preco_br(texto: str) -> Decimal | None:
    """Converte 'R$ 4.399,90' em Decimal('4399.90')."""
    if not texto:
        return None
    import re

    # pega só dígitos, ponto e vírgula
    numeros = re.sub(r"[^\d,\.]", "", texto)
    if not numeros:
        return None

    # normalizar: remove pontos de milhar, troca vírgula por ponto
    numeros = numeros.replace(".", "").replace(",", ".")
    try:
        return Decimal(numeros)
    except InvalidOperation:
        return None


def get(url: str, params: dict | None = None) -> requests.Response:
    """Wrapper com headers e tratamento simples de erro."""
    resp = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    return resp


# ==========================
# MERCADO LIVRE (API OFICIAL)
# ==========================

def buscar_mercado_livre(brand: str) -> list[dict]:
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": f"{QUERY_BASE} {brand}",
        "limit": 30,
        "sort": "price_asc",
    }
    try:
        r = get(url, params=params).json()
    except Exception as e:
        print(f"[ML] Erro na requisição para {brand}: {e}")
        return []

    resultados = []
    for item in r.get("results", []):
        price = Decimal(str(item.get("price", 0)))
        title = item.get("title", "").strip()
        link = item.get("permalink")

        if not title or not link:
            continue

        if PRECO_LIMITE is not None and price > PRECO_LIMITE:
            continue

        resultados.append(
            {
                "fonte": "Mercado Livre",
                "brand": brand,
                "titulo": title,
                "preco": price,
                "link": link,
            }
        )

    return resultados


# ==========================
# BUSCAPÉ (SCRAPING)
# ==========================

def buscar_buscape(brand: str) -> list[dict]:
    """
    Scraping simples do Buscapé.
    OBS: os seletores podem mudar com o tempo; se quebrar, é só abrir o site
    no navegador, inspecionar o HTML e ajustar abaixo.
    """
    query = f"{QUERY_BASE} {brand}"
    url = "https://www.buscape.com.br/search"
    params = {"q": query}

    try:
        resp = get(url, params=params)
    except Exception as e:
        print(f"[Buscapé] Erro na requisição para {brand}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    # estes seletores podem precisar ser ajustados conforme o HTML atual
    # ideia geral: cada card de produto, com nome e preço
    cards = soup.select("[data-testid='product-card']") or soup.select("a[data-testid*='product-card']")
    if not cards:
        # fallback bem genérico – pode pegar coisas a mais
        cards = soup.select("a")

    for card in cards:
        texto = card.get_text(" ", strip=True)
        if not texto:
            continue

        # filtro bem grosseiro: precisa conter 'R$'
        if "R$" not in texto:
            continue

        # tenta achar um pedaço de texto que pareça preço
        # normalmente o primeiro 'R$' já serve
        partes = texto.split("R$")
        if len(partes) < 2:
            continue

        preco_str = "R$" + partes[1].split(" ")[0]
        preco = parse_preco_br(preco_str)
        if preco is None:
            continue

        if PRECO_LIMITE is not None and preco > PRECO_LIMITE:
            continue

        titulo = card.get("title") or texto[:120]
        href = card.get("href")
        if not href:
            continue

        if href.startswith("/"):
            link = "https://www.buscape.com.br" + href
        else:
            link = href

        resultados.append(
            {
                "fonte": "Buscapé",
                "brand": brand,
                "titulo": titulo.strip(),
                "preco": preco,
                "link": link,
            }
        )

    return resultados


# ==========================
# ZOOM (SCRAPING)
# ==========================

def buscar_zoom(brand: str) -> list[dict]:
    """
    Scraping simples do Zoom.
    Mesma lógica: se quebrar, ajusta os seletores conforme o HTML atual.
    """
    query = f"{QUERY_BASE} {brand}"
    # formato clássico de busca do Zoom
    url = "https://www.zoom.com.br/search"
    params = {"q": query}

    try:
        resp = get(url, params=params)
    except Exception as e:
        print(f"[Zoom] Erro na requisição para {brand}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    # Seletores que costumam representar cards de produto:
    cards = soup.select("div[data-testid='product-card']") or soup.select("a[data-testid*='product-card']")
    if not cards:
        cards = soup.select("a")

    for card in cards:
        texto = card.get_text(" ", strip=True)
        if "R$" not in texto:
            continue

        partes = texto.split("R$")
        if len(partes) < 2:
            continue

        preco_str = "R$" + partes[1].split(" ")[0]
        preco = parse_preco_br(preco_str)
        if preco is None:
            continue

        if PRECO_LIMITE is not None and preco > PRECO_LIMITE:
            continue

        titulo = card.get("title") or texto[:120]
        href = card.get("href")
        if not href:
            continue

        if href.startswith("/"):
            link = "https://www.zoom.com.br" + href
        else:
            link = href

        resultados.append(
            {
                "fonte": "Zoom",
                "brand": brand,
                "titulo": titulo.strip(),
                "preco": preco,
                "link": link,
            }
        )

    return resultados


# ==========================
# AGREGAÇÃO DOS RESULTADOS
# ==========================

def coletar_todas_ofertas() -> list[dict]:
    todas: list[dict] = []

    for brand in BRANDS:
        print(f"🔎 Buscando {brand} no Mercado Livre...")
        todas.extend(buscar_mercado_livre(brand))

        print(f"🔎 Buscando {brand} no Buscapé...")
        todas.extend(buscar_buscape(brand))

        print(f"🔎 Buscando {brand} no Zoom...")
        todas.extend(buscar_zoom(brand))

    # remover duplicados grosseiros por (titulo, preco, fonte)
    vistos: set[tuple] = set()
    unicos: list[dict] = []
    for o in todas:
        chave = (o["fonte"], o["titulo"], o["preco"])
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(o)

    # ordenar pelo menor preço
    unicos.sort(key=lambda x: x["preco"])
    return unicos[:RESULTADOS_MAX]


# ==========================
# WHATSAPP (TWILIO)
# ==========================

def enviar_whatsapp(mensagem: str) -> None:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    w_from = os.getenv("TWILIO_WHATSAPP_FROM")
    w_to = os.getenv("WHATSAPP_TO")

    if not all([sid, token, w_from, w_to]):
        print("⚠️ Variáveis de ambiente do Twilio não configuradas. Nada enviado.")
        return

    try:
        client = Client(sid, token)
        msg = client.messages.create(
            from_=w_from,
            to=w_to,
            body=mensagem,
        )
        print("✅ WhatsApp enviado. SID:", msg.sid)
    except Exception as e:
        print("❌ Erro ao enviar WhatsApp:", e)


# ==========================
# MAIN
# ==========================

def montar_mensagem(ofertas: list[dict]) -> str:
    if not ofertas:
        return "Nenhuma oferta encontrada dentro dos critérios configurados."

    linhas = ["🔥 Ofertas de ar-condicionado split 30.000 BTUs (Agratto / Elgin / TCL)"]
    for o in ofertas:
        linhas.append(
            f"\n💰 R$ {o['preco']:.2f} | {o['brand']} ({o['fonte']})\n"
            f"🛒 {o['titulo']}\n"
            f"🔗 {o['link']}"
        )
    return "\n".join(linhas)


def main():
    print("=== Iniciando monitoramento ===")
    ofertas = coletar_todas_ofertas()
    print(f"Total de ofertas coletadas (após filtro/uniques): {len(ofertas)}")

    if not ofertas:
        print("Nenhuma oferta encontrada.")
        return

    mensagem = montar_mensagem(ofertas)
    print("\n--- MENSAGEM GERADA ---")
    print(mensagem)
    print("------------------------\n")

    enviar_whatsapp(mensagem)


if __name__ == "__main__":
    main()

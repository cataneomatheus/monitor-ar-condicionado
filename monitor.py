import os
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from twilio.rest import Client

# ==========================
# CONFIG
# ==========================

QUERY = "ar condicionado 30000 btus"
RESULTADOS_MAX = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}


def parse_preco(text):
    """Converte texto tipo R$ 4.399,00 em Decimal"""
    if not text:
        return None

    import re
    text = text.strip()
    numeros = re.sub(r"[^\d,\.]", "", text)

    if "," in numeros:
        numeros = numeros.replace(".", "").replace(",", ".")
    try:
        return Decimal(numeros)
    except:
        return None


# ==========================
# BUSCAPÉ
# ==========================

def buscar_buscape():
    query_encoded = QUERY.replace(" ", "%20")

    url = (
        f"https://www.buscape.com.br/search"
        f"?q={query_encoded}"
        f"&hitsPerPage=30"
        f"&page=1"
        f"&sortBy=price_asc"
    )

    print("🔎 Buscando no Buscapé...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Erro Buscapé:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    cards = soup.select("[data-testid='product-card']")

    for card in cards:
        texto = card.get_text(" ", strip=True)
        if "R$" not in texto:
            continue

        preco_part = texto.split("R$")[1].split(" ")[0]
        preco = parse_preco("R$" + preco_part)
        if preco is None:
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
                "titulo": titulo,
                "preco": preco,
                "link": link,
            }
        )

    return resultados


# ==========================
# ZOOM
# ==========================

def buscar_zoom():
    query_encoded = QUERY.replace(" ", "+")
    url = f"https://www.zoom.com.br/search?q={query_encoded}&sort=price_asc"

    print("🔎 Buscando no Zoom...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Erro Zoom:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    cards = soup.select("[data-testid='product-card']")

    for card in cards:
        texto = card.get_text(" ", strip=True)
        if "R$" not in texto:
            continue

        preco_part = texto.split("R$")[1].split(" ")[0]
        preco = parse_preco("R$" + preco_part)
        if preco is None:
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
                "titulo": titulo,
                "preco": preco,
                "link": link,
            }
        )

    return resultados


# ==========================
# AMAZON
# ==========================

def buscar_amazon():
    query_encoded = QUERY.replace(" ", "+")
    url = f"https://www.amazon.com.br/s?k={query_encoded}"

    print("🔎 Buscando na Amazon...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Erro Amazon:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    cards = soup.select("div.s-result-item")

    for card in cards:
        titulo_tag = card.select_one("h2 a span")
        preco_tag = card.select_one(".a-price .a-offscreen")

        if not titulo_tag or not preco_tag:
            continue

        titulo = titulo_tag.get_text(strip=True)
        preco = parse_preco(preco_tag.get_text(strip=True))

        if preco is None:
            continue

        href = card.select_one("h2 a")
        if not href:
            continue

        link = "https://www.amazon.com.br" + href.get("href")

        resultados.append(
            {
                "fonte": "Amazon",
                "titulo": titulo,
                "preco": preco,
                "link": link,
            }
        )

    return resultados


# ==========================
# WHATSAPP (Twilio)
# ==========================

def enviar_whatsapp(msg):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    w_from = os.getenv("TWILIO_WHATSAPP_FROM")
    w_to = os.getenv("WHATSAPP_TO")

    if not all([sid, token, w_from, w_to]):
        print("⚠ Configuração do Twilio ausente.")
        return

    try:
        client = Client(sid, token)
        msg = client.messages.create(
            from_=w_from,
            to=w_to,
            body=msg
        )
        print("📲 WhatsApp enviado:", msg.sid)
    except Exception as e:
        print("❌ Erro ao enviar WhatsApp:", e)


# ==========================
# MAIN
# ==========================

def main():
    print("=== MONITOR INICIADO ===")

    ofertas = []

    ofertas.extend(buscar_buscape())
    ofertas.extend(buscar_zoom())
    ofertas.extend(buscar_amazon())

    if not ofertas:
        print("Nenhuma oferta encontrada.")
        return

    # ordenar pelo menor preço
    ofertas.sort(key=lambda x: x["preco"])
    ofertas = ofertas[:RESULTADOS_MAX]

    msg = "🔥 Ofertas encontradas 🔥\n\n"
    for o in ofertas:
        msg += (
            f"💰 R$ {o['preco']:.2f}\n"
            f"{o['titulo']}\n"
            f"🛒 {o['fonte']}\n"
            f"🔗 {o['link']}\n\n"
        )

    print(msg)
    enviar_whatsapp(msg)


if __name__ == "__main__":
    main()

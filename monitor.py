import os
import re
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from twilio.rest import Client

# ==========================
# CONFIG
# ==========================

BUSCAPE_URL = (
    "https://www.buscape.com.br/search?"
    "q=ar%20condicionado%2030000%20btus"
    "&hitsPerPage=30"
    "&page=1"
    "&sortBy=price_asc"
)

RESULTADOS_MAX = 5   # <<< TOP 5 MAIS BARATOS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}


# ==========================
# UTIL
# ==========================

def parse_preco(text: str) -> Decimal | None:
    """
    Converte textos tipo:
      'R$ 4.249,00'  -> Decimal('4249.00')
    """
    if not text:
        return None

    numeros = re.sub(r"[^\d,\.]", "", text)

    if not numeros:
        return None

    # remove pontos de milhar (4.249,00 -> 4249,00)
    numeros = numeros.replace(".", "")
    # troca vírgula decimal por ponto (4249,00 -> 4249.00)
    numeros = numeros.replace(",", ".")

    try:
        return Decimal(numeros)
    except:
        return None


# ==========================
# SCRAPER DO BUSCAPÉ
# ==========================

def buscar_buscape():
    print("🔎 Buscando no Buscapé...")
    resultados = []

    try:
        resp = requests.get(BUSCAPE_URL, headers=HEADERS, timeout=25)
        resp.raise_for_status()
    except Exception as e:
        print("❌ Erro ao buscar página do Buscapé:", e)
        return resultados

    soup = BeautifulSoup(resp.text, "html.parser")

    # cada card de produto
    cards = soup.select('[data-testid="product-card"]')
    print(f"📦 Cards encontrados: {len(cards)}")

    cards_com_preco = 0

    for card in cards:
        # 1) preço com seletor EXATO que você me passou
        preco_el = card.select_one('[data-testid="product-card::price"]')
        if not preco_el:
            continue

        preco_texto = preco_el.get_text(strip=True)
        preco = parse_preco(preco_texto)
        if preco is None:
            continue

        cards_com_preco += 1

        # 2) título
        nome_el = card.select_one('[data-testid="product-card::name"]')
        if nome_el:
            titulo = nome_el.get_text(strip=True)
        else:
            titulo = card.get_text(" ", strip=True)[:120]

        # 3) link do <a href>
        link_el = card.select_one("a[href]")
        if not link_el:
            continue

        href = link_el.get("href")
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

    print(f"💰 Cards com preço válido: {cards_com_preco}")
    print(f"✅ Ofertas montadas: {len(resultados)}")

    return resultados


# ==========================
# WHATSAPP (Twilio)
# ==========================

def enviar_whatsapp(msg: str):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    w_from = os.getenv("TWILIO_WHATSAPP_FROM")
    w_to = os.getenv("WHATSAPP_TO")

    if not all([sid, token, w_from, w_to]):
        print("⚠ Variáveis do Twilio não configuradas.")
        return

    try:
        client = Client(sid, token)
        message = client.messages.create(
            from_=w_from,
            to=w_to,
            body=msg
        )
        print("📲 WhatsApp enviado:", message.sid)
    except Exception as e:
        print("❌ Erro ao enviar WhatsApp:", e)


# ==========================
# MAIN
# ==========================

def main():
    print("=== MONITOR — BUSCAPÉ (TOP 5) ===")

    ofertas = buscar_buscape()

    if not ofertas:
        print("⚠ Nenhuma oferta encontrada.")
        return

    # pegar apenas os mais baratos
    ofertas.sort(key=lambda x: x["preco"])
    ofertas = ofertas[:RESULTADOS_MAX]

    msg = "🔥 *Top 5 Menores Preços — Buscapé* 🔥\n\n"

    for o in ofertas:
        titulo_curto = o["titulo"][:60]  # cortar título p/ caber no WhatsApp
        msg += (
            f"💰 *R$ {o['preco']:.2f}*\n"
            f"{titulo_curto}\n"
            f"{o['link']}\n\n"
        )

    print(msg)
    enviar_whatsapp(msg)


if __name__ == "__main__":
    main()

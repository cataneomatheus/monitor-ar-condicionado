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

BUSCAPE_URL = (
    "https://www.buscape.com.br/search?"
    "q=ar%20condicionado%2030000%20btus"
    "&hitsPerPage=30"
    "&page=1"
    "&sortBy=price_asc"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}


def parse_preco(text):
    """Converte 'R$ 4.399,00' em Decimal('4399.00')"""
    if not text:
        return None
    import re
    numeros = re.sub(r"[^\d,]", "", text)
    if not numeros:
        return None
    return Decimal(numeros) / 100


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
        print("❌ Erro Buscapé:", e)
        return resultados

    soup = BeautifulSoup(resp.text, "html.parser")

    # Primeiro, tente pegar estrutura com data-testid
    cards = soup.select("[data-testid='product-card']")

    # Se não achar nada, tentar estrutura antiga
    if not cards:
        cards = soup.select("a[data-testid*='product-card']")

    # Fallback ainda mais agressivo
    if not cards:
        cards = soup.find_all("a")

    print(f"📦 Cards encontrados: {len(cards)}")

    for card in cards:
        texto = card.get_text(" ", strip=True)

        # precisa ter preço
        if "R$" not in texto:
            continue

        # pegar o primeiro preço que aparecer
        preco_str = texto.split("R$")[1].split(" ")[0]
        preco = parse_preco("R$" + preco_str)
        if preco is None:
            continue

        # título
        titulo = card.get("title") or texto[:120]

        # link
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
# WHATSAPP
# ==========================

def enviar_whatsapp(msg):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    w_from = os.getenv("TWILIO_WHATSAPP_FROM")
    w_to = os.getenv("WHATSAPP_TO")

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
    print("=== MONITOR — BUSCAPÉ ===")

    ofertas = buscar_buscape()

    if not ofertas:
        print("⚠ Nenhuma oferta encontrada.")
        return

    ofertas.sort(key=lambda x: x["preco"])
    ofertas = ofertas[:RESULTADOS_MAX]

    msg = "🔥 *Ofertas Buscapé* 🔥\n\n"
    for o in ofertas:
        msg += (
            f"💰 *R$ {o['preco']:.2f}*\n"
            f"{o['titulo']}\n"
            f"🔗 {o['link']}\n\n"
        )

    print(msg)
    enviar_whatsapp(msg)


if __name__ == "__main__":
    main()

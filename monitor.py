import os
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from twilio.rest import Client

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
    if not text:
        return None
    import re
    numeros = re.sub(r"[^\d,]", "", text)
    if not numeros:
        return None
    return Decimal(numeros) / 100


# ==========================
# BUSCAPÉ
# ==========================

def buscar_buscape():
    print("🔎 Teste Buscapé...")
    return []  # temporariamente vazio


# ==========================
# ZOOM
# ==========================

def buscar_zoom():
    print("🔎 Teste Zoom...")
    return []  # temporariamente vazio


# ==========================
# AMAZON
# ==========================

def buscar_amazon():
    print("🔎 Teste Amazon...")
    return []  # temporariamente vazio


# ==========================
# WHATSAPP
# ==========================

def enviar_whatsapp(msg):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    w_from = os.getenv("TWILIO_WHATSAPP_FROM")
    w_to = os.getenv("WHATSAPP_TO")

    print("📨 Enviando WhatsApp...")

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
# MAIN LOGIC
# ==========================

def main():
    print("=== MONITOR INICIADO ===")

    ofertas = []

    ofertas.extend(buscar_buscape())
    ofertas.extend(buscar_zoom())
    ofertas.extend(buscar_amazon())

    # INCLUIR UMA OFERTA FAKE PARA TESTE
    ofertas.append({
        "fonte": "TESTE",
        "titulo": "Oferta Fake (Teste de Funcionamento)",
        "preco": Decimal("123.45"),
        "link": "https://exemplo.com"
    })

    ofertas.sort(key=lambda x: x["preco"])
    ofertas = ofertas[:RESULTADOS_MAX]

    msg = "🔥 TESTE DE OFERTAS 🔥\n\n"
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

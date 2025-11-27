import os
import json
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from twilio.rest import Client

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
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def buscar_buscape():
    print("🔎 Buscando no Buscapé...")

    try:
        resp = requests.get(BUSCAPE_URL, headers=HEADERS, timeout=25)
        resp.raise_for_status()
    except Exception as e:
        print("❌ Erro ao carregar página:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # pegar o JSON principal do Next.js
    script_tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not script_tag:
        print("❌ JSON principal não encontrado!")
        return []

    try:
        data = json.loads(script_tag.string)
    except Exception as e:
        print("❌ Erro ao ler JSON:", e)
        return []

    resultados = []

    try:
        # caminhos observados na estrutura oficial
        products = (
            data["props"]["pageProps"]["dehydratedState"]["queries"][0]
            ["state"]["data"]["products"]
        )
    except Exception as e:
        print("❌ Estrutura do JSON alterada:", e)
        return []

    for p in products:
        try:
            titulo = p["name"]
            preco = Decimal(p["price"] / 100)  # price vem em centavos
            link = "https://www.buscape.com.br" + p["link"]
        except:
            continue

        resultados.append(
            {
                "fonte": "Buscapé",
                "titulo": titulo,
                "preco": preco,
                "link": link,
            }
        )

    print(f"📦 Encontrados {len(resultados)} produtos via JSON do Buscapé")
    return resultados


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


def main():
    print("=== MONITOR — BUSCAPÉ (JSON MODE) ===")

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

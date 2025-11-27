import os
import requests
from twilio.rest import Client
from decimal import Decimal

BRANDS = ["Agratto", "Elgin", "TCL"]
QUERY_BASE = "ar condicionado 30000 btus"
PRECO_LIMITE = 4500   # você pode alterar aqui
RESULTADOS_MAX = 5

def enviar_whatsapp(msg):
    """Envia WhatsApp usando Twilio."""
    try:
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        message = client.messages.create(
            from_=os.getenv("TWILIO_WHATSAPP_FROM"),
            to=os.getenv("WHATSAPP_TO"),
            body=msg
        )
        print("Mensagem enviada:", message.sid)
    except Exception as e:
        print("Erro ao enviar WhatsApp:", e)


def buscar_mercado_livre(brand):
    """Busca produtos no Mercado Livre utilizando API oficial."""
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": f"{QUERY_BASE} {brand}",
        "limit": 30,
        "sort": "price_asc"    # já traz mais barato primeiro
    }

    results = []
    r = requests.get(url, params=params).json()

    for item in r.get("results", []):
        results.append({
            "title": item["title"],
            "price": Decimal(str(item["price"])),
            "id": item["id"],
            "permalink": item["permalink"],
            "brand": brand
        })

    return results


def monitorar():
    todas = []

    for brand in BRANDS:
        ofertas = buscar_mercado_livre(brand)

        for o in ofertas:
            if o["price"] <= PRECO_LIMITE:
                todas.append(o)

    todas.sort(key=lambda x: x["price"])
    return todas[:RESULTADOS_MAX]


def main():
    ofertas = monitorar()

    if not ofertas:
        print("Nenhuma oferta encontrada.")
        return

    msg = "🔥 *Ofertas de Ar Condicionado 30.000 BTUs* 🔥\n\n"
    for o in ofertas:
        msg += (
            f"*{o['title']}*\n"
            f"Marca: {o['brand']}\n"
            f"Preço: R$ {o['price']:.2f}\n"
            f"🔗 {o['permalink']}\n\n"
        )

    print(msg)
    enviar_whatsapp(msg)


if __name__ == "__main__":
    main()

def main():
    print("=== MONITOR — BUSCAPÉ (HTML) ===")

    ofertas = buscar_buscape()

    if not ofertas:
        print("⚠ Nenhuma oferta encontrada.")
        return

    # ordena pelo menor preço
    ofertas.sort(key=lambda x: x["preco"])

    # 🔥 limitar para evitar estourar 1600 caracteres
    ofertas = ofertas[:5]

    # montar mensagem compacta
    msg = "🔥 *Top 5 menores preços — Buscapé* 🔥\n\n"
    for o in ofertas:
        titulo_curto = o["titulo"][:60]  # corta para evitar texto demais
        msg += (
            f"💰 *R$ {o['preco']:.2f}*\n"
            f"{titulo_curto}\n"
            f"{o['link']}\n\n"
        )

    print(msg)
    enviar_whatsapp(msg)

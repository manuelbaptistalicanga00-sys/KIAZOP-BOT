"""Testa o bot no terminal, sem WhatsApp nem Meta. Precisa só de ANTHROPIC_API_KEY.
Uso: $env:ANTHROPIC_API_KEY="..." ; python simular.py"""
import os
for k in ("WA_TOKEN", "WA_PHONE_ID", "VERIFY_TOKEN"):
    os.environ.setdefault(k, "teste")
os.environ.setdefault("DB_PATH", "simulacao.db")
import bot
bot.enviar = lambda phone, texto, *args: print(f"\n  BOT -> {texto}\n") or "terminal-synthetic"
print("Simulador (escreva 'sair' para terminar). Configure o perfil no painel; produção exige perfil guardado e válido.")
while True:
    msg = input("Cliente: ").strip()
    if msg.lower() == "sair":
        break
    if msg:
        bot.responder("simulacao", msg)

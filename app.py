from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

# Senhas aceitas para desativar o lockdown (comparadas sem espaços, barras ou maiúsculas)
SENHAS_VALIDAS = {"TEC-047", "TEC047", "09121988"}

# Endereço da fábrica revelado nas pistas. TROQUE pelo endereço da sua lore.
ENDERECO_FABRICA = "Av. das Fábricas, 1300, Distrito Industrial"

# Estado do terminal: None | "desbloqueado" | "redefinido"
# Um botão usado trava o outro, até o mestre reiniciar.
estado = {"modo": None}


def normalizar(texto: str) -> str:
    return texto.strip().upper().replace(" ", "").replace("/", "")


@app.get("/")
def terminal():
    return render_template("terminal.html", modo=estado["modo"], endereco=ENDERECO_FABRICA)


# Painel interno do Lucker (explorador de arquivos). O mestre abre quando
# os jogadores apertarem o botão nas costas dele.
@app.get("/lucker")
def lucker():
    return render_template("lucker.html", endereco=ENDERECO_FABRICA)


@app.post("/api/desbloquear")
def desbloquear():
    if estado["modo"] is not None:
        return jsonify(ok=False, erro="Terminal já utilizado."), 409
    senha = normalizar((request.get_json(silent=True) or {}).get("senha", ""))
    if senha not in SENHAS_VALIDAS:
        return jsonify(ok=False, erro="Credencial incorreta."), 401
    estado["modo"] = "desbloqueado"
    return jsonify(ok=True)


@app.post("/api/redefinir")
def redefinir():
    if estado["modo"] is not None:
        return jsonify(ok=False, erro="Terminal já utilizado."), 409
    estado["modo"] = "redefinido"
    return jsonify(ok=True)


# Rota do mestre: volta o terminal ao estado inicial para outra mesa/teste
@app.get("/mestre/reiniciar")
def reiniciar():
    estado["modo"] = None
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

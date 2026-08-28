from flask import Flask, render_template_string, request
import os
import shutil
import subprocess

app = Flask(__name__)

MODEL = "ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0"

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Alex Vision Lab</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
            text-align: center;
            padding: 25px 15px;
        }

        .caixa {
            max-width: 850px;
            margin: auto;
            background: #1f2937;
            padding: 25px;
            border-radius: 20px;
        }

        h1 {
            font-size: 30px;
        }

        .painel {
            margin-top: 20px;
            padding: 20px;
            border-radius: 15px;
            background: #111827;
            border: 1px solid #374151;
            text-align: left;
        }

        .status {
            padding: 15px;
            border-radius: 10px;
            margin-top: 12px;
        }

        .verde {
            background: #065f46;
        }

        .amarelo {
            background: #78350f;
        }

        .vermelho {
            background: #7f1d1d;
        }

        .azul {
            background: #1e3a8a;
        }

        button {
            width: 100%;
            padding: 16px;
            margin-top: 15px;
            border: none;
            border-radius: 12px;
            background: #2563eb;
            color: white;
            font-size: 17px;
            font-weight: bold;
        }

        pre {
            white-space: pre-wrap;
            word-break: break-word;
            background: #030712;
            padding: 15px;
            border-radius: 10px;
            overflow-x: auto;
        }

        code {
            word-break: break-word;
        }
    </style>
</head>

<body>

<div class="caixa">

    <h1>🧪 Alex Vision Lab</h1>

    <p>
        Primeiro teste controlado de carregamento do SmolVLM
    </p>

    <div class="painel">

        <h2>🔬 Runtime</h2>

        {% if llama %}
            <div class="status verde">
                🟢 llama.cpp encontrado!
                <br><br>
                <code>{{ llama }}</code>
            </div>
        {% else %}
            <div class="status vermelho">
                🔴 llama.cpp não encontrado.
            </div>
        {% endif %}

        {% if mtmd %}
            <div class="status verde">
                🟢 llama-mtmd-cli encontrado!
                <br><br>
                <code>{{ mtmd }}</code>
            </div>
        {% else %}
            <div class="status amarelo">
                🟡 llama-mtmd-cli não encontrado.
            </div>
        {% endif %}

        {% if server %}
            <div class="status verde">
                🟢 llama-server encontrado!
                <br><br>
                <code>{{ server }}</code>
            </div>
        {% else %}
            <div class="status amarelo">
                🟡 llama-server não encontrado.
            </div>
        {% endif %}

    </div>

    <div class="painel">

        <h2>🧠 SmolVLM-256M</h2>

        <div class="status azul">

            Modelo:

            <br><br>

            <code>{{ model }}</code>

        </div>

        <p>
            O modelo será carregado somente quando você
            apertar o botão abaixo.
        </p>

        <form method="POST">

            <button type="submit">
                🧠 Carregar SmolVLM
            </button>

        </form>

    </div>

    {% if resultado %}

    <div class="painel">

        <h2>🧪 Resultado</h2>

        {% if sucesso %}

            <div class="status verde">
                🟢 O processo terminou com sucesso.
            </div>

        {% else %}

            <div class="status vermelho">
                🔴 O processo terminou com erro.
            </div>

        {% endif %}

        <pre>{{ resultado }}</pre>

    </div>

    {% endif %}

    <div class="painel">

        <h2>🎯 Objetivo desta etapa</h2>

        <div class="status azul">

            1️⃣ Confirmar llama.cpp<br>
            2️⃣ Baixar/carregar SmolVLM<br>
            3️⃣ Mostrar o resultado<br>
            4️⃣ Depois testar imagens

        </div>

    </div>

</div>

</body>
</html>
"""


def procurar(nome):

    caminho = shutil.which(nome)

    if caminho:
        return caminho

    caminhos = [
        f"./bin/{nome}",
        f"./{nome}",
        f"./llama.cpp/{nome}",
        f"./llama.cpp/build/bin/{nome}"
    ]

    for caminho in caminhos:

        if os.path.isfile(caminho):
            return caminho

    return None


def executar_teste(caminho):

    if not caminho:
        return (
            False,
            "❌ llama-cli não foi encontrado."
        )

    comando = [
        caminho,
        "-hf",
        MODEL,
        "-p",
        "Olá Alex. Responda apenas: modelo carregado.",
        "-n",
        "16"
    ]

    try:

        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=300
        )

        saida = resultado.stdout or ""
        erro = resultado.stderr or ""

        texto = ""

        if saida.strip():
            texto += saida

        if erro.strip():

            if texto:
                texto += "\n\n"

            texto += "=== STDERR ===\n"
            texto += erro

        if resultado.returncode == 0:

            return (
                True,
                texto[-15000:]
            )

        return (
            False,
            "Código de saída: "
            + str(resultado.returncode)
            + "\n\n"
            + texto[-15000:]
        )

    except subprocess.TimeoutExpired:

        return (
            False,
            "⏱️ O teste ultrapassou 5 minutos."
        )

    except Exception as e:

        return (
            False,
            "❌ Erro ao executar o teste:\n"
            + str(e)
        )


@app.route("/", methods=["GET", "POST"])
def inicio():

    llama = procurar("llama-cli")

    if not llama:
        llama = procurar("llama")

    mtmd = procurar("llama-mtmd-cli")

    server = procurar("llama-server")

    resultado = None
    sucesso = False

    if request.method == "POST":

        sucesso, resultado = executar_teste(
            llama
        )

    return render_template_string(
        HTML,
        llama=llama,
        mtmd=mtmd,
        server=server,
        model=MODEL,
        resultado=resultado,
        sucesso=sucesso
    )


if __name__ == "__main__":

    porta = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=porta
    )

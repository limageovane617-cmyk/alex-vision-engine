from flask import Flask, render_template_string
import os
import shutil
import subprocess

app = Flask(__name__)


HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Alex Vision Lab</title>

    <style>

        body {
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
            text-align: center;
            padding: 30px 15px;
        }

        .caixa {
            max-width: 800px;
            margin: auto;
            background: #1f2937;
            padding: 25px;
            border-radius: 20px;
        }

        h1 {
            font-size: 30px;
        }

        p {
            color: #d1d5db;
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
            padding: 14px;
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

        code {
            word-break: break-word;
        }

        pre {
            white-space: pre-wrap;
            word-break: break-word;
        }

    </style>

</head>

<body>

<div class="caixa">

    <h1>🧪 Alex Vision Lab</h1>

    <p>
        Teste controlado do suporte multimodal
        do llama.cpp
    </p>


    <div class="painel">

        <h2>🔬 Runtime</h2>

        <div class="status azul">
            ⚙️ Runtime:
            <strong>llama.cpp</strong>
        </div>

        <div class="status azul">
            🧠 Modelo reservado:
            <strong>SmolVLM-256M-Instruct-GGUF</strong>
        </div>

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

    </div>


    <div class="painel">

        <h2>👁️ Suporte Multimodal</h2>

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

        <h2>🧪 Diagnóstico dos Executáveis</h2>

        <div class="status azul">

            <pre>{{ diagnostico }}</pre>

        </div>

    </div>


    <div class="painel">

        <h2>📦 SmolVLM</h2>

        <div class="status amarelo">

            ⏸️ O SmolVLM ainda NÃO será baixado.

            <br><br>

            Primeiro vamos confirmar que o
            suporte multimodal está disponível.

        </div>

    </div>


    <div class="painel">

        <h2>🎯 Próxima etapa</h2>

        <div class="status azul">

            1️⃣ Confirmar llama.cpp<br>
            2️⃣ Confirmar llama-mtmd-cli<br>
            3️⃣ Confirmar llama-server<br>
            4️⃣ Depois carregar o SmolVLM

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


def executar_version(caminho):

    if not caminho:
        return "Não encontrado."

    comandos = [

        [caminho, "--version"],
        [caminho, "-h"]

    ]

    for comando in comandos:

        try:

            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=10
            )

            saida = (
                resultado.stdout
                or resultado.stderr
                or ""
            )

            if saida.strip():

                return saida.strip()[:3000]

        except Exception:
            pass

    return "Executável encontrado, mas não foi possível obter a versão."


def diagnosticar():

    nomes = [

        "llama",
        "llama-cli",
        "llama-mtmd-cli",
        "llama-server"

    ]

    linhas = []

    linhas.append(
        "🧪 DIAGNÓSTICO MULTIMODAL"
    )

    linhas.append(
        "================================"
    )

    for nome in nomes:

        caminho = procurar(nome)

        if caminho:

            linhas.append(
                f"🟢 {nome}: {caminho}"
            )

            linhas.append(
                executar_version(caminho)
            )

        else:

            linhas.append(
                f"🟡 {nome}: não encontrado"
            )

    linhas.append(
        "================================"
    )

    linhas.append(
        "📦 SmolVLM não foi baixado."
    )

    return "\n".join(linhas)


@app.route("/")
def inicio():

    llama = procurar("llama")

    if not llama:
        llama = procurar("llama-cli")

    mtmd = procurar("llama-mtmd-cli")

    server = procurar("llama-server")

    return render_template_string(

        HTML,

        llama=llama,

        mtmd=mtmd,

        server=server,

        diagnostico=diagnosticar()

    )


@app.route("/diagnostico")
def rota_diagnostico():

    return (
        "<h1>🧪 Alex Vision Lab</h1>"
        "<pre>"
        + diagnosticar()
        + "</pre>"
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

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
            max-width: 700px;
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
        Laboratório isolado para teste do llama.cpp
        e do SmolVLM-256M
    </p>

    <div class="painel">

        <h2>🔬 Diagnóstico</h2>

        <div class="status verde">
            🟢 Laboratório iniciado
        </div>

        <div class="status azul">
            🧠 Modelo planejado:
            <strong>SmolVLM-256M-Instruct-GGUF</strong>
        </div>

        <div class="status azul">
            ⚙️ Runtime planejado:
            <strong>llama.cpp</strong>
        </div>

        {% if llama_caminho %}

            <div class="status verde">

                🟢 llama.cpp encontrado!

                <br><br>

                Caminho:

                <br>

                <code>{{ llama_caminho }}</code>

            </div>

        {% else %}

            <div class="status amarelo">

                🟡 llama.cpp ainda não está instalado
                neste ambiente.

            </div>

        {% endif %}

    </div>


    <div class="painel">

        <h2>🧪 Resultado do Teste</h2>

        {% if resultado %}

            <div class="status azul">

                <pre>{{ resultado }}</pre>

            </div>

        {% else %}

            <p>
                Nenhum teste executado ainda.
            </p>

        {% endif %}

    </div>


    <div class="painel">

        <h2>📦 Modelo</h2>

        <p>
            O modelo ainda NÃO será baixado nesta etapa.
        </p>

        <div class="status amarelo">

            ⚠️ Primeiro vamos confirmar se o
            runtime llama.cpp existe.

        </div>

    </div>

</div>

</body>

</html>
"""


def encontrar_llama():

    nomes = [
        "llama",
        "llama-cli",
        "llama-server",
        "llama-mtmd-cli"
    ]

    for nome in nomes:

        caminho = shutil.which(nome)

        if caminho:

            return caminho

    caminhos_locais = [

        "./llama",

        "./llama-cli",

        "./llama-server",

        "./llama-mtmd-cli",

        "./bin/llama",

        "./bin/llama-cli",

        "./bin/llama-server",

        "./bin/llama-mtmd-cli"

    ]

    for caminho in caminhos_locais:

        if os.path.isfile(caminho):

            return caminho

    return None


def testar_llama(caminho):

    if not caminho:

        return (
            "🟡 TESTE CONCLUÍDO\\n\\n"
            "llama.cpp não foi encontrado.\\n\\n"
            "Isso é esperado nesta primeira etapa."
        )

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

                return (
                    "🟢 llama.cpp respondeu!\\n\\n"
                    + saida[:4000]
                )

        except Exception as erro:

            ultimo_erro = str(erro)

    return (
        "🟡 O executável foi encontrado, "
        "mas não respondeu ao diagnóstico."
    )


@app.route("/")
def inicio():

    caminho = encontrar_llama()

    resultado = testar_llama(caminho)

    return render_template_string(
        HTML,
        llama_caminho=caminho,
        resultado=resultado
    )


@app.route("/diagnostico")
def diagnostico():

    caminho = encontrar_llama()

    if not caminho:

        return (
            "<h1>🟡 llama.cpp não encontrado</h1>"
            "<p>O ambiente ainda não possui "
            "o runtime instalado.</p>"
        )

    try:

        resultado = subprocess.run(
            [caminho, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        saida = (
            resultado.stdout
            or resultado.stderr
            or "Sem saída."
        )

        return (
            "<h1>🟢 llama.cpp encontrado</h1>"
            f"<p>Caminho: <code>{caminho}</code></p>"
            f"<pre>{saida}</pre>"
        )

    except Exception as erro:

        return (
            "<h1>🟡 Executável encontrado</h1>"
            f"<p>Erro ao executar: {erro}</p>"
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

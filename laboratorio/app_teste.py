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
            max-width: 720px;
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
        Teste controlado do runtime llama.cpp
    </p>

    <div class="painel">

        <h2>🔬 Diagnóstico</h2>

        <div class="status verde">
            🟢 Laboratório iniciado
        </div>

        <div class="status azul">
            ⚙️ Runtime:
            <strong>llama.cpp</strong>
        </div>

        <div class="status azul">
            🧠 Modelo reservado:
            <strong>SmolVLM-256M-Instruct-GGUF</strong>
        </div>

        {% if llama_caminho %}

            <div class="status verde">

                🟢 Executável encontrado!

                <br><br>

                Caminho:

                <br>

                <code>{{ llama_caminho }}</code>

            </div>

        {% else %}

            <div class="status amarelo">

                🟡 llama.cpp ainda não está instalado.

                <br><br>

                Nesta etapa isso é esperado.

            </div>

        {% endif %}

    </div>


    <div class="painel">

        <h2>🧪 Teste do Runtime</h2>

        <div class="status azul">

            <pre>{{ resultado }}</pre>

        </div>

    </div>


    <div class="painel">

        <h2>📦 SmolVLM</h2>

        <div class="status amarelo">

            ⏸️ Modelo ainda não será baixado.

            <br><br>

            Primeiro precisamos provar que
            o runtime funciona.

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
        "./bin/llama-mtmd-cli",

        "./llama.cpp/llama-cli",
        "./llama.cpp/llama-server",

        "./llama.cpp/build/bin/llama-cli",
        "./llama.cpp/build/bin/llama-server",
        "./llama.cpp/build/bin/llama-mtmd-cli"

    ]

    for caminho in caminhos_locais:

        if os.path.isfile(caminho):

            return caminho

    return None


def testar_runtime(caminho):

    if not caminho:

        return (
            "🟡 TESTE DO RUNTIME\\n\\n"
            "llama.cpp não foi encontrado.\\n\\n"
            "Resultado: o ambiente ainda não possui "
            "o executável.\\n\\n"
            "Nenhum modelo foi baixado."
        )

    comandos = [

        [caminho, "--version"],

        [caminho, "-h"]

    ]

    ultimo_erro = ""

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
                    "🟢 TESTE DO RUNTIME APROVADO!\\n\\n"
                    "llama.cpp respondeu corretamente.\\n\\n"
                    + saida[:4000]
                )

        except Exception as erro:

            ultimo_erro = str(erro)

    return (
        "🟡 EXECUTÁVEL ENCONTRADO\\n\\n"
        "O arquivo existe, mas o diagnóstico "
        "não conseguiu obter uma resposta.\\n\\n"
        f"Erro: {ultimo_erro}"
    )


@app.route("/")
def inicio():

    caminho = encontrar_llama()

    resultado = testar_runtime(caminho)

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
            "<p>O runtime ainda não está instalado.</p>"
            "<p>Nenhum modelo foi baixado.</p>"
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

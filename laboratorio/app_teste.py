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
            max-width: 760px;
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
        Diagnóstico controlado do ambiente para
        instalação do llama.cpp
    </p>


    <div class="painel">

        <h2>🔬 Runtime</h2>

        <div class="status azul">
            ⚙️ Runtime planejado:
            <strong>llama.cpp</strong>
        </div>

        <div class="status azul">
            🧠 Modelo reservado:
            <strong>SmolVLM-256M-Instruct-GGUF</strong>
        </div>

        {% if llama_caminho %}

            <div class="status verde">

                🟢 llama.cpp encontrado!

                <br><br>

                <code>{{ llama_caminho }}</code>

            </div>

        {% else %}

            <div class="status amarelo">

                🟡 llama.cpp ainda não está instalado.

            </div>

        {% endif %}

    </div>


    <div class="painel">

        <h2>🛠️ Ferramentas disponíveis</h2>

        <div class="status {{ git_status }}">

            {{ git_text }}

        </div>

        <div class="status {{ cmake_status }}">

            {{ cmake_text }}

        </div>

        <div class="status {{ make_status }}">

            {{ make_text }}

        </div>

    </div>


    <div class="painel">

        <h2>🧪 Diagnóstico completo</h2>

        <div class="status azul">

            <pre>{{ diagnostico }}</pre>

        </div>

    </div>


    <div class="painel">

        <h2>📦 Modelo</h2>

        <div class="status amarelo">

            ⏸️ SmolVLM ainda NÃO será baixado.

            <br><br>

            Primeiro precisamos preparar o runtime.

        </div>

    </div>

</div>

</body>

</html>
"""


def encontrar_executavel():

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

    caminhos = [

        "./llama",
        "./llama-cli",
        "./llama-server",
        "./llama-mtmd-cli",

        "./bin/llama",
        "./bin/llama-cli",
        "./bin/llama-server",
        "./bin/llama-mtmd-cli",

        "./llama.cpp/build/bin/llama-cli",
        "./llama.cpp/build/bin/llama-server",
        "./llama.cpp/build/bin/llama-mtmd-cli"

    ]

    for caminho in caminhos:

        if os.path.isfile(caminho):
            return caminho

    return None


def verificar_comando(nome):

    caminho = shutil.which(nome)

    if caminho:

        return True, caminho

    return False, None


def executar_versao(comando):

    try:

        resultado = subprocess.run(
            [comando, "--version"],
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

            return saida.strip()

        return "Comando encontrado, mas sem saída."

    except Exception as erro:

        return f"Erro: {erro}"


def diagnosticar():

    linhas = []

    linhas.append(
        "🧪 DIAGNÓSTICO DO AMBIENTE"
    )

    linhas.append(
        "================================"
    )

    llama = encontrar_executavel()

    if llama:

        linhas.append(
            f"🟢 llama.cpp encontrado: {llama}"
        )

        linhas.append(
            executar_versao(llama)
        )

    else:

        linhas.append(
            "🟡 llama.cpp: não encontrado"
        )

    git_ok, git_path = verificar_comando("git")

    if git_ok:

        linhas.append(
            f"🟢 Git encontrado: {git_path}"
        )

        linhas.append(
            executar_versao(git_path)
        )

    else:

        linhas.append(
            "🔴 Git não encontrado"
        )

    cmake_ok, cmake_path = verificar_comando("cmake")

    if cmake_ok:

        linhas.append(
            f"🟢 CMake encontrado: {cmake_path}"
        )

        linhas.append(
            executar_versao(cmake_path)
        )

    else:

        linhas.append(
            "🔴 CMake não encontrado"
        )

    make_ok, make_path = verificar_comando("make")

    if make_ok:

        linhas.append(
            f"🟢 Make encontrado: {make_path}"
        )

    else:

        linhas.append(
            "🟡 Make não encontrado"
        )

    linhas.append(
        "================================"
    )

    linhas.append(
        "📦 Nenhum modelo foi baixado."
    )

    return "\n".join(linhas)


@app.route("/")
def inicio():

    llama = encontrar_executavel()

    git_ok, git_path = verificar_comando("git")

    cmake_ok, cmake_path = verificar_comando("cmake")

    make_ok, make_path = verificar_comando("make")


    if git_ok:

        git_status = "verde"

        git_text = (
            f"🟢 Git disponível: {git_path}"
        )

    else:

        git_status = "vermelho"

        git_text = (
            "🔴 Git não encontrado"
        )


    if cmake_ok:

        cmake_status = "verde"

        cmake_text = (
            f"🟢 CMake disponível: {cmake_path}"
        )

    else:

        cmake_status = "vermelho"

        cmake_text = (
            "🔴 CMake não encontrado"
        )


    if make_ok:

        make_status = "verde"

        make_text = (
            f"🟢 Make disponível: {make_path}"
        )

    else:

        make_status = "amarelo"

        make_text = (
            "🟡 Make não encontrado"
        )


    return render_template_string(
        HTML,

        llama_caminho=llama,

        git_status=git_status,
        git_text=git_text,

        cmake_status=cmake_status,
        cmake_text=cmake_text,

        make_status=make_status,
        make_text=make_text,

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

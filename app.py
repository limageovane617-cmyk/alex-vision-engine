from flask import Flask, request, render_template_string
import base64
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

    <title>Alex Vision Engine</title>

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

        hr {
            border: none;
            border-top: 1px solid #374151;
            margin: 25px 0;
        }

        input[type="file"] {
            width: 100%;
            margin: 20px 0;
        }

        textarea {
            width: 100%;
            min-height: 100px;
            padding: 12px;
            box-sizing: border-box;
            border-radius: 10px;
            border: none;
            font-size: 16px;
            resize: vertical;
        }

        button {
            margin-top: 15px;
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
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
            padding: 12px;
            border-radius: 10px;
            margin-top: 10px;
        }

        .verde {
            background: #065f46;
        }

        .azul {
            background: #1e3a8a;
        }

        .amarelo {
            background: #78350f;
        }

        .vermelho {
            background: #7f1d1d;
        }

        .imagem {
            max-width: 100%;
            margin-top: 20px;
            border-radius: 15px;
        }

        .resultado {
            margin-top: 20px;
            padding: 18px;
            border-radius: 12px;
            background: #374151;
            text-align: left;
        }

        code {
            word-break: break-word;
        }

    </style>

</head>

<body>

<div class="caixa">

    <h1>🧠 Alex Vision Engine</h1>

    <p>
        Terceiro estágio do motor de visão da Alex IA Ultra
    </p>

    <hr>

    <div class="painel">

        <h2>🧠 Diagnóstico do Motor</h2>

        <div class="status verde">
            🟢 Motor base online
        </div>

        <div class="status azul">
            🔬 Modelo planejado:
            <strong>SmolVLM-256M-Instruct</strong>
        </div>

        <div class="status azul">
            ⚙️ Runtime planejado:
            <strong>llama.cpp</strong>
        </div>

        {% if llama_status %}

            <div class="status verde">
                🟢 llama.cpp encontrado!
            </div>

        {% else %}

            <div class="status amarelo">
                🟡 llama.cpp ainda não está instalado neste ambiente.
            </div>

        {% endif %}

        <p>
            Esta etapa apenas verifica o ambiente.
            Nenhum modelo será baixado automaticamente.
        </p>

    </div>

    <h2>📷 Teste de Visão</h2>

    <form
        method="POST"
        enctype="multipart/form-data"
    >

        <input
            type="file"
            name="imagem"
            accept="image/*"
            required
        >

        <textarea
            name="comando"
            placeholder="Digite uma pergunta sobre a imagem..."
            required
        ></textarea>

        <br>

        <button type="submit">
            🧠 Enviar para o Motor
        </button>

    </form>

    {% if imagem %}

        <div class="status verde">

            🟢 Imagem recebida pelo motor!

        </div>

        <img
            class="imagem"
            src="data:{{ tipo }};base64,{{ imagem }}"
        >

    {% endif %}

    {% if comando %}

        <div class="resultado">

            <strong>
                ✏️ Pergunta recebida:
            </strong>

            <br><br>

            {{ comando }}

        </div>

    {% endif %}

    {% if imagem and comando %}

        <div class="status azul">

            🧪 Terceira etapa recebida!

            <br><br>

            📷 Imagem: OK<br>
            ✏️ Pergunta: OK<br>
            🧠 Interface: OK

        </div>

        {% if llama_status %}

            <div class="status verde">

                🟢 Runtime llama.cpp disponível.

                <br><br>

                Próximo passo:
                preparar o modelo SmolVLM.

            </div>

        {% else %}

            <div class="status amarelo">

                🟡 Runtime llama.cpp ainda não disponível.

                <br><br>

                O motor está funcionando,
                mas o cérebro ainda não foi instalado.

            </div>

        {% endif %}

    {% endif %}

</div>

</body>

</html>
"""


def verificar_llama():

    nomes = [
        "llama-server",
        "llama-cli",
        "llama"
    ]

    for nome in nomes:

        caminho = shutil.which(nome)

        if caminho:

            return caminho

    caminhos_locais = [
        "./llama-server",
        "./llama-cli",
        "./llama/llama-server",
        "./llama/llama-cli"
    ]

    for caminho in caminhos_locais:

        if os.path.isfile(caminho):

            return caminho

    return None


@app.route("/", methods=["GET", "POST"])
def inicio():

    imagem = None
    tipo = None
    comando = None

    llama_caminho = verificar_llama()
    llama_status = llama_caminho is not None

    if request.method == "POST":

        arquivo = request.files.get("imagem")

        comando = request.form.get(
            "comando",
            ""
        ).strip()

        if arquivo and arquivo.filename:

            dados = arquivo.read()

            imagem = base64.b64encode(
                dados
            ).decode("utf-8")

            tipo = (
                arquivo.mimetype
                or "image/jpeg"
            )

    return render_template_string(
        HTML,
        imagem=imagem,
        tipo=tipo,
        comando=comando,
        llama_status=llama_status,
        llama_caminho=llama_caminho
    )


@app.route("/diagnostico")
def diagnostico():

    llama_caminho = verificar_llama()

    if llama_caminho:

        try:

            resultado = subprocess.run(
                [llama_caminho, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            versao = (
                resultado.stdout
                or resultado.stderr
                or "Versão não informada."
            )

            return (
                "🟢 llama.cpp encontrado!<br><br>"
                f"Caminho: <code>{llama_caminho}</code>"
                "<br><br>"
                f"<pre>{versao}</pre>"
            )

        except Exception as erro:

            return (
                "🟡 llama.cpp foi encontrado, "
                "mas não foi possível executar "
                "o diagnóstico.<br><br>"
                f"Erro: {erro}"
            )

    return (
        "🟡 llama.cpp ainda não está instalado "
        "neste ambiente."
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

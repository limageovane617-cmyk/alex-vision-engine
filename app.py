from flask import Flask, request, render_template_string
import base64
import os

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

    </style>

</head>

<body>

<div class="caixa">

    <h1>🧠 Alex Vision Engine</h1>

    <p>
        Segundo estágio do motor de visão da Alex IA Ultra
    </p>

    <hr>

    <div class="painel">

        <h2>🧠 Motor de Visão</h2>

        <div class="status verde">
            🟢 Motor base online
        </div>

        <div class="status azul">
            🔬 Modelo planejado:
            <strong>SmolVLM-256M-Instruct</strong>
        </div>

        <div class="status amarelo">
            ⚙️ Runtime planejado:
            <strong>llama.cpp</strong>
        </div>

        <p>
            O modelo ainda não foi carregado.
            Esta etapa prepara a interface para a
            integração controlada do motor multimodal.
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

            🧪 Segunda etapa recebida!

            <br><br>

            📷 Imagem: OK<br>
            ✏️ Pergunta: OK<br>
            🧠 Interface do motor: OK<br>
            🔬 SmolVLM: aguardando integração

        </div>

    {% endif %}

</div>

</body>

</html>
"""


@app.route("/", methods=["GET", "POST"])
def inicio():

    imagem = None
    tipo = None
    comando = None

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
        comando=comando
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

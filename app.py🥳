from flask import Flask, request, render_template_string
import base64

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

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
            max-width: 650px;
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
        }

        button {
            margin-top: 15px;
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
        }

        .sucesso {
            margin-top: 20px;
            padding: 15px;
            border-radius: 12px;
            background: #065f46;
        }

        .imagem {
            max-width: 100%;
            margin-top: 20px;
            border-radius: 15px;
        }

    </style>

</head>

<body>

<div class="caixa">

    <h1>🧠 Alex Vision Engine</h1>

    <p>
        Primeiro laboratório do motor de visão da Alex IA Ultra
    </p>

    <hr>

    <h2>📷 Teste do Motor</h2>

    <form method="POST" enctype="multipart/form-data">

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
            🧪 Testar Motor
        </button>

    </form>

    {% if imagem %}

        <div class="sucesso">

            🟢 Imagem recebida pelo motor!

        </div>

        <img
            class="imagem"
            src="data:{{ tipo }};base64,{{ imagem }}"
        >

    {% endif %}

    {% if comando %}

        <div class="sucesso">

            ✏️ Comando recebido:

            <br><br>

            {{ comando }}

        </div>

    {% endif %}

    {% if imagem and comando %}

        <div class="sucesso">

            🧪 TESTE DA BASE CONCLUÍDO!

            <br><br>

            📷 Imagem recebida<br>
            ✏️ Comando recebido<br>
            🧠 Motor preparado para receber o modelo de IA

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

    import os

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

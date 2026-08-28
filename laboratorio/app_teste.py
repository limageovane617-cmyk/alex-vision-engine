from flask import Flask, render_template_string, jsonify
import os
import shutil
import subprocess
import threading
import time
import signal
import queue

app = Flask(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================

MODEL = "ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0"

# Limite máximo do teste: 30 minutos
LIMITE_SEGUNDOS = 1800

# Quantidade máxima de saída armazenada
MAX_OUTPUT = 50000

# Intervalo de atualização do processo
INTERVALO_MONITORAMENTO = 0.25


# ============================================================
# ESTADO GLOBAL DO TESTE
# ============================================================

job_lock = threading.Lock()

job = {
    "status": "idle",
    "success": False,
    "output": "",
    "started_at": None,
    "finished_at": None,
    "pid": None,
    "mensagem": "⏸️ Aguardando início do teste.",
}

processo_atual = None


# ============================================================
# INTERFACE HTML
# ============================================================

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
    white-space: pre-wrap;
    word-break: break-word;
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

.cinza {
    background: #374151;
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
    cursor: pointer;
}

button:disabled {
    background: #4b5563;
    cursor: wait;
}

pre {
    white-space: pre-wrap;
    word-break: break-word;
    background: #030712;
    padding: 15px;
    border-radius: 10px;
    overflow-x: auto;
    max-height: 500px;
    overflow-y: auto;
}

code {
    word-break: break-word;
}

.pequeno {
    opacity: 0.8;
    font-size: 14px;
}

.tempo {
    font-size: 22px;
    font-weight: bold;
    margin-top: 10px;
}

</style>

</head>

<body>

<div class="caixa">

<h1>🧪 Alex Vision Lab</h1>

<p>
Teste controlado do carregamento do SmolVLM
</p>


<!-- ====================================================== -->
<!-- RUNTIME -->
<!-- ====================================================== -->

<div class="painel">

<h2>🔬 Runtime</h2>

{% if llama %}

<div class="status verde">

🟢 llama-cli encontrado!

<br><br>

<code>{{ llama }}</code>

</div>

{% else %}

<div class="status vermelho">

🔴 llama-cli não encontrado.

</div>

{% endif %}


{% if mtmd %}

<div class="status verde">

🟢 llama-mtmd-cli encontrado!

<br><br>

<code>{{ mtmd }}</code>

</div>

{% else %}

<div class="status vermelho">

🔴 llama-mtmd-cli não encontrado.

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


<!-- ====================================================== -->
<!-- MODELO -->
<!-- ====================================================== -->

<div class="painel">

<h2>🧠 SmolVLM-256M</h2>

<div class="status azul">

Modelo:

<br><br>

<code>{{ model }}</code>

</div>

<p>
O modelo será carregado pelo llama-mtmd-cli.
</p>

<p class="pequeno">
⏱️ Limite de segurança: 30 minutos.
</p>

<button
    id="botao"
    onclick="iniciarTeste()"
>
🧠 Carregar SmolVLM
</button>

</div>


<!-- ====================================================== -->
<!-- STATUS -->
<!-- ====================================================== -->

<div class="painel">

<h2>🧪 Status do Teste</h2>

<div
    id="status"
    class="status cinza"
>
⏸️ Aguardando início do teste.
</div>

<div
    id="tempo"
    class="tempo"
></div>

<pre
    id="resultado"
    style="display:none;"
></pre>

</div>


<!-- ====================================================== -->
<!-- OBJETIVO -->
<!-- ====================================================== -->

<div class="painel">

<h2>🎯 Objetivo desta etapa</h2>

<div class="status azul">

1️⃣ Confirmar llama.cpp

<br><br>

2️⃣ Usar llama-mtmd-cli para o SmolVLM

<br><br>

3️⃣ Baixar/carregar o modelo

<br><br>

4️⃣ Confirmar que o modelo responde

<br><br>

5️⃣ Depois testar imagens

</div>

</div>


</div>


<script>

let monitorando = false;
let tentativasFalha = 0;


/* ==========================================================
   INICIAR TESTE
   ========================================================== */

async function iniciarTeste() {

    const botao =
        document.getElementById("botao");

    const status =
        document.getElementById("status");

    const resultado =
        document.getElementById("resultado");

    const tempo =
        document.getElementById("tempo");


    botao.disabled = true;

    botao.innerText =
        "⏳ Iniciando...";


    status.className =
        "status amarelo";

    status.innerText =
        "🟡 Preparando llama-mtmd-cli...";


    tempo.innerText = "";

    resultado.style.display =
        "none";

    resultado.innerText =
        "";

    tentativasFalha = 0;


    try {

        const resposta =
            await fetch(
                "/iniciar",
                {
                    method: "POST",
                    cache: "no-store"
                }
            );


        if (!resposta.ok) {

            throw new Error(
                "Servidor respondeu HTTP " +
                resposta.status
            );

        }


        const dados =
            await resposta.json();


        if (!dados.ok) {

            status.className =
                "status vermelho";

            status.innerText =
                "🔴 " +
                (dados.mensagem ||
                "Não foi possível iniciar.");

            liberarBotao();

            return;

        }


        monitorando = true;


        status.className =
            "status amarelo";

        status.innerText =
            "🟡 Processo iniciado. " +
            "O SmolVLM está sendo carregado...";


        acompanhar();

    }

    catch (erro) {

        monitorando = false;

        status.className =
            "status vermelho";

        status.innerText =
            "🔴 Erro ao iniciar o teste:\n\n" +
            erro.message;

        liberarBotao();

    }

}


/* ==========================================================
   ACOMPANHAR PROCESSO
   ========================================================== */

async function acompanhar() {

    if (!monitorando) {
        return;
    }


    try {

        const resposta =
            await fetch(
                "/status?t=" +
                Date.now(),
                {
                    method: "GET",
                    cache: "no-store"
                }
            );


        if (!resposta.ok) {

            throw new Error(
                "HTTP " +
                resposta.status
            );

        }


        const dados =
            await resposta.json();


        tentativasFalha = 0;


        const status =
            document.getElementById("status");

        const tempo =
            document.getElementById("tempo");


        /* ==================================================
           PROCESSANDO
           ================================================== */

        if (
            dados.status === "running" ||
            dados.status === "starting"
        ) {

            const segundos =
                Number(dados.tempo) || 0;


            const minutos =
                Math.floor(
                    segundos / 60
                );


            const restante =
                Math.floor(
                    segundos % 60
                );


            status.className =
                "status amarelo";


            status.innerText =
                dados.mensagem ||
                "🟡 SmolVLM carregando...";


            tempo.innerText =
                "⏱️ " +
                minutos +
                "m " +
                String(restante).padStart(
                    2,
                    "0"
                ) +
                "s";


            if (dados.output) {

                mostrarResultado(
                    dados.output
                );

            }


            setTimeout(
                acompanhar,
                2000
            );


            return;

        }


        /* ==================================================
           SUCESSO
           ================================================== */

        if (
            dados.status === "success"
        ) {

            monitorando = false;


            status.className =
                "status verde";


            status.innerText =
                "🟢 SmolVLM carregado " +
                "e processo concluído!";


            tempo.innerText =
                "⏱️ Tempo total: " +
                formatarTempo(
                    dados.tempo || 0
                );


            mostrarResultado(
                dados.output
            );


            liberarBotao();

            return;

        }


        /* ==================================================
           ERRO
           ================================================== */

        if (
            dados.status === "error"
        ) {

            monitorando = false;


            status.className =
                "status vermelho";


            status.innerText =
                "🔴 O processo terminou com erro.\n\n" +
                (
                    dados.mensagem ||
                    "Erro desconhecido."
                );


            tempo.innerText =
                "⏱️ Tempo executado: " +
                formatarTempo(
                    dados.tempo || 0
                );


            mostrarResultado(
                dados.output
            );


            liberarBotao();

            return;

        }


        /* ==================================================
           IDLE
           ================================================== */

        if (
            dados.status === "idle"
        ) {

            monitorando = false;


            status.className =
                "status cinza";


            status.innerText =
                "⏸️ Aguardando início do teste.";


            tempo.innerText = "";


            liberarBotao();

            return;

        }


        setTimeout(
            acompanhar,
            2000
        );

    }

    catch (erro) {

        tentativasFalha++;


        const status =
            document.getElementById(
                "status"
            );


        status.className =
            "status amarelo";


        status.innerText =
            "🟡 Falha temporária ao consultar " +
            "o processo. Tentando novamente...\n\n" +
            "Tentativa: " +
            tentativasFalha;


        /*
         * NÃO encerramos o processo.
         *
         * Uma falha momentânea na consulta
         * não significa que o SmolVLM morreu.
         */

        setTimeout(
            acompanhar,
            3000
        );

    }

}


/* ==========================================================
   MOSTRAR RESULTADO
   ========================================================== */

function mostrarResultado(texto) {

    const resultado =
        document.getElementById(
            "resultado"
        );


    if (
        !texto ||
        String(texto).trim() === ""
    ) {

        return;

    }


    resultado.style.display =
        "block";


    resultado.innerText =
        String(texto);

}


/* ==========================================================
   FORMATAR TEMPO
   ========================================================== */

function formatarTempo(segundos) {

    segundos =
        Math.max(
            0,
            Number(segundos) || 0
        );


    const minutos =
        Math.floor(
            segundos / 60
        );


    const segundosRestantes =
        Math.floor(
            segundos % 60
        );


    return (
        minutos +
        "m " +
        String(
            segundosRestantes
        ).padStart(
            2,
            "0"
        ) +
        "s"
    );

}


/* ==========================================================
   LIBERAR BOTÃO
   ========================================================== */

function liberarBotao() {

    const botao =
        document.getElementById(
            "botao"
        );


    botao.disabled =
        false;


    botao.innerText =
        "🧠 Carregar SmolVLM";

}

</script>

</body>

</html>
"""


# ============================================================
# LOCALIZAR EXECUTÁVEIS
# ============================================================

def procurar(nome):

    caminho = shutil.which(nome)

    if caminho:
        return caminho


    caminhos = [
        os.path.join(".", "bin", nome),
        os.path.join(".", nome),
        os.path.join(".", "llama.cpp", nome),
        os.path.join(".", "llama.cpp", "build", "bin", nome),
        os.path.join(
            ".",
            "llama.cpp",
            "build",
            "bin",
            "Release",
            nome
        ),
    ]


    for caminho in caminhos:

        if os.path.isfile(caminho):

            try:
                os.chmod(
                    caminho,
                    0o755
                )
            except Exception:
                pass


            return caminho


    return None


# ============================================================
# ATUALIZAR SAÍDA
# ============================================================




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



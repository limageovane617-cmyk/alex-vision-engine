from flask import Flask, render_template_string, jsonify
import os
import shutil
import subprocess
import threading
import time
import signal

app = Flask(__name__)

MODEL = "ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0"

# ============================================================
# CONTROLE GLOBAL DO TESTE
# ============================================================

job_lock = threading.Lock()

job = {
    "status": "idle",
    "success": False,
    "output": "",
    "started_at": None,
    "finished_at": None,
    "pid": None,
    "returncode": None,
    "command": "",
}

processo_atual = None


# ============================================================
# INTERFACE
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

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
}

code {
    word-break: break-word;
}

.pequeno {
    opacity: 0.8;
    font-size: 14px;
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

🟢 llama.cpp encontrado!

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

O processo será executado em segundo plano.
A página continuará respondendo durante o carregamento.

</p>

<button
    id="botao"
    onclick="iniciarTeste()">

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
    class="status cinza">

⏸️ Aguardando início do teste.

</div>

<pre
    id="resultado"
    style="display:none;"></pre>

</div>


<!-- ====================================================== -->
<!-- OBJETIVO -->
<!-- ====================================================== -->

<div class="painel">

<h2>🎯 Objetivo desta etapa</h2>

<div class="status azul">

1️⃣ Confirmar llama.cpp

<br>

2️⃣ Iniciar carregamento do SmolVLM

<br>

3️⃣ Executar sem bloquear a página

<br>

4️⃣ Capturar o erro verdadeiro se falhar

<br>

5️⃣ Depois testar o motor de visão

</div>

</div>


</div>


<script>

let monitorando = false;


async function iniciarTeste() {

    const botao =
        document.getElementById("botao");

    const status =
        document.getElementById("status");

    const resultado =
        document.getElementById("resultado");


    botao.disabled = true;

    botao.innerText =
        "⏳ Iniciando...";


    status.className =
        "status amarelo";

    status.innerText =
        "🟡 Iniciando o teste em segundo plano...";


    resultado.style.display =
        "none";

    resultado.innerText =
        "";


    try {

        const resposta =
            await fetch(
                "/iniciar",
                {
                    method: "POST"
                }
            );


        const dados =
            await resposta.json();


        if (!dados.ok) {

            status.className =
                "status vermelho";

            status.innerText =
                "🔴 " + dados.mensagem;

            botao.disabled =
                false;

            botao.innerText =
                "🧠 Carregar SmolVLM";

            return;
        }


        monitorando = true;


        status.className =
            "status amarelo";

        status.innerText =
            "🟡 Processo iniciado em segundo plano...";


        acompanhar();


    } catch (erro) {

        status.className =
            "status vermelho";

        status.innerText =
            "🔴 Erro ao iniciar: " + erro;


        botao.disabled =
            false;

        botao.innerText =
            "🧠 Carregar SmolVLM";
    }
}



async function acompanhar() {

    if (!monitorando) {
        return;
    }


    try {

        const resposta =
            await fetch(
                "/status",
                {
                    cache: "no-store"
                }
            );


        const dados =
            await resposta.json();


        if (dados.status === "starting") {

            document.getElementById(
                "status"
            ).className =
                "status azul";


            document.getElementById(
                "status"
            ).innerText =
                "🔵 Preparando processo...";


            setTimeout(
                acompanhar,
                1500
            );

            return;
        }


        if (dados.status === "running") {

            const segundos =
                dados.tempo || 0;


            const minutos =
                Math.floor(
                    segundos / 60
                );


            const restante =
                segundos % 60;


            document.getElementById(
                "status"
            ).className =
                "status amarelo";


            document.getElementById(
                "status"
            ).innerText =
                "🟡 SmolVLM carregando... "
                + minutos
                + "m "
                + restante
                + "s"
                + " | PID: "
                + (dados.pid || "?");


            setTimeout(
                acompanhar,
                2000
            );

            return;
        }


        if (dados.status === "success") {

            monitorando =
                false;


            document.getElementById(
                "status"
            ).className =
                "status verde";


            document.getElementById(
                "status"
            ).innerText =
                "🟢 Processo concluído com sucesso!";


            mostrarResultado(
                dados.output
            );


            liberarBotao();

            return;
        }


        if (dados.status === "error") {

            monitorando =
                false;


            document.getElementById(
                "status"
            ).className =
                "status vermelho";


            document.getElementById(
                "status"
            ).innerText =
                "🔴 O processo terminou com erro."
                + " Código: "
                + (dados.returncode ?? "desconhecido");


            mostrarResultado(
                dados.output
            );


            liberarBotao();

            return;
        }


        if (dados.status === "idle") {

            monitorando =
                false;


            document.getElementById(
                "status"
            ).className =
                "status cinza";


            document.getElementById(
                "status"
            ).innerText =
                "⏸️ Aguardando início do teste.";


            liberarBotao();

            return;
        }


        setTimeout(
            acompanhar,
            2000
        );


    } catch (erro) {

        document.getElementById(
            "status"
        ).className =
            "status vermelho";


        document.getElementById(
            "status"
        ).innerText =
            "🔴 Erro ao consultar status. Tentando novamente...";


        setTimeout(
            acompanhar,
            3000
        );
    }
}



function mostrarResultado(texto) {

    const resultado =
        document.getElementById(
            "resultado"
        );


    resultado.style.display =
        "block";


    resultado.innerText =
        texto ||
        "Nenhuma saída foi recebida pelo processo.";
}



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

        f"./bin/{nome}",

        f"./{nome}",

        f"./llama.cpp/{nome}",

        f"./llama.cpp/build/bin/{nome}",

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
# EXECUÇÃO DO SMOLVLM EM SEGUNDO PLANO
# ============================================================

def executar_em_segundo_plano(caminho):

    global processo_atual


    comando = [

        caminho,

        "-hf",
        MODEL,

        "-p",
        "Olá Alex. Responda apenas: modelo carregado.",

        "-n",
        "16",

    ]


    inicio =
    time.time()


    with job_lock:

        job["status"] =
            "running"

        job["success"] =
            False

        job["output"] =
            ""

        job["started_at"] =
            inicio

        job["finished_at"] =
            None

        job["pid"] =
            None

        job["returncode"] =
            None

        job["command"] =
            " ".join(comando)


    try:

        saida = []


        saida.append(
            "🧪 Alex Vision Lab\n"
        )

        saida.append(
            "==============================\n"
        )

        saida.append(
            "🚀 Iniciando llama.cpp...\n\n"
        )

        saida.append(
            "📦 Modelo:\n"
            + MODEL
            + "\n\n"
        )

        saida.append(
            "▶️ Comando:\n"
            + " ".join(comando)
            + "\n\n"
        )


        # ----------------------------------------------------
        # INICIAR PROCESSO
        # ----------------------------------------------------

        processo = subprocess.Popen(

            comando,

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            stdin=subprocess.DEVNULL,

            text=True,

            bufsize=1,

            errors="replace",

            start_new_session=True,

        )


        processo_atual =
            processo


        with job_lock:

            job["pid"] =
                processo.pid


        saida.append(
            "🟢 Processo iniciado.\n"
        )

        saida.append(
            "PID: "
            + str(processo.pid)
            + "\n\n"
        )


        with job_lock:

            job["output"] =
                "".join(saida)


        # ----------------------------------------------------
        # LIMITE DE SEGURANÇA
        # ----------------------------------------------------

        LIMITE_SEGUNDOS = 1800


        while True:

            linha =
                processo.stdout.readline()


            if linha:

                saida.append(
                    linha
                )


                texto_atual =
                    "".join(saida)


                with job_lock:

                    job["output"] =
                        texto_atual[-50000:]


            retorno =
                processo.poll()


            if retorno is not None:

                break


            if (
                time.time()
                - inicio
                > LIMITE_SEGUNDOS
            ):

                saida.append(
                    "\n\n"
                    "⏱️ LIMITE INTERNO DE 30 MINUTOS "
                    "ATINGIDO.\n"
                )


                try:

                    os.killpg(
                        os.getpgid(
                            processo.pid
                        ),
                        signal.SIGTERM
                    )

                except Exception:

                    try:
                        processo.kill()

                    except Exception:
                        pass


                with job_lock:

                    job["status"] =
                        "error"

                    job["success"] =
                        False

                    job["output"] =
                        "".join(saida)[-50000:]

                    job["finished_at"] =
                        time.time()

                    job["pid"] =
                        None

                    job["returncode"] =
                        -1


                processo_atual =
                    None

                return


        # ----------------------------------------------------
        # CAPTURAR RESTANTE
        # ----------------------------------------------------

        restante =
            processo.stdout.read()


        if restante:

            saida.append(
                restante
            )


        texto =
            "".join(saida)


        retorno =
            processo.returncode


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        if retorno == 0:

            texto += (
                "\n\n"
                "================================\n"
                "🟢 PROCESSO FINALIZADO COM SUCESSO\n"
                "================================\n"
            )


            with job_lock:

                job["status"] =
                    "success"

                job["success"] =
                    True

                job["output"] =
                    texto[-50000:]

                job["finished_at"] =
                    time.time()

                job["pid"] =
                    None

                job["returncode"] =
                    retorno


        else:

            texto += (
                "\n\n"
                "================================\n"
                "🔴 PROCESSO FINALIZADO COM ERRO\n"
                "================================\n\n"
                "Código de saída: "
                + str(retorno)
                + "\n"
            )


            with job_lock:

                job["status"] =
                    "error"

                job["success"] =
                    False

                job["output"] =
                    texto[-50000:]

                job["finished_at"] =
                    time.time()

                job["pid"] =
                    None

                job["returncode"] =
                    retorno


    except Exception as erro:

        texto_erro = (

            "================================\n"
            "🔴 EXCEÇÃO PYTHON\n"
            "================================\n\n"

            "Tipo: "
            + type(erro).__name__
            + "\n\n"

            "Mensagem:\n"
            + str(erro)
            + "\n\n"

            "Comando:\n"
            + " ".join(comando)
        )


        with job_lock:

            job["status"] =
                "error"

            job["success"] =
                False

            job["output"] =
                texto_erro

            job["finished_at"] =
                time.time()

            job["pid"] =
                None

            job["returncode"] =
                -1


    finally:

        processo_atual =
            None


# ============================================================
# INICIAR TESTE
# ============================================================

@app.route(
    "/iniciar",
    methods=["POST"]
)
def iniciar():

    llama =
        procurar(
            "llama-cli"
        )


    if not llama:

        llama =
            procurar(
                "llama"
            )


    if not llama:

        return jsonify({

            "ok":
                False,

            "mensagem":
                "llama-cli não foi encontrado."

        })


    with job_lock:

        if job["status"] in (
            "starting",
            "running"
        ):

            return jsonify({

                "ok":
                    False,

                "mensagem":
                    "O SmolVLM já está sendo carregado."

            })


        job["status"] =
            "starting"

        job["output"] =
            ""

        job["success"] =
            False

        job["started_at"] =
            time.time()

        job["finished_at"] =
            None

        job["pid"] =
            None

        job["returncode"] =
            None

        job["command"] =
            ""


    thread = threading.Thread(

        target=
            executar_em_segundo_plano,

        args=
            (llama,),

        daemon=True,

    )


    thread.start()


    return jsonify({

        "ok":
            True,

        "mensagem":
            "Processo iniciado em segundo plano."

    })


# ============================================================
# STATUS
# ============================================================

@app.route(
    "/status",
    methods=["GET"]
)
def status():

    with job_lock:

        dados =
            dict(job)


    tempo = 0


    if dados["started_at"]:

        fim =
            dados["finished_at"]


        if fim is None:

            fim =
                time.time()


        tempo =
            int(
                max(
                    0,
                    fim
                    - dados["started_at"]
                )
            )


    dados["tempo"] =
        tempo


    return jsonify(dados)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def inicio():

    llama =
        procurar(
            "llama-cli"
        )


    if not llama:

        llama =
            procurar(
                "llama"
            )


    mtmd =
        procurar(
            "llama-mtmd-cli"
        )


    server =
        procurar(
            "llama-server"
        )


    return render_template_string(

        HTML,

        llama=llama,

        mtmd=mtmd,

        server=server,

        model=MODEL,

    )


# ============================================================
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == "__main__":

    porta = int(

        os.environ.get(
            "PORT",
            10000
        )

    )


    app.run(

        host="0.0.0.0",

        port=porta,

    )

from flask import Flask, render_template_string, jsonify
import os
import shutil
import subprocess
import threading
import time
import signal
import queue
import platform


# ============================================================
# ALEX VISION LAB
# TESTE CONTROLADO DO SMOLVLM-256M
# ============================================================

app = Flask(__name__)

MODEL = "ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0"

# 30 minutos
LIMITE_SEGUNDOS = 1800

# Limite da saída armazenada
MAX_OUTPUT = 60000

# Intervalo de atualização
INTERVALO_STATUS = 2


# ============================================================
# ESTADO GLOBAL DO TESTE
# ============================================================

job_lock = threading.RLock()

job = {
    "status": "idle",
    "success": False,
    "output": "",
    "started_at": None,
    "finished_at": None,
    "pid": None,
    "mensagem": "Aguardando início do teste.",
    "returncode": None,
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
    padding: 20px 12px;
}

.caixa {
    max-width: 900px;
    margin: auto;
    background: #1f2937;
    padding: 22px;
    border-radius: 20px;
}

h1 {
    font-size: 30px;
}

.painel {
    margin-top: 18px;
    padding: 18px;
    border-radius: 15px;
    background: #111827;
    border: 1px solid #374151;
    text-align: left;
}

.status {
    padding: 15px;
    border-radius: 10px;
    margin-top: 10px;
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
    max-height: 550px;
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

.indicador {
    margin-top: 10px;
    font-size: 14px;
    opacity: 0.75;
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
O modelo será iniciado em segundo plano.
</p>

<p class="pequeno">
⏱️ Limite máximo: 30 minutos.
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

<div
    id="tempo"
    class="tempo">
</div>

<div
    id="conexao"
    class="indicador">
🟢 Monitoramento conectado
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

<br><br>

2️⃣ Iniciar SmolVLM

<br><br>

3️⃣ Acompanhar o processo

<br><br>

4️⃣ Capturar o resultado real

<br><br>

5️⃣ Depois testar imagens

</div>

</div>


</div>


<script>

let monitorando = false;

let falhasStatus = 0;


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
        "🟡 Preparando o carregamento do SmolVLM...";

    tempo.innerText = "";

    resultado.style.display = "none";

    resultado.innerText = "";

    falhasStatus = 0;


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
                "🔴 " + dados.mensagem;

            liberarBotao();

            return;
        }


        monitorando = true;


        status.className =
            "status amarelo";

        status.innerText =
            "🟡 Processo iniciado. Aguardando o SmolVLM...";


        acompanhar();

    }

    catch (erro) {

        status.className =
            "status vermelho";

        status.innerText =
            "🔴 Não foi possível iniciar o teste:\n" +
            erro;


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
                    cache: "no-store",
                    headers: {
                        "Cache-Control": "no-cache"
                    }
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


        falhasStatus = 0;


        document.getElementById(
            "conexao"
        ).innerText =
            "🟢 Monitoramento conectado";


        atualizarTela(dados);


    }

    catch (erro) {

        falhasStatus++;


        document.getElementById(
            "conexao"
        ).innerText =
            "🟡 Comunicação temporariamente indisponível (" +
            falhasStatus +
            ")";


        /*
         * IMPORTANTE:
         *
         * Uma falha na consulta HTTP NÃO significa
         * que o SmolVLM falhou.
         *
         * O processo continua no servidor.
         */

        if (falhasStatus <= 20) {

            setTimeout(
                acompanhar,
                3000
            );

            return;
        }


        /*
         * Depois de muitas falhas consecutivas,
         * fazemos uma última tentativa.
         */

        setTimeout(
            acompanhar,
            5000
        );

        return;
    }


    if (monitorando) {

        setTimeout(
            acompanhar,
            INTERVALO_STATUS * 1000
        );

    }

}


/* ==========================================================
   ATUALIZAR TELA
   ========================================================== */

function atualizarTela(dados) {

    const status =
        document.getElementById("status");

    const tempo =
        document.getElementById("tempo");


    const segundos =
        Number(dados.tempo) || 0;


    tempo.innerText =
        "⏱️ " +
        formatarTempo(segundos);


    if (dados.output) {

        mostrarResultado(
            dados.output
        );

    }


    /* ======================================================
       INICIANDO / RODANDO
       ====================================================== */

    if (
        dados.status === "starting" ||
        dados.status === "running"
    ) {

        status.className =
            "status amarelo";


        let mensagem =
            "🟡 SmolVLM carregando...";


        if (dados.mensagem) {

            mensagem +=
                "\n\n" +
                dados.mensagem;

        }


        if (dados.pid) {

            mensagem +=
                "\n\nPID: " +
                dados.pid;

        }


        status.innerText =
            mensagem;


        return;
    }


    /* ======================================================
       SUCESSO
       ====================================================== */

    if (
        dados.status === "success"
    ) {

        monitorando = false;


        status.className =
            "status verde";


        status.innerText =
            "🟢 llama.cpp terminou normalmente.";


        if (dados.mensagem) {

            status.innerText +=
                "\n\n" +
                dados.mensagem;

        }


        liberarBotao();

        return;
    }


    /* ======================================================
       ERRO
       ====================================================== */

    if (
        dados.status === "error"
    ) {

        monitorando = false;


        status.className =
            "status vermelho";


        status.innerText =
            "🔴 O processo terminou com erro.";


        if (dados.mensagem) {

            status.innerText +=
                "\n\n" +
                dados.mensagem;

        }


        if (
            dados.returncode !== null &&
            dados.returncode !== undefined
        ) {

            status.innerText +=
                "\n\nCódigo de saída: " +
                dados.returncode;

        }


        liberarBotao();

        return;
    }


    /* ======================================================
       IDLE
       ====================================================== */

    if (
        dados.status === "idle"
    ) {

        monitorando = false;


        status.className =
            "status cinza";


        status.innerText =
            "⏸️ Aguardando início do teste.";


        liberarBotao();

        return;
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


    const restante =
        Math.floor(
            segundos % 60
        );


    return (
        minutos +
        "m " +
        String(restante).padStart(
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

    # Primeiro procura no PATH
    caminho = shutil.which(nome)

    if caminho:
        return caminho


    # Depois procura nos locais conhecidos
    caminhos = [

        f"./bin/{nome}",

        f"./{nome}",

        f"./llama.cpp/{nome}",

        f"./llama.cpp/build/bin/{nome}",

        f"./llama.cpp/build/bin/Release/{nome}",

        f"/usr/local/bin/{nome}",

        f"/usr/bin/{nome}",

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
# ADICIONAR SAÍDA
# ============================================================

def adicionar_saida(texto):

    if not texto:
        return


    texto = str(texto)


    with job_lock:

        atual =
            job.get(
                "output",
                ""
            )


        novo =
            atual + texto


        job["output"] =
            novo[-MAX_OUTPUT:]


# ============================================================
# LEITOR DE SAÍDA
# ============================================================

def ler_saida(
    processo,
    fila
):

    try:

        while True:

            linha =
                processo.stdout.readline()


            if linha == "":
                break


            fila.put(
                linha
            )


    except Exception as erro:

        fila.put(
            "\n❌ Erro no leitor de saída:\n" +
            str(erro) +
            "\n"
        )


# ============================================================
# ENCERRAR PROCESSO
# ============================================================

def encerrar_processo(
    processo
):

    if processo is None:
        return


    try:

        if processo.poll() is not None:
            return


        # Linux / Render
        if platform.system() != "Windows":

            try:

                os.killpg(
                    os.getpgid(
                        processo.pid
                    ),
                    signal.SIGTERM
                )

            except Exception:

                try:
                    processo.terminate()
                except Exception:
                    pass

        else:

            try:
                processo.terminate()
            except Exception:
                pass


        try:

            processo.wait(
                timeout=8
            )

        except subprocess.TimeoutExpired:

            try:

                if platform.system() != "Windows":

                    os.killpg(
                        os.getpgid(
                            processo.pid
                        ),
                        signal.SIGKILL
                    )

                else:

                    processo.kill()

            except Exception:

                try:
                    processo.kill()
                except Exception:
                    pass


    except Exception:
        pass


# ============================================================
# EXECUTAR SMOLVLM
# ============================================================

def executar_em_segundo_plano(
    caminho
):

    global processo_atual


    processo = None


    inicio =
        time.time()


    comando = [

        caminho,

        "-hf",

        MODEL,

        "-p",

        "Olá Alex. Responda apenas: modelo carregado.",

        "-n",

        "16",

    ]


    try:

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

            job["mensagem"] =
                "🟡 Iniciando llama.cpp..."


        adicionar_saida(
            "==================================================\n"
        )

        adicionar_saida(
            "🧠 ALEX VISION LAB\n"
        )

        adicionar_saida(
            "Iniciando SmolVLM-256M...\n"
        )

        adicionar_saida(
            "Modelo: " +
            MODEL +
            "\n\n"
        )


        adicionar_saida(
            "Comando:\n" +
            " ".join(comando) +
            "\n\n"
        )


        # ====================================================
        # INICIAR PROCESSO
        # ====================================================

        processo = subprocess.Popen(

            comando,

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            stdin=subprocess.DEVNULL,

            text=True,

            bufsize=1,

            errors="replace",

            start_new_session=(
                platform.system() != "Windows"
            ),

        )


        processo_atual =
            processo


        with job_lock:

            job["pid"] =
                processo.pid

            job["mensagem"] =
                "🟡 Processo ativo. Aguardando o carregamento do modelo..."


        adicionar_saida(
            "🟢 Processo iniciado.\n"
        )

        adicionar_saida(
            "PID: " +
            str(processo.pid) +
            "\n\n"
        )


        # ====================================================
        # LEITOR
        # ====================================================

        fila =
            queue.Queue()


        leitor =
            threading.Thread(

                target=ler_saida,

                args=(
                    processo,
                    fila
                ),

                daemon=True,

            )


        leitor.start()


        # ====================================================
        # WATCHDOG
        # ====================================================

        while True:

            agora =
                time.time()


            tempo_decorrido =
                agora - inicio


            # ------------------------------------------------
            # DRENAR SAÍDA
            # ------------------------------------------------

            while True:

                try:

                    linha =
                        fila.get_nowait()

                except queue.Empty:

                    break


                adicionar_saida(
                    linha
                )


            # ------------------------------------------------
            # VERIFICAR PROCESSO
            # ------------------------------------------------

            retorno =
                processo.poll()


            if retorno is not None:

                # Drena saída restante
                while True:

                    try:

                        linha =
                            fila.get_nowait()

                    except queue.Empty:

                        break


                    adicionar_saida(
                        linha
                    )


                try:

                    leitor.join(
                        timeout=3
                    )

                except Exception:
                    pass


                texto_final = ""


                with job_lock:

                    texto_final =
                        job.get(
                            "output",
                            ""
                        )

                    job["finished_at"] =
                        time.time()

                    job["pid"] =
                        None

                    job["returncode"] =
                        retorno


                # ============================================
                # SUCESSO
                # ============================================

                if retorno == 0:

                    adicionar_saida(
                        "\n\n"
                        "==================================================\n"
                        "🟢 PROCESSO CONCLUÍDO COM SUCESSO\n"
                        "==================================================\n"
                    )


                    with job_lock:

                        job["status"] =
                            "success"

                        job["success"] =
                            True

                        job["mensagem"] =
                            "🟢 llama.cpp terminou normalmente."

                        job["pid"] =
                            None


                # ============================================
                # ERRO
                # ============================================

                else:

                    mensagem_erro =
                        (
                            "\n\n"
                            "==================================================\n"
                            "🔴 LLAMA.CPP ENCERROU COM ERRO\n"
                            "==================================================\n"
                            "Código de saída: " +
                            str(retorno) +
                            "\n"
                        )


                    adicionar_saida(
                        mensagem_erro
                    )


                    with job_lock:

                        job["status"] =
                            "error"

                        job["success"] =
                            False

                        job["mensagem"] =
                            (
                                "🔴 llama.cpp encerrou "
                                "com código " +
                                str(retorno)
                            )

                        job["output"] =
                            (
                                job.get(
                                    "output",
                                    ""
                                )
                            )[-MAX_OUTPUT:]

                        job["pid"] =
                            None


                processo_atual =
                    None

                return


            # ------------------------------------------------
            # TIMEOUT
            # ------------------------------------------------

            if (
                tempo_decorrido >=
                LIMITE_SEGUNDOS
            ):

                mensagem_timeout =
                    (
                        "\n\n"
                        "==================================================\n"
                        "⏱️ LIMITE DE 30 MINUTOS ATINGIDO\n"
                        "==================================================\n"
                        "O laboratório encerrou o processo "
                        "automaticamente.\n"
                    )


                adicionar_saida(
                    mensagem_timeout
                )


                encerrar_processo(
                    processo
                )


                with job_lock:

                    job["status"] =
                        "error"

                    job["success"] =
                        False

                    job["finished_at"] =
                        time.time()

                    job["pid"] =
                        None

                    job["returncode"] =
                        -1

                    job["mensagem"] =
                        "⏱️ Timeout de 30 minutos."


                processo_atual =
                    None

                return


            # ------------------------------------------------
            # MENSAGEM DE PROGRESSO
            # ------------------------------------------------

            minutos =
                int(
                    tempo_decorrido //
                    60
                )


            segundos =
                int(
                    tempo_decorrido %
                    60
                )


            with job_lock:

                job["mensagem"] =
                    (
                        "🟡 Carregando SmolVLM... "
                        +
                        str(minutos)
                        +
                        "m "
                        +
                        str(segundos)
                        +
                        "s"
                    )


            time.sleep(
                0.25
            )


    except Exception as erro:

        texto_erro =
            (
                "\n\n"
                "==================================================\n"
                "❌ ERRO AO EXECUTAR LLAMA.CPP\n"
                "==================================================\n"
                +
                str(erro)
                +
                "\n"
            )


        adicionar_saida(
            texto_erro
        )


        try:

            if processo is not None:

                encerrar_processo(
                    processo
                )

        except Exception:
            pass


        with job_lock:

            job["status"] =
                "error"

            job["success"] =
                False

            job["finished_at"] =
                time.time()

            job["pid"] =
                None

            job["returncode"] =
                -1

            job["mensagem"] =
                "🔴 Erro interno ao executar o modelo."


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

            "ok": False,

            "mensagem":
                "🔴 llama-cli não foi encontrado."

        })


    with job_lock:

        if job["status"] in (

            "running",

            "starting"

        ):

            return jsonify({

                "ok": False,

                "mensagem":
                    "🟡 O SmolVLM já está sendo carregado."

            })


        job["status"] =
            "starting"

        job["success"] =
            False

        job["output"] =
            ""

        job["started_at"] =
            time.time()

        job["finished_at"] =
            None

        job["pid"] =
            None

        job["returncode"] =
            None

        job["mensagem"] =
            "🟡 Preparando llama.cpp..."


    thread =
        threading.Thread(

            target=
                executar_em_segundo_plano,

            args=(
                llama,
            ),

            daemon=True,

        )


    thread.start()


    return jsonify({

        "ok": True,

        "mensagem":
            "🟢 Processo iniciado em segundo plano."

    })


# ============================================================
# STATUS
# ============================================================

@app.route(
    "/status",
    methods=["GET"]
)
def status():

    try:

        with job_lock:

            dados =
                dict(job)


        tempo =
            0


        if dados.get(
            "started_at"
        ):

            fim =
                dados.get(
                    "finished_at"
                )


            if fim is None:

                fim =
                    time.time()


            tempo =
                int(
                    max(
                        0,
                        fim -
                        dados["started_at"]
                    )
                )


        dados["tempo"] =
            tempo


        if dados.get(
            "output"
        ) is None:

            dados["output"] =
                ""


        if dados.get(
            "mensagem"
        ) is None:

            dados["mensagem"] =
                ""


        return jsonify(
            dados
        )


    except Exception as erro:

        # Nunca deixar /status quebrar
        return jsonify({

            "status":
                "running",

            "success":
                False,

            "output":
                "",

            "mensagem":
                "🟡 Monitoramento temporariamente indisponível: "
                + str(erro),

            "tempo":
                0,

            "pid":
                None,

            "returncode":
                None,

        })


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
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    porta =
        int(
            os.environ.get(
                "PORT",
                10000
            )
        )


    print(
        "=============================================="
    )

    print(
        "🧪 ALEX VISION LAB"
    )

    print(
        "🧠 SmolVLM-256M"
    )

    print(
        "=============================================="
    )

    print(
        "Modelo:",
        MODEL
    )

    print(
        "Porta:",
        porta
    )


    app.run(

        host="0.0.0.0",

        port=porta,

        threaded=True,

    )

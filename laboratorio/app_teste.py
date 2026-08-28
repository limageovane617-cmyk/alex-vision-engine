from flask import Flask, render_template_string, jsonify
import os
import shutil
import subprocess
import threading
import time
import signal
import queue


app = Flask(__name__)

MODEL = "ggml-org/SmolVLM-256M-Instruct-GGUF:Q8_0"

# ============================================================
# CONFIGURAÇÕES DO TESTE
# ============================================================

# Agora o limite é 30 minutos.
# Importante: o relógio não depende da saída do processo.
LIMITE_SEGUNDOS = 1800

# Quantidade máxima de saída guardada na memória.
MAX_OUTPUT = 50000

# ============================================================
# CONTROLE DO TESTE EM SEGUNDO PLANO
# ============================================================

job_lock = threading.Lock()

job = {
    "status": "idle",
    "success": False,
    "output": "",
    "started_at": None,
    "finished_at": None,
    "pid": None,
    "mensagem": "",
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

🟢 llama.cpp encontrado!

<br><br>

<code>{{ llama }}</code>

</div>

{% else %}

<div class="status vermelho">

🔴 llama.cpp não encontrado.

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
O modelo será carregado em segundo plano.
</p>

<p class="pequeno">
⏱️ Limite de segurança: 30 minutos.
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

3️⃣ Acompanhar o processo sem timeout

<br>

4️⃣ Mostrar o resultado real

<br>

5️⃣ Depois testar imagens

</div>

</div>


</div>


<script>

let monitorando = false;


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
        "🟡 Iniciando o carregamento do SmolVLM...";


    tempo.innerText = "";

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


        monitorando =
            true;


        status.className =
            "status amarelo";

        status.innerText =
            "🟡 Processo iniciado. O modelo está sendo carregado em segundo plano...";


        acompanhar();

    }

    catch (erro) {

        status.className =
            "status vermelho";

        status.innerText =
            "🔴 Erro ao iniciar o teste: " + erro;


        botao.disabled =
            false;

        botao.innerText =
            "🧠 Carregar SmolVLM";

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
                "/status",
                {
                    cache: "no-store"
                }
            );


        const dados =
            await resposta.json();


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
                dados.tempo || 0;


            const minutos =
                Math.floor(
                    segundos / 60
                );


            const restante =
                segundos % 60;


            status.className =
                "status amarelo";


            status.innerText =
                "🟡 SmolVLM carregando...";


            tempo.innerText =
                "⏱️ " +
                minutos +
                "m " +
                String(restante).padStart(2, "0") +
                "s";


            if (dados.mensagem) {

                status.innerText +=
                    "\\n" +
                    dados.mensagem;

            }


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

            monitorando =
                false;


            status.className =
                "status verde";


            status.innerText =
                "🟢 Processo concluído com sucesso!";


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

            monitorando =
                false;


            status.className =
                "status vermelho";


            status.innerText =
                "🔴 O processo terminou com erro.";


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

            monitorando =
                false;


            status.className =
                "status cinza";


            status.innerText =
                "⏸️ Aguardando início do teste.";


            tempo.innerText =
                "";


            liberarBotao();

            return;
        }


        setTimeout(
            acompanhar,
            2000
        );

    }

    catch (erro) {

        document.getElementById(
            "status"
        ).className =
            "status vermelho";


        document.getElementById(
            "status"
        ).innerText =
            "🔴 Falha temporária ao consultar o processo. Tentando novamente...";


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
        texto.trim() === ""
    ) {

        return;
    }


    resultado.style.display =
        "block";


    resultado.innerText =
        texto;

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
        segundos % 60;


    return (
        minutos +
        "m " +
        String(
            segundosRestantes
        ).padStart(2, "0") +
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
        f"./bin/{nome}",
        f"./{nome}",
        f"./llama.cpp/{nome}",
        f"./llama.cpp/build/bin/{nome}",
        f"./llama.cpp/build/bin/Release/{nome}",
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

def adicionar_saida(texto):

    if not texto:
        return


    with job_lock:

        atual = job.get(
            "output",
            ""
        )


        novo = atual + texto


        job["output"] = novo[-MAX_OUTPUT:]


# ============================================================
# LEITOR DA SAÍDA DO PROCESSO
#
# IMPORTANTE:
# Essa função roda separadamente.
#
# Assim o watchdog NÃO fica preso em readline().
# ============================================================

def ler_saida(processo, fila):

    try:

        while True:

            linha = processo.stdout.readline()


            if linha == "":
                break


            fila.put(linha)

    except Exception as erro:

        fila.put(
            "\n❌ Erro no leitor de saída: "
            + str(erro)
            + "\n"
        )


# ============================================================
# ENCERRAR PROCESSO COM SEGURANÇA
# ============================================================

def encerrar_processo(processo):

    if processo is None:
        return


    try:

        if processo.poll() is not None:
            return


        # Linux / Render:
        # tenta encerrar todo o grupo de processos.

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


        # Espera alguns segundos.

        try:

            processo.wait(
                timeout=8
            )

        except subprocess.TimeoutExpired:

            try:

                os.killpg(
                    os.getpgid(
                        processo.pid
                    ),
                    signal.SIGKILL
                )

            except Exception:

                try:
                    processo.kill()
                except Exception:
                    pass

    except Exception:
        pass


# ============================================================
# EXECUÇÃO EM SEGUNDO PLANO
# ============================================================

def executar_em_segundo_plano(caminho):

    global processo_atual


    # --------------------------------------------------------
    # COMANDO
    # --------------------------------------------------------

    comando = [
        caminho,
        "-hf",
        MODEL,
        "-p",
        "Olá Alex. Responda apenas: modelo carregado.",
        "-n",
        "16",
    ]


    inicio = time.time()


    try:

        with job_lock:

            job["status"] = "running"

            job["success"] = False

            job["output"] = ""

            job["started_at"] = inicio

            job["finished_at"] = None

            job["pid"] = None

            job["mensagem"] = (
                "🟡 llama.cpp iniciou o processo..."
            )


        # ----------------------------------------------------
        # INICIAR PROCESSO
        #
        # Não usamos timeout no Popen.
        # O nosso watchdog controla o tempo.
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

            job["mensagem"] = (
                "🟡 Processo ativo. "
                "Aguardando carregamento do modelo..."
            )


        # ----------------------------------------------------
        # FILA DE SAÍDA
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # WATCHDOG
        #
        # Esse loop nunca fica preso em readline().
        # ----------------------------------------------------

        while True:

            agora =
                time.time()


            tempo_decorrido =
                agora - inicio


            # ------------------------------------------------
            # DRENAR SAÍDA DISPONÍVEL
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
            # PROCESSO TERMINOU?
            # ------------------------------------------------

            retorno =
                processo.poll()


            if retorno is not None:

                # Drena o restante.

                while True:

                    try:

                        linha =
                            fila.get_nowait()

                    except queue.Empty:

                        break


                    adicionar_saida(
                        linha
                    )


                # Aguarda o leitor finalizar.

                try:

                    leitor.join(
                        timeout=2
                    )

                except Exception:

                    pass


                with job_lock:

                    job["finished_at"] =
                        time.time()

                    job["pid"] =
                        None


                texto_final = ""


                with job_lock:

                    texto_final =
                        job["output"]


                # --------------------------------------------
                # SUCESSO
                # --------------------------------------------

                if retorno == 0:

                    with job_lock:

                        job["status"] =
                            "success"

                        job["success"] =
                            True

                        job["mensagem"] =
                            "🟢 llama.cpp terminou normalmente."

                        job["pid"] =
                            None


                # --------------------------------------------
                # ERRO
                # --------------------------------------------

                else:

                    mensagem_erro = (
                        "🔴 llama.cpp encerrou com "
                        "código de saída: "
                        + str(retorno)
                    )


                    with job_lock:

                        job["status"] =
                            "error"

                        job["success"] =
                            False

                        job["mensagem"] =
                            mensagem_erro

                        job["output"] = (
                            mensagem_erro
                            + "\n\n"
                            + texto_final
                        )[-MAX_OUTPUT:]

                        job["pid"] =
                            None


                processo_atual =
                    None


                return


            # ------------------------------------------------
            # TIMEOUT REAL
            # ------------------------------------------------

            if tempo_decorrido >= LIMITE_SEGUNDOS:

                mensagem_timeout = (
                    "\n\n"
                    "⏱️ LIMITE DE 30 MINUTOS ATINGIDO.\n"
                    "O processo foi encerrado pelo laboratório "
                    "porque não terminou dentro do tempo máximo.\n"
                )


                adicionar_saida(
                    mensagem_timeout
                )


                # Mata o processo.

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

                    job["mensagem"] =
                        "⏱️ Timeout de 30 minutos."


                processo_atual =
                    None


                return


            # ------------------------------------------------
            # ATUALIZA MENSAGEM
            # ------------------------------------------------

            minutos =
                int(
                    tempo_decorrido // 60
                )


            segundos =
                int(
                    tempo_decorrido % 60
                )


            with job_lock:

                job["mensagem"] = (
                    "🟡 Carregando SmolVLM... "
                    + str(minutos)
                    + "m "
                    + str(segundos)
                    + "s"
                )


            # ------------------------------------------------
            # PEQUENA PAUSA
            # ------------------------------------------------

            time.sleep(
                0.25
            )


    except Exception as erro:

        texto_erro = (
            "❌ Erro ao executar llama.cpp:\n\n"
            + str(erro)
        )


        try:

            if processo_atual:

                encerrar_processo(
                    processo_atual
                )

        except Exception:

            pass


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

            job["mensagem"] =
                "🔴 Erro interno do laboratório."


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
                "llama-cli não foi encontrado."

        })


    with job_lock:

        if job["status"] in (
            "running",
            "starting"
        ):

            return jsonify({

                "ok": False,

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

        job["mensagem"] =
            "🟡 Preparando llama.cpp..."


    thread =
        threading.Thread(

            target=executar_em_segundo_plano,

            args=(llama,),

            daemon=True,
        )


    thread.start()


    return jsonify({

        "ok": True,

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


    tempo =
        0


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
                    fim -
                    dados["started_at"]
                )
            )


    dados["tempo"] =
        tempo


    # Nunca devolver None para o frontend.

    if dados.get("output") is None:

        dados["output"] =
            ""


    if dados.get("mensagem") is None:

        dados["mensagem"] =
            ""


    return jsonify(
        dados
    )


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

    porta =
        int(
            os.environ.get(
                "PORT",
                10000
            )
        )


    app.run(

        host="0.0.0.0",

        port=porta,

        threaded=True,

    )

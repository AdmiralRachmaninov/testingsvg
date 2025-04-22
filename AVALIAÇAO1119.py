import network
import socket
import ujson
import time
from machine import Pin, DAC

SSID = "Aegis2.4GHz"
PASSWORD = "Strudel#22"


dac = DAC(Pin(25))


sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(SSID, PASSWORD)

print("Conectando ao Wi-Fi...")
start = time.time()
while not sta.isconnected():
    if time.time() - start > 10:
        raise RuntimeError("Erro ao conectar-se ao Wi-Fi.")
    time.sleep(0.1)

print("Conectado! IP:", sta.ifconfig()[0])

def html_page():
    return """
<!DOCTYPE html>
<html lang="pt">

<head>
    <title>Sistema de Controle Hidráulico</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #f0f4f7;
            font-family: 'Segoe UI', sans-serif;
        }

        .main-container {
            position: relative;
            width: 800px;
            height: 600px;
        }

        .system-svg {
            width: 150%;
            height: 200%;
            background: url('https://raw.githubusercontent.com/AdmiralRachmaninov/testingsvg/d03d23ea4dcd2a3e15048128845e1d4c0fa63e26/svgfinal2.svg');
            background-size: contain;
            background-repeat: no-repeat;
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
        }

        .control-panel {
            position: fixed;
            top: 15%;
            right: 75%;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            width: 220px;
            backdrop-filter: blur(5px);
            animation: panelEntry 0.8s ease-out;
        }

        .dac-slider {
            width: 100%;
            margin: 15px 0;
            -webkit-appearance: none;
            height: 8px;
            border-radius: 4px;
            background: #e0e5ec;
            outline: none;
            opacity: 0.9;
            transition: opacity 0.2s;
        }

        .dac-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #2196F3;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .value-display {
            text-align: center;
            margin: 15px 0;
            font-size: 1.1em;
            color: #2c3e50;
        }

        .value-number {
            font-size: 1.4em;
            font-weight: 600;
            color: #2196F3;
            text-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
        }

        @keyframes panelEntry {
            from {
                transform: translateY(20px);
                opacity: 0;
            }

            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .status-led {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-left: 10px;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.5);
            }

            70% {
                box-shadow: 0 0 0 8px rgba(33, 150, 243, 0);
            }

            100% {
                box-shadow: 0 0 0 0 rgba(33, 150, 243, 0);
            }
        }
        <style>
    /* ... (outros estilos) ... */

    /* ============================================= */
    /* === AJUSTES ESPECÍFICOS PARA MODO RETRATO === */
    @media (orientation: portrait) {
        .main-container {
            width: 100vw!important;
            height: 100vh!important;
            padding: 0!important;
        }

        .system-svg {
            width: 100%!important;
            height: 60vh!important;  /* Reduz altura da imagem */
            position: absolute;
            top: 5vh;
        }

        .control-panel {
            width: 85%!important;
            right: 50%!important;
            left: auto!important;
            top: 65vh!important;  /* Posiciona abaixo da imagem */
            transform: translateX(50%)!important;  /* Centraliza */
            padding: 15px!important;
        }

        /* Aumenta elementos para toque */
        .dac-slider {
            height: 10px!important;
            margin: 25px 0!important;
        }

        .dac-slider::-webkit-slider-thumb {
            width: 28px!important;
            height: 28px!important;
        }

        .value-display {
            font-size: 1.1em!important;
            margin: 20px 0!important;
        }
    }
     @media (max-width: 600px) {
        .main-container {
            width: 100%!important;
            height: auto!important;
            padding: 10px;
        }

        .control-panel {
            width: 90%!important;
            right: 5%!important;
            left: auto!important;
            top: 10%!important;
            transform: none!important;
        }

        .system-svg {
            width: 100%!important;
            height: auto!important;
        }

        .value-number {
            font-size: 1.2em!important;
        }
    }
    </style>
</head>

<body>
    <div class="main-container">
        <div class="system-svg"></div>

        <!-- Painel de Controle Flutuante -->
        <div class="control-panel">
            <h3 style="color: #2196F3; margin-bottom: 20px;">
                Controle DAC
                <span class="status-led"></span>
            </h3>

            <input type="range" min="0" max="255" value="0" class="dac-slider" id="dacSlider"
                oninput="updateDAC(this.value)">

            <div class="value-display">
                <div>Frequência:</div>
                <span class="value-number" id="freq">0</span> Hz
            </div>

            <div class="value-display">
                <div>Vazão:</div>
                <span class="value-number" id="vazao">0</span> L/h
            </div>
        </div>
    </div>

    <script>
        let updateTimeout;
        const statusLed = document.querySelector('.status-led');

        function updateDAC(value) {
            // Feedback visual imediato
            statusLed.style.background = '#ff9800';
            document.getElementById('freq').textContent = (value / 255 * 60).toFixed(1);
            document.getElementById('vazao').textContent = (value / 255 * 38).toFixed(1);

            // Debounce para evitar flood de requisições
            clearTimeout(updateTimeout);
            updateTimeout = setTimeout(() => {
                const xhr = new XMLHttpRequest();
                xhr.open("GET", "/update?dac=" + value, true);

                xhr.onload = function () {
                    statusLed.style.background = '#4CAF50';
                    const response = JSON.parse(xhr.responseText);
                    document.getElementById('freq').textContent = response.freq.toFixed(1);
                    document.getElementById('vazao').textContent = response.vazao.toFixed(1);
                };

                xhr.onerror = function () {
                    statusLed.style.background = '#f44336';
                };

                xhr.send();
            }, 150);
        }
    </script>
</body>

</html>
"""
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("Servidor HTTP iniciado em:", addr)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()

        if "GET /favicon.ico" in request:
            conn.send("HTTP/1.1 204 No Content\r\n\r\n")
            conn.close()
            continue

        if "/update?dac=" in request:
            try:
                val = int(request.split("/update?dac=")[1].split(" ")[0])
                val = max(0, min(255, val))
                dac.write(val)
                freq = (val / 255) * 60
                vazao = (val / 255) * 38
                resp_json = ujson.dumps({"freq": freq, "vazao": vazao})
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
                conn.send(resp_json)
                conn.close()
                continue
            except Exception as e:
                print("Erro no update:", e)

        header = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n"
        response = header + html_page()
        conn.send(response.encode('utf-8')) 
        conn.close()

    except Exception as e:
        print("Erro geral:", e)
        conn.close()
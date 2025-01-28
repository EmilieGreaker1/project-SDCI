from flask import Flask, render_template, request, jsonify, Response
import threading
import time
import json
import sys

# Import your main function
from main import (
    startMonitoring, 
    startAdaptation, 
    stopMonitoring, 
    stopAdaptation, 
    startMapekLoop, 
    stopMapekLoop, 
    runMapekLoop
)

app = Flask(__name__)
stop_monitoring = True
main_stop = True

@app.route("/")
def index():
    return render_template("index.html")

mape_monitor = None

@app.route("/start/mape", methods=["POST"])
def startMape():
    global mape_monitor

    mape_monitor = startMapekLoop()
    runMapekLoop(mape_monitor)

@app.route("/stop/mape", methods=["POST"])
def stopMape():
    global mape_monitor
 
    stopMapekLoop(mape_monitor)
    return jsonify({"status": "success"})

@app.route("/stream_mape")
def stream_mape():
    global mape_monitor
    print("mape_monitor: ", mape_monitor)
    def generate():
        while mape_monitor:  # Continuously stream while monitoring is active
            time.sleep(0.2)  # Simulate checking every 1 second
            data = {
                'Flow Reduction Service Up': mape_monitor.frservice_up,
                'CPU GI Usage Percentage': mape_monitor.usageCPU_GI,
                'Alerts': mape_monitor.alerts
            }
            yield f"data: {json.dumps(data)}\n\n"  # Stream the data to the client
    return Response(generate(), content_type='text/event-stream')


monitor = None

@app.route("/toggle/monitoring", methods=["POST"])
def toggleMonitoring():
    global monitor

    data = request.get_json()
    stop_monitoring = data.get("stop_monitoring")

    if stop_monitoring == 'true':
        monitor = startMonitoring()
    else:
        stopMonitoring(monitor)
    
    return jsonify({"status": "success", "stop_monitoring": stop_monitoring, "monitor_frservice_up": monitor.frservice_up})

@app.route("/stream_monitor")
def stream_monitor():
    global monitor
    def generate():
        while monitor:  # Continuously stream while monitoring is active
            time.sleep(0.2)  # Simulate checking every 1 second
            data = {
                'Flow Reduction Service Up': monitor.frservice_up,
                'CPU GI Usage Percentage': monitor.usageCPU_GI,
                'Alerts': monitor.alerts
            }
            yield f"data: {json.dumps(data)}\n\n"  # Stream the data to the client
    return Response(generate(), content_type='text/event-stream')

@app.route("/toggle/adaptation", methods=["POST"])
def toggleAdaptation():

    data = request.get_json()
    stop_adaptation = data.get("stop_adaptation")

    if stop_adaptation == 'true':
        startAdaptation()
    else:
        stopAdaptation()

    return jsonify({"status": "success", "stop_adaptation": stop_adaptation})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

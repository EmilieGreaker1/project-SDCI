#a simple python program to implement the MAPE loop  using one thread for just the Monitor phase
# no other threads are used for Analyze, Plan, Execute phases
# the Monitor phase is implemented in a separate thread
# the monitor raises alerts towards the main program
# when receving an alert, the main program executes in sequence the Analyze, Plan, Execute phases
# the main program always waits for alerts from the monitor
# the monitor runs continuously in the background
# the main program runs in a loop
# the monitor is implemented as a separate class

import time
import threading
import random
import sys
import subprocess

def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

# the analyze, plan, execute phases are implemented in separate functions
def analyze():
    print("Analyze")
    time.sleep(1)

def plan(RFC):
    if RFC["saturation"] and not RFC["frservice"]:
        return "reduce flow"
    elif not RFC["saturation"] and RFC["frservice"]:
        return "reset flow"
    else:
        return None
        
def execute(executionPlan):
    if executionPlan == "reduce flow":
        # We deploy a pod of our flow reduction service
        run_command("kubectl scale --replicas=1 deployment/sdci-frservice")
        # We apply the routing virtual service to reroute the data packages from the non-critical zones to our flow reduction service
        run_command("kubectl apply -f kubernetes/sdci_routing_virtualservice.yaml")
    elif executionPlan == "reset flow":
        # We delete the routing virtual service to get back to the initial routing
        run_command("kubectl delete virtualservice sdci-gf-routing")
        # We stop deploying our flow reduction service
        run_command("kubectl scale --replicas=0 deployment/sdci-frservice")


# the Monitor class
class Monitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.alerts = 0
        self.running = True

    def run(self):
        while self.running:
            # generate random alerts
            if random.randint(0, 100) < 10:
                self.alerts += 1
                print("Alerts: %d" % self.alerts)
            time.sleep(1)

    def stop(self):
        self.running = False

# the main program
def main():
    monitor = Monitor()
    monitor.start()
    up=True

    RFC = {
    "saturation": True,
    "frservice": False
    }

    while True:
        #while monitor.alerts == 0:
        #    time.sleep(1)
        #print("Analyze")
        #RFC = analyze()

        if up :
            RFC["saturation"] = True 
            RFC["frservice"] = False
        else :
            RFC["saturation"] = False 
            RFC["frservice"] = True


        print("Plan")
        executionPlan = plan(RFC)

        print("Execute")
        execute(executionPlan)

        #monitor.alerts -= 1
        print("IM UP ",up)
        up = not up
        time.sleep(100)


    monitor.stop()
    monitor.join()

if __name__ == "__main__":
    main()
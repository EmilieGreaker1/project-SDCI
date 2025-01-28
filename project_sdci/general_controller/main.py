# a simple python program to implement the MAPE loop  using one thread for just the Monitor phase

import time
import threading
import random
import sys
import io
import subprocess
from kubernetes import client, config

log_stream = io.StringIO()
sys.stdout = log_stream

# Function to run a command in shell
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

# Given a monitor instance, this function analyzes and returns an RFC
def analyze(monitor):
    RFC = {}

    # If the CPU usage of the Intermediate Gateway is greater than 80%, the GI is saturated
    if monitor.usageCPU_GI > 80:
        RFC["saturation"] = True
    else:
        RFC["saturation"] = False

    # We also return the status of the Flow Reduction Service
    RFC["frservice"] = monitor.frservice_up

    return RFC

# Given a RFC, we determine the action to take
def plan(RFC):
    # If the Intermediate Gateway is saturated and the Flow Reduction Service is not deployed, we reduce the flow
    if RFC["saturation"] and not RFC["frservice"]:
        return "reduce flow"
    # If the Intermediate Gateway is not saturated and the Flow Reduction Service is deployed, we reset the initial flow
    elif not RFC["saturation"] and RFC["frservice"]:
        return "reset flow"
    # Else, we don't do anything
    else:
        return None
        
# Given an execution plan, we apply it
def execute(executionPlan):
    if executionPlan == "reduce flow":
        # We deploy a pod of our Flow Reduction Service
        run_command("kubectl scale --replicas=1 deployment/sdci-frservice")
        # We apply the routing virtual service to reroute the data packages from the non-critical zones to our flow reduction service
        run_command("kubectl apply -f ../kubernetes/sdci_routing_virtualservice.yaml")

    elif executionPlan == "reset flow":
        # We delete the routing virtual service to get back to the initial routing
        run_command("kubectl delete virtualservice sdci-gf-routing")
        # We stop deploying our flow reduction service
        run_command("kubectl scale --replicas=0 deployment/sdci-frservice")

# The Monitor phase is a separate class implemented in a separate thread, it raises alerts
class Monitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # Boolean returning whether the Flow Reduction Service is up
        self.frservice_up = None
        # The CPU Usage Percentage of the Intermediate Gateway
        self.usageCPU_GI = 0
        # The number of alerts we raise
        self.alerts = 0
        # Whether our thread is running
        self.running = True
        
        # Load Kubernetes configuration to interact with Kubernetes API
        config.load_kube_config()

    # Returns the CPU Usage Percentage of a Deployment
    def get_deployment_cpu_percentage(self, deployment_name, namespace="default"):
        try:
            # Get the deployment to get the label selector
            apps_v1_api = client.AppsV1Api()
            deployment = apps_v1_api.read_namespaced_deployment(deployment_name, namespace)
            
            # Get the label selector
            label_selector = ",".join(
                [f"{key}={value}" for key, value in deployment.spec.selector.match_labels.items()]
            )

            # Get the metrics for pods in the namespace
            custom_api = client.CustomObjectsApi()
            metrics = custom_api.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods"
            )

            # Get pods of the deployment and calculate total CPU usage
            total_cpu_usage_millicores = 0
            for pod in metrics["items"]:
                # Check if pod matches the deployment's label selector
                if all(label in pod["metadata"]["labels"].items() for label in deployment.spec.selector.match_labels.items()):
                    for container in pod["containers"]:
                        # Get CPU Usage
                        cpu_usage = container["usage"]["cpu"]

                        # Convert to millicores
                        if cpu_usage.endswith("n"):  
                            total_cpu_usage_millicores += int(cpu_usage[:-1]) / 1_000_000
                        elif cpu_usage.endswith("m"):  
                            total_cpu_usage_millicores += int(cpu_usage[:-1])
                        else: 
                            total_cpu_usage_millicores += int(cpu_usage) * 1000

            # Get the total requested CPU for the deployment
            total_requested_cpu_millicores = 0
            for container in deployment.spec.template.spec.containers:
                if container.resources.requests and "cpu" in container.resources.requests:
                    requested_cpu = container.resources.requests["cpu"]
                    if requested_cpu.endswith("n"): 
                        total_requested_cpu_millicores += int(requested_cpu[:-1]) / 1_000_000
                    elif requested_cpu.endswith("m"):  
                        total_requested_cpu_millicores += int(requested_cpu[:-1])
                    else: 
                        total_requested_cpu_millicores += int(requested_cpu) * 1000

            # Calculate CPU usage percentage
            if total_requested_cpu_millicores > 0:
                cpu_usage_percentage = (total_cpu_usage_millicores / total_requested_cpu_millicores) * 100
                return cpu_usage_percentage
            else:
                print("Error: Requested CPU for the deployment is zero.")
                return 0
        except Exception as e:
            print(f"Error retrieving CPU percentage for deployment {deployment_name}: {e}")
            return 0

    # Returns whether a deployment has at least one pod ready
    def is_deployment_up(self, deployment_name, namespace="default"):
        # Get the Deployment
        apps_v1_api = client.AppsV1Api()
        deployment = apps_v1_api.read_namespaced_deployment(deployment_name, namespace=namespace)

        # Check if at least one pod is available
        if deployment.status and deployment.status.available_replicas and deployment.status.available_replicas > 0:
            return True
        else:
            return False

    # Increments alerts if CPU Usage Percentage or Flow Reduction Service status changed
    def run(self):
        # Initialize those attributes
        pastusageCPU_GI = self.get_deployment_cpu_percentage("sdci-gi")
        past_frservice_up = False

        while self.running:
            # Updata data
            self.usageCPU_GI = self.get_deployment_cpu_percentage("sdci-gi")
            print(f"\nUsage CPU percentage : {self.usageCPU_GI}")

            self.frservice_up = self.is_deployment_up("sdci-frservice")
            print(f"Service 'Flow Reduction' est {'actif' if self.frservice_up else 'inactif'}")

            # If it changed, alerts increments
            if pastusageCPU_GI != self.usageCPU_GI : 
                self.alerts += 1
                print(f"- usageCPU_GI has changed: {self.usageCPU_GI}")

            if past_frservice_up != self.frservice_up:
                self.alerts += 1
                print(f"- service status has changed: {self.frservice_up}")
            print(f"Alerts: {self.alerts}")


            # Remember past data
            pastusageCPU_GI = self.usageCPU_GI 
            past_frservice_up = self.frservice_up 
            time.sleep(0.2)

    # Stop Monitor
    def stop(self):
        self.running = False

# Start monitoring, returns the monitor instance
def startMonitoring():
    monitor = Monitor()
    monitor.start()
    return monitor

# Stop monitoring thread
def stopMonitoring(monitor):
    monitor.stop()
    monitor.join()   

# Start adaptation, reduces flow
def startAdaptation():
    execute("reduce flow")

# Stop adaptation, resets flow
def stopAdaptation():
    execute("reset flow")

# Start mapek loop, returns monitor
def startMapekLoop():
    monitor = startMonitoring()
    return monitor

# Run mapek loop
def runMapekLoop(monitor):
    while monitor.running:
        # If no alert from the monitor, we wait for 1 second before checking again if we have new alerts
        while monitor.alerts == 0:
            time.sleep(0.1)

        # If we have an alert from the monitor, we start the process of analyzing/planning/executing
        print("Analyze")
        RFC = analyze(monitor)

        print("Plan")
        executionPlan = plan(RFC)

        print("Execute")
        execute(executionPlan)

        time.sleep(1)
        # We have dealt with one alert, we keep dealing with the other alerts
        monitor.alerts -= 1
        print("What Action Am I Taking ? ",executionPlan)

# Stop mapek loop
def stopMapekLoop(monitor):
    stopMonitoring(monitor)

# Main program
main_stop = False
def main():
    monitor = startMapekLoop()
    runMapekLoop(monitor)

    stopMapekLoop(monitor)

if __name__ == "__main__":
    main()
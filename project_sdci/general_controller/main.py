#a simple python program to implement the MAPE loop  using one thread for just the Monitor phase
# no other threads are used for Analyze, Plan, Execute phases
# the Monitor phase is implemented in a separate thread
# the monitor raises alerts towards the main program
# when receving an alert, the main program executes in sequence the Analyze, Plan, Execute phases
# the main program always waits for alerts from the monitor
# the monitor runs continuously in the background
# the main program runs in a loop
# the monitor is implemented as a separate class
# the analyze, plan, execute phases are implemented in separate functions

import time
import threading
import random
import sys
import subprocess
from kubernetes import client, config

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

def analyze(monitor_instance):
    RFC = {}
    with monitor_instance.lock:
        if monitor_instance.usageCPU_GI > 80:
            RFC["saturation"] = True
        else:
            RFC["saturation"] = False

        RFC["frservice"] = monitor_instance.frservice_up

    return RFC

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

class Monitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.frservice_up = None
        self.usageCPU_GI = 0
        self.alerts = 0
        self.running = True
        self.lock = threading.Lock()
        
        config.load_kube_config()

    def get_deployment_cpu_percentage(self, deployment_name, namespace="default"):
        try:
            # Get the deployment to retrieve the label selector
            apps_v1_api = client.AppsV1Api()
            deployment = apps_v1_api.read_namespaced_deployment(deployment_name, namespace)
            
            # Get the label selector from the deployment
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

            # Filter pods belonging to the deployment and calculate total CPU usage
            total_cpu_usage_millicores = 0
            for pod in metrics["items"]:
                # Check if the pod matches the deployment's label selector
                if all(label in pod["metadata"]["labels"].items() for label in deployment.spec.selector.match_labels.items()):
                    for container in pod["containers"]:
                        cpu_usage = container["usage"]["cpu"]
                        
                        # Convert CPU usage to millicores
                        if cpu_usage.endswith("n"):  # Nanocores to millicores
                            total_cpu_usage_millicores += int(cpu_usage[:-1]) / 1_000_000
                        elif cpu_usage.endswith("m"):  # Millicores
                            total_cpu_usage_millicores += int(cpu_usage[:-1])
                        else:  # Cores to millicores
                            total_cpu_usage_millicores += int(cpu_usage) * 1000

            # Get the total requested CPU for the deployment
            total_requested_cpu_millicores = 0
            for container in deployment.spec.template.spec.containers:
                if container.resources.requests and "cpu" in container.resources.requests:
                    requested_cpu = container.resources.requests["cpu"]
                    if requested_cpu.endswith("n"):  # Nanocores to millicores
                        total_requested_cpu_millicores += int(requested_cpu[:-1]) / 1_000_000
                    elif requested_cpu.endswith("m"):  # Millicores
                        total_requested_cpu_millicores += int(requested_cpu[:-1])
                    else:  # Cores to millicores
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

    def is_deployment_up(self, deployment_name, namespace="default"):
        # Get the Deployment
        apps_v1_api = client.AppsV1Api()  
        deployment = apps_v1_api.read_namespaced_deployment(deployment_name, namespace=namespace)

        # Check if at least one pod is available
        if deployment.status and deployment.status.available_replicas and deployment.status.available_replicas > 0:
            return True
        else:
            return False

    def run(self):
        pastusageCPU_GI = 0
        past_frservice_up = None

        while self.running:
            with self.lock:
                # Updata data
                self.usageCPU_GI = self.get_deployment_cpu_percentage("sdci-gi")
                print(f"Usage CPU total : {self.usageCPU_GI} cores")

                self.frservice_up = self.is_deployment_up("sdci-frservice")
                print(f"Service 'Flow Reduction' est {'actif' if self.frservice_up else 'inactif'}")

                # If it changed, alert
                if pastusageCPU_GI != self.usageCPU_GI : 
                    self.alerts += 1
                    print(f"- service status has changed: {self.frservice_up}")

                if past_frservice_up != self.frservice_up:
                    self.alerts += 1
                    print(f"- service status has changed: {self.frservice_up}")
                print(f"Alerts: {self.alerts}")


                # Remember past data
                pastusageCPU_GI = self.usageCPU_GI 
                past_frservice_up = self.frservice_up 
                time.sleep(5)

    def stop(self):
        self.running = False

# the main program
def main():
    monitor = Monitor()
    monitor.start()

    while True:
        # If no alert from the monitor, we wait for 3 seconds before checking again if we have new alerts
        while monitor.alerts == 0:
            time.sleep(3)

        # If we have an alert from the monitor, we start the process of analyzing/planning/executing
        print("Analyze")
        RFC = analyze(monitor)

        print("Plan")
        executionPlan = plan(RFC)

        print("Execute")
        execute(executionPlan)

        # We have dealt with one alert, we keep dealing with the other alerts
        monitor.alerts -= 1
        print("What Action Am I Taking ? ",executionPlan)

    monitor.stop()
    monitor.join()

if __name__ == "__main__":
    main()
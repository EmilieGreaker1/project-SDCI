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

# the analyze, plan, execute phases are implemented in separate functions
def analyze():
    print("Analyze")
    time.sleep(1)

def plan():
    print("Plan")
    time.sleep(1)

def execute():
    print("Execute")
    time.sleep(1)   

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
    while True:
        while monitor.alerts == 0:
            time.sleep(1)
        print("Analyze")
        time.sleep(1)
        print("Plan")
        time.sleep(1)
        print("Execute")
        time.sleep(1)
        monitor.alerts -= 1
    monitor.stop()
    monitor.join()

if __name__ == "__main__":
    main()
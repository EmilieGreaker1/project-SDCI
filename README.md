Presented by Emilie GREAKER and Y-Quynh NGUYEN as our 5th year INSA Toulouse, SDCI minor project.

This project revolved around resolving an issue for an application architecture using Kubernetes and Istio. The mentioned issue for this specific project, was the saturation of the intermediate gateway.

This GitHub repository contains the code we deployed in our Kubernetes cluster on our OpenStack resources (consisting of a master and two workers). 
This includer dockerfiles for building the different dockerimages, the various YAML files for the Kubernetes deployments, 
clusterIPs and re-routing virtual service and the code for the general controller as well as the flow reduction service.

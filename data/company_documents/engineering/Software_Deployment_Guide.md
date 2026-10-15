# Nexus Engineering - Production CI/CD and Kubernetes Deployment Guide

## 1. GitOps Architecture & CI/CD Pipeline
Nexus uses a GitOps deployment strategy driven by GitHub Actions and ArgoCD. Every merge to the `main` branch triggers:
1. Automated unit and integration testing suite execution.
2. Static code analysis and dependency vulnerability scans (Trivy and SonarQube).
3. Multi-stage Docker image build pushed to AWS Elastic Container Registry (ECR) tagged with Git SHA.
4. ArgoCD syncs the updated image tag to the Kubernetes production cluster.

## 2. Kubernetes Cluster Topology (EKS 1.30)
Production microservices run on Amazon Elastic Kubernetes Service (EKS) across three Availability Zones (`us-west-2a`, `us-west-2b`, `us-west-2c`). Pods are governed by:
- Horizontal Pod Autoscaler (HPA) targeting 70% CPU and 80% memory utilization.
- Resource Requests: 500m CPU, 1Gi RAM; Limits: 2000m CPU, 4Gi RAM per pod.
- PodDisruptionBudgets (PDB) guaranteeing a minimum of 66% available pods during maintenance.

## 3. Canary Deployment Strategy
Deployments utilize progressive canary rollouts via Argo Rollouts:
- Phase 1: 10% traffic routed to canary pods for 15 minutes.
- Automated Analysis: Datadog metrics monitor HTTP 5xx error rates and P95 latency.
- Rollback Trigger: If HTTP 5xx error rate exceeds 0.5% or latency exceeds 450ms, the rollout is automatically aborted and traffic reverts 100% to stable pods.
- Phase 2: Traffic scales to 50% for 15 minutes, then promotes to 100%.

## 4. Secrets Management
Zero secrets are stored in Git. Application secrets are stored in HashiCorp Vault and injected into pods as ephemeral volumes using the Kubernetes External Secrets Operator (ESO).
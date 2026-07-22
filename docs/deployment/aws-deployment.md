# AWS Infrastructure Deployment Guide

This guide describes how to provision the Walter AI backend infrastructure on AWS using Terraform.

## Prerequisites
- Installed Terraform (>= 1.5.0)
- Installed AWS CLI with configured access keys
- A pre-created SSH Key Pair in your AWS account

## Provisioning Infrastructure
1. Navigate to the `terraform/` directory.
2. Copy `terraform.tfvars.example` to `terraform.tfvars` and update variables:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
3. Initialize Terraform:
   ```bash
   terraform init
   ```
4. Run validation and preview changes:
   ```bash
   terraform plan
   ```
5. Apply the plan to spin up resources:
   ```bash
   terraform apply
   ```
6. Save the output public IP returned by the CLI.

## Hosting App
Once provisioning is complete:
- SSH into the instance: `ssh -i /path/to/key.pem ubuntu@<instance_public_ip>`
- The EBS volume is mounted at `/data`.
- Place your `docker-compose.yml` on the instance and run `docker-compose up -d`, ensuring SQLite DB path resolves to `/data/walter-ai.db`.

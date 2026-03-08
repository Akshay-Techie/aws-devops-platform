# ============================================================
# terraform/environments/prod/outputs.tf
# Values printed after terraform apply
# ============================================================

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "Load Balancer DNS — open this in browser"
  value       = module.alb.alb_dns_name
}

output "master_public_ip" {
  description = "K8s master — SSH: ssh -i ~/.ssh/akshaytechie-key ubuntu@<this_ip>"
  value       = module.ec2.master_public_ip
}

output "worker_public_ip" {
  description = "K8s worker public IP"
  value       = module.ec2.worker_public_ip
}

output "ecr_image" {
  description = "Your ECR image URI — use this in Helm values"
  value       = "793433927733.dkr.ecr.ap-south-1.amazonaws.com/akshaytechie/aws-devops-platform:1.0"
}
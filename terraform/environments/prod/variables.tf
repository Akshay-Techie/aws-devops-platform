variable "project_name" {
  description = "Prefix for all resource names"
  type        = string
  default     = "akshaytechie"
}

variable "aws_region" {
  description = "AWS region Mumbai"
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZs in Mumbai"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "master_instance_type" {
  description = "EC2 type for K8s master"
  type        = string
  default     = "t3.medium"
}

variable "worker_instance_type" {
  description = "EC2 type for K8s worker"
  type        = string
  default     = "t3.medium"
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  sensitive   = true
}

variable "admin_cidr_blocks" {
  description = "IPs allowed SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
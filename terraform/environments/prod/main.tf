# ============================================================
# terraform/environments/prod/main.tf
# Root config — wires all modules together
# ============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Data Sources ────────────────────────────────────────────

data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── Locals ───────────────────────────────────────────────────

locals {
  common_tags = {
    Project     = var.project_name
    Environment = "production"
    ManagedBy   = "terraform"
    Owner       = "akshaytechie"
  }
}

# ── Module: VPC ──────────────────────────────────────────────

module "vpc" {
  source = "../../modules/vpc"

  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  common_tags          = local.common_tags
}

# ── Module: Security Groups ──────────────────────────────────

module "security_groups" {
  source = "../../modules/security-groups"

  project_name      = var.project_name
  vpc_id            = module.vpc.vpc_id
  vpc_cidr          = module.vpc.vpc_cidr
  admin_cidr_blocks = var.admin_cidr_blocks
  common_tags       = local.common_tags
}

# ── Module: EC2 ──────────────────────────────────────────────

module "ec2" {
  source = "../../modules/ec2"

  project_name         = var.project_name
  aws_region           = var.aws_region
  ami_id               = data.aws_ami.ubuntu.id
  master_instance_type = var.master_instance_type
  worker_instance_type = var.worker_instance_type
  private_subnet_ids   = module.vpc.private_subnet_ids
  public_subnet_ids    = module.vpc.public_subnet_ids
  k8s_master_sg_id     = module.security_groups.k8s_master_sg_id
  k8s_worker_sg_id     = module.security_groups.k8s_worker_sg_id
  ssh_public_key       = var.ssh_public_key
  common_tags          = local.common_tags
}

# ── Module: ALB ──────────────────────────────────────────────

module "alb" {
  source = "../../modules/alb"

  project_name        = var.project_name
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  alb_sg_id           = module.security_groups.alb_sg_id
  worker_instance_ids = module.ec2.worker_instance_ids
  common_tags         = local.common_tags
}
variable "project_name" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "ami_id" {
  type = string
}

variable "master_instance_type" {
  type = string
}

variable "worker_instance_type" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "k8s_master_sg_id" {
  type = string
}

variable "k8s_worker_sg_id" {
  type = string
}

variable "ssh_public_key" {
  type      = string
  sensitive = true
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
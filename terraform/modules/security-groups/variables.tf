variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "admin_cidr_blocks" {
  type = list(string)
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
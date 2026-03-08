output "alb_sg_id" {
  value = aws_security_group.alb.id
}

output "k8s_master_sg_id" {
  value = aws_security_group.k8s_master.id
}

output "k8s_worker_sg_id" {
  value = aws_security_group.k8s_worker.id
}
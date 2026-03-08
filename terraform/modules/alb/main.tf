# ============================================================
# terraform/modules/alb/main.tf
# Creates: ALB, Target Group, HTTP Listener, registers worker
# ============================================================

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [var.alb_sg_id]

  enable_deletion_protection = false

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-alb"
  })
}

# Target group — ALB routes traffic to worker node on port 30080
resource "aws_lb_target_group" "app" {
  name     = "${var.project_name}-tg"
  port     = 30080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = var.common_tags
}

# Register worker EC2 instance as a target
resource "aws_lb_target_group_attachment" "worker" {
  count            = length(var.worker_instance_ids)
  target_group_arn = aws_lb_target_group.app.arn
  target_id        = var.worker_instance_ids[count.index]
  port             = 30080
}

# HTTP listener — port 80 forwards to target group
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
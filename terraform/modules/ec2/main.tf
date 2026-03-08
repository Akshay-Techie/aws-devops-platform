# ============================================================
# terraform/modules/ec2/main.tf
# Creates: IAM role, Key Pair, Master EC2, Worker EC2
# ============================================================

# ── IAM Role ─────────────────────────────────────────────────
# Allows EC2 instances to pull from ECR without credentials
resource "aws_iam_role" "k8s_node" {
  name = "${var.project_name}-k8s-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.k8s_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.k8s_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "k8s_node" {
  name = "${var.project_name}-k8s-node-profile"
  role = aws_iam_role.k8s_node.name
}

# ── SSH Key Pair ─────────────────────────────────────────────
resource "aws_key_pair" "k8s" {
  key_name   = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

# ── Master Node ──────────────────────────────────────────────
resource "aws_instance" "master" {
  ami                    = var.ami_id
  instance_type          = var.master_instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [var.k8s_master_sg_id]
  iam_instance_profile   = aws_iam_instance_profile.k8s_node.name
  key_name               = aws_key_pair.k8s.key_name

  # Public IP so we can SSH directly to master
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  # Installs Docker, kubeadm, kubelet, kubectl on first boot
  user_data_base64 = base64encode(<<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y apt-transport-https ca-certificates curl

    # Install Docker
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu

    # Disable swap (required for Kubernetes)
    swapoff -a
    sed -i '/ swap / s/^/#/' /etc/fstab

    # Kernel modules for K8s networking
    modprobe overlay
    modprobe br_netfilter
    cat > /etc/sysctl.d/k8s.conf <<SYSCTL
    net.bridge.bridge-nf-call-iptables  = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.ipv4.ip_forward                 = 1
    SYSCTL
    sysctl --system

    # Install kubeadm kubelet kubectl
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | \
        gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
        https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" \
        > /etc/apt/sources.list.d/kubernetes.list
    apt-get update -y
    apt-get install -y kubelet kubeadm kubectl
    apt-mark hold kubelet kubeadm kubectl
    systemctl enable kubelet

    echo "MASTER NODE READY" > /tmp/setup-done.txt
  EOF
  )

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-k8s-master"
    Role = "master"
  })
}

# ── Worker Node ──────────────────────────────────────────────
resource "aws_instance" "worker" {
  ami                    = var.ami_id
  instance_type          = var.worker_instance_type
  subnet_id              = var.public_subnet_ids[1]
  vpc_security_group_ids = [var.k8s_worker_sg_id]
  iam_instance_profile   = aws_iam_instance_profile.k8s_node.name
  key_name               = aws_key_pair.k8s.key_name

  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  user_data_base64 = base64encode(<<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y apt-transport-https ca-certificates curl

    # Install Docker
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu

    # Disable swap
    swapoff -a
    sed -i '/ swap / s/^/#/' /etc/fstab

    # Kernel modules
    modprobe overlay
    modprobe br_netfilter
    cat > /etc/sysctl.d/k8s.conf <<SYSCTL
    net.bridge.bridge-nf-call-iptables  = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.ipv4.ip_forward                 = 1
    SYSCTL
    sysctl --system

    # Install kubeadm kubelet kubectl
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | \
        gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
        https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" \
        > /etc/apt/sources.list.d/kubernetes.list
    apt-get update -y
    apt-get install -y kubelet kubeadm kubectl
    apt-mark hold kubelet kubeadm kubectl
    systemctl enable kubelet

    echo "WORKER NODE READY" > /tmp/setup-done.txt
  EOF
  )

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-k8s-worker"
    Role = "worker"
  })
}
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "walter_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "walter-ai-vpc"
  }
}

resource "aws_internet_gateway" "walter_igw" {
  vpc_id = aws_vpc.walter_vpc.id
  tags = {
    Name = "walter-ai-igw"
  }
}

resource "aws_subnet" "walter_subnet" {
  vpc_id                  = aws_vpc.walter_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  tags = {
    Name = "walter-ai-subnet"
  }
}

resource "aws_route_table" "walter_rt" {
  vpc_id = aws_vpc.walter_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.walter_igw.id
  }
  tags = {
    Name = "walter-ai-rt"
  }
}

resource "aws_route_table_association" "walter_rta" {
  subnet_id      = aws_subnet.walter_subnet.id
  route_table_id = aws_route_table.walter_rt.id
}

resource "aws_security_group" "walter_sg" {
  name        = "walter-ai-sg"
  description = "Allow HTTP/HTTPS and SSH ingress"
  vpc_id      = aws_vpc.walter_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "walter-ai-sg"
  }
}

resource "aws_instance" "walter_instance" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS (x86_64) in us-east-1. Adjust if region varies.
  instance_type = var.instance_type
  subnet_id     = aws_subnet.walter_subnet.id
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.walter_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io docker-compose git
              systemctl start docker
              systemctl enable docker
              
              # Mount persistent EBS volume
              mkdir -p /data
              # Format volume only if it does not have a filesystem
              if ! blkid /dev/xvdf; then
                mkfs -t ext4 /dev/xvdf
              fi
              mount /dev/xvdf /data
              echo '/dev/xvdf /data ext4 defaults,nofail 0 2' >> /etc/fstab
              EOF

  tags = {
    Name = "walter-ai-backend"
  }
}

resource "aws_ebs_volume" "walter_volume" {
  availability_zone = aws_subnet.walter_subnet.availability_zone
  size              = 10 # 10 GB persistent storage for SQLite database
  type              = "gp3"
  tags = {
    Name = "walter-ai-db-volume"
  }
}

resource "aws_volume_attachment" "walter_volume_attach" {
  device_name = "/dev/sdh" # Will expose on Linux as /dev/xvdf or similar
  volume_id   = aws_ebs_volume.walter_volume.id
  instance_id = aws_instance.walter_instance.id
}

resource "aws_eip" "walter_eip" {
  domain = "vpc"
}

resource "aws_eip_association" "walter_eip_assoc" {
  instance_id   = aws_instance.walter_instance.id
  allocation_id = aws_eip.walter_eip.id
}


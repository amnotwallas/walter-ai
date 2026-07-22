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
              apt-get install -y docker.io docker-compose-plugin git
              systemctl start docker
              systemctl enable docker
              
              mkdir -p /data
              # Wait for EBS volume to attach
              VOLUME_DEV=""
              for i in {1..30}; do
                if [ -b /dev/xvdf ]; then
                  VOLUME_DEV="/dev/xvdf"
                  break
                elif [ -b /dev/nvme1n1 ]; then
                  VOLUME_DEV="/dev/nvme1n1"
                  break
                elif [ -b /dev/nvme2n1 ]; then
                  VOLUME_DEV="/dev/nvme2n1"
                  break
                fi
                sleep 2
              done

              if [ -n "$VOLUME_DEV" ]; then
                if ! blkid "$VOLUME_DEV"; then
                  mkfs -t ext4 "$VOLUME_DEV"
                fi
                mount "$VOLUME_DEV" /data
                echo "$VOLUME_DEV /data ext4 defaults,nofail 0 2" >> /etc/fstab
              fi
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
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.walter_volume.id
  instance_id = aws_instance.walter_instance.id
}

resource "aws_eip" "walter_eip" {
  domain = "vpc"
  tags = {
    Name = "walter-ai-eip"
  }
}

resource "aws_eip_association" "walter_eip_assoc" {
  instance_id   = aws_instance.walter_instance.id
  allocation_id = aws_eip.walter_eip.id
}


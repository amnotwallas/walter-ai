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

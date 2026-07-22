output "instance_public_ip" {
  value       = aws_eip.walter_eip.public_ip
  description = "Public IP address of the Walter AI backend instance"
}

from prompt_templates import (
    EC2_PROMPT, S3_PROMPT, RDS_PROMPT, LAMBDA_PROMPT, VPC_PROMPT,
    IAM_PROMPT, TERRAFORM_AWS_PROMPT, KUBERNETES_PROMPT, DOCKER_PROMPT
)

def ec2_terraform_prompt(instance_type, ami, subnet_id, security_group_id, region):
    """Generate EC2 Terraform configuration"""
    return f"""
resource "aws_instance" "example" {{
  ami           = "{ami}"
  instance_type = "{instance_type}"
  subnet_id     = {subnet_id}
  vpc_security_group_ids = [{security_group_id}]
  
  tags = {{
    Name = "ExampleInstance"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

provider "aws" {{
  region = "{region}"
}}
"""

def default_vpc_resources_prompt(region):
    """Generate default VPC resources Terraform configuration"""
    return f"""
resource "aws_vpc" "default" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name = "DefaultVPC"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

resource "aws_subnet" "default" {{
  vpc_id                  = aws_vpc.default.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "{region}a"
  map_public_ip_on_launch = true
  
  tags = {{
    Name = "DefaultSubnet"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

resource "aws_internet_gateway" "default" {{
  vpc_id = aws_vpc.default.id
  
  tags = {{
    Name = "DefaultIGW"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

resource "aws_route_table" "default" {{
  vpc_id = aws_vpc.default.id
  
  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.default.id
  }}
  
  tags = {{
    Name = "DefaultRouteTable"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

resource "aws_route_table_association" "default" {{
  subnet_id      = aws_subnet.default.id
  route_table_id = aws_route_table.default.id
}}

resource "aws_security_group" "default" {{
  name        = "default_sg"
  description = "Default security group"
  vpc_id      = aws_vpc.default.id
  
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${{var.allowed_ssh_cidrs}}"]
    description = "SSH access"
  }}
  
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }}
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }}
  
  tags = {{
    Name = "DefaultSG"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

variable "allowed_ssh_cidrs" {{
  description = "CIDR blocks allowed for SSH access"
  type        = string
  default     = "10.0.0.0/8"
}}

output "vpc_id" {{
  description = "ID of the VPC"
  value       = aws_vpc.default.id
}}

output "subnet_id" {{
  description = "ID of the subnet"
  value       = aws_subnet.default.id
}}

output "security_group_id" {{
  description = "ID of the security group"
  value       = aws_security_group.default.id
}}
"""

def generate_boto3_code(service_type, user_input):
    """Generate boto3 code based on service type and user input"""
    prompt_mapping = {
        'ec2': EC2_PROMPT,
        's3': S3_PROMPT,
        'rds': RDS_PROMPT,
        'lambda': LAMBDA_PROMPT,
        'vpc': VPC_PROMPT,
        'iam': IAM_PROMPT
    }
    
    prompt = prompt_mapping.get(service_type.lower(), EC2_PROMPT)
    return prompt.format(user_input=user_input)

def generate_terraform_code(user_input):
    """Generate Terraform code based on user input"""
    return TERRAFORM_AWS_PROMPT.format(user_input=user_input)

def generate_kubernetes_manifest(user_input):
    """Generate Kubernetes manifest based on user input"""
    return KUBERNETES_PROMPT.format(user_input=user_input)

def generate_dockerfile(user_input):
    """Generate Dockerfile based on user input"""
    return DOCKER_PROMPT.format(user_input=user_input)
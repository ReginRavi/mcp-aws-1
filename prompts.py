def ec2_terraform_prompt(instance_type, ami, subnet_id, security_group_id, region):
    return f"""
resource "aws_instance" "example" {{
  ami           = "{ami}"
  instance_type = "{instance_type}"
  subnet_id     = "{subnet_id}"
  vpc_security_group_ids = ["{security_group_id}"]
  tags = {{
    Name = "ExampleInstance"
  }}
}}
provider "aws" {{
  region = "{region}"
}}
"""

def default_vpc_resources_prompt(region):
    return f"""
resource "aws_vpc" "default" {{
  cidr_block = "10.0.0.0/16"
  tags = {{
    Name = "DefaultVPC"
  }}
}}

resource "aws_subnet" "default" {{
  vpc_id     = aws_vpc.default.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "{region}a"
  tags = {{
    Name = "DefaultSubnet"
  }}
}}

resource "aws_security_group" "default" {{
  name        = "default_sg"
  description = "Default security group"
  vpc_id      = aws_vpc.default.id
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  tags = {{
    Name = "DefaultSG"
  }}
}}
"""

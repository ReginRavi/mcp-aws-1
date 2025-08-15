import os
import json
from typing import Dict, Any, Optional
from prompts import (
    ec2_terraform_prompt, 
    default_vpc_resources_prompt,
    generate_terraform_code,
    generate_boto3_code
)

class TerraformGenerator:
    """Enhanced Terraform generator with multi-service support"""
    
    def __init__(self, base_dir: str = "terraform"):
        self.base_dir = base_dir
        self.ensure_directory_exists(self.base_dir)
    
    def ensure_directory_exists(self, directory: str) -> None:
        """Create directory if it doesn't exist"""
        os.makedirs(directory, exist_ok=True)
    
    def generate_ec2_tf(self, instance_type: str, ami: str, region: str, 
                       instance_name: str = "example", out_dir: str = "terraform_ec2") -> str:
        """Generate EC2 Terraform configuration"""
        full_out_dir = os.path.join(self.base_dir, out_dir)
        self.ensure_directory_exists(full_out_dir)
        
        # Generate VPC and EC2 resources
        vpc_content = default_vpc_resources_prompt(region)
        ec2_content = ec2_terraform_prompt(
            instance_type,
            ami,
            "aws_subnet.default.id",
            "aws_security_group.default.id",
            region
        )
        
        # Update instance name in EC2 content
        ec2_content = ec2_content.replace(
            'resource "aws_instance" "example"',
            f'resource "aws_instance" "{instance_name}"'
        )
        ec2_content = ec2_content.replace(
            'Name = "ExampleInstance"',
            f'Name = "{instance_name}"'
        )
        
        tf_content = vpc_content + "\n" + ec2_content
        tf_path = os.path.join(full_out_dir, "main.tf")
        
        with open(tf_path, "w") as f:
            f.write(tf_content)
        
        # Generate terraform.tfvars file
        tfvars_content = f"""# Terraform variables
allowed_ssh_cidrs = "10.0.0.0/8"
instance_type = "{instance_type}"
ami_id = "{ami}"
region = "{region}"
"""
        tfvars_path = os.path.join(full_out_dir, "terraform.tfvars")
        with open(tfvars_path, "w") as f:
            f.write(tfvars_content)
        
        return tf_path
    
    def generate_s3_tf(self, bucket_name: str, region: str, 
                      versioning: bool = False, out_dir: str = "terraform_s3") -> str:
        """Generate S3 Terraform configuration"""
        full_out_dir = os.path.join(self.base_dir, out_dir)
        self.ensure_directory_exists(full_out_dir)
        
        tf_content = f"""
provider "aws" {{
  region = "{region}"
}}

resource "aws_s3_bucket" "{bucket_name.replace('-', '_')}" {{
  bucket = "{bucket_name}"
  
  tags = {{
    Name = "{bucket_name}"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

resource "aws_s3_bucket_versioning" "{bucket_name.replace('-', '_')}_versioning" {{
  bucket = aws_s3_bucket.{bucket_name.replace('-', '_')}.id
  versioning_configuration {{
    status = "{'Enabled' if versioning else 'Disabled'}"
  }}
}}

resource "aws_s3_bucket_server_side_encryption_configuration" "{bucket_name.replace('-', '_')}_encryption" {{
  bucket = aws_s3_bucket.{bucket_name.replace('-', '_')}.id

  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}

output "bucket_name" {{
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.{bucket_name.replace('-', '_')}.bucket
}}

output "bucket_arn" {{
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.{bucket_name.replace('-', '_')}.arn
}}
"""
        
        tf_path = os.path.join(full_out_dir, "main.tf")
        with open(tf_path, "w") as f:
            f.write(tf_content)
        
        return tf_path
    
    def generate_rds_tf(self, db_instance_class: str, engine: str, 
                       db_name: str, region: str, out_dir: str = "terraform_rds") -> str:
        """Generate RDS Terraform configuration"""
        full_out_dir = os.path.join(self.base_dir, out_dir)
        self.ensure_directory_exists(full_out_dir)
        
        tf_content = f"""
provider "aws" {{
  region = "{region}"
}}

resource "aws_db_instance" "{db_name}" {{
  identifier     = "{db_name}"
  engine         = "{engine}"
  engine_version = "{self._get_engine_version(engine)}"
  instance_class = "{db_instance_class}"
  allocated_storage = 20
  storage_type = "gp2"
  
  db_name  = "{db_name}"
  username = "admin"
  password = "changeme123!"  # Should use AWS Secrets Manager in production
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name
  
  backup_retention_period = 7
  backup_window          = "07:00-09:00"
  maintenance_window     = "sun:09:00-sun:10:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  
  tags = {{
    Name = "{db_name}"
    Environment = "development"
    ManagedBy = "terraform"
  }}
}}

resource "aws_db_subnet_group" "default" {{
  name       = "{db_name}-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  
  tags = {{
    Name = "{db_name}-subnet-group"
  }}
}}

resource "aws_security_group" "rds" {{
  name        = "{db_name}-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id
  
  ingress {{
    from_port   = {self._get_db_port(engine)}
    to_port     = {self._get_db_port(engine)}
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "{engine.upper()} access"
  }}
  
  tags = {{
    Name = "{db_name}-rds-sg"
  }}
}}

# Basic VPC setup for RDS
resource "aws_vpc" "main" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name = "{db_name}-vpc"
  }}
}}

resource "aws_subnet" "private_1" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "{region}a"
  
  tags = {{
    Name = "{db_name}-private-1"
  }}
}}

resource "aws_subnet" "private_2" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "{region}b"
  
  tags = {{
    Name = "{db_name}-private-2"
  }}
}}

output "rds_endpoint" {{
  description = "RDS instance endpoint"
  value       = aws_db_instance.{db_name}.endpoint
}}

output "rds_port" {{
  description = "RDS instance port"
  value       = aws_db_instance.{db_name}.port
}}
"""
        
        tf_path = os.path.join(full_out_dir, "main.tf")
        with open(tf_path, "w") as f:
            f.write(tf_content)
        
        return tf_path
    
    def generate_custom_tf(self, user_input: str, out_dir: str = "terraform_custom") -> str:
        """Generate custom Terraform configuration based on natural language input"""
        full_out_dir = os.path.join(self.base_dir, out_dir)
        self.ensure_directory_exists(full_out_dir)
        
        # Use the prompt template to generate Terraform code
        tf_content = generate_terraform_code(user_input)
        
        tf_path = os.path.join(full_out_dir, "main.tf")
        with open(tf_path, "w") as f:
            f.write(tf_content)
        
        return tf_path
    
    def _get_engine_version(self, engine: str) -> str:
        """Get default engine version based on engine type"""
        versions = {
            "mysql": "8.0",
            "postgres": "13.7",
            "mariadb": "10.6",
            "oracle-ee": "19.0.0.0.ru-2022-01.rur-2022-01.r1",
            "sqlserver-ex": "15.00.4153.1.v1"
        }
        return versions.get(engine.lower(), "8.0")
    
    def _get_db_port(self, engine: str) -> int:
        """Get default port based on engine type"""
        ports = {
            "mysql": 3306,
            "postgres": 5432,
            "mariadb": 3306,
            "oracle-ee": 1521,
            "sqlserver-ex": 1433
        }
        return ports.get(engine.lower(), 3306)

# Backward compatibility functions
def generate_ec2_tf(instance_type: str, ami: str, region: str, 
                   out_dir: str = "terraform_ec2") -> str:
    """Backward compatible EC2 generation function"""
    generator = TerraformGenerator()
    return generator.generate_ec2_tf(instance_type, ami, region, out_dir=out_dir)
# MCP Infrastructure Management System v2.0

A comprehensive multi-service cloud infrastructure management system that uses natural language processing to deploy AWS resources via Terraform and boto3.

## 🚀 Features

### Multi-Service Support
- **EC2**: Launch, configure, and manage instances
- **S3**: Create and manage buckets with versioning and encryption
- **RDS**: Deploy managed databases (MySQL, PostgreSQL, MariaDB)
- **Custom Infrastructure**: Deploy complex architectures via natural language

### Natural Language Interface
- Convert plain English commands into infrastructure code
- Support for both Terraform and boto3 code generation
- Intelligent parsing of resource specifications

### Enhanced Security
- Configurable SSH CIDR blocks (no more 0.0.0.0/0 by default!)
- Resource tagging and organization
- Environment-specific configurations

### Developer Experience
- Interactive CLI client
- Batch command execution
- Comprehensive health checks
- Structured logging
- API documentation

## 📋 Prerequisites

### Required Dependencies
```bash
# Python packages
pip install fastapi uvicorn pydantic requests

# System dependencies
# Terraform CLI (https://developer.hashicorp.com/terraform/downloads)
# AWS CLI (optional): pip install awscli
```

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=ap-south-1
```

## 🔧 Installation & Setup

### 1. Initial Setup
```bash
# Setup directories and sample configurations
python bootstrap.py setup

# Copy and configure environment
cp .env.sample .env
# Edit .env with your AWS credentials
```

### 2. Start the Server
```bash
# Start FastAPI server
python bootstrap.py server

# Or with custom port
python bootstrap.py server --port 9000

# Development mode with auto-reload
python bootstrap.py --dev server
```

### 3. Verify Installation
```bash
# Health check
python bootstrap.py health

# Check API documentation
# Open: http://localhost:8000/docs
```

## 💡 Usage Examples

### Interactive Mode
```bash
# Start interactive client
python bootstrap.py client

# Or directly
python run_client.py --interactive
```

Interactive commands:
```
🤖 MCP> create ec2 instance t2.micro named web-server
🤖 MCP> create s3 bucket my-data-bucket with versioning  
🤖 MCP> create rds mysql database named app-db
🤖 MCP> generate terraform code for load balancer
🤖 MCP> delete ec2 instance i-1234567890abcdef0
🤖 MCP> get ec2 state
🤖 MCP> health
```

### Single Commands
```bash
# EC2 instances
python run_client.py create ec2 instance t2.small named production-web
python run_client.py create ec2 instance t3.medium in us-west-2 named api-server

# S3 buckets
python run_client.py create s3 bucket my-app-data-2024
python run_client.py create s3 bucket backup-storage with versioning

# RDS databases
python run_client.py create rds mysql database named production-db
python run_client.py create rds postgres database named analytics-db

# Code generation
python run_client.py generate terraform code for web application with load balancer
python run_client.py generate boto3 code for creating lambda function
```

### Batch Operations
```bash
# Create commands file
cat > my-commands.txt << EOF
create ec2 instance t2.micro named web-1
create ec2 instance t2.micro named web-2  
create s3 bucket app-storage-prod
create rds mysql database named prod-db
EOF

# Execute batch
python run_client.py --batch my-commands.txt
```

### API Direct Usage
```python
import requests

# Create EC2 instance
response = requests.post('http://localhost:8000/create_ec2', json={
    "instance_type": "t2.micro",
    "instance_name": "my-server",
    "region": "us-east-1",
    "allowed_ssh_cidrs": "10.0.0.0/8"
})

# Generate code
response = requests.post('http://localhost:8000/generate_code', json={
    "user_input": "create a load balancer with auto scaling",
    "service_type": "terraform"
})

print(response.json()['generated_code'])
```

## 🏗️ Architecture

### File Structure
```
├── bootstrap.py              # Main bootstrap and CLI
├── mcp_fastapi_server.py    # FastAPI server with all endpoints
├── mcp_client.py            # Enhanced client with NLP
├── run_client.py            # Interactive client interface
├── terraform_generator.py   # Multi-service Terraform generator
├── prompts.py              # Updated prompt functions
├── prompt_templates.py     # Comprehensive prompt templates
├── terraform/              # Generated Terraform configurations
│   ├── terraform_ec2/      # EC2 configurations
│   ├── terraform_s3/       # S3 configurations  
│   ├── terraform_rds/      # RDS configurations
│   └── terraform_custom/   # Custom configurations
└── logs/                   # Application logs
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API information and available services |
| `/health` | GET | System health check |
| `/create_ec2` | POST | Deploy EC2 instances |
| `/create_s3` | POST | Create S3 buckets |
| `/create_rds` | POST | Deploy RDS databases |
| `/generate_code` | POST | Generate infrastructure code |
| `/deploy_custom` | POST | Deploy custom infrastructure |
| `/delete_resource` | DELETE | Delete AWS resources |
| `/terraform_state/{type}` | GET | Get Terraform state |

## 🔒 Security Improvements

### SSH Access Control
```hcl
# Old (dangerous)
cidr_blocks = ["0.0.0.0/0"]

# New (secure)
variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = string
  default     = "10.0.0.0/8"
}
```

### Resource Tagging
All resources now include:
- `Environment` tag
- `ManagedBy = "terraform"` tag
- Proper naming conventions

### Input Validation
- Pydantic models for API request validation
- Natural language parsing with safeguards
- Timeout protection for Terraform operations

## 🚨 Error Handling & Monitoring

### Comprehensive Logging
```python
# Structured logging throughout the application
logger.info(f"Creating EC2 instance: {instance_name}")
logger.error(f"Terraform apply failed: {stderr}")
```

### Health Checks
```bash
# Manual health check
python bootstrap.py health

# Programmatic health check
curl http://localhost:8000/health
```

### Error Response Format
```json
{
  "error": "Detailed error message",
  "timestamp": "2025-08-11T10:30:00Z",
  "terraform_file": "/path/to/config.tf"
}
```

## 📚 Advanced Usage

### Custom Terraform Generation
```python
# Natural language to Terraform
python run_client.py generate terraform code for "web application with RDS database, load balancer, and auto scaling in multiple AZs"
```

### Multi-Region Deployments
```bash
# Deploy to different regions
python run_client.py --region us-west-2 create ec2 instance t2.micro named west-server
python run_client.py --region eu-west-1 create s3 bucket european-data-store
```

### State Management
```bash
# Check Terraform state
python run_client.py get ec2 state
python run_client.py get s3 state
python run_client.py get rds state
```

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check dependencies
python bootstrap.py health

# Check port availability
netstat -tulpn | grep :8000
```

**Terraform errors:**
```bash
# Verify Terraform installation
terraform --version

# Check AWS credentials
aws sts get-caller-identity
```

**Permission errors:**
```bash
# Ensure proper AWS IAM permissions for:
# - EC2 (create instances, VPCs, security groups)
# - S3 (create/manage buckets)
# - RDS (create databases, subnets)
```

### Debug Mode
```bash
# Start server in development mode
python bootstrap.py --dev server

# Enable detailed logging
export LOG_LEVEL=DEBUG
python bootstrap.py server
```

## 🔄 Migration from v1.0

The updated system is backward compatible, but for full benefits:

1. **Update prompt templates**: Copy `prompt_templates.py` 
2. **Regenerate configurations**: Run `python bootstrap.py setup`
3. **Update security groups**: Review and update SSH CIDR blocks
4. **Use new client**: Switch to enhanced `run_client.py`

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd mcp-infrastructure-system

# Setup development environment
python bootstrap.py setup
python bootstrap.py --dev server
```

### Adding New Services
1. Add service prompts to `prompt_templates.py`
2. Extend `TerraformGenerator` class in `terraform_generator.py`  
3. Add API endpoint in `mcp_fastapi_server.py`
4. Update natural language parser in `mcp_client.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Run health checks: `python bootstrap.py health`
4. Check logs in the `logs/` directory

---

**Happy Infrastructure Management! 🚀**
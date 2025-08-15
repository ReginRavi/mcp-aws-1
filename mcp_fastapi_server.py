from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import subprocess
import os
import json
import logging
from datetime import datetime
from terraform_generator import TerraformGenerator
from prompts import generate_boto3_code, generate_terraform_code

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Infrastructure Management API",
    description="Multi-service cloud infrastructure management using Terraform and boto3",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Terraform generator
tf_generator = TerraformGenerator()

# Request Models
class EC2Request(BaseModel):
    instance_type: str = Field(default="t2.micro", description="EC2 instance type")
    image_id: str = Field(default="ami-03f4878755434977f", description="AMI ID")
    region: str = Field(default="ap-south-1", description="AWS region")
    instance_name: str = Field(default="example", description="Instance name")
    allowed_ssh_cidrs: str = Field(default="10.0.0.0/8", description="Allowed SSH CIDR blocks")

class S3Request(BaseModel):
    bucket_name: str = Field(..., description="S3 bucket name")
    region: str = Field(default="ap-south-1", description="AWS region")
    versioning: bool = Field(default=False, description="Enable versioning")

class RDSRequest(BaseModel):
    db_instance_class: str = Field(default="db.t3.micro", description="RDS instance class")
    engine: str = Field(default="mysql", description="Database engine")
    db_name: str = Field(..., description="Database name")
    region: str = Field(default="ap-south-1", description="AWS region")

class CustomInfraRequest(BaseModel):
    user_input: str = Field(..., description="Natural language description of infrastructure")
    service_type: str = Field(default="terraform", description="Service type (terraform, boto3)")
    region: str = Field(default="ap-south-1", description="AWS region")

class DeleteResourceRequest(BaseModel):
    resource_type: str = Field(..., description="Type of resource (ec2, s3, rds)")
    resource_identifier: str = Field(..., description="Resource identifier (name, ID, etc.)")
    region: str = Field(default="ap-south-1", description="AWS region")

# Response Models
class TerraformResponse(BaseModel):
    terraform_file: str
    terraform_init_stdout: Optional[str] = None
    terraform_init_stderr: Optional[str] = None
    terraform_apply_stdout: Optional[str] = None
    terraform_apply_stderr: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class CodeGenerationResponse(BaseModel):
    generated_code: str
    service_type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Helper Functions
def run_terraform_commands(tf_dir: str) -> Dict[str, Any]:
    """Execute Terraform init and apply commands"""
    try:
        # Terraform init
        init_result = subprocess.run(
            ["terraform", "init"],
            cwd=tf_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Terraform plan (for validation)
        plan_result = subprocess.run(
            ["terraform", "plan"],
            cwd=tf_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Terraform apply
        apply_result = subprocess.run(
            ["terraform", "apply", "-auto-approve"],
            cwd=tf_dir,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        return {
            "terraform_init_stdout": init_result.stdout,
            "terraform_init_stderr": init_result.stderr,
            "terraform_plan_stdout": plan_result.stdout,
            "terraform_plan_stderr": plan_result.stderr,
            "terraform_apply_stdout": apply_result.stdout,
            "terraform_apply_stderr": apply_result.stderr,
            "init_success": init_result.returncode == 0,
            "plan_success": plan_result.returncode == 0,
            "apply_success": apply_result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        logger.error("Terraform command timed out")
        return {"error": "Terraform command timed out"}
    except Exception as e:
        logger.error(f"Error running Terraform commands: {str(e)}")
        return {"error": str(e)}

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "MCP Infrastructure Management API",
        "version": "2.0.0",
        "services": ["EC2", "S3", "RDS", "Custom Infrastructure"],
        "endpoints": ["/create_ec2", "/create_s3", "/create_rds", "/generate_code", "/delete_resource"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "terraform_available": subprocess.run(["terraform", "-version"], capture_output=True).returncode == 0
    }

@app.post("/create_ec2", response_model=TerraformResponse)
async def create_ec2(req: EC2Request):
    """Create EC2 instance using Terraform"""
    logger.info(f"Creating EC2 instance: {req.instance_name}")
    
    try:
        tf_path = tf_generator.generate_ec2_tf(
            req.instance_type,
            req.image_id,
            req.region,
            req.instance_name
        )
        tf_dir = os.path.dirname(tf_path)
        
        # Update SSH CIDR in terraform.tfvars
        tfvars_path = os.path.join(tf_dir, "terraform.tfvars")
        with open(tfvars_path, "r") as f:
            content = f.read()
        content = content.replace('allowed_ssh_cidrs = "10.0.0.0/8"', 
                                f'allowed_ssh_cidrs = "{req.allowed_ssh_cidrs}"')
        with open(tfvars_path, "w") as f:
            f.write(content)
        
        terraform_result = run_terraform_commands(tf_dir)
        
        return TerraformResponse(
            terraform_file=tf_path,
            **terraform_result
        )
        
    except Exception as e:
        logger.error(f"Error creating EC2 instance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_s3", response_model=TerraformResponse)
async def create_s3(req: S3Request):
    """Create S3 bucket using Terraform"""
    logger.info(f"Creating S3 bucket: {req.bucket_name}")
    
    try:
        tf_path = tf_generator.generate_s3_tf(
            req.bucket_name,
            req.region,
            req.versioning
        )
        tf_dir = os.path.dirname(tf_path)
        terraform_result = run_terraform_commands(tf_dir)
        
        return TerraformResponse(
            terraform_file=tf_path,
            **terraform_result
        )
        
    except Exception as e:
        logger.error(f"Error creating S3 bucket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_rds", response_model=TerraformResponse)
async def create_rds(req: RDSRequest):
    """Create RDS instance using Terraform"""
    logger.info(f"Creating RDS instance: {req.db_name}")
    
    try:
        tf_path = tf_generator.generate_rds_tf(
            req.db_instance_class,
            req.engine,
            req.db_name,
            req.region
        )
        tf_dir = os.path.dirname(tf_path)
        terraform_result = run_terraform_commands(tf_dir)
        
        return TerraformResponse(
            terraform_file=tf_path,
            **terraform_result
        )
        
    except Exception as e:
        logger.error(f"Error creating RDS instance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_code", response_model=CodeGenerationResponse)
async def generate_infrastructure_code(req: CustomInfraRequest):
    """Generate infrastructure code based on natural language input"""
    logger.info(f"Generating {req.service_type} code for: {req.user_input}")
    
    try:
        if req.service_type.lower() == "terraform":
            generated_code = generate_terraform_code(req.user_input)
        elif req.service_type.lower() in ["boto3", "python"]:
            # Extract service type from user input or default to EC2
            service_type = "ec2"  # Default
            if "s3" in req.user_input.lower():
                service_type = "s3"
            elif "rds" in req.user_input.lower():
                service_type = "rds"
            elif "lambda" in req.user_input.lower():
                service_type = "lambda"
            elif "vpc" in req.user_input.lower():
                service_type = "vpc"
            elif "iam" in req.user_input.lower():
                service_type = "iam"
            
            generated_code = generate_boto3_code(service_type, req.user_input)
        else:
            raise HTTPException(status_code=400, detail="Unsupported service type")
        
        return CodeGenerationResponse(
            generated_code=generated_code,
            service_type=req.service_type
        )
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy_custom", response_model=TerraformResponse)
async def deploy_custom_infrastructure(req: CustomInfraRequest):
    """Deploy custom infrastructure based on natural language input"""
    logger.info(f"Deploying custom infrastructure: {req.user_input}")
    
    try:
        tf_path = tf_generator.generate_custom_tf(req.user_input)
        tf_dir = os.path.dirname(tf_path)
        terraform_result = run_terraform_commands(tf_dir)
        
        return TerraformResponse(
            terraform_file=tf_path,
            **terraform_result
        )
        
    except Exception as e:
        logger.error(f"Error deploying custom infrastructure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_resource")
async def delete_resource(req: DeleteResourceRequest):
    """Delete AWS resources by destroying Terraform configuration"""
    logger.info(f"Deleting {req.resource_type} resource: {req.resource_identifier}")
    
    try:
        # Determine terraform directory based on resource type
        tf_dir_mapping = {
            "ec2": "terraform_ec2",
            "s3": "terraform_s3",
            "rds": "terraform_rds"
        }
        
        tf_dir = os.path.join("terraform", tf_dir_mapping.get(req.resource_type, "terraform_ec2"))
        
        if not os.path.exists(tf_dir):
            raise HTTPException(status_code=404, detail=f"No Terraform configuration found for {req.resource_type}")
        
        # Run terraform destroy
        destroy_result = subprocess.run(
            ["terraform", "destroy", "-auto-approve"],
            cwd=tf_dir,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        return {
            "resource_type": req.resource_type,
            "resource_identifier": req.resource_identifier,
            "terraform_destroy_stdout": destroy_result.stdout,
            "terraform_destroy_stderr": destroy_result.stderr,
            "success": destroy_result.returncode == 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error deleting resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/terraform_state/{resource_type}")
async def get_terraform_state(resource_type: str):
    """Get Terraform state information for a resource type"""
    try:
        tf_dir_mapping = {
            "ec2": "terraform_ec2",
            "s3": "terraform_s3",
            "rds": "terraform_rds"
        }
        
        tf_dir = os.path.join("terraform", tf_dir_mapping.get(resource_type, "terraform_ec2"))
        
        if not os.path.exists(tf_dir):
            return {"error": f"No Terraform configuration found for {resource_type}"}
        
        # Run terraform show
        show_result = subprocess.run(
            ["terraform", "show", "-json"],
            cwd=tf_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if show_result.returncode == 0:
            try:
                state_data = json.loads(show_result.stdout)
                return {
                    "resource_type": resource_type,
                    "state": state_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    "resource_type": resource_type,
                    "raw_output": show_result.stdout,
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            return {
                "error": "Failed to retrieve Terraform state",
                "stderr": show_result.stderr
            }
        
    except Exception as e:
        logger.error(f"Error getting Terraform state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
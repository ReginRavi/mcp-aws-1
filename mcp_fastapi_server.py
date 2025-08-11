from fastapi import FastAPI, Request
from pydantic import BaseModel
from terraform_generator import generate_ec2_tf
import subprocess
import os

app = FastAPI()

class EC2Request(BaseModel):
    InstanceType: str = "t2.micro"
    ImageId: str = "ami-03f4878755434977f"
    region: str = "ap-south-1"

class DeleteEC2Request(BaseModel):
    instance_name: str = "example"
    region: str = "ap-south-1"

@app.post("/create_ec2")
async def create_ec2(req: EC2Request):
    tf_path = generate_ec2_tf(req.InstanceType, req.ImageId, req.region)
    tf_dir = os.path.dirname(tf_path)
    try:
        init_result = subprocess.run(["terraform", "init"], cwd=tf_dir, capture_output=True, text=True)
        apply_result = subprocess.run(["terraform", "apply", "-auto-approve"], cwd=tf_dir, capture_output=True, text=True)
        return {
            "terraform_file": tf_path,
            "terraform_init_stdout": init_result.stdout,
            "terraform_init_stderr": init_result.stderr,
            "terraform_apply_stdout": apply_result.stdout,
            "terraform_apply_stderr": apply_result.stderr
        }
    except Exception as e:
        return {
            "terraform_file": tf_path,
            "error": str(e)
        }

@app.post("/delete_ec2")
async def delete_ec2(req: DeleteEC2Request):
    tf_path = os.path.join("terraform_ec2", "main.tf")
    try:
        with open(tf_path, "r") as f:
            lines = f.readlines()
        # Remove EC2 resource block
        cleaned_lines = []
        skip = False
        brace_count = 0
        for line in lines:
            if not skip and f'resource "aws_instance" "{req.instance_name}"' in line:
                skip = True
                brace_count = line.count("{") - line.count("}")
                continue
            if skip:
                brace_count += line.count("{")
                brace_count -= line.count("}")
                if brace_count <= 0:
                    skip = False
                continue
            cleaned_lines.append(line)
        # Remove stray closing braces and empty lines
        final_lines = []
        for line in cleaned_lines:
            if line.strip() == "}" and (len(final_lines) == 0 or final_lines[-1].strip() == ""):
                continue
            if line.strip() == "":
                continue
            final_lines.append(line)
        with open(tf_path, "w") as f:
            f.writelines(final_lines)
        tf_dir = os.path.dirname(tf_path)
        init_result = subprocess.run(["terraform", "init"], cwd=tf_dir, capture_output=True, text=True)
        apply_result = subprocess.run(["terraform", "apply", "-auto-approve"], cwd=tf_dir, capture_output=True, text=True)
        return {
            "terraform_file": tf_path,
            "terraform_init_stdout": init_result.stdout,
            "terraform_init_stderr": init_result.stderr,
            "terraform_apply_stdout": apply_result.stdout,
            "terraform_apply_stderr": apply_result.stderr
        }
    except Exception as e:
        return {
            "terraform_file": tf_path,
            "error": str(e)
        }

@app.get("/")
async def root():
    return {"message": "MCP FastAPI server is running."}

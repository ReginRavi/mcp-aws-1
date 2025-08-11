import os
from prompts import ec2_terraform_prompt

def generate_ec2_tf(instance_type, ami, region, out_dir="terraform_ec2"):
    from prompts import default_vpc_resources_prompt
    os.makedirs(out_dir, exist_ok=True)
    # Compose VPC, subnet, SG, and EC2 resources
    vpc_content = default_vpc_resources_prompt(region)
    ec2_content = ec2_terraform_prompt(
        instance_type,
        ami,
        "${aws_subnet.default.id}",
        "${aws_security_group.default.id}",
        region
    )
    tf_content = vpc_content + "\n" + ec2_content
    tf_path = os.path.join(out_dir, "main.tf")
    with open(tf_path, "w") as f:
        f.write(tf_content)
    return tf_path

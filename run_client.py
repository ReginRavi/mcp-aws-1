"""
Enhanced run_client.py with multi-service support and improved natural language processing.
"""
import sys
import argparse
import json
from mcp_client1 import MCPClient, NaturalLanguageParser

def interactive_mode():
    """Interactive mode for continuous commands"""
    client = MCPClient()
    
    print("🚀 MCP Interactive Mode")
    print("=" * 50)
    print("Examples:")
    print("  • create ec2 instance t2.micro named web-server")
    print("  • create s3 bucket my-data-bucket with versioning")
    print("  • create rds mysql database named production-db")
    print("  • generate terraform code for load balancer")
    print("  • delete ec2 instance i-1234567890abcdef0")
    print("  • get ec2 state")
    print("  • health (check API status)")
    print("  • quit (exit)")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n🤖 MCP> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not command:
                continue
            
            if command.lower() == 'health':
                health = client.health_check()
                if 'error' in health:
                    print("❌ API server is not available")
                else:
                    print(f"✅ API server is healthy (Terraform: {'✅' if health.get('terraform_available') else '❌'})")
                continue
            
            # Parse and execute command
            parsed_command = NaturalLanguageParser.parse_command(command)
            print(f"🔍 Parsed action: {parsed_command['action']}")
            
            result = execute_parsed_command(client, parsed_command)
            display_result(result)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def execute_parsed_command(client: MCPClient, parsed_command: dict):
    """Execute a parsed command using the MCP client"""
    action = parsed_command['action']
    
    if action == 'create_ec2':
        return client.create_ec2_instance(
            instance_type=parsed_command.get('instance_type', 't2.micro'),
            region=parsed_command.get('region', 'ap-south-1'),
            instance_name=parsed_command.get('instance_name', 'example')
        )
    
    elif action == 'create_s3':
        return client.create_s3_bucket(
            bucket_name=parsed_command['bucket_name'],
            region=parsed_command.get('region', 'ap-south-1'),
            versioning=parsed_command.get('versioning', False)
        )
    
    elif action == 'create_rds':
        return client.create_rds_instance(
            db_instance_class=parsed_command.get('db_instance_class', 'db.t3.micro'),
            engine=parsed_command.get('engine', 'mysql'),
            db_name=parsed_command['db_name'],
            region=parsed_command.get('region', 'ap-south-1')
        )
    
    elif action == 'delete_resource':
        return client.delete_resource(
            resource_type=parsed_command['resource_type'],
            resource_identifier=parsed_command['resource_identifier'],
            region='ap-south-1'
        )
    
    elif action == 'generate_code':
        return client.generate_code(
            user_input=parsed_command['user_input'],
            service_type=parsed_command.get('service_type', 'terraform'),
            region='ap-south-1'
        )
    
    elif action == 'deploy_custom':
        return client.deploy_custom_infrastructure(
            user_input=parsed_command['user_input'],
            region='ap-south-1'
        )
    
    elif action == 'get_state':
        return client.get_terraform_state(parsed_command['resource_type'])
    
    else:
        return {"error": f"Unknown action: {action}"}

def display_result(result):
    """Display result in a user-friendly format"""
    if not result:
        print("❌ No result received")
        return
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if 'generated_code' in result:
        print("\n📝 Generated Code:")
        print("=" * 60)
        print(result['generated_code'])
        print("=" * 60)
        
    elif 'terraform_file' in result:
        print(f"\n🏗️  Infrastructure Operation")
        print(f"📁 Terraform file: {result['terraform_file']}")
        
        if result.get('apply_success'):
            print("✅ Terraform apply successful!")
        elif result.get('terraform_apply_stderr'):
            print(f"❌ Terraform apply failed:")
            print(result['terraform_apply_stderr'])
        
        if result.get('terraform_apply_stdout'):
            print("\n📊 Terraform Output:")
            print("-" * 40)
            print(result['terraform_apply_stdout'])
    
    elif 'state' in result:
        print(f"\n📊 Terraform State for {result.get('resource_type', 'unknown')}")
        print("=" * 50)
        
        state = result['state']
        if 'values' in state and 'root_module' in state['values']:
            resources = state['values']['root_module'].get('resources', [])
            for resource in resources:
                print(f"🔹 {resource.get('type', 'unknown')} - {resource.get('name', 'unnamed')}")
                if 'values' in resource:
                    for key, value in resource['values'].items():
                        if key in ['id', 'arn', 'name', 'state']:
                            print(f"   {key}: {value}")
        else:
            print("No resources found in state")
    
    elif 'success' in result:
        if result['success']:
            print("✅ Operation completed successfully!")
        else:
            print("❌ Operation failed")
        
        for key, value in result.items():
            if key not in ['success', 'timestamp']:
                print(f"{key}: {value}")
    
    else:
        print("✅ Operation completed")
        for key, value in result.items():
            if key not in ['timestamp']:
                print(f"{key}: {value}")

def batch_mode(commands_file: str):
    """Execute commands from a file"""
    client = MCPClient()
    
    try:
        with open(commands_file, 'r') as f:
            commands = f.readlines()
        
        print(f"📁 Executing {len(commands)} commands from {commands_file}")
        
        for i, command in enumerate(commands, 1):
            command = command.strip()
            if not command or command.startswith('#'):
                continue
            
            print(f"\n[{i}] Executing: {command}")
            parsed_command = NaturalLanguageParser.parse_command(command)
            result = execute_parsed_command(client, parsed_command)
            display_result(result)
            
            if 'error' in result:
                print(f"⚠️  Stopping batch execution due to error")
                break
                
    except FileNotFoundError:
        print(f"❌ File not found: {commands_file}")
    except Exception as e:
        print(f"❌ Batch execution error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced MCP Client with Multi-Service Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python run_client.py

  # Single command
  python run_client.py create ec2 instance t2.micro named web-server
  
  # Batch mode
  python run_client.py --batch commands.txt
  
  # JSON output
  python run_client.py --json create s3 bucket my-test-bucket
  
  # Specific region
  python run_client.py --region us-west-2 create rds postgres database myapp
        """
    )
    
    parser.add_argument('command', nargs='*', help='Natural language command')
    parser.add_argument('--region', default='ap-south-1', help='AWS region')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--batch', help='Execute commands from file')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--api-port', type=int, default=8000, help='API port')
    
    args = parser.parse_args()
    
    # Batch mode
    if args.batch:
        batch_mode(args.batch)
        return
    
    # Interactive mode (default if no command provided)
    if not args.command or args.interactive:
        interactive_mode()
        return
    
    # Single command mode
    client = MCPClient(host=args.host, api_port=args.api_port)
    command_str = " ".join(args.command)
    
    # Health check
    health = client.health_check()
    if 'error' in health:
        print("❌ API server is not available. Please start the server first.")
        print("Run: python mcp_fastapi_server.py")
        return
    
    # Parse and execute command
    parsed_command = NaturalLanguageParser.parse_command(command_str)
    result = execute_parsed_command(client, parsed_command)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        display_result(result)

if __name__ == "__main__":
    main()
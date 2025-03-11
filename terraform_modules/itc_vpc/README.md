## ITC VPC

This Terraform module provisions an AWS Virtual Private Cloud (VPC) designed for hosting an RDS database with private and public subnets, secure networking, and integration with AWS services like Lambda and Secrets Manager.

### Features
- **Custom VPC**: Creates a dedicated VPC with a CIDR block of `10.1.0.0/16`.
- **Subnets**:
  - Public Subnets: `10.1.5.0/24`, `10.1.6.0/24`
  - Private Subnets: Defined by `private_subnet_cidrs`
- **Security Groups**:
  - Allows PostgreSQL access from specific IPs
  - Provides outbound access
- **Routing**:
  - Internet Gateway for public subnets
  - NAT Gateway for private subnets
- **VPC Endpoints**:
  - Supports Lambda, DynamoDB, S3
  - Interface endpoint for Secrets Manager
- **IAM Policies and Roles**: Configures secure access to AWS services.

## Usage
To use this module, see the usage in the main `main.tf`.

### Resources Created
1. **VPC**: `aws_vpc.itc_database_vpc`
2. **Subnets**:
   - Public: `aws_subnet.itc_database_aws_subnet`
   - Private: `aws_subnet.itc_database_private_subnet`
3. **Security Groups**:
   - `aws_security_group.itc_database_vpc_sg` (for RDS access)
   - `aws_security_group.vpc_endpoints_sg` (for VPC endpoints)
4. **Routing**:
   - `aws_route_table.itc_database_vpc_rt` (for public subnets)
   - `aws_route_table.itc_database_private_rt` (for private subnets)
   - NAT Gateway: `aws_nat_gateway.nat_gateway`
5. **VPC Endpoints**:
   - Lambda, DynamoDB, S3, and Secrets Manager endpoints

### Variables
- `itc_database_prefix`: Prefix for naming AWS resources
- `private_subnet_cidrs`: List of CIDR blocks for private subnets
- `public_subnet_cidrs`: List of CIDR blocks for public subnets
- `azs`: Availability Zones (default: `us-east-1a`, `us-east-1b`)
- `my_ip`: Your IP for PostgreSQL access
- `vpc_endpoint_services`: List of AWS services requiring VPC endpoints

### Notes
- Ensure that `my_ip` is correctly set to allow secure database access.
- Private subnets require the NAT Gateway for outbound internet access.
- Update the `vpc_endpoint_services` variable to include any additional AWS services required for the VPC.

This module ensures a secure and scalable networking setup for hosting an RDS instance within a controlled AWS environment.


## Deployment
1. Ensure that Terraform and AWS CLI are installed and configured.
2. Make sure you are logged in to the correct AWS account.
3. Initialize Terraform:
   ```sh
   terraform init
   ```
4. Plan the deployment:
   ```sh
   terraform plan
   ```
5. Apply the changes:
   ```sh
   terraform apply
   ```

## Cleanup
To remove the resources, run:
```sh
terraform destroy
```
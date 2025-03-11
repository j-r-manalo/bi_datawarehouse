# output "itc_vpc_resources" {
#   value = {
#     itc_database_vpc_id                 = aws_vpc.itc_database_vpc.id
#     itc_database_vpc_security_group_id  = aws_security_group.itc_database_vpc_sg.id
#     itc_database_vpc_subnet_ids         = aws_subnet.itc_database_aws_subnet[*].id
#     vpc_endpoints_security_group_id     = aws_security_group.vpc_endpoints_sg.id
#   }
# }
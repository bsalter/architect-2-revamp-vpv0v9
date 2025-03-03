# Variables for the networking module that creates AWS VPC, subnets, security groups,
# and other network resources for the Interaction Management System

variable "environment" {
  description = "Environment name used for resource naming and tagging (e.g., dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets_cidr" {
  description = "List of CIDR blocks for public subnets, one per availability zone"
  type        = list(string)
  default     = []
}

variable "private_app_subnets_cidr" {
  description = "List of CIDR blocks for private application subnets, one per availability zone"
  type        = list(string)
  default     = []
}

variable "private_data_subnets_cidr" {
  description = "List of CIDR blocks for private data subnets, one per availability zone"
  type        = list(string)
  default     = []
}

variable "availability_zones" {
  description = "List of availability zones to deploy resources in"
  type        = list(string)
  default     = []
}

variable "enable_nat_gateway" {
  description = "Whether to create NAT Gateways for private subnets outbound internet access"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Whether to create a single shared NAT Gateway across all availability zones"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Whether to create a VPN Gateway for connecting to on-premises networks"
  type        = bool
  default     = false
}

variable "enable_dns_hostnames" {
  description = "Whether to enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Whether to enable DNS support in the VPC"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Whether to enable VPC flow logs for network monitoring"
  type        = bool
  default     = false
}

variable "flow_logs_destination_type" {
  description = "Type of flow log destination (s3 or cloud-watch-logs)"
  type        = string
  default     = "cloud-watch-logs"
}

variable "flow_logs_traffic_type" {
  description = "Type of traffic to capture in flow logs (ACCEPT, REJECT, or ALL)"
  type        = string
  default     = "ALL"
}

variable "create_alb_security_group" {
  description = "Whether to create a security group for the Application Load Balancer"
  type        = bool
  default     = true
}

variable "create_app_security_group" {
  description = "Whether to create a security group for the application tier"
  type        = bool
  default     = true
}

variable "create_db_security_group" {
  description = "Whether to create a security group for the database tier"
  type        = bool
  default     = true
}

variable "create_cache_security_group" {
  description = "Whether to create a security group for the cache tier"
  type        = bool
  default     = true
}

variable "alb_ingress_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "alb_ingress_port" {
  description = "Port on which the ALB accepts incoming traffic"
  type        = number
  default     = 443
}

variable "app_ingress_port" {
  description = "Port on which the application accepts traffic from the ALB"
  type        = number
  default     = 5000
}

variable "db_port" {
  description = "Port on which the database accepts connections"
  type        = number
  default     = 5432
}

variable "cache_port" {
  description = "Port on which the cache accepts connections"
  type        = number
  default     = 6379
}

variable "tags" {
  description = "Tags to apply to all resources created by this module"
  type        = map(string)
  default     = {}
}
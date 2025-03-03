# ------------------------------------------------------------------------------
# COMPUTE MODULE - MAIN
# Provisions AWS compute resources for the Interaction Management System
# ------------------------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# LOCAL VARIABLES
# ---------------------------------------------------------------------------------------------------------------------
locals {
  name_prefix = "${var.environment}-${var.project_name}"
  common_tags = merge(var.tags, {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  })
  alb_name = "${local.name_prefix}-alb"
  frontend_name = "${local.name_prefix}-frontend"
  backend_name = "${local.name_prefix}-backend"
  ecs_cluster_name = "${local.name_prefix}-cluster"
  frontend_task_family = "${local.name_prefix}-frontend-task"
  backend_task_family = "${local.name_prefix}-backend-task"
  is_prod = var.environment == "prod"
  frontend_port = 80
  backend_port = var.backend_config.container_port
}

# ---------------------------------------------------------------------------------------------------------------------
# APPLICATION LOAD BALANCER
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_lb" "this" {
  name               = local.alb_name
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = local.is_prod

  # Access logs configuration - only enabled in production
  dynamic "access_logs" {
    for_each = local.is_prod ? [1] : []
    content {
      bucket  = "alb-logs-${var.project_name}-${var.environment}"
      enabled = true
    }
  }

  idle_timeout = 60

  tags = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# TARGET GROUPS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_lb_target_group" "frontend" {
  name     = "${local.frontend_name}-tg"
  port     = local.frontend_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"  # Use "ip" for awsvpc network mode (Fargate)

  health_check {
    path                = var.frontend_config.health_check_path
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200-299"
  }

  deregistration_delay = 30

  tags = local.common_tags
}

resource "aws_lb_target_group" "backend" {
  name     = "${local.backend_name}-tg"
  port     = local.backend_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"  # Use "ip" for awsvpc network mode (Fargate)

  health_check {
    path                = var.backend_config.health_check_path
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200-299"
  }

  deregistration_delay = 30

  tags = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# LISTENERS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = var.enable_https ? "redirect" : "forward"

    dynamic "redirect" {
      for_each = var.enable_https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "forward" {
      for_each = var.enable_https ? [] : [1]
      content {
        target_group {
          arn = aws_lb_target_group.frontend.arn
        }
      }
    }
  }

  tags = local.common_tags
}

resource "aws_lb_listener" "https" {
  count = var.enable_https && var.certificate_arn != null ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  tags = local.common_tags
}

# Backend API Listener Rule - routes /api/* to backend service
resource "aws_lb_listener_rule" "backend" {
  listener_arn = var.enable_https && var.certificate_arn != null ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# IAM ROLES AND POLICIES FOR ECS
# ---------------------------------------------------------------------------------------------------------------------
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Task execution role - for ECS to pull images, write logs, etc.
resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags = local.common_tags
}

# Task execution role policy
data "aws_iam_policy_document" "ecs_task_execution" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "ssm:GetParameters",
      "secretsmanager:GetSecretValue",
      "kms:Decrypt"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_task_execution" {
  name   = "${local.name_prefix}-ecs-execution-policy"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.ecs_task_execution.json
}

# Task role - for the application running in the container
resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags = local.common_tags
}

# Task role policy - application-specific permissions
data "aws_iam_policy_document" "ecs_task" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameters",
      "secretsmanager:GetSecretValue",
      "kms:Decrypt"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_task" {
  name   = "${local.name_prefix}-ecs-task-policy"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task.json
}

# ---------------------------------------------------------------------------------------------------------------------
# CLOUDWATCH LOG GROUPS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.frontend_name}"
  retention_in_days = local.is_prod ? 90 : 30
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.backend_name}"
  retention_in_days = local.is_prod ? 90 : 30
  tags              = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# ECS CLUSTER
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_ecs_cluster" "this" {
  name = local.ecs_cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# ECS TASK DEFINITIONS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "frontend" {
  family                   = local.frontend_task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_config.cpu
  memory                   = var.frontend_config.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = var.frontend_config.image
      essential = true
      portMappings = [
        {
          containerPort = var.frontend_config.container_port
          hostPort      = var.frontend_config.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "API_URL"
          value = "/api"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "frontend"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.frontend_config.container_port}${var.frontend_config.health_check_path} || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "backend" {
  family                   = local.backend_task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_config.cpu
  memory                   = var.backend_config.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.backend_config.image
      essential = true
      portMappings = [
        {
          containerPort = var.backend_config.container_port
          hostPort      = var.backend_config.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "PORT"
          value = tostring(var.backend_config.container_port)
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "backend"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.backend_config.container_port}${var.backend_config.health_check_path} || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# ECS SERVICES
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_ecs_service" "frontend" {
  name                               = local.frontend_name
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.frontend.arn
  desired_count                      = var.frontend_config.desired_count
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  health_check_grace_period_seconds  = var.health_check_grace_period

  network_configuration {
    subnets          = var.private_app_subnet_ids
    security_groups  = [var.app_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.frontend_config.container_port
  }

  # Ignore changes to desired_count because it will be managed by autoscaling
  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener.http]

  tags = local.common_tags
}

resource "aws_ecs_service" "backend" {
  name                               = local.backend_name
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.backend.arn
  desired_count                      = var.backend_config.desired_count
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  health_check_grace_period_seconds  = var.health_check_grace_period

  network_configuration {
    subnets          = var.private_app_subnet_ids
    security_groups  = [var.app_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = var.backend_config.container_port
  }

  # Ignore changes to desired_count because it will be managed by autoscaling
  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener_rule.backend]

  tags = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# AUTO SCALING
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = var.max_size
  min_capacity       = var.min_size
  resource_id        = "service/${aws_ecs_cluster.this.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${local.frontend_name}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_scale_out_threshold
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown
  }
}

resource "aws_appautoscaling_target" "backend" {
  max_capacity       = var.max_size
  min_capacity       = var.min_size
  resource_id        = "service/${aws_ecs_cluster.this.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${local.backend_name}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_scale_out_threshold
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# ROUTE 53 DNS RECORD (OPTIONAL)
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_route53_record" "this" {
  count   = var.domain_name != null && var.enable_https ? 1 : 0
  zone_id = data.aws_route53_zone.this[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.this.dns_name
    zone_id                = aws_lb.this.zone_id
    evaluate_target_health = true
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# DATA SOURCES
# ---------------------------------------------------------------------------------------------------------------------
data "aws_region" "current" {}

data "aws_route53_zone" "this" {
  count = var.domain_name != null ? 1 : 0
  
  # Extract the domain from the subdomain if needed (e.g., app.example.com -> example.com)
  # This simple regex looks for the last two parts of the domain (example.com)
  name = regex("[^.]+\\.[^.]+$", var.domain_name)
  
  private_zone = false
}

# ---------------------------------------------------------------------------------------------------------------------
# OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.this.arn
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

output "backend_target_group_arn" {
  description = "ARN of the backend target group"
  value       = aws_lb_target_group.backend.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.this.name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "backend_service_name" {
  description = "Name of the backend ECS service"
  value       = aws_ecs_service.backend.name
}

output "application_url" {
  description = "URL to access the application"
  value       = var.domain_name != null && var.enable_https ? "https://${var.domain_name}" : "http://${aws_lb.this.dns_name}"
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}
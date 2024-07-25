module "lambda-cleanup" {
  for_each = {
    for index, command in var.django_command :
    command.task_name => command
  }
  source       = "../../../i-ai-core-infrastructure//modules/lambda"
  image_config = {
    command = ["venv/bin/django-admin", each.value.command]
  }
  package_type = "Image"
  image_uri              = "${var.ecr_repository_uri}/${var.project_name}-django-app:37d4ac8fe83c92653e79f2edc870747ffcc82d61"
  function_name          = "${local.name}-${each.value.task_name}-lambda"
  iam_role_name          = "${local.name}-${each.value.task_name}-lambda-role"
  timeout                = 60
  environment_variables  = merge(local.django_app_secrets, local.django_lambda_environment_variables)
  aws_security_group_ids = [aws_security_group.service_security_group.id]
  subnet_ids             = data.terraform_remote_state.vpc.outputs.private_subnets
}

resource "aws_security_group" "service_security_group" {
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id
  description = "${local.name} redbox lambda security group"
  name        = "${local.name}-redbox-lambda-sg"
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "lambda_to_rds_egress" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = module.rds.postgres_sg_id
  security_group_id        = aws_security_group.service_security_group.id
  description              = "Allow requests from the lambda to get to the RDS"
}

resource "aws_security_group_rule" "lambda_to_443_egress" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
  security_group_id = aws_security_group.service_security_group.id
}

#data "archive_file" "code" {
#  type        = "zip"
#  source_dir  = "${path.module}/cleanup_lambda/code"
#  output_path = "${path.module}/cleanup_lambda/code.zip"
#}
#
#
#resource "aws_lambda_layer_version" "layer" {
#  layer_name          = "cleanup-layer"
#  filename            = data.archive_file.layer.output_path
#  source_code_hash    = data.archive_file.layer.output_base64sha256
#  compatible_runtimes = ["python3.12"]
#}
#
#
#data "archive_file" "layer" {
#  type        = "zip"
#  source_dir  = "${path.module}/cleanup_lambda/layer"
#  output_path = "${path.module}/cleanup_lambda/layer.zip"
#  depends_on  = [null_resource.pip_install]
#}
#
#
#resource "null_resource" "pip_install" {
#  triggers = {
#    shell_hash = sha256(file("${path.module}/cleanup_lambda/requirements.txt"))
#  }
#
#  provisioner "local-exec" {
#    command = "python3 -m pip install -r ./cleanup_lambda/requirements.txt -t ${path.module}/cleanup_lambda/layer/python"
#  }
#}
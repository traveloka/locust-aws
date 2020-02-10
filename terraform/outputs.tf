output "service_role_name" {
  value = "${aws_iam_role.aws_batch_service_role.name}"
}

output "instance_role_name" {
  value = "${aws_iam_role.ecs_instance_role.name}"
}

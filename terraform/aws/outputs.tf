output "service_role_name" {
  value = "${aws_iam_role.aws_batch_service_role.name}"
}

output "instance_role_name" {
  value = "${aws_iam_role.ecs_instance_role.name}"
}

output "batch_job_queue_arn" {
  value = "${aws_batch_job_queue.this.arn}"
  description = "ARN of the batch job queue"
}

output "batch_compute_environment_arn" {
  value = "${aws_batch_compute_environment.this.arn}"
  description = "ARN of the batch job compute environment"
}

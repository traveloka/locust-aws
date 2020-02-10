resource "aws_batch_job_queue" "this" {
  name                 = "${var.name}"
  state                = "ENABLED"
  priority             = 1
  compute_environments = ["${aws_batch_compute_environment.this.arn}"]
}

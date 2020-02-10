provider "aws" {
  region = "ap-southeast-1"
}

module "aws_batch" {
  source = "../"

  name               = "sample"
  security_group_ids = ["${aws_security_group.sample.id}"]
  subnets            = ["${aws_subnet.private.id}"]
  max_vcpus          = 16
}

resource "aws_subnet" "public" {
  vpc_id     = "${aws_vpc.sample.id}"
  cidr_block = "10.1.10.0/24"
}

resource "aws_subnet" "private" {
  vpc_id     = "${aws_vpc.sample.id}"
  cidr_block = "10.1.20.0/24"
}

resource "aws_security_group" "sample" {
  name = "aws_batch_compute_environment_security_group"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  vpc_id = "${aws_vpc.sample.id}"
}

resource "aws_vpc" "sample" {
  cidr_block = "10.1.0.0/16"
  enable_dns_support = "true"
  enable_dns_hostnames = "true"
}

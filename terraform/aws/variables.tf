variable "name" {
  type = "string"
}

variable "instance_type" {
  type    = "list"
  default = ["c5.large"]
}

variable "security_group_ids" {
  type = "list"
}

variable "subnets" {
  type = "list"
}

variable "min_vcpus" {
  type    = "string"
  default = "0"
}

variable "max_vcpus" {
  type = "string"
}

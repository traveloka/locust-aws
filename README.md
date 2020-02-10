# Locust for AWS ![Build Status](https://travis-ci.com/jinhong-/locust-aws.svg?branch=master)

This is customized specifically to support locust via the usage of AWS batch with multinode type. Minimum 2 nodes must be configured

## Notes

- Unable to create Job Definition via terraform as multinode job type is not supported via terraform at the point of writing
- Job Definition will require a minimum of 2 nodes, using container image icern/locust-aws:latest
- Does not seem to work with A1 instances, even though it is accepted in configuration
- VPC must allow internet access. This is a ECS cluster requirement
- ECS cluster must sit in a private subnet behind a NAT gateway, else there will be no internet access from the tasks
- Structured stats are printed to console. This will allow cloudwatch to process logs into metrics
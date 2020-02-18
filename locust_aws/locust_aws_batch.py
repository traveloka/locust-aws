import sys
import configargparse
from locust import main as locust_main, runners
from locust.log import console_logger
from .git_locust_file_selector import GitLocustFileSelectorMiddleware
from .locust_file_selector import LocustFileSelectorPipeline
import atexit
import os
import six
import json
import boto3
from datetime import datetime
import tempfile


# Inputs
# host
# git url to file
# users
# hatch rate
# running time
# expected number of slaves (master node only) -> AWS_BATCH_JOB_NUM_NODES
# master node url (slave node only) -> AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS


def parse_options():
    parser = configargparse.ArgumentParser()
    parser.add_argument('-H', '--host', required=True, help='Host to load test on')
    parser.add_argument('-f', '--locustfile-source',
                        required=True,
                        help='locust file source to load file from. Only git is support at '
                             'this point in time. Use the same syntax as terraform module '
                             'source')
    parser.add_argument(
        '--master-host',
        help="Host or IP address of locust master for distributed load testing."
    )
    parser.add_argument(
        '--expect-slaves',
        type=int,
        help="How many slaves master should expect to connect before starting the test"
    )
    # Number of clients
    parser.add_argument(
        '-c', '--clients',
        dest='num_clients',
        default='1',
        help="Number of concurrent Locust users"
    )

    # Client hatch rate
    parser.add_argument(
        '-r', '--hatch-rate',
        default='1',
        help="The rate per second in which clients are spawned"
    )

    # Time limit of the test run
    parser.add_argument(
        '-t', '--run-time',
        help="Stop after the specified amount of time, e.g. (300s, 20m, 3h, 1h30m, etc.)."
    )

    parser.add_argument(
        '--cloudwatch-metric-ns',
        help="Namespace to publish cloudwatch metrics to. Publishes only when namespace is set"
    )

    parser.add_argument(
        '--ssh-pvt-key-ssm-param-name',
        help="SSM parameter name to get private key from"
    )

    opt = parser.parse_args()
    opt.master_host = opt.master_host or os.environ.get('AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS')

    def get_slave_count_from_env():
        num_nodes = os.environ.get('AWS_BATCH_JOB_NUM_NODES')
        return str(int(num_nodes) - 1) if num_nodes is not None else None

    opt.expect_slaves = opt.expect_slaves or (get_slave_count_from_env() if opt.master_host is None else None)
    return opt


PERCENTILES_TO_REPORT = [
    0.50,
    0.66,
    0.75,
    0.80,
    0.90,
    0.95,
    0.98,
    0.99,
    0.999,
    0.9999,
    0.99999,
    1.0
]


def main():
    options = parse_options()

    ssh_pvt_key_ssm_param_name = options.ssh_pvt_key_ssm_param_name

    def get_ssh_identity_file():
        if ssh_pvt_key_ssm_param_name is not None:
            ssm = boto3.client('ssm')
            ssh_pvt_key = ssm.get_parameter(Name=ssh_pvt_key_ssm_param_name, WithDecryption=True)['Parameter']['Value']
            fd, file_name = tempfile.mkstemp()
            with open(file_name, 'w') as file:
                file.write(ssh_pvt_key)
                os.close(fd)
                return file_name
        return None

    ssh_identity_file = get_ssh_identity_file()

    locustfile_selector = LocustFileSelectorPipeline(
        [GitLocustFileSelectorMiddleware(ssh_identity_file=ssh_identity_file)])

    locustfile_source = locustfile_selector.select(options.locustfile_source)

    locusfile = locustfile_source.fetch()

    def get_percentiles(stat_entry):
        return {str(e) + '%': stat_entry.get_response_time_percentile(e) for e in PERCENTILES_TO_REPORT}

    def print_formatted_stats_on_primary_node(stats):
        if options.master_host is not None:  # Slave mode. Do not print stats on slaves
            return
        for key in sorted(six.iterkeys(stats.entries)):
            item = stats.entries[key]
            console_logger.info(json.dumps({**{
                "locust_stat_type": "standard",
                "rps": item.total_rps
            }, **item.serialize()}))

        percentile_stats = [{**{
            "locust_stat_type": "percentile",
            "name": stats.entries[key].name,
            "method": stats.entries[key].method,
            "num_request": stats.entries[key].num_requests
        }, **get_percentiles(stats.entries[key])} for key in sorted(six.iterkeys(stats.entries))]
        for item in percentile_stats:
            console_logger.info(json.dumps(item))

    def create_standard_metric_data(stat_entry):
        return [
            {
                'MetricName': 'Req/s', 'Value': stat_entry.total_rps,
                'Unit': 'Count/Second'
            },
            {
                'MetricName': 'Min Response Time',
                'Value': stat_entry.min_response_time,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'Max Response Time',
                'Value': stat_entry.max_response_time,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'Avg Response Time',
                'Value': stat_entry.avg_response_time,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'Median Response Time',
                'Value': stat_entry.median_response_time,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'Total Requests',
                'Value': stat_entry.num_requests,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Total Failed Requests',
                'Value': stat_entry.num_failures,
                'Unit': 'Count'
            },
        ]

    def create_percentile_metric_data(stat_entry):
        return [{
            'MetricName': str(p * 100) + '% Latency',
            'Value': stat_entry.get_response_time_percentile(p),
            'Unit': 'Percent'
        } for p in PERCENTILES_TO_REPORT]

    def create_metric_data(stat_entry):
        timestamp = datetime.utcnow()

        return list(map(lambda e: {**e, **{
            'Timestamp': timestamp,
            'Dimensions': [
                {
                    'Name': 'Method',
                    'Value': stat_entry.method
                },
                {
                    'Name': 'Name',
                    'Value': stat_entry.name
                },
                {
                    'Name': 'Host',
                    'Value': options.host
                }]}}, create_standard_metric_data(stat_entry) + create_percentile_metric_data(stat_entry)))

    cloudwatch = None

    def ensure_cloudwatch_client_created():
        nonlocal cloudwatch
        if cloudwatch is not None:
            return
        cloudwatch = boto3.client('cloudwatch')

    def report_to_cloudwatch_metrics(stats):
        namespace = options.cloudwatch_metric_ns
        if namespace is None:
            return

        if options.master_host is None:  # represents that this is the master node. Report metrics only for master nodes
            return
        ensure_cloudwatch_client_created()
        for entry in six.itervalues(stats.entries):
            metric_data = create_metric_data(entry)
            cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)

    def on_exit(**kwargs):
        if ssh_identity_file is not None:
            os.remove(ssh_identity_file)
        locustfile_source.cleanup()
        print_formatted_stats_on_primary_node(runners.locust_runner.stats)
        report_to_cloudwatch_metrics(runners.locust_runner.stats)
        console_logger.info('exiting')

    argv = [sys.argv[0], '-f', locusfile, '--no-web', '-c', options.num_clients, '-r', options.hatch_rate,
            '-H', options.host]

    if options.expect_slaves is not None:
        argv += ['--master', '--expect-slaves', str(options.expect_slaves)]

    if options.master_host is not None:
        argv += ['--slave', '--master-host', str(options.master_host)]
    else:
        argv += ['--run-time', options.run_time]

    sys.argv = argv

    atexit.register(on_exit)
    console_logger.info('starting')
    locust_main.main()

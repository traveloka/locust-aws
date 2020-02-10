from setuptools import find_packages, setup

setup(name='locust-aws',
      version='1.0',
      description='locust on AWS',
      author='Jin',
      url='https://github.com/jinhong-/locust-aws',
      packages=['locust_aws'],
      install_requires=['locustio==0.14.4', 'ConfigArgParse==1.0', 'GitPython==3.0.5', 'six==1.14.0', 'boto3==1.11.12'],
      include_package_data=True,
      zip_safe=False,
      python_requires=">=3.6",
      entry_points={
          'console_scripts': [
              'locust-aws = locust_aws.locust_aws_batch:main',
          ]
      })

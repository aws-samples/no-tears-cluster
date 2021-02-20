# This is the global package version number.
# - Used by setup.py to control package build.
# - Used by pcluster/pcluster_stack.py to adjust default Parameter values
# - Used by upload.sh and report_s3.py to control asset publication on S3
#   NOTE: synthesized CDK assets are published to s3://BUCKET/__version__/ prefix
#
# Semantic Versioning: MAJOR.MINOR.PATCH
__version__ = '0.2.3'


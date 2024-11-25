import boto3
import pytest
from botocore.exceptions import ClientError
import json
from s3_helpers import(
    create_bucket_versioning,
)
#use sleep()


#Create
#Recover
#Delete old versions


#Structure:
#    VersionId
#    DeleteMarker
#    ObjectName

dict_vesioning = {
    'Status': 'Enabled'
}


def test_create_bucket_versioning(s3_client, bucket_with_one_object):
    bucket_name, object_key, content = bucket_with_one_object
    assert create_bucket_versioning(s3_client, bucket_name, dict_vesioning)



#def test_retrieve_bucket_vesioning(s3_client, bucket_with_one_object, ):
    
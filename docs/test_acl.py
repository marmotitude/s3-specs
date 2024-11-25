import boto3
import pytest
from botocore.exceptions import ClientError
from s3_helpers import(
    put_object_and_wait
)
#use sleep()

def test_create_delete_bucket(existing_bucket_name):
    assert existing_bucket_name

@pytest.mark.parametrize("acl_name",['private','public-read','public-read-write','authenticated-read','""',"''"])

def test_setup_bucket_acl(s3_client, existing_bucket_name, acl_name):
    try:
        s3_client.put_bucket_acl(Bucket = existing_bucket_name, ACL = acl_name)
    except ClientError as e:
        assert e.response['Error']['Code'] == "InvalidArgument"
    except ClientError as e:
        assert e.response['Error']['Code'] == 'BucketNotExists'


#discover how to use only parametrize multiple times across the script
@pytest.mark.parametrize("acl_name",['private','public-read','public-read-write','authenticated-read','""',"''"])

#define more varieties of json  (deny, block)
def test_access_bucket_with_acl(multiple_s3_client, existing_bucket_name, acl_name):
    try:
        test_setup_bucket_acl(multiple_s3_client[0], existing_bucket_name, acl_name)
        put_object_and_wait(multiple_s3_client[1], existing_bucket_name, "conftest.py")
        pytest.fail("Error not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == "AccessDeniedByBucketPolicy"



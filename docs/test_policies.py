import pytest
from botocore.exceptions import ClientError
import json
from s3_helpers import(
    put_object_and_wait
)



policy_read ='''{
    "Version": "2012-10-18",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "meu-bucket/*"
        }
    ]
}'''

false_policy = """{
    "Version": "2012-10-18",
    "Statement": [
        {
            ¨¨ dsa
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "vosso-bucket/*"
        }
    ]
}
"""

json_read = """{
    "Version": "2012-10-18",
    "Statement": 
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "teu-bucket/*"
        }
    ]
}
"""

cases = [
    *[(case, "MalformedJSON") for case in ['', 'jason',"''", json_read,false_policy]],
    *[(case, "MalformedPolicy") for case in ['{}','""', policy_read]],
 ]   

@pytest.mark.parametrize('input, expected_error', cases)

def test_put_invalid_bucket_policy(s3_client, existing_bucket_name, input, expected_error):
    try:
        s3_client.put_bucket_policy(Bucket=existing_bucket_name, Policy=input)
        pytest.fail("Expected exception not raised")
    except ClientError as e:
        # Assert the error code matches the expected one 
        assert e.response['Error']['Code'] == expected_error



dict_test = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "meu-bucket/*"
        }
    ]
}

@pytest.mark.parametrize('actions', [
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:GetObject",
])
   # ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"] s new bucket


def test_setup_policies(s3_client, existing_bucket_name, actions):
    bucket_name = existing_bucket_name

    #given a existent and valid bucket
    dict_test["Statement"][0]["Resource"] = existing_bucket_name + "/*"
    dict_test["Statement"][0]["Action"] = actions

    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(dict_test))
    #except ClientError as e:
    #    assert e.response['Error']['Code'] == "Forbidden"
    except ClientError as e:
        assert e.response['Error']['Code'] == 'BucketNotExists'

    
@pytest.mark.parametrize('actions, expected_output', [
    ("s3:PutObject", 'AccessDeniedByBucketPolicy'),
    ("s3:DeleteObject", 'AccessDeniedByBucketPolicy'),
    ("s3:GetObject", 'AccessDeniedByBucketPolicy'),
])
## secure that there are object to be deleted and gotten

#add custom json with deny to this test
def test_access_buckets_with_policies(s3_client, existing_bucket_name, actions, expected_output):
    try:
        test_setup_policies(s3_client, existing_bucket_name, actions)
        put_object_and_wait(s3_client, existing_bucket_name, "conftest.py")
        pytest.fail("Error not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == expected_output


#Follow-up error (that one)
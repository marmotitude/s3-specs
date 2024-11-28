import pytest
from botocore.exceptions import ClientError
from s3_helpers import(
    change_policies_json,
    put_object_and_wait,
    delete_object_and_wait,
)



malformed_policy_json ='''{
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

typo_policy = """{
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

wrong_date_policy = """{
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

policy_dict = {
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


cases = [
    *[(case, "MalformedJSON") for case in ['', 'jason',"''", typo_policy, wrong_date_policy]],
    *[(case, "MalformedPolicy") for case in ['{}','""', malformed_policy_json]],
 ]   

@pytest.mark.parametrize('input, expected_error', cases)

# Asserting the possible combinations that are allowed as policy arguments
def test_put_invalid_bucket_policy(s3_client, existing_bucket_name, input, expected_error):
    try:
        s3_client.put_bucket_policy(Bucket=existing_bucket_name, Policy=input)
        pytest.fail("Expected exception not raised")
    except ClientError as e:
        # Assert the error code matches the expected one 
        assert e.response['Error']['Code'] == expected_error


@pytest.mark.parametrize('policies_args', [
    {"policy_dict": policy_dict, "actions": "s3:PutObject", "effect": "Deny"},
    {"policy_dict": policy_dict, "actions": "s3:GetObject", "effect": "Deny"},
    {"policy_dict": policy_dict, "actions": "s3:DeleteObject", "effect": "Deny"}
])

def test_setup_policies(s3_client, existing_bucket_name, policies_args):
    bucket_name = existing_bucket_name

    #given a existent and valid bucket
    policies = change_policies_json(existing_bucket_name, policies_args)
    assert s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policies)

    
@pytest.mark.parametrize('bucket_with_policy, expected_output', [
    ({"policy_dict": policy_dict, "actions": "s3:PutObject", "effect": "Deny"}, "AccessDeniedByBucketPolicy"),
    ({"policy_dict": policy_dict, "actions": "s3:GetObject", "effect": "Deny"}, "AccessDeniedByBucketPolicy"),
    ({"policy_dict": policy_dict, "actions": "s3:DeleteObject", "effect": "Deny"}, "AccessDeniedByBucketPolicy")
], indirect = ['bucket_with_policy'])

#add custom json with deny to this test
def test_operations_bucket_policies(s3_client, bucket_with_policy, expected_output):
    
    bucket_name = bucket_with_policy
    object_key = "PolicyObject.txt"
    
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body='42')
        s3_client.get_object(Bucket=bucket_name, Key=object_key)
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        pytest.fail("Error not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == expected_output


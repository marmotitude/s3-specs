import pytest
import logging
from botocore.exceptions import ClientError
from s3_helpers import(
    change_policies_json,
)

# # Policy Tests

# ### Test Variables
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

wrong_date_policy = """{
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

# ## Asserting the possible combinations that are allowed as policy arguments
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
# ## Base case of putting a policy into a bcuket
def test_setup_policies(s3_client, existing_bucket_name, policies_args):
    bucket_name = existing_bucket_name

    #given a existent and valid bucket
    policies = change_policies_json(existing_bucket_name, policies_args)
    assert s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policies)

# # Tests related to actions on the bucket
    
@pytest.mark.parametrize('bucket_with_one_object_policy, boto3_action', [
    ({"policy_dict": policy_dict, "actions": "s3:PutObject", "effect": "Deny"}, 'put_object'),
    ({"policy_dict": policy_dict, "actions": "s3:GetObject", "effect": "Deny"}, 'get_object'),
    ({"policy_dict": policy_dict, "actions": "s3:DeleteObject", "effect": "Deny"}, 'delete_object')
], indirect = ['bucket_with_one_object_policy'])

# ## Asserting if the owner has permissions blocked from own bucket
def test_denied_policy_operations_by_owner(s3_client, bucket_with_one_object_policy, boto3_action):
    bucket_name, object_key = bucket_with_one_object_policy
    kwargs = {
        'Bucket': bucket_name,  # Set 'Bucket' value from the variable
        'Key': object_key
    }

    #PutObject needs another variable
    if boto3_action == 'put_object' :
        kwargs['Body'] = 'The answer for everthong is 42'
        
    #retrieve the method passed as argument
    method = getattr(s3_client, boto3_action)
    try:
        method(**kwargs)
        logging.info(method)
        pytest.fail("Expected exception not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == 'AccessDeniedByBucketPolicy'


@pytest.mark.parametrize('bucket_with_one_object_policy, boto3_action', [
    ({"policy_dict": policy_dict, "actions": "s3:PutObject", "effect": "Allow", "Principal": "*"}, 'put_object'),
    ({"policy_dict": policy_dict, "actions": "s3:GetObject", "effect": "Allow", "Principal": "*"}, 'get_object'),
    ({"policy_dict": policy_dict, "actions": "s3:DeleteObject", "effect": "Allow", "Principal": "*"}, 'delete_object')
], indirect = ['bucket_with_one_object_policy'])

# ## Asserting if the owner has permissions blocked from own bucket
def test_allow_policy_operations_by_owner(s3_client, bucket_with_one_object_policy, boto3_action):
    bucket_name, object_key = bucket_with_one_object_policy

    kwargs = {
        'Bucket': bucket_name,  # Set 'Bucket' value from the variable
        'Key': object_key
    }

    #PutObject needs another variable
    if boto3_action == 'put_object' :
        kwargs['Body'] = 'The answer for everthong is 42'
        
    #retrieve the method passed as argument
    method = getattr(s3_client, boto3_action)
    assert method(**kwargs)



    
    
    

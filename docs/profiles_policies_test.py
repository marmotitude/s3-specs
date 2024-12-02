import pytest
from botocore.exceptions import ClientError


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


# override s3_client fixture to return multiple clients
@pytest.fixture
def s3_client(multiple_s3_clients):
    return multiple_s3_clients[0]

tenant = {"MGC":["b39b111a-0264-43a8-ae01-c1bb15c8e259"]}



# Example of the list for actions, tenants, and methods
actions = [["s3:GetObject", tenant], ["s3:PutObject", tenant], ["s3:DeleteObject", tenant]]
multiple_s3_clients_list = ["br-ne1", "br-ne1-2"]
methods = ["get_object", "put_object", "delete_object"]

@pytest.mark.parametrize(
    'bucket_with_one_object_policy, multiple_s3_clients, boto3_action',
    [
        (
            {"policy_dict": policy_dict, "actions": action, "effect": "Deny"},
            {"profiles": multiple_s3_clients_list},
            method
        )
        for action, method in zip(actions, methods)
    ],
    indirect=['bucket_with_one_object_policy', 'multiple_s3_clients'],
)


def test_denied_policy_operations(multiple_s3_clients, bucket_with_one_object_policy, boto3_action):
    s3_clients_list = multiple_s3_clients
    
    bucket_name, object_key = bucket_with_one_object_policy

    kwargs = {
        'Bucket': bucket_name,  # Set 'Bucket' value from the variable
        'Key': object_key
    }

    #PutObject needs another variable
    if boto3_action == 'put_object' :
        kwargs['Body'] = 'The answer for everthong is 42'
        
    #retrieve the method passed as argument
    
    try:
        method = getattr(s3_clients_list[0], boto3_action)
        method(**kwargs)
        pytest.fail("Expected exception not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == 'AccessDeniedByBucketPolicy'






@pytest.mark.parametrize(
    'bucket_with_one_object_policy, multiple_s3_clients, boto3_action',
    [
        (
            {"policy_dict": policy_dict, "actions": action, "effect": "Allow"},
            {"profiles": multiple_s3_clients_list},
            method
        )
        for action, method in zip(actions, methods)
    ],
    indirect=['bucket_with_one_object_policy', 'multiple_s3_clients'],
)


def test_allowed_policy_operations(multiple_s3_clients, bucket_with_one_object_policy, boto3_action):
    s3_clients_list = multiple_s3_clients
    
    bucket_name, object_key = bucket_with_one_object_policy

    kwargs = {
        'Bucket': bucket_name,  # Set 'Bucket' value from the variable
        'Key': object_key
    }

    #PutObject needs another variable
    if boto3_action == 'put_object' :
        kwargs['Body'] = 'The answer for everthong is 42'
        
    #retrieve the method passed as argument
    
    try:
        method = getattr(s3_clients_list[0], boto3_action)
        method(**kwargs)
        pytest.fail("Expected exception not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == 'AccessDeniedByBucketPolicy'

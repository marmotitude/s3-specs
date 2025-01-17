import uuid
import os

# Function is responsible to check and format bucket names into valid ones

def generate_valid_bucket_name(base_name="my-unique-bucket"):
    """
    Generate a random sufix and valid s3 compatible bucket name from a given base_name. 
    This functions gets rid of any unique "." occurrences.
    :param base_name: str: base_name which must be a string or compatible with string conversion
    :return: str: valid s3 bucket name
    """

    unique_id = uuid.uuid4().hex[:6]  # Short unique suffix

    # assuring base name is a string
    try:
        base_name = ("test-" + str(base_name) + unique_id).lower()
    except Exception as e:
        raise Exception(f"Error converting base_name to string: {e}")

    new_name = []

    for char in base_name:
        if ((char >= 'a' and char <= 'z') or (char >= '0' and char <= '9') or char == '-'):
            new_name.append(char)


    return "".join(new_name)

# Function which will be using to create mock files with different sizes

def create_big_file(file_path, size = 1, unit='MB'):
    """
    Create a big file with the specified size in the specified path
    :param file_path: str: path to the file to be created
    :param size: int: size of the file to be created
    :param unit: str: unit of the size, default is MB
    :return: None
    """

    size = 1024 

    units = {
        'kb': 1024,
        'mb': 1024 * 1024,
        'mb': 1024 * 1024 * 1024,
    }

    if unit.lower() not in units:
        raise Exception(f"Invalid unit: {unit}")
    
    # Creating a file of size * unit
    size = size * units[unit.lower()]
    with open(file_path, 'wb') as file:
        file.write(b'a' * size)

    # yielding to the calling function
    try:
        yield file_path
    finally:
        os.remove(file_path)
def add_slash(path):
    """
    Adds a slash to the end of a path if not there already. 
    
    Args:
        path (str): The path to check. 

    Returns:
        path (str): The path terminating with a slash. 
    """

    if not path.endswith("/"):
        path += "/"
    return path 

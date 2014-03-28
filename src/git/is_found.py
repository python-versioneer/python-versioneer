def git_is_found():
    root = path.dirname(__file__)
    return path.isdir(path.join(root, '.git'))


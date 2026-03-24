import pathlib

#to get absolute path - resolve path of executable file and remove file from path
def resolve_absolute_path_of_executables():
    file_path = pathlib.Path(__file__).resolve()
    path_elements = str(file_path).split('/')
    elements_counter  = 0
    folders_path = ''
    for element in path_elements:
        if elements_counter < (len(path_elements) - 1):
            folders_path += element + '/'
            elements_counter += 1
    return folders_path
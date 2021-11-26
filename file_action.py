class FileAction:
    RENAME_MOVE = 'r' # Rename or move the file
    DELETE = 'd'      # Delete the file
    COPY = 'c'        # Copy the file
    LINK = 'l'        # Create a symbolic link to the file
    IGNORE = 'i'      # Do not do anything with the file, but keep it in the index

    ALL_ACTIONS=[
            RENAME_MOVE,
            DELETE,
            COPY,
            LINK,
            IGNORE]



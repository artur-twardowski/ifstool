from os.path import join, dirname
from os import walk
from importlib import import_module

class ExtensionParam:
    def __init__(self, name, description, **kwargs):
        self.name = name
        self.description = description
        if "default" in kwargs:
            self.default_value = kwargs["default"]
        else:
            self.default_value = None

        if "values" in kwargs:
            self.enum_values = kwargs["values"]
        else:
            self.enum_values = None

class Extension:
    def on_name_query(self): 
        """
        Returns the full name of the extension. Must be implemented.

        Returns:
        str:Extension name
        """
        pass

    def on_description_query(self): 
        """
        Returns the description of the extension. Must be implemented.

        Returns:
        str:Extension description
        """
        pass

    def on_params_query(self):
        """
        Returns the list of parameters supported by the extension.

        Returns:
        list:List of ExtensionParam objects
        """
        return []

    def on_params_passed(self, params:dict):
        """
        Invoked after the extension is loaded.

        Parameters:
        params: A dictionary consisting of parameters passed as an input

        Returns:
        None if the parameters are correct. A string with an error message if
        one or more parameters have incorrect values.
        """
        return None

    def before_file_added(self, filename):
        """
        Invoked for each file encountered before its entry is created and added
        to the index. Allows to filter the files in the index, discarding selected
        ones.

        Parameters:
        filename: Name of the file added to the index

        Returns:
        True if the file is to be added to the index. False if the file has to be discarded.
        """
        return True
    
    def after_file_added(self, entry):
        """
        Invoked for each file encountered right after it is added to the index.
        Allows to assign a single file to a group or build its metadata information.
        """
        pass

    def on_index_complete(self, index):
        """
        Invoked after all the files are added to the index. Allows to manipulate the index
        when its complete shape is already known.
        """

    def before_file_ops(self, entry):
        """
        Invoked for each file in the index before the rename/move/copy/link operations
        are triggered. The metadata is already processed and updated.
        """
        pass

    def after_file_ops(self, entry, new_file_name):
        """
        Invoked for each file in the index after the rename/move/copy/link operations
        are triggered.
        """

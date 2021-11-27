from file_action import FileAction

class Configuration:
    def __init__(self):
        self.default_action = FileAction.RENAME_MOVE
        self.use_absolute_paths = False
        self.include_directories = False
        self.prompt_on_actions = True
        self.simulation_mode = False
        self.multistage_mode = False
        self.create_directories = False
        self.allow_overwriting = False
        self.extensions_chain = []


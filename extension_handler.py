from os_abstraction import IOSAbstraction
from configuration import Configuration
from extension import Extension, ExtensionParam
from extensions.df import Extension_df
from extensions.cadf.audio import Extension_cadf_audio

def validate_and_fill(params_dict: dict, extension_interface: list):
    for ext_param in extension_interface:
        assert(isinstance(ext_param, ExtensionParam))
        if ext_param.name not in params_dict and ext_param.default_value is not None:
            params_dict[ext_param.name] = ext_param.default_value

        if ext_param.enum_values is not None:
            if params_dict[ext_param.name] not in ext_param.enum_values:
                valid_items = ""
                for val in ext_param.enum_values:
                    valid_items += val+ ", "
                valid_items = valid_items[:-2]
                print("Invalid value of %s: %s. Valid values are: %s" % (
                    ext_param.name,
                    params_dict[ext_param.name],
                    valid_items))
    return params_dict


def get_extensions():
    extensions = {
            "df": Extension_df,
            "cadf.audio": Extension_cadf_audio
            }
    return extensions


def use_extension(config: Configuration, os: IOSAbstraction, ext_str: str):
    exts = get_extensions()

    if ext_str.find(':') != -1:
        ext_name, ext_param_str = ext_str.split(':', 1)
    else:
        ext_name = ext_str
        ext_param_str = None

    if ext_name in exts:
        extension_obj = exts[ext_name]()
        if ext_param_str == "help":
            show_extension_info(extension_obj)
            exit(1)
        elif ext_param_str is not None:
            params = ext_param_str.split(' ')
            params_dict = {}
            for param in params:
                if '=' in param:
                    key, value = param.split('=', 1)
                else:
                    key = param
                    value = None
                params_dict[key] = value

            params_dict = validate_and_fill(params_dict, extension_obj.on_params_query())
            print(params_dict)
            extension_obj.on_params_passed(params_dict)
        config.extensions_chain.append(extension_obj)
    else:
        os.show_error("No such extension: %s" % ext_name)
        exit(1)


def show_extension_info(ext: Extension):
    print("Extension %s" % ext.on_name_query())
    print(ext.on_description_query())

    params = ext.on_params_query()
    if len(params) > 0:
        print("Parameters:")
        for param in params:
            assert(isinstance(param, ExtensionParam))
            print("  %-14s %s" % (param.name, param.description))
            if param.enum_values is not None:
                print(" "*17 + "Possible values:")
                for value, description in param.enum_values.items():
                    print(" "*17 + "  %-14s %s" % (value, description))
            if param.default_value is not None:
                print(" "*17 + "Default value: %s" % param.default_value)


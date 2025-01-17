from utils import _set_paths

_set_paths()

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

arbitrum_config_object = ConfigManager(chain='arbitrum')

# Call this method to set your config object attributes from a config file
# Can also pass kwarg 'filepath' to specify path to config file
arbitrum_config_object.set_config()

# overwrite object attributes like so
arbitrum_config_object.set_rpc('https://test.org')
print(arbitrum_config_object.rpc)

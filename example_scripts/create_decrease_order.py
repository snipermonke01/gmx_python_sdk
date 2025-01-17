from utils import _set_paths

_set_paths()

from gmx_python_sdk.scripts.v2.order.create_decrease_order import DecreaseOrder
from gmx_python_sdk.scripts.v2.order.order_argument_parser import (
    OrderArgumentParser
)

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager(chain='arbitrum')
config.set_config()


# Example of passing arguments through the Order parser to close the desired position
parameters = {
    "chain": 'arbitrum',

    "index_token_symbol": "SOL",

    "collateral_token_symbol": "SOL",

    # set start token the same as your collateral
    "start_token_symbol": "SOL",

    "is_long": True,

    # amount of your position you want to close in USD
    "size_delta_usd": 3,

    # amount of tokens NOT USD you want to remove as collateral.
    "initial_collateral_delta": 0.027,

    # as a percentage
    "slippage_percent": 0.03
}

order_parameters = OrderArgumentParser(
    config,
    is_decrease=True).process_parameters_dictionary(parameters)

order = DecreaseOrder(
    config=config,
    market_key=order_parameters['market_key'],
    collateral_address=order_parameters['collateral_address'],
    index_token_address=order_parameters['index_token_address'],
    is_long=order_parameters['is_long'],
    size_delta=order_parameters['size_delta'],
    initial_collateral_delta_amount=order_parameters['initial_collateral_delta'],
    slippage_percent=order_parameters['slippage_percent'],
    swap_path=[],
    debug_mode=True
)

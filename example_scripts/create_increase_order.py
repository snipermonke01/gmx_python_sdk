from utils import _set_paths

_set_paths()

from gmx_python_sdk.scripts.v2.order.order_argument_parser import (
    OrderArgumentParser
)
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

arbitrum_config_object = ConfigManager(chain='arbitrum')
arbitrum_config_object.set_config()

parameters = {
    "chain": 'arbitrum',

    # the market you want to trade on
    "index_token_symbol": "GMX",

    # token to use as collateral. Start token swaps into collateral token
    # if different
    "collateral_token_symbol": "GMX",

    # the token to start with - WETH not supported yet
    "start_token_symbol": "USDC",

    # True for long, False for short
    "is_long": False,

    # Position size in in USD
    "size_delta_usd": 5,

    # if leverage is passed, will calculate number of tokens in
    # start_token_symbol amount
    "leverage": 1,

    # as a decimal ie 0.003 == 0.3%
    "slippage_percent": 0.003
}


order_parameters = OrderArgumentParser(
    arbitrum_config_object,
    is_increase=True
).process_parameters_dictionary(
    parameters
)

order = IncreaseOrder(
    config=arbitrum_config_object,
    market_key=order_parameters['market_key'],
    collateral_address=order_parameters['start_token_address'],
    index_token_address=order_parameters['index_token_address'],
    is_long=order_parameters['is_long'],
    size_delta=order_parameters['size_delta'],
    initial_collateral_delta_amount=(
        order_parameters['initial_collateral_delta']
    ),
    slippage_percent=order_parameters['slippage_percent'],
    swap_path=order_parameters['swap_path'],
    debug_mode=True,
    execution_buffer=1.5
)

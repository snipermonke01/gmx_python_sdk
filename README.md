
# GMX Python SDK

A python based SDK developed for interacting with GMX v2

- [Pip Install](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#pip-install)
- [Requirements](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#requirements)
- [Config File Setup](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#config-file-setup)
- [Example Scripts](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#example-scripts)
- [General Usage](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#general-usage)
    - [Increase Position](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#increase-position)
    - [Decrease Position](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#decrease-position)
    - [Swap Order](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#swap-order)
    - [Deposit Order](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#deposit-order)
    - [Withdraw Order](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#withdraw-order)
    - [Estimate Swap Output](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#estimate-swap-output)
    - [Helper Scripts](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#helper-scripts)
        - [Order Argument Parser](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#order-argument-parser)
        - [Liquidity Argument Parser](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#liquidity-argument-parser)
        - [Closing Positions](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#closing-positions)
    - [GMX Stats](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#gmx-stats)
    - [Debug Mode](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#debug-mode)
- [Known Limitations](https://github.com/snipermonke01/gmx_python_sdk/tree/main?tab=readme-ov-file#known-limitations)

## Pip Install

The SDK can be installed via pip:

```
pip install gmx-python-sdk
```

## Requirements

Developed using:
```python
  python=3.10.4
```

If not using the pip method to install package you may also try creating a new conda environment step by step with the following instructions:
```
conda create --name gmx_sdk python=3.10
conda activate gmx_sdk
pip install numpy
pip install hexbytes
pip install web3==6.10.0
pip install pyaml
pip install pandas==1.4.2
pip install numerize
```

The codebase is designed around the usage of web3py [6.10.0](https://web3py.readthedocs.io/en/stable/releases.html#web3-py-v6-10-0-2023-09-21), and will not work with older versions and has not been tested with the latest version.
## Config File Setup

[Config file](https://github.com/snipermonke01/gmx_python_sdk/blob/main/config.yaml) can be set before usage by editing the yaml file. For stats based operations, you will need only an RPC but for execution you need to save both a wallet address and the private key of that wallet. 

```yaml
rpcs:
  arbitrum: arbitrum_rpc
  avalanche: avax_rpc
chain_ids:
  arbitrum: 42161
  avalanche: 43114
private_key: private_key
user_wallet_address: user_wallet_address

```

The example script [setting_config.py](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/setting_config.py) can be viewed for demonstration on how to import config and update with new details from within a script.

There is an example in all the example scripts of how to import the config and init the object to pass to functions and classes through the SDK.

## Example Scripts

There are several example scripts which can be run and can be found in [example scripts.](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/) These are mostly for demonstration purposes on how to utilise the SDK, and can should be incoporated into your own scripts and strategies.


## General Usage

### [Increase Position](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/create_increase_order.py)

The following block demonstrates how to open (or increase) a position:

```python
from gmx_python_sdk_scripts.v2.order.create_increase_order import IncreaseOrder

order = IncreaseOrder(
    config=config,
    market_key=market_key,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta_usd=size_delta_usd,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=swap_path,
    debug_mode=debug_mode
)
```
**config** - *type obj*: an initialised config object (avalanche currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to increase a position on

**collateral_address** - *type str*: the contract address of the token you want to use as collateral

**index_token_address** - *type str*: the contract address of the token you want to trade

**is_long** - *type bool*: True for long or False for short

**size_delta_usd** - *type int*: the size of position you want to open 10^30

**initial_collateral_delta_amount** - *type int*: the amount of token you want to use as collateral, 10^decimal of that token

**slippage_percent** - *type float*: the percentage you want to allow slippage

**swap_path** - *type list(str)*: a list of the GMX markets you will need to swap through if the starting token is different to the token you want to use as collateral

**debug_mode** - *type bool*: set to true to create an order without submitting

### [Decrease Position](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/create_decrease_order.py)

The following block demonstrates how to close (or decrease) a position:

```python
from gmx_python_sdk_scripts.v2.order.create_decrease_order import DecreaseOrder

order = DecreaseOrder(
    config=config,
    market_key=market_key,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta_usd=size_delta_usd,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=swap_path,
    debug_mode=debug_mode
)
```
**config** - *type obj*: an initialised config object (avalanche currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to decrease a position for

**collateral_address** - *type str*: the contract address of the token you are using as collateral

**index_token_address** - *type str*: the contract address of the token are trading

**is_long** - *type bool*: True for long or False for short

**size_delta_usd** - *type int*: the size of the decrease to apply to your position, 10^30

**initial_collateral_delta_amount** - *type int*: the amount of collateral token you want to remove, 10^decimal of that token

**slippage_percent** - *type float*: the percentage you want to allow slippage

**swap_path** - *type list(str)*: a list of the GMX markets you will need to swap through to get your desired out token

**debug_mode** - *type bool*: set to true to create an order without submitting

### [Swap Order](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/create_swap_order.py)

The following block demonstrates how to make a swap:

```python
from gmx_python_sdk_scripts.v2.order.create_swap_order import SwapOrder

order = SwapOrder(
    config=config,
    market_key=market_key,
    start_token=start_token,
    out_token=out_token,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta=size_delta,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=swap_path,
    debug_mode=debug_mode
)
```
**config** - *type obj*: an initialised config object (avalanche currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to (first) market you want to swap through

**start_token** - *type str*: the contract address of the token you start the swap with

**out_token** - *type str*: the contract address of the token you want out

**collateral_address** - *type str*: the contract address of the token you start the swap with

**index_token** - *type str*: the contract address of the token you want out

**is_long** - *type bool*: set to False

**size_delta_usd** - *type int*: set to 0

**initial_collateral_delta_amount** - *type int*: the amount of start token you are swapping

**slippage_percent** - *type float*: the percentage you want to allow slippage

**swap_path** - *type list()*: list of gmx market address your swap will go through

**debug_mode** - *type bool*: set to true to create an order without submitting

### [Deposit Order](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/create_deposit_order.py)

The following block demonstrates how to make a deposit to a gm pool:

```python
from gmx_python_sdk_scripts.v2.order.create_deposit_order import DepositOrder

order = DepositOrder(
    config=config,
    market_key=market_key,
    initial_long_token=initial_long_token,
    initial_short_token=initial_short_token,
    long_token_amount=long_token_amount,
    short_token_amount=short_token_amount,
    debug_mode=debug_mode
)
```
**config** - *type obj*: an initialised config object (avalanche currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to deposit into

**initial_long_token** - *type str*: the contract address of the token you want to use to deposit into long side, can be None

**initial_short_token** - *type str*: the contract address of the token you want to use to deposit into short side, can be None

**long_token_amount** - *type str*: the amount of token to add to long side, can be 0

**short_token_amount** - *type str*: the amount of token to add to short side, can be 0

**debug_mode** - *type bool*: set to true to create an order without submitting

### [Withdraw Order](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/create_withdraw_order.py)

The following block demonstrates how to make a withdrawal from a gm pool:

```python
from gmx_python_sdk_scripts.v2.order.create_withdrawal_order import WithdrawOrder

order = WithdrawOrder(
    config=config,
    market_key=market_key,
    out_token=out_token,
    gm_amount=gm_amount,
    debug_mode=debug_mode
)
```
**config** - *type obj*: an initialised config object (avalanche currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to withdraw from

**out_token** - *type str*: the contract address of the token you want to use to receive

**gm_amount** - *type str*: amount of gm tokens to burn

**debug_mode** - *type bool*: set to true to create an order without submitting

### Estimate Swap output

Below shows an example of how to estimate swap output using the [EstimateSwapOutput](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/estimate_swap_output.py#L20) class in [estimate_swap_ouput.py](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/estimate_swap_output.py). One can provide either a token symbol or contract address for in and out tokens and the script will return a dictionary containing the estimate output number of tokens and price impact.

```python
from gmx_python_sdk.example_scripts.estimate_swap_output import EstimateSwapOutput
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager("arbitrum")
config.set_config()

in_token_symbol = "GMX"
out_token_symbol = "USDC"
token_amount = 10
in_token_address = None
out_token_address = None
token_amount_expanded = None

output = EstimateSwapOutput(config=config).get_swap_output(
     in_token_symbol=in_token_symbol,
     out_token_symbol=out_token_symbol,
     token_amount=token_amount,
     in_token_address=in_token_address,
     out_token_address=out_token_address,
     token_amount_expanded=token_amount_expanded
)

```

### Helper Scripts

To assist in argument formatting, there are a few helper functions:

#### [Order Argument Parser](https://github.com/snipermonke01/gmx_python_sdk/blob/main/gmx_python_sdk/scripts/v2/order/order_argument_parser.py)

Human readable numbers can be parsed in a dictionary with the following keys/values which are processed by a class, OrderArgumentParser. This class should initialised with a bool to indicate is_increase, is_decrease, or is_swap, calling the method: "process_parameters_dictionary". This will output a dictionary containing the user input parameters reformatted to allow for successful order creation.

For increase:


```python
from gmx_python_sdk.scripts.v2.order.order_argument_parser import OrderArgumentParser
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager("arbitrum")
config.set_config()

parameters = {
    "chain": 'arbitrum',

    # the market you want to trade on
    "index_token_symbol": "ARB",

    # the token you want as collateral
    "collateral_token_symbol": "ARB",

    # the token to start with
    "start_token_symbol": "USDC",

    # True for long, False for short
    "is_long": False,

    # in USD
    "size_delta": 6.69,

    # if leverage is passed, will calculate number of tokens in start_token_symbol amount
    "leverage": 1,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(
     config=config,
     is_increase=True
).process_parameters_dictionary(
     parameters
)
```

For decrease:

```python
from gmx_python_sdk.scripts.v2.order.order_argument_parser import OrderArgumentParser
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager("arbitrum")
config.set_config()

parameters = {
    "chain": 'arbitrum',
    "index_token_symbol": "ARB",

    "collateral_token_symbol": "USDC",

    # set start token the same as your collateral
    "start_token_symbol": "USDC",

    "is_long": False,

    # amount of your position you want to close in USD
    "size_delta": 12,

    # amount of collateral you want to remove in collateral tokens
    "initial_collateral_delta": 6,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(
     config=config,
     is_decrease=True
).process_parameters_dictionary(
     parameters
)
```
For Swap:

```python
from gmx_python_sdk.scripts.v2.order.order_argument_parser import OrderArgumentParser
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager("arbitrum")
config.set_config()

parameters = {
    "chain": 'arbitrum',

    # token to use as collateral. Start token swaps into collateral token if different
    "out_token_symbol": "ETH",

    # the token to start with - WETH not supported yet
    "start_token_symbol": "USDC",

    # True for long, False for short
    "is_long": False,

    # Position size in in USD
    "size_delta_usd": 0,

    # Amount of start tokens to swap out
    "initial_collateral_delta": 10,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(
     config=config,
     is_swap=True
).process_parameters_dictionary(
     parameters
)
```
#### [Liquidity Argument Parser](https://github.com/snipermonke01/gmx_python_sdk/blob/main/gmx_python_sdk/scripts/v2/order/liquidity_argument_parser.py)

Human readable numbers can be parsed in a dictionary with the following keys/values which are processed by a class, LiquidityArgumentParser. This class should initialised with a bool to indicate is_deposit or is_withdraw calling the method: "process_parameters_dictionary". This will output a dictionary containing the user input parameters reformatted to allow for successful deposit/withdrawal order creation.

For Deposit:

```python
from gmx_python_sdk.scripts.v2.order.liquidity_argument_parser import LiquidityArgumentParser
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager("arbitrum")
config.set_config()

parameters = {
    "chain": "arbitrum",
    "market_token_symbol": "ETH",
    "long_token_symbol": "ETH",
    "short_token_symbol": USDC,
    "long_token_usd": 10,
    "short_token_usd": 10
}

output = LiquidityArgumentParser(
     config=config,
     is_deposit=True
).process_parameters_dictionary(
     parameters
)
```


For Withdraw:

```python
from gmx_python_sdk.scripts.v2.order.liquidity_argument_parser import LiquidityArgumentParser
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

parameters = {
    "chain": "arbitrum",
    "market_token_symbol": "ETH",
    "out_token_symbol": "ETH",
    "gm_amount": 1
}

output = LiquidityArgumentParser(
     config=config,
     is_withdraw=True
).process_parameters_dictionary(
     parameters
)
```

#### Closing positions

Instead of passing the parameters to close a position, if you are aware of the market symbol and the direction of the trade you want to close you can pass these to [transform_open_position_to_order_parameters](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/get_positions.py#L51) after collecting all open positions using [get_positions](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/get_positions.py#L16). You can specify the amount of collateral or position size to remove/close as a decimal, eg 0.5 would close/remove 50% of size/collateral:

```python
from gmx_python_sdk.example_scripts.get_positions import get_positions, transform_open_position_to_order_parameters
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

config = ConfigManager(chain='arbitrum')
config.set_config()

address = None
market_symbol = "ETH"
out_token = "ETH"
is_long = False
slippage_percent = 0.003
amount_of_position_to_close = 1
amount_of_collateral_to_remove = 1

# gets all open positions as a dictionary, which the keys as each position
positions = get_positions(
     config=config,
     address=address
)

order_parameters = transform_open_position_to_order_parameters(
    config=config,
    positions=positions,
    market_symbol=market_symbol,
    is_long=is_long,
    slippage_percent=slippage_percent,
    out_token=out_token,
    amount_of_position_to_close=amount_of_position_to_close,
    amount_of_collateral_to_remove=amount_of_collateral_to_remove
)
```

### GMX Stats

A number of stats can be obtained using a wide range of scripts. The overview on how to call these can be found in [get_gmx_stats](https://github.com/snipermonke01/gmx_python_sdk/blob/main/example_scripts/get_gmx_stats.py). Each method returns a dictionary containing long/short information for a given chain. When initialising the class, pass to_json or to_csv as True to save the output to the [data store](https://github.com/snipermonke01/gmx_python_sdk/tree/main/gmx_python_sdk/data_store): 

```python
from gmx_python_sdk.example_scripts.get_gmx_stats import GetGMXv2Stats
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

to_json = False
to_csv = False

config = ConfigManager(chain='arbitrum')
config.set_config()

stats_object = GetGMXv2Stats(
     config=config,
     to_json=to_json,
     to_csv=to_csv
)

liquidity = stats_object.get_available_liquidity()
borrow_apr = stats_object.get_borrow_apr()
claimable_fees = stats_object.get_claimable_fees()
contract_tvl = stats_object.get_contract_tvl()
funding_apr = stats_object.get_funding_apr()
gm_prices = stats_object.get_gm_price()
markets = stats_object.get_available_markets()
open_interest = stats_object.get_open_interest()
oracle_prices = stats_object.get_oracle_prices()
pool_tvl = stats_object.get_pool_tvl()
```

### Debug Mode

It is possible to call IncreaseOrder, DecreaseOrder, SwapOrder, DepositOrder, and WithdrawOrder in debug mode by passing debug_mode=True when initialising the class:

```python
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder

order = IncreaseOrder(
    config=config,
    market_key=market_key,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta_usd=size_delta_usd,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=swap_path,
    debug_mode=True
)
```

This will allow you to submit parameters to the order class and build your txn without executing it.

### Known Limitations

- Avalanche chain not fully tested.
- A high rate limit RPC is required to read multiple sets of stats successively.
- Possible to specify out token not the long/short of the GM market when withdrawing,
  but it will fail and return GM tokens to users wallet.
- Testnet is currently NOT supported

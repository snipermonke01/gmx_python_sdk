from .keys import (
    decrease_order_gas_limit_key, increase_order_gas_limit_key,
    execution_gas_fee_base_amount_key, execution_gas_fee_multiplier_key,
    single_swap_gas_limit_key, swap_order_gas_limit_key, deposit_gas_limit_key,
    withdraw_gas_limit_key
)

from .gmx_utils import apply_factor, get_datastore_contract, create_connection


def get_execution_fee(gas_limits: dict, estimated_gas_limit, gas_price: int):
    """
    Given a dictionary of gas_limits, the uncalled datastore object of a given operation, and the
    latest gas price, calculate the minimum execution fee required to perform an action

    Parameters
    ----------
    gas_limits : dict
        dictionary of uncalled datastore limit obkects.
    estimated_gas_limit : datastore_object
        the uncalled datastore object specific to operation that will be undertaken.
    gas_price : int
        latest gas price.

    """

    base_gas_limit = gas_limits['estimated_fee_base_gas_limit'].call()
    multiplier_factor = gas_limits['estimated_fee_multiplier_factor'].call()
    adjusted_gas_limit = base_gas_limit + apply_factor(estimated_gas_limit.call(),
                                                       multiplier_factor)

    return adjusted_gas_limit * gas_price


def get_gas_limits(datastore_object):
    """
    Given a Web3 contract object of the datstore, return a dictionary with the uncalled gas limits
    that correspond to various operations that will require the execution fee to calculated for.

    Parameters
    ----------
    datastore_object : web3 object
        contract connection.

    """
    gas_limits = {
        "deposit": datastore_object.functions.getUint(deposit_gas_limit_key()),
        "withdraw": datastore_object.functions.getUint(withdraw_gas_limit_key()),
        "single_swap": datastore_object.functions.getUint(single_swap_gas_limit_key()),
        "swap_order": datastore_object.functions.getUint(swap_order_gas_limit_key()),
        "increase_order": datastore_object.functions.getUint(increase_order_gas_limit_key()),
        "decrease_order": datastore_object.functions.getUint(decrease_order_gas_limit_key()),
        "estimated_fee_base_gas_limit": datastore_object.functions.getUint(
            execution_gas_fee_base_amount_key()),
        "estimated_fee_multiplier_factor": datastore_object.functions.getUint(
            execution_gas_fee_multiplier_key())}

    return gas_limits


if __name__ == "__main__":

    chain = 'arbitrum'
    connection = create_connection(chain=chain)
    datastore_object = get_datastore_contract(chain)
    gas_limits = get_gas_limits(datastore_object)
    gas_price = connection.eth.gas_price
    execution_fee = int(get_execution_fee(gas_limits, gas_limits['increase_order'], gas_price))

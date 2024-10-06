import json
import os

from web3 import Web3

from .gmx_utils import (
    create_connection, base_dir, convert_to_checksum_address
)


def check_if_approved(
        config,
        spender: str,
        token_to_approve: str,
        amount_of_tokens_to_spend: int,
        max_fee_per_gas,
        approve: bool):
    """
    For a given chain, check if a given amount of tokens is approved for spend by a contract, and
    approve is passed as true

    Parameters
    ----------
    chain : str
        arbitrum or avalanche.
    spender : str
        contract address of the requested spender.
    token_to_approve : str
        contract address of token to spend.
    amount_of_tokens_to_spend : int
        amount of tokens to spend in expanded decimals.
    approve : bool
        Pass as True if we want to approve spend incase it is not already.

    Raises
    ------
    Exception
        Insufficient balance or token not approved for spend.

    """

    connection = create_connection(config)

    if token_to_approve == "0x47904963fc8b2340414262125aF798B9655E58Cd":
        token_to_approve = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"

    spender_checksum_address = convert_to_checksum_address(
        config, spender
    )

    # User wallet address will be taken from config file
    user_checksum_address = convert_to_checksum_address(
        config,
        config.user_wallet_address)

    token_checksum_address = convert_to_checksum_address(config, token_to_approve)

    token_contract_abi = json.load(open(os.path.join(
        base_dir,
        'gmx_python_sdk',
        'contracts',
        'token_approval.json'
    )))

    token_contract_obj = connection.eth.contract(address=token_to_approve,
                                                 abi=token_contract_abi)

    # TODO - for AVAX support this will need to incl WAVAX address
    if token_checksum_address == "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1":
        try:
            balance_of = connection.eth.getBalance(user_checksum_address)
        except AttributeError:
            balance_of = connection.eth.get_balance(user_checksum_address)

    else:
        balance_of = token_contract_obj.functions.balanceOf(user_checksum_address).call()

    if balance_of < amount_of_tokens_to_spend:
        raise Exception("Insufficient balance!")

    amount_approved = token_contract_obj.functions.allowance(
        user_checksum_address,
        spender_checksum_address
    ).call()

    print("Checking coins for approval..")
    if amount_approved < amount_of_tokens_to_spend and approve:

        print('Approving contract "{}" to spend {} tokens belonging to token address: {}'.format(
            spender_checksum_address, amount_of_tokens_to_spend, token_checksum_address))

        nonce = connection.eth.get_transaction_count(user_checksum_address)

        arguments = spender_checksum_address, amount_of_tokens_to_spend
        raw_txn = token_contract_obj.functions.approve(
            *arguments
        ).build_transaction({
            'value': 0,
            'chainId': config.chain_id,
            'gas': 4000000,
            'maxFeePerGas': int(max_fee_per_gas),
            'maxPriorityFeePerGas': 0,
            'nonce': nonce})

        signed_txn = connection.eth.account.sign_transaction(raw_txn,
                                                             config.private_key)
        tx_hash = connection.eth.send_raw_transaction(signed_txn.raw_transaction)

        print("Txn submitted!")
        print("Check status: https://arbiscan.io/tx/{}".format(tx_hash.hex()))

    if amount_approved < amount_of_tokens_to_spend and not approve:
        raise Exception("Token not approved for spend, please allow first!")

    print('Contract "{}" approved to spend {} tokens belonging to token address: {}'.format(
        spender_checksum_address, amount_of_tokens_to_spend, token_checksum_address))
    print("Coins Approved for spend!")


if __name__ == "__main__":

    pass

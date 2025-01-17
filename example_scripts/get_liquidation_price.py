from utils import _set_paths
from web3 import Web3
import hashlib
from hexbytes import HexBytes

_set_paths()

from get_positions import get_positions

from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from gmx_python_sdk.scripts.v2.gmx_utils import (
    ConfigManager, get_reader_contract, get_datastore_contract,
    get_tokens_address_dict)

from gmx_python_sdk.scripts.v2.keys import (
    min_collateral, accountPositionListKey,
    max_position_impact_factor_for_liquidations_key,
    min_collateral_factor_key)


from gmx_python_sdk.scripts.v2.get.get import GetData

from decimal import Decimal

# TODO - KNOWN ISSUES
# - Single Side Pools not working
# - markets beyond WIF not supported


def calculate_liquidation_price(
    datastore_obj,
    market_address,
    index_token_address,
    size_in_usd: Decimal,
    size_in_tokens: Decimal,
    collateral_amount: Decimal,
    collateral_usd: Decimal,
    collateral_token: dict,
    pending_funding_fees_usd: Decimal,
    pending_borrowing_fees_usd: Decimal,
    min_collateral_usd: Decimal,
    is_long: bool,
    use_max_price_impact: bool = False,
    user_referral_info: dict = None
) -> Decimal:

    print(f"collateral amount: {collateral_amount}")
    print(f"size in tokens: {size_in_tokens}")
    print(f"Funding Fees: {pending_funding_fees_usd}")
    print(f"Borrow Fees: {pending_borrowing_fees_usd}")

    if size_in_usd <= 0 or size_in_tokens <= 0:
        return None

    index_token = index_token_address

    closing_fee_usd = get_position_fee(size_in_usd,
                                       True,
                                       user_referral_info)['positionFeeUsd']

    total_pending_fees_usd = get_position_pending_fees_usd(
        pending_funding_fees_usd, pending_borrowing_fees_usd)

    total_fees_usd = total_pending_fees_usd + closing_fee_usd

    maxPositionImpactFactorForLiquidations = datastore_obj.functions.getUint(
        max_position_impact_factor_for_liquidations_key(market_address)
    ).call()

    # max_negative_price_impact_usd = -1 * \
    #     apply_factor(size_in_usd, maxPositionImpactFactorForLiquidations)

    price_impact_delta_usd = 0

    # if use_max_price_impact:
    #     price_impact_delta_usd = max_negative_price_impact_usd
    # else:
    #     price_impact_delta_usd = get_price_impact_for_position(
    #         market_info, -size_in_usd, is_long, fallback_to_zero=True)

    #     if price_impact_delta_usd < max_negative_price_impact_usd:
    #         price_impact_delta_usd = max_negative_price_impact_usd

    #     # Ignore positive price impact
    #     if price_impact_delta_usd > 0:
    #         price_impact_delta_usd = Decimal(0)

    minCollateralFactor = datastore_obj.functions.getUint(
        min_collateral_factor_key(market_address)
    ).call()

    liquidation_collateral_usd = apply_factor(
        size_in_usd, minCollateralFactor)

    print(f"Liq Collat: {liquidation_collateral_usd}")

    if liquidation_collateral_usd < min_collateral_usd:
        liquidation_collateral_usd = min_collateral_usd

    liquidation_price = Decimal(0)

    if get_is_equivalent_tokens(collateral_token, index_token):
        if is_long:
            denominator = size_in_tokens + collateral_amount
            print(f"denominator: {denominator}")
            if denominator == 0:
                return None

            liquidation_price = (
                (size_in_usd + liquidation_collateral_usd -
                 price_impact_delta_usd + total_fees_usd) / denominator
            )
            # TODO - add back in ) * 10**22
        else:
            denominator = size_in_tokens - collateral_amount

            if denominator == 0:
                return None

            liquidation_price = (
                (size_in_usd - liquidation_collateral_usd +
                 price_impact_delta_usd - total_fees_usd) / denominator
            )
            # TODO - add back in ) * 10**22
    else:
        if size_in_tokens == 0:
            return None

        print(f"Price Impact delta USD: {price_impact_delta_usd}")
        print(f"Pending Fees: {total_pending_fees_usd}")
        print(f"Closing Fee: {closing_fee_usd}")
        print(f"Collat USD: {collateral_usd}")

        remaining_collateral_usd = (collateral_usd + price_impact_delta_usd -
                                    total_pending_fees_usd - closing_fee_usd)

        print(f"Remaining Colat: {remaining_collateral_usd}")
        if is_long:
            liquidation_price = (
                (liquidation_collateral_usd -
                 remaining_collateral_usd + size_in_usd) / size_in_tokens
            )
            # TODO - add back in ) * 10**22
        else:
            liquidation_price = (
                (liquidation_collateral_usd - remaining_collateral_usd -
                 size_in_usd) / - size_in_tokens
            )
            # TODO - add back in ) * 10**22

    if liquidation_price <= 0:
        return None

    return liquidation_price


def get_position_fee(
    size_delta_usd: Decimal,
    for_positive_impact: bool,
    referral_info: dict = None,
    ui_fee_factor: Decimal = Decimal(0)
) -> dict:

    factor = 0.0005 if for_positive_impact else 0.0007

    position_fee_usd = apply_factor(size_delta_usd,
                                    factor)

    return {
        'positionFeeUsd': position_fee_usd,
    }


def get_position_pending_fees_usd(pending_funding_fees_usd: Decimal, pending_borrowing_fees_usd: Decimal) -> Decimal:
    return pending_borrowing_fees_usd + pending_funding_fees_usd


def apply_factor(value, factor):
    return (value * factor) / 10**30


def get_price_impact_for_position(market_info, size_in_usd, is_long, fallback_to_zero):
    # Placeholder for the actual implementation
    return Decimal('0')


def get_is_equivalent_tokens(token1, token2):
    print(token1, token2)
    if token1 == token2:
        return True
    if token2 == "0x47904963fc8b2340414262125aF798B9655E58Cd":
        if token1 == "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f":
            return True
    return False


def get_position_key(account: str, market_address: str, collateral_address: str, is_long: bool) -> bytes:
    # Create the concatenated string
    concatenated_string = f"{account}:{market_address}:{collateral_address}:{is_long}"

    # Hash the string using SHA-256 to get a fixed-size byte array
    hash_object = hashlib.sha256(concatenated_string.encode())
    # Convert the hash object to a bytes32-like output (32 bytes)
    return hash_object.digest()[:32]


def transform_to_dict(account_positions_list):
    result = []
    for pos in account_positions_list:
        # Unpack the components of each position
        position, referral, fees, base_pnl_usd, uncapped_base_pnl_usd, pnl_after_price_impact_usd = pos

        position_dict = {
            "position": {
                "addresses": {
                    "account": position[0][0],
                    "market": position[0][1],
                    "collateralToken": position[0][2],
                },
                "numbers": {
                    "sizeInUsd": position[1][0],
                    "sizeInTokens": position[1][1],
                    "collateralAmount": position[1][2],
                    "borrowingFactor": position[1][3],
                    "fundingFeeAmountPerSize": position[1][4],
                    "longTokenClaimableFundingAmountPerSize": position[1][5],
                    "shortTokenClaimableFundingAmountPerSize": position[1][6],
                    "increasedAtBlock": position[1][7],
                    "decreasedAtBlock": position[1][8],
                    "increasedAtTime": position[1][9],
                    "decreasedAtTime": position[1][10],
                },
                "flags": {
                    "isLong": position[2][0],
                },
            },
            "referral": {
                "referralCode": referral[0][0],
                "affiliate": referral[0][1],
                "trader": referral[0][2],
                "totalRebateFactor": referral[0][3],
                "traderDiscountFactor": referral[0][4],
                "totalRebateAmount": referral[0][5],
                "traderDiscountAmount": referral[0][6],
                "affiliateRewardAmount": referral[0][7],
            },
            "fees": {
                "fundingFeeAmount": referral[1][0],
                "claimableLongTokenAmount": referral[1][1],
                "claimableShortTokenAmount": referral[1][2],
                "latestFundingFeeAmountPerSize": referral[1][3],
                "latestLongTokenClaimableFundingAmountPerSize": referral[1][4],
                "latestShortTokenClaimableFundingAmountPerSize": referral[1][5],
            },
            "borrowing": {
                "borrowingFeeUsd": referral[2][0],
                "borrowingFeeAmount": referral[2][1],
                "borrowingFeeReceiverFactor": referral[2][2],
                "borrowingFeeAmountForFeeReceiver": referral[2][3],
            },
            "ui": {
                "uiFeeReceiver": referral[3][0],
                "uiFeeReceiverFactor": referral[3][1],
                "uiFeeAmount": referral[3][2],
            },
            "collateralTokenPrice": {
                "min": referral[4][0],
                "max": referral[4][1],
            },
            "positionFeeFactor": referral[5],
            "protocolFeeAmount": referral[6],
            "positionFeeReceiverFactor": referral[7],
            "feeReceiverAmount": referral[8],
            "feeAmountForPool": referral[9],
            "positionFeeAmountForPool": referral[10],
            "positionFeeAmount": referral[11],
            "totalCostAmountExcludingFunding": referral[12],
            "totalCostAmount": referral[13],
            "basePnlUsd": base_pnl_usd,
            "uncappedBasePnlUsd": uncapped_base_pnl_usd,
            "pnlAfterPriceImpactUsd": pnl_after_price_impact_usd,
        }

        result.append(position_dict)
    return result


def find_position(market_address, account_position):
    print(market_address, account_position['position']['addresses']['market'])
    if market_address == account_position['position']['addresses']['market']:
        return True
    else:
        return False


def get_liquidation_price(config, position_dict, wallet_address=None):

    referral_storage = "0xe6fab3F0c7199b0d34d7FbE83394fc0e0D06e99d"
    datastore = "0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8"

    market_address = position_dict["market"]

    data_obj = GetData(config=config, use_local_datastore=False,
                       filter_swap_markets=True)
    data_obj._get_token_addresses(market_address)
    market_info = data_obj.markets.get_available_markets()[market_address]

    index_token_address = market_info["index_token_address"]

    output = [data_obj._get_oracle_prices(market_address,
                                          index_token_address,
                                          return_tuple=True)]

    hex_data = accountPositionListKey(wallet_address)
    reader_obj = get_reader_contract(config)
    datastore_obj = get_datastore_contract(config)
    position_keys = datastore_obj.functions.getBytes32ValuesAt(hex_data, 0, 1000).call()

    account_positions_list_filter = []
    for i in position_keys:
        print(i)
        # get account positions using positions key built with info above
        account_positions_list_raw = reader_obj.functions.getAccountPositionInfoList(
            datastore, referral_storage, [i], output, wallet_address).call()
        account_positions_list = transform_to_dict(account_positions_list_raw)

        account_positions_list_filter += account_positions_list

    for account_position in account_positions_list_filter:
        if find_position(market_address, account_position):
            break

    decimals = tokens = get_tokens_address_dict(config.chain)[
        account_position['position']['addresses']['collateralToken']]['decimals']

    print(f"funding fee amount: {int(account_position['fees']['fundingFeeAmount'])}")

    liquidation_price = calculate_liquidation_price(
        datastore_obj=datastore_obj,
        market_address=market_address,
        index_token_address=index_token_address,
        size_in_usd=account_position['position']['numbers']['sizeInUsd'],
        size_in_tokens=account_position['position']['numbers']['sizeInTokens'],
        collateral_amount=account_position['position']['numbers']['collateralAmount'],
        collateral_usd=position_dict['inital_collateral_amount_usd'][0] * 10**30,
        collateral_token=account_position['position']['addresses']['collateralToken'],
        pending_funding_fees_usd=int(
            (account_position['fees']['fundingFeeAmount'] * 10**-decimals) * 10**30),
        pending_borrowing_fees_usd=account_position['borrowing']['borrowingFeeUsd'],
        min_collateral_usd=datastore_obj.functions.getUint(min_collateral()).call(),
        is_long=position_dict["is_long"],
        use_max_price_impact=True,
        user_referral_info=None)

    decimals = market_info["market_metadata"]['decimals']

    return liquidation_price / 10**(30 - decimals)


if __name__ == "__main__":

    wallet_address = "0xaB4A1001154220e942813763dF8D5ce0d8ea42d9"
    config = ConfigManager(chain='arbitrum')
    config.set_config()
    positions = get_positions(config, address=wallet_address)

    liquidation_price = get_liquidation_price(
        config, positions['GMX_long'], wallet_address)

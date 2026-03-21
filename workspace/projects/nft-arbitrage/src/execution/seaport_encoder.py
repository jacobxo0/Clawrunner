"""
Seaport ABI Encoder — encodes fulfillment data from OpenSea API into transaction calldata.

OpenSea's fulfillment API returns structured parameters (as dicts) plus the function
signature. This module encodes them into the raw bytes needed for on-chain execution.
"""

from web3 import Web3

SEAPORT_ADDRESS = "0x0000000000000068F116a894984e2DB1123eB395"

# Minimal Seaport 1.6 ABI — only the functions used by OpenSea fulfillment
SEAPORT_ABI = [
    {
        "name": "fulfillBasicOrder_efficient_6GL6yc",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "parameters",
                "type": "tuple",
                "components": [
                    {"name": "considerationToken", "type": "address"},
                    {"name": "considerationIdentifier", "type": "uint256"},
                    {"name": "considerationAmount", "type": "uint256"},
                    {"name": "offerer", "type": "address"},
                    {"name": "zone", "type": "address"},
                    {"name": "offerToken", "type": "address"},
                    {"name": "offerIdentifier", "type": "uint256"},
                    {"name": "offerAmount", "type": "uint256"},
                    {"name": "basicOrderType", "type": "uint8"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                    {"name": "zoneHash", "type": "bytes32"},
                    {"name": "salt", "type": "uint256"},
                    {"name": "offererConduitKey", "type": "bytes32"},
                    {"name": "fulfillerConduitKey", "type": "bytes32"},
                    {"name": "totalOriginalAdditionalRecipients", "type": "uint256"},
                    {
                        "name": "additionalRecipients",
                        "type": "tuple[]",
                        "components": [
                            {"name": "amount", "type": "uint256"},
                            {"name": "recipient", "type": "address"},
                        ],
                    },
                    {"name": "signature", "type": "bytes"},
                ],
            }
        ],
        "outputs": [{"name": "fulfilled", "type": "bool"}],
    },
    {
        "name": "fulfillBasicOrder",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "parameters",
                "type": "tuple",
                "components": [
                    {"name": "considerationToken", "type": "address"},
                    {"name": "considerationIdentifier", "type": "uint256"},
                    {"name": "considerationAmount", "type": "uint256"},
                    {"name": "offerer", "type": "address"},
                    {"name": "zone", "type": "address"},
                    {"name": "offerToken", "type": "address"},
                    {"name": "offerIdentifier", "type": "uint256"},
                    {"name": "offerAmount", "type": "uint256"},
                    {"name": "basicOrderType", "type": "uint8"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                    {"name": "zoneHash", "type": "bytes32"},
                    {"name": "salt", "type": "uint256"},
                    {"name": "offererConduitKey", "type": "bytes32"},
                    {"name": "fulfillerConduitKey", "type": "bytes32"},
                    {"name": "totalOriginalAdditionalRecipients", "type": "uint256"},
                    {
                        "name": "additionalRecipients",
                        "type": "tuple[]",
                        "components": [
                            {"name": "amount", "type": "uint256"},
                            {"name": "recipient", "type": "address"},
                        ],
                    },
                    {"name": "signature", "type": "bytes"},
                ],
            }
        ],
        "outputs": [{"name": "fulfilled", "type": "bool"}],
    },
    {
        "name": "matchAdvancedOrders",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "orders",
                "type": "tuple[]",
                "components": [
                    {
                        "name": "parameters",
                        "type": "tuple",
                        "components": [
                            {"name": "offerer", "type": "address"},
                            {"name": "zone", "type": "address"},
                            {
                                "name": "offer",
                                "type": "tuple[]",
                                "components": [
                                    {"name": "itemType", "type": "uint8"},
                                    {"name": "token", "type": "address"},
                                    {"name": "identifierOrCriteria", "type": "uint256"},
                                    {"name": "startAmount", "type": "uint256"},
                                    {"name": "endAmount", "type": "uint256"},
                                ],
                            },
                            {
                                "name": "consideration",
                                "type": "tuple[]",
                                "components": [
                                    {"name": "itemType", "type": "uint8"},
                                    {"name": "token", "type": "address"},
                                    {"name": "identifierOrCriteria", "type": "uint256"},
                                    {"name": "startAmount", "type": "uint256"},
                                    {"name": "endAmount", "type": "uint256"},
                                    {"name": "recipient", "type": "address"},
                                ],
                            },
                            {"name": "orderType", "type": "uint8"},
                            {"name": "startTime", "type": "uint256"},
                            {"name": "endTime", "type": "uint256"},
                            {"name": "zoneHash", "type": "bytes32"},
                            {"name": "salt", "type": "uint256"},
                            {"name": "conduitKey", "type": "bytes32"},
                            {"name": "totalOriginalConsiderationItems", "type": "uint256"},
                        ],
                    },
                    {"name": "numerator", "type": "uint120"},
                    {"name": "denominator", "type": "uint120"},
                    {"name": "signature", "type": "bytes"},
                    {"name": "extraData", "type": "bytes"},
                ],
            },
            {
                "name": "criteriaResolvers",
                "type": "tuple[]",
                "components": [
                    {"name": "orderIndex", "type": "uint256"},
                    {"name": "side", "type": "uint8"},
                    {"name": "index", "type": "uint256"},
                    {"name": "identifier", "type": "uint256"},
                    {"name": "criteriaProof", "type": "bytes32[]"},
                ],
            },
            {
                "name": "fulfillments",
                "type": "tuple[]",
                "components": [
                    {
                        "name": "offerComponents",
                        "type": "tuple[]",
                        "components": [
                            {"name": "orderIndex", "type": "uint256"},
                            {"name": "itemIndex", "type": "uint256"},
                        ],
                    },
                    {
                        "name": "considerationComponents",
                        "type": "tuple[]",
                        "components": [
                            {"name": "orderIndex", "type": "uint256"},
                            {"name": "itemIndex", "type": "uint256"},
                        ],
                    },
                ],
            },
            {"name": "recipient", "type": "address"},
        ],
        "outputs": [
            {"name": "executions", "type": "tuple[]", "components": [
                {"name": "item", "type": "tuple", "components": [
                    {"name": "itemType", "type": "uint8"},
                    {"name": "token", "type": "address"},
                    {"name": "identifier", "type": "uint256"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "recipient", "type": "address"},
                ]},
                {"name": "offerer", "type": "address"},
                {"name": "conduitKey", "type": "bytes32"},
            ]},
        ],
    },
    {
        "name": "fulfillAvailableAdvancedOrders",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "advancedOrders",
                "type": "tuple[]",
                "components": [
                    {
                        "name": "parameters",
                        "type": "tuple",
                        "components": [
                            {"name": "offerer", "type": "address"},
                            {"name": "zone", "type": "address"},
                            {
                                "name": "offer",
                                "type": "tuple[]",
                                "components": [
                                    {"name": "itemType", "type": "uint8"},
                                    {"name": "token", "type": "address"},
                                    {"name": "identifierOrCriteria", "type": "uint256"},
                                    {"name": "startAmount", "type": "uint256"},
                                    {"name": "endAmount", "type": "uint256"},
                                ],
                            },
                            {
                                "name": "consideration",
                                "type": "tuple[]",
                                "components": [
                                    {"name": "itemType", "type": "uint8"},
                                    {"name": "token", "type": "address"},
                                    {"name": "identifierOrCriteria", "type": "uint256"},
                                    {"name": "startAmount", "type": "uint256"},
                                    {"name": "endAmount", "type": "uint256"},
                                    {"name": "recipient", "type": "address"},
                                ],
                            },
                            {"name": "orderType", "type": "uint8"},
                            {"name": "startTime", "type": "uint256"},
                            {"name": "endTime", "type": "uint256"},
                            {"name": "zoneHash", "type": "bytes32"},
                            {"name": "salt", "type": "uint256"},
                            {"name": "conduitKey", "type": "bytes32"},
                            {"name": "totalOriginalConsiderationItems", "type": "uint256"},
                        ],
                    },
                    {"name": "numerator", "type": "uint120"},
                    {"name": "denominator", "type": "uint120"},
                    {"name": "signature", "type": "bytes"},
                    {"name": "extraData", "type": "bytes"},
                ],
            },
            {
                "name": "criteriaResolvers",
                "type": "tuple[]",
                "components": [
                    {"name": "orderIndex", "type": "uint256"},
                    {"name": "side", "type": "uint8"},
                    {"name": "index", "type": "uint256"},
                    {"name": "identifier", "type": "uint256"},
                    {"name": "criteriaProof", "type": "bytes32[]"},
                ],
            },
            {
                "name": "offerFulfillments",
                "type": "tuple[][]",
                "components": [
                    {"name": "orderIndex", "type": "uint256"},
                    {"name": "itemIndex", "type": "uint256"},
                ],
            },
            {
                "name": "considerationFulfillments",
                "type": "tuple[][]",
                "components": [
                    {"name": "orderIndex", "type": "uint256"},
                    {"name": "itemIndex", "type": "uint256"},
                ],
            },
            {"name": "fulfillerConduitKey", "type": "bytes32"},
            {"name": "recipient", "type": "address"},
            {"name": "maximumFulfilled", "type": "uint256"},
        ],
        "outputs": [],
    },
]

_seaport_contract = None


def _get_contract():
    global _seaport_contract
    if _seaport_contract is None:
        w3 = Web3()
        _seaport_contract = w3.eth.contract(
            address=Web3.to_checksum_address(SEAPORT_ADDRESS),
            abi=SEAPORT_ABI,
        )
    return _seaport_contract


def _coerce_bytes32(val) -> bytes:
    """Convert a bytes32 value from various formats."""
    if isinstance(val, bytes):
        return val.ljust(32, b'\x00')[:32]
    if isinstance(val, str):
        if val.startswith("0x"):
            return bytes.fromhex(val[2:].ljust(64, '0'))[:32]
        return bytes.fromhex(val.ljust(64, '0'))[:32]
    if isinstance(val, int):
        return val.to_bytes(32, 'big')
    return b'\x00' * 32


def _coerce_bytes(val) -> bytes:
    """Convert a bytes value from various formats."""
    if isinstance(val, bytes):
        return val
    if isinstance(val, str):
        if val.startswith("0x"):
            return bytes.fromhex(val[2:])
        return val.encode()
    return b''


def _coerce_int(val) -> int:
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        return int(val)
    return 0


def _coerce_address(val) -> str:
    if not val or val == "0x0000000000000000000000000000000000000000":
        return "0x0000000000000000000000000000000000000000"
    return Web3.to_checksum_address(val)


def encode_basic_order(params: dict) -> bytes:
    """Encode fulfillBasicOrder_efficient_6GL6yc call from OpenSea parameters."""
    contract = _get_contract()

    additional_recipients = []
    for r in params.get("additionalRecipients", []):
        additional_recipients.append((
            _coerce_int(r.get("amount", 0)),
            _coerce_address(r.get("recipient")),
        ))

    order_params = (
        _coerce_address(params.get("considerationToken")),
        _coerce_int(params.get("considerationIdentifier", 0)),
        _coerce_int(params.get("considerationAmount", 0)),
        _coerce_address(params.get("offerer")),
        _coerce_address(params.get("zone")),
        _coerce_address(params.get("offerToken")),
        _coerce_int(params.get("offerIdentifier", 0)),
        _coerce_int(params.get("offerAmount", 0)),
        _coerce_int(params.get("basicOrderType", 0)),
        _coerce_int(params.get("startTime", 0)),
        _coerce_int(params.get("endTime", 0)),
        _coerce_bytes32(params.get("zoneHash", b'\x00' * 32)),
        _coerce_int(params.get("salt", 0)),
        _coerce_bytes32(params.get("offererConduitKey", b'\x00' * 32)),
        _coerce_bytes32(params.get("fulfillerConduitKey", b'\x00' * 32)),
        _coerce_int(params.get("totalOriginalAdditionalRecipients", 0)),
        additional_recipients,
        _coerce_bytes(params.get("signature", b'')),
    )

    return contract.encode_abi("fulfillBasicOrder_efficient_6GL6yc", [order_params])


def _build_offer_item(item: dict) -> tuple:
    return (
        _coerce_int(item.get("itemType", 0)),
        _coerce_address(item.get("token")),
        _coerce_int(item.get("identifierOrCriteria", 0)),
        _coerce_int(item.get("startAmount", 0)),
        _coerce_int(item.get("endAmount", 0)),
    )


def _build_consideration_item(item: dict) -> tuple:
    return (
        _coerce_int(item.get("itemType", 0)),
        _coerce_address(item.get("token")),
        _coerce_int(item.get("identifierOrCriteria", 0)),
        _coerce_int(item.get("startAmount", 0)),
        _coerce_int(item.get("endAmount", 0)),
        _coerce_address(item.get("recipient")),
    )


def _build_advanced_order(order: dict) -> tuple:
    params = order.get("parameters", {})
    return (
        (
            _coerce_address(params.get("offerer")),
            _coerce_address(params.get("zone")),
            [_build_offer_item(i) for i in params.get("offer", [])],
            [_build_consideration_item(i) for i in params.get("consideration", [])],
            _coerce_int(params.get("orderType", 0)),
            _coerce_int(params.get("startTime", 0)),
            _coerce_int(params.get("endTime", 0)),
            _coerce_bytes32(params.get("zoneHash", b'\x00' * 32)),
            _coerce_int(params.get("salt", 0)),
            _coerce_bytes32(params.get("conduitKey", b'\x00' * 32)),
            _coerce_int(params.get("totalOriginalConsiderationItems", 0)),
        ),
        _coerce_int(order.get("numerator", 1)),
        _coerce_int(order.get("denominator", 1)),
        _coerce_bytes(order.get("signature", b'')),
        _coerce_bytes(order.get("extraData", b'')),
    )


def encode_match_advanced_orders(input_data: dict) -> bytes:
    """Encode matchAdvancedOrders call from OpenSea parameters."""
    contract = _get_contract()

    orders = [_build_advanced_order(o) for o in input_data.get("orders", [])]

    criteria_resolvers = []
    for cr in input_data.get("criteriaResolvers", []):
        criteria_resolvers.append((
            _coerce_int(cr.get("orderIndex", 0)),
            _coerce_int(cr.get("side", 0)),
            _coerce_int(cr.get("index", 0)),
            _coerce_int(cr.get("identifier", 0)),
            [_coerce_bytes32(p) for p in cr.get("criteriaProof", [])],
        ))

    fulfillments = []
    for f in input_data.get("fulfillments", []):
        offer_components = [
            (_coerce_int(c.get("orderIndex", 0)), _coerce_int(c.get("itemIndex", 0)))
            for c in f.get("offerComponents", [])
        ]
        consideration_components = [
            (_coerce_int(c.get("orderIndex", 0)), _coerce_int(c.get("itemIndex", 0)))
            for c in f.get("considerationComponents", [])
        ]
        fulfillments.append((offer_components, consideration_components))

    recipient = _coerce_address(input_data.get("recipient", "0x0000000000000000000000000000000000000000"))

    return contract.encode_abi("matchAdvancedOrders", [
        orders, criteria_resolvers, fulfillments, recipient,
    ])


def encode_fulfill_available_advanced_orders(input_data: dict) -> bytes:
    """Encode fulfillAvailableAdvancedOrders call from OpenSea parameters."""
    contract = _get_contract()

    orders = [_build_advanced_order(o) for o in input_data.get("advancedOrders", [])]

    criteria_resolvers = []
    for cr in input_data.get("criteriaResolvers", []):
        criteria_resolvers.append((
            _coerce_int(cr.get("orderIndex", 0)),
            _coerce_int(cr.get("side", 0)),
            _coerce_int(cr.get("index", 0)),
            _coerce_int(cr.get("identifier", 0)),
            [_coerce_bytes32(p) for p in cr.get("criteriaProof", [])],
        ))

    offer_fulfillments = []
    for group in input_data.get("offerFulfillments", []):
        components = [
            (_coerce_int(c.get("orderIndex", 0)), _coerce_int(c.get("itemIndex", 0)))
            for c in (group if isinstance(group, list) else [group])
        ]
        offer_fulfillments.append(components)

    consideration_fulfillments = []
    for group in input_data.get("considerationFulfillments", []):
        components = [
            (_coerce_int(c.get("orderIndex", 0)), _coerce_int(c.get("itemIndex", 0)))
            for c in (group if isinstance(group, list) else [group])
        ]
        consideration_fulfillments.append(components)

    fulfiller_conduit_key = _coerce_bytes32(
        input_data.get("fulfillerConduitKey", b'\x00' * 32)
    )
    recipient = _coerce_address(
        input_data.get("recipient", "0x0000000000000000000000000000000000000000")
    )
    maximum_fulfilled = _coerce_int(input_data.get("maximumFulfilled", len(orders)))

    return contract.encode_abi("fulfillAvailableAdvancedOrders", [
        orders,
        criteria_resolvers,
        offer_fulfillments,
        consideration_fulfillments,
        fulfiller_conduit_key,
        recipient,
        maximum_fulfilled,
    ])


def encode_fulfillment_tx(tx_data: dict) -> bytes:
    """
    Encode a fulfillment transaction from OpenSea's API response.

    Detects the function type and dispatches to the correct encoder.
    Returns raw calldata bytes ready for transaction submission.
    """
    function_name = tx_data.get("function", "")
    input_data = tx_data.get("input_data", {})

    if isinstance(input_data, str) and input_data.startswith("0x"):
        return bytes.fromhex(input_data[2:])

    if not isinstance(input_data, dict):
        return b""

    if "fulfillBasicOrder" in function_name:
        params = input_data.get("parameters", {})
        calldata = encode_basic_order(params)
        if isinstance(calldata, str) and calldata.startswith("0x"):
            return bytes.fromhex(calldata[2:])
        return calldata if isinstance(calldata, bytes) else bytes.fromhex(calldata)

    if "matchAdvancedOrders" in function_name:
        calldata = encode_match_advanced_orders(input_data)
        if isinstance(calldata, str) and calldata.startswith("0x"):
            return bytes.fromhex(calldata[2:])
        return calldata if isinstance(calldata, bytes) else bytes.fromhex(calldata)

    if "fulfillAvailableAdvancedOrders" in function_name:
        calldata = encode_fulfill_available_advanced_orders(input_data)
        if isinstance(calldata, str) and calldata.startswith("0x"):
            return bytes.fromhex(calldata[2:])
        return calldata if isinstance(calldata, bytes) else bytes.fromhex(calldata)

    return b""

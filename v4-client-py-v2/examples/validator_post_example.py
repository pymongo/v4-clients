import asyncio
import json
import random
import time
from pathlib import Path

from dydx_v4_client import MAX_CLIENT_ID, NodeClient, Order, OrderFlags, Wallet
from dydx_v4_client.network import TESTNET,mainnet_node,make_mainnet
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.node.market import Market
from dydx_v4_client.node.message import order, order_id
from tests.conftest import DYDX_TEST_MNEMONIC, TEST_ADDRESS
from dydx_v4_client import FaucetClient

PERPETUAL_PAIR_BTC_USD = 0

with open(Path(__file__).parent / "raw_orders.json", "r") as file:
    orders = json.load(file)

'''
fullnode rest/json-rpc/grpc
Available endpoints:

Endpoints that require arguments:
//test-dydx-rpc.kingnodes.com/abci_info?
//test-dydx-rpc.kingnodes.com/abci_query?path=_&data=_&height=_&prove=_
//test-dydx-rpc.kingnodes.com/block?height=_
//test-dydx-rpc.kingnodes.com/block_by_hash?hash=_
//test-dydx-rpc.kingnodes.com/block_results?height=_
//test-dydx-rpc.kingnodes.com/block_search?query=_&page=_&per_page=_&order_by=_
//test-dydx-rpc.kingnodes.com/blockchain?minHeight=_&maxHeight=_
//test-dydx-rpc.kingnodes.com/broadcast_evidence?evidence=_
//test-dydx-rpc.kingnodes.com/broadcast_tx_async?tx=_
//test-dydx-rpc.kingnodes.com/broadcast_tx_commit?tx=_
//test-dydx-rpc.kingnodes.com/broadcast_tx_sync?tx=_
//test-dydx-rpc.kingnodes.com/check_tx?tx=_
//test-dydx-rpc.kingnodes.com/commit?height=_
//test-dydx-rpc.kingnodes.com/consensus_params?height=_
//test-dydx-rpc.kingnodes.com/consensus_state?
//test-dydx-rpc.kingnodes.com/dump_consensus_state?
//test-dydx-rpc.kingnodes.com/genesis?
//test-dydx-rpc.kingnodes.com/genesis_chunked?chunk=_
//test-dydx-rpc.kingnodes.com/header?height=_
//test-dydx-rpc.kingnodes.com/header_by_hash?hash=_
//test-dydx-rpc.kingnodes.com/health?
//test-dydx-rpc.kingnodes.com/net_info?
//test-dydx-rpc.kingnodes.com/num_unconfirmed_txs?
//test-dydx-rpc.kingnodes.com/status?
//test-dydx-rpc.kingnodes.com/subscribe?query=_
//test-dydx-rpc.kingnodes.com/tx?hash=_&prove=_
//test-dydx-rpc.kingnodes.com/tx_search?query=_&prove=_&page=_&per_page=_&order_by=_
//test-dydx-rpc.kingnodes.com/unconfirmed_txs?limit=_
//test-dydx-rpc.kingnodes.com/unsubscribe?query=_
//test-dydx-rpc.kingnodes.com/unsubscribe_all?
//test-dydx-rpc.kingnodes.com/validators?height=_&page=_&per_page=_

**Order Tx**
tx_response {
  txhash: "9B199EC142E39E6F4E1412B5DC692D4FE3E6A9EB29AFC6E5820C3356D4FF3785"
  raw_log: "[]"
}

测试 chain_id='dydx-testnet-4', denomination='ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5', memo='Client Example')) 72
主网 chain_id='dydx-mainnet-1', denomination='ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5', memo='Client Example')) 100
'''
USDC_DENOM="ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5"
async def test():
    node: NodeClient = await NodeClient.connect(TESTNET.node)
    if False:
        testnet_wallet='dydx1x4t6xspyf6g3nvx28nhx69m3h65rd3xrq088ea'
        faucet=FaucetClient(faucet_url="https://faucet.v4testnet.dydx.exchange")
        faucet_response = await faucet.fill(testnet_wallet, 0, 2000)
        print(faucet_response)
        return

    mainnet_node: NodeClient = await NodeClient.connect(make_mainnet(
        rest_indexer="https://indexer.dydx.trade/v4",
        websocket_indexer="wss://indexer.dydx.trade/v4/ws",
        # https://docs.dydx.exchange/infrastructure_providers-network/resources#full-node-endpoints
        # https://test-dydx-rpc.kingnodes.com/validators
        #node_url="test-dydx-grpc.kingnodes.com",
        node_url="dydx-mainnet-full-grpc.public.blastapi.io:443"
    ).node)
    wallet = await Wallet.from_mnemonic(node, DYDX_TEST_MNEMONIC, TEST_ADDRESS)
    validators = await node.get_all_validators()
    print(await node.get_account_balance(TEST_ADDRESS, USDC_DENOM))
    from v4_proto.dydxprotocol.clob.order_pb2 import Order
    print(node, len(validators.validators))
    
    orders = [{
        "timeInForce": 0,
        "reduceOnly": False,
        "orderFlags": 64,
        "side": 1,
        "quantums": 10000000,
        "subticks": 40000000000
    }]
    for order_dict in orders:
        id = order_id(
            TEST_ADDRESS,
            0,
            random.randint(0, MAX_CLIENT_ID),
            PERPETUAL_PAIR_BTC_USD,
            order_dict["orderFlags"],
        )

        good_til_block = None
        good_til_block_time = round(time.time() + 60)
        if order_dict["orderFlags"] == 0:
            good_til_block_time = None
            current_block = await node.latest_block_height()
            good_til_block = current_block + 3

        place = await node.place_order(
            wallet,
            order(
                id,
                order_dict["side"],
                quantums=order_dict["quantums"],
                subticks=40000000000,
                time_in_force=order_dict["timeInForce"],
                reduce_only=False,
                good_til_block=good_til_block,
                good_til_block_time=good_til_block_time,
            ),
        )
        print("**Order Tx**")
        print(place)
        # FIXME: Remove
        wallet.sequence += 1
        time.sleep(5)


asyncio.run(test())

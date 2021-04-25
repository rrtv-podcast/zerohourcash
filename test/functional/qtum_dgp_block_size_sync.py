#!/usr/bin/env python3

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.script import *
from test_framework.mininode import *
from test_framework.zerohour import *
from test_framework.address import *
from test_framework.blocktools import *
import io

"""
Note, these tests do not test the functionality of the DGP template contract itself, for tests for the DGP template, see zerohour-dgp.py
"""
class ZHCASHDGPBlockSizeSyncTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 8

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def create_block_of_approx_max_size(self, size_in_bytes):
        tip = self.node.getblock(self.node.getbestblockhash())
        block = create_block(int(self.node.getbestblockhash(), 16), create_coinbase(self.node.getblockcount()+1), tip['time'])
        block.hashUTXORoot = int(tip['hashUTXORoot'], 16)
        block.hashStateRoot = int(tip['hashStateRoot'], 16)

        unspents = self.node.listunspent()
        while len(block.serialize()) < size_in_bytes:
            unspent = unspents.pop(0)
            tx = CTransaction()
            tx.vin = [CTxIn(COutPoint(int(unspent['txid'], 16), unspent['vout']), nSequence=0)]
            for i in range(50):
                tx.vout.append(CTxOut(int(unspent['amount']*COIN/100 - 11000), scriptPubKey=CScript([OP_TRUE]*10000)))
            tx_hex = self.node.signrawtransactionwithwallet(bytes_to_hex_str(tx.serialize()))['hex']
            f = io.BytesIO(hex_str_to_bytes(tx_hex))
            block.vtx.append(CTransaction())
            block.vtx[-1].deserialize(f)

        while len(block.serialize()) > size_in_bytes:
            block.vtx[-1].vout.pop(-1)
            if not block.vtx[-1].vout:
                block.vtx.pop(-1)
        tx_hex = self.node.signrawtransactionwithwallet(bytes_to_hex_str(block.vtx[-1].serialize()))['hex']
        f = io.BytesIO(hex_str_to_bytes(tx_hex))
        block.vtx[-1] = CTransaction()
        block.vtx[-1].deserialize(f)

        block.hashMerkleRoot = block.calc_merkle_root()
        block.rehash()
        block.solve()
        print("block size", len(block.serialize()))
        return block

    def create_proposal_contract(self, block_size=2000000):
        """
        pragma solidity ^0.4.11;

        contract blockSize {

            uint32[1] _blockSize=[
                8000000 //block size in bytes
            ];

            function getBlockSize() constant returns(uint32[1] _size){
                return _blockSize;
            }
        }
        """
        # The contracts below only differ in the _blockSize variable
        if block_size == 32000000:
            contract_data = self.node.createcontract("60606040526020604051908101604052806301e8480063ffffffff16815250600090600161002e92919061003f565b50341561003a57600080fd5b610115565b8260016007016008900481019282156100d15791602002820160005b8382111561009f57835183826101000a81548163ffffffff021916908363ffffffff160217905550926020019260040160208160030104928301926001030261005b565b80156100cf5782816101000a81549063ffffffff021916905560040160208160030104928301926001030261009f565b505b5090506100de91906100e2565b5090565b61011291905b8082111561010e57600081816101000a81549063ffffffff0219169055506001016100e8565b5090565b90565b610162806101246000396000f30060606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806392ac3c621461003e575b600080fd5b341561004957600080fd5b610051610090565b6040518082600160200280838360005b8381101561007d5780820151818401525b602081019050610061565b5050505090500191505060405180910390f35b610098610108565b60006001806020026040519081016040528092919082600180156100fd576020028201916000905b82829054906101000a900463ffffffff1663ffffffff16815260200190600401906020826003010492830192600103820291508084116100c05790505b505050505090505b90565b6020604051908101604052806001905b600063ffffffff1681526020019060019003908161011857905050905600a165627a7a72305820322c4456cb00ecc4c7f2878fe22cc7ff6addbf199842e68a4b23e98d51446b080029", 10000000)
        elif block_size == 8000000:
            contract_data = self.node.createcontract("6060604052602060405190810160405280627a120062ffffff16815250600090600161002c92919061003d565b50341561003857600080fd5b610112565b8260016007016008900481019282156100ce5791602002820160005b8382111561009c57835183826101000a81548163ffffffff021916908362ffffff1602179055509260200192600401602081600301049283019260010302610059565b80156100cc5782816101000a81549063ffffffff021916905560040160208160030104928301926001030261009c565b505b5090506100db91906100df565b5090565b61010f91905b8082111561010b57600081816101000a81549063ffffffff0219169055506001016100e5565b5090565b90565b610162806101216000396000f30060606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806392ac3c621461003e575b600080fd5b341561004957600080fd5b610051610090565b6040518082600160200280838360005b8381101561007d5780820151818401525b602081019050610061565b5050505090500191505060405180910390f35b610098610108565b60006001806020026040519081016040528092919082600180156100fd576020028201916000905b82829054906101000a900463ffffffff1663ffffffff16815260200190600401906020826003010492830192600103820291508084116100c05790505b505050505090505b90565b6020604051908101604052806001905b600063ffffffff1681526020019060019003908161011857905050905600a165627a7a723058209bab110523b5fdedfb12512d3aedc1ba1add53dff85edb77aeec48ebdc01c35c0029", 10000000)
        elif block_size == 4000000:
            contract_data = self.node.createcontract("6060604052602060405190810160405280623d090062ffffff16815250600090600161002c92919061003d565b50341561003857600080fd5b610112565b8260016007016008900481019282156100ce5791602002820160005b8382111561009c57835183826101000a81548163ffffffff021916908362ffffff1602179055509260200192600401602081600301049283019260010302610059565b80156100cc5782816101000a81549063ffffffff021916905560040160208160030104928301926001030261009c565b505b5090506100db91906100df565b5090565b61010f91905b8082111561010b57600081816101000a81549063ffffffff0219169055506001016100e5565b5090565b90565b610162806101216000396000f30060606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806392ac3c621461003e575b600080fd5b341561004957600080fd5b610051610090565b6040518082600160200280838360005b8381101561007d5780820151818401525b602081019050610061565b5050505090500191505060405180910390f35b610098610108565b60006001806020026040519081016040528092919082600180156100fd576020028201916000905b82829054906101000a900463ffffffff1663ffffffff16815260200190600401906020826003010492830192600103820291508084116100c05790505b505050505090505b90565b6020604051908101604052806001905b600063ffffffff1681526020019060019003908161011857905050905600a165627a7a72305820c5f02b85c3d9d7b93140775449355f53a7cb98dcafc56f07cdb09e9f2dc240550029", 10000000)
        elif block_size == 2000000:
            contract_data = self.node.createcontract("6060604052602060405190810160405280621e848062ffffff16815250600090600161002c92919061003d565b50341561003857600080fd5b610112565b8260016007016008900481019282156100ce5791602002820160005b8382111561009c57835183826101000a81548163ffffffff021916908362ffffff1602179055509260200192600401602081600301049283019260010302610059565b80156100cc5782816101000a81549063ffffffff021916905560040160208160030104928301926001030261009c565b505b5090506100db91906100df565b5090565b61010f91905b8082111561010b57600081816101000a81549063ffffffff0219169055506001016100e5565b5090565b90565b610162806101216000396000f30060606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806392ac3c621461003e575b600080fd5b341561004957600080fd5b610051610090565b6040518082600160200280838360005b8381101561007d5780820151818401525b602081019050610061565b5050505090500191505060405180910390f35b610098610108565b60006001806020026040519081016040528092919082600180156100fd576020028201916000905b82829054906101000a900463ffffffff1663ffffffff16815260200190600401906020826003010492830192600103820291508084116100c05790505b505050505090505b90565b6020604051908101604052806001905b600063ffffffff1681526020019060019003908161011857905050905600a165627a7a723058201f747ceade404003185ab16248ecd30e8c1a63a811e55d7961ce3a47ddd01b160029", 10000000)
        elif block_size == 1000000:
            contract_data = self.node.createcontract("6060604052602060405190810160405280620f424062ffffff16815250600090600161002c92919061003d565b50341561003857600080fd5b610112565b8260016007016008900481019282156100ce5791602002820160005b8382111561009c57835183826101000a81548163ffffffff021916908362ffffff1602179055509260200192600401602081600301049283019260010302610059565b80156100cc5782816101000a81549063ffffffff021916905560040160208160030104928301926001030261009c565b505b5090506100db91906100df565b5090565b61010f91905b8082111561010b57600081816101000a81549063ffffffff0219169055506001016100e5565b5090565b90565b610162806101216000396000f30060606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806392ac3c621461003e575b600080fd5b341561004957600080fd5b610051610090565b6040518082600160200280838360005b8381101561007d5780820151818401525b602081019050610061565b5050505090500191505060405180910390f35b610098610108565b60006001806020026040519081016040528092919082600180156100fd576020028201916000905b82829054906101000a900463ffffffff1663ffffffff16815260200190600401906020826003010492830192600103820291508084116100c05790505b505050505090505b90565b6020604051908101604052806001905b600063ffffffff1681526020019060019003908161011857905050905600a165627a7a7230582034c00d84f338629f594676d9bc32d5b9d7b92f3b438e9cc82a3efd92805f14730029", 10000000)

        self.proposal_address = contract_data['address']

    def assert_block_accepted(self, block, with_witness=True):
        current_block_count = self.node.getblockcount()
        assert_equal(self.node.submitblock(bytes_to_hex_str(block.serialize(with_witness))), None)
        assert_equal(self.node.getblockcount(), current_block_count+1)
        t = time.time()
        while time.time() < t+5:
            if self.nodes[0].getbestblockhash() == self.nodes[1].getbestblockhash():
                break
        else:
            assert(False)
        assert_equal(self.nodes[0].getbestblockhash(), self.nodes[1].getbestblockhash())

    def assert_block_limits(self, max_accepted_block_size, possible_block_sizes):
        accepted_block_sizes = possible_block_sizes[0:possible_block_sizes.index(max_accepted_block_size)+1]

        for block_size in accepted_block_sizes:
            block = self.create_block_of_approx_max_size(block_size)
            self.assert_block_accepted(block)

        t = time.time()
        while time.time() < t+5:
            if self.nodes[0].getbestblockhash() == self.nodes[1].getbestblockhash():
                break
        else:
            assert(False)

        # Make sure that both nodes now have the same tip
        assert_equal(self.nodes[0].getbestblockhash(), self.nodes[1].getbestblockhash())

    def run_test(self):
        # stop 6 nodes that will be used later for IBD
        for i in range(2, 8):
            self.stop_node(i)
        # Generate some blocks to make sure we have enough spendable outputs
        self.node = self.nodes[0]
        self.node.generate(1000 + COINBASE_MATURITY)
        self.BLOCK_SIZE_DGP = DGPState(self.node, "0000000000000000000000000000000000000081")
        self.is_network_split = False
        connect_nodes_bi(self.nodes, 0, 1)
        
        # Start off by setting ourself as admin
        admin_address = self.node.getnewaddress()

        # Set ourself up as admin
        self.BLOCK_SIZE_DGP.send_set_initial_admin(admin_address)
        self.node.generate(1)

        possible_block_sizes = [1000000, 2000000, 4000000, 8000000]
        ascending_block_sizes = sorted(possible_block_sizes)

        for max_block_size in possible_block_sizes:
            self.create_proposal_contract(max_block_size)
            self.BLOCK_SIZE_DGP.send_add_address_proposal(self.proposal_address, 2, admin_address)
            self.node.generate(2) # We need to generate 2 blocks now for it to activate
            self.assert_block_limits(max_block_size, ascending_block_sizes)

        # Bring the last nodes online and make sure that they sync with node 0 and 1 (A and B)
        for i in range(2, 8):
            self.start_node(i)
            connect_nodes_bi(self.nodes, 0, i)
            connect_nodes_bi(self.nodes, 1, i)
        self.sync_all()

if __name__ == '__main__':
    ZHCASHDGPBlockSizeSyncTest().main()

# blockchain/land_registry.py
from web3 import Web3
import json

class LandRegistry:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://rinkeby.infura.io/v3/YOUR_PROJECT_ID'))
        with open('contracts/LandRegistry.json') as f:
            contract_abi = json.load(f)['abi']
        self.contract = self.w3.eth.contract(
            address='0xCONTRACT_ADDRESS',
            abi=contract_abi
        )
    
    def register_land(self, owner_address, parcel_id, location):
        tx_hash = self.contract.functions.registerLand(
            parcel_id,
            location
        ).transact({'from': owner_address})
        return tx_hash
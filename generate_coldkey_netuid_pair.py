import bittensor
from dotenv import load_dotenv
import os

load_dotenv()
WS_URL = os.getenv("WS_URL")
subnet_count = 128


subtensor = bittensor.subtensor(network=WS_URL)

subnet_coldkeys = {}

for netuid in range(1,subnet_count+1):
    subnet_coldkeys[netuid] = subtensor.subnet(netuid).owner_coldkey
    
print(subnet_coldkeys)
from substrateinterface import SubstrateInterface, Keypair
import bittensor
from config import *

keypair   = Keypair.create_from_mnemonic(MNEMONIC)
substrate = SubstrateInterface(url=WS_URL)
metadata  = substrate.get_metadata()
subtensor = bittensor.subtensor(network=WS_URL)

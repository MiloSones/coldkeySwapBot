from substrateinterface import SubstrateInterface, Keypair
import bittensor
import config

keypair = Keypair.create_from_mnemonic(config.MNEMONIC)
substrate = SubstrateInterface(url=config.WS_URL)
metadata = substrate.get_metadata()
subtensor = bittensor.subtensor(network=config.WS_URL)


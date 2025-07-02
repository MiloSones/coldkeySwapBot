from scalecodec.types import Extrinsic
from scalecodec.base import ScaleBytes
from subtensor import metadata
from subtensor import substrate

def decode_extrinsic(hex_string):
    xt = Extrinsic(data=ScaleBytes(hex_string), metadata=metadata)
    xt.decode()
    return xt

def get_pool_reserves(netuid):
    alpha_reserve = substrate.query(
        module='SubtensorModule',
        storage_function='SubnetAlphaIn',
        params=[netuid]
    ).value
    tao_reserve = substrate.query(
        module='SubtensorModule',
        storage_function='SubnetTAO',
        params=[netuid]
    ).value
    return alpha_reserve, tao_reserve
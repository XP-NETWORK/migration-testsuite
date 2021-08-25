from config import Config
from consts.common import CACHE_ELROND, CACHE_POLKADOT_ELRD
from setup import load_or_setup, setup_elrd, setup_polkadot
from chains.elrond import ElrondHelper


config = Config()
#polka = setup_polkadot(config.polkadot, "./workaround.json", CACHE_POLKADOT_ELRD)
elrd = ElrondHelper.setup(config.elrond)

#elrd.send_tokens(elrd.sender, "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY", 100000000000000)

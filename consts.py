CONFIG_FILE: str = "config.ini"

# Validator stuff
VALIDATOR_CONFIG = "{project}/src/config.json"

# Polkadot Stuff
ALICE_URI = "//Alice"
POLKADOT_OUT_DIR = "{project}/target/ink/"
POLKADOT_FREEZER_ENDOW = 10**16
POLKADOT_DEPLOY_GASL = 1000000000000
FREEZER_SEND_CALL = "send"
FREEZER_UNFREEZE_CALL = "withdraw_wrapper"
INK_EGLD_NEW_OWNER_CALL = "new_owner"
WORKAROUND_METADATA = "workaround.json"

# Elrond stuff
ELROND_ESDT_VALUE = 50000000000000000
ELROND_ESDT_SC_ADDR = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u"  # noqa: E501
ELROND_GAS_PRICE = 1000000000
ELROND_ESDT_GASL = 800000000
ELROND_ESDT_IDENT_HEX = b"XPNET".hex()
ELROND_ESDT_ISSUE_DATA = f"issue@{ELROND_ESDT_IDENT_HEX}@{ELROND_ESDT_IDENT_HEX}@03E8@06@63616E4D696E74@74727565@63616E4275726E@74727565@63616E4368616E67654F776E6572@74727565"  # noqa: E501
ELROND_TX_URI = "{proxy}/transaction/{tx}?withResults=true"
ELROND_ESDT_BAL_URI = "{proxy}/address/{addr}/esdt/{token}"
ELROND_CONTRACT_ARGS = "0x{esdt} 1 0x{sender}"
ELROND_SETROLE_DATA = "setSpecialRole@{esdt}@{sc_addr}@45534454526F6C654C6F63616C4D696E74@45534454526F6C654C6F63616C4275726E"  # noqa: E501

# Web3 stuff
WEB3_MINTER_JSON = "{project}/artifacts/contracts/Minter.sol/Minter.json"
WEB3_XPNET_JSON = "{project}/artifacts/contracts/XPNet.sol/XPNet.json"

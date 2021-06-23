ESDT_SC_ADDR = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u"  # noqa: E501
GAS_PRICE = 1000000000
ESDT_GASL = 800000000
ESDT_IDENT_HEX = b"XPNET".hex()
ESDT_ISSUE_DATA = f"issue@{ESDT_IDENT_HEX}@{ESDT_IDENT_HEX}@03E8@06@63616E4D696E74@74727565@63616E4275726E@74727565@63616E4368616E67654F776E6572@74727565"  # noqa: E501
TX_URI = "{proxy}/transaction/{tx}?withResults=true"
ESDT_BAL_URI = "{proxy}/address/{addr}/esdt/{token}"
CONTRACT_ARGS = "0x{esdt} 1 0x{sender}"
SETROLE_DATA = "setSpecialRole@{esdt}@{sc_addr}@45534454526F6C654C6F63616C4D696E74@45534454526F6C654C6F63616C4275726E"  # noqa: E501
OUT_FILE = "{project}/output/elrond-mint-contract.wasm"

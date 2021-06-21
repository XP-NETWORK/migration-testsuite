import consts

from dataclasses import dataclass, field
from os.path import abspath
from configparser import ConfigParser, SectionProxy
from typing import Final


class Config:
    def __init__(self) -> None:
        parser = ConfigParser()
        parser.read(consts.CONFIG_FILE)
        self.validator: Final = ValidatorConfig(parser["VALIDATOR"])
        self.polkadot: Final = PolkadotConfig(parser["POLKADOT"])
        self.elrond: Final = ElrondConfig(parser["ELROND"])


class ValidatorConfig:
    def __init__(self, parser: SectionProxy):
        self.project: Final = abspath(str(parser["DIR"]))


class PolkadotConfig:
    def __init__(self, parser: SectionProxy):
        self.uri: Final = str(parser["NODE_URI"])
        self.freezer_project: Final = abspath(str(parser["FREEZER_PROJECT"]))
        self.erc20_project: Final = abspath(str(parser["ERC20_PROJECT"]))
        self.validator: Final = str(parser["VALIDATOR_WORKAROUND"])


class ElrondConfig:
    def __init__(self, parser: SectionProxy):
        self.uri: Final = str(parser["NODE_URI"])
        self.event_socket: Final = str(parser["EVENT_SOCK"])
        self.event_rest: Final = str(parser["EVENT_REST"])
        self.sender: Final = abspath(str(parser["SENDER_PEM"]))
        self.project: Final = abspath(str(parser["MINT_PROJECT"]))


@dataclass
class ValidatorRuntimeConfig:
    xnode: Final[str] = field(metadata={"required": True})
    elrond_node: Final[str] = field(metadata={"required": True})
    private_key: Final[str] = field(metadata={"required": True})
    elrond_sender: Final[str] = field(metadata={"required": True})
    elrond_minter: Final[str] = field(metadata={"required": True})
    xp_freezer: Final[str] = field(metadata={"required": True})
    elrond_ev_socket: Final[str] = field(metadata={"required": True})

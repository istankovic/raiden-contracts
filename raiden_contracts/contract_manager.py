import os
import json
import logging
from functools import wraps

log = logging.getLogger(__name__)
CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), 'data/contracts.json')
CONTRACTS_SOURCE_DIRS = [
    os.path.join(os.path.dirname(__file__), '../contracts'),
    os.path.join(os.path.dirname(__file__), '../contracts/test'),

]
HAS_SOLIDITY = False

#
# set HAS_SOLIDITY to True if ethereum library is installed AND solidity binary exists
#
try:
    from ethereum.tools import _solidity
    if _solidity.get_compiler_path() is None:
        log.warn('solc not found in $PATH. Check your path or set $SOLC_BINARY.')
    else:
        HAS_SOLIDITY = True
except ImportError:
    log.info('ethereum._solidity not found. Contract compilation will be unavailable')


def assert_has_solidity(func):
    """decorator - Raise CompileError if HAS_SOLIDITY is set to False"""
    @wraps(func)
    def func_wrap(*args, **kwargs):
        if HAS_SOLIDITY is False:
            raise _solidity.CompileError(
                'solc not found in $PATH. Check your path or set $SOLC_BINARY.'
            )
        return func(*args, **kwargs)
    return func_wrap


class ContractManager:
    def __init__(self, path: str) -> None:
        """Params:
            path (str, list): either path to a precompiled contract JSON file, or a list of
                directories which contain solidity files to compile
        """
        self.contracts_source_dirs = None
        self.abi = dict()
        if isinstance(path, list):
            for dir_path in path:
                self.abi.update(ContractManager.precompile_contracts(dir_path))
            self.contracts_source_dirs = path
        elif os.path.isdir(path) is True:
            ContractManager.__init__(self, [path])
        else:
            self.abi = json.load(open(path, 'r'))

    @assert_has_solidity
    def compile_contract(self, contract_name, libs=None, *args):
        """Compile contract and return JSON containing abi and bytecode"""
        return _solidity.compile_contract(
            self.get_contract_path(contract_name)[0],
            contract_name,
            combined='abi,bin',
            libraries=libs
        )

    def get_contract_path(self, contract_name: str):
        return sum(
            (self.list_contract_path(contract_name, x)
             for x in self.contracts_source_dirs),
            []
        )

    @staticmethod
    def list_contract_path(contract_name: str, directory: str):
        """Get contract source file for a specified contract"""
        return [
            os.path.join(directory, x)
            for x in os.listdir(directory)
            if os.path.basename(x).split('.', 1)[0] == contract_name
        ]

    @staticmethod
    @assert_has_solidity
    def precompile_contracts(contracts_dir: str) -> dict:
        """
        Compile solidity contracts into ABI. This requires solc somewhere in the $PATH
            and also ethereum.tools python library.
        Parameters:
            contracts_dir (str): directory where the contracts are stored.
            All files with .sol suffix will be compiled.
            The method won't recurse into subdirectories.
        Return:
            map (contract_name => ABI)
        """
        ret = {}
        for contract in os.listdir(contracts_dir):
            contract_path = os.path.join(contracts_dir, contract)
            if os.path.isfile(contract_path) is False and '.sol' not in contract_path:
                continue
            contract_name = os.path.basename(contract).split('.')[0]
            ret[contract_name] = _solidity.compile_contract(
                contract_path, contract_name,
                combined='abi'
            )
        return ret

    def get_contract_abi(self, contract_name: str) -> dict:
        """
        Return:
            ABI of a contract
        """
        return self.abi[contract_name]

    def get_event_abi(self, contract_name: str, event_name: str):
        """
        Get ABI of an event
        """
        contract_abi = self.get_contract_abi(contract_name)
        return [
            x for x in contract_abi['abi']
            if x['type'] == 'event' and x['name'] == event_name
        ]


CONTRACT_MANAGER = ContractManager(CONTRACTS_DIR)

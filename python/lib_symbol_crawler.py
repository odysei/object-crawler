from __future__ import print_function
import os
import sys
import subprocess
import yaml

scan = ["/opt/xdaq/lib/libtstoreclient.so"]

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class symbol_holder:
    def __init__(self):
        # sort by length
        self.U = []
        self.X = []  # any, if not above

class crawler:
    """object crawler"""
    
    def __init__(self, config_fn):
        ## options are supposed to be updated by config file(s)
        self.config = {"name": "",
                       "binary": "",
                       "investigate": [],
                       "lib_pool": [],
                       "verbosity": 0
                       }
        self.investigate_keys_ = None    # store sorted
        self.investigate = {}
        self.lib_pool_keys_ = None   # store sorted
        self.lib_pool = {}
        
        self.Load_yaml_config(config_fn)
    
    ### Methods follow below
    def Load_yaml_config(self, input_config=None):
        """Used to initialize a class using parameters from a config file"""
        
        if os.path.lexists(input_config):
            with open(input_config, 'r') as config_file:
                cfg = yaml.load(config_file)
            
            self.config["name"] = input_config
            self.config["binary"] = cfg["binary"]
            self.config["verbosity"] = cfg["verbosity"]
            
            for libs in cfg["lib_pool"]:
                self.config["lib_pool"].append(libs["libs"])
            
            for obj in cfg["investigate"]:
                self.config["investigate"].append(obj["object"])
            
        else:
            raise RuntimeError, 'A config file {0} does not exist.'.format(
                input_config)
    
    def Load_symbols(self, config=None):
        if config==None:
            config = self.config
        for obj in config["investigate"]:
            if not os.path.lexists(obj):
                raise RuntimeError, 'file to investigate: {0} not found.'.format(obj)
            out = subprocess.check_output(self.config["binary"] + " " + obj,
                                          shell = True)
            nm_lines = out.splitlines()
            self.investigate[obj] = self.Parse_nm_symbols(nm_lines)
        self.investigate_keys_ = sorted(self.investigate.keys())
        
        for group in config["lib_pool"]:
            loc = group["path"]
            files = group["files"]
            
            for fn in files:
                lib = os.path.join(loc, fn)
                
                if not os.path.lexists(lib):
                    raise RuntimeError, 'lib in pool: {0} not found.'.format(
                        lib)
                
                out = subprocess.check_output(self.config["binary"] + " " + lib,
                                              shell = True)
                nm_lines = out.splitlines()
                self.lib_pool[lib] = self.Parse_nm_symbols(nm_lines)
        self.lib_pool_keys_ = sorted(self.lib_pool.keys())
        
        return 0
    
    def Parse_nm_symbols(self, nm_lines):
        result = symbol_holder()
        
        for symbol_ln in nm_lines:
            parts = symbol_ln.split()
            length = len(parts)
            if length > 3:
                eprint('parsing ERROR: columns in line > 3')
            if length < 2:
                eprint('parsing ERROR: columns in line < 2')
            
            if length == 2:
                if parts[0] == "U":
                    result.U.append(parts[1])
                    continue
                result.X.append(parts[1])
            
            if length == 3:
                if parts[1] == "U":
                    result.U.append(parts[2])
                    continue
                result.X.append(parts[2])
        
        result.U.sort(key=len)
        result.X.sort(key=len)
        return result

    def Crawl(self, symbol):
        matches = []
        for lib in self.lib_pool_keys_:
            
            for lookup in self.lib_pool[lib].X:
                if lookup == symbol:
                    matches.append(lib)
                if len(symbol) < len(lookup):
                    break
        
        if len(matches) == 0:
            matches.append("NONE")
        
        return matches
    
    def Investigate_sorted_results_(self, found, missing):
        lib_list = []
        for symbol in found.keys():
            for lib in found[symbol]:
                lib_list.append(lib)
        
        lib_list = set(lib_list)
        for lib in sorted(lib_list):
            print("    " + lib)
        
        if len(missing) > 0:
            print("    WARNING: there are unmatched symbols")
    
    def Investigate_deeper_look_(self, found, missing):
        found_keys_ = sorted(found.keys())
        print("FOUND:")
        for found_symb in found_keys_:
            print(4 * " " + found_symb)
            for lib in found[found_symb]:
                print(8 * " " + lib)
            
        print("MISSING:")
        msg = ""
        for missing_symb in missing:
            msg += " " + missing_symb
        if len(missing) == 0:
            NONE
        else:
            print("   " + msg)
    
    def Investigate(self):
        for fn in self.investigate_keys_:
            print(fn)
            inv_symbols = self.investigate[fn]
            
            found = {}
            missing = []
            for symbol in inv_symbols.U:
                matches = self.Crawl(symbol)
                if matches[0] == "NONE":
                    missing.append(symbol)
                else:
                    found[symbol] = matches
            
            self.Investigate_sorted_results_(found, missing)
            if self.config["verbosity"] >= 1:
                self.Investigate_deeper_look_(found, missing)

def Crawl_for_symbols(fn):
    out = subprocess.check_output("nm -D " + fn, shell = True)
    symbols = out.splitlines()
    for symbol_ln in symbols:
        parts = symbol_ln.split()
        if parts[0] == "U":
            print(parts[1])

def main(argv=None):
    if argv is None:
        argv = sys.argv
    
    if len(argv) < 2:
        print('Choose a YAML configuration file\n' +\
            'python lib_symbol_crawler.py filename')
        
        sys.exit(1)
    
    if not os.path.lexists(argv[1]):
        print('file not found: {0}'.format(argv[1]))
        return 1
    
    c = crawler(argv[1])
    c.Load_symbols()
    c.Investigate()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

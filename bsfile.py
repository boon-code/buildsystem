import cPickle

INPUT = 'inp'
OUTPUT = 'out'


def load_cfg(file_path, load_all=False):
    
    f = open(file_path, 'r')
    try:
        pick = cPickle.Unpickler(f)
        config = pick.load()
        return config
    finally:
        f.close()


def save_cfg(file_path, in_vars, out_vars):
    
    f = open(file_path, 'w')
    try:
        pick = cPickle.Pickler(f)
        pick.dump({INPUT : in_vars, OUTPUT : out_vars})
    finally:
        f.close()

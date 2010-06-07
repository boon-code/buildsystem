import cPickle

INPUT = 'inp'
OUTPUT = 'out'


def load_cfg(file_path):
    
    f = open(file_path, 'r')
    try:
        pick = cPickle.Unpickler(f)
        config = pick.load()
        return config
    finally:
        f.close()


def save_cfg(file_path, out_vars):
    
    f = open(file_path, 'w')
    try:
        pick = cPickle.Pickler(f)
        pick.dump(out_vars)
    finally:
        f.close()

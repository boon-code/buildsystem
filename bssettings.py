import re

START_TAG = "<?"
END_TAG = "?>"
CODE_RE = re.compile("^<\\?\\s*py:")
VERSION = "0.0.1"

CFG_SCRIPTFILE_RE = re.compile("^configure_([^\\s]+)[.]{1}py")
CFG_SCRIPTFILE = "configure_%s.py"
CFG_EXTENSION_RE = re.compile("^\\s*#\\$\\s+" + 
    "([^\\n,^\\r]+)\\r{0,1}\\n{0,1}\\r{0,1}$")
CFG_USERFILE = "userconfig.pickle0"
CFG_CACHEFILE = "cachedconfig.pickle0"

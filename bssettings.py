import re

CFG_SCRIPTFILE_RE = re.compile("^configure_([^\\s]+)[.]{1}py")
CFG_SCRIPTFILE = "configure_%s.py"
CFG_USERFILE = "userconfig.pickle0"
CFG_CACHEFILE = "cachedconfig.pickle0"

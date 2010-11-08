#    Copyright (C) 2010  Chris Targett  <chris@xlevus.net>
#
#    This file is part of StagFS.
#
#    StagFS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    StagFS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with StagFS.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import logging

logger = logging.getLogger('stagfs')

def setup_logging():
    def exceptionCallback(eType, eValue, eTraceBack):
        import cgitb
        txt = cgitb.text((eType, eValue, eTraceBack))
        logger.critical(txt)

    logging.basicConfig(level = logging.DEBUG,
            format = '%(asctime)s %(levelname)s %(name)s: %(message)s',
            filename = '/tmp/stagfs.log',
            filemode = 'a')
 
    sys.excepthook = exceptionCallback # replace default exception handler
    
    logging.debug('Logging and exception handling has been set up')

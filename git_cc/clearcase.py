from .common import *

class Clearcase:
    def rebase(self):
        pass
    def mkact(self, comment):
        pass
    def rmactivity(self):
        pass
    def commit(self):
        pass
    def getCommentFmt(self):
        return '%Nc'
    def getRealComment(self, comment):
        return comment

class UCM:
    def __init__(self):
        self.activities = {}
    def rebase(self):
        out = cc_exec(['rebase', '-rec', '-f'])
        if not out.startswith('No rebase needed'):
            debug(out)
            debug(cc_exec(['rebase', '-complete']))
    def mkact(self, comment):
        self.activity = self._getActivities().get(comment)
        if self.activity:
            cc_exec(['setact', self.activity])
            return
        _comment = cc_exec(['mkact', '-f', '-headline', comment])
        _comment = _comment.split('\n')[0]
        self.activity = _comment[_comment.find('"')+1:_comment.rfind('"')]
        self._getActivities()[comment] = self.activity
    def rmactivity(self):
        cc_exec(['setact', '-none'])
        cc_exec(['rmactivity', '-f', self.activity], errors=False)
    def commit(self):
        cc_exec(['setact', '-none'])
        debug(cc_exec(['deliver','-f']))
        debug(cc_exec(['deliver', '-com', '-f']))
    def getCommentFmt(self):
        return '%[activity]p'
    def getRealComment(self, activity):
        return cc_exec(['lsactivity', '-fmt', '%[headline]p', activity]) if activity else activity
    def _getActivities(self):
        if not self.activities:
            sep = '@@@'
            for line in cc_exec(['lsactivity', '-fmt', '%[headline]p|%n' + sep]).split(sep):
                if line:
                    line = line.strip().split('|')
                    self.activities[line[0]] = line[1]
        return self.activities

cc = (UCM if cfg.getCore('type') == 'UCM' else Clearcase)();

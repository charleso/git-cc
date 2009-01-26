from common import *

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
    def rebase(self):
        out = cc_exec(['rebase', '-rec', '-f'])
        if not out.startswith('No rebase needed'):
            debug(out)
            debug(cc_exec(['rebase', '-complete']))
    def mkact(self, comment):
        self.rebase()
        comment = cc_exec(['mkact', '-f', '-headline', comment])
        comment = comment.split('\n')[0]
        self.activity = comment[comment.find('"')+1:comment.rfind('"')]
    def rmactivity(self):
        cc_exec(['setact', '-none'])
        cc_exec(['rmactivity', '-f', self.activity])
    def commit(self):
        cc_exec(['setact', '-none'])
        debug(cc_exec(['deliver','-f']))
        debug(cc_exec(['deliver', '-com', '-f']))
    def getCommentFmt(self):
        return '%[activity]p'
    def getRealComment(self, activity):
        return cc_exec(['lsactivity', '-fmt', '%[headline]p', activity]) if activity else activity

cc = (UCM if cfg.get('type') == 'UCM' else Clearcase)();

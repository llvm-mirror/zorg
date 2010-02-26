from buildbot import util, interfaces
from zope.interface import implements
from buildbot.status import builder, mail

class InformativeMailNotifier(mail.MailNotifier):
    """MailNotifier subclass which provides additional information about the
    build failure inside the email."""

    implements(interfaces.IEmailSender)
    compare_attrs = (mail.MailNotifier.compare_attrs +
                     ["num_lines", "only_failure_logs"])

    # Remove messageFormatter from the compare_attrs, that would lead to
    # recursion, and is checked by the class test.
    compare_attrs.remove("messageFormatter")

    def __init__(self, 
                 num_lines = 10, only_failure_logs = True,
                 *attrs, **kwargs):
        mail.MailNotifier.__init__(self,
                                   messageFormatter=self.informative_formatter, 
                                   *attrs, **kwargs)
        self.num_lines = num_lines
        self.only_failure_logs = only_failure_logs
        
    def informative_formatter(self, mode, name, build, results, status):
        # Get the standard message.
        data = self.defaultMessage(mode, name, build, results, status)['body']
        data += '\n' + '='*80 + '\n\n'

        # Append additional information on the changes.
        ss = build.getSourceStamp()
        if ss:
            data += 'CHANGES:\n'
            data += '\n\n'.join([c.asText() for c in ss.changes])
            data += '\n\n'
        else:
            data += 'NO SOURCE STAMP (CHANGES UNAVAILABLE)'
            data += '\n\n'
    
        # Append log files.
        if self.num_lines:
            data += 'LOGS:\n'
            for logf in build.getLogs():
                logStep = logf.getStep()
                logStatus,_ = logStep.getResults()
                if (self.only_failure_logs and logStatus != builder.FAILURE):
                    continue
                
                trailingLines = logf.getText().splitlines()[-self.num_lines:]
                data += "Last %d lines of '%s':\n" % (self.num_lines,
                                                      logf.getName())
                data += '\t' + '\n\t'.join(trailingLines)
                data += '\n\n'

        return { 'body' : data,
                 'type' : 'plain' }

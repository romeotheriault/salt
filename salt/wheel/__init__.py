'''
Modules used to control the master itself
'''

# Import salt libs
import salt.loader
import salt.payload
import salt.utils


class Wheel(object):
    '''
    Manage calls to the salt wheel system
    '''
    def __init__(self, opts):
        self.opts = opts
        self.w_funcs = salt.loader.wheels(opts)

    def call_func(self, mod, fun, **kwargs):
        '''
        Execute a master control function
        '''
        func = '{0}.{1}'.format(mod, fun)
        if not func in self.w_funcs:
            return 'Unknown wheel function'
        f_call = salt.utils.format_call(self.w_funcs[func], kwargs)
        return self.w_funcs[func](*f_call.get('args', ()), **f_call.get('kwargs', {}))

    def master_call(self, mod, fun, **kwargs):
        '''
        Send a function call to a wheel module through the master network interface
        '''
        load = kwargs
        load['cmd'] = 'wheel'
        load['mod'] = mod
        load['fun'] = fun
        sreq = salt.payload.SREQ(
                'tcp://{0[interface]}:{0[ret_port]}'.format(self.opts),
                )
        return sreq.send('clear', load)

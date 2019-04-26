

def report(func):
    def run(*args,**kwargs):
        print('[@spider doing]:{}'.format(func.__name__))
        ret=func(*args,**kwargs)
        print('[@spider done]:{}'.format(func.__name__))
        return ret
    return run

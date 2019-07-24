import nox

nox.options.reuse_existing_virtualenvs = True


@nox.session(python=('3.5', '3.6', '3.7'))
@nox.parametrize('django', ('2.0', '2.1', '2.2'))
def tests(session, django):
    session.install(f'django>={django},<{django}.999')
    session.install('-e', '.[dev]')
    session.run('pytest')
